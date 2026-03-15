"""LMS domain models — Courses, assignments, submissions, grades, content, activities.

Reference: Pack C4 (Data Model — LMS section), Sprint 1 story S-016.
Migration group: G3-LMS (depends on G1-IAM, G2-ERP).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class AssessmentResultStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    GRADED = "graded"
    PUBLISHED = "published"


class ContentItemStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentProgressStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActivitySessionStatus(str, enum.Enum):
    STARTED = "started"
    COMPLETED = "completed"
    EXPIRED = "expired"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Course(TimestampMixin, Base):
    """Course — teacher-created course within a class."""

    __tablename__ = "courses"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=CourseStatus.DRAFT.value
    )

    # Relationships
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_courses_school_class", "school_id", "class_id"),
    )


class Assignment(TimestampMixin, Base):
    """Assignment — teacher-created work for students in a course."""

    __tablename__ = "assignments"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="assignments")
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_points >= 0", name="ck_assignments_total_points"),
        Index("idx_assignments_course_due", "course_id", "due_at"),
    )


class Submission(TimestampMixin, Base):
    """Student submission for an assignment.

    INV-LMS-SUBMISSION: only one active (draft/submitted) submission per student per assignment.
    """

    __tablename__ = "submissions"

    assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SubmissionStatus.DRAFT.value
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    assignment: Mapped["Assignment"] = relationship(back_populates="submissions")
    files: Mapped[list["SubmissionFile"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan"
    )
    grade: Mapped["Grade | None"] = relationship(
        back_populates="submission", uselist=False
    )

    __table_args__ = (
        # INV-LMS-SUBMISSION: one active submission per student per assignment
        Index(
            "uq_submissions_assignment_student_active",
            "assignment_id",
            "student_id",
            unique=True,
            postgresql_where="status IN ('draft', 'submitted')",
        ),
    )


class SubmissionFile(TimestampMixin, Base):
    """File attached to a submission."""

    __tablename__ = "submission_files"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="files")


class Grade(TimestampMixin, Base):
    """Grade given by a teacher for a submission."""

    __tablename__ = "grades"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="grade")

    __table_args__ = (
        Index("idx_grades_submission_published", "submission_id", "published_at"),
    )


class Assessment(TimestampMixin, Base):
    """Formal assessment (exam, quiz) for a class."""

    __tablename__ = "assessments"

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    window_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AssessmentStatus.DRAFT.value
    )

    # Relationships
    results: Mapped[list["AssessmentResult"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_points >= 0", name="ck_assessments_total_points"),
        Index("idx_assessments_class_status", "class_id", "status"),
    )


class AssessmentResult(TimestampMixin, Base):
    """Student result for an assessment. Unique per (assessment, student)."""

    __tablename__ = "assessment_results"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AssessmentResultStatus.SUBMITTED.value
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(back_populates="results")

    __table_args__ = (
        UniqueConstraint(
            "assessment_id", "student_id",
            name="uq_assessment_results_assessment_student",
        ),
    )


class ContentItem(TimestampMixin, Base):
    """Educational content item (video, document, interactive).

    school_id nullable for shared/platform-wide content.
    """

    __tablename__ = "content_items"

    school_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ContentItemStatus.DRAFT.value
    )

    # Relationships
    assets: Mapped[list["ContentItemAsset"]] = relationship(
        back_populates="content_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "idx_content_items_type_level_lang",
            "content_type",
            "level_band",
            "language",
        ),
    )


class ContentItemAsset(TimestampMixin, Base):
    """File/media asset attached to a content item."""

    __tablename__ = "content_item_assets"

    content_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    # Relationships
    content_item: Mapped["ContentItem"] = relationship(back_populates="assets")


class ContentProgress(TimestampMixin, Base):
    """Student progress tracking for a content item. Unique per (student, item)."""

    __tablename__ = "content_progress"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ContentProgressStatus.NOT_STARTED.value
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "content_item_id",
            name="uq_content_progress_student_item",
        ),
    )


class Activity(TimestampMixin, Base):
    """Pedagogical activity (quiz, exercise, game).

    school_id nullable for shared/platform-wide activities.
    """

    __tablename__ = "activities"

    school_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    pedagogical_objective: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sessions: Mapped[list["ActivitySession"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_activities_school_type", "school_id", "type"),
    )


class ActivitySession(TimestampMixin, Base):
    """Student session for an activity — tracks attempts and scores."""

    __tablename__ = "activity_sessions"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ActivitySessionStatus.STARTED.value
    )
    score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Relationships
    activity: Mapped["Activity"] = relationship(back_populates="sessions")

    __table_args__ = (
        Index("idx_activity_sessions_student_activity", "student_id", "activity_id"),
    )
