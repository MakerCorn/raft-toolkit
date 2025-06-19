"""
Tests for dataset service.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.models import ProcessingResult, QADataPoint
from raft_toolkit.core.services.dataset_service import DatasetService


@pytest.mark.unit
class TestDatasetService:
    """Test DatasetService class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(
            datapath=Path("test.pdf"), output="output", openai_key="test-key", output_format="hf", output_type="jsonl"
        )

    @pytest.fixture
    def dataset_service(self, config):
        """Create DatasetService instance."""
        return DatasetService(config)

    @pytest.fixture
    def sample_qa_point(self):
        """Create sample QA data point."""
        return QADataPoint.create(
            question="What is the capital?",
            oracle_context="Paris is the capital of France.",
            distractor_contexts=["London is in England.", "Berlin is in Germany."],
            cot_answer="The capital is Paris.",
            doctype="pdf",
        )

    @pytest.fixture
    def sample_results(self, sample_qa_point):
        """Create sample processing results."""
        return [
            ProcessingResult(
                job_id="job1",
                success=True,
                qa_data_points=[sample_qa_point],
                processing_time=1.0,
                token_usage={"total_tokens": 100},
            )
        ]

    def test_init(self, dataset_service, config):
        """Test DatasetService initialization."""
        assert dataset_service.config == config

    def test_create_dataset_from_results(self, dataset_service, sample_results):
        """Test creating dataset from results."""
        dataset = dataset_service.create_dataset_from_results(sample_results)

        assert len(dataset) == 1
        assert "question" in dataset[0]
        assert "context" in dataset[0]
        assert "answer" in dataset[0]

    def test_save_dataset_jsonl(self, dataset_service, sample_results):
        """Test saving dataset as JSONL."""
        dataset = dataset_service.create_dataset_from_results(sample_results)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            output_path = f.name

        try:
            dataset_service.save_dataset(dataset, output_path)

            # Verify file was created and contains data
            with open(output_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 1
                data = json.loads(lines[0])
                assert "question" in data
        finally:
            Path(output_path).unlink()

    def test_format_hf(self, dataset_service, sample_qa_point):
        """Test HuggingFace format conversion."""
        formatted = dataset_service._format_hf(sample_qa_point)

        assert "question" in formatted
        assert "context" in formatted
        assert "answer" in formatted

    def test_format_completion(self, dataset_service, sample_qa_point):
        """Test completion format conversion."""
        formatted = dataset_service._format_completion(sample_qa_point)

        assert "prompt" in formatted
        assert "completion" in formatted

    def test_format_chat(self, dataset_service, sample_qa_point):
        """Test chat format conversion."""
        formatted = dataset_service._format_chat(sample_qa_point)

        assert "messages" in formatted
        assert len(formatted["messages"]) >= 2

    def test_format_eval(self, dataset_service, sample_qa_point):
        """Test evaluation format conversion."""
        formatted = dataset_service._format_eval(sample_qa_point)

        assert "question" in formatted
        assert "context" in formatted
        assert "gold_final_answer" in formatted

    def test_unsupported_format(self, dataset_service, sample_qa_point):
        """Test unsupported output format."""
        dataset_service.config.output_format = "unsupported"

        with pytest.raises(ValueError, match="Unsupported output format"):
            dataset_service._format_qa_point(sample_qa_point)

    def test_empty_results(self, dataset_service):
        """Test handling empty results."""
        dataset = dataset_service.create_dataset_from_results([])
        assert len(dataset) == 0
