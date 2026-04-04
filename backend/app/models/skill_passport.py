"""Life-skills passport models driven by milestone evaluation rules."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class SkillProgressStatus(str, enum.Enum):
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    UNLOCKED = "unlocked"


class SkillDimension(TimestampMixin, Base):
    """Top-level behavioral skill tracked by the passport engine."""

    __tablename__ = "skill_dimensions"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[str] = mapped_column(String(200), nullable=False)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    milestones: Mapped[list["SkillMilestone"]] = relationship(
        back_populates="dimension",
        cascade="all, delete-orphan",
        order_by="SkillMilestone.level",
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_skill_dimensions_code"),
        CheckConstraint(
            "display_order >= 0",
            name="ck_skill_dimensions_display_order",
        ),
        Index("idx_skill_dimensions_active_order", "is_active", "display_order"),
    )

    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "_")
        if not cleaned:
            raise ValueError("Skill dimension code is required")
        return cleaned

    def __repr__(self) -> str:
        return f"<SkillDimension id={_short_id(self.id)} code={self.code}>"


class SkillMilestone(TimestampMixin, Base):
    """Rule-driven milestone inside a skill dimension."""

    __tablename__ = "skill_milestones"

    dimension_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill_dimensions.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name_fr: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    rule_config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    badge_icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    dimension: Mapped["SkillDimension"] = relationship(back_populates="milestones")
    progress_entries: Mapped[list["SkillProgress"]] = relationship(
        back_populates="milestone",
        cascade="all, delete-orphan",
        order_by="SkillProgress.created_at",
    )

    __table_args__ = (
        UniqueConstraint(
            "dimension_id",
            "code",
            name="uq_skill_milestones_dimension_code",
        ),
        CheckConstraint("level >= 1", name="ck_skill_milestones_level_min"),
        CheckConstraint("level <= 5", name="ck_skill_milestones_level_max"),
        Index("idx_skill_milestones_dimension_level", "dimension_id", "level"),
        Index("idx_skill_milestones_active", "is_active"),
    )

    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        cleaned = value.strip().lower().replace(" ", "_")
        if not cleaned:
            raise ValueError("Skill milestone code is required")
        return cleaned

    def __repr__(self) -> str:
        return f"<SkillMilestone id={_short_id(self.id)} code={self.code} level={self.level}>"


class SkillProgress(TimestampMixin, SchoolScopedMixin, Base):
    """Per-student milestone progression for an academic year."""

    __tablename__ = "skill_progress"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    milestone_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skill_milestones.id", ondelete="CASCADE"),
        nullable=False,
    )
    unlocked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_value: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=0,
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            SkillProgressStatus,
            name="skill_progress_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=SkillProgressStatus.LOCKED.value,
    )
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    student = relationship("User", foreign_keys=[student_id])
    milestone: Mapped["SkillMilestone"] = relationship(back_populates="progress_entries")
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "milestone_id",
            "academic_year_id",
            name="uq_skill_progress_student_milestone_year",
        ),
        CheckConstraint(
            "current_value >= 0",
            name="ck_skill_progress_current_value_min",
        ),
        CheckConstraint(
            "current_value <= 100",
            name="ck_skill_progress_current_value_max",
        ),
        Index(
            "idx_skill_progress_school_student_status",
            "school_id",
            "student_id",
            "status",
        ),
        Index(
            "idx_skill_progress_year_milestone",
            "academic_year_id",
            "milestone_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SkillProgress id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} status={self.status}>"
        )


class SkillPassport(TimestampMixin, SchoolScopedMixin, Base):
    """Generated yearly summary of a student's unlocked life skills."""

    __tablename__ = "skill_passports"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    total_milestones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlocked_milestones: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_score: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )

    student = relationship("User", foreign_keys=[student_id])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_year_id",
            name="uq_skill_passports_student_year",
        ),
        CheckConstraint(
            "total_milestones >= 0",
            name="ck_skill_passports_total_milestones",
        ),
        CheckConstraint(
            "unlocked_milestones >= 0",
            name="ck_skill_passports_unlocked_milestones",
        ),
        CheckConstraint(
            "unlocked_milestones <= total_milestones",
            name="ck_skill_passports_unlocked_lte_total",
        ),
        CheckConstraint(
            "overall_score >= 0",
            name="ck_skill_passports_overall_score_min",
        ),
        CheckConstraint(
            "overall_score <= 100",
            name="ck_skill_passports_overall_score_max",
        ),
        Index(
            "idx_skill_passports_school_student_year",
            "school_id",
            "student_id",
            "academic_year_id",
        ),
    )

    @validates("pdf_url")
    def validate_pdf_url(self, key: str, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

    def __repr__(self) -> str:
        return (
            f"<SkillPassport id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} score={self.overall_score}>"
        )
