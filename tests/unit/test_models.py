"""
Tests for core.models module.
"""

from datetime import datetime
from uuid import UUID

import pytest

from core.models import ChunkingStrategy, DocType, DocumentChunk, JobStatus, OutputFormat, ProcessingResult, QADataPoint


@pytest.mark.unit
class TestDocumentChunk:
    """Test DocumentChunk model."""

    @pytest.mark.unit
    def test_document_chunk_creation(self):
        """Test basic document chunk creation."""
        chunk = DocumentChunk.create(content="Test content", source="test.pdf", metadata={"type": "pdf"})

        assert chunk.content == "Test content"
        assert chunk.source == "test.pdf"
        assert chunk.metadata == {"type": "pdf"}
        assert isinstance(chunk.id, str)
        assert isinstance(chunk.created_at, datetime)
        assert len(chunk.id) > 0

    @pytest.mark.unit
    def test_document_chunk_with_custom_id(self):
        """Test document chunk creation with custom ID."""
        custom_id = "custom-chunk-id"
        chunk = DocumentChunk.create(content="Test content", source="test.pdf", chunk_id=custom_id)

        assert chunk.id == custom_id

    @pytest.mark.unit
    def test_document_chunk_serialization(self):
        """Test document chunk serialization."""
        chunk = DocumentChunk.create(content="Test content", source="test.pdf", metadata={"type": "pdf", "page": 1})

        data = chunk.to_dict()

        assert data["content"] == "Test content"
        assert data["source"] == "test.pdf"
        assert data["metadata"]["type"] == "pdf"
        assert data["metadata"]["page"] == 1
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.unit
    def test_document_chunk_from_dict(self):
        """Test document chunk deserialization."""
        data = {
            "id": "test-id",
            "content": "Test content",
            "source": "test.pdf",
            "metadata": {"type": "pdf"},
            "created_at": datetime.now().isoformat(),
        }

        chunk = DocumentChunk.from_dict(data)

        assert chunk.id == "test-id"
        assert chunk.content == "Test content"
        assert chunk.source == "test.pdf"
        assert chunk.metadata == {"type": "pdf"}
        assert isinstance(chunk.created_at, datetime)


@pytest.mark.unit
class TestQADataPoint:
    """Test QADataPoint model."""

    @pytest.mark.unit
    def test_qa_datapoint_creation(self):
        """Test basic QA data point creation."""
        qa_point = QADataPoint(
            id="test-qa-1",
            type="cot",
            question="What is AI?",
            context="Context about AI",
            oracle_context="Oracle context about AI",
            cot_answer="AI is artificial intelligence.",
            instruction="Answer the question.",
        )

        assert qa_point.id == "test-qa-1"
        assert qa_point.type == "cot"
        assert qa_point.question == "What is AI?"
        assert qa_point.context == "Context about AI"
        assert qa_point.oracle_context == "Oracle context about AI"
        assert qa_point.cot_answer == "AI is artificial intelligence."
        assert qa_point.instruction == "Answer the question."

    @pytest.mark.unit
    def test_qa_datapoint_serialization(self):
        """Test QA data point serialization."""
        qa_point = QADataPoint(
            id="test-qa-1",
            type="cot",
            question="What is AI?",
            context="Context about AI",
            oracle_context="Oracle context about AI",
            cot_answer="AI is artificial intelligence.",
            instruction="Answer the question.",
        )

        data = qa_point.to_dict()

        assert data["id"] == "test-qa-1"
        assert data["type"] == "cot"
        assert data["question"] == "What is AI?"
        assert data["context"] == "Context about AI"
        assert data["oracle_context"] == "Oracle context about AI"
        assert data["cot_answer"] == "AI is artificial intelligence."
        assert data["instruction"] == "Answer the question."

    @pytest.mark.unit
    def test_qa_datapoint_from_dict(self):
        """Test QA data point deserialization."""
        data = {
            "id": "test-qa-1",
            "type": "cot",
            "question": "What is AI?",
            "context": "Context about AI",
            "oracle_context": "Oracle context about AI",
            "cot_answer": "AI is artificial intelligence.",
            "instruction": "Answer the question.",
        }

        qa_point = QADataPoint.from_dict(data)

        assert qa_point.id == "test-qa-1"
        assert qa_point.type == "cot"
        assert qa_point.question == "What is AI?"
        assert qa_point.context == "Context about AI"


@pytest.mark.unit
class TestProcessingResult:
    """Test ProcessingResult model."""

    @pytest.mark.unit
    def test_processing_result_success(self):
        """Test successful processing result."""
        qa_points = [
            QADataPoint(
                id="qa-1",
                type="cot",
                question="Test question",
                context="Test context",
                oracle_context="Test oracle",
                cot_answer="Test answer",
                instruction="Test instruction",
            )
        ]

        result = ProcessingResult(
            job_id="job-1",
            success=True,
            qa_data_points=qa_points,
            processing_time=1.5,
            token_usage={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
        )

        assert result.job_id == "job-1"
        assert result.success is True
        assert len(result.qa_data_points) == 1
        assert result.qa_data_points[0].id == "qa-1"
        assert result.processing_time == 1.5
        assert result.token_usage["total_tokens"] == 100
        assert result.error is None

    @pytest.mark.unit
    def test_processing_result_failure(self):
        """Test failed processing result."""
        result = ProcessingResult(
            job_id="job-2", success=False, error="Processing failed due to API error", processing_time=0.5
        )

        assert result.job_id == "job-2"
        assert result.success is False
        assert result.error == "Processing failed due to API error"
        assert result.qa_data_points == []
        assert result.processing_time == 0.5
        assert result.token_usage == {}

    @pytest.mark.unit
    def test_processing_result_serialization(self):
        """Test processing result serialization."""
        result = ProcessingResult(job_id="job-1", success=True, processing_time=1.5, token_usage={"total_tokens": 100})

        data = result.to_dict()

        assert data["job_id"] == "job-1"
        assert data["success"] is True
        assert data["processing_time"] == 1.5
        assert data["token_usage"]["total_tokens"] == 100
        assert "qa_data_points" in data


@pytest.mark.unit
class TestEnums:
    """Test enum types."""

    @pytest.mark.unit
    def test_doc_type_enum(self):
        """Test DocType enum."""
        assert DocType.PDF.value == "pdf"
        assert DocType.TXT.value == "txt"
        assert DocType.JSON.value == "json"
        assert DocType.API.value == "api"
        assert DocType.PPTX.value == "pptx"

    @pytest.mark.unit
    def test_chunking_strategy_enum(self):
        """Test ChunkingStrategy enum."""
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.FIXED.value == "fixed"
        assert ChunkingStrategy.SENTENCE.value == "sentence"

    @pytest.mark.unit
    def test_output_format_enum(self):
        """Test OutputFormat enum."""
        assert OutputFormat.HF.value == "hf"
        assert OutputFormat.COMPLETION.value == "completion"
        assert OutputFormat.CHAT.value == "chat"
        assert OutputFormat.EVAL.value == "eval"

    @pytest.mark.unit
    def test_job_status_enum(self):
        """Test JobStatus enum."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
