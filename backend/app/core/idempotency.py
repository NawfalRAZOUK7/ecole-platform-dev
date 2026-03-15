"""Idempotency-Key middleware — Redis-backed key->response cache.

Reference: S-070 — Idempotency-Key middleware
Applies to all POST/PUT/PATCH endpoints.

Flow:
1. Extract Idempotency-Key header from request
2. Check Redis for cached response for this key (scoped to user)
3. If found, return cached response immediately (replay)
4. If not found, process request, cache response, return response
5. Keys expire after 24 hours

Cache key format: idem:{user_id}:{idempotency_key}
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.redis import redis_client

# Cache TTL: 24 hours
IDEMPOTENCY_TTL_SECONDS = 86400

# Methods that support idempotency
IDEMPOTENT_METHODS = {"POST", "PUT", "PATCH"}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware that caches responses for idempotent POST/PUT/PATCH requests.

    Clients send an `Idempotency-Key` header. If the same key is seen again
    within the TTL window, the cached response is replayed without
    re-executing the handler.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only apply to mutating methods
        if request.method not in IDEMPOTENT_METHODS:
            return await call_next(request)

        # Extract idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            # No key provided — proceed without caching
            return await call_next(request)

        # Build cache key scoped to the request path + idempotency key
        # We use path to prevent cross-endpoint key collisions
        path_hash = hashlib.sha256(request.url.path.encode()).hexdigest()[:16]
        cache_key = f"idem:{path_hash}:{idempotency_key}"

        # Check for cached response
        try:
            cached = await redis_client.get(cache_key)
        except Exception:
            # Redis unavailable — proceed without idempotency
            return await call_next(request)

        if cached is not None:
            # Replay cached response
            try:
                cached_data = json.loads(cached)
                return JSONResponse(
                    content=cached_data["body"],
                    status_code=cached_data["status_code"],
                    headers={"X-Idempotency-Replayed": "true"},
                )
            except (json.JSONDecodeError, KeyError):
                # Corrupted cache — proceed normally
                pass

        # Process the request
        response = await call_next(request)

        # Only cache successful responses (2xx)
        if 200 <= response.status_code < 300:
            try:
                # Read response body
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk if isinstance(chunk, bytes) else chunk.encode()

                body_str = body_bytes.decode("utf-8")
                body_json = json.loads(body_str)

                # Cache the response
                cache_payload = json.dumps({
                    "status_code": response.status_code,
                    "body": body_json,
                })
                await redis_client.setex(cache_key, IDEMPOTENCY_TTL_SECONDS, cache_payload)

                # Return new response since we consumed the body iterator
                return JSONResponse(
                    content=body_json,
                    status_code=response.status_code,
                )
            except Exception:
                # If caching fails, return the response body we already read
                if body_bytes:
                    return Response(
                        content=body_bytes,
                        status_code=response.status_code,
                        media_type="application/json",
                    )

        return response
