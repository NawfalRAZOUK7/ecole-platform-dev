"""AI domain models — Writing Attempts, AI Preferences.

Reference: S-143 (Writing assistance), S-144 (AI opt-out), Pack G3 — AI Governance
Migration group: G7-AI (depends on G1-IAM for users FK).
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class WritingAttempt(TimestampMixin, Base):
    """Student writing assistance attempt — stores request + AI response.

    Reference: S-143, PROMPT-G3-002
    """

    __tablename__ = "writing_attempts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    subject: Mapped[str | None] = mapped_column(String(200), nullable=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    input_word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed"
    )
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    hints: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prompt_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    warnings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_writing_attempts_student", "student_id"),
        Index("idx_writing_attempts_school", "school_id"),
    )


class AIPreference(TimestampMixin, Base):
    """AI personalization opt-out preference.

    Reference: S-144, DEC-009, G3.3 — Consent & Opt-out Contract
    - user_id: the user setting the preference (typically parent)
    - target_user_id: the user affected (typically child, or self)
    - opt_out: True = AI personalization disabled for target
    """

    __tablename__ = "ai_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    opt_out: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        # One preference per (user, target) pair
        UniqueConstraint(
            "user_id", "target_user_id",
            name="uq_ai_preferences_user_target",
        ),
        Index("idx_ai_preferences_target", "target_user_id"),
        Index("idx_ai_preferences_school", "school_id"),
    )
