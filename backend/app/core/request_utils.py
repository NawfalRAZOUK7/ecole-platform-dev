"""Shared request and router helper utilities."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext
from app.core.exceptions import AuthenticationError
from app.core.permissions import get_permissions_for_role
from app.core.security import decode_access_token
from app.models.iam import Session

_bearer_scheme = HTTPBearer(auto_error=False)


def _extract_access_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is not None:
        return credentials.credentials

    token = request.query_params.get("token")
    if not token:
        return None
    if token.lower().startswith("bearer "):
        return token.split(" ", 1)[1].strip()
    return token


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP from forwarded headers or the socket."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def request_locale(request: Request) -> str:
    """Resolve the preferred request locale from Accept-Language."""
    accept_language = request.headers.get("Accept-Language", "fr").lower()
    if accept_language.startswith("ar"):
        return "ar"
    if accept_language.startswith("en"):
        return "en"
    return "fr"


def parse_device_name(user_agent: str | None) -> str | None:
    """Convert a user agent string into a short readable device label."""
    if not user_agent:
        return None

    ua = user_agent.lower()

    if "flutter" in ua or "dart" in ua:
        return "Mobile App (Flutter)"
    if "android" in ua:
        platform = "Android"
    elif "iphone" in ua or "ipad" in ua:
        platform = "iOS"
    elif "macintosh" in ua or "mac os" in ua:
        platform = "macOS"
    elif "windows" in ua:
        platform = "Windows"
    elif "linux" in ua:
        platform = "Linux"
    else:
        platform = "Unknown OS"

    if "edg/" in ua:
        browser = "Edge"
    elif "chrome" in ua and "safari" in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua:
        browser = "Safari"
    else:
        browser = "Unknown Browser"

    return f"{browser} on {platform}"


def serialize_device(device: Any) -> dict[str, Any]:
    """Serialize a device token row for API responses."""
    token = getattr(device, "token", "") or ""
    preview = f"{token[:12]}...{token[-6:]}" if len(token) > 20 else token
    return {
        "id": str(device.id),
        "user_id": str(device.user_id),
        "platform": device.platform,
        "device_name": device.device_name,
        "token_preview": preview,
        "last_active_at": device.last_active_at.isoformat(),
        "created_at": device.created_at.isoformat(),
    }


async def optional_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext | None:
    """Resolve the current user when a bearer token is optional."""
    token = _extract_access_token(request, credentials)
    if token is None:
        return None

    payload = decode_access_token(token)
    session_id = uuid.UUID(payload["session_id"])
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.revoke_at.is_(None))
    )
    if result.scalar_one_or_none() is None:
        raise AuthenticationError(
            "Session has been revoked",
            error_code="ERR-IAM-401",
        )

    role = payload["role"]
    return AuthContext(
        user_id=uuid.UUID(payload["sub"]),
        role=role,
        school_id=uuid.UUID(payload["school_id"]),
        session_id=session_id,
        permissions=get_permissions_for_role(role),
    )
