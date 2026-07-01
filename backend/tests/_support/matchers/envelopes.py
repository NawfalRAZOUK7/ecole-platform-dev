"""API response-envelope matchers.

Mirrors app/core/response.py:
  success: { "data": <payload>, "meta": { "timestamp", "version", ... } }
  list:    { "data": [...],     "meta": { "next_cursor", "has_more", "timestamp" } }
  error:   { "error": { "code", "message", "category", "correlation_id", ... } }
"""

from __future__ import annotations

from typing import Any


def assert_success_envelope(payload: dict[str, Any]) -> Any:
    """Assert a success envelope and return its ``data`` block."""
    assert isinstance(payload, dict), f"expected dict envelope, got {type(payload)}"
    assert "data" in payload, f"success envelope missing 'data': {payload!r}"
    assert "meta" in payload, f"success envelope missing 'meta': {payload!r}"
    return payload["data"]


def assert_list_envelope(
    payload: dict[str, Any],
    *,
    min_items: int = 0,
) -> list[Any]:
    """Assert a paginated list envelope and return its ``data`` list."""
    data = assert_success_envelope(payload)
    assert isinstance(data, list), f"list envelope 'data' is not a list: {data!r}"
    meta = payload["meta"]
    assert "has_more" in meta, f"list envelope meta missing 'has_more': {meta!r}"
    assert "next_cursor" in meta, f"list envelope meta missing 'next_cursor': {meta!r}"
    assert len(data) >= min_items, f"expected >= {min_items} items, got {len(data)}"
    return data


def assert_error_envelope(
    payload: dict[str, Any],
    *,
    code: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Assert an error envelope; optionally check the error code/category."""
    assert isinstance(payload, dict), f"expected dict envelope, got {type(payload)}"
    assert "error" in payload, f"error envelope missing 'error': {payload!r}"
    err = payload["error"]
    assert "message" in err, f"error block missing 'message': {err!r}"
    if code is not None:
        assert (
            err.get("code") == code
        ), f"expected error code {code!r}, got {err.get('code')!r}"
    if category is not None:
        assert (
            err.get("category") == category
        ), f"expected category {category!r}, got {err.get('category')!r}"
    return err
