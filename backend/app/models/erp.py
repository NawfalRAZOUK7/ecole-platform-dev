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

    G49: optional program_id captures the academic program (filière) the student
    is enrolled under for this period. Nullable so historical enrollment rows
    backfill cleanly. The historical record of *changes* lives in
    ``program_assignment_events`` (append-only).
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
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"), nullable=True
    )
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_versions.id", ondelete="RESTRICT"), nullable=True
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
    program: Mapped["Program | None"] = relationship(
        "Program", foreign_keys=[program_id], lazy="raise_on_sql"
    )

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
        Index(
            "idx_enrollments_school_student_program",
            "school_id",
            "student_id",
            "program_id",
        ),
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
    attachment_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

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
            "'max_consecutive_classes',"
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


# ---------------------------------------------------------------------------
# Academic Program Management & Student Academic History (G49)
# ---------------------------------------------------------------------------


class ProgramAssignmentReason(str, enum.Enum):
    """Reason codes for ``ProgramAssignmentEvent``.

    Modeled as an application-level enum (string column) rather than a
    PostgreSQL enum type so the catalog can be extended without a migration.
    """

    INITIAL = "INITIAL"
    TRANSFER = "TRANSFER"
    PROMOTION = "PROMOTION"
    CORRECTION = "CORRECTION"
    READMISSION = "READMISSION"


class Program(TimestampMixin, SchoolScopedMixin, Base):
    """Academic program / filière (e.g., 'Sciences Maths', 'Lettres Modernes').

    School-scoped catalog of tracks a student can be enrolled under for a
    given period. Soft-disable via ``is_active = false``; never hard-delete
    (FKs from ``enrollments`` and ``program_assignment_events`` use RESTRICT
    to preserve historical truth).

    Lightweight versioning shim:
        - ``version_label`` and ``effective_from`` let admins record
          curriculum revisions without a full ProgramVersion table.
        - When real curriculum drift becomes meaningful, promote into a
          dedicated ``program_versions`` table; the API contract already
          carries program code + name, so consumers won't break.
    """

    __tablename__ = "programs"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    version_label: Mapped[str] = mapped_column(
        String(20), nullable=False, default="1.0"
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_programs_school_code"),
        Index("idx_programs_school_active", "school_id", "is_active"),
        Index("idx_programs_school_level", "school_id", "level"),
    )

    @validates("code")
    def validate_code(self, key: str, value: str) -> str:
        cleaned = value.strip().upper().replace(" ", "-")
        if not cleaned:
            raise ValueError("Program code is required")
        return cleaned

    @validates("name")
    def validate_name(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Program name is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<Program id={_short_id(self.id)} code={self.code} "
            f"version={self.version_label}>"
        )


