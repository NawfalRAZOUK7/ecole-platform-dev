"""Account recovery API endpoints: request, verify OTP, reset password.

Reference: S-041 — Account recovery flow
All endpoints are PUBLIC (no auth required) — prevent email enumeration.
- POST /recovery/request — Start recovery, send OTP
- POST /recovery/verify  — Verify OTP (pending -> verified)
- POST /recovery/reset   — Reset password (verified -> reset)
"""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.response import success_response
from app.schemas.auth import (
    RecoveryRequestCreate,
    RecoveryResetRequest,
    RecoveryVerifyRequest,
)
from app.services.auth import RecoveryService

router = APIRouter(prefix="/recovery", tags=["recovery"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# POST /recovery/request — Public
# ---------------------------------------------------------------------------
@router.post(
    "/request",
    summary="Request password recovery",
    response_description="Recovery request ID (always 200, no email enumeration)",
)
async def request_recovery(
    body: RecoveryRequestCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Request account recovery. Always returns 200 to prevent email enumeration.

    If user exists: creates recovery request and generates OTP (logged in dev).
    If user doesn't exist: returns success anyway.
    """
    service = RecoveryService(db, redis)
    result = await service.request_recovery(
        email=body.email,
        school_id=body.school_id,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /recovery/verify — Public
# ---------------------------------------------------------------------------
@router.post(
    "/verify",
    summary="Verify recovery OTP",
    response_description="OTP verification confirmation",
)
async def verify_recovery(
    body: RecoveryVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Verify recovery OTP. Transitions status: pending -> verified.

    Lockout after 5 failed attempts (30-minute lock).
    """
    service = RecoveryService(db, redis)
    result = await service.verify_otp(
        request_id=body.request_id,
        otp=body.otp,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /recovery/reset — Public
# ---------------------------------------------------------------------------
@router.post(
    "/reset",
    summary="Reset password",
    response_description="Password reset confirmation",
)
async def reset_password(
    body: RecoveryResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Reset user's password. Requires status=verified.

    Revokes all active sessions for the user (force re-login).
    State machine: pending -> verified -> reset (no backward transitions).
    """
    service = RecoveryService(db, redis)
    result = await service.reset_password(
        request_id=body.request_id,
        new_password=body.new_password,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)
