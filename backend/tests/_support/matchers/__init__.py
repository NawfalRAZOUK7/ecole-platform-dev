"""Reusable assertion matchers for the test suite.

Usage::

    from tests._support.matchers import (
        assert_uuid, assert_success_envelope, assert_activation_url,
    )
"""

from __future__ import annotations

from tests._support.matchers.envelopes import (
    assert_error_envelope,
    assert_list_envelope,
    assert_success_envelope,
)
from tests._support.matchers.identifiers import assert_uuid, is_uuid
from tests._support.matchers.onboarding import assert_activation_url

__all__ = [
    "is_uuid",
    "assert_uuid",
    "assert_success_envelope",
    "assert_list_envelope",
    "assert_error_envelope",
    "assert_activation_url",
]
