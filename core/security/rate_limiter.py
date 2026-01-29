"""
Rate limiting middleware to prevent API abuse and DoS attacks.
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import DefaultDict

from aiohttp import web


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    
    Limits requests per IP address to prevent abuse.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute per IP
            burst_size: Maximum burst of requests allowed
        """
        self.rate = requests_per_minute / 60.0  # Convert to requests per second
        self.burst_size = burst_size
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Store tokens and last update time for each IP
        self.buckets: DefaultDict[str, dict] = defaultdict(
            lambda: {"tokens": burst_size, "last_update": time.time()}
        )
        
        # Cleanup task
        self._cleanup_task = None
    
    def start_cleanup(self):
        """Start periodic cleanup of old entries."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Periodically clean up old bucket entries."""
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            current_time = time.time()
            
            # Remove buckets that haven't been accessed in 10 minutes
            old_ips = [
                ip for ip, bucket in self.buckets.items()
                if current_time - bucket["last_update"] > 600
            ]
            
            for ip in old_ips:
                del self.buckets[ip]
            
            if old_ips:
                self.logger.debug(f"Cleaned up {len(old_ips)} old rate limit entries")
    
    def is_allowed(self, ip_address: str) -> bool:
        """
        Check if a request from the given IP is allowed.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        bucket = self.buckets[ip_address]
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - bucket["last_update"]
        bucket["tokens"] = min(
            self.burst_size,
            bucket["tokens"] + time_elapsed * self.rate
        )
        bucket["last_update"] = current_time
        
        # Check if we have tokens available
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        
        self.logger.warning(f"Rate limit exceeded for IP: {ip_address}")
        return False
    
    def get_retry_after(self, ip_address: str) -> int:
        """
        Get seconds until next request is allowed.
        
        Args:
            ip_address: Client IP address
            
        Returns:
            Seconds until rate limit resets
        """
        bucket = self.buckets[ip_address]
        tokens_needed = 1 - bucket["tokens"]
        
        if tokens_needed <= 0:
            return 0
        
        return int(tokens_needed / self.rate) + 1


def create_rate_limit_middleware(rate_limiter: RateLimiter):
    """
    Create middleware for rate limiting.
    
    Args:
        rate_limiter: RateLimiter instance
        
    Returns:
        Middleware function
    """
    @web.middleware
    async def rate_limit_middleware(request, handler):
        # Skip rate limiting for static files
        if (request.path.startswith("/static") or
            request.path.endswith((".html", ".css", ".js", ".png", ".jpg", ".svg")) or
            request.path == "/"):
            return await handler(request)
        
        # Get client IP address
        # Check X-Forwarded-For header first (for proxies)
        ip_address = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        
        if not ip_address:
            # Fallback to direct connection IP
            ip_address = request.remote or "unknown"
        
        # Check rate limit
        if not rate_limiter.is_allowed(ip_address):
            retry_after = rate_limiter.get_retry_after(ip_address)
            
            return web.json_response(
                {
                    "success": False,
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                status=429,
                headers={"Retry-After": str(retry_after)}
            )
        
        return await handler(request)
    
    return rate_limit_middleware
