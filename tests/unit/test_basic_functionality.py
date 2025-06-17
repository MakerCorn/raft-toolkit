"""
Basic functionality tests to ensure core components work.
"""

import tempfile
from pathlib import Path

import pytest

from core.config import RaftConfig
from core.models import DocumentChunk, ProcessingResult, QADataPoint


class TestBasicFunctionality:
    """Test basic functionality that should always work."""

    def test_config_creation(self):
        """Test basic configuration creation."""
        config = RaftConfig(datapath="test.txt", openai_key="test-key")

        assert str(config.datapath) == "test.txt"
        assert config.openai_key == "test-key"
        assert config.questions > 0
        assert config.distractors >= 0

    def test_document_chunk_creation(self):
        """Test document chunk model creation."""
        chunk = DocumentChunk(
            id="test-chunk-1", content="This is test content", source="test.txt", metadata={"chunk_id": 1}
        )

        assert chunk.id == "test-chunk-1"
        assert chunk.content == "This is test content"
        assert chunk.source == "test.txt"
        assert chunk.metadata["chunk_id"] == 1
        assert chunk.embedding is None

    def test_processing_result_creation(self):
        """Test processing result model creation."""
        result = ProcessingResult(
            job_id="test-job",
            success=True,
            qa_data_points=[
                QADataPoint(
                    id="qa1",
                    type="pdf",
                    question="Q?",
                    context="C",
                    oracle_context="Oracle context",
                    cot_answer="A.",
                    instruction="Answer the question",
                )
            ],
            processing_time=1.0,
            token_usage={"total": 100},
        )

        assert result.job_id == "test-job"
        assert result.success is True
        assert len(result.qa_data_points) == 1
        assert result.processing_time == 1.0
        assert result.token_usage["total"] == 100

    def test_config_validation_basic(self):
        """Test basic configuration validation."""
        # Valid config should not raise exception
        config = RaftConfig(datapath="test.txt", openai_key="test-key", doctype="txt")

        # Should have reasonable defaults
        assert config.chunk_size > 0
        assert config.workers > 0
        assert config.completion_model is not None

    def test_config_defaults(self):
        """Test configuration defaults are reasonable."""
        config = RaftConfig(datapath="test.txt", openai_key="test-key")

        # Test defaults
        assert config.questions >= 1
        assert config.distractors >= 0
        assert config.chunk_size > 0
        assert config.workers >= 1
        assert 0.0 <= config.p <= 1.0
        assert config.output_format in ["hf", "completion", "chat"]
        assert config.output_type in ["jsonl", "parquet"]
        assert config.chunking_strategy in ["semantic", "fixed", "sentence"]

    def test_document_chunk_with_embedding(self):
        """Test document chunk with embedding."""
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        chunk = DocumentChunk(
            id="test-chunk-2",
            content="Test content with embedding",
            source="test.txt",
            metadata={},
            embedding=embedding,
        )

        assert chunk.embedding == embedding
        assert len(chunk.embedding) == 5

    def test_processing_result_failure(self):
        """Test processing result for failed processing."""
        result = ProcessingResult(
            job_id="failed-job",
            success=False,
            qa_data_points=[],
            processing_time=0.5,
            token_usage={},
            error="Processing failed",
        )

        assert result.success is False
        assert len(result.qa_data_points) == 0
        assert result.error == "Processing failed"

    def test_config_with_different_doctypes(self):
        """Test configuration with different document types."""
        doctypes = ["pdf", "txt", "json", "api", "pptx"]

        for doctype in doctypes:
            config = RaftConfig(datapath=f"test.{doctype}", openai_key="test-key", doctype=doctype)
            assert config.doctype == doctype

    def test_config_with_different_output_formats(self):
        """Test configuration with different output formats."""
        formats = ["hf", "completion", "chat"]

        for fmt in formats:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", output_format=fmt)
            assert config.output_format == fmt

    def test_config_with_chunking_strategies(self):
        """Test configuration with different chunking strategies."""
        strategies = ["semantic", "fixed", "sentence"]

        for strategy in strategies:
            config = RaftConfig(datapath="test.txt", openai_key="test-key", chunking_strategy=strategy)
            assert config.chunking_strategy == strategy

    def test_document_chunk_create_method(self):
        """Test document chunk creation using class method."""
        chunk = DocumentChunk.create(
            content="Test content created with class method", source="test.txt", metadata={"chunk_id": 1}
        )

        assert chunk.content == "Test content created with class method"
        assert chunk.source == "test.txt"
        assert chunk.metadata["chunk_id"] == 1
        assert chunk.id is not None  # Should have generated ID
        assert len(chunk.id) > 0

    def test_models_string_representation(self):
        """Test string representation of models."""
        chunk = DocumentChunk(id="test-chunk-3", content="Test content", source="test.txt", metadata={})

        # Should have string representation
        str_repr = str(chunk)
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_processing_result_statistics(self):
        """Test processing result with statistics."""
        result = ProcessingResult(
            job_id="stats-job",
            success=True,
            qa_data_points=[
                QADataPoint(
                    id="qa1",
                    type="pdf",
                    question="Q1?",
                    context="C1",
                    oracle_context="Oracle 1",
                    cot_answer="A1.",
                    instruction="Answer the question",
                ),
                QADataPoint(
                    id="qa2",
                    type="pdf",
                    question="Q2?",
                    context="C2",
                    oracle_context="Oracle 2",
                    cot_answer="A2.",
                    instruction="Answer the question",
                ),
            ],
            processing_time=2.5,
            token_usage={"prompt": 50, "completion": 75, "total": 125},
        )

        assert len(result.qa_data_points) == 2
        assert result.token_usage["prompt"] == 50
        assert result.token_usage["completion"] == 75
        assert result.token_usage["total"] == 125

    def test_config_parameter_types(self):
        """Test configuration parameter types."""
        config = RaftConfig(
            datapath="test.txt", openai_key="test-key", questions=5, distractors=3, chunk_size=512, workers=4, p=0.8
        )

        # Test types
        assert isinstance(config.questions, int)
        assert isinstance(config.distractors, int)
        assert isinstance(config.chunk_size, int)
        assert isinstance(config.workers, int)
        assert isinstance(config.p, (int, float))
        assert isinstance(config.datapath, (str, Path))
        assert isinstance(config.openai_key, str)
