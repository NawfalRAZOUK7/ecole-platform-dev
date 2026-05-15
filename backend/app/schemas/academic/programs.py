"""Pydantic schemas for academic program management & student academic history.

Reference: G49 — Hybrid L2 + L3 versioning shim design.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Program catalog
# ---------------------------------------------------------------------------
class ProgramCreateRequest(BaseModel):
    """Create an academic program (filière) inside the caller's school."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    level: str | None = Field(None, max_length=50)
    description: str | None = None
    version_label: str = Field("1.0", max_length=20)
    effective_from: date | None = None


class ProgramUpdateRequest(BaseModel):
    """Patch an existing program. All fields optional; ``code`` is immutable."""

    name: str | None = Field(None, min_length=1, max_length=200)
    level: str | None = Field(None, max_length=50)
    description: str | None = None
    is_active: bool | None = None
    version_label: str | None = Field(None, max_length=20)
    effective_from: date | None = None


class ProgramResponse(BaseModel):
    id: str
    school_id: str
    code: str
    name: str
    level: str | None
    description: str | None
    is_active: bool
    version_label: str
    effective_from: date | None
    created_at: datetime
    updated_at: datetime | None


# ---------------------------------------------------------------------------
# Program assignment (write)
# ---------------------------------------------------------------------------
class ProgramAssignRequest(BaseModel):
    """Assign or change the program on an existing enrollment.

    The service creates a new active enrollment row (soft-replace) when this
    represents a real change (i.e. the previous enrollment had a different
    program). It always writes one ``ProgramAssignmentEvent`` row.
    """

    program_id: uuid.UUID
    program_version_id: uuid.UUID | None = None
    reason_code: str = Field(
        ...,
        pattern="^(INITIAL|TRANSFER|PROMOTION|CORRECTION|READMISSION)$",
        description=(
            "Why the program is being assigned/changed. "
            "INITIAL: first program for this enrollment. "
            "TRANSFER: same period, switching filière. "
            "PROMOTION: year-rollover. "
            "CORRECTION: fixing a data error. "
            "READMISSION: returning student."
        ),
    )
    reason_note: str | None = Field(None, max_length=2000)


class ProgramAssignmentEventResponse(BaseModel):
    id: str
    school_id: str
    student_id: str
    academic_year_id: str
    period_id: str | None
    from_program_id: str | None
    to_program_id: str
    from_enrollment_id: str | None
    to_enrollment_id: str | None
    reason_code: str
    reason_note: str | None
    actor_user_id: str | None
    occurred_at: datetime


# ---------------------------------------------------------------------------
# Read views — academic timeline + current program
# ---------------------------------------------------------------------------
class ProgramSummary(BaseModel):
    """Lightweight program reference for embedding in timeline/current views."""

    id: str
    code: str
    name: str
    version_label: str


class AcademicTimelineEntry(BaseModel):
    """One row of the per-student academic timeline.

    Each entry corresponds to one ``Enrollment`` joined to ``Class``,
    ``Period``, ``AcademicYear`` and (optionally) ``Program``.
    """

    enrollment_id: str
    academic_year_id: str
    academic_year_label: str | None
    academic_year_start: date
    academic_year_end: date
    period_id: str
    period_label: str | None
    period_start: date
    period_end: date
    class_id: str
    class_code: str
    class_name: str
    program: ProgramSummary | None
    status: str


class CurrentProgramResponse(BaseModel):
    """Convenience shape: 'what is this student studying *right now*?'"""

    student_id: str
    academic_year_id: str | None
    period_id: str | None
    enrollment_id: str | None
    program: ProgramSummary | None


# ---------------------------------------------------------------------------
# Program versions (Phase 3.1)
# ---------------------------------------------------------------------------
class ProgramVersionCreateRequest(BaseModel):
    version_label: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    effective_from: date | None = None
    is_active: bool = True


class ProgramVersionUpdateRequest(BaseModel):
    description: str | None = None
    effective_from: date | None = None
    retired_at: date | None = None
    is_active: bool | None = None


class ProgramVersionResponse(BaseModel):
    id: str
    school_id: str
    program_id: str
    version_label: str
    description: str | None
    effective_from: date | None
    retired_at: date | None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


# ---------------------------------------------------------------------------
# Program equivalences (Phase 3.2)
# ---------------------------------------------------------------------------
class ProgramEquivalenceCreateRequest(BaseModel):
    from_program_id: uuid.UUID
    to_program_id: uuid.UUID
    kind: str = Field(..., pattern="^(EQUIVALENT|SUPERSEDES|PARTIAL)$")
    note: str | None = None
    ratified_at: date | None = None


class ProgramEquivalenceResponse(BaseModel):
    id: str
    school_id: str
    from_program_id: str
    to_program_id: str
    kind: str
    note: str | None
    ratified_at: date | None
    ratified_by: str | None
    created_at: datetime
    updated_at: datetime | None


# ---------------------------------------------------------------------------
# Academic snapshots (Phase 3.3)
# ---------------------------------------------------------------------------
class AcademicSnapshotCreateRequest(BaseModel):
    student_id: uuid.UUID
    academic_year_id: uuid.UUID
    snapshot_kind: str = Field("MANUAL", pattern="^(YEAR_END|MID_YEAR|MANUAL)$")


class AcademicSnapshotResponse(BaseModel):
    id: str
    school_id: str
    student_id: str
    academic_year_id: str
    snapshot_kind: str
    snapshot_data: dict
    taken_at: datetime
    taken_by: str | None


# ---------------------------------------------------------------------------
# Eligibility rules (Phase 3.4)
# ---------------------------------------------------------------------------
class EligibilityRuleCreateRequest(BaseModel):
    kind: str = Field(..., pattern="^(PROMOTION|ADMISSION|TRANSFER)$")
    target_program_id: uuid.UUID
    condition_type: str = Field(..., min_length=1, max_length=40)
    condition_params: dict = Field(default_factory=dict)
    message_key: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True


class EligibilityRuleResponse(BaseModel):
    id: str
    school_id: str
    kind: str
    target_program_id: str
    condition_type: str
    condition_params: dict
    message_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class EligibilityCheckResultItem(BaseModel):
    rule_id: str
    condition_type: str
    message_key: str
    passed: bool
    detail: str | None = None


class EligibilityCheckResponse(BaseModel):
    student_id: str
    target_program_id: str
    kind: str
    eligible: bool
    rules: list[EligibilityCheckResultItem]


# ---------------------------------------------------------------------------
# Transcript view (Phase 3.5)
# ---------------------------------------------------------------------------
class TranscriptProgramSummary(BaseModel):
    id: str
    code: str | None = None
    name: str | None = None
    version_label: str | None = None


class TranscriptEquivalenceResolution(BaseModel):
    program: TranscriptProgramSummary
    resolved_program_ids: list[str]
    resolved_programs: list[TranscriptProgramSummary]


class TranscriptSource(BaseModel):
    mode: str
    snapshot_id: str | None = None
    snapshot_kind: str | None = None
    taken_at: datetime | None = None
    taken_by: str | None = None
    generated_at: datetime
    resolved_at: datetime | None = None
    schema_version: int | None = None


class TranscriptSchool(BaseModel):
    id: str
    name: str | None = None
    code: str | None = None
    city: str | None = None
    region: str | None = None


class TranscriptResponse(BaseModel):
    student: dict
    school: TranscriptSchool
    academic_year: dict
    source: TranscriptSource
    enrollments: list[dict]
    program_events: list[dict]
    grades_summary: list[dict]
    attendance_summary: dict
    equivalence_resolutions: list[TranscriptEquivalenceResolution]