class ProgramVersion(TimestampMixin, SchoolScopedMixin, Base):
    """A specific curriculum version of a Program (G50a / Phase 3.1).

    Promotion of the lightweight ``programs.version_label`` shim into a
    proper entity. Each ``Program`` has 1..N versions; an Enrollment can
    optionally pin to a specific version via ``Enrollment.program_version_id``.
    Append-only-ish: versions are soft-disabled via ``is_active = false`` and
    their ``retired_at`` date can be set; we never hard-delete because
    enrollments and assignment-event rows reference them with RESTRICT.
    """

    __tablename__ = "program_versions"

    program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    retired_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "program_id",
            "version_label",
            name="uq_program_versions_program_label",
        ),
        Index(
            "idx_program_versions_school_program",
            "school_id",
            "program_id",
        ),
        Index(
            "idx_program_versions_program_active",
            "program_id",
            "is_active",
        ),
    )

    @validates("version_label")
    def validate_version_label(self, key: str, value: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise ValueError("ProgramVersion version_label is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<ProgramVersion id={_short_id(self.id)} "
            f"program={_short_id(self.program_id)} label={self.version_label}>"
        )


class ProgramAssignmentEvent(SchoolScopedMixin, Base):
    """Append-only audit log of student program changes (G49).

    Every program change for a student writes one row here, in the same
    transaction as the underlying enrollment write. Rows are NEVER updated
    or deleted — a database trigger (created in the G49 migration) refuses
    UPDATE / DELETE at the SQL level as defence-in-depth.

    Use cases:
        - Reconstruct *why* a student switched programs without inferring
          from enrollment timestamps.
        - Distinguish an INITIAL assignment from a mid-year TRANSFER from a
          year-rollover PROMOTION.
        - Power the ``GET /students/{id}/program-history`` endpoint.

    Note: this model intentionally has no ``updated_at`` and no
    ``TimestampMixin`` — the row is written once and never modified.
    """

    __tablename__ = "program_assignment_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("periods.id", ondelete="SET NULL"), nullable=True
    )
    from_program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"), nullable=True
    )
    to_program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"), nullable=False
    )
    from_program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_versions.id", ondelete="RESTRICT"), nullable=True
    )
    to_program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("program_versions.id", ondelete="RESTRICT"), nullable=True
    )
    from_enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True
    )
    to_enrollment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("enrollments.id", ondelete="SET NULL"), nullable=True
    )
    reason_code: Mapped[str] = mapped_column(String(30), nullable=False)
    reason_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "reason_code IN ("
            "'INITIAL', 'TRANSFER', 'PROMOTION', 'CORRECTION', 'READMISSION'"
            ")",
            name="ck_prog_assignment_events_reason_code",
        ),
        CheckConstraint(
            "from_program_id IS DISTINCT FROM to_program_id",
            name="ck_prog_assignment_events_changed",
        ),
        Index(
            "idx_prog_events_school_student_occurred",
            "school_id",
            "student_id",
            "occurred_at",
        ),
        Index(
            "idx_prog_events_school_year",
            "school_id",
            "academic_year_id",
        ),
        Index("idx_prog_events_to_program", "to_program_id"),
    )

    @validates("reason_code")
    def validate_reason_code(self, key: str, value: str) -> str:
        allowed = {r.value for r in ProgramAssignmentReason}
        cleaned = (value or "").strip().upper()
        if cleaned not in allowed:
            raise ValueError(
                "ProgramAssignmentEvent.reason_code must be one of: "
                + ", ".join(sorted(allowed))
            )
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<ProgramAssignmentEvent id={_short_id(self.id)} "
            f"student={_short_id(self.student_id)} reason={self.reason_code}>"
        )


# ---------------------------------------------------------------------------
# Program equivalences (Phase 3.2 / G50b)
# ---------------------------------------------------------------------------
class ProgramEquivalenceKind(str, enum.Enum):
    """Kinds of inter-program equivalence; mirrored in the
    ``ck_program_equivalences_kind`` CHECK constraint."""

    EQUIVALENT = "EQUIVALENT"
    SUPERSEDES = "SUPERSEDES"
    PARTIAL = "PARTIAL"


class ProgramEquivalence(TimestampMixin, SchoolScopedMixin, Base):
    """Declared equivalence between two programs.

    Directional (``from`` → ``to``). Not transitive at write time — the
    transcript service computes reachability if it needs to chain.
    """

    __tablename__ = "program_equivalences"

    from_program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    to_program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    ratified_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    ratified_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "from_program_id",
            "to_program_id",
            name="uq_program_equivalences_school_pair",
        ),
        CheckConstraint(
            "kind IN ('EQUIVALENT', 'SUPERSEDES', 'PARTIAL')",
            name="ck_program_equivalences_kind",
        ),
        CheckConstraint(
            "from_program_id <> to_program_id",
            name="ck_program_equivalences_distinct_programs",
        ),
        Index(
            "idx_program_equivalences_school_from",
            "school_id",
            "from_program_id",
        ),
        Index(
            "idx_program_equivalences_school_to",
            "school_id",
            "to_program_id",
        ),
    )

    @validates("kind")
    def validate_kind(self, key: str, value: str) -> str:
        allowed = {k.value for k in ProgramEquivalenceKind}
        cleaned = (value or "").strip().upper()
        if cleaned not in allowed:
            raise ValueError(
                "ProgramEquivalence.kind must be one of: " + ", ".join(sorted(allowed))
            )
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<ProgramEquivalence id={_short_id(self.id)} "
            f"{_short_id(self.from_program_id)}→{_short_id(self.to_program_id)} "
            f"kind={self.kind}>"
        )


