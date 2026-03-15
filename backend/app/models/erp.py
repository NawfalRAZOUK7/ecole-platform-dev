"""ERP domain models — Academic years, periods, classes, enrollments, attendance.

Reference: Pack C4 (Data Model — ERP section), Sprint 1 story S-015.
Migration group: G2-ERP (depends on G1-IAM for user FKs).
"""

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PeriodStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    TRANSFERRED = "transferred"
    DROPPED = "dropped"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    EXCUSED = "excused"
    LATE = "late"


class JustificationStatus(str, enum.Enum):
    PENDING = "pending"
    JUSTIFIED = "justified"
    REJECTED = "rejected"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AcademicYear(TimestampMixin, Base):
    """Academic year — school calendar boundaries.

    INV-ERP-DATE: periods must be contained within the academic year dates.
    Non-overlapping within a school is enforced at application level.
    """

    __tablename__ = "academic_years"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    periods: Mapped[list["Period"]] = relationship(
        back_populates="academic_year", cascade="all, delete-orphan"
    )
    classes: Mapped[list["Class"]] = relationship(
        back_populates="academic_year", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("date_end > date_start", name="ck_academic_years_dates"),
        Index("idx_academic_years_school", "school_id"),
    )


class Period(TimestampMixin, Base):
    """Period (semester/trimester) within an academic year.

    INV-ERP-DATE: period dates must be contained within academic year dates.
    """

    __tablename__ = "periods"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PeriodStatus.ACTIVE.value
    )
    date_start: Mapped[date] = mapped_column(Date, nullable=False)
    date_end: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="periods")

    __table_args__ = (
        CheckConstraint("date_end > date_start", name="ck_periods_dates"),
        Index("idx_periods_school_year", "school_id", "academic_year_id"),
    )


class Class(TimestampMixin, Base):
    """School class (e.g., 3eme A, 6eme B).

    Unique per (code, school, academic year).
    """

    __tablename__ = "classes"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="classes")
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "code", "school_id", "academic_year_id",
            name="uq_classes_code_school_year",
        ),
    )


class Enrollment(TimestampMixin, Base):
    """Student enrollment in a class for a period.

    INV-ERP-CLASS-ACTIVE: only one active enrollment per student per period.
    """

    __tablename__ = "enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=EnrollmentStatus.ACTIVE.value
    )

    # Relationships
    class_: Mapped["Class"] = relationship(back_populates="enrollments")

    __table_args__ = (
        # uq_enrollments_school_student_period_active — one active enrollment per student per period
        Index(
            "uq_enrollments_school_student_period_active",
            "school_id",
            "student_id",
            "period_id",
            unique=True,
            postgresql_where="status = 'active'",
        ),
    )


class TeacherAssignment(TimestampMixin, Base):
    """Teacher assignment to a class for a period."""

    __tablename__ = "teacher_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)

    __table_args__ = (
        # idx_teacher_school_class_period
        Index(
            "idx_teacher_school_class_period",
            "school_id",
            "teacher_id",
            "class_id",
            "period_id",
        ),
    )


class AttendanceSession(TimestampMixin, Base):
    """Attendance session — one per class/date/slot.

    Created by the teacher when taking attendance.
    """

    __tablename__ = "attendance_sessions"

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    records: Mapped[list["AttendanceRecord"]] = relationship(
        back_populates="attendance_session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # One session per class/date/slot
        UniqueConstraint(
            "class_id", "session_date", "slot",
            name="uq_attendance_sessions_class_date_slot",
        ),
    )


class AttendanceRecord(TimestampMixin, Base):
    """Individual student attendance record within a session."""

    __tablename__ = "attendance_records"

    attendance_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    absence_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    attendance_session: Mapped["AttendanceSession"] = relationship(
        back_populates="records"
    )
    justification: Mapped["AbsenceJustification | None"] = relationship(
        back_populates="attendance_record", uselist=False
    )

    __table_args__ = (
        # idx_attendance_school_student_date — for student attendance queries
        Index(
            "idx_attendance_records_school_student",
            "school_id",
            "student_id",
        ),
        # One record per student per session
        UniqueConstraint(
            "attendance_session_id", "student_id",
            name="uq_attendance_records_session_student",
        ),
    )


class AbsenceJustification(TimestampMixin, Base):
    """Parent-submitted justification for a student absence."""

    __tablename__ = "absence_justifications"

    attendance_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attendance_records.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JustificationStatus.PENDING.value
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    attendance_record: Mapped["AttendanceRecord"] = relationship(
        back_populates="justification"
    )
    reviews: Mapped[list["JustificationReview"]] = relationship(
        back_populates="justification", cascade="all, delete-orphan"
    )


class JustificationReview(TimestampMixin, Base):
    """Teacher/admin review decision on a justification."""

    __tablename__ = "justification_reviews"

    justification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("absence_justifications.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    justification: Mapped["AbsenceJustification"] = relationship(
        back_populates="reviews"
    )
