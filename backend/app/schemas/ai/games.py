"""Schemas for mobile game configurations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.ai.rewards import BadgeResponse, StudentRewardResponse


class GameConfigResponse(BaseModel):
    id: str
    game_type: str
    title: str
    title_ar: str | None = None
    title_fr: str | None = None
    subject: str | None = None
    difficulty: str
    target_age_min: int | None = None
    target_age_max: int | None = None
    config: dict[str, Any]
    reward_stars: int
    reward_xp: int
    school_id: str | None = None
    is_active: bool
    created_at: str
    updated_at: str | None = None


class GameConfigCreateRequest(BaseModel):
    game_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=300)
    title_ar: str | None = Field(None, max_length=300)
    title_fr: str | None = Field(None, max_length=300)
    subject: str | None = Field(None, max_length=50)
    difficulty: str = Field("easy", min_length=1, max_length=20)
    target_age_min: int | None = Field(None, ge=0)
    target_age_max: int | None = Field(None, ge=0)
    config: dict[str, Any]
    reward_stars: int = Field(10, ge=0)
    reward_xp: int = Field(15, ge=0)
    is_active: bool = True


class GameConfigUpdateRequest(BaseModel):
    game_type: str | None = Field(None, min_length=1, max_length=50)
    title: str | None = Field(None, min_length=1, max_length=300)
    title_ar: str | None = Field(None, max_length=300)
    title_fr: str | None = Field(None, max_length=300)
    subject: str | None = Field(None, max_length=50)
    difficulty: str | None = Field(None, min_length=1, max_length=20)
    target_age_min: int | None = Field(None, ge=0)
    target_age_max: int | None = Field(None, ge=0)
    config: dict[str, Any] | None = None
    reward_stars: int | None = Field(None, ge=0)
    reward_xp: int | None = Field(None, ge=0)
    is_active: bool | None = None


class GameCompletionRequest(BaseModel):
    score: int = Field(..., ge=0)
    time_seconds: int = Field(..., ge=0)


class GameCompletionResponse(BaseModel):
    reward: StudentRewardResponse
    newly_earned_badges: list[BadgeResponse] = Field(default_factory=list)
