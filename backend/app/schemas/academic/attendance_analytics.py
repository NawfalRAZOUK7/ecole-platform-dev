"""Attendance analytics schemas for ENH-C2."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class StudentAbsenceRateResponse(BaseModel):
    student_id: str
    student_name: str | None = None
    period_id: str
    absence_count: int
    total_sessions: int
    absence_rate: float
    mention: str


class ClassAbsenceRateResponse(BaseModel):
    class_id: str
    period_id: str
    students: list[StudentAbsenceRateResponse] = Field(default_factory=list)


class AbsenceTrendPointResponse(BaseModel):
    bucket_start: str
    absent_count: int
    total_sessions: int
    absence_rate: float


class AbsenceTrendResponse(BaseModel):
    class_id: str
    period_id: str
    granularity: str
    points: list[AbsenceTrendPointResponse] = Field(default_factory=list)


class AttendanceAlertResponse(BaseModel):
    id: str
    student_id: str
    student_name: str | None = None
    school_id: str
    period_id: str
    absence_count: int
    total_sessions: int
    absence_rate: float
    threshold_exceeded: str
    notified_at: str | None = None
    created_at: str
    updated_at: str | None = None


class AttendanceThresholdCheckRequest(BaseModel):
    period_id: uuid.UUID


class AttendanceThresholdCheckResponse(BaseModel):
    created: int
    skipped: int
    alerts: list[AttendanceAlertResponse] = Field(default_factory=list)
