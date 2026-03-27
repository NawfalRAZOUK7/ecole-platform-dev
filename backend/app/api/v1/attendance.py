"""Attendance API endpoints.

Reference:
  S-048 — POST /attendance/sessions (TCH) — Take attendance for a class
  S-049 — POST /attendance/justifications (PAR) — Submit absence justification
  S-050 — POST /attendance/justifications/{id}/review (ADM) — Review justification
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_parent_child_ids,
    get_teacher_class_ids,
    requires_permission,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import success_response
from app.core.request_utils import get_client_ip
from app.models.erp import (
    AbsenceJustification,
    AttendanceRecord,
    AttendanceSession,
    Class,
    JustificationReview,
    Period,
)
from app.schemas.erp import (
    AttendanceSessionCreateRequest,
    JustificationCreateRequest,
    JustificationReviewRequest,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/attendance", tags=["erp-attendance"])



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
    audit = AuditService(db)

    # 1. Validate class exists + school boundary
    class_result = await db.execute(select(Class).where(Class.id == body.class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")
    verify_school_boundary(cls.school_id, auth)

    # 2. ABAC: Teacher must be assigned to this class
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(body.class_id, teacher_classes)

    # 3. Validate period exists + active
    period_result = await db.execute(select(Period).where(Period.id == body.period_id))
    period = period_result.scalar_one_or_none()
    if period is None:
        raise NotFoundError("Period not found", error_code="ERR-ERP-404")
    verify_school_boundary(period.school_id, auth)
    if period.status != "active":
        raise ConflictError("Period is not active", error_code="ERR-ERP-409")

    # 4. Check for duplicate session (class + date + slot)
    existing_result = await db.execute(
        select(AttendanceSession).where(
            AttendanceSession.class_id == body.class_id,
            AttendanceSession.session_date == body.session_date,
            AttendanceSession.slot == body.slot,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        raise ConflictError(
            "Attendance session already exists for this class/date/slot",
            error_code="ERR-ERP-409",
            details={
                "existing_session_id": str(existing.id),
            },
        )

    # 5. Create attendance session
    session = AttendanceSession(
        class_id=body.class_id,
        period_id=body.period_id,
        teacher_id=auth.user_id,
        school_id=auth.school_id,
        session_date=body.session_date,
        slot=body.slot,
    )
    db.add(session)
    await db.flush()

    # 6. Create attendance records
    record_responses = []
    for rec in body.records:
        record = AttendanceRecord(
            attendance_session_id=session.id,
            student_id=rec.student_id,
            school_id=auth.school_id,
            status=rec.status,
            absence_reason=rec.absence_reason,
        )
        db.add(record)
        await db.flush()
        record_responses.append(
            {
                "id": str(record.id),
                "student_id": str(record.student_id),
                "status": record.status,
                "absence_reason": record.absence_reason,
            }
        )

    # 7. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="ATTENDANCE_MARKED",
        outcome="success",
        target_type="attendance_session",
        target_id=session.id,
        entity_after={
            "class_id": str(body.class_id),
            "session_date": str(body.session_date),
            "slot": body.slot,
            "record_count": len(body.records),
        },
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "id": str(session.id),
            "class_id": str(session.class_id),
            "period_id": str(session.period_id),
            "teacher_id": str(session.teacher_id),
            "school_id": str(session.school_id),
            "session_date": str(session.session_date),
            "slot": session.slot,
            "records": record_responses,
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
    audit = AuditService(db)

    # 1. Validate attendance record exists + school boundary
    record_result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.id == body.attendance_record_id)
    )
    record = record_result.scalar_one_or_none()
    if record is None:
        raise NotFoundError("Attendance record not found", error_code="ERR-ERP-404")
    verify_school_boundary(record.school_id, auth)

    # 2. Only absent or late records can be justified
    if record.status not in ("absent", "late"):
        raise ValidationError(
            "Only absent or late records can be justified",
            error_code="ERR-ERP-422",
        )

    # 3. ABAC: Parent-child ownership
    child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
    verify_parent_child_ownership(record.student_id, child_ids)

    # 4. Check for existing justification (idempotent)
    existing_result = await db.execute(
        select(AbsenceJustification).where(
            AbsenceJustification.attendance_record_id == body.attendance_record_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return success_response(
            {
                "id": str(existing.id),
                "attendance_record_id": str(existing.attendance_record_id),
                "parent_id": str(existing.parent_id),
                "school_id": str(existing.school_id),
                "status": existing.status,
                "reason": existing.reason,
                "rejection_reason": existing.rejection_reason,
            }
        )

    # 5. Create justification
    justification = AbsenceJustification(
        attendance_record_id=body.attendance_record_id,
        parent_id=auth.user_id,
        school_id=auth.school_id,
        status="pending",
        reason=body.reason,
    )
    db.add(justification)
    await db.flush()

    # 6. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="JUSTIFICATION_SUBMITTED",
        outcome="success",
        target_type="absence_justification",
        target_id=justification.id,
        entity_after={
            "attendance_record_id": str(body.attendance_record_id),
            "reason": body.reason,
        },
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "id": str(justification.id),
            "attendance_record_id": str(justification.attendance_record_id),
            "parent_id": str(justification.parent_id),
            "school_id": str(justification.school_id),
            "status": justification.status,
            "reason": justification.reason,
            "rejection_reason": justification.rejection_reason,
        }
    )


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
    audit = AuditService(db)

    # 1. Validate justification exists + school boundary
    just_result = await db.execute(
        select(AbsenceJustification).where(AbsenceJustification.id == justification_id)
    )
    justification = just_result.scalar_one_or_none()
    if justification is None:
        raise NotFoundError("Justification not found", error_code="ERR-ERP-404")
    verify_school_boundary(justification.school_id, auth)

    # 2. Must be pending
    if justification.status != "pending":
        raise ConflictError(
            "Justification has already been reviewed",
            error_code="ERR-ERP-409",
            details={"current_status": justification.status},
        )

    # 3. Rejection requires reason
    if body.decision == "rejected" and not body.rejection_reason:
        raise ValidationError(
            "Rejection reason is required when rejecting a justification",
            error_code="ERR-ERP-422",
        )

    # 4. Update justification status
    justification.status = body.decision
    if body.decision == "rejected":
        justification.rejection_reason = body.rejection_reason

    # If justified, update attendance record status to excused
    if body.decision == "justified":
        record_result = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.id == justification.attendance_record_id
            )
        )
        record = record_result.scalar_one_or_none()
        if record:
            record.status = "excused"

    # 5. Create review record
    review = JustificationReview(
        justification_id=justification_id,
        reviewer_id=auth.user_id,
        school_id=auth.school_id,
        decision=body.decision,
    )
    db.add(review)
    await db.flush()

    # 6. Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="JUSTIFICATION_REVIEWED",
        outcome="success",
        target_type="justification_review",
        target_id=review.id,
        entity_after={
            "justification_id": str(justification_id),
            "decision": body.decision,
        },
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "id": str(review.id),
            "justification_id": str(review.justification_id),
            "reviewer_id": str(review.reviewer_id),
            "school_id": str(review.school_id),
            "decision": review.decision,
        }
    )
