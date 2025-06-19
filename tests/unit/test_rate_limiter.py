"""
Unit tests for rate limiter functionality.
"""

import time
from unittest.mock import patch

import pytest

from core.utils.rate_limiter import RateLimitConfig, RateLimiter, RateLimitStrategy, create_rate_limiter_from_config


@pytest.mark.unit
class TestRateLimitConfig:
    """Test rate limit configuration."""

    def test_rate_limit_config_creation(self):
        """Test basic rate limit config creation."""
        config = RateLimitConfig(
            enabled=True, strategy=RateLimitStrategy.SLIDING_WINDOW, requests_per_minute=100, tokens_per_minute=10000
        )

        assert config.enabled is True
        assert config.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert config.requests_per_minute == 100
        assert config.tokens_per_minute == 10000

    def test_rate_limit_config_defaults(self):
        """Test default rate limit config values."""
        config = RateLimitConfig()

        assert config.enabled is False
        assert config.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert config.requests_per_minute is None
        assert config.tokens_per_minute is None


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        config = RateLimitConfig(enabled=True, strategy=RateLimitStrategy.SLIDING_WINDOW, requests_per_minute=100)

        limiter = RateLimiter(config)

        assert limiter.config == config
        assert hasattr(limiter, "_lock")

    def test_rate_limiter_disabled(self):
        """Test disabled rate limiter."""
        config = RateLimitConfig(enabled=False)
        limiter = RateLimiter(config)

        # Should allow requests without limitation when disabled
        wait_time = limiter.acquire()
        assert wait_time == 0.0

    def test_rate_limiter_basic_functionality(self):
        """Test basic rate limiting functionality."""
        config = RateLimitConfig(
            enabled=True,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            requests_per_minute=60,  # 1 per second
            max_burst_requests=5,
        )

        limiter = RateLimiter(config)

        # First request should have minimal wait time
        wait_time = limiter.acquire()
        assert isinstance(wait_time, (int, float))
        assert wait_time >= 0

    def test_rate_limiter_token_limiting(self):
        """Test token-based rate limiting."""
        config = RateLimitConfig(
            enabled=True, strategy=RateLimitStrategy.TOKEN_BUCKET, tokens_per_minute=1000, requests_per_minute=10
        )

        limiter = RateLimiter(config)

        # Test with token usage
        wait_time = limiter.acquire(estimated_tokens=100)
        assert isinstance(wait_time, (int, float))
        assert wait_time >= 0

    def test_rate_limiter_statistics(self):
        """Test rate limiter statistics."""
        config = RateLimitConfig(enabled=True)
        limiter = RateLimiter(config)

        # Make some requests
        limiter.acquire()

        stats = limiter.get_statistics()
        assert isinstance(stats, dict)
        assert "total_requests" in stats

    def test_rate_limiter_statistics_tracking(self):
        """Test rate limiter statistics tracking."""
        config = RateLimitConfig(enabled=True)
        limiter = RateLimiter(config)

        # Make some requests
        limiter.acquire()
        limiter.acquire()

        # Check statistics are tracked
        stats = limiter.get_statistics()
        assert stats["total_requests"] >= 2

        # Should be able to make more requests
        wait_time = limiter.acquire()
        assert isinstance(wait_time, (int, float))

    def test_sliding_window_strategy(self):
        """Test sliding window strategy."""
        config = RateLimitConfig(enabled=True, strategy=RateLimitStrategy.SLIDING_WINDOW, requests_per_minute=60)

        limiter = RateLimiter(config)
        assert limiter.config.strategy == RateLimitStrategy.SLIDING_WINDOW

    def test_fixed_window_strategy(self):
        """Test fixed window strategy."""
        config = RateLimitConfig(enabled=True, strategy=RateLimitStrategy.FIXED_WINDOW, requests_per_minute=60)

        limiter = RateLimiter(config)
        assert limiter.config.strategy == RateLimitStrategy.FIXED_WINDOW

    def test_token_bucket_strategy(self):
        """Test token bucket strategy."""
        config = RateLimitConfig(enabled=True, strategy=RateLimitStrategy.TOKEN_BUCKET, requests_per_minute=60)

        limiter = RateLimiter(config)
        assert limiter.config.strategy == RateLimitStrategy.TOKEN_BUCKET


@pytest.mark.unit
class TestRateLimiterFactory:
    """Test rate limiter factory functionality."""

    def test_create_rate_limiter_from_config(self):
        """Test creating rate limiter from config."""
        limiter = create_rate_limiter_from_config(enabled=True, strategy="sliding_window", requests_per_minute=100)

        assert isinstance(limiter, RateLimiter)
        assert limiter.config.enabled is True
        assert limiter.config.strategy == RateLimitStrategy.SLIDING_WINDOW
        assert limiter.config.requests_per_minute == 100

    def test_create_disabled_rate_limiter(self):
        """Test creating disabled rate limiter."""
        limiter = create_rate_limiter_from_config(enabled=False)

        assert isinstance(limiter, RateLimiter)
        assert limiter.config.enabled is False

    def test_rate_limiter_with_preset(self):
        """Test rate limiter with preset configuration."""
        # Test with preset-like configuration
        limiter = create_rate_limiter_from_config(
            enabled=True,
            strategy="sliding_window",
            requests_per_minute=500,  # OpenAI GPT-4 like
            tokens_per_minute=10000,
            max_burst_requests=50,
        )

        assert isinstance(limiter, RateLimiter)

    def test_invalid_strategy_handling(self):
        """Test handling of invalid strategy."""
        limiter = create_rate_limiter_from_config(enabled=True, strategy="invalid_strategy", requests_per_minute=60)

        # Should create with fallback strategy
        assert isinstance(limiter, RateLimiter)
        assert limiter.config.strategy == RateLimitStrategy.SLIDING_WINDOW

    def test_negative_limits_handling(self):
        """Test handling of negative limits."""
        limiter = create_rate_limiter_from_config(enabled=True, requests_per_minute=-10, tokens_per_minute=-100)

        # Should handle negative values gracefully
        assert isinstance(limiter, RateLimiter)
        assert limiter.config.requests_per_minute == -10
        assert limiter.config.tokens_per_minute == -100


@pytest.mark.unit
class TestRateLimiterIntegration:
    """Test rate limiter integration scenarios."""

    def test_rate_limiter_with_actual_timing(self):
        """Test rate limiter with actual timing (short duration)."""
        config = RateLimitConfig(
            enabled=True,
            strategy=RateLimitStrategy.FIXED_WINDOW,
            requests_per_minute=120,  # 2 per second
        )

        limiter = RateLimiter(config)

        # Make rapid requests
        start_time = time.time()
        total_wait_time = 0

        for _ in range(5):
            wait_time = limiter.acquire()
            total_wait_time += wait_time

        elapsed = time.time() - start_time

        # Should have completed reasonably quickly
        assert elapsed < 10.0
        assert total_wait_time >= 0

    def test_rate_limiter_concurrent_access(self):
        """Test rate limiter with concurrent access simulation."""
        config = RateLimitConfig(enabled=True, strategy=RateLimitStrategy.SLIDING_WINDOW, requests_per_minute=60)

        limiter = RateLimiter(config)

        # Simulate concurrent requests
        wait_times = []
        for _ in range(10):
            wait_time = limiter.acquire()
            wait_times.append(wait_time)

        # Should handle multiple requests
        assert len(wait_times) == 10
        assert all(isinstance(wt, (int, float)) for wt in wait_times)
        assert all(wt >= 0 for wt in wait_times)
