"""
Test for Nomic embeddings integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.config import RaftConfig
from core.services.embedding_service import EmbeddingService


@pytest.fixture
def config():
    """Create a test configuration with Nomic embeddings."""
    config = RaftConfig()
    config.embedding_model = "nomic-embed-text"
    config.openai_key = "test_key"
    return config


@patch("core.services.embedding_service.NomicEmbeddings")
def test_nomic_embeddings_creation(mock_nomic, config):
    """Test that Nomic embeddings are created when specified in config."""
    # Setup mock
    mock_instance = MagicMock()
    mock_nomic.return_value = mock_instance

    # Create embedding service
    with patch("core.services.embedding_service.HAS_NOMIC_EMBEDDINGS", True):
        EmbeddingService(config)

    # Verify Nomic embeddings were created
    mock_nomic.assert_called_once_with(model="nomic-embed-text")


@patch("core.clients.openai_client.NomicEmbeddings")
def test_nomic_embeddings_via_client_builder(mock_nomic, config):
    """Test that Nomic embeddings are created via the client builder."""
    # Setup mock
    mock_instance = MagicMock()
    mock_nomic.return_value = mock_instance

    # Create embedding service with patched client builder
    with patch("core.services.embedding_service.build_langchain_embeddings") as mock_builder:
        EmbeddingService(config)

    # Verify client builder was called
    mock_builder.assert_called_once()


def test_fallback_when_nomic_not_available(config):
    """Test fallback to mock embeddings when Nomic is not available."""
    # Create embedding service with Nomic unavailable
    with patch("core.services.embedding_service.HAS_NOMIC_EMBEDDINGS", False):
        with patch("core.services.embedding_service.HAS_LANGCHAIN_OPENAI", False):
            with patch("core.services.embedding_service._create_mock_embeddings") as mock_create:
                mock_create.return_value = MagicMock()
                EmbeddingService(config)

            # Verify mock embeddings were created
            mock_create.assert_called_once()
