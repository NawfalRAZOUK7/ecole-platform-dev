"""Enrollment API endpoint: POST /enrollments.

Reference: S-046 — First write endpoint exercising idempotency + invariant checking.
Role: ADM (PERM-ERP:enrollment:assign)
Invariant: INV-ERP-CLASS-ACTIVE — one active enrollment per student per period (409)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import success_response
from app.core.request_utils import get_client_ip
from app.services.erp import ERPService

router = APIRouter(prefix="/enrollments", tags=["erp-enrollments"])


class EnrollmentCreateRequest(BaseModel):
    student_id: uuid.UUID
    class_id: uuid.UUID
    period_id: uuid.UUID



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
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)
