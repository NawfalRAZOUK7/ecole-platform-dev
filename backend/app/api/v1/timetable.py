"""Timetable API endpoints — Phase 11A.

Reference: Phase 11A — Timetable / Schedule Management
Endpoints:
  POST   /timetable/slots              — Create slot(s) (ADM)
  GET    /timetable/slots              — List slots with filters (ADM, TCH, PAR, STD)
  PUT    /timetable/slots/{id}         — Update a slot (ADM)
  DELETE /timetable/slots/{id}         — Delete a slot (ADM)
  GET    /timetable/class/{id}/weekly  — Weekly view for a class
  GET    /timetable/teacher/{id}/weekly — Weekly view for a teacher
  GET    /timetable/me/weekly          — Weekly view for current user
  POST   /timetable/exceptions         — Create exception (ADM, TCH)
  GET    /timetable/exceptions         — List exceptions with filters
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    get_parent_child_ids,
    requires_permission,
    verify_school_boundary,
)
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.response import list_response, success_response
from app.models.erp import (
    AcademicYear,
    Class,
    Enrollment,
    TimetableException,
    TimetableSlot,
)
from app.schemas.erp import (
    TimetableExceptionCreateRequest,
    TimetableExceptionResponse,
    TimetableSlotBulkCreateRequest,
    TimetableSlotCreateRequest,
    TimetableSlotResponse,
    TimetableSlotUpdateRequest,
    WeeklySlotResponse,
    WeeklyTimetableResponse,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/timetable", tags=["erp-timetable"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _slot_to_response(slot: TimetableSlot) -> dict:
    """Convert a TimetableSlot ORM instance to a response dict."""
    return TimetableSlotResponse(
        id=str(slot.id),
        school_id=str(slot.school_id),
        class_id=str(slot.class_id),
        academic_year_id=str(slot.academic_year_id),
        day_of_week=slot.day_of_week,
        start_time=slot.start_time.strftime("%H:%M"),
        end_time=slot.end_time.strftime("%H:%M"),
        subject=slot.subject,
        teacher_id=str(slot.teacher_id),
        room=slot.room,
        is_recurring=slot.is_recurring,
        effective_from=slot.effective_from.isoformat() if slot.effective_from else None,
        effective_until=slot.effective_until.isoformat()
        if slot.effective_until
        else None,
        created_at=slot.created_at.isoformat(),
        updated_at=slot.updated_at.isoformat() if slot.updated_at else None,
    ).model_dump()


def _exception_to_response(exc: TimetableException) -> dict:
    """Convert a TimetableException ORM instance to a response dict."""
    return TimetableExceptionResponse(
        id=str(exc.id),
        timetable_slot_id=str(exc.timetable_slot_id),
        school_id=str(exc.school_id),
        exception_date=exc.exception_date.isoformat(),
        exception_type=exc.exception_type,
        substitute_teacher_id=str(exc.substitute_teacher_id)
        if exc.substitute_teacher_id
        else None,
        new_room=exc.new_room,
        reason=exc.reason,
        created_at=exc.created_at.isoformat(),
    ).model_dump()


async def _check_overlap(
    db: AsyncSession,
    school_id: uuid.UUID,
    class_id: uuid.UUID,
    teacher_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    day_of_week: int,
    start_time,
    end_time,
    exclude_slot_id: uuid.UUID | None = None,
) -> None:
    """Validate no overlapping slots for the same class or teacher.

    Overlap: two slots overlap if they share the same day_of_week and
    their time ranges overlap (slot1.start < slot2.end AND slot1.end > slot2.start).
    """
    # Check class overlap
    class_query = select(TimetableSlot).where(
        TimetableSlot.school_id == school_id,
        TimetableSlot.class_id == class_id,
        TimetableSlot.academic_year_id == academic_year_id,
        TimetableSlot.day_of_week == day_of_week,
        TimetableSlot.start_time < end_time,
        TimetableSlot.end_time > start_time,
    )
    if exclude_slot_id:
        class_query = class_query.where(TimetableSlot.id != exclude_slot_id)
    class_result = await db.execute(class_query)
    if class_result.scalar_one_or_none() is not None:
        raise ConflictError(
            "Class already has a slot at this time",
            error_code="ERR-ERP-409",
            details={"class_id": str(class_id), "day_of_week": day_of_week},
        )

    # Check teacher overlap
    teacher_query = select(TimetableSlot).where(
        TimetableSlot.school_id == school_id,
        TimetableSlot.teacher_id == teacher_id,
        TimetableSlot.academic_year_id == academic_year_id,
        TimetableSlot.day_of_week == day_of_week,
        TimetableSlot.start_time < end_time,
        TimetableSlot.end_time > start_time,
    )
    if exclude_slot_id:
        teacher_query = teacher_query.where(TimetableSlot.id != exclude_slot_id)
    teacher_result = await db.execute(teacher_query)
    if teacher_result.scalar_one_or_none() is not None:
        raise ConflictError(
            "Teacher already has a slot at this time",
            error_code="ERR-ERP-409",
            details={"teacher_id": str(teacher_id), "day_of_week": day_of_week},
        )


def _get_week_bounds(target_date: date) -> tuple[date, date]:
    """Return (Monday, Sunday) of the week containing target_date."""
    monday = target_date - timedelta(days=target_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


# ---------------------------------------------------------------------------
# POST /timetable/slots — Create slot(s) (ADM)
# ---------------------------------------------------------------------------
@router.post(
    "/slots",
    status_code=201,
    summary="Create timetable slot(s)",
    response_description="Created timetable slot(s)",
)
async def create_timetable_slots(
    body: TimetableSlotCreateRequest | TimetableSlotBulkCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:create")),
    db: AsyncSession = Depends(get_db),
):
    """Create one or more timetable slots.

    Accepts either a single slot or a bulk request with up to 50 slots.
    Validates:
    1. Class exists and belongs to the same school
    2. Academic year exists and belongs to the same school
    3. end_time > start_time
    4. No overlapping slots for the same class or teacher
    """
    audit = AuditService(db)

    # Normalize to list
    if isinstance(body, TimetableSlotCreateRequest):
        slot_requests = [body]
    else:
        slot_requests = body.slots

    created_slots = []

    for slot_req in slot_requests:
        # Validate time ordering
        if slot_req.end_time <= slot_req.start_time:
            raise ValidationError(
                "end_time must be after start_time",
                error_code="ERR-ERP-422",
                details={
                    "start_time": str(slot_req.start_time),
                    "end_time": str(slot_req.end_time),
                },
            )

        # Validate class exists + school boundary
        class_result = await db.execute(
            select(Class).where(Class.id == slot_req.class_id)
        )
        cls = class_result.scalar_one_or_none()
        if cls is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        verify_school_boundary(cls.school_id, auth)

        # Validate academic year exists + school boundary
        ay_result = await db.execute(
            select(AcademicYear).where(AcademicYear.id == slot_req.academic_year_id)
        )
        ay = ay_result.scalar_one_or_none()
        if ay is None:
            raise NotFoundError("Academic year not found", error_code="ERR-ERP-404")
        verify_school_boundary(ay.school_id, auth)

        # Check overlap
        await _check_overlap(
            db=db,
            school_id=auth.school_id,
            class_id=slot_req.class_id,
            teacher_id=slot_req.teacher_id,
            academic_year_id=slot_req.academic_year_id,
            day_of_week=slot_req.day_of_week,
            start_time=slot_req.start_time,
            end_time=slot_req.end_time,
        )

        slot = TimetableSlot(
            school_id=auth.school_id,
            class_id=slot_req.class_id,
            academic_year_id=slot_req.academic_year_id,
            day_of_week=slot_req.day_of_week,
            start_time=slot_req.start_time,
            end_time=slot_req.end_time,
            subject=slot_req.subject,
            teacher_id=slot_req.teacher_id,
            room=slot_req.room,
            is_recurring=slot_req.is_recurring,
            effective_from=slot_req.effective_from,
            effective_until=slot_req.effective_until,
        )
        db.add(slot)
        await db.flush()
        created_slots.append(slot)

        await audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="timetable_slot.create",
            target_type="timetable_slot",
            target_id=slot.id,
            outcome="success",
            entity_after=_slot_to_response(slot),
            ip_address=_get_client_ip(request),
        )

    await db.commit()

    response_data = [_slot_to_response(s) for s in created_slots]

    if len(response_data) == 1:
        return success_response(response_data[0])
    return success_response(response_data)


# ---------------------------------------------------------------------------
# GET /timetable/slots — List slots with filters
# ---------------------------------------------------------------------------
@router.get(
    "/slots",
    summary="List timetable slots",
    response_description="Filtered list of timetable slots",
)
async def list_timetable_slots(
    class_id: uuid.UUID | None = Query(None),
    teacher_id: uuid.UUID | None = Query(None),
    academic_year_id: uuid.UUID | None = Query(None),
    day_of_week: int | None = Query(None, ge=0, le=6),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """List timetable slots with optional filters.

    Filters: class_id, teacher_id, academic_year_id, day_of_week.
    Always scoped to the user's school.
    """
    query = select(TimetableSlot).where(TimetableSlot.school_id == auth.school_id)

    if class_id:
        query = query.where(TimetableSlot.class_id == class_id)
    if teacher_id:
        query = query.where(TimetableSlot.teacher_id == teacher_id)
    if academic_year_id:
        query = query.where(TimetableSlot.academic_year_id == academic_year_id)
    if day_of_week is not None:
        query = query.where(TimetableSlot.day_of_week == day_of_week)

    query = query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
    result = await db.execute(query)
    slots = result.scalars().all()

    return list_response([_slot_to_response(s) for s in slots])


# ---------------------------------------------------------------------------
# PUT /timetable/slots/{slot_id} — Update a slot (ADM)
# ---------------------------------------------------------------------------
@router.put(
    "/slots/{slot_id}",
    summary="Update timetable slot",
    response_description="Updated timetable slot",
)
async def update_timetable_slot(
    slot_id: uuid.UUID,
    body: TimetableSlotUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing timetable slot.

    Validates overlap after applying changes.
    """
    audit = AuditService(db)

    result = await db.execute(select(TimetableSlot).where(TimetableSlot.id == slot_id))
    slot = result.scalar_one_or_none()
    if slot is None:
        raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
    verify_school_boundary(slot.school_id, auth)

    entity_before = _slot_to_response(slot)

    # Apply updates
    if body.day_of_week is not None:
        slot.day_of_week = body.day_of_week
    if body.start_time is not None:
        slot.start_time = body.start_time
    if body.end_time is not None:
        slot.end_time = body.end_time
    if body.subject is not None:
        slot.subject = body.subject
    if body.teacher_id is not None:
        slot.teacher_id = body.teacher_id
    if body.room is not None:
        slot.room = body.room
    if body.is_recurring is not None:
        slot.is_recurring = body.is_recurring
    if body.effective_from is not None:
        slot.effective_from = body.effective_from
    if body.effective_until is not None:
        slot.effective_until = body.effective_until

    # Validate time ordering
    if slot.end_time <= slot.start_time:
        raise ValidationError(
            "end_time must be after start_time",
            error_code="ERR-ERP-422",
        )

    # Check overlap (exclude self)
    await _check_overlap(
        db=db,
        school_id=auth.school_id,
        class_id=slot.class_id,
        teacher_id=slot.teacher_id,
        academic_year_id=slot.academic_year_id,
        day_of_week=slot.day_of_week,
        start_time=slot.start_time,
        end_time=slot.end_time,
        exclude_slot_id=slot.id,
    )

    await db.flush()

    entity_after = _slot_to_response(slot)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="timetable_slot.update",
        target_type="timetable_slot",
        target_id=slot.id,
        outcome="success",
        entity_before=entity_before,
        entity_after=entity_after,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(entity_after)


