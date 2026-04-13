"""Pydantic schemas for student rewards and gamification."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class AwardRewardRequest(BaseModel):
    student_id: uuid.UUID
    event_type: str = Field(..., min_length=1, max_length=50)
    stars_earned: int = Field(0, ge=0)
    xp_earned: int = Field(0, ge=0)
    source_type: str | None = Field(None, max_length=50)
    source_id: uuid.UUID | None = None
    metadata: dict[str, Any] | None = None


class BadgeCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    title_fr: str = Field(..., min_length=1, max_length=100)
    title_ar: str = Field(..., min_length=1, max_length=100)
    title_en: str = Field(..., min_length=1, max_length=100)
    description_fr: str | None = None
    description_ar: str | None = None
    description_en: str | None = None
    icon: str | None = Field(None, max_length=255)
    criteria_type: str = Field(..., min_length=1, max_length=50)
    criteria_value: int = Field(..., ge=0)


class BadgeResponse(BaseModel):
    id: str
    code: str
    title_fr: str
    title_ar: str
    title_en: str
    description_fr: str | None = None
    description_ar: str | None = None
    description_en: str | None = None
    icon: str | None = None
    criteria_type: str
    criteria_value: int
    display_order: int
    is_active: bool
    created_at: str


class StudentRewardResponse(BaseModel):
    id: str
    student_id: str
    stars: int
    xp: int
    level: int
    streak_days: int
    longest_streak: int
    badges: list[str] = Field(default_factory=list)
    last_activity_at: str | None = None
    level_progress: float


class AwardRewardResponse(StudentRewardResponse):
    newly_earned_badges: list[BadgeResponse] = Field(default_factory=list)


class RewardEventResponse(BaseModel):
    id: str
    event_type: str
    stars_earned: int
    xp_earned: int
    source_type: str | None = None
    source_id: str | None = None
    created_at: str


class LeaderboardEntry(BaseModel):
    student_id: str
    student_name: str
    stars: int
    level: int
    rank: int
