"""MEN compliance models for curriculum coverage against Moroccan standards."""

from __future__ import annotations

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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


class MenCurriculum(TimestampMixin, Base):
    """Reference MEN curriculum for a level, grade, subject, and version."""

    __tablename__ = "men_curricula"

    level: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    objectives: Mapped[list["MenObjective"]] = relationship(
        back_populates="curriculum",
        cascade="all, delete-orphan",
        order_by="MenObjective.display_order",
    )
    reports: Mapped[list["ComplianceReport"]] = relationship(
        back_populates="curriculum",
        cascade="all, delete-orphan",
        order_by="ComplianceReport.generated_at",
    )

    __table_args__ = (
        UniqueConstraint(
            "level",
            "grade",
            "subject",
            "academic_year",
            "version",
            name="uq_men_curricula_scope",
        ),
        Index(
            "idx_men_curricula_level_grade_subject",
            "level",
            "grade",
            "subject",
        ),
        Index("idx_men_curricula_active_year", "is_active", "academic_year"),
    )

    @validates("level", "grade", "subject", "academic_year", "version")
    def validate_required_text(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"Men curriculum {key} is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<MenCurriculum id={_short_id(self.id)} subject={self.subject} "
            f"grade={self.grade}>"
        )


class MenObjective(TimestampMixin, Base):
    """Atomic MEN objective inside a curriculum reference."""

    __tablename__ = "men_objectives"

    curriculum_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("men_curricula.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title_fr: Mapped[str] = mapped_column(String(500), nullable=False)
    title_ar: Mapped[str] = mapped_column(String(500), nullable=False)
    description_fr: Mapped[str | None] = mapped_column(Text, nullable=True)
    trimester: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hours_recommended: Mapped[float | None] = mapped_column(
        Numeric(6, 2),
        nullable=True,
    )
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)

    curriculum: Mapped["MenCurriculum"] = relationship(back_populates="objectives")
    mappings: Mapped[list["CurriculumMapping"]] = relationship(
        back_populates="objective",
        cascade="all, delete-orphan",
        order_by="CurriculumMapping.mapped_at",
    )

    __table_args__ = (
        UniqueConstraint(
            "curriculum_id", "code", name="uq_men_objectives_curriculum_code"
        ),
        CheckConstraint("trimester >= 1", name="ck_men_objectives_trimester_min"),
        CheckConstraint("trimester <= 3", name="ck_men_objectives_trimester_max"),
        CheckConstraint("unit_number >= 1", name="ck_men_objectives_unit_number"),
        CheckConstraint(
            "hours_recommended IS NULL OR hours_recommended >= 0",
            name="ck_men_objectives_hours_recommended",
        ),
        CheckConstraint("display_order >= 0", name="ck_men_objectives_display_order"),
        Index(
            "idx_men_objectives_curriculum_trimester",
            "curriculum_id",
            "trimester",
        ),
        Index("idx_men_objectives_curriculum_order", "curriculum_id", "display_order"),
        Index("idx_men_objectives_curriculum_id", "curriculum_id"),
    )

    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        cleaned = value.strip().upper().replace(" ", "-")
        if not cleaned:
            raise ValueError("MEN objective code is required")
        return cleaned

    @validates("title_fr", "title_ar")
    def validate_title(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"MEN objective {key} is required")
        return cleaned

    def __repr__(self) -> str:
        return f"<MenObjective id={_short_id(self.id)} code={self.code}>"


class CurriculumMapping(TimestampMixin, SchoolScopedMixin, Base):
    """School-level mapping from local pedagogy artifacts to MEN objectives."""

    __tablename__ = "curriculum_mappings"

    objective_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("men_objectives.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
    )
    content_item_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id", ondelete="SET NULL"),
        nullable=True,
    )
    mapped_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    mapped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    coverage_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    objective: Mapped["MenObjective"] = relationship(back_populates="mappings")
    course = relationship("Course", foreign_keys=[course_id])
    content_item = relationship("ContentItem", foreign_keys=[content_item_id])
    mapper = relationship("User", foreign_keys=[mapped_by])

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "objective_id",
            "course_id",
            name="uq_curriculum_mappings_school_objective_course",
        ),
        CheckConstraint(
            "coverage_percent >= 0",
            name="ck_curriculum_mappings_coverage_percent_min",
        ),
        CheckConstraint(
            "coverage_percent <= 100",
            name="ck_curriculum_mappings_coverage_percent_max",
        ),
        CheckConstraint(
            "course_id IS NOT NULL OR content_item_id IS NOT NULL",
            name="ck_curriculum_mappings_target_present",
        ),
        Index(
            "idx_curriculum_mappings_school_objective",
            "school_id",
            "objective_id",
        ),
        Index("idx_curriculum_mappings_course", "course_id"),
        Index("idx_curriculum_mappings_content_item", "content_item_id"),
        Index("idx_curriculum_mappings_objective_id", "objective_id"),
        Index("idx_curriculum_mappings_course_id", "course_id"),
        Index("idx_curriculum_mappings_content_item_id", "content_item_id"),
        Index("idx_curriculum_mappings_mapped_by", "mapped_by"),
    )

    def __repr__(self) -> str:
        return (
            f"<CurriculumMapping id={_short_id(self.id)} "
            f"objective_id={_short_id(self.objective_id)}>"
        )


class ComplianceReport(TimestampMixin, SchoolScopedMixin, Base):
    """Generated compliance snapshot for a curriculum and academic year."""

    __tablename__ = "compliance_reports"

    curriculum_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("men_curricula.id", ondelete="CASCADE"),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    generated_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_objectives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mapped_objectives: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compliance_percent: Mapped[float] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=0,
    )
    unmapped_objectives: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )

    curriculum: Mapped["MenCurriculum"] = relationship(back_populates="reports")
    generator = relationship("User", foreign_keys=[generated_by])
    academic_year = relationship("AcademicYear", foreign_keys=[academic_year_id])

    __table_args__ = (
        CheckConstraint(
            "total_objectives >= 0",
            name="ck_compliance_reports_total_objectives",
        ),
        CheckConstraint(
            "mapped_objectives >= 0",
            name="ck_compliance_reports_mapped_objectives",
        ),
        CheckConstraint(
            "mapped_objectives <= total_objectives",
            name="ck_compliance_reports_mapped_lte_total",
        ),
        CheckConstraint(
            "compliance_percent >= 0",
            name="ck_compliance_reports_percent_min",
        ),
        CheckConstraint(
            "compliance_percent <= 100",
            name="ck_compliance_reports_percent_max",
        ),
        Index(
            "idx_compliance_reports_school_year_curriculum",
            "school_id",
            "academic_year_id",
            "curriculum_id",
        ),
        Index("idx_compliance_reports_generated_by", "generated_by"),
        Index("idx_compliance_reports_curriculum_id", "curriculum_id"),
        Index("idx_compliance_reports_generated_by_fk", "generated_by"),
        Index("idx_compliance_reports_academic_year_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ComplianceReport id={_short_id(self.id)} "
            f"compliance={self.compliance_percent}>"
        )