# ---------------------------------------------------------------------------
# DELETE /timetable/slots/{slot_id} — Delete a slot (ADM)
# ---------------------------------------------------------------------------
@router.delete(
    "/slots/{slot_id}",
    status_code=200,
    summary="Delete timetable slot",
    response_description="Deletion confirmation",
)
async def delete_timetable_slot(
    slot_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a timetable slot and all its exceptions (cascade)."""
    audit = AuditService(db)

    result = await db.execute(select(TimetableSlot).where(TimetableSlot.id == slot_id))
    slot = result.scalar_one_or_none()
    if slot is None:
        raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
    verify_school_boundary(slot.school_id, auth)

    entity_before = _slot_to_response(slot)
    await db.delete(slot)

    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="timetable_slot.delete",
        target_type="timetable_slot",
        target_id=slot.id,
        outcome="success",
        entity_before=entity_before,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response({"deleted": True, "id": str(slot_id)})


# ---------------------------------------------------------------------------
# GET /timetable/class/{class_id}/weekly — Weekly view for a class
# ---------------------------------------------------------------------------
@router.get(
    "/class/{class_id}/weekly",
    summary="Weekly timetable for a class",
    response_description="Weekly timetable with exceptions",
)
async def get_class_weekly_timetable(
    class_id: uuid.UUID,
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for a class, with exception overlays."""
    # Validate class
    class_result = await db.execute(select(Class).where(Class.id == class_id))
    cls = class_result.scalar_one_or_none()
    if cls is None:
        raise NotFoundError("Class not found", error_code="ERR-ERP-404")
    verify_school_boundary(cls.school_id, auth)

    return await _build_weekly_timetable(
        db=db,
        school_id=auth.school_id,
        target_date=target_date or date.today(),
        class_id=class_id,
    )


# ---------------------------------------------------------------------------
# GET /timetable/teacher/{teacher_id}/weekly — Weekly view for a teacher
# ---------------------------------------------------------------------------
@router.get(
    "/teacher/{teacher_id}/weekly",
    summary="Weekly timetable for a teacher",
    response_description="Weekly timetable with exceptions",
)
async def get_teacher_weekly_timetable(
    teacher_id: uuid.UUID,
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(requires_permission("PERM-ERP:timetable:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for a teacher, with exception overlays."""
    return await _build_weekly_timetable(
        db=db,
        school_id=auth.school_id,
        target_date=target_date or date.today(),
        teacher_id=teacher_id,
    )


# ---------------------------------------------------------------------------
# GET /timetable/me/weekly — Weekly view for current user
# ---------------------------------------------------------------------------
@router.get(
    "/me/weekly",
    summary="My weekly timetable",
    response_description="Weekly timetable for current user",
)
async def get_my_weekly_timetable(
    target_date: date | None = Query(
        None, description="Any date in the target week (defaults to today)"
    ),
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the weekly timetable for the current user.

    - TCH: returns teacher's own timetable
    - STD: returns student's class timetable
    - PAR: returns first child's class timetable (use /class/{id}/weekly for specific child)
    - ADM/DIR: returns empty (use explicit class/teacher views)
    """
    td = target_date or date.today()

    if auth.role == "TCH":
        return await _build_weekly_timetable(
            db=db,
            school_id=auth.school_id,
            target_date=td,
            teacher_id=auth.user_id,
        )

    if auth.role == "STD":
        # Find student's active class
        class_id = await _get_student_class_id(db, auth.user_id, auth.school_id)
        if class_id is None:
            return success_response(
                WeeklyTimetableResponse(
                    academic_year_id="",
                    week_start=td.isoformat(),
                    week_end=td.isoformat(),
                    slots=[],
                ).model_dump()
            )
        return await _build_weekly_timetable(
            db=db,
            school_id=auth.school_id,
            target_date=td,
            class_id=class_id,
        )

    if auth.role == "PAR":
        # Get first child's class
        child_ids = await get_parent_child_ids(auth.user_id, auth.school_id, db)
        if not child_ids:
            return success_response(
                WeeklyTimetableResponse(
                    academic_year_id="",
                    week_start=td.isoformat(),
                    week_end=td.isoformat(),
                    slots=[],
                ).model_dump()
            )
        first_child_id = next(iter(child_ids))
        class_id = await _get_student_class_id(db, first_child_id, auth.school_id)
        if class_id is None:
            return success_response(
                WeeklyTimetableResponse(
                    academic_year_id="",
                    week_start=td.isoformat(),
                    week_end=td.isoformat(),
                    slots=[],
                ).model_dump()
            )
        return await _build_weekly_timetable(
            db=db,
            school_id=auth.school_id,
            target_date=td,
            class_id=class_id,
        )

    # ADM/DIR/SUP — return empty
    monday, sunday = _get_week_bounds(td)
    return success_response(
        WeeklyTimetableResponse(
            academic_year_id="",
            week_start=monday.isoformat(),
            week_end=sunday.isoformat(),
            slots=[],
        ).model_dump()
    )


# ---------------------------------------------------------------------------
# POST /timetable/exceptions — Create exception (ADM, TCH)
# ---------------------------------------------------------------------------
@router.post(
    "/exceptions",
    status_code=201,
    summary="Create timetable exception",
    response_description="Created timetable exception",
)
async def create_timetable_exception(
    body: TimetableExceptionCreateRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-exception:create")
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create an exception for a timetable slot (cancel, substitute, room change).

    Validates:
    1. Slot exists and belongs to the same school
    2. No duplicate exception for same slot+date
    3. SUBSTITUTED requires substitute_teacher_id
    4. ROOM_CHANGED requires new_room
    """
    audit = AuditService(db)

    # Validate slot exists
    slot_result = await db.execute(
        select(TimetableSlot).where(TimetableSlot.id == body.timetable_slot_id)
    )
    slot = slot_result.scalar_one_or_none()
    if slot is None:
        raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")
    verify_school_boundary(slot.school_id, auth)

    # TCH ABAC: teacher can only create exceptions for their own slots
    if auth.role == "TCH" and slot.teacher_id != auth.user_id:
        raise NotFoundError("Timetable slot not found", error_code="ERR-ERP-404")

    # Validate exception_type-specific fields
    if body.exception_type == "SUBSTITUTED" and body.substitute_teacher_id is None:
        raise ValidationError(
            "substitute_teacher_id is required for SUBSTITUTED exceptions",
            error_code="ERR-ERP-422",
        )
    if body.exception_type == "ROOM_CHANGED" and body.new_room is None:
        raise ValidationError(
            "new_room is required for ROOM_CHANGED exceptions",
            error_code="ERR-ERP-422",
        )

    # Check duplicate
    dup_result = await db.execute(
        select(TimetableException).where(
            TimetableException.timetable_slot_id == body.timetable_slot_id,
            TimetableException.exception_date == body.exception_date,
        )
    )
    if dup_result.scalar_one_or_none() is not None:
        raise ConflictError(
            "An exception already exists for this slot on this date",
            error_code="ERR-ERP-409",
        )

    exception = TimetableException(
        timetable_slot_id=body.timetable_slot_id,
        school_id=auth.school_id,
        exception_date=body.exception_date,
        exception_type=body.exception_type,
        substitute_teacher_id=body.substitute_teacher_id,
        new_room=body.new_room,
        reason=body.reason,
    )
    db.add(exception)
    await db.flush()

    resp = _exception_to_response(exception)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="timetable_exception.create",
        target_type="timetable_exception",
        target_id=exception.id,
        outcome="success",
        entity_after=resp,
        ip_address=_get_client_ip(request),
    )

    await db.commit()
    return success_response(resp)


# ---------------------------------------------------------------------------
# GET /timetable/exceptions — List exceptions
# ---------------------------------------------------------------------------
@router.get(
    "/exceptions",
    summary="List timetable exceptions",
    response_description="Filtered list of timetable exceptions",
)
async def list_timetable_exceptions(
    timetable_slot_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    exception_type: str | None = Query(
        None, pattern="^(CANCELED|SUBSTITUTED|ROOM_CHANGED)$"
    ),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:timetable-exception:read")
    ),
    db: AsyncSession = Depends(get_db),
):
    """List timetable exceptions with optional filters."""
    query = select(TimetableException).where(
        TimetableException.school_id == auth.school_id
    )

    if timetable_slot_id:
        query = query.where(TimetableException.timetable_slot_id == timetable_slot_id)
    if date_from:
        query = query.where(TimetableException.exception_date >= date_from)
    if date_to:
        query = query.where(TimetableException.exception_date <= date_to)
    if exception_type:
        query = query.where(TimetableException.exception_type == exception_type)

    query = query.order_by(TimetableException.exception_date.desc())
    result = await db.execute(query)
    exceptions = result.scalars().all()

    return list_response([_exception_to_response(e) for e in exceptions])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_student_class_id(
    db: AsyncSession,
    student_id: uuid.UUID,
    school_id: uuid.UUID,
) -> uuid.UUID | None:
    """Get the class_id for a student's active enrollment."""
    result = await db.execute(
        select(Enrollment.class_id)
        .where(
            Enrollment.student_id == student_id,
            Enrollment.school_id == school_id,
            Enrollment.status == "active",
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _build_weekly_timetable(
    db: AsyncSession,
    school_id: uuid.UUID,
    target_date: date,
    class_id: uuid.UUID | None = None,
    teacher_id: uuid.UUID | None = None,
) -> dict:
    """Build a weekly timetable view with exception overlays.

    Exactly one of class_id or teacher_id must be provided.
    """
    monday, sunday = _get_week_bounds(target_date)

    # Build slot query
    query = select(TimetableSlot).where(TimetableSlot.school_id == school_id)
    if class_id:
        query = query.where(TimetableSlot.class_id == class_id)
    if teacher_id:
        query = query.where(TimetableSlot.teacher_id == teacher_id)

    # Filter by effective dates (slot must be active during this week)
    query = query.where(
        and_(
            # effective_from is NULL or <= sunday
            (TimetableSlot.effective_from.is_(None))
            | (TimetableSlot.effective_from <= sunday),
            # effective_until is NULL or >= monday
            (TimetableSlot.effective_until.is_(None))
            | (TimetableSlot.effective_until >= monday),
        )
    )

    query = query.order_by(TimetableSlot.day_of_week, TimetableSlot.start_time)
    result = await db.execute(query)
    slots = result.scalars().all()

    if not slots:
        return success_response(
            WeeklyTimetableResponse(
                academic_year_id="",
                week_start=monday.isoformat(),
                week_end=sunday.isoformat(),
                slots=[],
            ).model_dump()
        )

    slot_ids = [s.id for s in slots]
    academic_year_id = str(slots[0].academic_year_id) if slots else ""

    # Load exceptions for this week
    exc_result = await db.execute(
        select(TimetableException).where(
            TimetableException.timetable_slot_id.in_(slot_ids),
            TimetableException.exception_date >= monday,
            TimetableException.exception_date <= sunday,
        )
    )
    exceptions = exc_result.scalars().all()
    exc_by_slot: dict[uuid.UUID, dict[date, TimetableException]] = {}
    for exc in exceptions:
        exc_by_slot.setdefault(exc.timetable_slot_id, {})[exc.exception_date] = exc

    # Load class names
    class_ids = {s.class_id for s in slots}
    class_result = await db.execute(select(Class).where(Class.id.in_(class_ids)))
    class_map = {c.id: c.name for c in class_result.scalars().all()}

    # Build response
    weekly_slots = []
    for slot in slots:
        # Check the exception for this slot's day in this week
        slot_date = monday + timedelta(days=slot.day_of_week)
        exc = exc_by_slot.get(slot.id, {}).get(slot_date)

        weekly_slots.append(
            WeeklySlotResponse(
                id=str(slot.id),
                day_of_week=slot.day_of_week,
                start_time=slot.start_time.strftime("%H:%M"),
                end_time=slot.end_time.strftime("%H:%M"),
                subject=slot.subject,
                teacher_id=str(slot.teacher_id),
                room=slot.room,
                is_recurring=slot.is_recurring,
                class_id=str(slot.class_id),
                class_name=class_map.get(slot.class_id),
                exception=TimetableExceptionResponse(
                    id=str(exc.id),
                    timetable_slot_id=str(exc.timetable_slot_id),
                    school_id=str(exc.school_id),
                    exception_date=exc.exception_date.isoformat(),
                    exception_type=exc.exception_type,
                    substitute_teacher_id=str(exc.substitute_teacher_id)
                    if exc.substitute_teacher_id
                    else None,
                    new_room=exc.new_room,
                    reason=exc.reason,
                    created_at=exc.created_at.isoformat(),
                )
                if exc
                else None,
            ).model_dump()
        )

    return success_response(
        WeeklyTimetableResponse(
            academic_year_id=academic_year_id,
            week_start=monday.isoformat(),
            week_end=sunday.isoformat(),
            slots=weekly_slots,
        ).model_dump()
    )
