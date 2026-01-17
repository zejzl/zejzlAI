#!/usr/bin/env python3
"""
Rate Limiter for ZEJZL.NET
Prevents API quota exhaustion for AI providers
"""

import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import deque

logger = logging.getLogger("RateLimiter")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10  # Allow burst of requests


class TokenBucket:
    """Token bucket algorithm for rate limiting"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket

        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from bucket

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait (None = wait forever)

        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.time()

        async with self._lock:
            while True:
                # Refill tokens based on time elapsed
                now = time.time()
                elapsed = now - self.last_refill
                refill_amount = elapsed * self.refill_rate

                self.tokens = min(self.capacity, self.tokens + refill_amount)
                self.last_refill = now

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                # Check timeout
                if timeout is not None:
                    elapsed_wait = time.time() - start_time
                    if elapsed_wait >= timeout:
                        return False

                # Wait a bit before retrying
                wait_time = (tokens - self.tokens) / self.refill_rate
                await asyncio.sleep(min(wait_time, 0.1))


class RateLimiter:
    """
    Multi-tier rate limiter for AI providers
    Enforces per-minute, per-hour, and per-day limits
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config

        # Token buckets for different time scales
        self.minute_bucket = TokenBucket(
            capacity=config.requests_per_minute,
            refill_rate=config.requests_per_minute / 60.0
        )
        self.hour_bucket = TokenBucket(
            capacity=config.requests_per_hour,
            refill_rate=config.requests_per_hour / 3600.0
        )
        self.day_bucket = TokenBucket(
            capacity=config.requests_per_day,
            refill_rate=config.requests_per_day / 86400.0
        )

        # Request history for tracking
        self.request_times: deque = deque(maxlen=1000)
        self._stats_lock = asyncio.Lock()

    async def acquire(self, timeout: Optional[float] = 30.0) -> bool:
        """
        Acquire permission to make a request

        Args:
            timeout: Maximum time to wait for rate limit clearance

        Returns:
            True if request allowed, False if timeout or limit exceeded
        """
        # Try to acquire from all buckets
        tasks = [
            self.minute_bucket.acquire(1, timeout),
            self.hour_bucket.acquire(1, timeout),
            self.day_bucket.acquire(1, timeout)
        ]

        results = await asyncio.gather(*tasks)

        if all(results):
            # Record successful request
            async with self._stats_lock:
                self.request_times.append(time.time())
            return True
        else:
            logger.warning("Rate limit exceeded - request denied")
            return False

    async def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        async with self._stats_lock:
            now = time.time()

            # Count requests in different time windows
            requests_last_minute = sum(1 for t in self.request_times if now - t < 60)
            requests_last_hour = sum(1 for t in self.request_times if now - t < 3600)
            requests_last_day = sum(1 for t in self.request_times if now - t < 86400)

            return {
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour,
                "requests_last_day": requests_last_day,
                "minute_limit": self.config.requests_per_minute,
                "hour_limit": self.config.requests_per_hour,
                "day_limit": self.config.requests_per_day,
                "minute_tokens_available": int(self.minute_bucket.tokens),
                "hour_tokens_available": int(self.hour_bucket.tokens),
                "day_tokens_available": int(self.day_bucket.tokens),
            }


class ProviderRateLimiter:
    """
    Rate limiter manager for multiple AI providers
    Each provider has independent rate limits
    """

    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self._lock = asyncio.Lock()

        # Default rate limits per provider (adjust based on actual API limits)
        self.default_configs = {
            "chatgpt": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
            "claude": RateLimitConfig(
                requests_per_minute=50,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
            "gemini": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1500,
                requests_per_day=15000
            ),
            "grok": RateLimitConfig(
                requests_per_minute=50,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
            "deepseek": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
            "qwen": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
            "zai": RateLimitConfig(
                requests_per_minute=60,
                requests_per_hour=1000,
                requests_per_day=10000
            ),
        }

    async def get_limiter(self, provider: str) -> RateLimiter:
        """Get or create rate limiter for provider"""
        provider = provider.lower()

        if provider not in self.limiters:
            async with self._lock:
                if provider not in self.limiters:
                    config = self.default_configs.get(
                        provider,
                        RateLimitConfig()  # Default config for unknown providers
                    )
                    self.limiters[provider] = RateLimiter(config)
                    logger.info(f"Created rate limiter for {provider}")

        return self.limiters[provider]

    async def acquire(self, provider: str, timeout: Optional[float] = 30.0) -> bool:
        """Acquire permission to make request to provider"""
        limiter = await self.get_limiter(provider)
        return await limiter.acquire(timeout)

    async def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all providers"""
        stats = {}
        for provider, limiter in self.limiters.items():
            stats[provider] = await limiter.get_stats()
        return stats


# Global rate limiter instance
_global_rate_limiter: Optional[ProviderRateLimiter] = None


def get_rate_limiter() -> ProviderRateLimiter:
    """Get global rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = ProviderRateLimiter()
    return _global_rate_limiter
