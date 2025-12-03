"""Rate limiter for API calls to prevent hitting rate limits."""

import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API calls.
    
    Allows bursts up to max_tokens, then enforces a steady rate.
    Thread-safe for async usage.
    """
    
    def __init__(
        self,
        max_requests_per_minute: int = 10,
        min_delay_seconds: float = 1.0,
    ):
        """Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum requests allowed per minute
            min_delay_seconds: Minimum delay between consecutive requests
        """
        self.max_rpm = max_requests_per_minute
        self.min_delay = min_delay_seconds
        
        # Token bucket parameters
        self.tokens = float(max_requests_per_minute)
        self.max_tokens = float(max_requests_per_minute)
        self.refill_rate = max_requests_per_minute / 60.0  # tokens per second
        
        self.last_update = time.monotonic()
        self.last_request = 0.0
        self.lock = asyncio.Lock()
        
        logger.info(
            f"Rate limiter initialized: {max_requests_per_minute} RPM, "
            f"{min_delay_seconds}s min delay"
        )
    
    async def acquire(self) -> None:
        """Acquire permission to make a request.
        
        Blocks until a token is available, respecting both:
        1. Token bucket (max RPM)
        2. Minimum delay between requests
        """
        async with self.lock:
            now = time.monotonic()
            
            # Refill tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_tokens,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_update = now
            
            # Wait if we don't have tokens
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.refill_rate
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s for token")
                await asyncio.sleep(wait_time)
                self.tokens = 1.0
                self.last_update = time.monotonic()
            
            # Enforce minimum delay between requests
            time_since_last = now - self.last_request
            if time_since_last < self.min_delay:
                delay = self.min_delay - time_since_last
                logger.debug(f"Rate limit: enforcing {delay:.2f}s min delay")
                await asyncio.sleep(delay)
            
            # Consume token
            self.tokens -= 1.0
            self.last_request = time.monotonic()
            
            logger.debug(
                f"Rate limit: request approved ({self.tokens:.1f} tokens remaining)"
            )


class NoOpRateLimiter:
    """No-op rate limiter that allows all requests immediately."""
    
    async def acquire(self) -> None:
        """No-op acquire."""
        pass
