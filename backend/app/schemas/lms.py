"""LMS domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-051 to S-060
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.rewards import BadgeResponse, StudentRewardResponse


# ---------------------------------------------------------------------------
# Course (S-051)
# ---------------------------------------------------------------------------
class CourseCreateRequest(BaseModel):
    class_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")


class CourseResponse(BaseModel):
    id: str
    school_id: str
    class_id: str
    teacher_id: str
    title: str
    description: str | None = None
    status: str


# ---------------------------------------------------------------------------
# Assignment (S-052)
# ---------------------------------------------------------------------------
class AssignmentCreateRequest(BaseModel):
    course_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    due_at: datetime | None = None
    total_points: int = Field(default=0, ge=0)
    grace_period_hours: int = Field(default=0, ge=0)
    late_penalty_per_day: float = Field(default=0.0, ge=0)
    max_late_days: int | None = Field(default=None, ge=0)
    allow_late: bool = True
    # Phase 9B
    exercise_type: str = Field(
        default="STANDARD", pattern="^(STANDARD|PRINTABLE_PDF|QUIZ)$"
    )
    quiz_id: uuid.UUID | None = None
    # Phase 9C — exercise_pdf_path is set server-side from file upload, not in body


class AssignmentResponse(BaseModel):
    id: str
    course_id: str
    teacher_id: str
    title: str
    description: str | None = None
    due_at: str | None = None
    total_points: int
    exercise_type: str = "STANDARD"
    quiz_id: str | None = None
    exercise_pdf_path: str | None = None


# ---------------------------------------------------------------------------
# Submission (S-053)
# ---------------------------------------------------------------------------
class SubmissionCreateRequest(BaseModel):
    assignment_id: uuid.UUID


class SubmissionResponse(BaseModel):
    id: str
    assignment_id: str
    student_id: str
    status: str
    submitted_at: str | None = None


# ---------------------------------------------------------------------------
# Grade (S-054)
# ---------------------------------------------------------------------------
class GradeRequest(BaseModel):
    score: float = Field(..., ge=0)
    feedback_text: str | None = None
    publish: bool = False


class GradeResponse(BaseModel):
    id: str
    submission_id: str
    teacher_id: str
    score: float
    feedback_text: str | None = None
    published_at: str | None = None


# ---------------------------------------------------------------------------
# Result (S-055)
# ---------------------------------------------------------------------------
class ResultResponse(BaseModel):
    assignment_id: str
    assignment_title: str
    course_title: str
    submission_id: str | None = None
    status: str | None = None
    score: float | None = None
    feedback_text: str | None = None
    total_points: int
    due_at: str | None = None


# ---------------------------------------------------------------------------
# Content Item (S-056)
# ---------------------------------------------------------------------------
class ContentItemResponse(BaseModel):
    id: str
    school_id: str | None = None
    title: str
    content_type: str
    level_band: str | None = None
    language: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    status: str


class ContentItemAssetResponse(BaseModel):
    id: str
    content_item_id: str
    file_path: str
    checksum: str | None = None
    mime_type: str | None = None
    file_size: int | None = None
    page_number: int | None = None
    narration_text: str | None = None
    has_activity: bool
    asset_type: str | None = None


# ---------------------------------------------------------------------------
# Content Progress (S-057)
# ---------------------------------------------------------------------------
class ContentProgressRequest(BaseModel):
    status: str = Field(..., pattern="^(not_started|in_progress|completed)$")


class ContentProgressResponse(BaseModel):
    id: str
    student_id: str
    content_item_id: str
    status: str


class ContentCompleteRequest(BaseModel):
    time_spent_seconds: int | None = Field(default=None, ge=0)


class ContentCompleteResponse(BaseModel):
    progress: ContentProgressResponse
    reward: StudentRewardResponse
    newly_earned_badges: list[BadgeResponse] = Field(default_factory=list)


class ColoringSaveResponse(BaseModel):
    document_id: str
    reward: StudentRewardResponse
    newly_earned_badges: list[BadgeResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Activity (S-058)
# ---------------------------------------------------------------------------
class ActivityResponse(BaseModel):
    id: str
    school_id: str | None = None
    type: str
    difficulty: str | None = None
    title: str
    pedagogical_objective: str | None = None


class ActivitySessionCreateRequest(BaseModel):
    activity_id: uuid.UUID


class ActivitySessionResponse(BaseModel):
    id: str
    student_id: str
    activity_id: str
    status: str
    score: float | None = None
    attempt_no: int


# ---------------------------------------------------------------------------
# Activity Session Complete (S-059)
# ---------------------------------------------------------------------------
class ActivitySessionCompleteRequest(BaseModel):
    score: float | None = Field(default=None, ge=0)


# ---------------------------------------------------------------------------
# Assessment (S-060)
# ---------------------------------------------------------------------------
class AssessmentCreateRequest(BaseModel):
    class_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=300)
    due_at: datetime | None = None
    window_end: datetime | None = None
    total_points: int = Field(default=0, ge=0)
    status: str = Field(default="draft", pattern="^(draft|published|closed)$")


class AssessmentResponse(BaseModel):
    id: str
    class_id: str
    teacher_id: str
    title: str
    due_at: str | None = None
    window_end: str | None = None
    total_points: int
    status: str


class AssessmentResultSubmitRequest(BaseModel):
    assessment_id: uuid.UUID
    score: float | None = Field(default=None, ge=0)


class AssessmentResultResponse(BaseModel):
    id: str
    assessment_id: str
    student_id: str
    score: float | None = None
    status: str
