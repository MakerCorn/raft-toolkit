"""
Tests for input service.
"""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.services.input_service import InputService


@pytest.mark.unit
class TestInputService:
    """Test InputService class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(
            datapath=Path("test.pdf"),
            output="output",
            openai_key="test-key",
            source_type="local",
            source_uri="test_path",
        )

    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        return Mock()

    @pytest.fixture
    def mock_input_source(self):
        """Create mock input source."""
        mock_source = Mock()
        mock_source.validate = AsyncMock()
        mock_source.get_processing_preview = AsyncMock(
            return_value={"total_documents": 5, "supported_documents": 4, "unsupported_documents": 1}
        )
        mock_source.list_documents = AsyncMock(return_value=[])
        return mock_source

    @pytest.fixture
    def input_service(self, config, mock_llm_service, mock_input_source):
        """Create InputService instance."""
        with (
            patch("raft_toolkit.core.services.input_service.DocumentService"),
            patch("raft_toolkit.core.services.input_service.InputSourceFactory.create_source") as mock_factory,
        ):

            mock_factory.return_value = mock_input_source
            service = InputService(config, mock_llm_service)
            service.input_source = mock_input_source
            return service

    def test_init(self, input_service, config, mock_llm_service):
        """Test InputService initialization."""
        assert input_service.config == config
        assert input_service.llm_service == mock_llm_service

    @pytest.mark.asyncio
    async def test_validate_source_success(self, input_service, mock_input_source):
        """Test successful source validation."""
        await input_service.validate_source()
        mock_input_source.validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_source_failure(self, input_service, mock_input_source):
        """Test source validation failure."""
        from raft_toolkit.core.sources import SourceValidationError

        mock_input_source.validate.side_effect = Exception("Validation failed")

        with pytest.raises(SourceValidationError):
            await input_service.validate_source()

    @pytest.mark.asyncio
    async def test_get_processing_preview(self, input_service, mock_input_source):
        """Test processing preview."""
        preview = await input_service.get_processing_preview()

        assert "total_documents" in preview
        assert "estimated_chunks" in preview
        assert "estimated_qa_points" in preview

    @pytest.mark.asyncio
    async def test_process_documents_empty(self, input_service, mock_input_source):
        """Test processing with no documents."""
        mock_input_source.list_documents.return_value = []

        result = await input_service.process_documents()

        assert result == []

    @pytest.mark.asyncio
    async def test_process_local_documents(self, input_service, mock_input_source):
        """Test processing local documents."""
        from datetime import datetime

        from raft_toolkit.core.sources import SourceDocument

        # Mock document
        mock_doc = SourceDocument(
            name="test.pdf",
            source_path="/path/test.pdf",
            size=1000,
            last_modified=datetime.now(),
            extension=".pdf",
            content_type="application/pdf",
        )

        mock_input_source.list_documents.return_value = [mock_doc]

        # Mock document service
        mock_chunks = [Mock()]
        input_service.document_service.process_documents.return_value = mock_chunks

        result = await input_service.process_documents()

        assert len(result) == 1

    def test_get_source_info(self, input_service):
        """Test getting source information."""
        info = input_service.get_source_info()

        assert "source_type" in info
        assert "source_uri" in info
        assert "supported_types" in info

    def test_create_input_source_local(self, config, mock_llm_service):
        """Test creating local input source."""
        config.source_type = "local"
        config.source_uri = None

        with (
            patch("raft_toolkit.core.services.input_service.DocumentService"),
            patch("raft_toolkit.core.services.input_service.InputSourceFactory.create_source") as mock_factory,
        ):

            InputService(config, mock_llm_service)
            mock_factory.assert_called_once()

    def test_create_input_source_missing_uri(self, config, mock_llm_service):
        """Test creating input source with missing URI."""
        config.source_type = "s3"
        config.source_uri = None

        with patch("raft_toolkit.core.services.input_service.DocumentService"):
            with pytest.raises(ValueError, match="source_uri is required"):
                InputService(config, mock_llm_service)
