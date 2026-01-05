"""
Rate Limiter - Prevents hitting exchange API rate limits.
"""

import asyncio
from collections import deque
import logging
import time


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    Prevents bot from hitting exchange rate limits and getting banned.
    """

    def __init__(self, max_calls: int = 10, time_window: int = 1):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum number of calls allowed in the time window
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.call_times = deque()
        self.semaphore = asyncio.Semaphore(max_calls)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def acquire(self, endpoint: str = "general"):
        """
        Acquire permission to make an API call.
        Will wait if rate limit would be exceeded.

        Args:
            endpoint: API endpoint name (for logging)
        """
        async with self.semaphore:
            now = time.time()

            # Remove calls outside the time window
            while self.call_times and self.call_times[0] < now - self.time_window:
                self.call_times.popleft()

            # If at limit, wait until oldest call expires
            if len(self.call_times) >= self.max_calls:
                sleep_time = self.call_times[0] + self.time_window - now
                if sleep_time > 0:
                    self.logger.debug(
                        f"Rate limit reached. Waiting {sleep_time:.2f}s before calling {endpoint}"
                    )
                    await asyncio.sleep(sleep_time)
                    # Remove expired call after waiting
                    self.call_times.popleft()

            # Record this call
            self.call_times.append(time.time())

    def get_stats(self) -> dict[str, any]:
        """Get rate limiter statistics."""
        now = time.time()
        recent_calls = sum(1 for t in self.call_times if t > now - self.time_window)

        return {
            "max_calls_per_window": self.max_calls,
            "time_window_seconds": self.time_window,
            "recent_calls": recent_calls,
            "remaining_calls": max(0, self.max_calls - recent_calls),
            "utilization_percent": (recent_calls / self.max_calls) * 100,
        }


class ExchangeRateLimiter:
    """
    Exchange-specific rate limiter with different limits per endpoint.
    """

    # Default limits for common exchanges (conservative)
    EXCHANGE_LIMITS: dict = {  # noqa: RUF012
        "kraken": {"public": (1, 1), "private": (15, 3), "orders": (10, 1)},  # (max_calls, window_seconds)
        "binance": {"public": (20, 1), "private": (10, 1), "orders": (10, 1)},
        "bybit": {"public": (50, 1), "private": (50, 1), "orders": (50, 1)},
        "coinbase": {"public": (10, 1), "private": (15, 1), "orders": (10, 1)},
    }

    def __init__(self, exchange_name: str):
        """
        Initialize exchange-specific rate limiter.

        Args:
            exchange_name: Name of the exchange (e.g., 'kraken', 'binance')
        """
        self.exchange_name = exchange_name.lower()
        self.logger = logging.getLogger(self.__class__.__name__)

        # Get limits for this exchange
        limits = self.EXCHANGE_LIMITS.get(self.exchange_name, {"public": (10, 1), "private": (5, 1), "orders": (5, 1)})

        # Create rate limiters for each endpoint type
        self.limiters = {
            "public": RateLimiter(*limits["public"]),
            "private": RateLimiter(*limits["private"]),
            "orders": RateLimiter(*limits["orders"]),
        }

        self.logger.info(
            f"Rate limiter initialized for {exchange_name}: "
            f"public={limits['public']}, private={limits['private']}, orders={limits['orders']}"
        )

    async def acquire(self, endpoint_type: str = "private"):
        """
        Acquire permission for an API call.

        Args:
            endpoint_type: Type of endpoint ('public', 'private', or 'orders')
        """
        limiter = self.limiters.get(endpoint_type, self.limiters["private"])
        await limiter.acquire(f"{self.exchange_name}/{endpoint_type}")

    def get_stats(self) -> dict[str, dict]:
        """Get statistics for all rate limiters."""
        return {
            endpoint: limiter.get_stats()
            for endpoint, limiter in self.limiters.items()
        }
