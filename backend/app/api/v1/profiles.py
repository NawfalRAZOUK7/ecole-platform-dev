"""Profile API endpoints — role-specific profile CRUD (Phase 1B).

Reference: Phase 1B — Role-Specific Profile Tables
Endpoints:
  GET  /me/profile              — authenticated user's profile + role-specific data
  PUT  /me/profile              — update authenticated user's role-specific fields
  GET  /admin/users/{id}/profile — admin reads any user's profile (ADM only)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import success_response
from app.models.iam import (
    Membership,
    ParentProfile,
    StudentProfile,
    TeacherProfile,
    User,
)
from app.schemas.profile import (
    ParentProfileResponse,
    ParentProfileUpdate,
    StudentProfileResponse,
    StudentProfileUpdate,
    TeacherProfileResponse,
    TeacherProfileUpdate,
    UserProfileResponse,
)
from app.services.audit import AuditService

router = APIRouter(tags=["profiles"])

ADMIN_PERM = "PERM-IAM:session:list"

# Map role codes to profile model classes
_ROLE_PROFILE_MAP = {
    "STD": StudentProfile,
    "TCH": TeacherProfile,
    "PAR": ParentProfile,
}


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _get_user_with_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    school_id: uuid.UUID,
    role: str,
) -> dict:
    """Load user + role-specific profile and build combined response."""
    user = await db.get(User, user_id)
    if not user or user.school_id != school_id:
        raise NotFoundError("User not found", error_code="ERR-RES-404")

    result: dict = {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "role": role,
        "school_id": user.school_id,
        "student_profile": None,
        "parent_profile": None,
        "teacher_profile": None,
    }

    profile_cls = _ROLE_PROFILE_MAP.get(role)
    if profile_cls:
        stmt = select(profile_cls).where(
            profile_cls.user_id == user_id,
            profile_cls.school_id == school_id,
        )
        profile = (await db.execute(stmt)).scalar_one_or_none()
        if profile:
            if role == "STD":
                result["student_profile"] = StudentProfileResponse.model_validate(profile)
            elif role == "PAR":
                result["parent_profile"] = ParentProfileResponse.model_validate(profile)
            elif role == "TCH":
                result["teacher_profile"] = TeacherProfileResponse.model_validate(profile)

    return result


# ---------------------------------------------------------------------------
# GET /me/profile — Current user's combined profile
# ---------------------------------------------------------------------------
@router.get(
    "/me/profile",
    summary="Get current user's role-specific profile",
    response_description="User data with role-specific profile fields",
)
async def get_my_profile(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the authenticated user's profile including role-specific data."""
    data = await _get_user_with_profile(db, auth.user_id, auth.school_id, auth.role)
    return success_response(data)


# ---------------------------------------------------------------------------
# PUT /me/profile — Update current user's role-specific fields
# ---------------------------------------------------------------------------
@router.put(
    "/me/profile",
    summary="Update current user's role-specific profile",
    response_description="Updated profile",
)
async def update_my_profile(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the authenticated user's role-specific profile fields.

    Accepts role-specific fields depending on user role (STD, PAR, TCH).
    Creates the profile row if it doesn't exist yet.
    """
    body = await request.json()
    role = auth.role

    profile_cls = _ROLE_PROFILE_MAP.get(role)
    if not profile_cls:
        raise ValidationError(
            f"Role '{role}' does not have an extended profile",
            error_code="ERR-PROF-001",
        )

    # Validate input via the appropriate schema
    if role == "STD":
        update_data = StudentProfileUpdate(**body).model_dump(exclude_unset=True)
    elif role == "PAR":
        update_data = ParentProfileUpdate(**body).model_dump(exclude_unset=True)
    elif role == "TCH":
        update_data = TeacherProfileUpdate(**body).model_dump(exclude_unset=True)
    else:
        update_data = {}

    if not update_data:
        raise ValidationError("No fields to update", error_code="ERR-PROF-002")

    # Find or create profile
    stmt = select(profile_cls).where(
        profile_cls.user_id == auth.user_id,
        profile_cls.school_id == auth.school_id,
    )
    profile = (await db.execute(stmt)).scalar_one_or_none()

    entity_before = None
    if profile:
        entity_before = {k: getattr(profile, k) for k in update_data}
        for field, value in update_data.items():
            setattr(profile, field, value)
        profile.updated_at = datetime.now(timezone.utc)
    else:
        profile = profile_cls(
            user_id=auth.user_id,
            school_id=auth.school_id,
            **update_data,
        )
        db.add(profile)

    await db.flush()
    await db.refresh(profile)

    # Audit trail
    audit = AuditService(db)
    await audit.log(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="profile.update",
        target_type="profile",
        target_id=profile.id,
        entity_before=entity_before,
        entity_after=update_data,
        outcome="success",
        ip_address=_get_client_ip(request),
    )

    await db.commit()

    # Return full combined profile
    data = await _get_user_with_profile(db, auth.user_id, auth.school_id, auth.role)
    return success_response(data)


# ---------------------------------------------------------------------------
# GET /admin/users/{user_id}/profile — Admin reads any user's profile
# ---------------------------------------------------------------------------
@router.get(
    "/admin/users/{user_id}/profile",
    summary="Admin: get any user's role-specific profile",
    response_description="User data with role-specific profile fields",
)
async def admin_get_user_profile(
    user_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(ADMIN_PERM)),
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: read any user's combined profile (user + role-specific data).

    Enforces school boundary — admin can only view users in their own school.
    """
    # Load the target user
    target_user = await db.get(User, user_id)
    if not target_user or target_user.school_id != auth.school_id:
        raise NotFoundError("User not found", error_code="ERR-RES-404")

    # Resolve the target user's role via active membership
    stmt = select(Membership.role_code).where(
        Membership.user_id == user_id,
        Membership.school_id == auth.school_id,
        Membership.status == "active",
    )
    role_row = (await db.execute(stmt)).first()
    target_role = role_row[0] if role_row else ""

    data = await _get_user_with_profile(db, user_id, auth.school_id, target_role)
    return success_response(data)
