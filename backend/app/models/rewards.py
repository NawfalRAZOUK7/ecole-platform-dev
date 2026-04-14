"""Student rewards models for the kid-facing rewards system."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, TimestampMixin

ALLOWED_SOURCE_TYPES = {"content", "quiz", "game", "coloring", "login"}


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


class StudentReward(TimestampMixin, Base):
    """Aggregate rewards state for a single student."""

    __tablename__ = "student_rewards"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    streak_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
    )

    def __repr__(self) -> str:
        return (
            f"<StudentReward id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} stars={self.stars} level={self.level}>"
        )


class RewardEvent(Base):
    """Immutable record of an awarded reward event."""

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
        if not cleaned:
            raise ValueError("Reward event type is required")
        return cleaned

    @validates("source_type")
    def validate_source_type(self, key: str, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().lower()
        if cleaned not in ALLOWED_SOURCE_TYPES:
            raise ValueError("Unsupported reward source type")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<RewardEvent id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} event_type={self.event_type}>"
        )
