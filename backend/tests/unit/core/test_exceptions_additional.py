"""Additional coverage-focused tests for domain exceptions."""

from __future__ import annotations

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    DomainException,
    ErrorCategory,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestDomainExceptionAdditional:
    def test_domain_exception_accepts_custom_category(self):
        exc = DomainException("Gateway timed out", category=ErrorCategory.NETWORK)

        assert exc.category == ErrorCategory.NETWORK

    def test_domain_exception_accepts_custom_retryable_flag(self):
        exc = DomainException("Temporary outage", retryable=True)

        assert exc.retryable is True

    def test_rate_limit_error_can_disable_retryable(self):
        exc = RateLimitError(retryable=False)

        assert exc.retryable is False

    def test_authentication_error_can_override_category(self):
        exc = AuthenticationError(category=ErrorCategory.POLICY)

        assert exc.category == ErrorCategory.POLICY

    def test_not_found_error_preserves_custom_details(self):
        exc = NotFoundError(details={"entity": "payment_plan", "masked": True})

        assert exc.details == {"entity": "payment_plan", "masked": True}

    def test_conflict_error_preserves_custom_error_code(self):
        exc = ConflictError(error_code="ERR-BIL-409")

        assert exc.error_code == "ERR-BIL-409"

    def test_validation_error_can_be_marked_retryable(self):
        exc = ValidationError("Try again later", retryable=True)

        assert exc.retryable is True

    def test_domain_exception_defaults_details_to_none(self):
        exc = DomainException("No extra context")

        assert exc.details is None
