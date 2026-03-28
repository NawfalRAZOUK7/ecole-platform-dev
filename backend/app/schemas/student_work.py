"""Schemas for unified student work responses."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StudentWorkItem(BaseModel):
    """Unified view of one assignment, quiz, or assessment."""

    id: str
    type: Literal["assignment", "quiz", "assessment"]
    title: str
    due_at: str | None = None
    status: str | None = None
    total_points: int = Field(ge=0)
    grading_type: Literal["manual", "auto"]


class StudentWorkListResponse(BaseModel):
    """Unified student work list payload."""

    items: list[StudentWorkItem] = Field(default_factory=list)
    total: int = Field(ge=0)
