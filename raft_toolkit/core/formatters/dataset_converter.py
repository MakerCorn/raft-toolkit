import argparse
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional
from typing import get_args as typing_get_args

from datasets import Dataset, load_dataset

from ..logging.setup import log_setup

"""
This file allows to convert raw HuggingFace Datasets into files suitable to fine tune completion and chat models.
"""

OutputDatasetType = Literal["parquet", "jsonl"]
outputDatasetTypes = list(typing_get_args(OutputDatasetType))

InputDatasetType = Literal["arrow", "jsonl"]
inputDatasetTypes = list(typing_get_args(InputDatasetType))

DatasetFormat = Literal["hf", "completion", "chat", "eval"]
datasetFormats = list(typing_get_args(DatasetFormat))


def get_args() -> argparse.Namespace:
    """
    Parses and returns the arguments specified by the user's command

    Returns:
        argparse.Namespace: The parsed arguments
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("--input", type=str, required=True, help="Input HuggingFace dataset file")
    parser.add_argument(
        "--input-type",
        type=str,
        default="arrow",
        help="Format of the input dataset. Defaults to arrow.",
        choices=inputDatasetTypes,
    )
    parser.add_argument("--output", type=str, required=True, help="Output file")
    parser.add_argument(
        "--output-format", type=str, required=True, help="Format to convert the dataset to", choices=datasetFormats
    )
    parser.add_argument(
        "--output-type",
        type=str,
        default="jsonl",
        help="Type to export the dataset to. Defaults to jsonl.",
        choices=outputDatasetTypes,
    )
    parser.add_argument(
        "--output-chat-system-prompt", type=str, help="The system prompt to use when the output format is chat"
    )
    parser.add_argument(
        "--output-completion-prompt-column",
        type=str,
        default="prompt",
        help="The prompt column name to use for the completion format",
    )
    parser.add_argument(
        "--output-completion-completion-column",
        type=str,
        default="completion",
        help="The completion column name to use for the completion format",
    )
    parser.add_argument(
        "--output-completion-stop", type=str, default="<STOP>", help="The stop keyword to use for the completion format"
    )

    args = parser.parse_args()
    return args


class DatasetFormatter(ABC):
    """
    Base class for dataset formatters. Formatters rename columns, remove and add
    columns to match the expected target format structure. HF, Chat or Completion models file formats.
    https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset
    """

    @abstractmethod
    def format(self, ds: Dataset, params: Dict[str, str]) -> Dataset:
        pass


class DatasetExporter(ABC):
    """
    Base class for dataset exporters. Exporters export dataset to different file types, JSONL, Parquet, ...
    """

    @abstractmethod
    def export(self, ds: Dataset, output_path: str):
        pass


class DatasetConverter:
    """
    Entry point class. It resolves which DatasetFormatter and which DatasetExporter to use and runs them.
    """

    formats: Dict[DatasetFormat, DatasetFormatter]
    exporters: Dict[OutputDatasetType, Any]

    def __init__(self) -> None:
        self.formats = {
            "hf": HuggingFaceDatasetFormatter(),
            "completion": OpenAiCompletionDatasetFormatter(),
            "chat": OpenAiChatDatasetFormatter(),
            "eval": EvalDatasetFormatter(),
        }
        self.exporters = {"parquet": ParquetDatasetExporter(), "jsonl": JsonlDatasetExporter()}

    def convert(
        self,
        ds: Dataset,
        format: DatasetFormat,
        output_path: str,
        output_type: OutputDatasetType,
        params: Dict[str, str],
    ):
        if format not in self.formats:
            raise Exception(f"Output Format {format} is not supported, pleased select one of {self.formats.keys()}")

        if output_type not in self.exporters:
            raise Exception(
                f"Output Type {output_type} is not supported, pleased select one of {self.exporters.keys()}"
            )

        formatter = self.formats[format]
        newds = formatter.format(ds, params)
        exporter = self.exporters[output_type]
        exporter.export(newds, output_path)


class HuggingFaceDatasetFormatter(DatasetFormatter):
    """
    Returns the HuggingFace Dataset as is
    """

    def format(self, ds: Dataset, params: Dict[str, str]) -> Dataset:
        return ds


def _remove_all_columns_but(ds: Dataset, keep_columns: List[str]) -> Dataset:
    """
    HF Dataset doesn't have a way to copy only specific columns of a Dataset so this help
    removes all columns but the ones specified.

    Args:
        ds (Dataset): The dataset to remove columns from
        keep_columns (list): The list of column names to keep

    Returns:
        Dataset: The dataset with only the specified columns
    """
    remove_columns = list(ds.column_names)
    for keep in keep_columns:
        try:
            remove_columns.remove(keep)
        except ValueError:
            raise Exception(f"Column {keep} not found in {remove_columns}")
    ds = ds.remove_columns(remove_columns)
    return ds


class OpenAiCompletionDatasetFormatter(DatasetFormatter):
    """
    Returns the Dataset in the OpenAI Completion Fine-tuning file format with two fields "prompt" and "completion".
    Field names can be customized because different systems have different expectations.
    https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset
    """

    def format(self, ds: Dataset, params: Dict[str, str]) -> Dataset:
        prompt_column = params.get("prompt_column", "prompt")
        completion_column = params.get("completion_column", "completion")
        stop = params.get("stop", "<STOP>")

        newds = ds.filter(
            lambda example: example["cot_answer"] and example["instruction"], desc="Filter out empty examples"
        )
        newds = newds.rename_columns(column_mapping={"instruction": prompt_column})
        newds = newds.map(
            lambda examples: {completion_column: [answer + stop for answer in examples["cot_answer"]]},
            batched=True,
            desc=f"Rename fields and add {stop} token",
        )
        return _remove_all_columns_but(newds, [prompt_column, completion_column])


class OpenAiChatDatasetFormatter(DatasetFormatter):
    """
    Returns the Dataset in the OpenAI Chat Fine-tuning file format with one field "messages".
    https://platform.openai.com/docs/guides/fine-tuning/preparing-your-dataset
    """

    def format(self, ds: Dataset, params: Dict[str, str]) -> Dataset:
        # First format as completion dataset
        completion_formatter = OpenAiCompletionDatasetFormatter()
        newds = completion_formatter.format(ds, params)

        prompt_column = params.get("prompt_column", "prompt")
        completion_column = params.get("completion_column", "completion")

        def format_messages(row):
            messages = []
            if "system_prompt" in params:
                system_prompt = params["system_prompt"]
                messages.append({"role": "system", "content": system_prompt})
            messages.extend(
                [
                    {"role": "user", "content": row[prompt_column]},
                    {"role": "assistant", "content": row[completion_column]},
                ]
            )
            chat_row = {"messages": messages}
            return chat_row

        newds = newds.map(format_messages)
        return _remove_all_columns_but(newds, ["messages"])


def extract_final_answer(cot_answer: str) -> Optional[str]:
    """
    Extracts the final answer from the cot_answer field

    Args:
        cot_answer (str): The chain-of-thought answer string

    Returns:
        Optional[str]: The extracted final answer or None if not found
    """
    if cot_answer:
        return cot_answer.split("<ANSWER>: ")[-1]
    return None


def extract_context(instruction: str) -> str:
    """
    Extracts the context from the instruction field.
    Keeps all <DOCUMENTS/> and removes the last line with the question.

    Args:
        instruction (str): The instruction string

    Returns:
        str: The extracted context
    """
    return "\n".join(instruction.split("\n")[:-1])


class EvalDatasetFormatter(DatasetFormatter):
    """
    Returns the Dataset in a format suitable for evaluation. Extracts final answer separates context from question.
    """

    def format(self, ds: Dataset, params: Dict[str, str]) -> Dataset:
        newds = ds.filter(
            lambda example: example["cot_answer"] and example["instruction"] and example["context"],
            desc="Filter out empty examples",
        )
        newds = newds.rename_columns({"context": "context_sentences"})
        newds = newds.map(
            lambda examples: {"gold_final_answer": [extract_final_answer(answer) for answer in examples["cot_answer"]]},
            batched=True,
        )
        keep_columns = ["question", "gold_final_answer", "context"]
        if "answer" in newds.column_names:
            # Add columns to the list without using list comprehension
            keep_columns.append("answer")
            keep_columns.append("final_answer")

            newds = newds.map(
                lambda examples: {"final_answer": [extract_final_answer(answer) for answer in examples["answer"]]},
                batched=True,
            )
        else:
            # Add a column with empty values initially, using the dataset length to create an empty list
            newds = newds.add_column("final_answer", [None] * len(newds))
            keep_columns.append("final_answer")

        newds = newds.map(
            lambda examples: {"context": [extract_context(instruction) for instruction in examples["instruction"]]},
            batched=True,
        )
        return _remove_all_columns_but(newds, keep_columns)


def append_extension(path: str, extension: str) -> str:
    """
    Appends the given extension to the file path if not already present.

    Args:
        path (str): The file path
        extension (str): The extension to append

    Returns:
        str: The file path with the appended extension
    """
    from pathlib import Path

    path_obj = Path(path)

    # If path is a directory, create a default filename
    if path_obj.is_dir():
        path_obj = path_obj / f"dataset.{extension}"
        return str(path_obj)

    suffix = "." + extension
    if not str(path_obj).endswith(suffix):
        path_obj = path_obj.with_suffix(suffix)
    return str(path_obj)


class JsonlDatasetExporter(DatasetExporter):
    """
    Exports the Dataset to a JSONL file
    """

    def export(self, ds: Dataset, output_path: str):
        ds.to_json(append_extension(output_path, "jsonl"))


class ParquetDatasetExporter(DatasetExporter):
    """
    Exports the Dataset to a Parquet file
    """

    def export(self, ds: Dataset, output_path: str):
        ds.to_parquet(append_extension(output_path, "parquet"))


def main():
    """
    When raft.py is executed from the command line.
    """

    log_setup()
    args = get_args()
    input_type = args.input_type

    # datasets except json when loading jsonl files
    if input_type == "jsonl":
        input_type = "json"

    logger = logging.getLogger("raft")
    # Load dataset from local files only - not from HuggingFace Hub
    ds = load_dataset(input_type, data_files={"train": args.input}, trust_remote_code=False)["train"]  # nosec B615
    logger.info(f"Dataset has {ds.num_rows} rows")
    formatter = DatasetConverter()

    if args.output_chat_system_prompt and args.output_format != "chat":
        raise Exception("Parameter --output-chat-system-prompt can only be used with --output-format chat")

    format_params = {}
    if args.output_chat_system_prompt:
        format_params["system_prompt"] = args.output_chat_system_prompt

    if args.output_format == "completion":
        format_params["prompt_column"] = args.output_completion_prompt_column
        format_params["completion_column"] = args.output_completion_completion_column
        format_params["stop"] = args.output_completion_stop

    # Also add these parameters for chat format
    if args.output_format == "chat":
        format_params["prompt_column"] = args.output_completion_prompt_column
        format_params["completion_column"] = args.output_completion_completion_column
        format_params["stop"] = args.output_completion_stop

    logger.info(
        f"Converting {args.input_type} file {args.input} to {args.output_type} {args.output_format} file {args.output}"
    )

    formatter.convert(
        ds=ds, format=args.output_format, output_path=args.output, output_type=args.output_type, params=format_params
    )


if __name__ == "__main__":
    main()
