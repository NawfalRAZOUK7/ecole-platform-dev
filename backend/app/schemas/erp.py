"""ERP domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-047 to S-050
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


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
