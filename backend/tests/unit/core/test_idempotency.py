"""Unit tests for app/core/idempotency.py — full branch coverage.

Strategy:
- Mock redis_client with AsyncMock to avoid real Redis dependency.
- Create minimal starlette Request objects via scope dicts.
- Provide async body_iterator on mock responses to exercise caching path.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.idempotency import (
    IDEMPOTENCY_TTL_SECONDS,
    IDEMPOTENT_METHODS,
    IdempotencyMiddleware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(
    method: str = "POST",
    path: str = "/api/v1/orders",
    headers: dict | None = None,
) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": method.upper(),
        "path": path,
        "query_string": b"",
        "headers": raw_headers,
        "server": ("localhost", 8000),
    }
    return Request(scope)


def _make_streaming_response(body: dict, status_code: int = 200) -> MagicMock:
    """Return a mock Response whose body_iterator yields serialised JSON."""
    body_bytes = json.dumps(body).encode()

    async def _iter():
        yield body_bytes

    resp = MagicMock()
    resp.status_code = status_code
    resp.body_iterator = _iter()
    resp.headers = {}
    return resp


def _middleware() -> IdempotencyMiddleware:
    return IdempotencyMiddleware(app=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Non-idempotent methods → pass through
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_request_skipped():
    mw = _middleware()
    request = _make_request(method="GET")
    expected = Response("ok")
    call_next = AsyncMock(return_value=expected)

    result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is expected


@pytest.mark.asyncio
async def test_delete_request_skipped():
    mw = _middleware()
    request = _make_request(method="DELETE")
    expected = Response("ok")
    call_next = AsyncMock(return_value=expected)

    result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is expected


# ---------------------------------------------------------------------------
# Missing Idempotency-Key header → pass through
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_without_key_skipped():
    mw = _middleware()
    request = _make_request(method="POST", headers={})
    expected = Response("ok")
    call_next = AsyncMock(return_value=expected)

    result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is expected


@pytest.mark.asyncio
async def test_put_without_key_skipped():
    mw = _middleware()
    request = _make_request(method="PUT", headers={})
    call_next = AsyncMock(return_value=Response("ok"))

    await mw.dispatch(request, call_next)
    call_next.assert_awaited_once()


# ---------------------------------------------------------------------------
# Redis unavailable → degrade gracefully (pass through)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_down_on_get_passes_through():
    mw = _middleware()
    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "key-redis-down"},
    )
    expected = Response("ok")
    call_next = AsyncMock(return_value=expected)

    mock_redis = AsyncMock()
    mock_redis.get.side_effect = ConnectionError("redis down")

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once_with(request)
    assert result is expected


# ---------------------------------------------------------------------------
# Cache hit → replay cached response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_hit_replays_response():
    mw = _middleware()
    cached_body = {"id": 42, "status": "created"}
    cached_payload = json.dumps({"status_code": 201, "body": cached_body})

    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "replay-key-001"},
    )
    call_next = AsyncMock()

    mock_redis = AsyncMock()
    mock_redis.get.return_value = cached_payload

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    call_next.assert_not_awaited()
    assert isinstance(result, JSONResponse)
    assert result.status_code == 201
    assert result.headers.get("X-Idempotency-Replayed") == "true"


@pytest.mark.asyncio
async def test_cache_hit_body_matches_original():
    mw = _middleware()
    original_body = {"order_id": "abc-123"}
    cached_payload = json.dumps({"status_code": 200, "body": original_body})

    request = _make_request(
        method="PUT",
        headers={"Idempotency-Key": "check-body-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = cached_payload

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, AsyncMock())

    body = json.loads(result.body)
    assert body == original_body


# ---------------------------------------------------------------------------
# Cache hit but corrupted JSON → proceed normally
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_corrupted_cache_proceeds_normally():
    mw = _middleware()
    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "corrupt-key"},
    )
    downstream_response = _make_streaming_response({"ok": True}, status_code=200)
    call_next = AsyncMock(return_value=downstream_response)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = "NOT VALID JSON {{{"
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once()
    assert result is not None


@pytest.mark.asyncio
async def test_cache_hit_missing_body_key_proceeds():
    mw = _middleware()
    # Valid JSON but missing required 'body' key
    bad_payload = json.dumps({"status_code": 200})
    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "bad-schema-key"},
    )
    downstream_response = _make_streaming_response({"result": "ok"}, status_code=200)
    call_next = AsyncMock(return_value=downstream_response)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = bad_payload
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    call_next.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache miss + 2xx response → cache it
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_2xx_response_is_cached():
    mw = _middleware()
    body_payload = {"created": True}
    downstream = _make_streaming_response(body_payload, status_code=201)
    call_next = AsyncMock(return_value=downstream)

    request = _make_request(
        method="POST",
        path="/api/v1/students",
        headers={"Idempotency-Key": "new-resource-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None  # cache miss
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    mock_redis.setex.assert_awaited_once()
    call_args = mock_redis.setex.call_args
    assert call_args.args[1] == IDEMPOTENCY_TTL_SECONDS
    cached = json.loads(call_args.args[2])
    assert cached["body"] == body_payload
    assert cached["status_code"] == 201


@pytest.mark.asyncio
async def test_2xx_response_returned_correctly():
    mw = _middleware()
    body = {"id": 99}
    downstream = _make_streaming_response(body, status_code=200)
    call_next = AsyncMock(return_value=downstream)

    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "return-check-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    assert result.status_code == 200
    assert json.loads(result.body) == body


# ---------------------------------------------------------------------------
# Cache miss + non-2xx response → do NOT cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_4xx_response_not_cached():
    mw = _middleware()
    downstream = _make_streaming_response({"error": "bad"}, status_code=400)
    call_next = AsyncMock(return_value=downstream)

    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "error-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    mock_redis.setex.assert_not_awaited()
    # The original (unconsumed) response is returned
    assert result is downstream


@pytest.mark.asyncio
async def test_5xx_response_not_cached():
    mw = _middleware()
    downstream = _make_streaming_response({"error": "server error"}, status_code=500)
    call_next = AsyncMock(return_value=downstream)

    request = _make_request(
        method="PATCH",
        headers={"Idempotency-Key": "server-error-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    mock_redis.setex.assert_not_awaited()


# ---------------------------------------------------------------------------
# Redis down when caching response → return already-read body
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_down_on_setex_returns_body():
    mw = _middleware()
    body = {"saved": True}
    downstream = _make_streaming_response(body, status_code=200)
    call_next = AsyncMock(return_value=downstream)

    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "setex-fail-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = RuntimeError("redis down on write")

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    # Should still return something (the body we already read)
    assert result is not None
    assert result.status_code == 200


# ---------------------------------------------------------------------------
# Chunk body as str (not bytes)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_body_as_str_chunks():
    """Exercises the `chunk.encode()` branch for str chunks."""
    mw = _middleware()
    body_str = json.dumps({"msg": "hello"})

    async def _str_iter():
        yield body_str  # str, not bytes

    resp = MagicMock()
    resp.status_code = 200
    resp.body_iterator = _str_iter()
    resp.headers = {}
    call_next = AsyncMock(return_value=resp)

    request = _make_request(
        method="POST",
        headers={"Idempotency-Key": "str-chunk-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        result = await mw.dispatch(request, call_next)

    assert result.status_code == 200


# ---------------------------------------------------------------------------
# PATCH method is idempotent
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_method_is_idempotent():
    mw = _middleware()
    body = {"updated": True}
    downstream = _make_streaming_response(body, status_code=200)

    request = _make_request(
        method="PATCH",
        headers={"Idempotency-Key": "patch-key"},
    )

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex = AsyncMock()

    with patch("app.core.idempotency.redis_client", mock_redis):
        await mw.dispatch(request, AsyncMock(return_value=downstream))

    mock_redis.setex.assert_awaited_once()


# ---------------------------------------------------------------------------
# Cache key is scoped to path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_key_includes_path_hash():
    """Different paths with the same Idempotency-Key → different cache keys."""
    mw = _middleware()
    idempotency_key = "same-key"

    calls = []

    async def capture_setex(key, ttl, value):
        calls.append(key)

    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.setex.side_effect = capture_setex

    for path in ("/api/v1/orders", "/api/v1/payments"):
        downstream = _make_streaming_response({"ok": True})
        request = _make_request(
            method="POST",
            path=path,
            headers={"Idempotency-Key": idempotency_key},
        )
        with patch("app.core.idempotency.redis_client", mock_redis):
            await mw.dispatch(request, AsyncMock(return_value=downstream))

    assert len(calls) == 2
    assert calls[0] != calls[1], "Different paths must yield different cache keys"
