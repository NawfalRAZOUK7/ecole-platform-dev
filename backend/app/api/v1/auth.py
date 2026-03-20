"""Auth API endpoints: login, refresh, logout, me, sessions, change-password, 2FA, email verification.

Reference: S-030 through S-033 — Auth endpoints
Phase 2A: Session management (list, revoke), password change, device info on login.
Phase 2B: TOTP 2FA (setup, verify-setup, disable, verify-login), email verification.
Pipeline: Router -> Service -> Repository (Pack D2)
Public endpoints: login, refresh, 2fa/verify, verify-email (no auth required)
Protected endpoints: logout, me, sessions, change-password, 2fa/setup, 2fa/verify-setup, 2fa/disable
"""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Cookie, Depends, Header, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.redis import get_redis
from app.core.response import success_response
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerifyRequest,
    LoginRequest,
    TwoFactorDisableRequest,
    TwoFactorVerifyLoginRequest,
    TwoFactorVerifySetupRequest,
)
from app.services.auth import AuthService, EmailVerificationService, TwoFactorService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request (X-Forwarded-For or direct)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _parse_device_name(user_agent: str | None) -> str | None:
    """Parse User-Agent string to extract a readable device name.

    Phase 2A: Simple parser — extracts browser + OS from User-Agent.
    Returns e.g. "Chrome on Windows", "Safari on macOS", "Mobile App (Flutter)".
    """
    if not user_agent:
        return None

    ua = user_agent.lower()

    # Detect platform
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

    # Detect browser
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


# ---------------------------------------------------------------------------
# POST /auth/login (S-030) — Public
# ---------------------------------------------------------------------------
@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Authenticate user and create a session.

    Returns access token in response body.
    Sets refresh token as HttpOnly/Secure/SameSite=Lax cookie.
    Sets CSRF token as non-HttpOnly cookie (for double-submit pattern).
    """
    user_agent = request.headers.get("User-Agent")
    service = AuthService(db, redis)
    result = await service.login(
        email=body.email,
        password=body.password,
        school_id=body.school_id,
        source="web",
        ip_address=_get_client_ip(request),
        user_agent=user_agent,
        device_name=_parse_device_name(user_agent),
    )

    # Phase 2B: If 2FA is required, return temp_token instead of full tokens
    if result.get("requires_2fa"):
        return success_response(
            {
                "requires_2fa": True,
                "temp_token": result["temp_token"],
                "message": result["message"],
            }
        )

    # Set refresh token cookie (HttpOnly, Secure, SameSite=Lax)
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,  # 7 days
    )

    # Set CSRF cookie (NOT HttpOnly — client reads it for X-CSRF-Token header)
    response.set_cookie(
        key="csrf_token",
        value=result["csrf_token"],
        httponly=False,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,
    )

    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/refresh (S-031) — Public (uses refresh cookie)
# ---------------------------------------------------------------------------
@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    refresh_token: str | None = Cookie(None),
    x_csrf_token: str | None = Header(None, alias="X-CSRF-Token"),
):
    """Refresh the access token using a valid refresh token from the HttpOnly cookie.

    Requires X-CSRF-Token header matching the double-submit cookie value.
    Implements token rotation: old refresh token invalidated, new one issued.
    """
    from app.core.exceptions import AuthenticationError

    if not refresh_token:
        raise AuthenticationError(
            "Missing refresh token",
            error_code="ERR-IAM-401",
        )

    service = AuthService(db, redis)
    result = await service.refresh(
        refresh_token_str=refresh_token,
        csrf_token=x_csrf_token,
        ip_address=_get_client_ip(request),
    )

    # Rotate cookies
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,
    )
    response.set_cookie(
        key="csrf_token",
        value=result["csrf_token"],
        httponly=False,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,
    )

    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/logout (S-032) — Protected
# ---------------------------------------------------------------------------
@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Revoke the user's session and clear authentication cookies.

    Idempotent: calling logout on an already-revoked session returns 200.
    """
    service = AuthService(db, redis)
    await service.logout(
        session_id=auth.session_id,
        user_id=auth.user_id,
        school_id=auth.school_id,
        ip_address=_get_client_ip(request),
    )

    # Clear cookies (set expiry in the past)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="csrf_token", path="/api/v1/auth")

    return success_response(None)


