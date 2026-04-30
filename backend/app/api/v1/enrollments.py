"""Enrollment API endpoint: POST /enrollments.

Reference: S-046 — First write endpoint exercising idempotency + invariant checking.
Role: ADM (PERM-ERP:enrollment:assign)
Invariant: INV-ERP-CLASS-ACTIVE — one active enrollment per student per period (409)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.response import list_response, success_response
from app.core.request_utils import get_client_ip
from app.models.erp import Class, Enrollment
from app.services.erp import ERPService

router = APIRouter(prefix="/enrollments", tags=["erp-enrollments"])


class EnrollmentCreateRequest(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    period_id: uuid.UUID
    program_id: uuid.UUID | None = None


@router.get(
    "",
    summary="Compatibility: list active enrollments for current user",
    response_description="Active enrollment list",
)
async def list_enrollments(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List active class enrollments for the authenticated student."""
    result = await db.execute(
        select(Enrollment, Class)
        .join(Class, Class.id == Enrollment.class_id)
        .where(
            Enrollment.student_id == auth.user_id,
            Enrollment.school_id == auth.school_id,
            Enrollment.status == "active",
        )
        .order_by(Class.name.asc(), Enrollment.id.asc())
    )
    items = [
        {
            "class_id": str(enrollment.class_id),
            "class_name": school_class.name,
        }
        for enrollment, school_class in result.all()
    ]
    return list_response(items, next_cursor=None, has_more=False)


@router.post(
    "",
    status_code=201,
    summary="Enroll student in class",
    response_description="Enrollment record",
)
async def create_enrollment(
    body: EnrollmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:enrollment:assign")),
    db: AsyncSession = Depends(get_db),
):
    """Enroll a student in a class.

    Validates:
    - Student exists and is in the same school
    - Class exists and is in the same school
    - Period is active
    - INV-ERP-CLASS-ACTIVE: one active enrollment per student per period (409)

    Idempotent: re-enrolling same student in same class returns existing enrollment.
    """
    service = ERPService(db)
    result = await service.create_enrollment(
        student_id=body.student_id,
        class_id=body.class_id,
        period_id=body.period_id,
        program_id=body.program_id,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)
