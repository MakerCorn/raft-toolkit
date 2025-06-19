"""
Embedding service for generating embeddings with custom prompt templates.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Protocol

from raft_toolkit.core.config import RaftConfig
from raft_toolkit.core.models import DocumentChunk
from raft_toolkit.core.services.langwatch_service import create_langwatch_service
from raft_toolkit.core.utils.template_loader import create_template_loader


# Define protocol for embeddings
class EmbeddingsProtocol(Protocol):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        pass

    def embed_query(self, text: str) -> List[float]:
        pass


# Try to import real implementations
try:
    from langchain_openai.embeddings import AzureOpenAIEmbeddings, OpenAIEmbeddings

    HAS_OPENAI_EMBEDDINGS = True
except ImportError:
    HAS_OPENAI_EMBEDDINGS = False
    # Create stub classes only if imports fail

    class OpenAIEmbeddings:  # type: ignore
        def embed_documents(self, texts):
            pass

        def embed_query(self, text):
            pass

    class AzureOpenAIEmbeddings:  # type: ignore
        def embed_documents(self, texts):
            pass

        def embed_query(self, text):
            pass


# Try to import Nomic embeddings
try:
    from langchain_community.embeddings import NomicEmbeddings

    HAS_NOMIC_EMBEDDINGS = True
except ImportError:
    HAS_NOMIC_EMBEDDINGS = False
    # Create stub class only if import fails

    class NomicEmbeddings:  # type: ignore
        def embed_documents(self, texts):
            pass

        def embed_query(self, text):
            pass


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings with custom prompts."""

    def __init__(self, config: RaftConfig):
        self.config = config
        self.template_loader = create_template_loader(config)
        self.embeddings_model = self._build_embeddings_model()
        self.embedding_template = self._load_embedding_template()
        self.langwatch_service = create_langwatch_service(config)

    def _create_mock_embeddings(self) -> Any:
        """Create a mock embeddings model for testing or when real implementation is unavailable."""

        class MockEmbeddings:
            def embed_documents(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]

            def embed_query(self, text):
                return [0.1, 0.2, 0.3]

        logger.warning("Langchain embeddings not available, using mock implementation")
        return MockEmbeddings()

    def _build_embeddings_model(self) -> Any:
        """Build the underlying embeddings model."""
        try:
            if self.config.use_azure_identity:
                from ..utils import get_azure_openai_token

                api_key = get_azure_openai_token()
            else:
                api_key = self.config.openai_key

            # Try to use the OpenAI client building function if available
            try:
                from ..clients.openai_client import build_langchain_embeddings

                return build_langchain_embeddings(api_key=api_key, model=self.config.embedding_model)
            except ImportError:
                # Check if we should use Nomic embeddings
                if self.config.embedding_model.startswith("nomic-"):
                    if HAS_NOMIC_EMBEDDINGS:
                        logger.info(f"Using Nomic embeddings model: {self.config.embedding_model}")
                        return NomicEmbeddings(model=self.config.embedding_model)
                    else:
                        logger.warning(
                            "Nomic embeddings requested but not available, falling back to mock implementation"
                        )
                        return self._create_mock_embeddings()

                # Fall back to direct langchain integration
                if self.config.azure_openai_enabled:
                    # Create a mock embeddings model if real implementation not available
                    if not HAS_OPENAI_EMBEDDINGS:
                        return self._create_mock_embeddings()

                    # Parameters may vary based on the version - use **kwargs for flexibility
                    kwargs = {
                        "deployment": self.config.embedding_model,
                        "api_version": "2023-05-15",
                    }

                    if hasattr(self.config, "azure_endpoint"):
                        kwargs["endpoint"] = self.config.azure_endpoint

                    if api_key:
                        # Convert SecretStr to string for compatibility
                        kwargs["api_key"] = api_key

                    return AzureOpenAIEmbeddings(**kwargs)  # type: ignore
                else:
                    # Create a mock embeddings model if real implementation not available
                    if not HAS_OPENAI_EMBEDDINGS:
                        return self._create_mock_embeddings()

                    # Use the real implementation with appropriate parameters
                    kwargs = {}

                    if self.config.embedding_model:
                        kwargs["model"] = self.config.embedding_model

                    if api_key:
                        # Use raw string instead of SecretStr
                        kwargs["api_key"] = api_key

                    return OpenAIEmbeddings(**kwargs)  # type: ignore
        except ImportError:
            return self._create_mock_embeddings()

    def _load_embedding_template(self) -> str:
        """Load the embedding prompt template with robust fallback."""
        try:
            template = self.template_loader.load_embedding_template(self.config.embedding_prompt_template)
            if template:
                logger.debug("Successfully loaded embedding template")
                return template
            else:
                logger.warning("No embedding template found, using minimal default")
                return "Generate an embedding for the following content:\n\nContent: {content}"
        except Exception as e:
            logger.warning(f"Error loading embedding template: {e}. Using minimal default.")
            return "Generate an embedding for the following content:\n\nContent: {content}"

    def create_embeddings_with_template(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Create embeddings for chunks using the configured template.

        Args:
            chunks: List of document chunks to embed

        Returns:
            List of chunks with embeddings added
        """
        logger.info(f"Creating embeddings for {len(chunks)} chunks using template")

        start_time = time.time()

        # Prepare texts with template formatting
        formatted_texts = []
        for chunk in chunks:
            formatted_text = self._format_chunk_for_embedding(chunk)
            formatted_texts.append(formatted_text)

        # Generate embeddings
        try:
            embeddings = self.embeddings_model.embed_documents(formatted_texts)

            # Add embeddings to chunks
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
                # Also store the formatted text used for embedding
                chunk.metadata = chunk.metadata or {}
                chunk.metadata["embedding_prompt"] = self._format_chunk_for_embedding(chunk)

            # Track embedding generation
            processing_time = time.time() - start_time
            self.langwatch_service.track_embedding_generation(chunks, processing_time, self.config.embedding_model)

            logger.info(f"Successfully created embeddings for {len(chunks)} chunks")
            return chunks

        except Exception as e:
            logger.error(f"Failed to create embeddings: {e}")
            # Return chunks without embeddings
            return chunks

    def create_embedding_for_query(self, query: str, document_type: str = "query") -> List[float]:
        """
        Create embedding for a single query using the template.

        Args:
            query: The query text
            document_type: Type of document for template formatting

        Returns:
            Embedding vector
        """
        formatted_query = self._format_text_for_embedding(
            content=query, document_type=document_type, metadata={"type": "query"}
        )

        try:
            embedding = self.embeddings_model.embed_query(formatted_query)
            if isinstance(embedding, list):
                return embedding
            else:
                logger.warning(f"Unexpected embedding type: {type(embedding)}, converting to list")
                return list(embedding)
        except Exception as e:
            logger.error(f"Failed to create query embedding: {e}")
            # Return a zero vector as fallback
            return [0.0] * 768  # Standard embedding dimension

    def _format_chunk_for_embedding(self, chunk: DocumentChunk) -> str:
        """Format a chunk using the embedding template."""
        document_type = chunk.metadata.get("type", "unknown") if chunk.metadata else "unknown"
        metadata = chunk.metadata or {}

        return self._format_text_for_embedding(
            content=chunk.content,
            document_type=document_type,
            metadata=metadata,
            chunk_index=metadata.get("chunk_index"),
            chunking_strategy=metadata.get("chunking_strategy"),
        )

    def _format_text_for_embedding(
        self,
        content: str,
        document_type: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        chunk_index: Optional[int] = None,
        chunking_strategy: Optional[str] = None,
    ) -> str:
        """
        Format text using the embedding template.

        Args:
            content: The main content to embed
            document_type: Type of document (pdf, txt, json, etc.)
            metadata: Additional metadata
            chunk_index: Index of chunk within document
            chunking_strategy: Strategy used for chunking

        Returns:
            Formatted text ready for embedding
        """
        try:
            formatted_text = self.template_loader.format_template(
                self.embedding_template,
                content=content,
                document_type=document_type,
                metadata=str(metadata) if metadata else "",
                chunk_index=chunk_index or 0,
                chunking_strategy=chunking_strategy or "unknown",
            )
            return formatted_text
        except Exception as e:
            logger.warning(f"Template formatting failed, using raw content: {e}")
            return content

    def get_embedding_statistics(self) -> Dict[str, Any]:
        """Get statistics about the embedding service."""
        return {
            "model": self.config.embedding_model,
            "template_used": bool(self.embedding_template),
            "custom_template": bool(self.config.embedding_prompt_template),
            "azure_enabled": self.config.azure_openai_enabled,
            "template_preview": (
                self.embedding_template[:200] + "..." if len(self.embedding_template) > 200 else self.embedding_template
            ),
        }


def create_embedding_service(config: RaftConfig) -> EmbeddingService:
    """Create and return an embedding service instance."""
    return EmbeddingService(config)
