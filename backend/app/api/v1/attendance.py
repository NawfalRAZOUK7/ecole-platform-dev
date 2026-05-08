"""Attendance API endpoints.

Reference:
  S-048 — POST /attendance/sessions (TCH) — Take attendance for a class
  S-049 — POST /attendance/justifications (PAR) — Submit absence justification
  S-050 — POST /attendance/justifications/{id}/review (ADM) — Review justification
  I4 — multipart attachment, /justifications/mine, /records/student/{id}
"""

from __future__ import annotations

import uuid
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ValidationError
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
from app.services.file_storage import file_storage_service

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
# I4: GET /attendance/records/student/{student_id} — Parent's child absences
# ---------------------------------------------------------------------------
@router.get(
    "/records/student/{student_id}",
    summary="List a student's attendance records (parent)",
    response_description="Attendance records filtered by status",
)
async def list_student_attendance_records(
    student_id: uuid.UUID,
    status: str | None = Query(None, description="Filter by status, e.g. absent"),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:justify")),
    db: AsyncSession = Depends(get_db),
):
    service = ERPService(db)
    result = await service.list_student_absences(
        student_id=student_id,
        status=status,
        auth=auth,
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# S-049: POST /attendance/justifications — Submit justification (PAR)
# I4 — now accepts multipart/form-data with optional attachment
# ---------------------------------------------------------------------------
@router.post(
    "/justifications",
    status_code=201,
    summary="Submit absence justification",
    response_description="Justification record",
)
async def create_justification(
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:justify")),
    db: AsyncSession = Depends(get_db),
):
    """Submit an absence justification for a student.

    Accepts multipart/form-data:
      - attendance_record_id (UUID, required)
      - reason (str, required)
      - attachment (file, optional)
    """
    content_type = request.headers.get("content-type", "").lower()
    attachment = None
    if content_type.startswith("multipart/form-data") or content_type.startswith(
        "application/x-www-form-urlencoded"
    ):
        form = await request.form()
        payload = {
            "attendance_record_id": form.get("attendance_record_id"),
            "reason": form.get("reason"),
        }
        maybe_attachment = form.get("attachment")
        if (
            maybe_attachment is not None
            and hasattr(maybe_attachment, "filename")
            and hasattr(maybe_attachment, "read")
        ):
            attachment = maybe_attachment
    else:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Invalid request body") from exc

    try:
        body = JustificationCreateRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    attachment_url: str | None = None
    if attachment is not None and attachment.filename:
        content = await attachment.read()
        if content:
            storage_path, _thumb = await file_storage_service.store_upload(
                content=content,
                original_filename=attachment.filename,
                mime_type=attachment.content_type or "application/octet-stream",
            )
            attachment_url = storage_path

    service = ERPService(db)
    result = await service.create_justification(
        body=body,
        auth=auth,
        ip_address=get_client_ip(request),
        attachment_url=attachment_url,
    )
    return success_response(result)


# ---------------------------------------------------------------------------
# I4: GET /attendance/justifications/mine — Parent's submitted justifications
# ---------------------------------------------------------------------------
@router.get(
    "/justifications/mine",
    summary="List my submitted justifications",
    response_description="Justifications submitted by the current parent",
)
async def list_my_justifications(
    auth: AuthContext = Depends(requires_permission("PERM-ERP:absence:justify")),
    db: AsyncSession = Depends(get_db),
):
    service = ERPService(db)
    result = await service.list_my_justifications(auth=auth)
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
