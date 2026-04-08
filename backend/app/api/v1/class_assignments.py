"""Teacher Assignment API: POST /class-assignments.

Reference: S-047 — Assign teacher to class (ADM only).
Role: ADM (PERM-ERP:assignment:update)
Validates: teacher exists, class exists, period exists, all same school.
"""

from __future__ import annotations


from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import success_response
from app.core.request_utils import get_client_ip
from app.schemas.erp import TeacherAssignmentCreateRequest
from app.services.erp import ERPService

router = APIRouter(prefix="/class-assignments", tags=["erp-class-assignments"])


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
    service = ERPService(db)
    result = await service.create_teacher_assignment(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)
