import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from azure.ai.evaluation import (
    AzureOpenAIModelConfiguration,
    CoherenceEvaluator,
    FluencyEvaluator,
    GroundednessEvaluator,
    RelevanceEvaluator,
    SimilarityEvaluator,
    evaluate,
)
from dotenv import load_dotenv

try:
    from client_utils import ChatCompleter, build_openai_client
    from logconf import log_setup
except ImportError:
    # Fallback to core toolkit imports
    from raft_toolkit.core.clients import build_openai_client
    from raft_toolkit.core.clients.stats import ChatCompleter
    from raft_toolkit.core.logging import log_setup
from openai import RateLimitError
from tenacity import retry, retry_if_exception_type, wait_exponential
from tqdm import tqdm

logger = logging.getLogger("pfeval-chat")

load_dotenv()


def get_args() -> argparse.Namespace:
    """Parses and returns the arguments specified by the user's command

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", type=str, default="input.jsonl", help="The input data JSONL file to load")
    parser.add_argument("--output", type=str, default="output.jsonl", help="The output data JSONL file to export to")
    parser.add_argument("--mode", type=str, default="local", help="local or remote")
    parser.add_argument("--model", type=str, default="gpt-4", help="The model to evaluate")
    parser.add_argument("--score-model", type=str, default="gpt-35-instruct", help="The model to use for scoring")
    parser.add_argument("--deployment", type=str, default="gpt-4", help="The deployment name for the model")
    parser.add_argument("--system-prompt-key", default="gpt", help="The system prompt to use to generate the dataset")
    parser.add_argument("--templates", default="./", help="The system prompt template location")

    args = parser.parse_args()
    return args


def load_prompt_template(file_path: str) -> str:
    """Loads a prompt template from a file

    Args:
        file_path (str): The path to the template file

    Returns:
        str: The content of the template file
    """
    with open(file_path, "r") as file:
        return file.read()


prompt_templates = {
    "gpt": "You are a helpful assistant who can provide an answer given a question and relevant context.",
    "llama": "You are a a helpful assistant who can provide an answer given a question and relevant context.",
}


@retry(
    wait=wait_exponential(multiplier=1, min=10, max=120), reraise=True, retry=retry_if_exception_type(RateLimitError)
)
def get_answer(chat_completer, context, question, model, system_prompt):
    """Gets an answer from the chat model given a context and question

    Args:
        chat_completer (ChatCompleter): The chat completer instance
        context (str): The context for the question
        question (str): The question to ask
        model (str): The model to use
        system_prompt (str): The system prompt to use

    Returns:
        dict: A dictionary containing the final answer
    """
    response = chat_completer(
        model=model,
        messages=[
            {"role": "system", "content": prompt_templates[system_prompt]},
            {"role": "user", "content": question},
        ],
        temperature=0.02,
        max_tokens=8192,
    )
    answer = response.choices[0].message["content"]
    return {"final_answer": answer}


def format_prompt(context, question):
    """Formats the prompt for the model by combining context and question

    Args:
        context (str): The context for the question
        question (str): The question to ask

    Returns:
        str: The formatted prompt
    """
    return f"{context}\n{question}"


def evaluate_aistudio(chat_completer, model_config, project_scope, project_scope_report, data_path, model, score_model):
    """Evaluates the model using the Aistudio platform

    Args:
        chat_completer (ChatCompleter): The chat completer instance
        model_config (AzureOpenAIModelConfiguration): The model configuration
        project_scope (dict): The project scope for groundedness
        project_scope_report (dict): The project scope for reporting
        data_path (str): The path to the input data
        model (str): The model to use for evaluation
        score_model (str): The model to use for scoring

    Returns:
        dict: The result of the evaluation
    """
    # create unique id for each run with date and time
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")
    run_id = f"chat_evaluation_sdk_{time_str}"
    print(run_id)

    final_answer = get_answer(
        chat_completer=chat_completer,
        question=data_path.question,
        context=data_path.context,
        model=model,
        system_prompt="gpt",
    )

    result = evaluate(
        evaluation_name=run_id,
        data=data_path,
        target=final_answer,
        azure_ai_project=project_scope_report,
        model=score_model,
        evaluators={
            "relevance": RelevanceEvaluator(model_config),
            "fluency": FluencyEvaluator(model_config),
            "coherence": CoherenceEvaluator(model_config),
            "similarity": SimilarityEvaluator(model_config),
            "groundedness": GroundednessEvaluator(model_config=model_config, project_scope=project_scope),
        },
        evaluator_config={
            "defaults": {  # type: ignore[typeddict-unknown-key]
                "query": "${data.question}",
                "response": "${final_answer}",
                "ground_truth": "${data.gold_final_answer}",
                "context": "${data.context}",
            },
        },
    )
    print(f"studio_url=f{result['studio_url']}")
    return result


def evaluate_local(chat_completer, model_config, project_scope, project_scope_report, data_path, model, score_model):
    """Evaluates the model locally using the provided data

    Args:
        chat_completer (ChatCompleter): The chat completer instance
        model_config (AzureOpenAIModelConfiguration): The model configuration
        project_scope (dict): The project scope for groundedness
        project_scope_report (dict): The project scope for reporting
        data_path (str): The path to the input data
        model (str): The model to use for evaluation
        score_model (str): The model to use for scoring

    Returns:
        list: A list of evaluation results for each data instance
    """
    data = []
    with open(data_path) as f:
        for line in f:
            data.append(json.loads(line))

    evaluators = [
        RelevanceEvaluator(model_config),
        FluencyEvaluator(model_config),
        CoherenceEvaluator(model_config),
        GroundednessEvaluator(model_config=model_config),
        SimilarityEvaluator(model_config),
    ]

    @retry(
        wait=wait_exponential(multiplier=1, min=10, max=120),
        reraise=True,
        retry=retry_if_exception_type(RateLimitError),
    )
    def evaluate_row_with(row, evaluator):
        """Evaluates a single row of data with the given evaluator

        Args:
            row (dict): The data row to evaluate
            evaluator (Evaluator): The evaluator to use

        Returns:
            dict: The evaluation result for the row
        """
        final_answer = get_answer(
            chat_completer=chat_completer,
            question=data_path.question,
            context=data_path.context,
            model=model,
            system_prompt="gpt",
        )
        result = evaluator(
            model=score_model,
            question=row["question"],
            answer=final_answer,
            context=row["context"],
            ground_truth=row["gold_final_answer"],
        )
        return result

    def evaluate_row(row, pbar):
        """Evaluates a single row of data and updates the progress bar

        Args:
            row (dict): The data row to evaluate
            pbar (tqdm): The progress bar instance

        Returns:
            dict: The evaluation result for the row
        """
        for evaluator in evaluators:
            result = evaluate_row_with(row, evaluator)
            row.update(result)
            pbar.update(1)
        return row

    results = []
    futures = []
    with tqdm(total=len(data) * len(evaluators)) as pbar:
        with ThreadPoolExecutor(max_workers=2) as executor:
            for row in data:
                futures.append(executor.submit(evaluate_row, row, pbar))
            for future in as_completed(futures):
                results.append(future.result())

    return results


def main():
    import time

    import jsonlines

    log_setup()
    args = get_args()

    # Initialize Azure OpenAI Connection for the model used for answer generation
    logger.info("Loading evaluation model configuration for answer generation.")

    base_url = os.environ["EVAL_OPENAI_BASE_URL"]
    api_key = os.environ["EVAL_OPENAI_API_KEY"]
    api_version = os.environ["EVAL_OPENAI_DEPLOYMENT"]

    logger.info(f"eval_base_url={base_url}")
    logger.info(f"eval_api_key={api_key}")
    logger.info(f"eval_api_version={api_version}")

    prompt_templates[args.system_prompt_key] = load_prompt_template(
        args.templates + args.system_prompt_key + "_template.txt"
    )

    client = build_openai_client("EVAL", azure_deployment=args.deployment)

    chat_completer = ChatCompleter(client)

    # Initialize Azure OpenAI Connection for the model used for scoring
    logger.info("Loading scoring model configuration")

    # Model config
    azure_endpoint = os.environ["SCORE_AZURE_OPENAI_ENDPOINT"]
    api_key = os.environ["SCORE_AZURE_OPENAI_API_KEY"]
    api_version = os.environ["SCORE_OPENAI_API_VERSION"]
    deployment = os.environ["SCORE_AZURE_OPENAI_DEPLOYMENT"]

    logger.info(f"deployment={deployment}")
    logger.info(f"api_version={api_version}")
    logger.info(f"azure_endpoint={azure_endpoint}")

    # Project Scope
    subscription_id = os.environ["GROUNDEDNESS_SUB_ID"]
    resource_group_name = os.environ["GROUNDEDNESS_GROUP"]
    project_name = os.environ["GROUNDEDNESS_PROJECT_NAME"]

    logger.info(f"subscription_id={subscription_id}")
    logger.info(f"resource_group_name={resource_group_name}")
    logger.info(f"project_name={project_name}")

    model_config = AzureOpenAIModelConfiguration(
        azure_deployment=deployment, api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint
    )

    project_scope = {
        "subscription_id": subscription_id,
        "resource_group_name": resource_group_name,
        "project_name": project_name,
    }

    subscription_id = os.environ["REPORT_SUB_ID"]
    resource_group_name = os.environ["REPORT_GROUP"]
    project_name = os.environ["REPORT_PROJECT_NAME"]

    print(f"report subscription_id={subscription_id}")
    print(f"report resource_group_name={resource_group_name}")
    print(f"report project_name={project_name}")

    project_scope_report = {
        "subscription_id": subscription_id,
        "resource_group_name": resource_group_name,
        "project_name": project_name,
    }

    start = time.time()
    logger.info("Starting evaluate...")

    modes = {"local": evaluate_local, "remote": evaluate_aistudio}
    evaluate_func = modes[args.mode]
    logger.info(f"Evaluating {args.input} with mode {args.mode}")
    logger.info(f"Output file will be saved to {args.output}")
    eval_result = evaluate_func(
        chat_completer,
        model_config=model_config,
        data_path=args.input,
        project_scope=project_scope,
        project_scope_report=project_scope_report,
        model=args.model,
        score_model=args.score_model,
    )

    end = time.time()
    logger.info(f"Finished evaluate in {end - start}s")
    logger.info(f"Writing {len(eval_result)} results to {args.output}")

    # save evaluation results to a JSONL file
    if args.mode == "local":
        with jsonlines.open(args.output, "w") as writer:
            writer.write_all(eval_result)


if __name__ == "__main__":
    main()
