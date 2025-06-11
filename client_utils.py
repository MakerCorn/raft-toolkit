from abc import ABC
from typing import Any
from langchain_openai import OpenAIEmbeddings, AzureOpenAIEmbeddings
from openai import AzureOpenAI, OpenAI
import logging
from env_config import read_env_config, set_env
from os import environ
import time
from threading import Lock
from clients.stats import UsageStats, StatsCompleter, ChatCompleter, CompletionsCompleter

logger = logging.getLogger("client_utils")

def is_azure() -> bool:
    """Check if the environment is configured for Azure OpenAI.

    Returns:
        bool: True if Azure OpenAI environment variables are set, False otherwise.
    """
    azure = (
        "AZURE_OPENAI_ENDPOINT" in environ or
        "AZURE_OPENAI_KEY" in environ or
        "AZURE_OPENAI_AD_TOKEN" in environ
    )
    if azure:
        logger.debug("Using Azure OpenAI environment variables")
    else:
        logger.debug("Using OpenAI environment variables")
    return azure

def build_openai_client(env_prefix: str = "COMPLETION", **kwargs: Any) -> OpenAI:
    """Build OpenAI or AzureOpenAI client based on environment variables.

    Args:
        env_prefix (str, optional): The prefix for the environment variables. Defaults to "COMPLETION".
        **kwargs (Any): Additional keyword arguments for the OpenAI or AzureOpenAI client.

    Returns:
        OpenAI: The configured OpenAI or AzureOpenAI client instance.
    """
    env = read_env_config(env_prefix)
    with set_env(**env):
        if is_azure():
            return AzureOpenAI(**kwargs)
        else:
            return OpenAI(**kwargs)

def build_langchain_embeddings(**kwargs: Any) -> OpenAIEmbeddings:
    """Build OpenAI or AzureOpenAI embeddings client based on environment variables.

    Args:
        **kwargs (Any): Additional keyword arguments for the OpenAIEmbeddings or AzureOpenAIEmbeddings client.

    Returns:
        OpenAIEmbeddings: The configured embeddings client instance.
    """
    env = read_env_config("EMBEDDING")
    with set_env(**env):
        if is_azure():
            return AzureOpenAIEmbeddings(**kwargs)
        else:
            return OpenAIEmbeddings(**kwargs)

def safe_min(a: Any, b: Any) -> Any:
    """Return the minimum of two values, safely handling None values."""
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)

def safe_max(a: Any, b: Any) -> Any:
    """Return the maximum of two values, safely handling None values."""
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)