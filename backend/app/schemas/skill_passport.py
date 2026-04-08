"""Pydantic schemas for life-skills passport workflows."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class SkillDimensionCreateRequest(BaseModel):
    """Payload for creating a skill dimension."""

    code: str = Field(..., min_length=1, max_length=50)
    name_fr: str = Field(..., min_length=1, max_length=200)
    name_ar: str = Field(..., min_length=1, max_length=200)
    name_en: str = Field(..., min_length=1, max_length=200)
    description_fr: str | None = Field(None, max_length=4000)
    icon: str | None = Field(None, max_length=50)
    display_order: int = Field(0, ge=0)
    is_active: bool = True


class SkillDimensionUpdateRequest(BaseModel):
    """Payload for updating a skill dimension."""

    code: str | None = Field(None, min_length=1, max_length=50)
    name_fr: str | None = Field(None, min_length=1, max_length=200)
    name_ar: str | None = Field(None, min_length=1, max_length=200)
    name_en: str | None = Field(None, min_length=1, max_length=200)
    description_fr: str | None = Field(None, max_length=4000)
    icon: str | None = Field(None, max_length=50)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class SkillDimensionResponse(BaseModel):
    """Serialized skill dimension response."""

    id: str
    code: str
    name_fr: str
    name_ar: str
    name_en: str
    description_fr: str | None = None
    icon: str | None = None
    display_order: int
    is_active: bool
    created_at: str
    updated_at: str | None = None


class SkillMilestoneCreateRequest(BaseModel):
    """Payload for creating a skill milestone."""

    dimension_id: uuid.UUID
    code: str = Field(..., min_length=1, max_length=100)
    name_fr: str = Field(..., min_length=1, max_length=200)
    name_ar: str = Field(..., min_length=1, max_length=200)
    level: int = Field(..., ge=1, le=5)
    rule_config: dict[str, Any] = Field(default_factory=dict)
    badge_icon: str | None = Field(None, max_length=50)
    is_active: bool = True


class SkillMilestoneUpdateRequest(BaseModel):
    """Payload for updating a skill milestone."""

    code: str | None = Field(None, min_length=1, max_length=100)
    name_fr: str | None = Field(None, min_length=1, max_length=200)
    name_ar: str | None = Field(None, min_length=1, max_length=200)
    level: int | None = Field(None, ge=1, le=5)
    rule_config: dict[str, Any] | None = None
    badge_icon: str | None = Field(None, max_length=50)
    is_active: bool | None = None


class SkillMilestoneResponse(BaseModel):
    """Serialized skill milestone response."""

    id: str
    dimension_id: str
    dimension_code: str | None = None
    code: str
    name_fr: str
    name_ar: str
    level: int
    rule_config: dict[str, Any]
    badge_icon: str | None = None
    is_active: bool
    created_at: str
    updated_at: str | None = None


class SkillProgressResponse(BaseModel):
    """Serialized skill progress response."""

    id: str
    student_id: str
    school_id: str
    milestone_id: str
    milestone_code: str | None = None
    dimension_id: str | None = None
    dimension_code: str | None = None
    unlocked_at: str | None = None
    current_value: float
    status: str
    evidence: dict[str, Any] | None = None
    academic_year_id: str
    created_at: str
    updated_at: str | None = None


class SkillPassportResponse(BaseModel):
    """Serialized skill passport response."""

    id: str
    student_id: str
    school_id: str
    academic_year_id: str
    generated_at: str
    pdf_url: str | None = None
    total_milestones: int
    unlocked_milestones: int
    overall_score: float
    created_at: str
    updated_at: str | None = None
    progress_items: list[SkillProgressResponse] = Field(default_factory=list)


class SkillEvaluationResponse(BaseModel):
    """Serialized student skill evaluation response."""

    student_id: str
    school_id: str
    academic_year_id: str
    evaluated_at: str
    total_milestones: int
    unlocked_milestones: int
    overall_score: float
    metrics: dict[str, float]
    progress_items: list[SkillProgressResponse] = Field(default_factory=list)


class SkillDimensionAnalyticsResponse(BaseModel):
    """Aggregated analytics for one skill dimension."""

    dimension_id: str
    code: str
    name_fr: str
    milestone_count: int
    unlocked_count: int
    average_progress: float


class SkillClassAnalyticsResponse(BaseModel):
    """Serialized class-level life-skills analytics."""

    class_id: str
    school_id: str
    academic_year_id: str
    student_count: int
    passport_count: int
    active_milestone_count: int
    progress_record_count: int
    unlocked_record_count: int
    average_overall_score: float
    dimension_summaries: list[SkillDimensionAnalyticsResponse] = Field(
        default_factory=list
    )


class SkillSchoolAnalyticsResponse(BaseModel):
    """Serialized school-level life-skills analytics."""

    school_id: str
    academic_year_id: str
    student_count: int
    passport_count: int
    active_milestone_count: int
    progress_record_count: int
    unlocked_record_count: int
    average_overall_score: float
    dimension_summaries: list[SkillDimensionAnalyticsResponse] = Field(
        default_factory=list
    )


class SkillLeaderboardEntryResponse(BaseModel):
    """Serialized leaderboard entry for anonymized ranking."""

    rank: int
    student_id: str
    alias: str
    total_milestones: int
    unlocked_milestones: int
    overall_score: float


__all__ = [
    "SkillDimensionCreateRequest",
    "SkillDimensionUpdateRequest",
    "SkillDimensionResponse",
    "SkillMilestoneCreateRequest",
    "SkillMilestoneUpdateRequest",
    "SkillMilestoneResponse",
    "SkillProgressResponse",
    "SkillPassportResponse",
    "SkillEvaluationResponse",
    "SkillDimensionAnalyticsResponse",
    "SkillClassAnalyticsResponse",
    "SkillSchoolAnalyticsResponse",
    "SkillLeaderboardEntryResponse",
]
