"""Unit tests for app/core/security_headers.py — full branch coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.core.security_headers import SecurityHeadersMiddleware


def _make_request(scheme: str = "http", path: str = "/api/test") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": path,
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
        "scheme": scheme,
    }
    return Request(scope)


def _middleware() -> SecurityHeadersMiddleware:
    return SecurityHeadersMiddleware(app=None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Common headers always present
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_content_type_options_header():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert result.headers["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_x_frame_options_header():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert result.headers["X-Frame-Options"] == "DENY"


@pytest.mark.asyncio
async def test_xss_protection_header():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert result.headers["X-XSS-Protection"] == "1; mode=block"


@pytest.mark.asyncio
async def test_referrer_policy_header():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert result.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


@pytest.mark.asyncio
async def test_permissions_policy_header():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert "geolocation=()" in result.headers["Permissions-Policy"]


@pytest.mark.asyncio
async def test_csp_header_present():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert "Content-Security-Policy" in result.headers


# ---------------------------------------------------------------------------
# HTTPS → HSTS added; HTTP → no HSTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hsts_on_https():
    mw = _middleware()
    request = _make_request(scheme="https")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert "Strict-Transport-Security" in result.headers
    assert "max-age=31536000" in result.headers["Strict-Transport-Security"]


@pytest.mark.asyncio
async def test_no_hsts_on_http():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    result = await mw.dispatch(request, call_next)

    assert "Strict-Transport-Security" not in result.headers


# ---------------------------------------------------------------------------
# CSP: production vs non-production
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_csp_production_strict():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    mock_settings = MagicMock()
    mock_settings.is_production = True

    with patch("app.core.security_headers.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    csp = result.headers["Content-Security-Policy"]
    assert "unsafe-inline" not in csp
    assert "default-src 'self'" in csp


@pytest.mark.asyncio
async def test_csp_development_relaxed():
    mw = _middleware()
    request = _make_request(scheme="http")
    call_next = AsyncMock(return_value=Response("ok"))

    mock_settings = MagicMock()
    mock_settings.is_production = False

    with patch("app.core.security_headers.settings", mock_settings):
        result = await mw.dispatch(request, call_next)

    csp = result.headers["Content-Security-Policy"]
    assert "unsafe-inline" in csp
