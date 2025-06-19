import time
from abc import ABC
from threading import Lock
from typing import Any, Optional


class UsageStats:
    """Tracks and aggregates usage statistics for API calls."""

    def __init__(self) -> None:
        self.start = time.time()
        self.completion_tokens = 0
        self.prompt_tokens = 0
        self.total_tokens = 0
        self.end: Optional[float] = None
        self.duration: float = 0.0
        self.calls = 0

    def __add__(self, other: "UsageStats") -> "UsageStats":
        """Aggregate two UsageStats instances."""
        stats = UsageStats()
        stats.start = min(self.start, other.start)
        stats.end = max(self.end or 0, other.end or 0)
        stats.completion_tokens = self.completion_tokens + other.completion_tokens
        stats.prompt_tokens = self.prompt_tokens + other.prompt_tokens
        stats.total_tokens = self.total_tokens + other.total_tokens
        stats.duration = self.duration + other.duration
        stats.calls = self.calls + other.calls
        return stats


class StatsCompleter(ABC):
    """Abstract base class for completers that collect statistics on usage."""

    def __init__(self, create_func):
        """
        Args:
            create_func (callable): The function to create the completion (e.g., client.chat.completions.create).
        """
        self.create_func = create_func
        self.stats: Optional[UsageStats] = None
        self.lock = Lock()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        """Call the completion function and collect statistics."""
        response = self.create_func(*args, **kwds)
        with self.lock:
            if not self.stats:
                self.stats = UsageStats()
            self.stats.completion_tokens += response.usage.completion_tokens
            self.stats.prompt_tokens += response.usage.prompt_tokens
            self.stats.total_tokens += response.usage.total_tokens
            self.stats.calls += 1
            return response

    def get_stats_and_reset(self) -> Optional[UsageStats]:
        """Get the current statistics and reset the collector."""
        with self.lock:
            end = time.time()
            stats = self.stats
            if stats:
                stats.end = end
                stats.duration = end - stats.start
                self.stats = None
            return stats


class ChatCompleter(StatsCompleter):
    """Completer for chat-based interactions."""

    def __init__(self, client):
        """
        Args:
            client (Any): The client instance for chat completions.
        """
        super().__init__(client.chat.completions.create)


class CompletionsCompleter(StatsCompleter):
    """Completer for standard text completions."""

    def __init__(self, client):
        """
        Args:
            client (Any): The client instance for text completions.
        """
        super().__init__(client.completions.create)
