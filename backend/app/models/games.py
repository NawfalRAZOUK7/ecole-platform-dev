"""Lightweight mobile game configuration models."""

from __future__ import annotations

import enum
import uuid
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base, TimestampMixin


class GameType(str, enum.Enum):
    MEMORY_MATCH = "memory_match"
    SORTING = "sorting"
    VOCABULARY_CARDS = "vocabulary_cards"


class GameDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class GameConfig(TimestampMixin, Base):
    """Stored configuration for a mobile game session."""

    __tablename__ = "game_configs"

    game_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    title_ar: Mapped[str | None] = mapped_column(String(300), nullable=True)
    title_fr: Mapped[str | None] = mapped_column(String(300), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False, default="easy")
    target_age_min: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    target_age_max: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    reward_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    reward_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        Index("idx_game_configs_type", "game_type"),
        Index(
            "idx_game_configs_active",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    @validates("game_type")
    def validate_game_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {item.value for item in GameType}:
            raise ValueError("Unsupported game type")
        return cleaned

    @validates("difficulty")
    def validate_difficulty(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {item.value for item in GameDifficulty}:
            raise ValueError("Unsupported game difficulty")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<GameConfig id={str(self.id)[:8]} game_type={self.game_type} "
            f"difficulty={self.difficulty}>"
        )
