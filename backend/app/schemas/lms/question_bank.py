"""Question bank schemas for reusable quiz question storage and generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.taxonomy import (
    normalize_difficulty,
    normalize_level_band,
)


class QuestionBankQuestionData(BaseModel):
    question_type: str = Field(
        ..., pattern="^(MCQ|TRUE_FALSE|FILL_IN|DRAG_DROP|MATCHING)$"
    )
    question_text: str = Field(..., min_length=1)
    question_media_path: str | None = None
    options: Any | None = None
    correct_answer: Any = Field(...)
    points: int = Field(default=1, ge=0)
    explanation: str | None = None


class QuestionBankCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=50)
    subject_other: str | None = Field(default=None, max_length=120)  # when subject == "other"
    level_band: str | None = Field(default=None, max_length=50)
    difficulty: str = Field(..., max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)
    question_data: QuestionBankQuestionData

    @field_validator("difficulty", mode="before")
    @classmethod
    def _normalize_difficulty(cls, v: str) -> str | None:
        return normalize_difficulty(v)

    # subject = matière (official OR a school custom one) → free String; the
    # service layer validates it's official or a registered custom matière.
    @field_validator("level_band", mode="before")
    @classmethod
    def _normalize_level_band(cls, v: str | None) -> str | None:
        return normalize_level_band(v)


class QuestionBankItemResponse(BaseModel):
    id: str
    school_id: str
    teacher_id: str
    subject: str
    level_band: str | None = None
    difficulty: str
    question_type: str
    question_data: dict
    tags: list[str] = Field(default_factory=list)
    usage_count: int
    is_archived: bool


class GenerateQuizFromBankRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=50)
    level_band: str | None = Field(default=None, max_length=50)
    distribution: dict[str, int] = Field(default_factory=dict)

    # subject = matière (official OR a school custom one) → free String.
    @field_validator("level_band", mode="before")
    @classmethod
    def _normalize_level_band(cls, v: str | None) -> str | None:
        return normalize_level_band(v)
    title: str | None = Field(default=None, min_length=1, max_length=300)
    description: str | None = None
    shuffle_questions: bool = False
    time_limit_minutes: int | None = Field(default=None, ge=0)
    max_attempts: int = Field(default=1, ge=1)


class GenerateQuizFromContentRequest(BaseModel):
    """Teacher-chosen options for generating a draft quiz from a PDF+audio item.

    The teacher decides per content: which question types, how many, and which
    sources to merge — deterministic ``template`` and/or the ``ai`` provider.
    """

    question_types: list[str] = Field(
        default_factory=lambda: ["MCQ", "TRUE_FALSE", "FILL_IN"]
    )
    count: int = Field(default=5, ge=1, le=30)
    sources: list[str] = Field(default_factory=lambda: ["template"])  # ai | template
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None
    difficulty: str | None = Field(default=None, max_length=20)
    time_limit_minutes: int | None = Field(default=None, ge=0)
    max_attempts: int = Field(default=1, ge=1)
    shuffle_questions: bool = False


class QuestionBankImportResponse(BaseModel):
    quiz_id: str
    imported_count: int


class QuestionBankStatsItemResponse(BaseModel):
    subject: str
    difficulty: str
    question_count: int
    total_usage: int
