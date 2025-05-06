
from azure.identity import DefaultAzureCredential
import logging
import time

from datetime import datetime, timezone

log = logging.getLogger(__name__)


tokens = {}

credential = DefaultAzureCredential()

def get_db_token():
    return _get_token("db_token", "https://ossrdbms-aad.database.windows.net/.default")

def get_azure_openai_token():
    return get_cognitive_service_token()

def get_cognitive_service_token():
    return _get_token("cognitive_token", "https://cognitiveservices.azure.com/.default") 

def _format_datetime(dt):
    return datetime.utcfromtimestamp(dt).replace(tzinfo=timezone.utc).astimezone().strftime('%Y-%m-%d %H:%M:%S')

def _get_token(token_key, resource):
    now = int(time.time())

    global tokens
    
    token = None

    if token_key in tokens:
        token = tokens[token_key]

    if token is None:
        log.debug(f"No existing token for {resource}...")
        token = credential.get_token(resource)
        tokens[token_key] = token
        
        log.debug(f"Got a new Azure AD token {resource} (expires: {_format_datetime(token.expires_on)}, now: {_format_datetime(now)})")
         
    else:     
        log.debug(f"Token exists for {resource} (expired: {_format_datetime(token.expires_on)}, now: {_format_datetime(now)})")
         
        if now > token.expires_on - 60:
            log.debug(f"Existing token has been expired, get a new Azure AD token for {resource}...")
        
            token = credential.get_token(resource)
            tokens[token_key] = token

            log.debug(f"Got a new token for {resource} (expired: {_format_datetime(token.expires_on)}, now: {_format_datetime(now)})")
        else:       
            log.debug(f"Using cached Azure AD token for {resource}")
    
    return token.token    