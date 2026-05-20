"""Pydantic schemas for the kid-facing rewards system."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, model_validator


class AwardRewardRequest(BaseModel):
    student_id: uuid.UUID
    event_type: str = Field(..., min_length=1, max_length=50)
    stars: int = Field(0, ge=0)
    xp: int = Field(0, ge=0)
    source_type: str | None = Field(None, max_length=50)
    source_id: uuid.UUID | None = None

    @model_validator(mode="before")
    @classmethod
    def map_legacy_fields(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        payload = dict(value)
        if "stars" not in payload and "stars_earned" in payload:
            payload["stars"] = payload["stars_earned"]
        if "xp" not in payload and "xp_earned" in payload:
            payload["xp"] = payload["xp_earned"]
        return payload


class RewardBadgeResponse(BaseModel):
    id: str
    code: str
    title_en: str | None = None
    title_fr: str | None = None
    title_ar: str | None = None
    description_en: str | None = None
    description_fr: str | None = None
    description_ar: str | None = None
    icon: str | None = None
    criteria_type: str | None = None
    criteria_value: int | None = None
    display_order: int = 0
    is_active: bool = True


class RewardBadgeCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    title_en: str | None = None
    title_fr: str | None = None
    title_ar: str | None = None
    description_en: str | None = None
    description_fr: str | None = None
    description_ar: str | None = None
    icon: str | None = None
    criteria_type: str | None = None
    criteria_value: int | None = Field(None, ge=0)
    display_order: int = Field(0, ge=0)
    is_active: bool = True


class RewardBadgeUpdateRequest(BaseModel):
    code: str | None = Field(None, min_length=1, max_length=50)
    title_en: str | None = None
    title_fr: str | None = None
    title_ar: str | None = None
    description_en: str | None = None
    description_fr: str | None = None
    description_ar: str | None = None
    icon: str | None = None
    criteria_type: str | None = None
    criteria_value: int | None = Field(None, ge=0)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class BadgeResponse(BaseModel):
    code: str
    title: str | None = None
    icon: str | None = None


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
