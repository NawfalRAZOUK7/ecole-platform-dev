"""CMS domain Pydantic schemas — Phase 9A Content Library & Promotion System.

Request/response models for CMS endpoints, content library, and teacher submissions.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.curriculum import (
    is_official_subject,
    is_subject_valid_for_level,
    matieres_for_level,
)
from app.models.lms import CONTENT_LEVEL_BANDS


def _ensure_level_band(value: str | None) -> str | None:
    if value is not None and value not in CONTENT_LEVEL_BANDS:
        raise ValueError(
            f"level_band must be null or one of {', '.join(CONTENT_LEVEL_BANDS)}"
        )
    return value


def _ensure_subject(value: str | None) -> str | None:
    # subject = matière, official (curriculum) OR a school custom one — so it is a
    # free String here; the *service* layer rejects unknown values (not official
    # and not a registered custom matière for the school).
    if value is not None:
        value = value.strip()
        if not value:
            return None
    return value


def _ensure_subject_for_level(level_band: str | None, subject: str | None) -> None:
    """Curriculum cross-field rule: an OFFICIAL matière must be taught at its niveau.

    Custom (non-official) matières are school-defined and bypass this check (the
    service validates they exist for the school). Out-of-scope levels (collège/
    lycée) are not constrained either.
    """
    if (
        level_band
        and subject
        and is_official_subject(subject)
        and not is_subject_valid_for_level(subject, level_band)
    ):
        allowed = ", ".join(matieres_for_level(level_band)) or "(none defined yet)"
        raise ValueError(
            f"subject '{subject}' is not taught at level '{level_band}'. "
            f"Allowed matières: {allowed}"
        )


# ---------------------------------------------------------------------------
# CMS Content (CONTENT_MGR)
# ---------------------------------------------------------------------------
class CmsContentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content_type: str = Field(..., min_length=1, max_length=50)
    level_band: str | None = None
    language: str | None = Field(None, max_length=10)
    subject: str | None = Field(None, max_length=50)
    subject_other: str | None = Field(None, max_length=120)  # name when subject == "other"
    topic: str | None = Field(None, max_length=200)  # sujet — free text
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")

    @field_validator("level_band")
    @classmethod
    def _check_level_band(cls, v: str | None) -> str | None:
        return _ensure_level_band(v)

    @field_validator("subject")
    @classmethod
    def _check_subject(cls, v: str | None) -> str | None:
        return _ensure_subject(v)

    @model_validator(mode="after")
    def _check_subject_for_level(self) -> "CmsContentCreateRequest":
        _ensure_subject_for_level(self.level_band, self.subject)
        return self


class CmsContentUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    content_type: str | None = Field(None, min_length=1, max_length=50)
    level_band: str | None = None
    language: str | None = Field(None, max_length=10)
    subject: str | None = Field(None, max_length=50)
    subject_other: str | None = Field(None, max_length=120)  # name when subject == "other"
    topic: str | None = Field(None, max_length=200)  # sujet — free text
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    status: str | None = Field(None, pattern="^(draft|published|archived)$")

    @field_validator("level_band")
    @classmethod
    def _check_level_band(cls, v: str | None) -> str | None:
        return _ensure_level_band(v)

    @field_validator("subject")
    @classmethod
    def _check_subject(cls, v: str | None) -> str | None:
        return _ensure_subject(v)

    @model_validator(mode="after")
    def _check_subject_for_level(self) -> "CmsContentUpdateRequest":
        _ensure_subject_for_level(self.level_band, self.subject)
        return self


class CmsContentResponse(BaseModel):
    id: str
    title: str
    content_type: str
    level_band: str | None = None
    language: str | None = None
    subject: str | None = None
    subject_other: str | None = None
    topic: str | None = None
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    thumbnail_path: str | None = None
    origin: str
    status: str
    created_by: str | None = None
    original_content_id: str | None = None


# ---------------------------------------------------------------------------
# Content Review (CONTENT_MGR)
# ---------------------------------------------------------------------------
class ReviewDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVED|REJECTED)$")
    review_notes: str | None = None
    reward_points: int = Field(default=10, ge=0, le=1000)


class ContentSubmissionResponse(BaseModel):
    id: str
    content_item_id: str
    content_title: str | None = None
    submitted_by: str
    submitter_name: str | None = None
    school_id: str
    status: str
    submitted_at: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_notes: str | None = None
    promoted_content_id: str | None = None


# ---------------------------------------------------------------------------
# Teacher: Content Library + Assign + Submit
# ---------------------------------------------------------------------------
class ContentAssignRequest(BaseModel):
    class_id: uuid.UUID
    content_item_id: uuid.UUID
    notes: str | None = None


class ContentAssignResponse(BaseModel):
    id: str
    teacher_id: str
    class_id: str
    content_item_id: str
    school_id: str
    assigned_at: str
    notes: str | None = None


class ContentSubmitForReviewRequest(BaseModel):
    content_item_id: uuid.UUID


class MySubmissionResponse(BaseModel):
    id: str
    content_item_id: str
    content_title: str | None = None
    status: str
    submitted_at: str
    review_notes: str | None = None
    promoted_content_id: str | None = None


# ---------------------------------------------------------------------------
# Student: Class Content
# ---------------------------------------------------------------------------
class ClassContentResponse(BaseModel):
    id: str
    content_item_id: str
    title: str
    content_type: str
    level_band: str | None = None
    language: str | None = None
    subject: str | None = None
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    assigned_at: str
    teacher_notes: str | None = None
