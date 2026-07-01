"""Difficulty adaptation audit log."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin
from app.models.taxonomy import ContentSubject


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class DifficultyAdaptation(TimestampMixin, Base):
    """Records every rule-based difficulty change for analytics and audit."""

    __tablename__ = "difficulty_adaptations"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(
        # Native enum incl. OTHER; school-specific matière = 'other' + free text.
        PgEnum(
            ContentSubject,
            name="content_subject_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
    previous_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    new_difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (Index("idx_diff_adapt_student_subject", "student_id", "subject"),)