# ---------------------------------------------------------------------------
# Academic snapshots (Phase 3.3 / G50c)
# ---------------------------------------------------------------------------
class AcademicSnapshotKind(str, enum.Enum):
    YEAR_END = "YEAR_END"
    MID_YEAR = "MID_YEAR"
    MANUAL = "MANUAL"


class AcademicSnapshot(SchoolScopedMixin, Base):
    """Frozen JSONB document for a (student, academic_year).

    Append-only by service convention. We don't install a DB trigger
    because admins are allowed to delete and re-take snapshots when a
    snapshot was taken with bad inputs (e.g. before all grades were
    finalized). The service layer logs deletions to audit_logs.
    """

    __tablename__ = "academic_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_kind: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    taken_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "snapshot_kind IN ('YEAR_END', 'MID_YEAR', 'MANUAL')",
            name="ck_academic_snapshots_kind",
        ),
        Index(
            "idx_academic_snapshots_student_year",
            "school_id",
            "student_id",
            "academic_year_id",
        ),
        Index(
            "idx_academic_snapshots_taken_at",
            "school_id",
            "taken_at",
        ),
    )

    @validates("snapshot_kind")
    def validate_kind(self, key: str, value: str) -> str:
        allowed = {k.value for k in AcademicSnapshotKind}
        cleaned = (value or "").strip().upper()
        if cleaned not in allowed:
            raise ValueError(
                "AcademicSnapshot.snapshot_kind must be one of: "
                + ", ".join(sorted(allowed))
            )
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<AcademicSnapshot id={_short_id(self.id)} "
            f"student={_short_id(self.student_id)} "
            f"year={_short_id(self.academic_year_id)} kind={self.snapshot_kind}>"
        )


# ---------------------------------------------------------------------------
# Eligibility rules (Phase 3.4 / G50d)
# ---------------------------------------------------------------------------
class EligibilityRuleKind(str, enum.Enum):
    PROMOTION = "PROMOTION"
    ADMISSION = "ADMISSION"
    TRANSFER = "TRANSFER"


class EligibilityRule(TimestampMixin, SchoolScopedMixin, Base):
    """Declarative rule: 'student must satisfy condition X to do action Y on program Z'.

    Service-side evaluator dispatches on ``condition_type`` and reads
    ``condition_params`` (JSONB). Built-ins are documented in the service.
    """

    __tablename__ = "eligibility_rules"

    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    target_program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"), nullable=False
    )
    condition_type: Mapped[str] = mapped_column(String(40), nullable=False)
    condition_params: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_key: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        CheckConstraint(
            "kind IN ('PROMOTION', 'ADMISSION', 'TRANSFER')",
            name="ck_eligibility_rules_kind",
        ),
        Index(
            "idx_eligibility_rules_school_kind_target",
            "school_id",
            "kind",
            "target_program_id",
        ),
        Index(
            "idx_eligibility_rules_active",
            "school_id",
            "is_active",
        ),
    )

    @validates("kind")
    def validate_kind(self, key: str, value: str) -> str:
        allowed = {k.value for k in EligibilityRuleKind}
        cleaned = (value or "").strip().upper()
        if cleaned not in allowed:
            raise ValueError(
                "EligibilityRule.kind must be one of: " + ", ".join(sorted(allowed))
            )
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<EligibilityRule id={_short_id(self.id)} kind={self.kind} "
            f"target={_short_id(self.target_program_id)} "
            f"condition={self.condition_type}>"
        )
