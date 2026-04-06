"""Security utilities: JWT token generation/validation, password hashing.

Reference: S-029 — JWT token infrastructure, Pack C6 (RBAC Model), D6 (Security Enforcement)
- Access token: short-lived (default 30min), sent in Authorization: Bearer header
- Refresh token: longer-lived (default 2d), HttpOnly/Secure/SameSite=Lax cookie
- Token claims: sub (user_id), role, school_id, session_id, exp, iat, jti
- Password hashing: bcrypt (direct library, compatible with bcrypt 5.x)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings
from app.core.exceptions import AuthenticationError

# ---------------------------------------------------------------------------
# Token types
# ---------------------------------------------------------------------------
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


# ---------------------------------------------------------------------------
# JWT token generation (S-029)
# ---------------------------------------------------------------------------
def create_access_token(
    user_id: uuid.UUID,
    role: str,
    school_id: uuid.UUID,
    session_id: uuid.UUID,
) -> str:
    """Create a short-lived access JWT.

    Claims: sub, role, school_id, session_id, exp, iat, jti, type
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "school_id": str(school_id),
        "session_id": str(session_id),
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": TOKEN_TYPE_ACCESS,
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def create_refresh_token(
    user_id: uuid.UUID,
    school_id: uuid.UUID,
    session_id: uuid.UUID,
    expire_days: float | None = None,
) -> tuple[str, str]:
    """Create a long-lived refresh JWT.

    Returns (token_string, jti) — jti is stored in Redis for rotation tracking.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(
        days=expire_days
        if expire_days is not None
        else settings.refresh_token_expire_days
    )
    jti = str(uuid.uuid4())
    payload = {
        "sub": str(user_id),
        "school_id": str(school_id),
        "session_id": str(session_id),
        "exp": expire,
        "iat": now,
        "jti": jti,
        "type": TOKEN_TYPE_REFRESH,
    }
    token = jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return token, jti


def create_csrf_token() -> str:
    """Generate a CSRF token for double-submit cookie pattern."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# JWT token validation (S-029)
# ---------------------------------------------------------------------------
def _decode_jwt(token: str) -> dict:
    """Decode JWT trying current key first, then previous key during rotation."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        if settings.jwt_previous_key:
            try:
                return jwt.decode(
                    token,
                    settings.jwt_previous_key,
                    algorithms=[settings.jwt_algorithm],
                )
            except JWTError:
                pass
        raise


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token.

    Raises AuthenticationError on any failure (expired, invalid, wrong type).
    Returns decoded payload dict.
    """
    try:
        payload = _decode_jwt(token)
    except JWTError as exc:
        raise AuthenticationError(
            "Invalid or expired access token",
            error_code="ERR-IAM-401",
        ) from exc

    if payload.get("type") != TOKEN_TYPE_ACCESS:
        raise AuthenticationError(
            "Invalid token type",
            error_code="ERR-IAM-401",
        )

    return payload


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token.

    Raises AuthenticationError on any failure.
    Returns decoded payload dict.
    """
    try:
        payload = _decode_jwt(token)
    except JWTError as exc:
        raise AuthenticationError(
            "Invalid or expired refresh token",
            error_code="ERR-IAM-401",
        ) from exc

    if payload.get("type") != TOKEN_TYPE_REFRESH:
        raise AuthenticationError(
            "Invalid token type",
            error_code="ERR-IAM-401",
        )

    return payload


# ---------------------------------------------------------------------------
# Password hashing (bcrypt — direct library for compat with bcrypt 5.x)
# ---------------------------------------------------------------------------
def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt.

    Returns the bcrypt hash string (60 chars).
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
