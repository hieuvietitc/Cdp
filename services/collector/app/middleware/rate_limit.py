"""
Redis sliding-window rate limiter.

Per write_key: default 1000 requests / 60 seconds.
Returns HTTP 429 when limit exceeded.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

import redis as redis_lib
from cdp_shared.config import settings

RATE_LIMIT_REQUESTS = 1000   # max requests per window
RATE_LIMIT_WINDOW_SEC = 60   # rolling window in seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW_SEC):
        super().__init__(app)
        self._redis = redis_lib.Redis.from_url(settings.redis_url, decode_responses=True)
        self.requests = requests
        self.window = window

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit event ingestion paths
        if not request.url.path.startswith("/v1/"):
            return await call_next(request)

        write_key = await self._extract_write_key(request)
        if not write_key:
            return await call_next(request)

        allowed, remaining, retry_after = self._check(write_key)
        if not allowed:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                headers={
                    "Content-Type": "application/json",
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _check(self, write_key: str) -> tuple[bool, int, int]:
        """Sliding window counter using Redis sorted set. Returns (allowed, remaining, retry_after_sec)."""
        now = time.time()
        window_start = now - self.window
        key = f"cdp:rl:{write_key}"

        pipe = self._redis.pipeline()
        # Remove old entries outside window
        pipe.zremrangebyscore(key, "-inf", window_start)
        # Count current window
        pipe.zcard(key)
        # Add this request
        pipe.zadd(key, {str(now): now})
        # Set expiry on key (cleanup)
        pipe.expire(key, self.window * 2)
        results = pipe.execute()

        count = results[1]  # count BEFORE this request
        if count >= self.requests:
            # Get oldest entry to compute retry_after
            oldest = self._redis.zrange(key, 0, 0, withscores=True)
            retry_after = int(self.window - (now - oldest[0][1])) + 1 if oldest else self.window
            return False, 0, retry_after

        return True, self.requests - count - 1, 0

    @staticmethod
    async def _extract_write_key(request: Request) -> str | None:
        """Extract write_key from body without consuming the stream for GET/OPTIONS."""
        if request.method in ("GET", "OPTIONS", "HEAD"):
            return None
        try:
            body = await request.body()
            import json
            data = json.loads(body)
            return data.get("write_key")
        except Exception:
            return None
