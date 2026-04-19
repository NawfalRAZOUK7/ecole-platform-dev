"""Difficulty adaptation audit log."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin


class DifficultyAdaptation(TimestampMixin, Base):
    """Records every rule-based difficulty change for analytics and audit."""

    __tablename__ = "difficulty_adaptations"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    new_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("idx_diff_adapt_student_subject", "student_id", "subject"),
    )
