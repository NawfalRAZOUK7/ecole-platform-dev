"""Schemas for level-age mapping endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LevelAgeMappingResponse(BaseModel):
    id: str
    level_code: str
    label_fr: str
    label_ar: str | None = None
    label_en: str | None = None
    default_age_min: int
    default_age_max: int
    display_order: int
    school_id: str | None = None


class LevelAgeMappingUpdateRequest(BaseModel):
    label_fr: str | None = None
    label_ar: str | None = None
    label_en: str | None = None
    default_age_min: int | None = Field(None, ge=2, le=20)
    default_age_max: int | None = Field(None, ge=2, le=20)
