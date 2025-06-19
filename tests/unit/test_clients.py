"""
Tests for core.clients module.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    OpenAI = None  # type: ignore
    AzureOpenAI = None  # type: ignore

from raft_toolkit.core.clients.openai_client import build_langchain_embeddings, build_openai_client, is_azure


@pytest.mark.unit
class TestOpenAIClient:
    """Test OpenAI client utilities."""

    @patch("core.clients.openai_client.is_azure")
    @patch("core.clients.openai_client.OpenAI")
    @pytest.mark.unit
    def test_build_openai_client_standard(self, mock_openai, mock_is_azure):
        """Test building standard OpenAI client."""
        mock_is_azure.return_value = False
        mock_client = Mock()
        mock_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {"COMPLETION_OPENAI_API_KEY": "test-key", "COMPLETION_OPENAI_API_BASE_URL": "https://api.openai.com/v1"},
        ):
            client = build_openai_client(env_prefix="COMPLETION")

            assert client == mock_client
            mock_openai.assert_called_once()

    @patch("core.clients.openai_client.is_azure")
    @patch("core.clients.openai_client.AzureOpenAI")
    @pytest.mark.unit
    def test_build_openai_client_azure(self, mock_azure_openai, mock_is_azure):
        """Test building Azure OpenAI client."""
        mock_is_azure.return_value = True
        mock_client = Mock()
        mock_azure_openai.return_value = mock_client

        with patch.dict(
            "os.environ",
            {
                "COMPLETION_AZURE_OPENAI_KEY": "test-key",
                "COMPLETION_AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/",
            },
        ):
            client = build_openai_client(env_prefix="COMPLETION")

            assert client == mock_client
            mock_azure_openai.assert_called_once()

    @pytest.mark.unit
    def test_is_azure_enabled(self):
        """Test Azure detection when enabled."""
        with patch.dict("os.environ", {"AZURE_OPENAI_ENABLED": "1"}):
            assert is_azure() is True

        with patch.dict("os.environ", {"AZURE_OPENAI_ENABLED": "true"}):
            assert is_azure() is True

        with patch.dict("os.environ", {"AZURE_OPENAI_ENABLED": "True"}):
            assert is_azure() is True

    @pytest.mark.unit
    def test_is_azure_disabled(self):
        """Test Azure detection when disabled."""
        with patch.dict("os.environ", {"AZURE_OPENAI_ENABLED": "0"}):
            assert is_azure() is False

        with patch.dict("os.environ", {"AZURE_OPENAI_ENABLED": "false"}):
            assert is_azure() is False

        with patch.dict("os.environ", {}):
            assert is_azure() is False

    @patch("core.clients.openai_client.is_azure")
    @pytest.mark.unit
    def test_build_langchain_embeddings_standard(self, mock_is_azure):
        """Test building standard LangChain embeddings."""
        mock_is_azure.return_value = False

        with patch("langchain_openai.OpenAIEmbeddings") as mock_embeddings:
            mock_instance = Mock()
            mock_embeddings.return_value = mock_instance

            embeddings = build_langchain_embeddings(api_key="test-key", model="text-embedding-ada-002")

            assert embeddings == mock_instance
            mock_embeddings.assert_called_once_with(api_key="test-key", model="text-embedding-ada-002")

    @patch("core.clients.openai_client.is_azure")
    @pytest.mark.unit
    def test_build_langchain_embeddings_azure(self, mock_is_azure):
        """Test building Azure LangChain embeddings."""
        mock_is_azure.return_value = True

        with patch("langchain_openai.AzureOpenAIEmbeddings") as mock_embeddings:
            mock_instance = Mock()
            mock_embeddings.return_value = mock_instance

            with patch.dict(
                "os.environ",
                {"AZURE_OPENAI_ENDPOINT": "https://test.openai.azure.com/", "AZURE_OPENAI_API_VERSION": "2024-02-01"},
            ):
                embeddings = build_langchain_embeddings(api_key="test-key", model="text-embedding-ada-002")

                assert embeddings == mock_instance
                mock_embeddings.assert_called_once()


@pytest.mark.unit
class TestStatsCompleter:
    """Test StatsCompleter wrapper."""

    @pytest.mark.unit
    def test_stats_completer_basic_usage(self):
        """Test basic usage of StatsCompleter."""
        from raft_toolkit.core.clients import StatsCompleter

        # Mock the underlying completion function
        mock_completion_func = Mock()
        mock_response = Mock()
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 50
        mock_completion_func.return_value = mock_response

        completer = StatsCompleter(mock_completion_func)

        # Call the completion
        response = completer(model="gpt-4", prompt="test prompt")

        assert response == mock_response
        mock_completion_func.assert_called_once_with(model="gpt-4", prompt="test prompt")

        # Check stats were recorded
        stats = completer.get_stats_and_reset()
        assert stats is not None
        assert stats.total_tokens == 100
        assert stats.prompt_tokens == 50
        assert stats.completion_tokens == 50
        assert stats.calls == 1


@pytest.mark.unit
class TestUsageStats:
    """Test UsageStats class."""

    @pytest.mark.unit
    def test_usage_stats_creation(self):
        """Test UsageStats creation and basic properties."""
        from raft_toolkit.core.clients import UsageStats

        stats = UsageStats()

        assert stats.total_tokens == 0
        assert stats.prompt_tokens == 0
        assert stats.completion_tokens == 0
        assert stats.calls == 0
        assert stats.duration == 0

    @pytest.mark.unit
    def test_usage_stats_addition(self):
        """Test adding UsageStats together."""
        from raft_toolkit.core.clients import UsageStats

        stats1 = UsageStats()
        stats1.total_tokens = 100
        stats1.prompt_tokens = 50
        stats1.completion_tokens = 50
        stats1.calls = 1
        stats1.duration = 1.0

        stats2 = UsageStats()
        stats2.total_tokens = 200
        stats2.prompt_tokens = 100
        stats2.completion_tokens = 100
        stats2.calls = 2
        stats2.duration = 2.0

        combined = stats1 + stats2

        assert combined.total_tokens == 300
        assert combined.prompt_tokens == 150
        assert combined.completion_tokens == 150
        assert combined.calls == 3
        assert combined.duration == 3.0
