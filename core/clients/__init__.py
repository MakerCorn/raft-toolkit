"""
Client utilities for OpenAI and Azure OpenAI services.
"""
from .openai_client import build_openai_client, is_azure
from .stats import UsageStats, StatsCompleter, ChatCompleter, CompletionsCompleter

__all__ = [
    'build_openai_client',
    'is_azure',
    'UsageStats',
    'StatsCompleter', 
    'ChatCompleter',
    'CompletionsCompleter'
]