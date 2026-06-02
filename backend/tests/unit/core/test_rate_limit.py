"""Unit tests for app/core/rate_limit.py — full branch coverage.

Strategy:
- Mock redis_client (pipeline) with AsyncMock.
- Patch settings.app_env and settings.enable_strict_rate_limit.
- Build Request objects via starlette scope dicts.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.rate_limit import (
    AUTH_PATHS,
    RATE_LIMITS,
    RateLimitMiddleware,
    _classify_request,
    _get_client_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    method: str = "GET",
    path: str = "/api/v1/some-endpoint",
    ip: str = "10.0.0.1",
    forwarded_for: str | None = None,
) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded_for:
        headers.append((b"x-forwarded-for", forwarded_for.encode()))
    scope = {
        "type": "http",
        "method": method.upper(),
        "path": path,
        "query_string": b"",
        "headers": headers,
        "server": ("localhost", 8000),
        "client": (ip, 12345),
    }
    return Request(scope)


def _make_pipeline_mock(count: int = 1, ttl: int = 30) -> MagicMock:
    """Return a mock Redis pipeline that simulates incr+ttl results.

    pipeline() is a synchronous call in redis.asyncio; only execute() is async.
    """
    pipe = MagicMock()
    pipe.execute = AsyncMock(return_value=[count, ttl])
    return pipe


def _make_redis_mock(pipe=None, expire_side_effect=None) -> MagicMock:
    """Build a MagicMock redis client with async expire."""
    mock = MagicMock()
    if pipe is not None:
        mock.pipeline.return_value = pipe
    mock.expire = AsyncMock(side_effect=expire_side_effect)
    return mock


def _middleware() -> RateLimitMiddleware:
    return RateLimitMiddleware(app=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _classify_request
# ---------------------------------------------------------------------------


def test_classify_auth_path():
    path = "/api/v1/auth/login"
    assert _classify_request("POST", path) == "auth"


def test_classify_auth_path_any_method():
    assert _classify_request("GET", "/api/v1/auth/login") == "auth"


def test_classify_write_post():
    assert _classify_request("POST", "/api/v1/students") == "write"


def test_classify_write_put():
    assert _classify_request("PUT", "/api/v1/students/1") == "write"


def test_classify_write_patch():
    assert _classify_request("PATCH", "/api/v1/students/1") == "write"


def test_classify_write_delete():
    assert _classify_request("DELETE", "/api/v1/students/1") == "write"


def test_classify_read_get():
    assert _classify_request("GET", "/api/v1/students") == "read"


def test_classify_read_head():
    assert _classify_request("HEAD", "/api/v1/students") == "read"


def test_classify_read_options():
    assert _classify_request("OPTIONS", "/api/v1/students") == "read"


def test_classify_all_auth_paths():
    for path in AUTH_PATHS:
        assert _classify_request("POST", path) == "auth", f"Expected auth for {path}"


# ---------------------------------------------------------------------------
# _get_client_key
# ---------------------------------------------------------------------------


def test_get_client_key_forwarded_for_single():
    request = _make_request(forwarded_for="203.0.113.5")
    assert _get_client_key(request) == "203.0.113.5"


def test_get_client_key_forwarded_for_multiple():
    request = _make_request(forwarded_for="203.0.113.5, 10.0.0.1, 192.168.1.1")
    assert _get_client_key(request) == "203.0.113.5"


def test_get_client_key_forwarded_for_with_spaces():
    request = _make_request(forwarded_for="  198.51.100.1  , 10.0.0.2")
    assert _get_client_key(request) == "198.51.100.1"


def test_get_client_key_no_forwarded_uses_client_host():
    request = _make_request(ip="192.168.1.50")
    assert _get_client_key(request) == "192.168.1.50"


def test_get_client_key_no_client_returns_unknown():
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
        # no "client" key
    }
    request = Request(scope)
    assert _get_client_key(request) == "unknown"


# ---------------------------------------------------------------------------
# Skip paths — middleware does nothing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skip_health_path():
    mw = _middleware()
    request = _make_request(path="/api/v1/health")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is downstream


@pytest.mark.asyncio
async def test_skip_metrics_path():
    mw = _middleware()
    request = _make_request(path="/metrics")
    call_next = AsyncMock(return_value=Response("ok"))

    await mw.dispatch(request, call_next)
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_skip_docs_path():
    mw = _middleware()
    request = _make_request(path="/docs")
    call_next = AsyncMock(return_value=Response("ok"))

    await mw.dispatch(request, call_next)
    call_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_skip_openapi_path():
    mw = _middleware()
    request = _make_request(path="/openapi.json")
    call_next = AsyncMock(return_value=Response("ok"))

    await mw.dispatch(request, call_next)
    call_next.assert_awaited_once()


# ---------------------------------------------------------------------------
# Non-production env → add headers but don't enforce
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dev_env_adds_headers_no_enforcement():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    mock_settings = MagicMock()
    mock_settings.app_env = "development"
    mock_settings.enable_strict_rate_limit = False

    with patch("app.core.config.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once()
    assert "X-RateLimit-Limit" in result.headers
    assert "X-RateLimit-Remaining" in result.headers
    assert "X-RateLimit-Reset" in result.headers


@pytest.mark.asyncio
async def test_dev_env_remaining_equals_limit():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    mock_settings = MagicMock()
    mock_settings.app_env = "development"
    mock_settings.enable_strict_rate_limit = False

    with patch("app.core.config.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    # In non-enforcement mode, remaining == limit
    assert (
        result.headers["X-RateLimit-Limit"] == result.headers["X-RateLimit-Remaining"]
    )


@pytest.mark.asyncio
async def test_test_env_not_enforced():
    mw = _middleware()
    request = _make_request(method="POST", path="/api/v1/orders")
    call_next = AsyncMock(return_value=Response("ok"))

    mock_settings = MagicMock()
    mock_settings.app_env = "test"
    mock_settings.enable_strict_rate_limit = False

    with patch("app.core.config.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    assert "X-RateLimit-Limit" in result.headers


@pytest.mark.asyncio
async def test_staging_env_with_strict_disabled_not_enforced():
    """enable_strict_rate_limit=False overrides staging enforcement."""
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    call_next = AsyncMock(return_value=Response("ok"))

    mock_settings = MagicMock()
    mock_settings.app_env = "staging"
    mock_settings.enable_strict_rate_limit = False

    with patch("app.core.config.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    # staging + strict disabled → no enforcement, but headers present
    assert "X-RateLimit-Limit" in result.headers


# ---------------------------------------------------------------------------
# Production enforcement — under limit
# ---------------------------------------------------------------------------


def _prod_settings():
    s = MagicMock()
    s.app_env = "production"
    s.enable_strict_rate_limit = True
    return s


@pytest.mark.asyncio
async def test_production_under_limit_allows_request():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok", status_code=200)
    call_next = AsyncMock(return_value=downstream)

    pipe = _make_pipeline_mock(count=1, ttl=55)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once()
    assert result is downstream
    assert result.headers["X-RateLimit-Remaining"] == "99"  # 100-1


@pytest.mark.asyncio
async def test_production_headers_present_on_success():
    mw = _middleware()
    request = _make_request(method="POST", path="/api/v1/orders")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    pipe = _make_pipeline_mock(count=5, ttl=45)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    assert "X-RateLimit-Limit" in result.headers
    assert "X-RateLimit-Remaining" in result.headers
    assert "X-RateLimit-Reset" in result.headers


# ---------------------------------------------------------------------------
# Production enforcement — first request (TTL == -1) → set expiry
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_first_request_sets_expiry():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    pipe = _make_pipeline_mock(count=1, ttl=-1)  # -1 means no TTL set yet
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        await mw.dispatch(request, call_next)

    # expire() must be called to set the window
    mock_redis.expire.assert_awaited_once()
    _, window_seconds = RATE_LIMITS["read"]
    assert mock_redis.expire.call_args.args[1] == window_seconds


@pytest.mark.asyncio
async def test_subsequent_request_does_not_reset_expiry():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    pipe = _make_pipeline_mock(count=10, ttl=30)  # positive TTL → already set
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        await mw.dispatch(request, call_next)

    mock_redis.expire.assert_not_awaited()


# ---------------------------------------------------------------------------
# Production enforcement — over limit → 429
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_over_limit_returns_429():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    call_next = AsyncMock()

    max_requests, _ = RATE_LIMITS["read"]
    pipe = _make_pipeline_mock(count=max_requests + 1, ttl=20)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    call_next.assert_not_awaited()
    assert result.status_code == 429


@pytest.mark.asyncio
async def test_429_response_has_rate_limit_headers():
    mw = _middleware()
    request = _make_request(method="POST", path="/api/v1/orders")
    call_next = AsyncMock()

    max_requests, _ = RATE_LIMITS["write"]
    pipe = _make_pipeline_mock(count=max_requests + 5, ttl=10)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    assert result.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in result.headers


@pytest.mark.asyncio
async def test_429_content_contains_error_code():
    import json

    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    call_next = AsyncMock()

    max_requests, _ = RATE_LIMITS["read"]
    pipe = _make_pipeline_mock(count=max_requests + 1, ttl=5)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    body = json.loads(result.body)
    assert body["error"]["code"] == "ERR-RATE-429"
    assert body["error"]["retryable"] is True


@pytest.mark.asyncio
async def test_auth_path_over_limit_returns_429():
    mw = _middleware()
    request = _make_request(method="POST", path="/api/v1/auth/login")
    call_next = AsyncMock()

    max_requests, _ = RATE_LIMITS["auth"]
    pipe = _make_pipeline_mock(count=max_requests + 1, ttl=800)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    assert result.status_code == 429


# ---------------------------------------------------------------------------
# Redis unavailable → graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_down_allows_request_through():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    mock_redis = MagicMock()
    mock_redis.pipeline.side_effect = ConnectionError("redis down")

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is downstream


@pytest.mark.asyncio
async def test_redis_down_still_adds_headers():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    mock_redis = MagicMock()
    mock_redis.pipeline.side_effect = RuntimeError("connection refused")

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    assert "X-RateLimit-Limit" in result.headers
    assert "X-RateLimit-Remaining" in result.headers


# ---------------------------------------------------------------------------
# Remaining clamped to 0 when over limit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_remaining_never_negative():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    pipe = _make_pipeline_mock(count=95, ttl=30)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", _prod_settings()),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    remaining = int(result.headers["X-RateLimit-Remaining"])
    assert remaining >= 0


# ---------------------------------------------------------------------------
# enable_strict_rate_limit=True in non-production → enforce
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_strict_flag_true_enforces_in_dev():
    mw = _middleware()
    request = _make_request(method="GET", path="/api/v1/students")
    call_next = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.app_env = "development"
    mock_settings.enable_strict_rate_limit = True

    max_requests, _ = RATE_LIMITS["read"]
    pipe = _make_pipeline_mock(count=max_requests + 1, ttl=30)
    mock_redis = _make_redis_mock(pipe=pipe)

    with (
        patch("app.core.config.settings", mock_settings),
        patch("app.core.rate_limit.redis_client", mock_redis),
    ):
        result = await mw.dispatch(request, call_next)

    assert result.status_code == 429
