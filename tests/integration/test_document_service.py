"""
Integration tests for document service.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.config import RaftConfig
from core.models import DocumentChunk
from core.services.document_service import DocumentService
from core.services.llm_service import LLMService


class TestDocumentServiceIntegration:
    """Integration tests for document service."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return RaftConfig(
            openai_key="test-key",
            embedding_model="text-embedding-ada-002",
            chunk_size=512,
            chunking_strategy="semantic",
        )

    @pytest.fixture
    def llm_service(self, config):
        """Create LLM service instance."""
        return LLMService(config)

    @pytest.fixture
    def document_service(self, config, llm_service):
        """Create document service instance."""
        with (
            patch("core.services.document_service.create_embedding_service") as mock_embedding_service,
            patch("core.clients.openai_client.build_langchain_embeddings") as mock_build_embeddings,
        ):
            # Mock the embedding service to avoid real API calls
            mock_service = Mock()
            mock_service.create_embeddings_with_template.side_effect = lambda chunks: chunks
            mock_embedding_service.return_value = mock_service

            # Mock the build_langchain_embeddings to return a mock embeddings model
            mock_embeddings = Mock()
            mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]
            mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
            mock_build_embeddings.return_value = mock_embeddings

            service = DocumentService(config, llm_service)
            # Replace the embedding service created during init
            service.embedding_service = mock_service
            return service

    @pytest.fixture
    def test_text_file(self):
        """Create a temporary text file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is the first paragraph of the test document.\n")
            f.write("It contains multiple sentences for testing.\n\n")
            f.write("This is the second paragraph.\n")
            f.write("It also has multiple sentences to test chunking strategies.\n")
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def test_json_file(self):
        """Create a temporary JSON file."""
        test_data = {
            "title": "Test Document",
            "content": "This is a test JSON document with structured data.",
            "sections": [
                {"name": "Introduction", "text": "This is the introduction section."},
                {"name": "Body", "text": "This is the main body of the document."},
                {"name": "Conclusion", "text": "This is the conclusion section."},
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def test_api_file(self):
        """Create a temporary API documentation file."""
        api_data = [
            {
                "user_name": "test_user",
                "api_name": "get_users",
                "api_call": "GET /users",
                "api_version": "1.0.0",
                "api_arguments": {"limit": "integer", "offset": "integer"},
                "functionality": "Retrieve all users from the system",
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(api_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_process_text_document(self, document_service, test_text_file):
        """Test processing a text document."""
        document_service.config.doctype = "txt"
        document_service.config.chunking_strategy = "fixed"  # Use fixed chunking to avoid API calls
        chunks = document_service.process_documents(Path(test_text_file))

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.content.strip() for chunk in chunks)  # No empty chunks
        assert all(chunk.source == test_text_file for chunk in chunks)

    def test_process_json_document(self, document_service, test_json_file):
        """Test processing a JSON document."""
        document_service.config.doctype = "json"
        document_service.config.chunking_strategy = "fixed"  # Use fixed chunking to avoid API calls
        chunks = document_service.process_documents(Path(test_json_file))

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        # JSON content should be flattened into text
        combined_content = " ".join(chunk.content for chunk in chunks)
        assert "Test Document" in combined_content

    def test_process_api_document(self, document_service, test_api_file):
        """Test processing an API documentation file."""
        document_service.config.doctype = "api"
        chunks = document_service.process_documents(Path(test_api_file))

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        # API content should include endpoint information
        combined_content = " ".join(chunk.content for chunk in chunks)
        assert "users" in combined_content.lower() or "api" in combined_content.lower()

    def test_process_directory(self, document_service):
        """Test processing a directory of documents."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple test files
            for i in range(3):
                file_path = os.path.join(temp_dir, f"test{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"This is test document {i}.\n")
                    f.write(f"It contains content for testing document {i}.")

            document_service.config.doctype = "txt"
            document_service.config.chunking_strategy = "fixed"  # Use fixed chunking to avoid API calls
            chunks = document_service.process_documents(Path(temp_dir))

            assert len(chunks) >= 3  # At least one chunk per file
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
            # Should have chunks from different files
            sources = {chunk.source for chunk in chunks}
            assert len(sources) >= 3

    @patch("core.clients.openai_client.build_langchain_embeddings")
    def test_semantic_chunking_integration(self, mock_embeddings_builder, document_service, test_text_file):
        """Test semantic chunking with embedding service."""
        # Mock langchain embeddings
        mock_embeddings = Mock()
        mock_embeddings_builder.return_value = mock_embeddings
        mock_embeddings.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
        mock_embeddings.embed_query.return_value = [0.1] * 1536

        # Update config for semantic chunking
        document_service.config.chunking_strategy = "semantic"
        document_service.config.doctype = "txt"

        chunks = document_service.process_documents(Path(test_text_file))

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

        # Verify embedding service was called (if available)
        if mock_embeddings.embed_documents.called:
            call_args = mock_embeddings.embed_documents.call_args
            assert call_args is not None

    def test_sentence_chunking_integration(self, document_service, test_text_file):
        """Test sentence-based chunking."""
        # Update config for sentence chunking
        document_service.config.chunking_strategy = "sentence"
        document_service.config.doctype = "txt"

        chunks = document_service.process_documents(Path(test_text_file))

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        # Sentence chunks should respect sentence boundaries
        for chunk in chunks:
            # Should not end mid-sentence (basic check)
            assert chunk.content.strip().endswith((".", "!", "?", "\n")) or len(chunk.content.strip()) == 0

    def test_error_handling_invalid_api_format(self, document_service):
        """Test error handling for invalid API format."""
        # Create invalid API file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"invalid": "format"}, f)
            invalid_file = f.name

        try:
            document_service.config.doctype = "api"
            chunks = document_service.process_documents(Path(invalid_file))
            # Should either succeed with empty chunks or handle gracefully
            assert isinstance(chunks, list)
        except Exception as e:
            # Should raise a meaningful error
            assert "api" in str(e).lower() or "format" in str(e).lower() or "invalid" in str(e).lower()
        finally:
            if os.path.exists(invalid_file):
                os.unlink(invalid_file)

    def test_error_handling_nonexistent_file(self, document_service):
        """Test error handling for nonexistent file."""
        nonexistent_file = "definitely_does_not_exist.txt"

        try:
            document_service.config.doctype = "txt"
            document_service.config.chunking_strategy = "fixed"  # Use fixed chunking to avoid API calls
            chunks = document_service.process_documents(Path(nonexistent_file))
            # If it doesn't raise an exception, should return empty list
            assert chunks == []
        except Exception as e:
            # Should raise a meaningful error about file not found
            error_msg = str(e).lower()
            assert "not found" in error_msg or "does not exist" in error_msg or "no such file" in error_msg

    @patch("core.clients.openai_client.build_langchain_embeddings")
    def test_parallel_processing(self, mock_embeddings_builder, document_service):
        """Test parallel processing capabilities."""
        # Mock langchain embeddings
        mock_embeddings = Mock()
        mock_embeddings_builder.return_value = mock_embeddings
        mock_embeddings.embed_documents.return_value = [[0.1] * 1536] * 10  # Multiple embeddings
        mock_embeddings.embed_query.return_value = [0.1] * 1536

        # Create multiple test files
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(5):
                file_path = os.path.join(temp_dir, f"test{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"This is test document {i} with substantial content.\n" * 10)
                files.append(file_path)

            # Process directory (should use parallel processing internally)
            document_service.config.doctype = "txt"
            document_service.config.chunking_strategy = "fixed"  # Use fixed chunking to avoid API calls
            chunks = document_service.process_documents(Path(temp_dir))

            assert len(chunks) > 0
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

            # Verify we got chunks from multiple files
            sources = {chunk.source for chunk in chunks}
            assert len(sources) >= 3  # Should process multiple files
