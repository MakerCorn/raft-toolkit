"""
Unit tests for dataset formatters.
"""

import json
import tempfile
from pathlib import Path

import pytest
from datasets import Dataset

from raft_toolkit.core.formatters.dataset_converter import (
    DatasetConverter,
    EvalDatasetFormatter,
    HuggingFaceDatasetFormatter,
    JsonlDatasetExporter,
    OpenAiChatDatasetFormatter,
    OpenAiCompletionDatasetFormatter,
    ParquetDatasetExporter,
    append_extension,
    extract_context,
    extract_final_answer,
)
from raft_toolkit.core.models import QADataPoint


class TestDatasetConverter:
    """Test dataset converter functionality."""

    @pytest.fixture
    def sample_dataset(self):
        """Create sample HuggingFace dataset."""
        data = {
            "question": ["What is machine learning?", "What is deep learning?"],
            "context": [
                "Machine learning is a method of data analysis that automates analytical model building.",
                "Deep learning uses neural networks with multiple layers to model data.",
            ],
            "cot_answer": [
                "Machine learning is a subset of artificial intelligence.<ANSWER>: AI subset",
                "Deep learning is a subset of machine learning.<ANSWER>: ML subset",
            ],
            "instruction": [
                "Context: Machine learning context\nQuestion: What is machine learning?",
                "Context: Deep learning context\nQuestion: What is deep learning?",
            ],
        }
        return Dataset.from_dict(data)

    def test_converter_initialization(self):
        """Test converter initialization."""
        converter = DatasetConverter()

        assert "hf" in converter.formats
        assert "completion" in converter.formats
        assert "chat" in converter.formats
        assert "eval" in converter.formats
        assert "jsonl" in converter.exporters
        assert "parquet" in converter.exporters

    def test_convert_to_hf_format(self, sample_dataset):
        """Test conversion to HuggingFace format."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            converter.convert(ds=sample_dataset, format="hf", output_path=output_path, output_type="jsonl", params={})

            # Verify file was created (append_extension adds .jsonl)
            assert Path(output_path + ".jsonl").exists()

        finally:
            if Path(output_path + ".jsonl").exists():
                Path(output_path + ".jsonl").unlink()

    def test_convert_to_completion_format(self, sample_dataset):
        """Test conversion to OpenAI completion format."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            converter.convert(
                ds=sample_dataset,
                format="completion",
                output_path=output_path,
                output_type="jsonl",
                params={"prompt_column": "prompt", "completion_column": "completion", "stop": "<STOP>"},
            )

            # Verify file was created (append_extension adds .jsonl)
            assert Path(output_path + ".jsonl").exists()

        finally:
            if Path(output_path + ".jsonl").exists():
                Path(output_path + ".jsonl").unlink()

    def test_convert_to_chat_format(self, sample_dataset):
        """Test conversion to OpenAI chat format."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            converter.convert(
                ds=sample_dataset,
                format="chat",
                output_path=output_path,
                output_type="jsonl",
                params={
                    "system_prompt": "You are a helpful assistant.",
                    "prompt_column": "prompt",
                    "completion_column": "completion",
                    "stop": "<STOP>",
                },
            )

            # Verify file was created (append_extension adds .jsonl)
            assert Path(output_path + ".jsonl").exists()

        finally:
            if Path(output_path + ".jsonl").exists():
                Path(output_path + ".jsonl").unlink()

    def test_convert_to_parquet(self, sample_dataset):
        """Test conversion to Parquet format."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            converter.convert(ds=sample_dataset, format="hf", output_path=output_path, output_type="parquet", params={})

            # Verify file was created (append_extension adds .parquet)
            assert Path(output_path + ".parquet").exists()
            assert Path(output_path + ".parquet").stat().st_size > 0

        except ImportError:
            # Parquet support might not be available
            pytest.skip("Parquet support not available")
        finally:
            if Path(output_path + ".parquet").exists():
                Path(output_path + ".parquet").unlink()

    def test_invalid_format(self, sample_dataset):
        """Test handling of invalid format."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(Exception, match="Output Format invalid_format is not supported"):
                converter.convert(
                    ds=sample_dataset, format="invalid_format", output_path=output_path, output_type="jsonl", params={}
                )
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()

    def test_invalid_output_type(self, sample_dataset):
        """Test handling of invalid output type."""
        converter = DatasetConverter()

        with tempfile.NamedTemporaryFile(suffix=".invalid", delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(Exception, match="Output Type invalid_type is not supported"):
                converter.convert(
                    ds=sample_dataset, format="hf", output_path=output_path, output_type="invalid_type", params={}
                )
        finally:
            if Path(output_path).exists():
                Path(output_path).unlink()


class TestDatasetFormatters:
    """Test individual dataset formatters."""

    @pytest.fixture
    def sample_dataset(self):
        """Create sample HuggingFace dataset."""
        data = {
            "question": ["What is AI?", "What is ML?"],
            "context": ["AI context", "ML context"],
            "cot_answer": ["AI answer<ANSWER>: AI", "ML answer<ANSWER>: ML"],
            "instruction": ["Context: AI info\nQuestion: What is AI?", "Context: ML info\nQuestion: What is ML?"],
        }
        return Dataset.from_dict(data)

    def test_huggingface_formatter(self, sample_dataset):
        """Test HuggingFace formatter."""
        formatter = HuggingFaceDatasetFormatter()
        result = formatter.format(sample_dataset, {})

        # Should return dataset unchanged
        assert result == sample_dataset
        assert "question" in result.column_names
        assert "context" in result.column_names

    def test_completion_formatter(self, sample_dataset):
        """Test OpenAI completion formatter."""
        formatter = OpenAiCompletionDatasetFormatter()
        params = {"prompt_column": "prompt", "completion_column": "completion", "stop": "<STOP>"}
        result = formatter.format(sample_dataset, params)

        assert "prompt" in result.column_names
        assert "completion" in result.column_names
        assert len(result.column_names) == 2

    def test_chat_formatter(self, sample_dataset):
        """Test OpenAI chat formatter."""
        formatter = OpenAiChatDatasetFormatter()
        params = {
            "system_prompt": "You are helpful.",
            "prompt_column": "prompt",
            "completion_column": "completion",
            "stop": "<STOP>",
        }
        result = formatter.format(sample_dataset, params)

        assert "messages" in result.column_names
        assert len(result.column_names) == 1

        # Check message structure
        messages = result[0]["messages"]
        assert isinstance(messages, list)
        assert any(msg["role"] == "system" for msg in messages)
        assert any(msg["role"] == "user" for msg in messages)
        assert any(msg["role"] == "assistant" for msg in messages)

    def test_eval_formatter(self, sample_dataset):
        """Test evaluation formatter."""
        formatter = EvalDatasetFormatter()
        result = formatter.format(sample_dataset, {})

        assert "question" in result.column_names
        assert "gold_final_answer" in result.column_names
        assert "context" in result.column_names
        assert "final_answer" in result.column_names


class TestUtilityFunctions:
    """Test utility functions."""

    def test_extract_final_answer(self):
        """Test final answer extraction."""
        cot_answer = "This is reasoning.<ANSWER>: Final answer"
        result = extract_final_answer(cot_answer)
        assert result == "Final answer"

        # Test with no answer tag
        result = extract_final_answer("Just reasoning")
        assert result == "Just reasoning"

        # Test with None
        result = extract_final_answer(None)
        assert result is None

    def test_extract_context(self):
        """Test context extraction."""
        instruction = "Context line 1\nContext line 2\nQuestion: What is this?"
        result = extract_context(instruction)
        assert result == "Context line 1\nContext line 2"

        # Test single line
        instruction = "Single question?"
        result = extract_context(instruction)
        assert result == ""

    def test_append_extension(self):
        """Test extension appending."""
        # Test adding extension
        result = append_extension("file", "txt")
        assert result == "file.txt"

        # Test when extension already exists
        result = append_extension("file.txt", "txt")
        assert result == "file.txt"

        # Test different extension
        result = append_extension("file.json", "txt")
        assert result == "file.json.txt"


class TestExporters:
    """Test dataset exporters."""

    @pytest.fixture
    def sample_dataset(self):
        """Create sample dataset for export testing."""
        data = {"test_col": ["value1", "value2"]}
        return Dataset.from_dict(data)

    def test_jsonl_exporter(self, sample_dataset):
        """Test JSONL exporter."""
        exporter = JsonlDatasetExporter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_dataset, output_path)

            # Verify file was created (append_extension adds .jsonl)
            final_path = output_path + ".jsonl"
            assert Path(final_path).exists()

            # Verify content
            with open(final_path, "r") as f:
                lines = f.readlines()
                assert len(lines) == 2
                for line in lines:
                    data = json.loads(line.strip())
                    assert "test_col" in data

        finally:
            final_path = output_path + ".jsonl"
            if Path(final_path).exists():
                Path(final_path).unlink()

    def test_parquet_exporter(self, sample_dataset):
        """Test Parquet exporter."""
        exporter = ParquetDatasetExporter()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            output_path = f.name

        try:
            exporter.export(sample_dataset, output_path)

            # Verify file was created (append_extension adds .parquet)
            final_path = output_path + ".parquet"
            assert Path(final_path).exists()
            assert Path(final_path).stat().st_size > 0

        except ImportError:
            pytest.skip("Parquet support not available")
        finally:
            final_path = output_path + ".parquet"
            if Path(final_path).exists():
                Path(final_path).unlink()
