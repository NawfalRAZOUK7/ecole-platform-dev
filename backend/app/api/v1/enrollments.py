"""Enrollment API endpoint: POST /enrollments.

Reference: S-046 — First write endpoint exercising idempotency + invariant checking.
Role: ADM (PERM-ERP:enrollment:assign)
Invariant: INV-ERP-CLASS-ACTIVE — one active enrollment per student per period (409)
"""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission, verify_school_boundary
from app.core.exceptions import ConflictError, NotFoundError
from app.core.redis import get_redis
from app.core.response import success_response
from app.models.erp import Class, Enrollment, Period
from app.models.iam import User
from app.services.audit import AuditService

router = APIRouter(prefix="/enrollments", tags=["erp-enrollments"])


class EnrollmentCreateRequest(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    period_id: uuid.UUID


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post("", status_code=201, summary="Enroll student in class", response_description="Enrollment record")
async def create_enrollment(
    body: EnrollmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:enrollment:assign")),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Enroll a student in a class.

    Validates:
    - Student exists and is in the same school
    - Class exists and is in the same school
    - Period is active
    - INV-ERP-CLASS-ACTIVE: one active enrollment per student per period (409)

    Idempotent: re-enrolling same student in same class returns existing enrollment.
    """
    audit = AuditService(db)

    # 1. Validate student exists + school boundary
    student_result = await db.execute(select(User).where(User.id == body.student_id))
    student = student_result.scalar_one_or_none()
    if student is None:
        raise NotFoundError("Student not found", error_code="ERR-ERP-404")
    verify_school_boundary(student.school_id, auth)

    # 2. Validate class exists + school boundary
    class_result = await db.execute(select(Class).where(Class.id == body.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")
    verify_school_boundary(cls.school_id, auth)

    # 3. Validate period exists + is active
    period_result = await db.execute(select(Period).where(Period.id == body.period_id))
    period = period_result.scalar_one_or_none()
    if period is None:
        raise NotFoundError("Period not found", error_code="ERR-ERP-404")
    verify_school_boundary(period.school_id, auth)

    if period.status != "active":
        raise ConflictError(
            "Period is not active",
            error_code="ERR-ERP-409",
        )

    # 4. Idempotency check — existing active enrollment for same student+class+period
    existing_result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == body.student_id,
            Enrollment.class_id == body.class_id,
            Enrollment.period_id == body.period_id,
            Enrollment.status == "active",
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        # Idempotent: return existing enrollment
        return success_response(
            {
                "id": str(existing.id),
                "student_id": str(existing.student_id),
                "class_id": str(existing.class_id),
                "period_id": str(existing.period_id),
                "school_id": str(existing.school_id),
                "status": existing.status,
            }
        )

    # 5. INV-ERP-CLASS-ACTIVE — check no other active enrollment for student in this period
    conflicting_result = await db.execute(
        select(Enrollment).where(
            Enrollment.student_id == body.student_id,
            Enrollment.period_id == body.period_id,
            Enrollment.school_id == auth.school_id,
            Enrollment.status == "active",
        )
    )
    conflicting = conflicting_result.scalar_one_or_none()
    if conflicting is not None:
        raise ConflictError(
            "Student already has an active enrollment for this period",
            error_code="ERR-ERP-409",
            details={
                "existing_enrollment_id": str(conflicting.id),
                "existing_class_id": str(conflicting.class_id),
            },
        )

    # 6. Create enrollment
    enrollment = Enrollment(
        student_id=body.student_id,
        class_id=body.class_id,
        period_id=body.period_id,
        school_id=auth.school_id,
        status="active",
    )
    db.add(enrollment)
    await db.flush()

    # 7. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ENROLLMENT_ASSIGNED",
        outcome="success",
        target_type="enrollment",
        target_id=enrollment.id,
        entity_after={
            "student_id": str(body.student_id),
            "class_id": str(body.class_id),
            "period_id": str(body.period_id),
            "status": "active",
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(enrollment.id),
            "student_id": str(enrollment.student_id),
            "class_id": str(enrollment.class_id),
            "period_id": str(enrollment.period_id),
            "school_id": str(enrollment.school_id),
            "status": enrollment.status,
        }
    )
