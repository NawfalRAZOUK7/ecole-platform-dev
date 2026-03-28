"""ERP domain models — Academic years, periods, classes, enrollments, attendance, timetable.

Reference: Pack C4 (Data Model — ERP section), Sprint 1 story S-015.
Migration group: G2-ERP (depends on G1-IAM for user FKs).
Phase 11A: Added TimetableSlot, TimetableException models.
"""

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Float,
    Index,
    Integer,
    String,
    Text,
    Time,
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


class ExceptionType(str, enum.Enum):
    """Timetable exception types (Phase 11A)."""

    CANCELED = "CANCELED"
    SUBSTITUTED = "SUBSTITUTED"
    ROOM_CHANGED = "ROOM_CHANGED"


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
            "code",
            "school_id",
            "academic_year_id",
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
            "class_id",
            "session_date",
            "slot",
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
            "attendance_session_id",
            "student_id",
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


class AttendanceAlert(TimestampMixin, Base):
    """Threshold-based attendance alert for a student within a period."""

    __tablename__ = "attendance_alerts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    absence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    absence_rate: Mapped[float] = mapped_column(Float, nullable=False)
    threshold_exceeded: Mapped[str] = mapped_column(String(20), nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "period_id",
            "threshold_exceeded",
            name="uq_aa_student_period_threshold",
        ),
        CheckConstraint(
            "absence_count >= 0",
            name="ck_attendance_alerts_absence_count",
        ),
        CheckConstraint(
            "total_sessions >= 0",
            name="ck_attendance_alerts_total_sessions",
        ),
        CheckConstraint(
            "absence_rate >= 0 AND absence_rate <= 1",
            name="ck_attendance_alerts_absence_rate",
        ),
        CheckConstraint(
            "threshold_exceeded IN ('warning', 'critical')",
            name="ck_attendance_alerts_threshold",
        ),
        Index("idx_attendance_alerts_school", "school_id"),
    )


# ---------------------------------------------------------------------------
# Timetable (Phase 11A)
# ---------------------------------------------------------------------------


class TimetableSlot(TimestampMixin, Base):
    """Recurring timetable slot — one class period per week.

    INV-ERP-TIMETABLE-TIME: end_time > start_time
    INV-ERP-TIMETABLE-DAY: day_of_week in 0..6 (Mon=0, Sun=6)
    Unique constraint: (class_id, day_of_week, start_time, academic_year_id)
    Overlap validation enforced at application level.
    """

    __tablename__ = "timetable_slots"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    exceptions: Mapped[list["TimetableException"]] = relationship(
        back_populates="timetable_slot", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_timetable_slots_times"),
        CheckConstraint(
            "day_of_week >= 0 AND day_of_week <= 6",
            name="ck_timetable_slots_day_of_week",
        ),
        UniqueConstraint(
            "class_id",
            "day_of_week",
            "start_time",
            "academic_year_id",
            name="uq_timetable_slots_class_day_time_year",
        ),
        Index("idx_timetable_slots_school", "school_id"),
        Index("idx_timetable_slots_class_year", "class_id", "academic_year_id"),
        Index("idx_timetable_slots_teacher", "teacher_id"),
    )


class TimetableException(TimestampMixin, Base):
    """Exception to a recurring timetable slot (cancel, substitute, room change).

    One exception per slot per date.
    """

    __tablename__ = "timetable_exceptions"

    timetable_slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("timetable_slots.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    exception_date: Mapped[date] = mapped_column(Date, nullable=False)
    exception_type: Mapped[str] = mapped_column(String(20), nullable=False)
    substitute_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    new_room: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    timetable_slot: Mapped["TimetableSlot"] = relationship(back_populates="exceptions")

    __table_args__ = (
        CheckConstraint(
            "exception_type IN ('CANCELED', 'SUBSTITUTED', 'ROOM_CHANGED')",
            name="ck_timetable_exceptions_type",
        ),
        UniqueConstraint(
            "timetable_slot_id",
            "exception_date",
            name="uq_timetable_exceptions_slot_date",
        ),
        Index("idx_timetable_exceptions_school", "school_id"),
        Index("idx_timetable_exceptions_date", "exception_date"),
    )
