"""Domain exceptions and error response model.

Reference: S-069 — Error response model, D5 — API Implementation Plan
Category enum: validation, authn, authz, conflict, external, system, rate_limit, network, not_found, policy
Error codes follow: ERR-{DOMAIN}-{NNN} (e.g., ERR-IAM-401, ERR-ERP-409)
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error category enum
# ---------------------------------------------------------------------------
class ErrorCategory(str, enum.Enum):
    VALIDATION = "validation"
    AUTHN = "authn"
    AUTHZ = "authz"
    CONFLICT = "conflict"
    EXTERNAL = "external"
    SYSTEM = "system"
    RATE_LIMIT = "rate_limit"
    NETWORK = "network"
    NOT_FOUND = "not_found"
    POLICY = "policy"


# ---------------------------------------------------------------------------
# ErrorResponse Pydantic model (S-069)
# ---------------------------------------------------------------------------
class ErrorDetail(BaseModel):
    """Unified error payload returned by all API error responses."""

    code: str = Field(..., description="Machine-readable error code, e.g. ERR-IAM-401")
    message: str = Field(..., description="Human-readable error message")
    category: ErrorCategory
    sub_category: str | None = Field(None, description="Optional sub-category")
    details: dict[str, Any] | None = Field(
        None, description="Extra context for debugging"
    )
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    retryable: bool = Field(False)
    docs_ref: str | None = Field(None, description="Link to documentation")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorResponse(BaseModel):
    """Envelope wrapping ErrorDetail to match { error: { ... } } contract."""

    error: ErrorDetail


# ---------------------------------------------------------------------------
# Base domain exception
# ---------------------------------------------------------------------------
class DomainException(Exception):
    """Base exception for all domain errors.

    All custom exceptions inherit from this and carry structured error metadata.
    Exception handlers convert these into ErrorResponse JSON.
    """

    status_code: int = 500
    error_code: str = "ERR-SYS-500"
    category: ErrorCategory = ErrorCategory.SYSTEM
    retryable: bool = False

    def __init__(
        self,
        message: str = "Internal server error",
        *,
        error_code: str | None = None,
        category: ErrorCategory | None = None,
        details: dict[str, Any] | None = None,
        retryable: bool | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if category is not None:
            self.category = category
        if details is not None:
            self.details = details
        else:
            self.details = None
        if retryable is not None:
            self.retryable = retryable


# ---------------------------------------------------------------------------
# Concrete domain exceptions (S-069)
# ---------------------------------------------------------------------------
class AuthenticationError(DomainException):
    """401 — token invalid, expired, or missing."""

    status_code = 401
    error_code = "ERR-AUTHN-001"
    category = ErrorCategory.AUTHN

    def __init__(self, message: str = "Authentication required", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class AuthorizationError(DomainException):
    """403 — authenticated but insufficient permissions."""

    status_code = 403
    error_code = "ERR-AUTHZ-001"
    category = ErrorCategory.AUTHZ

    def __init__(
        self, message: str = "Insufficient permissions", **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)


class NotFoundError(DomainException):
    """404 — resource not found (or scope-masked)."""

    status_code = 404
    error_code = "ERR-RES-404"
    category = ErrorCategory.NOT_FOUND

    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ConflictError(DomainException):
    """409 — business invariant violated (duplicate, already exists)."""

    status_code = 409
    error_code = "ERR-RES-409"
    category = ErrorCategory.CONFLICT

    def __init__(self, message: str = "Resource conflict", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class ValidationError(DomainException):
    """422 — request payload validation failed."""

    status_code = 422
    error_code = "ERR-VAL-422"
    category = ErrorCategory.VALIDATION

    def __init__(self, message: str = "Validation error", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)


class RateLimitError(DomainException):
    """429 — rate limit exceeded."""

    status_code = 429
    error_code = "ERR-RATE-429"
    category = ErrorCategory.RATE_LIMIT
    retryable = True

    def __init__(self, message: str = "Rate limit exceeded", **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
