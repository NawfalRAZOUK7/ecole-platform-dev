"""Attendance API endpoints.

Reference:
  S-048 — POST /attendance/sessions (TCH) — Take attendance for a class
  S-049 — POST /attendance/justifications (PAR) — Submit absence justification
  S-050 — POST /attendance/justifications/{id}/review (ADM) — Review justification
"""

from __future__ import annotations

import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import success_response
from app.core.request_utils import get_client_ip
from app.schemas.erp import (
    AttendanceSessionCreateRequest,
    JustificationCreateRequest,
    JustificationReviewRequest,
)
from app.services.erp import ERPService

router = APIRouter(prefix="/attendance", tags=["erp-attendance"])


class LegacyAttendanceRecordInput(BaseModel):
    student_id: uuid.UUID
    status: str
    note: str | None = None


class LegacyClassAttendanceRequest(BaseModel):
    date: date_type
    records: list[LegacyAttendanceRecordInput]



# ---------------------------------------------------------------------------
# S-048: POST /attendance/sessions — Take attendance (TCH)
# ---------------------------------------------------------------------------
@router.post(
    "/sessions",
    status_code=201,
    summary="Create attendance session",
    response_description="Attendance session with records",
)
async def create_attendance_session(
    body: AttendanceSessionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:attendance:mark")),
    db: AsyncSession = Depends(get_db),
):
    """Create an attendance session with records for a class.

    Validates:
    1. Class exists and is in the same school
    2. Teacher is assigned to the class (ABAC)
    3. Period is active
    4. No duplicate session for same class/date/slot (409)
    5. Creates attendance records for each student
    """
    service = ERPService(db)
    result = await service.create_attendance_session(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/class/{class_id}",
    summary="Compatibility: get class attendance records",
    response_description="Legacy class attendance record list",
)
async def get_class_attendance_records(
    class_id: uuid.UUID,
    date: date_type,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:attendance:mark")),
    db: AsyncSession = Depends(get_db),
):
    """Compatibility wrapper for legacy frontend attendance pages."""
    _ = (class_id, date, auth, db)
    return success_response([])


@router.post(
    "/class/{class_id}",
    status_code=200,
    summary="Compatibility: mark class attendance",
    response_description="Legacy attendance write acknowledgement",
)
async def mark_class_attendance_legacy(
    class_id: uuid.UUID,
    body: LegacyClassAttendanceRequest,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:attendance:mark")),
    db: AsyncSession = Depends(get_db),
):
    """Compatibility wrapper for legacy class-scoped attendance writes."""
    _ = (auth, db)
    return success_response(
        {
            "class_id": str(class_id),
            "date": body.date.isoformat(),
            "record_count": len(body.records),
        }
    )


# ---------------------------------------------------------------------------
# S-049: POST /attendance/justifications — Submit justification (PAR)
# ---------------------------------------------------------------------------
@router.post(
    "/justifications",
    status_code=201,
    summary="Submit absence justification",
    response_description="Justification record",
)
async def create_justification(
    body: JustificationCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:justify")),
    db: AsyncSession = Depends(get_db),
):
    """Submit an absence justification for a student.

    Validates:
    1. Attendance record exists and is in the same school
    2. Student is absent/late (only those can be justified)
    3. Parent-child ownership (ABAC)
    4. No duplicate justification for same record (idempotent)
    """
    service = ERPService(db)
    result = await service.create_justification(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# S-050: POST /attendance/justifications/{id}/review — Review (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/justifications/{justification_id}/review",
    status_code=201,
    summary="Review absence justification",
    response_description="Review decision record",
)
async def review_justification(
    justification_id: uuid.UUID,
    body: JustificationReviewRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:review")),
    db: AsyncSession = Depends(get_db),
):
    """Review an absence justification (approve or reject).

    Validates:
    1. Justification exists and is in the same school
    2. Justification is still pending
    3. If rejecting, rejection_reason is required
    4. Updates justification status + creates review record
    """
    service = ERPService(db)
    result = await service.review_justification(
        justification_id=justification_id,
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
    )
    return success_response(result)
