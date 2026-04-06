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
from fastapi import APIRouter, Cookie, Depends, Header, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.redis import get_redis
from app.core.response import Meta, list_response, success_response
from app.core.request_utils import get_client_ip, parse_device_name
from app.schemas.auth import (
    ChangePasswordRequest,
    EmailVerifyRequest,
    LoginData,
    LoginRequest,
    RegisterRequest,
    TwoFactorDisableRequest,
    TwoFactorVerifyLoginRequest,
    TwoFactorVerifySetupRequest,
)
from app.services.auth import AuthService, EmailVerificationService, TwoFactorService

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginTwoFactorData(BaseModel):
    requires_2fa: bool
    temp_token: str
    message: str


class LoginResponseEnvelope(BaseModel):
    data: LoginData | LoginTwoFactorData
    meta: Meta


def _set_auth_cookies(response: Response, result: dict) -> None:
    max_age = int(
        result.get("refresh_expires_in", settings.refresh_token_expire_days * 86400)
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=max_age,
    )
    response.set_cookie(
        key="csrf_token",
        value=result["csrf_token"],
        httponly=False,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=max_age,
    )


# ---------------------------------------------------------------------------
# POST /auth/login (S-030) — Public
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=LoginResponseEnvelope,
    summary="Authenticate user",
    response_description="Access token or 2FA temp token",
)
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
        ip_address=get_client_ip(request),
        user_agent=user_agent,
        device_name=parse_device_name(user_agent),
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

    _set_auth_cookies(response, result)

    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/register (Phase 2C) — Public
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    status_code=201,
    summary="Register with invitation code",
    response_description="JWT tokens + user info",
)
async def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Register a new account using an invitation code.

    Creates user + membership + role-specific profile in one transaction.
    Returns JWT tokens so the user is logged in immediately.
    Rate limited: 5 registrations per 15 minutes per IP (auth category).
    """
    user_agent = request.headers.get("User-Agent")
    service = AuthService(db, redis)
    result = await service.register(
        code=body.code,
        email=body.email,
        full_name=body.full_name,
        password=body.password,
        phone=body.phone,
        profile_data=body.profile_data,
        source="web",
        ip_address=get_client_ip(request),
        user_agent=user_agent,
        device_name=parse_device_name(user_agent),
    )

    # Send email verification OTP
    from app.services.auth import EmailVerificationService

    email_service = EmailVerificationService(db, redis)
    await email_service.send_verification_otp(
        user_id=result["user_id"],
        school_id=result["school_id"],
        email=body.email,
        ip_address=get_client_ip(request),
    )

    await db.commit()

    _set_auth_cookies(response, result)

    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "user_id": str(result["user_id"]),
            "school_id": str(result["school_id"]),
            "role": result["role"],
            "email_verification_required": result["email_verification_required"],
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/refresh (S-031) — Public (uses refresh cookie)
# ---------------------------------------------------------------------------
@router.post(
    "/refresh", summary="Refresh access token", response_description="New access token"
)
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
        ip_address=get_client_ip(request),
    )

    _set_auth_cookies(response, result)

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
@router.post(
    "/logout",
    summary="Revoke current session",
    response_description="Empty success response",
)
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
        ip_address=get_client_ip(request),
    )

    # Clear cookies (set expiry in the past)
    response.delete_cookie(key="refresh_token", path="/api/v1/auth")
    response.delete_cookie(key="csrf_token", path="/api/v1/auth")

    return success_response(None)


# ---------------------------------------------------------------------------
# GET /me (S-033) — Protected
# ---------------------------------------------------------------------------
@router.get(
    "/me",
    summary="Get current user profile",
    response_description="User profile with permissions and memberships",
)
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
@router.get(
    "/sessions",
    summary="List active sessions",
    response_description="List of active sessions with device info",
)
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


@router.get(
    "/login-history",
    summary="List my login history",
    response_description="Paginated login history for the authenticated user",
)
async def login_history(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """List the authenticated user's login history for the last 90 days."""
    service = AuthService(db, redis)
    items, next_cursor, has_more = await service.list_login_history(
        target_user_id=auth.user_id,
        auth=auth,
        limit=limit,
        cursor=cursor,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


# ---------------------------------------------------------------------------
# DELETE /auth/sessions/{session_id} (Phase 2A) — Protected
# ---------------------------------------------------------------------------
@router.delete(
    "/sessions/{session_id}",
    summary="Revoke a session",
    response_description="Session revocation confirmation",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/change-password (Phase 2A) — Protected
# ---------------------------------------------------------------------------
@router.post(
    "/change-password",
    summary="Change password",
    response_description="Password change confirmation",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/setup (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post(
    "/2fa/setup",
    summary="Start 2FA setup",
    response_description="TOTP secret and provisioning URI",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/verify-setup (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post(
    "/2fa/verify-setup",
    summary="Activate 2FA",
    response_description="Backup codes and confirmation",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/disable (Phase 2B) — Protected
# ---------------------------------------------------------------------------
@router.post(
    "/2fa/disable",
    summary="Disable 2FA",
    response_description="2FA deactivation confirmation",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /auth/2fa/verify (Phase 2B) — Public (uses temp_token)
# ---------------------------------------------------------------------------
@router.post(
    "/2fa/verify",
    summary="Verify 2FA code during login",
    response_description="Access token after successful 2FA",
)
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
        ip_address=get_client_ip(request),
    )

    _set_auth_cookies(response, result)

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
@router.post(
    "/verify-email",
    summary="Verify email address",
    response_description="Email verification confirmation",
)
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
        ip_address=get_client_ip(request),
    )
    return success_response(result)
