"""Security Headers Middleware (Phase 12).

Adds security headers to all HTTP responses:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Strict-Transport-Security (HTTPS only)
- Content-Security-Policy
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # X-Content-Type-Options: Prevents MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevents clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Strict-Transport-Security: Enforces HTTPS (only on HTTPS connections)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content-Security-Policy: Controls resource loading.
        # /docs and /redoc load swagger-ui/redoc from jsdelivr CDN — exempt them from
        # the strict same-origin policy so the dev UI renders correctly.
        path = request.url.path
        is_docs_path = path in ("/docs", "/redoc", "/docs/oauth2-redirect")
        if is_docs_path:
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
        elif settings.is_production:
            csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        else:
            csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';"
        response.headers["Content-Security-Policy"] = csp

        # X-XSS-Protection: Enables XSS filtering
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Controls referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Controls browser features
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        )

        return response
