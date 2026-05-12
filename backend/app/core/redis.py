"""Redis client for rate limiting, refresh token tracking, and caching.

Reference: Pack D3 — Runtime Configuration (Redis for rate limiting, token rotation)
"""

from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings


class _LazyRedisClient:
    """Lazy proxy that defers Redis connection creation until first use.

    Prevents import-time failures when Redis is unreachable (e.g. CI
    runners that only need the app code but not a live Redis instance).
    """

    def __init__(self) -> None:
        self._client: redis.Redis | None = None

    def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._client

    def __getattr__(self, name: str):
        return getattr(self._get_client(), name)

    def __setattr__(self, name: str, value) -> None:
        if name == "_client":
            super().__setattr__(name, value)
        else:
            setattr(self._get_client(), name, value)


# Async Redis connection pool (singleton) — lazy so imports never block
redis_client: redis.Redis = _LazyRedisClient()  # type: ignore[assignment]


async def get_redis() -> redis.Redis:
    """FastAPI dependency for Redis client."""
    return redis_client
