try:
    from azure.core.credentials import AccessToken
    from azure.identity import CredentialUnavailableError, DefaultAzureCredential

    credential = DefaultAzureCredential()
    AZURE_AVAILABLE = True
except ImportError:
    # Create dummy classes for type safety
    class DefaultAzureCredential:  # type: ignore
        def __init__(self):
            pass

    class CredentialUnavailableError(Exception):  # type: ignore
        pass

    class AccessToken:  # type: ignore
        token: str
        expires_on: int

    credential = DefaultAzureCredential()  # Create an instance of the dummy class
    AZURE_AVAILABLE = False

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)

tokens: Dict[str, Any] = {}


def get_db_token() -> Optional[str]:
    """Retrieves a token for database access using Azure Entra ID.

    Returns:
        Optional[str]: The database access token, or None if unavailable.
    """
    return _get_token("db_token", "https://ossrdbms-aad.database.windows.net/.default")


def get_azure_openai_token() -> Optional[str]:
    """Retrieves a token for Azure OpenAI service using Azure Entra ID.

    Returns:
        Optional[str]: The Azure OpenAI service token, or None if unavailable.
    """
    return get_cognitive_service_token()


def get_cognitive_service_token() -> Optional[str]:
    """Retrieves a token for Azure Cognitive Services using Azure Entra ID.

    Returns:
        Optional[str]: The Azure Cognitive Services token, or None if unavailable.
    """
    return _get_token("cognitive_token", "https://cognitiveservices.azure.com/.default")


def _format_datetime(dt):
    """Formats a datetime object as a string in the local timezone."""
    return datetime.utcfromtimestamp(dt).replace(tzinfo=timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _get_token(token_key: str, resource: str) -> Optional[str]:
    """Retrieves and caches an Azure AD token for the specified resource.

    Args:
        token_key (str): The key identifying the token.
        resource (str): The resource URI for which the token is requested.

    Returns:
        Optional[str]: The Azure AD token, or None if unavailable.
    """
    if not AZURE_AVAILABLE or credential is None:
        log.warning("Azure identity libraries not available, returning None for token")
        return None

    now = int(time.time())
    # Get token from cache
    cached_token = tokens.get(token_key)

    try:
        # Check if we need a new token
        need_new_token = True
        if cached_token is not None and hasattr(cached_token, "expires_on"):
            if now <= cached_token.expires_on - 60:
                need_new_token = False

        if need_new_token:
            log.debug(f"Requesting new Azure AD token for {resource}...")
            # Get new token
            token_obj = credential.get_token(resource)

            # Store token object
            if token_obj is not None:
                # Store the token object directly
                tokens[token_key] = token_obj

                # Extract token string
                if hasattr(token_obj, "token"):
                    token_str = str(token_obj.token)
                    expires = getattr(token_obj, "expires_on", 0)
                    log.debug(
                        f"Got new Azure AD token for {resource} (expires: {_format_datetime(expires)}, now: {_format_datetime(now)})"
                    )
                    return token_str
            return None
        else:
            # Use cached token - we already checked it's not None above
            if cached_token is None:
                log.error("Unexpected state: cached_token is None when it should exist")
                return None

            # Extract token string
            if hasattr(cached_token, "token"):
                token_str = str(cached_token.token)
                expires = getattr(cached_token, "expires_on", 0)
                log.debug(
                    f"Using cached Azure AD token for {resource} (expires: {_format_datetime(expires)}, now: {_format_datetime(now)})"
                )
                return token_str
            return None
    except CredentialUnavailableError as e:
        log.error(f"Azure credential unavailable: {e}")
        return None
    except Exception as e:
        log.error(f"Failed to get Azure AD token for {resource}: {e}")
        return None
