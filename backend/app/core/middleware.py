"""Application middleware: X-Correlation-Id, exception handlers.

Reference: S-039 — X-Correlation-Id middleware, S-069 — Error response model
Uses contextvars so correlation ID propagates to async tasks and background jobs.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.exceptions import DomainException, ErrorCategory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Correlation ID context (available throughout request lifecycle)
# ---------------------------------------------------------------------------
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Get the current request's correlation ID."""
    return correlation_id_ctx.get()


# ---------------------------------------------------------------------------
# X-Correlation-Id middleware (S-039)
# ---------------------------------------------------------------------------
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Manages X-Correlation-Id header for end-to-end request tracing.

    - Preserves incoming X-Correlation-Id if present
    - Generates a new UUID v4 if not present
    - Sets the correlation ID in response headers
    - Makes it available via contextvars for the entire request lifecycle
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Extract or generate correlation ID
        cid = request.headers.get("X-Correlation-Id") or str(uuid.uuid4())
        token = correlation_id_ctx.set(cid)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-Id"] = cid
            return response
        finally:
            correlation_id_ctx.reset(token)


# ---------------------------------------------------------------------------
# Exception handlers (S-069)
# ---------------------------------------------------------------------------
def _build_error_body(
    code: str,
    message: str,
    category: str,
    *,
    retryable: bool = False,
    details: dict | None = None,
) -> dict:
    """Build the standard { error: { ... } } response body."""
    cid = get_correlation_id()
    return {
        "error": {
            "code": code,
            "message": message,
            "category": category,
            "correlation_id": cid if cid else None,
            "retryable": retryable,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }


async def domain_exception_handler(
    request: Request, exc: DomainException
) -> JSONResponse:
    """Handle all DomainException subclasses → ErrorResponse JSON."""
    logger.warning(
        "DomainException: code=%s message=%s cid=%s",
        exc.error_code,
        exc.message,
        get_correlation_id(),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            code=exc.error_code,
            message=exc.message,
            category=exc.category.value,
            retryable=exc.retryable,
            details=getattr(exc, "details", None),
        ),
        headers={"X-Correlation-Id": get_correlation_id()},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI validation errors → ErrorResponse JSON."""
    errors = exc.errors()
    detail_list = []
    for err in errors:
        detail_list.append(
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=422,
        content=_build_error_body(
            code="ERR-VAL-422",
            message="Validation error",
            category=ErrorCategory.VALIDATION.value,
            details={"errors": detail_list},
        ),
        headers={"X-Correlation-Id": get_correlation_id()},
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled exceptions → 500 ErrorResponse."""
    logger.exception("Unhandled exception: %s cid=%s", exc, get_correlation_id())
    return JSONResponse(
        status_code=500,
        content=_build_error_body(
            code="ERR-SYS-500",
            message="Internal server error",
            category=ErrorCategory.SYSTEM.value,
        ),
        headers={"X-Correlation-Id": get_correlation_id()},
    )


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------
def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on the FastAPI app."""
    # Middleware (order matters — first added = outermost)
    app.add_middleware(CorrelationIdMiddleware)

    # Exception handlers
    app.add_exception_handler(DomainException, domain_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore[arg-type]
