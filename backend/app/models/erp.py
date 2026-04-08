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
from sqlalchemy.dialects.postgresql import ENUM as PgEnum, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


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


class TimetableJobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    APPLIED = "applied"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AcademicYear(TimestampMixin, SchoolScopedMixin, Base):
    """Academic year — school calendar boundaries.

    INV-ERP-DATE: periods must be contained within the academic year dates.
    Non-overlapping within a school is enforced at application level.
    """

    __tablename__ = "academic_years"

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

    def __repr__(self) -> str:
        return f"<AcademicYear id={_short_id(self.id)} label={self.label}>"


class Period(TimestampMixin, SchoolScopedMixin, Base):
    """Period (semester/trimester) within an academic year.

    INV-ERP-DATE: period dates must be contained within academic year dates.
    """

    __tablename__ = "periods"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
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
        Index("idx_periods_academic_year_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Period id={_short_id(self.id)} label={self.label} status={self.status}>"
        )


class Class(TimestampMixin, SchoolScopedMixin, Base):
    """School class (e.g., 3eme A, 6eme B).

    Unique per (code, school, academic year).
    """

    __tablename__ = "classes"

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
        Index("idx_classes_academic_year", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return f"<Class id={_short_id(self.id)} name={self.name} code={self.code}>"


class Enrollment(TimestampMixin, SchoolScopedMixin, Base):
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
    status: Mapped[str] = mapped_column(
        PgEnum(
            EnrollmentStatus,
            name="enrollment_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=EnrollmentStatus.ACTIVE.value,
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
        Index("idx_enrollments_school_id", "school_id"),
        Index("idx_enrollments_class", "class_id"),
        Index("idx_enrollments_student_id", "student_id"),
        Index("idx_enrollments_period_id", "period_id"),
    )

    @property
    def is_active(self) -> bool:
        return self.status == EnrollmentStatus.ACTIVE.value

    @validates("status")
    def validate_status(self, key: str, value: str) -> str:
        allowed = {status.value for status in EnrollmentStatus}
        if value not in allowed:
            raise ValueError(
                f"Enrollment status must be one of: {', '.join(sorted(allowed))}"
            )
        return value

    def __repr__(self) -> str:
        return (
            f"<Enrollment id={_short_id(self.id)} student_id={_short_id(self.student_id)} "
            f"status={self.status}>"
        )


class TeacherAssignment(TimestampMixin, SchoolScopedMixin, Base):
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
    __table_args__ = (
        # idx_teacher_school_class_period
        Index(
            "idx_teacher_school_class_period",
            "school_id",
            "teacher_id",
            "class_id",
            "period_id",
        ),
        Index("idx_teacher_assignments_teacher_id", "teacher_id"),
        Index("idx_teacher_assignments_class_id", "class_id"),
        Index("idx_teacher_assignments_period_id", "period_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TeacherAssignment id={_short_id(self.id)} "
            f"teacher_id={_short_id(self.teacher_id)} class_id={_short_id(self.class_id)}>"
        )


class AttendanceSession(TimestampMixin, SchoolScopedMixin, Base):
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
        Index("idx_attendance_sessions_class", "class_id"),
        Index("idx_attendance_sessions_period", "period_id"),
        Index("idx_attendance_sessions_teacher", "teacher_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AttendanceSession id={_short_id(self.id)} "
            f"class_id={_short_id(self.class_id)} date={self.session_date}>"
        )


class AttendanceRecord(TimestampMixin, SchoolScopedMixin, Base):
    """Individual student attendance record within a session."""

    __tablename__ = "attendance_records"

    attendance_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("attendance_sessions.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            AttendanceStatus,
            name="attendance_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
    )
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
        Index("idx_attendance_records_student_id", "student_id"),
        # One record per student per session
        UniqueConstraint(
            "attendance_session_id",
            "student_id",
            name="uq_attendance_records_session_student",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AttendanceRecord id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} status={self.status}>"
        )


class AbsenceJustification(TimestampMixin, SchoolScopedMixin, Base):
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

    __table_args__ = (
        Index("idx_absence_justifications_attendance_record", "attendance_record_id"),
        Index("idx_absence_justifications_parent", "parent_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<AbsenceJustification id={_short_id(self.id)} "
            f"record_id={_short_id(self.attendance_record_id)} status={self.status}>"
        )


class JustificationReview(TimestampMixin, SchoolScopedMixin, Base):
    """Teacher/admin review decision on a justification."""

    __tablename__ = "justification_reviews"

    justification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("absence_justifications.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)

    # Relationships
    justification: Mapped["AbsenceJustification"] = relationship(
        back_populates="reviews"
    )

    __table_args__ = (
        Index("idx_justification_reviews_justification", "justification_id"),
        Index("idx_justification_reviews_reviewer", "reviewer_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<JustificationReview id={_short_id(self.id)} "
            f"justification_id={_short_id(self.justification_id)}>"
        )


class AttendanceAlert(TimestampMixin, SchoolScopedMixin, Base):
    """Threshold-based attendance alert for a student within a period."""

    __tablename__ = "attendance_alerts"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
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

    @property
    def is_resolved(self) -> bool:
        return getattr(self, "resolved_at", None) is not None

    def __repr__(self) -> str:
        return (
            f"<AttendanceAlert id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} type={self.threshold_exceeded}>"
        )


# ---------------------------------------------------------------------------
# Timetable (Phase 11A / ENH-C3)
# ---------------------------------------------------------------------------


class TimetableConstraint(TimestampMixin, SchoolScopedMixin, Base):
    """School timetable generation constraint."""

    __tablename__ = "timetable_constraints"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    constraint_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        CheckConstraint(
            "constraint_type IN ("
            "'teacher_unavailable',"
            "'room_capacity',"
            "'max_hours_per_day',"
            "'subject_hours_per_week',"
            "'no_consecutive_same_subject'"
            ")",
            name="ck_timetable_constraints_type",
        ),
        Index("idx_tc_school_year", "school_id", "academic_year_id"),
        Index("idx_timetable_constraints_academic_year_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TimetableConstraint id={_short_id(self.id)} "
            f"type={self.constraint_type}>"
        )


class TimetableGenerationJob(TimestampMixin, SchoolScopedMixin, Base):
    """Stored result of a timetable generation run."""

    __tablename__ = "timetable_generation_jobs"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            TimetableJobStatus,
            name="timetable_job_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=TimetableJobStatus.PENDING.value,
    )
    constraints_snapshot: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_slot_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conflicts_found: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'applied')",
            name="ck_timetable_generation_jobs_status",
        ),
        Index("idx_tgj_school_year", "school_id", "academic_year_id"),
        Index("idx_timetable_generation_jobs_academic_year_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return f"<TimetableGenerationJob id={_short_id(self.id)} status={self.status}>"


# ---------------------------------------------------------------------------
# Timetable (Phase 11A)
# ---------------------------------------------------------------------------


class TimetableSlot(TimestampMixin, SchoolScopedMixin, Base):
    """Recurring timetable slot — one class period per week.

    INV-ERP-TIMETABLE-TIME: end_time > start_time
    INV-ERP-TIMETABLE-DAY: day_of_week in 0..6 (Mon=0, Sun=6)
    Unique constraint: (class_id, day_of_week, start_time, academic_year_id)
    Overlap validation enforced at application level.
    """

    __tablename__ = "timetable_slots"

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
        Index("idx_timetable_slots_academic_year_id", "academic_year_id"),
        Index("idx_timetable_slots_teacher", "teacher_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TimetableSlot id={_short_id(self.id)} day={self.day_of_week} "
            f"start_time={self.start_time}>"
        )


class TimetableException(TimestampMixin, SchoolScopedMixin, Base):
    """Exception to a recurring timetable slot (cancel, substitute, room change).

    One exception per slot per date.
    """

    __tablename__ = "timetable_exceptions"

    timetable_slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("timetable_slots.id", ondelete="CASCADE"), nullable=False
    )
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
        Index("idx_timetable_exceptions_timetable_slot", "timetable_slot_id"),
        Index("idx_timetable_exceptions_substitute_teacher", "substitute_teacher_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<TimetableException id={_short_id(self.id)} "
            f"date={self.exception_date}>"
        )
