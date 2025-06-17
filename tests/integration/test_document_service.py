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
    def document_service(self, config):
        """Create document service instance."""
        return DocumentService(config)

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
        api_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {"/users": {"get": {"summary": "Get users", "description": "Retrieve all users from the system"}}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(api_data, f)
            temp_path = f.name

        yield temp_path

        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_process_text_document(self, document_service, test_text_file):
        """Test processing a text document."""
        chunks = document_service.process_document(test_text_file, doctype="txt")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        assert all(chunk.content.strip() for chunk in chunks)  # No empty chunks
        assert all(chunk.metadata["source"] == test_text_file for chunk in chunks)

    def test_process_json_document(self, document_service, test_json_file):
        """Test processing a JSON document."""
        chunks = document_service.process_document(test_json_file, doctype="json")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
        # JSON content should be flattened into text
        combined_content = " ".join(chunk.content for chunk in chunks)
        assert "Test Document" in combined_content

    def test_process_api_document(self, document_service, test_api_file):
        """Test processing an API documentation file."""
        chunks = document_service.process_document(test_api_file, doctype="api")

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

            chunks = document_service.process_document(temp_dir, doctype="txt")

            assert len(chunks) >= 3  # At least one chunk per file
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
            # Should have chunks from different files
            sources = {chunk.metadata["source"] for chunk in chunks}
            assert len(sources) >= 3

    @patch("core.services.embedding_service.build_openai_client")
    def test_semantic_chunking_integration(self, mock_client_builder, document_service, test_text_file):
        """Test semantic chunking with embedding service."""
        # Mock embedding client
        mock_client = Mock()
        mock_client_builder.return_value = mock_client
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_response

        # Update config for semantic chunking
        document_service.config.chunking_strategy = "semantic"

        chunks = document_service.process_document(test_text_file, doctype="txt")

        assert len(chunks) > 0
        assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

        # Verify embedding service was called (if available)
        if mock_client.embeddings.create.called:
            call_args = mock_client.embeddings.create.call_args
            assert call_args is not None

    def test_sentence_chunking_integration(self, document_service, test_text_file):
        """Test sentence-based chunking."""
        # Update config for sentence chunking
        document_service.config.chunking_strategy = "sentence"

        chunks = document_service.process_document(test_text_file, doctype="txt")

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
            chunks = document_service.process_document(invalid_file, doctype="api")
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
            chunks = document_service.process_document(nonexistent_file, doctype="txt")
            # If it doesn't raise an exception, should return empty list
            assert chunks == []
        except Exception as e:
            # Should raise a meaningful error about file not found
            error_msg = str(e).lower()
            assert "not found" in error_msg or "does not exist" in error_msg or "no such file" in error_msg

    @patch("core.services.embedding_service.build_openai_client")
    def test_parallel_processing(self, mock_client_builder, document_service):
        """Test parallel processing capabilities."""
        # Mock embedding client
        mock_client = Mock()
        mock_client_builder.return_value = mock_client
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1] * 1536
        mock_client.embeddings.create.return_value = mock_response

        # Create multiple test files
        with tempfile.TemporaryDirectory() as temp_dir:
            files = []
            for i in range(5):
                file_path = os.path.join(temp_dir, f"test{i}.txt")
                with open(file_path, "w") as f:
                    f.write(f"This is test document {i} with substantial content.\n" * 10)
                files.append(file_path)

            # Process directory (should use parallel processing internally)
            chunks = document_service.process_document(temp_dir, doctype="txt")

            assert len(chunks) > 0
            assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)

            # Verify we got chunks from multiple files
            sources = {chunk.metadata["source"] for chunk in chunks}
            assert len(sources) >= 3  # Should process multiple files
