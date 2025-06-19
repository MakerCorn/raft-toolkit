"""
Tests for core.utils modules.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from core.utils.env_config import read_env_config, set_env
from core.utils.file_utils import extract_random_jsonl_rows, split_jsonl_file
from core.utils.identity_utils import AZURE_AVAILABLE, get_azure_openai_token, get_cognitive_service_token, get_db_token


@pytest.mark.unit
class TestFileUtils:
    """Test file utility functions."""

    @pytest.mark.unit
    def test_split_jsonl_file(self, temp_directory):
        """Test JSONL file splitting."""
        # Create a test JSONL file
        test_file = temp_directory / "test.jsonl"
        test_data = [
            {"id": 1, "text": "First record"},
            {"id": 2, "text": "Second record"},
            {"id": 3, "text": "Third record"},
            {"id": 4, "text": "Fourth record"},
        ]

        with open(test_file, "w") as f:
            for record in test_data:
                f.write(json.dumps(record) + "\n")

        # Split the file (small max_size to force split)
        split_files = split_jsonl_file(str(test_file), max_size=100)

        assert len(split_files) > 1

        # Verify split files contain all data
        all_records = []
        for split_file in split_files:
            split_path = Path(split_file)
            assert split_path.exists()

            with open(split_path) as f:
                for line in f:
                    all_records.append(json.loads(line))

        assert len(all_records) == len(test_data)

        # Verify IDs match
        original_ids = {record["id"] for record in test_data}
        split_ids = {record["id"] for record in all_records}
        assert original_ids == split_ids

    @pytest.mark.unit
    def test_extract_random_jsonl_rows(self, temp_directory):
        """Test random JSONL row extraction."""
        # Create a test JSONL file
        test_file = temp_directory / "test.jsonl"
        output_file = temp_directory / "output.jsonl"

        test_data = [{"id": i, "text": f"Record {i}"} for i in range(10)]

        with open(test_file, "w") as f:
            for record in test_data:
                f.write(json.dumps(record) + "\n")

        # Extract random rows
        extract_random_jsonl_rows(str(test_file), 5, str(output_file))

        assert output_file.exists()

        # Read extracted data
        extracted_data = []
        with open(output_file) as f:
            for line in f:
                extracted_data.append(json.loads(line))

        assert len(extracted_data) == 5

        # Verify all extracted records are from original data
        original_ids = {record["id"] for record in test_data}
        extracted_ids = {record["id"] for record in extracted_data}
        assert extracted_ids.issubset(original_ids)


@pytest.mark.unit
class TestEnvConfig:
    """Test environment configuration utilities."""

    @pytest.mark.unit
    def test_read_env_config_basic(self):
        """Test basic environment config reading."""
        test_env = {"TEST_OPENAI_API_KEY": "test-key", "TEST_AZURE_OPENAI_ENDPOINT": "https://api.test.com"}

        with patch.dict(os.environ, test_env):
            config = read_env_config("TEST")

            assert config["OPENAI_API_KEY"] == "test-key"
            assert config["AZURE_OPENAI_ENDPOINT"] == "https://api.test.com"

    @pytest.mark.unit
    def test_read_env_config_empty_prefix(self):
        """Test environment config reading with empty prefix."""
        test_env = {"OPENAI_API_KEY": "direct-key", "AZURE_OPENAI_ENDPOINT": "direct-endpoint"}

        with patch.dict(os.environ, test_env):
            config = read_env_config("")

            assert config["OPENAI_API_KEY"] == "direct-key"
            assert config["AZURE_OPENAI_ENDPOINT"] == "direct-endpoint"

    @pytest.mark.unit
    def test_set_env_context_manager(self):
        """Test set_env context manager."""
        original_value = os.environ.get("TEST_VAR", "not_set")

        test_env = {"TEST_VAR": "temp_value"}

        with set_env(**test_env):
            assert os.environ["TEST_VAR"] == "temp_value"

        # Should restore original value
        current_value = os.environ.get("TEST_VAR", "not_set")
        assert current_value == original_value


@pytest.mark.unit
class TestIdentityUtils:
    """Test Azure identity utilities."""

    def setup_method(self):
        """Clear token cache before each test."""
        # Clear the global token cache
        from core.utils.identity_utils import tokens

        tokens.clear()

    @pytest.mark.unit
    def test_azure_available_flag(self):
        """Test AZURE_AVAILABLE flag is properly set."""
        # This test just verifies the flag exists and is a boolean
        assert isinstance(AZURE_AVAILABLE, bool)

    @patch("core.utils.identity_utils.AZURE_AVAILABLE", True)
    @patch("core.utils.identity_utils.credential")
    @pytest.mark.unit
    def test_get_azure_openai_token_success(self, mock_credential):
        """Test successful Azure OpenAI token retrieval."""
        mock_token = Mock()
        mock_token.token = "test-azure-token"
        mock_token.expires_on = 9999999999  # Far future
        mock_credential.get_token.return_value = mock_token

        token = get_azure_openai_token()

        assert token == "test-azure-token"
        mock_credential.get_token.assert_called_once()

    @patch("core.utils.identity_utils.AZURE_AVAILABLE", False)
    @pytest.mark.unit
    def test_get_azure_openai_token_unavailable(self):
        """Test Azure OpenAI token when Azure is unavailable."""
        token = get_azure_openai_token()
        assert token is None

    @patch("core.utils.identity_utils.AZURE_AVAILABLE", True)
    @patch("core.utils.identity_utils.credential")
    @pytest.mark.unit
    def test_get_cognitive_service_token_success(self, mock_credential):
        """Test successful cognitive services token retrieval."""
        mock_token = Mock()
        mock_token.token = "test-cognitive-token"
        mock_token.expires_on = 9999999999  # Far future
        mock_credential.get_token.return_value = mock_token

        token = get_cognitive_service_token()

        assert token == "test-cognitive-token"
        mock_credential.get_token.assert_called_once()

    @patch("core.utils.identity_utils.AZURE_AVAILABLE", True)
    @patch("core.utils.identity_utils.credential")
    @pytest.mark.unit
    def test_get_db_token_success(self, mock_credential):
        """Test successful database token retrieval."""
        mock_token = Mock()
        mock_token.token = "test-db-token"
        mock_token.expires_on = 9999999999  # Far future
        mock_credential.get_token.return_value = mock_token

        token = get_db_token()

        assert token == "test-db-token"
        mock_credential.get_token.assert_called_once()

    @patch("core.utils.identity_utils.AZURE_AVAILABLE", True)
    @patch("core.utils.identity_utils.credential")
    @pytest.mark.unit
    def test_token_caching(self, mock_credential):
        """Test token caching behavior."""
        mock_token = Mock()
        mock_token.token = "cached-token"
        mock_token.expires_on = 9999999999  # Far future
        mock_credential.get_token.return_value = mock_token

        # First call should get new token
        token1 = get_azure_openai_token()
        assert token1 == "cached-token"

        # Second call should use cached token
        token2 = get_azure_openai_token()
        assert token2 == "cached-token"

        # Should only call get_token once due to caching
        assert mock_credential.get_token.call_count == 1
