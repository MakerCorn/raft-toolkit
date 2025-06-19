"""
Test for Nomic embeddings integration.
"""

from unittest.mock import MagicMock, patch

import pytest

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.services.embedding_service import EmbeddingService


@pytest.fixture
def config():
    """Create a test configuration with Nomic embeddings."""
    config = RaftConfig()
    config.embedding_model = "nomic-embed-text"
    config.openai_key = "test_key"
    return config


@patch("raft_toolkit.core.services.embedding_service.NomicEmbeddings")
@patch("raft_toolkit.core.services.embedding_service.HAS_NOMIC_EMBEDDINGS", True)
def test_nomic_embeddings_creation(mock_nomic, config):
    """Test that Nomic embeddings are created when specified in config."""
    # Setup mock
    mock_instance = MagicMock()
    mock_nomic.return_value = mock_instance

    # Create embedding service with client builder patched to avoid import
    with patch("raft_toolkit.core.clients.openai_client.build_langchain_embeddings", side_effect=ImportError):
        EmbeddingService(config)

    # Verify Nomic embeddings were created
    mock_nomic.assert_called_once_with(model="nomic-embed-text")


def test_nomic_embeddings_via_client_builder(config):
    """Test that Nomic embeddings are created via the client builder."""
    # Setup mock for the client builder function
    mock_instance = MagicMock()

    # Create embedding service with patched client builder
    with patch("raft_toolkit.core.clients.openai_client.build_langchain_embeddings") as mock_builder:
        mock_builder.return_value = mock_instance
        service = EmbeddingService(config)

    # Verify client builder was called and service was created successfully
    mock_builder.assert_called_once()
    assert service.embeddings_model == mock_instance


def test_fallback_when_nomic_not_available(config):
    """Test fallback to mock embeddings when Nomic is not available."""
    # Create embedding service with Nomic unavailable
    with patch("raft_toolkit.core.services.embedding_service.HAS_NOMIC_EMBEDDINGS", False):
        with patch("raft_toolkit.core.services.embedding_service.HAS_OPENAI_EMBEDDINGS", False):
            with patch("raft_toolkit.core.clients.openai_client.build_langchain_embeddings", side_effect=ImportError):
                service = EmbeddingService(config)

                # Verify that a mock embeddings instance was created
                assert hasattr(service, "embeddings_model")
                assert hasattr(service.embeddings_model, "embed_documents")
                assert hasattr(service.embeddings_model, "embed_query")

                # Test that it returns expected mock values
                result = service.embeddings_model.embed_documents(["test"])
                assert isinstance(result, list)
                assert len(result) == 1
                assert isinstance(result[0], list)
