"""Unit tests for response envelope, cursor pagination, and exception hierarchy.

Reference: S-068 — Standard response envelope, S-069 — Error response model
Tests pure functions: encode_cursor, decode_cursor, clamp_page_size,
success_response, list_response, and exception hierarchy attributes.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime

import pytest

from app.core.response import (
    APP_VERSION,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    Meta,
    PaginationMeta,
    clamp_page_size,
    decode_cursor,
    encode_cursor,
    list_response,
    success_response,
)
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainException,
    ErrorCategory,
    ErrorDetail,
    ErrorResponse,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


# ── Cursor Encoding / Decoding ──


class TestCursorEncoding:
    """Tests for opaque base64 cursor encode/decode."""

    def test_encode_decode_roundtrip(self):
        uid = uuid.uuid4()
        cursor = encode_cursor(uid)
        decoded_id, sort_val = decode_cursor(cursor)
        assert decoded_id == uid
        assert sort_val is None

    def test_encode_decode_with_sort_value(self):
        uid = uuid.uuid4()
        cursor = encode_cursor(uid, sort_value="2026-03-15T10:00:00")
        decoded_id, sort_val = decode_cursor(cursor)
        assert decoded_id == uid
        assert sort_val == "2026-03-15T10:00:00"

    def test_cursor_is_base64_string(self):
        uid = uuid.uuid4()
        cursor = encode_cursor(uid)
        # Should be valid base64 — decoding should not raise
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
        assert str(uid) in decoded

    def test_decode_invalid_cursor_raises_value_error(self):
        with pytest.raises(ValueError, match="Invalid cursor"):
            decode_cursor("not-valid-base64-!!!!")

    def test_decode_cursor_bad_uuid_raises(self):
        bad = base64.urlsafe_b64encode(b"not-a-uuid").decode()
        with pytest.raises(ValueError):
            decode_cursor(bad)

    def test_cursor_with_pipe_in_sort_value(self):
        """Sort value containing pipe should be preserved."""
        uid = uuid.uuid4()
        cursor = encode_cursor(uid, sort_value="a|b|c")
        decoded_id, sort_val = decode_cursor(cursor)
        assert decoded_id == uid
        assert sort_val == "a|b|c"  # Full sort value preserved after UUID pipe split


# ── Page Size Clamping ──


class TestClampPageSize:
    """Tests for pagination page size clamping."""

    def test_none_returns_default(self):
        assert clamp_page_size(None) == DEFAULT_PAGE_SIZE

    def test_valid_size_passes_through(self):
        assert clamp_page_size(10) == 10

    def test_zero_clamped_to_one(self):
        assert clamp_page_size(0) == 1

    def test_negative_clamped_to_one(self):
        assert clamp_page_size(-5) == 1

    def test_exceeds_max_clamped(self):
        assert clamp_page_size(999) == MAX_PAGE_SIZE

    def test_exact_max_allowed(self):
        assert clamp_page_size(MAX_PAGE_SIZE) == MAX_PAGE_SIZE

    def test_default_page_size_value(self):
        assert DEFAULT_PAGE_SIZE == 20

    def test_max_page_size_value(self):
        assert MAX_PAGE_SIZE == 100


# ── Success Response Envelope ──


class TestSuccessResponse:
    """Tests for the success_response helper."""

    def test_wraps_data(self):
        result = success_response({"id": "123"})
        assert result["data"] == {"id": "123"}

    def test_includes_meta(self):
        result = success_response({"id": "123"})
        assert "meta" in result
        assert "timestamp" in result["meta"]
        assert result["meta"]["version"] == APP_VERSION

    def test_meta_version_matches_constant(self):
        result = success_response({})
        assert result["meta"]["version"] == "0.1.0"

    def test_handles_list_data(self):
        items = [{"id": "1"}, {"id": "2"}]
        result = success_response(items)
        assert result["data"] == items

    def test_handles_none_data(self):
        result = success_response(None)
        assert result["data"] is None

    def test_accepts_extra_meta_kwargs(self):
        result = success_response({}, custom_key="value")
        assert result["meta"]["custom_key"] == "value"


# ── List Response Envelope ──


class TestListResponse:
    """Tests for the list_response helper."""

    def test_wraps_items_as_data(self):
        items = [{"a": 1}, {"a": 2}]
        result = list_response(items)
        assert result["data"] == items

    def test_default_pagination(self):
        result = list_response([])
        meta = result["meta"]
        assert meta["next_cursor"] is None
        assert meta["has_more"] is False

    def test_with_cursor(self):
        result = list_response(
            [{"id": 1}],
            next_cursor="abc123",
            has_more=True,
        )
        meta = result["meta"]
        assert meta["next_cursor"] == "abc123"
        assert meta["has_more"] is True

    def test_includes_version(self):
        result = list_response([])
        assert result["meta"]["version"] == APP_VERSION

    def test_empty_list_valid(self):
        result = list_response([])
        assert result["data"] == []

    def test_meta_timestamp_is_iso(self):
        result = list_response([])
        ts = result["meta"]["timestamp"]
        # Should be valid ISO format
        datetime.fromisoformat(ts)


# ── Pydantic Meta Models ──


class TestMetaModels:
    """Tests for Meta and PaginationMeta Pydantic models."""

    def test_meta_has_defaults(self):
        m = Meta()
        assert m.version == APP_VERSION
        assert isinstance(m.timestamp, datetime)

    def test_pagination_meta_defaults(self):
        pm = PaginationMeta()
        assert pm.next_cursor is None
        assert pm.has_more is False
        assert pm.version == APP_VERSION


# ── Exception Hierarchy ──


class TestExceptionHierarchy:
    """Tests for the domain exception classes and their attributes."""

    def test_domain_exception_defaults(self):
        exc = DomainException()
        assert exc.status_code == 500
        assert exc.error_code == "ERR-SYS-500"
        assert exc.category == ErrorCategory.SYSTEM
        assert exc.retryable is False

    def test_authentication_error_attributes(self):
        exc = AuthenticationError()
        assert exc.status_code == 401
        assert exc.error_code == "ERR-AUTHN-001"
        assert exc.category == ErrorCategory.AUTHN
        assert exc.retryable is False
        assert str(exc) == "Authentication required"

    def test_authorization_error_attributes(self):
        exc = AuthorizationError()
        assert exc.status_code == 403
        assert exc.error_code == "ERR-AUTHZ-001"
        assert exc.category == ErrorCategory.AUTHZ

    def test_not_found_error_attributes(self):
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.error_code == "ERR-RES-404"
        assert exc.category == ErrorCategory.NOT_FOUND

    def test_conflict_error_attributes(self):
        exc = ConflictError()
        assert exc.status_code == 409
        assert exc.error_code == "ERR-RES-409"
        assert exc.category == ErrorCategory.CONFLICT

    def test_validation_error_attributes(self):
        exc = ValidationError()
        assert exc.status_code == 422
        assert exc.error_code == "ERR-VAL-422"
        assert exc.category == ErrorCategory.VALIDATION

    def test_rate_limit_error_is_retryable(self):
        exc = RateLimitError()
        assert exc.status_code == 429
        assert exc.error_code == "ERR-RATE-429"
        assert exc.category == ErrorCategory.RATE_LIMIT
        assert exc.retryable is True

    def test_custom_message(self):
        exc = AuthenticationError("Token expired")
        assert str(exc) == "Token expired"
        assert exc.message == "Token expired"

    def test_custom_error_code(self):
        exc = ConflictError("Duplicate", error_code="ERR-ERP-409")
        assert exc.error_code == "ERR-ERP-409"

    def test_custom_details(self):
        exc = ValidationError(
            "Invalid field",
            details={"field": "email", "reason": "format"},
        )
        assert exc.details == {"field": "email", "reason": "format"}

    def test_all_exceptions_inherit_from_domain_exception(self):
        for cls in [
            AuthenticationError,
            AuthorizationError,
            NotFoundError,
            ConflictError,
            ValidationError,
            RateLimitError,
        ]:
            assert issubclass(cls, DomainException)
            assert issubclass(cls, Exception)


# ── ErrorDetail Pydantic Model ──


class TestErrorDetailModel:
    """Tests for the ErrorDetail and ErrorResponse Pydantic models."""

    def test_error_detail_required_fields(self):
        detail = ErrorDetail(
            code="ERR-IAM-401",
            message="Bad token",
            category=ErrorCategory.AUTHN,
        )
        assert detail.code == "ERR-IAM-401"
        assert detail.message == "Bad token"
        assert detail.category == ErrorCategory.AUTHN
        assert detail.retryable is False
        assert isinstance(detail.timestamp, datetime)

    def test_error_detail_optional_fields(self):
        detail = ErrorDetail(
            code="ERR-SYS-500",
            message="Server error",
            category=ErrorCategory.SYSTEM,
            sub_category="database",
            details={"table": "users"},
            correlation_id=uuid.uuid4(),
            retryable=True,
            docs_ref="https://docs.example.com",
        )
        assert detail.sub_category == "database"
        assert detail.details == {"table": "users"}
        assert detail.retryable is True
        assert detail.docs_ref is not None

    def test_error_response_envelope(self):
        detail = ErrorDetail(
            code="ERR-RES-404",
            message="Not found",
            category=ErrorCategory.NOT_FOUND,
        )
        resp = ErrorResponse(error=detail)
        assert resp.error.code == "ERR-RES-404"

    def test_error_category_values(self):
        expected = {
            "validation",
            "authn",
            "authz",
            "conflict",
            "external",
            "system",
            "rate_limit",
            "network",
            "not_found",
            "policy",
        }
        actual = {c.value for c in ErrorCategory}
        assert actual == expected
