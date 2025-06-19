"""
Dataset service for formatting and exporting datasets.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Literal

try:
    import datasets
    from datasets import Dataset
except ImportError:
    datasets = None
    Dataset = None

try:
    import pyarrow as pa
except ImportError:
    pa = None

from ..config import RaftConfig
from ..models import ProcessingResult

# Define type aliases
DatasetFormat = Literal["hf", "completion", "chat", "eval"]
OutputDatasetType = Literal["parquet", "jsonl"]


# Define a base class for the converter
class DatasetConverterBase:
    def convert(self, **kwargs: Any) -> None:
        pass


# Try to import the real implementation
try:
    from ..formatters.dataset_converter import DatasetConverter
except ImportError:
    # Mock implementation for demo
    class DatasetConverter(DatasetConverterBase):  # type: ignore[no-redef]
        def convert(self, **kwargs: Any) -> None:
            pass


logger = logging.getLogger(__name__)


class DatasetService:
    """Service for dataset creation, formatting, and export."""

    def __init__(self, config: RaftConfig):
        self.config = config
        self.converter = DatasetConverter()

    def create_dataset_from_results(self, results: List[ProcessingResult]) -> Dataset:
        """Create HuggingFace dataset from processing results."""
        all_qa_points = []

        for result in results:
            if result.success:
                all_qa_points.extend(result.qa_data_points)
            else:
                logger.warning(f"Skipping failed result for job {result.job_id}: {result.error}")

        if not all_qa_points:
            # Return empty dataset instead of raising error
            empty_records: List[Dict[str, Any]] = []
            if pa is None or Dataset is None:
                # Mock empty dataset
                class EmptyDataset:
                    def __len__(self):
                        return 0

                return EmptyDataset()
            table = pa.Table.from_pylist(empty_records)
            dataset = Dataset(table)
            logger.info("Created empty dataset - no successful QA data points")
            return dataset

        # Convert QA data points to dictionary format
        data_records = []
        for qa_point in all_qa_points:
            record = {
                "id": qa_point.id,
                "type": qa_point.type,
                "question": qa_point.question,
                "context": qa_point.context,
                "oracle_context": qa_point.oracle_context,
                "cot_answer": qa_point.cot_answer,
                "answer": qa_point.cot_answer,  # Add 'answer' field for compatibility
                "instruction": qa_point.instruction,
            }
            data_records.append(record)

        # Create PyArrow table and Dataset
        table = pa.Table.from_pylist(data_records)
        dataset = Dataset(table)

        logger.info(f"Created dataset with {len(dataset)} records")
        return dataset

    def save_dataset(self, dataset: Dataset, output_path: str) -> None:
        """Save dataset in multiple formats."""
        output_path = str(Path(output_path).absolute())

        # Save as HuggingFace dataset (arrow format)
        dataset.save_to_disk(output_path)
        logger.info(f"Saved HuggingFace dataset to {output_path}")

        # Convert and save in specified format
        format_params = self._get_format_params()

        # Cast string values to the expected types
        output_format = self.config.output_format
        output_type = self.config.output_type

        # Validate format and type against allowed values
        if output_format not in ["hf", "completion", "chat", "eval"]:
            logger.warning(f"Invalid output format: {output_format}, defaulting to 'hf'")
            output_format = "hf"

        if output_type not in ["parquet", "jsonl"]:
            logger.warning(f"Invalid output type: {output_type}, defaulting to 'jsonl'")
            output_type = "jsonl"

        # Use type assertions to satisfy mypy
        format_val: DatasetFormat = output_format  # type: ignore
        type_val: OutputDatasetType = output_type  # type: ignore

        self.converter.convert(
            ds=dataset,
            format=format_val,
            output_path=output_path,
            output_type=type_val,
            params=format_params,
        )

        logger.info(f"Converted and saved dataset in {self.config.output_format} format as {self.config.output_type}")

    def _get_format_params(self) -> Dict[str, Any]:
        """Get format-specific parameters."""
        params = {}

        if self.config.output_chat_system_prompt:
            params["system_prompt"] = self.config.output_chat_system_prompt

        if self.config.output_format == "completion":
            params["prompt_column"] = self.config.output_completion_prompt_column
            params["completion_column"] = self.config.output_completion_completion_column

        return params

    def load_dataset(self, input_path: str) -> Dataset:
        """Load dataset from disk."""
        return Dataset.load_from_disk(input_path)

    def get_dataset_stats(self, dataset: Dataset) -> Dict[str, Any]:
        """Get statistics about the dataset."""
        stats = {
            "total_records": len(dataset),
            "columns": list(dataset.column_names),
            "sample_record": dataset[0] if len(dataset) > 0 else None,
        }

        # Type distribution
        if "type" in dataset.column_names:
            type_counts: Dict[str, int] = {}
            for record_type in dataset["type"]:
                type_counts[record_type] = type_counts.get(record_type, 0) + 1
            stats["type_distribution"] = type_counts

        return stats

    def _format_qa_point(self, qa_point: Any) -> Dict[str, Any]:
        """Format QA point based on output format."""
        if self.config.output_format == "hf":
            return self._format_hf(qa_point)
        elif self.config.output_format == "completion":
            return self._format_completion(qa_point)
        elif self.config.output_format == "chat":
            return self._format_chat(qa_point)
        elif self.config.output_format == "eval":
            return self._format_eval(qa_point)
        else:
            raise ValueError(f"Unsupported output format: {self.config.output_format}")

    def _format_hf(self, qa_point: Any) -> Dict[str, Any]:
        """Format as HuggingFace dataset record."""
        return {
            "id": qa_point.id,
            "question": qa_point.question,
            "context": qa_point.context,
            "answer": qa_point.cot_answer,
            "oracle_context": qa_point.oracle_context,
            "instruction": qa_point.instruction,
        }

    def _format_completion(self, qa_point: Any) -> Dict[str, Any]:
        """Format as completion dataset record."""
        prompt = f"Context: {qa_point.context}\n\nQuestion: {qa_point.question}\n\nAnswer:"
        return {
            "prompt": prompt,
            "completion": qa_point.cot_answer,
        }

    def _format_chat(self, qa_point: Any) -> Dict[str, Any]:
        """Format as chat dataset record."""
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on provided context.",
            },
            {"role": "user", "content": f"Context: {qa_point.context}\n\nQuestion: {qa_point.question}"},
            {"role": "assistant", "content": qa_point.cot_answer},
        ]
        return {"messages": messages}

    def _format_eval(self, qa_point: Any) -> Dict[str, Any]:
        """Format as evaluation dataset record."""
        return {
            "question": qa_point.question,
            "context": qa_point.context,
            "gold_final_answer": qa_point.cot_answer,
            "oracle_context": qa_point.oracle_context,
        }
