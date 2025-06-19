import argparse
import json
import logging
import multiprocessing as mp
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import RateLimitError
from tenacity import before_sleep_log, retry, retry_if_exception_type, wait_exponential
from tqdm import tqdm

from raft_toolkit.core.clients import StatsCompleter, UsageStats, build_openai_client
from raft_toolkit.core.logging import log_setup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()  # take environment variables from .env.


def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--question-file", type=str, required=True)
    parser.add_argument("--answer-file", type=str, default="answer.jsonl")
    parser.add_argument("--model", type=str, default="gpt-4", help="The model to evaluate")
    parser.add_argument("--input-prompt-key", type=str, default="instruction", help="The column to use as input prompt")
    parser.add_argument("--output-answer-key", type=str, default="answer", help="The column to use as output answer")
    parser.add_argument(
        "--workers", type=int, default=1, help="The number of worker threads to use to evaluate the dataset"
    )

    args = parser.parse_args()
    return args


def main():
    log_setup()
    client = build_openai_client(env_prefix="EVAL")

    logger = logging.getLogger("eval")

    @retry(
        wait=wait_exponential(multiplier=1, min=10, max=120),
        reraise=True,
        retry=retry_if_exception_type(RateLimitError),
        before_sleep=before_sleep_log(logger, logging.INFO),
    )
    def retry_complete(*args, **kwargs):
        return client.completions.create(*args, **kwargs)

    completions_completer = StatsCompleter(retry_complete)
    args = get_args()

    model = args.model
    prompt_key = args.input_prompt_key
    answer_key = args.output_answer_key

    def get_openai_response(prompt: str) -> Optional[str]:
        """Gets a response from the OpenAI API for a given prompt.

        Args:
            prompt (str): The prompt to send to the OpenAI API.

        Returns:
            Optional[str]: The response from the API, or None if an error occurs.
        """
        response = completions_completer(model=model, prompt=prompt, temperature=0.02, max_tokens=8192, stop="<STOP>")

        try:
            return str(response.choices[0].text)
        except Exception as e:
            print(e)
            return None

    def get_answer(input_json: Dict[str, Any]) -> Dict[str, Any]:
        """Processes the input JSON to generate an answer using the OpenAI API.

        Args:
            input_json (Dict[str, Any]): The input data as a dictionary.

        Returns:
            Dict[str, Any]: The input JSON with the generated answer added.
        """
        prompt = input_json[prompt_key]
        try:
            result = get_openai_response(prompt)
            input_json[answer_key] = result
        except Exception as e:
            input_json["error"] = str(e)
        return input_json

    def write_result_to_file(result: Dict[str, Any], write_file_name: str) -> None:
        """Writes the result dictionary to a file in JSON Lines format.

        Args:
            result (Dict[str, Any]): The result to write to the file.
            write_file_name (str): The name of the file to write to.
        """
        with file_write_lock:
            with open(write_file_name, "a") as outfile:
                json.dump(result, outfile)
                outfile.write("\n")

    write_file_name = args.answer_file
    if os.path.isfile(write_file_name):
        os.remove(write_file_name)

    num_workers = args.workers
    file_write_lock = mp.Lock()
    inputs = []
    with open(args.question_file, "r") as f:
        for line in f:
            inputs.append(json.loads(line))

    logger.info(f"number of questions: {len(inputs)}")
    start_time = time.time()
    usage_stats = UsageStats()
    tps: float = 0.0
    # Access retry attribute safely
    retrying = getattr(retry_complete, "retry", None)
    with tqdm(total=len(inputs), unit="answers") as pbar:
        if num_workers > 1:
            with ThreadPoolExecutor(num_workers) as executor:
                futures = [executor.submit(get_answer, input) for input in inputs]

                for future in as_completed(futures):
                    result = future.result()

                    stats = completions_completer.get_stats_and_reset()
                    if stats:
                        if stats.duration > 0:
                            tps = float(stats.total_tokens) / float(stats.duration)
                            usage_stats += stats

                    # Access statistics safely
                    if retrying and hasattr(retrying, "statistics"):
                        retry_stats = retrying.statistics
                        if retry_stats and len(retry_stats.keys()) > 0:
                            logger.info(f"retrying stats: {retry_stats}")

                    if usage_stats.duration > 0:
                        pbar.set_postfix(
                            {"last tok/s": tps, "avg tok/s": usage_stats.total_tokens / usage_stats.duration}
                        )
                    pbar.update(1)
                    write_result_to_file(result, write_file_name)
        else:
            for input in inputs:

                logger.debug(f"Processing input {input}")

                result = get_answer(input)
                stats = completions_completer.get_stats_and_reset()
                if stats:
                    if stats.duration > 0:
                        tps = float(stats.total_tokens) / float(stats.duration)
                        usage_stats += stats

                # Access statistics safely
                if retrying and hasattr(retrying, "statistics"):
                    retry_stats = retrying.statistics
                    if retry_stats and len(retry_stats.keys()) > 0:
                        logger.info(f"retrying stats: {retry_stats}")

                if usage_stats.duration > 0:
                    pbar.set_postfix({"last tok/s": tps, "avg tok/s": usage_stats.total_tokens / usage_stats.duration})
                pbar.update(1)
                write_result_to_file(result, write_file_name)

    end_time = time.time()
    logger.info(f"total time used: {end_time - start_time}")


if __name__ == "__main__":
    main()
