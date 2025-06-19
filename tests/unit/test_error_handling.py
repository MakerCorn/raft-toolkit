"""
Tests for error handling across the application.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.raft_engine import RaftEngine


@pytest.mark.unit
class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return RaftConfig(datapath=Path("test.pdf"), output="output", openai_key="test-key")

    def test_invalid_config_validation(self):
        """Test validation with invalid configuration."""
        # Test invalid doctype
        config = RaftConfig(openai_key="test-key", doctype="invalid")
        with pytest.raises(ValueError, match="Invalid doctype"):
            config.validate()

        # Test invalid output format
        config = RaftConfig(openai_key="test-key", output_format="invalid")
        with pytest.raises(ValueError, match="Invalid output format"):
            config.validate()

        # Test invalid chunking strategy
        config = RaftConfig(openai_key="test-key", chunking_strategy="invalid")
        with pytest.raises(ValueError, match="Invalid chunking strategy"):
            config.validate()

    def test_missing_api_key(self):
        """Test handling missing API key."""
        config = RaftConfig()
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            config.validate()

    def test_nonexistent_file_handling(self, config):
        """Test handling nonexistent files."""
        with (
            patch("raft_toolkit.core.raft_engine.LLMService"),
            patch("raft_toolkit.core.raft_engine.DocumentService"),
            patch("raft_toolkit.core.raft_engine.InputService"),
            patch("raft_toolkit.core.raft_engine.DatasetService"),
        ):

            engine = RaftEngine(config)

            with pytest.raises(FileNotFoundError):
                engine.validate_inputs(Path("nonexistent.pdf"))

    def test_wrong_file_extension(self, config, tmp_path):
        """Test handling wrong file extension."""
        # Create a .txt file but config expects .pdf
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with (
            patch("raft_toolkit.core.raft_engine.LLMService"),
            patch("raft_toolkit.core.raft_engine.DocumentService"),
            patch("raft_toolkit.core.raft_engine.InputService"),
            patch("raft_toolkit.core.raft_engine.DatasetService"),
        ):

            engine = RaftEngine(config)

            with pytest.raises(ValueError, match="File extension does not match doctype"):
                engine.validate_inputs(test_file)

    def test_empty_document_handling(self, config, tmp_path):
        """Test handling empty documents."""
        from raft_toolkit.core.services.document_service import DocumentService

        # Create empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        config.doctype = "txt"
        mock_llm_service = Mock()

        with patch("raft_toolkit.core.services.document_service.create_embedding_service"):
            doc_service = DocumentService(config, mock_llm_service)

            # Should handle empty content gracefully
            text = doc_service._extract_text(empty_file)
            assert text == ""

    def test_output_directory_creation_error(self, config, tmp_path):
        """Test handling output directory creation errors."""
        from raft_toolkit.core.services.dataset_service import DatasetService

        # Try to create output in a read-only location (simulate permission error)
        config.output = "/root/readonly/output.jsonl"  # Typically not writable

        dataset_service = DatasetService(config)

        # Create mock dataset with save_to_disk method
        mock_dataset = Mock()
        mock_dataset.save_to_disk = Mock(side_effect=PermissionError("Permission denied"))

        # Should handle directory creation errors gracefully
        with pytest.raises(PermissionError):
            dataset_service.save_dataset(mock_dataset, config.output)
