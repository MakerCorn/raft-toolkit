"""
Tests for document service.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.services.document_service import DocumentService


@pytest.mark.unit
class TestDocumentService:
    """Test DocumentService class."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(
            datapath=Path("test.pdf"),
            output="output",
            openai_key="test-key",
            doctype="pdf",
            chunk_size=512,
            chunking_strategy="fixed",
        )

    @pytest.fixture
    def mock_llm_service(self):
        """Create mock LLM service."""
        return Mock()

    @pytest.fixture
    def document_service(self, config, mock_llm_service):
        """Create DocumentService instance."""
        with patch("raft_toolkit.core.services.document_service.create_embedding_service"):
            return DocumentService(config, mock_llm_service)

    def test_init(self, document_service, config, mock_llm_service):
        """Test DocumentService initialization."""
        assert document_service.config == config
        assert document_service.llm_service == mock_llm_service

    def test_extract_text_json(self, document_service):
        """Test text extraction from JSON file."""
        test_data = {"text": "Test content"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            document_service.config.doctype = "json"
            result = document_service._extract_text(temp_path)
            assert result == "Test content"
        finally:
            temp_path.unlink()

    def test_extract_text_txt(self, document_service):
        """Test text extraction from TXT file."""
        test_content = "This is test content"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)

        try:
            document_service.config.doctype = "txt"
            result = document_service._extract_text(temp_path)
            assert result == test_content
        finally:
            temp_path.unlink()

    def test_fixed_chunking(self, document_service):
        """Test fixed chunking strategy."""
        text = "A" * 1000
        document_service.config.chunk_size = 100

        chunks = document_service._fixed_chunking(text)

        assert len(chunks) == 10
        assert all(len(chunk) == 100 for chunk in chunks)

    def test_sentence_chunking(self, document_service):
        """Test sentence chunking strategy."""
        text = "First sentence. Second sentence. Third sentence."
        document_service.config.chunk_size = 30

        chunks = document_service._sentence_chunking(text)

        assert len(chunks) >= 1
        assert all(len(chunk) <= 30 for chunk in chunks)

    @patch("raft_toolkit.core.services.document_service.HAS_SEMANTIC_CHUNKER", False)
    def test_semantic_chunking_fallback(self, document_service):
        """Test semantic chunking fallback when not available."""
        text = "Test content"

        with patch.object(document_service, "_fixed_chunking") as mock_fixed:
            mock_fixed.return_value = ["chunk1", "chunk2"]

            result = document_service._semantic_chunking(None, text)

            mock_fixed.assert_called_once_with(text)
            assert result == ["chunk1", "chunk2"]

    def test_process_api_documents(self, document_service):
        """Test processing API documents."""
        api_data = [
            {
                "user_name": "test",
                "api_name": "test_api",
                "api_call": "GET /test",
                "api_version": "v1",
                "api_arguments": {},
                "functionality": "test function",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(api_data, f)
            temp_path = Path(f.name)

        try:
            document_service.config.doctype = "api"
            chunks = document_service._process_api_documents(temp_path)

            assert len(chunks) == 1
            assert chunks[0].metadata["type"] == "api"
        finally:
            temp_path.unlink()

    def test_unsupported_doctype(self, document_service):
        """Test unsupported document type."""
        document_service.config.doctype = "unsupported"

        with pytest.raises(ValueError, match="Unsupported document type"):
            document_service._extract_text(Path("test.unsupported"))
