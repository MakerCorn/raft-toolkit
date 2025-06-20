import argparse
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from azure.ai.evaluation import AzureOpenAIModelConfiguration, GroundednessEvaluator, SimilarityEvaluator, evaluate
from dotenv import load_dotenv

try:
    from client_utils import build_openai_client
    from logconf import log_setup
except ImportError:
    # Fallback to core toolkit imports
    from raft_toolkit.core.clients import build_openai_client
    from raft_toolkit.core.logging import log_setup
from openai import RateLimitError
from tenacity import retry, retry_if_exception_type, wait_exponential
from tqdm import tqdm

logger = logging.getLogger("pfeval")

load_dotenv()


def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", type=str, default="input.jsonl", help="The input data JSONL file to load")
    parser.add_argument("--output", type=str, default="output.jsonl", help="The output data JSONL file to export to")
    parser.add_argument("--mode", type=str, default="local", help="local or remote")
    parser.add_argument("--model", type=str, default="gpt-4", help="The model to evaluate")
    parser.add_argument("--deployment", type=str, default="gpt-4", help="The deployment name for the model")

    args = parser.parse_args()
    return args


base_url = os.environ["EVAL_OPENAI_BASE_URL"]
api_key = os.environ["EVAL_OPENAI_API_KEY"]
api_version = os.environ["EVAL_OPENAI_DEPLOYMENT"]

target_model = "Llama-2-7b-raft-bats-18k-unrrr"

print(f"base_url={base_url}")
print(f"api_key={api_key}")
print(f"api_version={api_version}")

client = build_openai_client("EVAL")
# client = OpenAI(
#    base_url=os.environ["EVAL_OPENAI_BASE_URL"],
#    api_key=os.environ["EVAL_OPENAI_API_KEY"],
# )


def get_answer(context, question):
    response = client.completions.create(
        model=target_model, prompt=format_prompt(context, question), temperature=0.02, max_tokens=8192, stop="<STOP>"
    )
    answer = response.choices[0].text
    return {"answer": answer}


def format_prompt(context, question):
    return f"{context}\n{question}"


def evaluate_aistudio(model_config, project_scope, project_scope_report, data_path):
    """Evaluate using AI Studio.

    Args:
        model_config: The model configuration.
        project_scope: The project scope.
        project_scope_report: The project scope report.
        data_path: The path to the data file.

    Returns:
        The result of the evaluation.
    """
    # create unique id for each run with date and time
    time_str = datetime.now().strftime("%Y%m%d%H%M%S")
    run_id = f"chat_evaluation_sdk_{time_str}"
    print(run_id)

    result = evaluate(
        evaluation_name=run_id,
        data=data_path,
        target=get_answer,
        azure_ai_project=project_scope_report,
        evaluators={
            "similarity": SimilarityEvaluator(model_config),
            "groundedness": GroundednessEvaluator(model_config=model_config, project_scope=project_scope),
        },
        evaluator_config={
            "defaults": {  # type: ignore[typeddict-unknown-key]
                "query": "${data.question}",
                "response": "${target.answer}",
                "ground_truth": "${data.gold_final_answer}",
                "context": "${data.context}",
            },
        },
    )
    print(f"studio_url=f{result['studio_url']}")
    return result


def evaluate_local(model_config, project_scope, project_scope_report, data_path):
    """Evaluate locally.

    Args:
        model_config: The model configuration.
        project_scope: The project scope.
        project_scope_report: The project scope report.
        data_path: The path to the data file.

    Returns:
        The results of the evaluation.
    """
    data = []
    with open(data_path) as f:
        for line in f:
            data.append(json.loads(line))

    evaluators = [
        #        RelevanceEvaluator(model_config),
        #        FluencyEvaluator(model_config),
        #        CoherenceEvaluator(model_config),
        GroundednessEvaluator(model_config=model_config),
        SimilarityEvaluator(model_config),
    ]

    @retry(
        wait=wait_exponential(multiplier=1, min=10, max=120),
        reraise=True,
        retry=retry_if_exception_type(RateLimitError),
    )
    def evaluate_row_with(row, evaluator):
        result = evaluator(
            question=row["question"],
            answer=row["final_answer"],
            context=row["context"],
            ground_truth=row["gold_final_answer"],
        )
        return result

    def evaluate_row(row, pbar):
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


class PfevalCompletion:
    """Handles completion-based programmatic function evaluation (PF-Eval) tasks.

    This class manages the setup, execution, and result processing for completion-based evaluation tasks, including prompt construction and result parsing.
    """

    def __init__(self, config):
        """Initializes PfevalCompletion with the given configuration.

        Args:
            config (dict): Configuration dictionary for the evaluation task.
        """
        # Initialization code here

    def run(self, input_data):
        """Executes the completion-based evaluation on the provided input data.

        Args:
            input_data (Any): The input data to be evaluated.

        Returns:
            Any: The result of the evaluation.
        """
        # Execution code here

    def build_prompt(self, input_data):
        """Constructs a prompt for the completion model based on input data.

        Args:
            input_data (Any): The input data for prompt construction.

        Returns:
            str: The constructed prompt string.
        """
        # Prompt construction code here

    def parse_result(self, result):
        """Parses the result returned by the completion model.

        Args:
            result (Any): The raw result from the completion model.

        Returns:
            Any: The parsed result in a structured format.
        """
        # Result parsing code here


def main():
    import time

    import jsonlines

    log_setup()
    args = get_args()

    # Initialize Azure OpenAI Connection
    logger.info("Loading model configuration")

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
        model_config=model_config,
        data_path=args.input,
        project_scope=project_scope,
        project_scope_report=project_scope_report,
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