# ---------------------------------------------------------------------------
# GET /me (S-033) — Protected
# ---------------------------------------------------------------------------
@router.get("/me")
async def me(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Return the authenticated user's profile with permissions and memberships.

    This endpoint is the frontend's source of truth for RBAC UI gating.
    """
    service = AuthService(db, redis)
    profile = await service.get_profile(
        user_id=auth.user_id,
        school_id=auth.school_id,
        role=auth.role,
    )
    return success_response(profile)


# ---------------------------------------------------------------------------
# GET /auth/sessions (Phase 2A) — Protected
# ---------------------------------------------------------------------------
@router.get("/sessions")
async def list_sessions(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """List the authenticated user's active sessions with device info.

    Returns sessions with: session_id, source, user_agent, ip_address,
    device_name, created_at, last_active.
    """
    service = AuthService(db, redis)
    sessions = await service.list_sessions(
        user_id=auth.user_id,
        school_id=auth.school_id,
    )
    return success_response(sessions)


# ---------------------------------------------------------------------------
# DELETE /auth/sessions/{session_id} (Phase 2A) — Protected
# ---------------------------------------------------------------------------
@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Revoke a specific session by ID.

    Users can revoke their own sessions. ADM can revoke any session in the school.
    Invalidates the refresh token and clears the session from Redis.
    """
    service = AuthService(db, redis)
    result = await service.revoke_session(
        target_session_id=session_id,
        actor_user_id=auth.user_id,
        actor_school_id=auth.school_id,
        actor_role=auth.role,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/change-password (Phase 2A) — Protected
# ---------------------------------------------------------------------------
@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Change the authenticated user's password.

    Requires current password verification. Enforces password policy on new password.
    Revokes all other active sessions (keeps current session).
    """
    service = AuthService(db, redis)
    result = await service.change_password(
        user_id=auth.user_id,
        school_id=auth.school_id,
        current_password=body.current_password,
        new_password=body.new_password,
        current_session_id=auth.session_id,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/setup (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post("/2fa/setup")
async def two_factor_setup(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Generate a new TOTP secret and QR code provisioning URI.

    Returns the secret and URI for the authenticator app.
    2FA is not yet active — call /auth/2fa/verify-setup with a valid code to activate.
    """
    service = TwoFactorService(db, redis)
    result = await service.setup(
        user_id=auth.user_id,
        school_id=auth.school_id,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/verify-setup (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post("/2fa/verify-setup")
async def two_factor_verify_setup(
    body: TwoFactorVerifySetupRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Verify first TOTP code to activate 2FA.

    Returns 10 single-use backup codes (shown once, store securely).
    """
    service = TwoFactorService(db, redis)
    result = await service.verify_setup(
        user_id=auth.user_id,
        school_id=auth.school_id,
        code=body.code,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/disable (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post("/2fa/disable")
async def two_factor_disable(
    body: TwoFactorDisableRequest,
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Disable 2FA. Requires a valid TOTP code or backup code."""
    service = TwoFactorService(db, redis)
    result = await service.disable(
        user_id=auth.user_id,
        school_id=auth.school_id,
        code=body.code,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/verify (Phase 2B) — Public (uses temp_token)
# ---------------------------------------------------------------------------
@router.post("/2fa/verify")
async def two_factor_verify_login(
    body: TwoFactorVerifyLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Verify TOTP code during login flow.

    Called after login returns requires_2fa=true.
    Accepts temp_token + TOTP code (or backup code) and returns full tokens.
    """
    service = TwoFactorService(db, redis)
    result = await service.verify_login(
        temp_token=body.temp_token,
        code=body.code,
        ip_address=_get_client_ip(request),
    )

    # Set cookies (same as normal login)
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,
    )
    response.set_cookie(
        key="csrf_token",
        value=result["csrf_token"],
        httponly=False,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=7 * 24 * 3600,
    )

    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/verify-email (Phase 2B) — Public
# ---------------------------------------------------------------------------
@router.post("/verify-email")
async def verify_email(
    body: EmailVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Verify email address via OTP sent during invite consumption."""
    service = EmailVerificationService(db, redis)
    result = await service.verify_email(
        user_id=body.user_id,
        school_id=body.school_id,
        otp=body.otp,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)
