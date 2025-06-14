"""
Dataset service for formatting and exporting datasets.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

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
from ..models import ProcessingResult, QADataPoint

try:
    from ..formatters import DatasetConverter
except ImportError:
    # Mock implementation for demo
    class DatasetConverter:
        def convert(self, **kwargs):
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
            raise ValueError("No successful QA data points to create dataset")

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
        output_path = Path(output_path).absolute()

        # Save as HuggingFace dataset (arrow format)
        dataset.save_to_disk(str(output_path))
        logger.info(f"Saved HuggingFace dataset to {output_path}")

        # Convert and save in specified format
        format_params = self._get_format_params()

        self.converter.convert(
            ds=dataset,
            format=self.config.output_format,
            output_path=str(output_path),
            output_type=self.config.output_type,
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
            type_counts = {}
            for record_type in dataset["type"]:
                type_counts[record_type] = type_counts.get(record_type, 0) + 1
            stats["type_distribution"] = type_counts

        return stats
