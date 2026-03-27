"""Teacher Assignment API: POST /class-assignments.

Reference: S-047 — Assign teacher to class (ADM only).
Role: ADM (PERM-ERP:assignment:update)
Validates: teacher exists, class exists, period exists, all same school.
"""

from __future__ import annotations


from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import NotFoundError
from app.core.response import success_response
from app.models.erp import Class, Period, TeacherAssignment
from app.models.iam import User
from app.schemas.erp import TeacherAssignmentCreateRequest
from app.services.audit import AuditService

router = APIRouter(prefix="/class-assignments", tags=["erp-class-assignments"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post(
    "",
    status_code=201,
    summary="Assign teacher to class",
    response_description="Teacher assignment record",
)
async def create_teacher_assignment(
    body: TeacherAssignmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:assignment:update")),
    db: AsyncSession = Depends(get_db),
):
    """Assign a teacher to a class for a period.

    Validates:
    1. Teacher exists and is in the same school
    2. Class exists and is in the same school
    3. Period exists and is in the same school
    4. No duplicate assignment (idempotent if same tuple exists)
    """
    audit = AuditService(db)

    # 1. Validate teacher exists + school boundary
    teacher_result = await db.execute(select(User).where(User.id == body.teacher_id))
    teacher = teacher_result.scalar_one_or_none()
    if teacher is None:
        raise NotFoundError("Teacher not found", error_code="ERR-ERP-404")
    verify_school_boundary(teacher.school_id, auth)

    # 2. Validate class exists + school boundary
    class_result = await db.execute(select(Class).where(Class.id == body.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")
    verify_school_boundary(cls.school_id, auth)

    # 3. Validate period exists + school boundary
    period_result = await db.execute(select(Period).where(Period.id == body.period_id))
    period = period_result.scalar_one_or_none()
    if period is None:
        raise NotFoundError("Period not found", error_code="ERR-ERP-404")
    verify_school_boundary(period.school_id, auth)

    # 4. Idempotency: check if assignment already exists
    existing_result = await db.execute(
        select(TeacherAssignment).where(
            TeacherAssignment.teacher_id == body.teacher_id,
            TeacherAssignment.class_id == body.class_id,
            TeacherAssignment.period_id == body.period_id,
            TeacherAssignment.school_id == auth.school_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response(
            {
                "id": str(existing.id),
                "teacher_id": str(existing.teacher_id),
                "class_id": str(existing.class_id),
                "period_id": str(existing.period_id),
                "school_id": str(existing.school_id),
            }
        )

    # 5. Create assignment
    assignment = TeacherAssignment(
        teacher_id=body.teacher_id,
        class_id=body.class_id,
        period_id=body.period_id,
        school_id=auth.school_id,
    )
    db.add(assignment)
    await db.flush()

    # 6. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="TEACHER_ASSIGNED",
        outcome="success",
        target_type="teacher_assignment",
        target_id=assignment.id,
        entity_after={
            "teacher_id": str(body.teacher_id),
            "class_id": str(body.class_id),
            "period_id": str(body.period_id),
        },
        ip_address=_get_client_ip(request),
    )

    return success_response(
        {
            "id": str(assignment.id),
            "teacher_id": str(assignment.teacher_id),
            "class_id": str(assignment.class_id),
            "period_id": str(assignment.period_id),
            "school_id": str(assignment.school_id),
        }
    )
