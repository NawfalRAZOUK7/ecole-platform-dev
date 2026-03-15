"""Standard response envelope and pagination helpers.

Reference: S-068 — Standard response envelope, D5 — API Implementation Plan
Success: { data: { ... }, meta: { timestamp, version } }
List:    { data: [...], meta: { next_cursor, has_more, timestamp } }
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any, Generic, Sequence, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")

APP_VERSION = "0.1.0"


# ---------------------------------------------------------------------------
# Meta models
# ---------------------------------------------------------------------------
class Meta(BaseModel):
    """Metadata for single-item responses."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = APP_VERSION


class PaginationMeta(BaseModel):
    """Metadata for paginated list responses."""

    next_cursor: str | None = None
    has_more: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = APP_VERSION


# ---------------------------------------------------------------------------
# Envelope helpers
# ---------------------------------------------------------------------------
class ApiResponse(BaseModel, Generic[T]):
    """Single-item success response envelope."""

    data: T
    meta: Meta = Field(default_factory=Meta)


class ApiListResponse(BaseModel, Generic[T]):
    """Paginated list response envelope."""

    data: list[T]
    meta: PaginationMeta = Field(default_factory=PaginationMeta)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def success_response(data: Any, **meta_kwargs: Any) -> dict[str, Any]:
    """Build a single-item success response dict."""
    return {
        "data": data,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": APP_VERSION,
            **meta_kwargs,
        },
    }


def list_response(
    items: Sequence[Any],
    *,
    next_cursor: str | None = None,
    has_more: bool = False,
    **meta_kwargs: Any,
) -> dict[str, Any]:
    """Build a paginated list response dict."""
    return {
        "data": items,
        "meta": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": APP_VERSION,
            **meta_kwargs,
        },
    }


# ---------------------------------------------------------------------------
# Cursor pagination helpers
# ---------------------------------------------------------------------------
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def encode_cursor(last_id: UUID, sort_value: str | None = None) -> str:
    """Encode a cursor as an opaque base64 string.

    Format: last_id or last_id|sort_value
    """
    payload = str(last_id)
    if sort_value is not None:
        payload = f"{payload}|{sort_value}"
    return base64.urlsafe_b64encode(payload.encode()).decode()


def decode_cursor(cursor: str) -> tuple[UUID, str | None]:
    """Decode a cursor back to (last_id, sort_value)."""
    try:
        payload = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = payload.split("|", 1)
        last_id = UUID(parts[0])
        sort_value = parts[1] if len(parts) > 1 else None
        return last_id, sort_value
    except Exception as exc:
        raise ValueError(f"Invalid cursor: {cursor}") from exc


def clamp_page_size(limit: int | None) -> int:
    """Clamp page size between 1 and MAX_PAGE_SIZE, defaulting to DEFAULT_PAGE_SIZE."""
    if limit is None:
        return DEFAULT_PAGE_SIZE
    return max(1, min(limit, MAX_PAGE_SIZE))
