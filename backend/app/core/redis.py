"""Redis client for rate limiting, refresh token tracking, and caching.

Reference: Pack D3 — Runtime Configuration (Redis for rate limiting, token rotation)
"""

from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings

# Async Redis connection pool (singleton)
redis_client: redis.Redis = redis.from_url(
    settings.redis_url,
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """FastAPI dependency for Redis client."""
    return redis_client
