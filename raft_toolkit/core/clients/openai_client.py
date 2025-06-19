"""
OpenAI and Azure OpenAI client management.
"""

import logging
from os import environ
from typing import Any, Union

try:
    from openai import AzureOpenAI, OpenAI
except ImportError:
    # Create dummy classes for type safety
    class AzureOpenAI:  # type: ignore
        pass

    class OpenAI:  # type: ignore
        pass


from ..utils.env_config import read_env_config, set_env

logger = logging.getLogger(__name__)


def is_azure() -> bool:
    """Check if the environment is configured for Azure OpenAI.

    Returns:
        bool: True if AZURE_OPENAI_ENABLED is set to '1' or 'true' (case-insensitive), False otherwise.
    """
    value = environ.get("AZURE_OPENAI_ENABLED", "0").lower()
    azure = value in ("1", "true", "yes")
    if azure:
        logger.debug("Azure OpenAI support is enabled via AZURE_OPENAI_ENABLED.")
    else:
        logger.debug(
            "Azure OpenAI support is disabled (AZURE_OPENAI_ENABLED not set or false). "
            "Using OpenAI environment variables."
        )
    return azure


def build_openai_client(env_prefix: str = "COMPLETION", **kwargs: Any) -> Union[OpenAI, AzureOpenAI]:
    """Build OpenAI or AzureOpenAI client based on environment variables.

    Args:
        env_prefix (str, optional): The prefix for the environment variables. Defaults to "COMPLETION".
        **kwargs (Any): Additional keyword arguments for the OpenAI or AzureOpenAI client.

    Returns:
        Union[OpenAI, AzureOpenAI]: The configured OpenAI or AzureOpenAI client instance.
    """
    env = read_env_config(env_prefix)
    with set_env(**env):
        if is_azure():
            return AzureOpenAI(**kwargs)
        else:
            return OpenAI(**kwargs)


def build_langchain_embeddings(**kwargs):
    """Build LangChain embeddings for semantic chunking.

    Args:
        **kwargs: Additional arguments for embeddings initialization.

    Returns:
        Embeddings instance for LangChain.
    """
    try:
        from langchain_openai import AzureOpenAIEmbeddings, OpenAIEmbeddings

        if is_azure():
            return AzureOpenAIEmbeddings(**kwargs)
        else:
            # Check if we should use nomic embeddings
            if kwargs.get("model", "").startswith("nomic-"):
                try:
                    from langchain_community.embeddings import NomicEmbeddings

                    return NomicEmbeddings(model=kwargs.get("model"))
                except ImportError:
                    logger.warning("NomicEmbeddings not available, falling back to OpenAIEmbeddings")
                    return OpenAIEmbeddings(**kwargs)
            return OpenAIEmbeddings(**kwargs)
    except ImportError:
        # Mock implementation for demo purposes
        class MockEmbeddings:
            def embed_documents(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]

            def embed_query(self, text):
                return [0.1, 0.2, 0.3]

        return MockEmbeddings()
