"""Unit tests for app/core/request_utils.py — pure/near-pure functions."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from app.core.request_utils import (
    _extract_bearer_token,
    get_client_ip,
    parse_device_name,
    request_locale,
    serialize_device,
)


def _make_request(headers: dict | None = None) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": raw,
        "server": ("localhost", 8000),
        "client": ("127.0.0.1", 9000),
    }
    return Request(scope)


def _no_client_request() -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 8000),
    }
    return Request(scope)


# ---------------------------------------------------------------------------
# _extract_bearer_token
# ---------------------------------------------------------------------------


def test_extract_bearer_token_none():
    assert _extract_bearer_token(None) is None


def test_extract_bearer_token_with_credentials():
    creds = MagicMock()
    creds.credentials = "my-token-abc"
    assert _extract_bearer_token(creds) == "my-token-abc"


# ---------------------------------------------------------------------------
# get_client_ip
# ---------------------------------------------------------------------------


def test_get_client_ip_forwarded_for():
    request = _make_request(headers={"X-Forwarded-For": "203.0.113.5, 10.0.0.1"})
    assert get_client_ip(request) == "203.0.113.5"


def test_get_client_ip_forwarded_for_single():
    request = _make_request(headers={"X-Forwarded-For": "198.51.100.10"})
    assert get_client_ip(request) == "198.51.100.10"


def test_get_client_ip_from_client():
    request = _make_request()
    assert get_client_ip(request) == "127.0.0.1"


def test_get_client_ip_no_client():
    request = _no_client_request()
    assert get_client_ip(request) is None


# ---------------------------------------------------------------------------
# request_locale
# ---------------------------------------------------------------------------


def test_request_locale_arabic():
    request = _make_request(headers={"Accept-Language": "ar-MA,ar;q=0.9"})
    assert request_locale(request) == "ar"


def test_request_locale_english():
    request = _make_request(headers={"Accept-Language": "en-US,en;q=0.9"})
    assert request_locale(request) == "en"


def test_request_locale_french_default():
    request = _make_request(headers={"Accept-Language": "fr-FR"})
    assert request_locale(request) == "fr"


def test_request_locale_no_header_defaults_fr():
    request = _make_request()
    assert request_locale(request) == "fr"


def test_request_locale_unknown_defaults_fr():
    request = _make_request(headers={"Accept-Language": "es-ES"})
    assert request_locale(request) == "fr"


# ---------------------------------------------------------------------------
# parse_device_name
# ---------------------------------------------------------------------------


def test_parse_device_name_none():
    assert parse_device_name(None) is None


def test_parse_device_name_empty():
    assert parse_device_name("") is None


def test_parse_device_name_flutter():
    result = parse_device_name("Dart/2.18 (dart:io)")
    assert result == "Mobile App (Flutter)"


def test_parse_device_name_android():
    ua = "Mozilla/5.0 (Linux; Android 13; Pixel 6) Chrome/112.0"
    result = parse_device_name(ua)
    assert "Android" in result


def test_parse_device_name_iphone():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0)"
    result = parse_device_name(ua)
    assert "iOS" in result


def test_parse_device_name_ipad():
    ua = "Mozilla/5.0 (iPad; CPU OS 16_0 like Mac OS X)"
    result = parse_device_name(ua)
    assert "iOS" in result


def test_parse_device_name_macos():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.0) Safari/537"
    result = parse_device_name(ua)
    assert "macOS" in result


def test_parse_device_name_windows():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/112"
    result = parse_device_name(ua)
    assert "Windows" in result


def test_parse_device_name_linux():
    ua = "Mozilla/5.0 (X11; Linux x86_64) Firefox/112"
    result = parse_device_name(ua)
    assert "Linux" in result


def test_parse_device_name_chrome():
    ua = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit Chrome/112 Safari/537"
    result = parse_device_name(ua)
    assert "Chrome" in result


def test_parse_device_name_firefox():
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112) Firefox/112"
    result = parse_device_name(ua)
    assert "Firefox" in result


def test_parse_device_name_safari():
    ua = "Mozilla/5.0 (Macintosh) AppleWebKit/605 Safari/605"
    result = parse_device_name(ua)
    assert "Safari" in result


def test_parse_device_name_edge():
    ua = "Mozilla/5.0 (Windows NT 10.0) Chrome/112 Safari/537 Edg/112"
    result = parse_device_name(ua)
    assert "Edge" in result


def test_parse_device_name_unknown():
    ua = "CustomBot/1.0"
    result = parse_device_name(ua)
    assert "Unknown" in result


# ---------------------------------------------------------------------------
# serialize_device
# ---------------------------------------------------------------------------


def test_serialize_device_long_token():
    device = MagicMock()
    device.id = "device-uuid-1234"
    device.user_id = "user-uuid-5678"
    device.platform = "ios"
    device.device_name = "iPhone 15"
    device.token = "abcdefghijklmnopqrstuvwxyz123456"
    device.last_active_at = MagicMock()
    device.last_active_at.isoformat.return_value = "2024-01-15T10:00:00+00:00"
    device.created_at = MagicMock()
    device.created_at.isoformat.return_value = "2024-01-01T00:00:00+00:00"

    result = serialize_device(device)

    assert result["id"] == "device-uuid-1234"
    assert result["platform"] == "ios"
    assert "..." in result["token_preview"]


def test_serialize_device_short_token():
    device = MagicMock()
    device.id = "d1"
    device.user_id = "u1"
    device.platform = "android"
    device.device_name = "Pixel 7"
    device.token = "short"
    device.last_active_at = MagicMock()
    device.last_active_at.isoformat.return_value = "2024-01-15T10:00:00+00:00"
    device.created_at = MagicMock()
    device.created_at.isoformat.return_value = "2024-01-01T00:00:00+00:00"

    result = serialize_device(device)

    assert result["token_preview"] == "short"


def test_serialize_device_none_token():
    device = MagicMock()
    device.id = "d2"
    device.user_id = "u2"
    device.platform = "web"
    device.device_name = "Browser"
    device.token = None
    device.last_active_at = MagicMock()
    device.last_active_at.isoformat.return_value = "2024-01-15T10:00:00+00:00"
    device.created_at = MagicMock()
    device.created_at.isoformat.return_value = "2024-01-01T00:00:00+00:00"

    result = serialize_device(device)

    assert result["token_preview"] == ""
