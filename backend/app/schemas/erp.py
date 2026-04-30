"""ERP domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-047 to S-050
Phase 11A: Added timetable slot and exception schemas.
"""

from __future__ import annotations

import uuid
from datetime import date, time

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------
class ClassResponse(BaseModel):
    id: str
    code: str
    name: str
    school_id: str
    academic_year_id: str
    teacher_count: int
    student_count: int


# ---------------------------------------------------------------------------
# Teacher Assignment (S-047)
# ---------------------------------------------------------------------------
class TeacherAssignmentCreateRequest(BaseModel):
    teacher_id: uuid.UUID
    class_id: uuid.UUID
    period_id: uuid.UUID


class TeacherAssignmentResponse(BaseModel):
    id: str
    teacher_id: str
    class_id: str
    period_id: str
    school_id: str


# ---------------------------------------------------------------------------
# Attendance (S-048)
# ---------------------------------------------------------------------------
class AttendanceRecordInput(BaseModel):
    student_id: uuid.UUID
    status: str = Field(..., pattern="^(present|absent|excused|late)$")
    absence_reason: str | None = None


class AttendanceSessionCreateRequest(BaseModel):
    class_id: uuid.UUID
    period_id: uuid.UUID
    session_date: date
    slot: str = Field(..., min_length=1, max_length=20)
    records: list[AttendanceRecordInput] = Field(..., min_length=1)


class AttendanceRecordResponse(BaseModel):
    id: str
    student_id: str
    status: str
    absence_reason: str | None = None


class AttendanceSessionResponse(BaseModel):
    id: str
    class_id: str
    period_id: str
    teacher_id: str
    school_id: str
    session_date: str
    slot: str
    records: list[AttendanceRecordResponse] = []


# ---------------------------------------------------------------------------
# Absence Justification (S-049)
# ---------------------------------------------------------------------------
class JustificationCreateRequest(BaseModel):
    attendance_record_id: uuid.UUID
    reason: str = Field(..., min_length=1, max_length=2000)


class JustificationResponse(BaseModel):
    id: str
    attendance_record_id: str
    parent_id: str
    school_id: str
    status: str
    reason: str | None = None
    rejection_reason: str | None = None
    attachment_url: str | None = None
    created_at: str | None = None
    student_id: str | None = None
    session_date: str | None = None


# ---------------------------------------------------------------------------
# Justification Review (S-050)
# ---------------------------------------------------------------------------
class JustificationReviewRequest(BaseModel):
    decision: str = Field(..., pattern="^(justified|rejected)$")
    rejection_reason: str | None = None


class JustificationReviewResponse(BaseModel):
    id: str
    justification_id: str
    reviewer_id: str
    school_id: str
    decision: str


# ---------------------------------------------------------------------------
# Enrollment (response, request already exists in enrollments.py)
# ---------------------------------------------------------------------------
class EnrollmentResponse(BaseModel):
    id: str
    student_id: str
    class_id: str
    period_id: str
    school_id: str
    status: str
    # G49 Phase 1 follow-up: populated when the enrollment carries a program,
    # null otherwise. Additive — clients that don't read this field continue
    # to see the same shape as before.
    program_id: str | None = None


# ---------------------------------------------------------------------------
# Timetable Slot (Phase 11A)
# ---------------------------------------------------------------------------
class TimetableSlotCreateRequest(BaseModel):
    class_id: uuid.UUID
    academic_year_id: uuid.UUID
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: time
    end_time: time
    subject: str = Field(..., min_length=1, max_length=200)
    teacher_id: uuid.UUID
    room: str | None = Field(None, max_length=100)
    is_recurring: bool = True
    effective_from: date | None = None
    effective_until: date | None = None


class TimetableSlotBulkCreateRequest(BaseModel):
    """Bulk create multiple timetable slots at once."""

    slots: list[TimetableSlotCreateRequest] = Field(..., min_length=1, max_length=50)


class TimetableSlotUpdateRequest(BaseModel):
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    subject: str | None = Field(None, min_length=1, max_length=200)
    teacher_id: uuid.UUID | None = None
    room: str | None = Field(None, max_length=100)
    is_recurring: bool | None = None
    effective_from: date | None = None
    effective_until: date | None = None


class TimetableSlotResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    academic_year_id: str
    day_of_week: int
    start_time: str
    end_time: str
    subject: str
    teacher_id: str
    room: str | None = None
    is_recurring: bool
    effective_from: str | None = None
    effective_until: str | None = None
    created_at: str
    updated_at: str | None = None


# ---------------------------------------------------------------------------
# Timetable Exception (Phase 11A)
# ---------------------------------------------------------------------------
class TimetableExceptionCreateRequest(BaseModel):
    timetable_slot_id: uuid.UUID
    exception_date: date
    exception_type: str = Field(..., pattern="^(CANCELED|SUBSTITUTED|ROOM_CHANGED)$")
    substitute_teacher_id: uuid.UUID | None = None
    new_room: str | None = Field(None, max_length=100)
    reason: str | None = Field(None, max_length=2000)


class TimetableExceptionResponse(BaseModel):
    id: str
    timetable_slot_id: str
    school_id: str
    exception_date: str
    exception_type: str
    substitute_teacher_id: str | None = None
    new_room: str | None = None
    reason: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Weekly View (Phase 11A)
# ---------------------------------------------------------------------------
class WeeklySlotResponse(BaseModel):
    """A single slot in the weekly timetable view, with exception info if any."""

    id: str
    day_of_week: int
    start_time: str
    end_time: str
    subject: str
    teacher_id: str
    room: str | None = None
    is_recurring: bool
    class_id: str
    class_name: str | None = None
    # Exception overlay for this specific date (None if no exception)
    exception: TimetableExceptionResponse | None = None


class WeeklyTimetableResponse(BaseModel):
    """Full weekly timetable — grouped by day."""

    academic_year_id: str
    week_start: str
    week_end: str
    slots: list[WeeklySlotResponse]
