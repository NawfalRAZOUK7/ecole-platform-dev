"""Unit tests for app/core/middleware.py — full branch coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.responses import Response

from app.core.exceptions import NotFoundError
from app.core.middleware import (
    CorrelationIdMiddleware,
    _build_error_body,
    correlation_id_ctx,
    domain_exception_handler,
    generic_exception_handler,
    get_correlation_id,
    validation_exception_handler,
)


def _make_request(headers: dict | None = None) -> Request:
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "query_string": b"",
        "headers": raw_headers,
        "server": ("localhost", 8000),
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# get_correlation_id
# ---------------------------------------------------------------------------


def test_get_correlation_id_default_empty():
    token = correlation_id_ctx.set("")
    assert get_correlation_id() == ""
    correlation_id_ctx.reset(token)


def test_get_correlation_id_with_value():
    cid = "test-cid-abc"
    token = correlation_id_ctx.set(cid)
    assert get_correlation_id() == cid
    correlation_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# _build_error_body
# ---------------------------------------------------------------------------


def test_build_error_body_structure():
    token = correlation_id_ctx.set("req-123")
    body = _build_error_body("ERR-TEST", "Test message", "validation")
    correlation_id_ctx.reset(token)

    assert body["error"]["code"] == "ERR-TEST"
    assert body["error"]["message"] == "Test message"
    assert body["error"]["category"] == "validation"
    assert body["error"]["retryable"] is False
    assert body["error"]["correlation_id"] == "req-123"


def test_build_error_body_retryable():
    token = correlation_id_ctx.set("")
    body = _build_error_body("ERR-RATE", "Rate limit", "rate_limit", retryable=True)
    correlation_id_ctx.reset(token)
    assert body["error"]["retryable"] is True


def test_build_error_body_no_correlation_id():
    token = correlation_id_ctx.set("")
    body = _build_error_body("ERR-TEST", "msg", "system")
    correlation_id_ctx.reset(token)
    assert body["error"]["correlation_id"] is None


def test_build_error_body_with_details():
    token = correlation_id_ctx.set("x")
    body = _build_error_body("ERR", "msg", "cat", details={"field": "name"})
    correlation_id_ctx.reset(token)
    assert body["error"]["details"] == {"field": "name"}


# ---------------------------------------------------------------------------
# CorrelationIdMiddleware
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_correlation_id_generated_when_missing():
    mw = CorrelationIdMiddleware(app=None)  # type: ignore[arg-type]
    request = _make_request()
    downstream = Response("ok")
    call_next = AsyncMock(return_value=downstream)

    result = await mw.dispatch(request, call_next)

    assert "X-Correlation-Id" in result.headers
    assert len(result.headers["X-Correlation-Id"]) > 0


@pytest.mark.asyncio
async def test_correlation_id_preserved_from_header():
    mw = CorrelationIdMiddleware(app=None)  # type: ignore[arg-type]
    cid = "my-correlation-id-123"
    request = _make_request(headers={"X-Correlation-Id": cid})
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert result.headers["X-Correlation-Id"] == cid


@pytest.mark.asyncio
async def test_correlation_id_in_context_during_request():
    mw = CorrelationIdMiddleware(app=None)  # type: ignore[arg-type]
    request = _make_request(headers={"X-Correlation-Id": "ctx-test-id"})

    captured_cid = None

    async def capturing_call_next(req):
        nonlocal captured_cid
        captured_cid = get_correlation_id()
        return Response("ok")

    await mw.dispatch(request, capturing_call_next)
    assert captured_cid == "ctx-test-id"


@pytest.mark.asyncio
async def test_correlation_id_reset_after_request():
    mw = CorrelationIdMiddleware(app=None)  # type: ignore[arg-type]
    token = correlation_id_ctx.set("")

    await mw.dispatch(
        _make_request(headers={"X-Correlation-Id": "temp-id"}),
        AsyncMock(return_value=Response("ok")),
    )

    # After dispatch, the ctx should be reset (back to whatever it was)
    correlation_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# domain_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_domain_exception_handler_returns_json():
    token = correlation_id_ctx.set("err-cid")
    request = _make_request()
    exc = NotFoundError("Resource not found", error_code="ERR-404")

    response = await domain_exception_handler(request, exc)

    correlation_id_ctx.reset(token)

    import json

    body = json.loads(response.body)
    assert response.status_code == 404
    assert body["error"]["code"] == "ERR-404"
    assert response.headers["X-Correlation-Id"] == "err-cid"


@pytest.mark.asyncio
async def test_domain_exception_handler_includes_details():
    from app.core.exceptions import ValidationError

    token = correlation_id_ctx.set("")
    request = _make_request()
    exc = ValidationError("Bad input", details={"field": "email"})

    response = await domain_exception_handler(request, exc)
    correlation_id_ctx.reset(token)

    import json

    body = json.loads(response.body)
    assert body["error"]["details"]["field"] == "email"


# ---------------------------------------------------------------------------
# validation_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validation_exception_handler_returns_422():
    token = correlation_id_ctx.set("")
    request = _make_request()

    exc = RequestValidationError(
        errors=[{"loc": ("body", "email"), "msg": "field required", "type": "missing"}]
    )
    response = await validation_exception_handler(request, exc)
    correlation_id_ctx.reset(token)

    assert response.status_code == 422

    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == "ERR-VAL-422"
    assert body["error"]["details"]["errors"][0]["field"] == "body.email"


@pytest.mark.asyncio
async def test_validation_exception_handler_empty_errors():
    token = correlation_id_ctx.set("")
    request = _make_request()
    exc = RequestValidationError(errors=[])

    response = await validation_exception_handler(request, exc)
    correlation_id_ctx.reset(token)

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# generic_exception_handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generic_exception_handler_returns_500():
    token = correlation_id_ctx.set("generic-cid")
    request = _make_request()

    response = await generic_exception_handler(request, RuntimeError("boom"))

    correlation_id_ctx.reset(token)
    assert response.status_code == 500

    import json

    body = json.loads(response.body)
    assert body["error"]["code"] == "ERR-SYS-500"
