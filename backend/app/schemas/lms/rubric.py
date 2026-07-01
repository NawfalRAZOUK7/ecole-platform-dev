"""Rubric Engine Pydantic schemas — model and grading payloads."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class LevelInput(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    points: float = Field(..., ge=0)
    position: int = Field(default=0, ge=0)


class CriterionInput(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    weight: float = Field(default=1.0, ge=0)
    position: int = Field(default=0, ge=0)
    levels: list[LevelInput] = Field(default_factory=list)


class RubricCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = None
    total_points: int = Field(default=20, ge=0)
    is_template: bool = False
    criteria: list[CriterionInput] = Field(default_factory=list)


class LevelResponse(BaseModel):
    id: str
    criterion_id: str
    label: str
    description: str | None = None
    points: float
    position: int


class CriterionResponse(BaseModel):
    id: str
    rubric_id: str
    title: str
    description: str | None = None
    weight: float
    position: int
    levels: list[LevelResponse] = Field(default_factory=list)


class RubricResponse(BaseModel):
    id: str
    school_id: str
    teacher_id: str
    title: str
    description: str | None = None
    total_points: int
    is_template: bool
    criteria: list[CriterionResponse] = Field(default_factory=list)


class RubricScoreInput(BaseModel):
    criterion_id: uuid.UUID
    level_id: uuid.UUID | None = None
    points_awarded: float = Field(..., ge=0)
    comment: str | None = None


class RubricScoreResponse(BaseModel):
    id: str
    submission_id: str
    criterion_id: str
    criterion_title: str | None = None
    criterion_weight: float | None = None
    level_id: str | None = None
    level_label: str | None = None
    level_points: float | None = None
    points_awarded: float
    comment: str | None = None


class RubricResultsResponse(BaseModel):
    submission_id: str
    assignment_id: str | None = None
    rubric_id: str | None = None
    grade_id: str | None = None
    published_at: str | None = None
    feedback_text: str | None = None
    total_score: float | None = None
    scores: list[RubricScoreResponse] = Field(default_factory=list)
