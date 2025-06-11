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
        bool: True if the AZURE_OPENAI_ENABLED environment variable is set to '1' or 'true' (case-insensitive), False otherwise.
    """
    value = environ.get("AZURE_OPENAI_ENABLED", "0").lower()
    azure = value in ("1", "true", "yes")
    if azure:
        logger.debug("Azure OpenAI support is enabled via AZURE_OPENAI_ENABLED.")
    else:
        logger.debug("Azure OpenAI support is disabled (AZURE_OPENAI_ENABLED not set or false). Using OpenAI environment variables.")
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