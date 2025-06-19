"""
Tests for core models.
"""

import pytest

from raft_toolkit.core.models import DocumentChunk, ProcessingJob, ProcessingResult, QADataPoint, Question


@pytest.mark.unit
class TestDocumentChunk:
    """Test DocumentChunk model."""

    def test_create_basic(self):
        """Test basic chunk creation."""
        chunk = DocumentChunk.create(content="Test content", source="test.pdf")

        assert chunk.content == "Test content"
        assert chunk.source == "test.pdf"
        assert chunk.id is not None
        assert chunk.metadata == {}
        assert chunk.embedding is None

    def test_create_with_metadata(self):
        """Test chunk creation with metadata."""
        metadata = {"type": "pdf", "page": 1}
        chunk = DocumentChunk.create(content="Test content", source="test.pdf", metadata=metadata)

        assert chunk.metadata == metadata

    def test_create_with_embedding(self):
        """Test chunk creation with embedding."""
        embedding = [0.1, 0.2, 0.3]
        chunk = DocumentChunk.create(content="Test content", source="test.pdf", embedding=embedding)

        assert chunk.embedding == embedding


@pytest.mark.unit
class TestQuestion:
    """Test Question model."""

    def test_create_basic(self):
        """Test basic question creation."""
        question = Question.create("What is the capital?", "chunk_123")

        assert question.text == "What is the capital?"
        assert question.chunk_id == "chunk_123"
        assert question.id is not None

    def test_create_with_metadata(self):
        """Test question creation with metadata."""
        metadata = {"difficulty": "easy"}
        question = Question.create("What is the capital?", "chunk_123", metadata=metadata)

        assert question.metadata == metadata


@pytest.mark.unit
class TestQADataPoint:
    """Test QADataPoint model."""

    def test_create_basic(self):
        """Test basic QA data point creation."""
        qa_point = QADataPoint.create(
            question="What is the capital?",
            oracle_context="Paris is the capital of France.",
            distractor_contexts=["London is in England."],
            cot_answer="The capital is Paris.",
            doctype="pdf",
        )

        assert qa_point.question == "What is the capital?"
        assert qa_point.oracle_context == "Paris is the capital of France."
        assert qa_point.distractor_contexts == ["London is in England."]
        assert qa_point.cot_answer == "The capital is Paris."
        assert qa_point.doctype == "pdf"
        assert qa_point.id is not None

    def test_create_with_metadata(self):
        """Test QA data point creation with metadata."""
        metadata = {"source": "test.pdf"}
        qa_point = QADataPoint.create(
            question="What is the capital?",
            oracle_context="Paris is the capital of France.",
            distractor_contexts=[],
            cot_answer="The capital is Paris.",
            doctype="pdf",
            metadata=metadata,
        )

        assert qa_point.metadata == metadata

    def test_get_all_contexts(self):
        """Test getting all contexts."""
        qa_point = QADataPoint.create(
            question="What is the capital?",
            oracle_context="Paris is the capital of France.",
            distractor_contexts=["London is in England.", "Berlin is in Germany."],
            cot_answer="The capital is Paris.",
            doctype="pdf",
        )

        all_contexts = qa_point.get_all_contexts()

        assert len(all_contexts) == 3
        assert "Paris is the capital of France." in all_contexts
        assert "London is in England." in all_contexts
        assert "Berlin is in Germany." in all_contexts


@pytest.mark.unit
class TestProcessingJob:
    """Test ProcessingJob model."""

    def test_create_basic(self):
        """Test basic processing job creation."""
        chunk = DocumentChunk.create("Test content", "test.pdf")
        job = ProcessingJob.create(chunk=chunk, num_questions=5, num_distractors=3, include_oracle_probability=0.8)

        assert job.chunk == chunk
        assert job.num_questions == 5
        assert job.num_distractors == 3
        assert job.include_oracle_probability == 0.8
        assert job.id is not None

    def test_create_with_metadata(self):
        """Test processing job creation with metadata."""
        chunk = DocumentChunk.create("Test content", "test.pdf")
        metadata = {"priority": "high"}
        job = ProcessingJob.create(
            chunk=chunk, num_questions=5, num_distractors=3, include_oracle_probability=0.8, metadata=metadata
        )

        assert job.metadata == metadata


@pytest.mark.unit
class TestProcessingResult:
    """Test ProcessingResult model."""

    def test_create_success(self):
        """Test successful processing result."""
        qa_point = QADataPoint.create(
            question="What is the capital?",
            oracle_context="Paris is the capital of France.",
            distractor_contexts=[],
            cot_answer="The capital is Paris.",
            doctype="pdf",
        )

        result = ProcessingResult(
            job_id="job_123",
            success=True,
            qa_data_points=[qa_point],
            processing_time=1.5,
            token_usage={"total_tokens": 100},
        )

        assert result.job_id == "job_123"
        assert result.success is True
        assert len(result.qa_data_points) == 1
        assert result.processing_time == 1.5
        assert result.token_usage == {"total_tokens": 100}
        assert result.error is None

    def test_create_failure(self):
        """Test failed processing result."""
        result = ProcessingResult(
            job_id="job_123",
            success=False,
            qa_data_points=[],
            processing_time=0.5,
            token_usage={},
            error="Processing failed",
        )

        assert result.job_id == "job_123"
        assert result.success is False
        assert len(result.qa_data_points) == 0
        assert result.error == "Processing failed"
