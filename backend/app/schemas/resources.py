"""Phase 16 resource library schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field, field_validator


class ResourceCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=120)
    level: str | None = Field(default=None, max_length=120)
    type: str = Field(
        ...,
        pattern="^(lesson_plan|worksheet|presentation|exam_template|reference)$",
    )
    visibility: str = Field(..., pattern="^(school|class)$")
    class_id: uuid.UUID | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item.strip()]


class ResourceUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    subject: str | None = Field(default=None, max_length=120)
    level: str | None = Field(default=None, max_length=120)
    type: str | None = Field(
        default=None,
        pattern="^(lesson_plan|worksheet|presentation|exam_template|reference)$",
    )
    visibility: str | None = Field(default=None, pattern="^(school|class)$")
    class_id: uuid.UUID | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return [item.strip() for item in value if item.strip()]


class ResourceRatingRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)

