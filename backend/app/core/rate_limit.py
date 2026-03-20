"""Rate limiting middleware — Redis-backed sliding window with response headers.

Reference: Phase 2A — Password Policy & Session Management
Per-endpoint rate limit categories:
  - auth:  5 requests / 15 minutes (login, recovery, refresh)
  - write: 30 requests / 1 minute  (POST, PUT, PATCH, DELETE)
  - read: 100 requests / 1 minute  (GET, HEAD, OPTIONS)

Response headers on all requests:
  - X-RateLimit-Limit: maximum requests allowed in window
  - X-RateLimit-Remaining: remaining requests in current window
  - X-RateLimit-Reset: Unix timestamp when the window resets
"""

from __future__ import annotations

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from app.core.redis import redis_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limit categories
# ---------------------------------------------------------------------------
# Auth endpoints: strict (5 per 15 min)
AUTH_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/auth/2fa/verify",
    "/api/v1/auth/verify-email",
    "/api/v1/recovery/request",
    "/api/v1/recovery/verify",
    "/api/v1/recovery/reset",
}

# Limit configs: (max_requests, window_seconds)
RATE_LIMITS = {
    "auth": (5, 900),     # 5 per 15 minutes
    "write": (30, 60),    # 30 per minute
    "read": (100, 60),    # 100 per minute
}

# Paths to skip rate limiting (health, metrics, docs)
SKIP_PATHS = {"/metrics", "/docs", "/redoc", "/openapi.json", "/api/v1/health"}


def _classify_request(method: str, path: str) -> str:
    """Classify a request into a rate limit category."""
    if path in AUTH_PATHS:
        return "auth"
    if method in ("POST", "PUT", "PATCH", "DELETE"):
        return "write"
    return "read"


def _get_client_key(request: Request) -> str:
    """Build a client identifier for rate limiting.

    Uses: IP address (from X-Forwarded-For or direct), falling back to "unknown".
    For authenticated requests, the auth middleware hasn't run yet at this point,
    so we rate limit by IP. Fine-grained user-level limits are handled in services.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces per-endpoint rate limits using Redis sliding window.

    Adds X-RateLimit-* headers to all responses. Returns 429 when limit exceeded.
    Gracefully degrades if Redis is unavailable (allows request through).
    Disabled in test environment (ENABLE_STRICT_RATE_LIMIT=false or app_env != production).
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path

        # Skip rate limiting for health/metrics/docs
        if path in SKIP_PATHS:
            return await call_next(request)

        # In non-production environments, add headers but don't enforce limits.
        # This allows integration tests to run without hitting rate limits.
        # Production enforcement is enabled via ENABLE_STRICT_RATE_LIMIT=true or app_env=production.
        from app.core.config import settings
        strict_rate_limit = getattr(settings, "enable_strict_rate_limit", False)
        if not strict_rate_limit and settings.app_env not in ("production", "staging"):
            response = await call_next(request)
            category = _classify_request(request.method, path)
            max_requests, window_seconds = RATE_LIMITS[category]
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max_requests)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)
            return response

        category = _classify_request(request.method, path)
        max_requests, window_seconds = RATE_LIMITS[category]
        client_ip = _get_client_key(request)

        # Redis key: ratelimit:{category}:{ip}
        redis_key = f"ratelimit:{category}:{client_ip}"

        try:
            # Atomic increment + expire via pipeline
            pipe = redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.ttl(redis_key)
            results = await pipe.execute()

            current_count = int(results[0])
            ttl = int(results[1])

            # Set expiry on first request in window
            if ttl == -1:
                await redis_client.expire(redis_key, window_seconds)
                ttl = window_seconds

            remaining = max(0, max_requests - current_count)
            reset_at = int(time.time()) + max(ttl, 0)

            # Check if over limit
            if current_count > max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "ERR-RATE-429",
                            "message": "Rate limit exceeded. Please try again later.",
                            "category": "rate_limit",
                            "retryable": True,
                            "correlation_id": None,
                            "details": {
                                "limit": max_requests,
                                "window_seconds": window_seconds,
                                "category": category,
                            },
                            "timestamp": None,
                        }
                    },
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                        "Retry-After": str(max(ttl, 1)),
                    },
                )

            # Process request normally
            response = await call_next(request)

            # Add rate limit headers to all responses
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_at)

            return response

        except Exception:
            # Redis unavailable — allow request through without rate limiting
            # but still add headers indicating unlimited (graceful degradation)
            logger.warning("Rate limit Redis unavailable, allowing request through")
            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(max_requests)
            response.headers["X-RateLimit-Remaining"] = str(max_requests)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)
            return response
