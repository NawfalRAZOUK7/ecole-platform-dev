"""Schemas for timetable constraint management and generation jobs."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TimetableConstraintInput(BaseModel):
    constraint_type: str = Field(
        ...,
        pattern=(
            "^(teacher_unavailable|room_capacity|max_consecutive_classes|max_hours_per_day|"
            "subject_hours_per_week|no_consecutive_same_subject)$"
        ),
    )
    entity_id: uuid.UUID | None = None
    params: dict = Field(default_factory=dict)


class TimetableConstraintSetRequest(BaseModel):
    academic_year_id: uuid.UUID
    constraints: list[TimetableConstraintInput] = Field(default_factory=list)


class TimetableConstraintResponse(BaseModel):
    id: str
    school_id: str
    academic_year_id: str
    constraint_type: str
    entity_id: str | None = None
    params: dict = Field(default_factory=dict)
    created_at: str
    updated_at: str | None = None


class TimetableGenerateRequest(BaseModel):
    academic_year_id: uuid.UUID


class TimetableGenerationConflictResponse(BaseModel):
    class_id: str | None = None
    class_name: str | None = None
    subject: str | None = None
    detail: str


class GeneratedTimetableSlotResponse(BaseModel):
    class_id: str
    class_name: str | None = None
    academic_year_id: str
    day_of_week: int
    start_time: str
    end_time: str
    subject: str
    teacher_id: str
    room: str | None = None
    is_recurring: bool = True
    effective_from: str | None = None
    effective_until: str | None = None


class TimetableGenerationJobResponse(BaseModel):
    id: str
    school_id: str
    academic_year_id: str
    status: str
    result_slot_count: int | None = None
    conflicts_found: int | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None


class TimetableGenerationPreviewResponse(BaseModel):
    job: TimetableGenerationJobResponse
    slots: list[GeneratedTimetableSlotResponse] = Field(default_factory=list)
    conflicts: list[TimetableGenerationConflictResponse] = Field(default_factory=list)


class TimetableGenerationApplyResponse(BaseModel):
    job_id: str
    status: str
    created_count: int
