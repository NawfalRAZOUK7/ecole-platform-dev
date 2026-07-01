"""Identifier matchers — UUID assertions shared across tests."""

from __future__ import annotations

import uuid
from typing import Any


def is_uuid(value: Any) -> bool:
    """Return True if ``value`` is a UUID or a string parseable as one."""
    if isinstance(value, uuid.UUID):
        return True
    if not isinstance(value, str):
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def assert_uuid(value: Any, *, label: str = "value") -> uuid.UUID:
    """Assert ``value`` is a UUID (or UUID string) and return it as ``uuid.UUID``."""
    assert is_uuid(value), f"{label} is not a valid UUID: {value!r}"
    return value if isinstance(value, uuid.UUID) else uuid.UUID(value)
