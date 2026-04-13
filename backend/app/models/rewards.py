"""Student rewards and gamification models."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


class EventType(str, enum.Enum):
    CONTENT_COMPLETED = "content_completed"
    QUIZ_PASSED = "quiz_passed"
    GAME_WON = "game_won"
    COLORING_SAVED = "coloring_saved"
    DAILY_LOGIN = "daily_login"
    STREAK_BONUS = "streak_bonus"


class SourceType(str, enum.Enum):
    CONTENT = "content"
    QUIZ = "quiz"
    GAME = "game"
    COLORING = "coloring"
    SYSTEM = "system"


class CriteriaType(str, enum.Enum):
    STARS_TOTAL = "stars_total"
    STREAK_DAYS = "streak_days"
    CONTENT_COMPLETED = "content_completed"
    QUIZ_SCORE = "quiz_score"
    GAMES_WON = "games_won"
    COLORING_SAVED = "coloring_saved"
    CONTENT_TYPES = "content_types"


class StudentReward(TimestampMixin, Base):
    """Aggregate reward state for one student."""

    __tablename__ = "student_rewards"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_activity_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    badges: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

    student = relationship("User", foreign_keys=[student_id])
    events: Mapped[list["RewardEvent"]] = relationship(
        primaryjoin="StudentReward.student_id == foreign(RewardEvent.student_id)",
        foreign_keys="RewardEvent.student_id",
        back_populates="student_reward",
        order_by="RewardEvent.created_at.desc()",
        viewonly=True,
    )

    __table_args__ = (
        Index("uq_student_rewards_student", "student_id", unique=True),
        CheckConstraint("stars >= 0", name="ck_student_rewards_stars_non_negative"),
        CheckConstraint("xp >= 0", name="ck_student_rewards_xp_non_negative"),
        CheckConstraint("level >= 1", name="ck_student_rewards_level_min"),
        CheckConstraint(
            "streak_days >= 0",
            name="ck_student_rewards_streak_days_non_negative",
        ),
        CheckConstraint(
            "longest_streak >= 0",
            name="ck_student_rewards_longest_streak_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentReward id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} stars={self.stars} level={self.level}>"
        )


class RewardEvent(Base):
    """Immutable reward grant event."""

    __tablename__ = "reward_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    stars_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    student = relationship("User", foreign_keys=[student_id])
    student_reward: Mapped[StudentReward | None] = relationship(
        primaryjoin="foreign(RewardEvent.student_id) == StudentReward.student_id",
        foreign_keys=[student_id],
        back_populates="events",
        viewonly=True,
    )

    __table_args__ = (
        Index("idx_reward_events_student", "student_id"),
        Index("idx_reward_events_created", "created_at"),
        CheckConstraint(
            "stars_earned >= 0",
            name="ck_reward_events_stars_earned_non_negative",
        ),
        CheckConstraint(
            "xp_earned >= 0",
            name="ck_reward_events_xp_earned_non_negative",
        ),
    )

    @validates("event_type")
    def validate_event_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {item.value for item in EventType}:
            raise ValueError("Unsupported reward event type")
        return cleaned

    @validates("source_type")
    def validate_source_type(self, key: str, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().lower()
        if cleaned not in {item.value for item in SourceType}:
            raise ValueError("Unsupported reward source type")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<RewardEvent id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} event_type={self.event_type}>"
        )


class RewardBadge(Base):
    """Badge criteria definition."""

    __tablename__ = "reward_badges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    title_fr: Mapped[str] = mapped_column(String(100), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(100), nullable=False)
    title_en: Mapped[str] = mapped_column(String(100), nullable=False)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ar: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criteria_type: Mapped[str] = mapped_column(String(50), nullable=False)
    criteria_value: Mapped[int] = mapped_column(Integer, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        CheckConstraint(
            "criteria_value >= 0",
            name="ck_reward_badges_criteria_value_non_negative",
        ),
        CheckConstraint(
            "display_order >= 0",
            name="ck_reward_badges_display_order_non_negative",
        ),
        Index("idx_reward_badges_active_order", "is_active", "display_order"),
    )

    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "_")
        if not cleaned:
            raise ValueError("Reward badge code is required")
        return cleaned

    @validates("criteria_type")
    def validate_criteria_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if cleaned not in {item.value for item in CriteriaType}:
            raise ValueError("Unsupported reward badge criteria type")
        return cleaned

    def __repr__(self) -> str:
        return f"<RewardBadge id={_short_id(self.id)} code={self.code}>"
