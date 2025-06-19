"""
Tests for RAFT engine.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.models import ProcessingResult, QADataPoint
from raft_toolkit.core.raft_engine import RaftEngine


@pytest.mark.unit
class TestRaftEngine:
    """Test RaftEngine class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(datapath=Path("test.pdf"), output="output", openai_key="test-key", source_type="local")

    @pytest.fixture
    def mock_services(self):
        """Create mock services."""
        return {"llm_service": Mock(), "document_service": Mock(), "input_service": Mock(), "dataset_service": Mock()}

    @pytest.fixture
    def raft_engine(self, config, mock_services):
        """Create RaftEngine instance with mocked services."""
        with (
            patch("raft_toolkit.core.raft_engine.LLMService") as mock_llm,
            patch("raft_toolkit.core.raft_engine.DocumentService") as mock_doc,
            patch("raft_toolkit.core.raft_engine.InputService") as mock_input,
            patch("raft_toolkit.core.raft_engine.DatasetService") as mock_dataset,
        ):

            mock_llm.return_value = mock_services["llm_service"]
            mock_doc.return_value = mock_services["document_service"]
            mock_input.return_value = mock_services["input_service"]
            mock_dataset.return_value = mock_services["dataset_service"]

            return RaftEngine(config)

    def test_init(self, raft_engine, config):
        """Test RaftEngine initialization."""
        assert raft_engine.config == config
        assert raft_engine.llm_service is not None
        assert raft_engine.document_service is not None
        assert raft_engine.input_service is not None
        assert raft_engine.dataset_service is not None

    @pytest.mark.asyncio
    async def test_validate_input_source_success(self, raft_engine, mock_services):
        """Test successful input source validation."""
        mock_services["input_service"].validate_source = AsyncMock()

        await raft_engine.validate_input_source()

        mock_services["input_service"].validate_source.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_input_source_failure(self, raft_engine, mock_services):
        """Test input source validation failure."""
        from raft_toolkit.core.sources import SourceValidationError

        mock_services["input_service"].validate_source = AsyncMock(
            side_effect=SourceValidationError("Validation failed")
        )

        with pytest.raises(SourceValidationError):
            await raft_engine.validate_input_source()

    @pytest.mark.asyncio
    async def test_get_processing_preview_async(self, raft_engine, mock_services):
        """Test async processing preview."""
        expected_preview = {"estimated_chunks": 10, "estimated_qa_points": 50}
        mock_services["input_service"].get_processing_preview = AsyncMock(return_value=expected_preview)

        result = await raft_engine.get_processing_preview_async()

        assert result == expected_preview

    def test_generate_dataset_sync(self, raft_engine):
        """Test synchronous dataset generation."""
        with patch.object(raft_engine, "generate_dataset_async") as mock_async:
            mock_async.return_value = {"total_qa_points": 10}

            result = raft_engine.generate_dataset()

            assert result == {"total_qa_points": 10}

    @pytest.mark.asyncio
    async def test_generate_dataset_async_success(self, raft_engine, mock_services):
        """Test successful async dataset generation."""
        # Setup mocks
        mock_services["input_service"].validate_source = AsyncMock()
        mock_services["input_service"].process_documents = AsyncMock(return_value=[Mock()])  # Mock chunks

        sample_qa = QADataPoint.create(
            question="Test?", oracle_context="Context", distractor_contexts=[], cot_answer="Answer", doctype="pdf"
        )

        mock_result = ProcessingResult(
            job_id="test",
            success=True,
            qa_data_points=[sample_qa],
            processing_time=1.0,
            token_usage={"total_tokens": 100},
        )

        mock_services["llm_service"].process_chunks_batch.return_value = [mock_result]
        mock_services["llm_service"].get_rate_limit_statistics.return_value = {}
        mock_services["dataset_service"].create_dataset_from_results.return_value = [{}]
        mock_services["dataset_service"].save_dataset.return_value = None

        result = await raft_engine.generate_dataset_async()

        assert "total_qa_points" in result
        assert "successful_chunks" in result
        assert "total_processing_time" in result

    def test_validate_inputs_local(self, raft_engine, tmp_path):
        """Test local input validation."""
        # Create a test file
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")

        # Update the config to point to the test file
        raft_engine.config.datapath = test_file

        raft_engine.validate_inputs(test_file)
        # Should not raise exception

    def test_validate_inputs_nonexistent_file(self, raft_engine):
        """Test validation with nonexistent file."""
        with pytest.raises(FileNotFoundError):
            raft_engine.validate_inputs(Path("nonexistent.pdf"))

    def test_validate_inputs_wrong_extension(self, raft_engine, tmp_path):
        """Test validation with wrong file extension."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="File extension does not match doctype"):
            raft_engine.validate_inputs(test_file)

    def test_get_processing_preview_local(self, raft_engine, tmp_path):
        """Test processing preview for local files."""
        # Create test files
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")

        preview = raft_engine.get_processing_preview(test_file)

        assert "input_path" in preview
        assert "estimated_chunks" in preview
        assert "estimated_qa_points" in preview

    def test_calculate_stats(self, raft_engine, mock_services):
        """Test statistics calculation."""
        sample_qa = QADataPoint.create(
            question="Test?", oracle_context="Context", distractor_contexts=[], cot_answer="Answer", doctype="pdf"
        )

        results = [
            ProcessingResult(
                job_id="test1",
                success=True,
                qa_data_points=[sample_qa],
                processing_time=1.0,
                token_usage={"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
            ),
            ProcessingResult(job_id="test2", success=False, qa_data_points=[], processing_time=0.5, token_usage={}),
        ]

        mock_services["llm_service"].get_rate_limit_statistics.return_value = {}
        mock_services["input_service"].get_source_info.return_value = {}

        stats = raft_engine._calculate_stats(results, 2.0)

        assert stats["total_qa_points"] == 1
        assert stats["successful_chunks"] == 1
        assert stats["failed_chunks"] == 1
        assert stats["total_processing_time"] == 2.0
        assert stats["token_usage"]["total_tokens"] == 100
