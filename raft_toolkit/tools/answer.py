import argparse
import json
import logging
import re
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed

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

logger = logging.getLogger("answer")
log_setup()

load_dotenv()


def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", type=str, default="input.jsonl", help="The input data JSONL file to load")
    parser.add_argument("--output", type=str, default="output.jsonl", help="The output data JSONL file to export to")
    parser.add_argument("--workers", type=int, default="1", help="Number of worker threads")
    parser.add_argument(
        "--model", type=str, default="gpt-4", help="Model name to generate answers for the evaluation data"
    )
    parser.add_argument(
        "--deployment", type=str, default="gpt-4", help="Deployment name for the model used for answer generation"
    )
    parser.add_argument(
        "--system-prompt-key", type=str, default="gpt", help="The system prompt to use to generate the dataset"
    )
    parser.add_argument("--templates", type=str, default="./", help="The system prompt template location")
    parser.add_argument("--count", type=int, default="-1", help="Count of a random set of questions to answer")

    args = parser.parse_args()
    return args


def load_prompt_template(file_path: str) -> str:
    """Loads the prompt template from the specified file.

    Args:
        file_path (str): The path to the prompt template file.

    Returns:
        str: The content of the prompt template file.
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
    """Generates an answer to a question based on the provided context.

    Args:
        chat_completer: The chat completer instance to use for generating the answer.
        context (str): The context information to use for generating the answer.
        question (str): The question to answer.
        model (str): The model name to use for generating the answer.
        system_prompt (str): The system prompt to use for generating the answer.

    Returns:
        dict: A dictionary containing the generated answer under the key "final_answer".
    """
    response = chat_completer(
        model=model,
        messages=[
            {"role": "system", "content": prompt_templates[system_prompt]},
            {"role": "user", "content": question},
        ],
        temperature=0.02,
        max_tokens=2048,
    )
    answer = answer = response.choices[0].message.content
    return {"final_answer": answer}


def answer_local(chat_completer, model, data_path, workers=1, system_prompt="gpt", total_records=-1):
    """Answers questions in the local dataset using the specified model and parameters.

    Args:
        chat_completer: The chat completer instance to use for generating answers.
        model (str): The model name to use for generating answers.
        data_path (str): The path to the input data file (JSONL format).
        workers (int, optional): The number of worker threads to use for parallel processing. Defaults to 1.
        system_prompt (str, optional): The system prompt to use for generating answers. Defaults to "gpt".
        total_records (int, optional): The total number of records/questions to process. Defaults to -1 (all records).

    Returns:
        list: A list of dictionaries containing the original data along with the generated answers.
    """
    data = []
    total_count = 0

    with open(data_path) as f:
        for line in f:
            data.append(json.loads(line))

    def answer_row_with(row):
        result = get_answer(
            chat_completer=chat_completer,
            question=row["question"],
            context=row["context"],
            model=model,
            system_prompt=system_prompt,
        )
        return result

    def answer_row(row, pbar):
        """Answers a single row (question-context pair) and updates the progress bar.

        Args:
            row (dict): The data row containing the question and context.
            pbar (tqdm): The progress bar instance to update.

        Returns:
            dict: The updated data row with the generated answer.
        """
        try:
            result = answer_row_with(row)
        except Exception as e:
            result = {"error": str(e)}

        row.update(result)
        pbar.update(1)

        return row

    results = []
    futures = []
    if total_records > 0:
        # Regular expression to match strings that start with a number followed by a period
        pattern = r"^\d+\."

        # Filter out rows where 'questions' start with the pattern
        filtered_questions = [q for q in data if not re.match(pattern, q["question"])]
        # Use secrets for cryptographically secure sampling
        data = secrets.SystemRandom().sample(filtered_questions, min(total_records, len(filtered_questions)))

    with tqdm(total=len(data)) as pbar:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            for row in data:
                if (total_records > 0) & (total_count > total_records):
                    break
                futures.append(executor.submit(answer_row, row, pbar))
                total_count += 1
            for future in as_completed(futures):
                results.append(future.result())

    return results


def main():
    import time

    import jsonlines

    args = get_args()

    prompt_templates[args.system_prompt_key] = load_prompt_template(
        args.templates + args.system_prompt_key + "_template.txt"
    )

    client = build_openai_client("EVAL", azure_deployment=args.deployment)
    chat_completer = ChatCompleter(client)

    start = time.time()
    logger.info("Starting answer generation...")

    logger.info(f"Building answers for {args.input} with model {args.model}")
    logger.info(f"Output file will be saved to {args.output}")
    answer_result = answer_local(
        chat_completer=chat_completer,
        model=args.model,
        data_path=args.input,
        workers=args.workers,
        system_prompt=args.system_prompt_key,
        total_records=args.count,
    )

    end = time.time()
    logger.info(f"Finished answer generation in {end - start}s")
    logger.info(f"Writing {len(answer_result)} results to {args.output}")

    # Save evaluation results to a JSONL file
    with jsonlines.open(args.output, "w") as writer:
        writer.write_all(answer_result)


if __name__ == "__main__":
    main()
