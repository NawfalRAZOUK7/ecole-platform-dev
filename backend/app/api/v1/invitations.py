"""Invitation code API endpoints: create, consume, revoke.

Reference: S-040 — Invitation code endpoints
Phase 2B: Hook invite consumption to send email verification OTP.
- POST /invites/create  — Role: ADM (PERM-IAM:invite:create)
- POST /invites/consume — Role: Authenticated user (PERM-IAM:invite:consume)
- POST /invites/revoke  — Role: ADM (PERM-IAM:invite:revoke)
"""

from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.redis import get_redis
from app.core.response import success_response
from app.schemas.auth import InviteConsumeRequest, InviteCreateRequest, InviteRevokeRequest
from app.services.auth import EmailVerificationService, InvitationService

router = APIRouter(prefix="/invites", tags=["invitations"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# POST /invites/create — ADM only
# ---------------------------------------------------------------------------
@router.post("/create", status_code=201, summary="Create invitation code", response_description="Plaintext invitation code (shown once)")
async def create_invite(
    body: InviteCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:invite:create")),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Create an invitation code for onboarding new users.

    Returns the plaintext code (shown once, never stored).
    """
    service = InvitationService(db, redis)
    result = await service.create_invite(
        school_id=auth.school_id,
        issuer_user_id=auth.user_id,
        role_target=body.role_target,
        expires_in_hours=body.expires_in_hours,
        target_student_id=body.target_student_id,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# POST /invites/consume — Authenticated user
# ---------------------------------------------------------------------------
@router.post("/consume", summary="Consume invitation code", response_description="New membership details")
async def consume_invite(
    body: InviteConsumeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:invite:consume")),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Consume an invitation code to join a school with the specified role.

    Idempotent: same code + same user = returns existing membership.
    """
    service = InvitationService(db, redis)
    result = await service.consume_invite(
        code=body.code,
        user_id=auth.user_id,
        school_id=auth.school_id,
        ip_address=_get_client_ip(request),
    )

    # Phase 2B: Send email verification OTP on successful consumption
    if result.get("membership_id"):
        from sqlalchemy import select
        from app.models.iam import User

        user_result = await db.execute(
            select(User).where(User.id == auth.user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and user.email_verified_at is None:
            email_service = EmailVerificationService(db, redis)
            await email_service.send_verification_otp(
                user_id=auth.user_id,
                school_id=auth.school_id,
                email=user.email,
                ip_address=_get_client_ip(request),
            )
            result["email_verification_required"] = True

    return success_response(result)


# ---------------------------------------------------------------------------
# POST /invites/revoke — ADM only
# ---------------------------------------------------------------------------
@router.post("/revoke", summary="Revoke invitation code", response_description="Revocation confirmation")
async def revoke_invite(
    body: InviteRevokeRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:invite:revoke")),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Soft-revoke an invitation code.

    Idempotent: revoking an already-revoked code is a no-op.
    """
    service = InvitationService(db, redis)
    result = await service.revoke_invite(
        invite_id=body.invite_id,
        school_id=auth.school_id,
        actor_id=auth.user_id,
        ip_address=_get_client_ip(request),
    )
    return success_response(result)
