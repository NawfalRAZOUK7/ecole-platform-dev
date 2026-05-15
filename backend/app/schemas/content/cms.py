"""CMS domain Pydantic schemas — Phase 9A Content Library & Promotion System.

Request/response models for CMS endpoints, content library, and teacher submissions.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# CMS Content (CONTENT_MGR)
# ---------------------------------------------------------------------------
class CmsContentCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content_type: str = Field(..., min_length=1, max_length=50)
    level_band: str | None = None
    language: str | None = Field(None, max_length=10)
    subject: str | None = Field(None, max_length=50)
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")


class CmsContentUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=300)
    content_type: str | None = Field(None, min_length=1, max_length=50)
    level_band: str | None = None
    language: str | None = Field(None, max_length=10)
    subject: str | None = Field(None, max_length=50)
    description: str | None = None
    page_count: int | None = None
    letter: str | None = None
    target_age_min: int | None = None
    target_age_max: int | None = None
    theme_color: str | None = None
    status: str | None = Field(None, pattern="^(draft|published|archived)$")


class CmsContentResponse(BaseModel):
    id: str
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
