"""LMS domain models — Courses, assignments, submissions, grades, content, activities.

Reference: Pack C4 (Data Model — LMS section), Sprint 1 story S-016.
Migration group: G3-LMS (depends on G1-IAM, G2-ERP).
"""

import enum
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
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

from app.core.database import (
    Base,
    NullableSchoolScopedMixin,
    SchoolScopedMixin,
    TimestampMixin,
)


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


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


class ExerciseType(str, enum.Enum):
    STANDARD = "STANDARD"
    PRINTABLE_PDF = "PRINTABLE_PDF"
    QUIZ = "QUIZ"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class Course(TimestampMixin, SchoolScopedMixin, Base):
    """Course — teacher-created course within a class."""

    __tablename__ = "courses"

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

    __table_args__ = (Index("idx_courses_school_class", "school_id", "class_id"),)

    def __repr__(self) -> str:
        return f"<Course id={_short_id(self.id)} title={self.title} status={self.status}>"


class GradeCategory(TimestampMixin, SchoolScopedMixin, Base):
    """Weighted grade category for a class and period."""

    __tablename__ = "grade_categories"

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="grade_category"
    )

    __table_args__ = (
        Index("idx_grade_categories_class_period", "class_id", "period_id"),
        CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="ck_grade_categories_weight",
        ),
    )

    @validates("weight")
    def validate_weight(self, key: str, value: float) -> float:
        if value <= 0 or value > 1:
            raise ValueError("GradeCategory weight must be between 0 and 1")
        return value

    def __repr__(self) -> str:
        return (
            f"<GradeCategory id={_short_id(self.id)} name={self.name} "
            f"weight={self.weight}>"
        )


class Rubric(TimestampMixin, SchoolScopedMixin, Base):
    """Structured grading rubric owned by a teacher or reused as a template."""

    __tablename__ = "rubrics"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    is_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    criteria: Mapped[list["RubricCriterion"]] = relationship(
        back_populates="rubric",
        cascade="all, delete-orphan",
        order_by="RubricCriterion.position",
    )
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="rubric")

    __table_args__ = (
        CheckConstraint("total_points >= 0", name="ck_rubrics_total_points"),
        Index("idx_rubrics_school_teacher", "school_id", "teacher_id"),
    )

    def __repr__(self) -> str:
        return f"<Rubric id={_short_id(self.id)} title={self.title}>"


class RubricCriterion(TimestampMixin, Base):
    """Weighted criterion within a rubric."""

    __tablename__ = "rubric_criteria"

    rubric_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rubrics.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rubric: Mapped["Rubric"] = relationship(back_populates="criteria")
    levels: Mapped[list["RubricLevel"]] = relationship(
        back_populates="criterion",
        cascade="all, delete-orphan",
        order_by="RubricLevel.position",
    )
    scores: Mapped[list["RubricScore"]] = relationship(
        back_populates="criterion",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint("weight >= 0", name="ck_rubric_criteria_weight"),
        Index("idx_rubric_criteria_rubric", "rubric_id"),
    )

    def __repr__(self) -> str:
        return f"<RubricCriterion id={_short_id(self.id)} title={self.title}>"


class RubricLevel(TimestampMixin, Base):
    """Level option for a rubric criterion."""

    __tablename__ = "rubric_levels"

    criterion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[float] = mapped_column(Float, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    criterion: Mapped["RubricCriterion"] = relationship(back_populates="levels")
    scores: Mapped[list["RubricScore"]] = relationship(back_populates="level")

    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_rubric_levels_points"),
        Index("idx_rubric_levels_criterion", "criterion_id"),
    )

    def __repr__(self) -> str:
        return f"<RubricLevel id={_short_id(self.id)} label={self.label}>"


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
    grace_period_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    late_penalty_per_day: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    max_late_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allow_late: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Phase 9B — exercise type + quiz link
    exercise_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ExerciseType.STANDARD.value
    )
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rubrics.id", ondelete="SET NULL"),
        nullable=True,
    )
    grade_category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("grade_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    quiz_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True
    )
    # Phase 9C — PDF exercise workflow
    exercise_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="assignments")
    rubric: Mapped["Rubric | None"] = relationship(back_populates="assignments")
    grade_category: Mapped["GradeCategory | None"] = relationship(
        back_populates="assignments"
    )
    submissions: Mapped[list["Submission"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("total_points >= 0", name="ck_assignments_total_points"),
        Index("idx_assignments_course_due", "course_id", "due_at"),
        Index("idx_assignments_rubric", "rubric_id"),
        Index("idx_assignments_grade_category", "grade_category_id"),
        Index("idx_assignments_quiz", "quiz_id"),
    )

    @property
    def is_past_due(self) -> bool:
        return self.due_at is not None and self.due_at < datetime.now(timezone.utc)

    @property
    def accepts_late(self) -> bool:
        if not self.allow_late or self.due_at is None:
            return False
        grace_deadline = self.due_at + timedelta(hours=self.grace_period_hours or 0)
        now = datetime.now(timezone.utc)
        if now <= grace_deadline:
            return False
        if self.max_late_days is None:
            return True
        return now <= grace_deadline + timedelta(days=self.max_late_days)

    @validates("total_points")
    def validate_total_points(self, key: str, value: int) -> int:
        if value <= 0:
            raise ValueError("Assignment total_points must be greater than 0")
        return value

    @validates("late_penalty_per_day")
    def validate_late_penalty_per_day(self, key: str, value: float) -> float:
        if value < 0 or value > 100:
            raise ValueError("Assignment late_penalty_per_day must be between 0 and 100")
        return value

    def __repr__(self) -> str:
        return (
            f"<Assignment id={_short_id(self.id)} title={self.title} "
            f"exercise_type={self.exercise_type}>"
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
    rubric_scores: Mapped[list["RubricScore"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
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

    @property
    def is_graded(self) -> bool:
        return self.status in {
            SubmissionStatus.GRADED.value,
            SubmissionStatus.RETURNED.value,
        }

    def __repr__(self) -> str:
        return (
            f"<Submission id={_short_id(self.id)} student_id={_short_id(self.student_id)} "
            f"status={self.status}>"
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
    # Phase 9C — hints for frontend display (SOLUTION_SCAN, SOLUTION_PHOTO, DOCUMENT)
    file_type_hint: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="files")

    def __repr__(self) -> str:
        filename = self.file_path.rsplit("/", 1)[-1]
        return f"<SubmissionFile id={_short_id(self.id)} filename={filename}>"


class RubricScore(TimestampMixin, Base):
    """Teacher score for one rubric criterion on a submission."""

    __tablename__ = "rubric_scores"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
    )
    criterion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
        nullable=False,
    )
    level_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("rubric_levels.id", ondelete="SET NULL"),
        nullable=True,
    )
    points_awarded: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission: Mapped["Submission"] = relationship(back_populates="rubric_scores")
    criterion: Mapped["RubricCriterion"] = relationship(back_populates="scores")
    level: Mapped["RubricLevel | None"] = relationship(back_populates="scores")

    __table_args__ = (
        CheckConstraint("points_awarded >= 0", name="ck_rubric_scores_points_awarded"),
        UniqueConstraint(
            "submission_id",
            "criterion_id",
            name="uq_rubric_scores_sub_criterion",
        ),
        Index("idx_rubric_scores_submission", "submission_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<RubricScore id={_short_id(self.id)} "
            f"submission_id={_short_id(self.submission_id)}>"
        )


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
    original_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    late_penalty: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    late_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    penalty_overridden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(back_populates="grade")

    __table_args__ = (
        Index("idx_grades_submission_published", "submission_id", "published_at"),
    )

    @validates("score")
    def validate_score(self, key: str, value: float) -> float:
        if value < 0 or value > 20:
            raise ValueError("Grade score must be between 0 and 20")
        return value

    @validates("late_penalty")
    def validate_late_penalty(self, key: str, value: float) -> float:
        if value < 0:
            raise ValueError("Grade late_penalty must be non-negative")
        return value

    def __repr__(self) -> str:
        return (
            f"<Grade id={_short_id(self.id)} submission_id={_short_id(self.submission_id)} "
            f"score={self.score}>"
        )


class StudentPeriodAverage(TimestampMixin, SchoolScopedMixin, Base):
    """Cached weighted average per student, class, and period."""

    __tablename__ = "student_period_averages"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    weighted_average: Mapped[float] = mapped_column(Float, nullable=False)
    mention: Mapped[str] = mapped_column(String(30), nullable=False)
    class_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_students: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "class_id",
            "period_id",
            name="uq_spa_student_class_period",
        ),
        Index("idx_spa_class_period", "class_id", "period_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentPeriodAverage id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} average={self.weighted_average}>"
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

    def __repr__(self) -> str:
        return (
            f"<Assessment id={_short_id(self.id)} title={self.title} "
            f"status={self.status}>"
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
            "assessment_id",
            "student_id",
            name="uq_assessment_results_assessment_student",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<AssessmentResult id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} score={self.score}>"
        )


class QuizStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QuestionType(str, enum.Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"
    FILL_IN = "FILL_IN"
    DRAG_DROP = "DRAG_DROP"
    MATCHING = "MATCHING"


class QuizAttemptStatus(str, enum.Enum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    TIMED_OUT = "TIMED_OUT"


class ContentOrigin(str, enum.Enum):
    PLATFORM = "PLATFORM"
    PROMOTED = "PROMOTED"


class ContentSubmissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ContentItem(TimestampMixin, NullableSchoolScopedMixin, Base):
    """Educational content item (video, document, interactive).

    school_id nullable for shared/platform-wide content.
    Phase 9A: added subject, created_by, description, thumbnail_path, origin, original_content_id.
    """

    __tablename__ = "content_items"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ContentItemStatus.DRAFT.value
    )
    # Phase 9A fields
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    origin: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ContentOrigin.PLATFORM.value
    )
    original_content_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True
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
        Index("idx_content_items_subject", "subject"),
        Index("idx_content_items_origin", "origin"),
        Index("idx_content_items_created_by", "created_by"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContentItem id={_short_id(self.id)} title={self.title} "
            f"content_type={self.content_type}>"
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

    def __repr__(self) -> str:
        return (
            f"<ContentItemAsset id={_short_id(self.id)} "
            f"content_item_id={_short_id(self.content_item_id)}>"
        )


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
            "student_id",
            "content_item_id",
            name="uq_content_progress_student_item",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ContentProgress id={_short_id(self.id)} "
            f"student_id={_short_id(self.student_id)} status={self.status}>"
        )


class Activity(TimestampMixin, NullableSchoolScopedMixin, Base):
    """Pedagogical activity (quiz, exercise, game).

    school_id nullable for shared/platform-wide activities.
    """

    __tablename__ = "activities"

    type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    pedagogical_objective: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    sessions: Mapped[list["ActivitySession"]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("idx_activities_school_type", "school_id", "type"),)

    def __repr__(self) -> str:
        return f"<Activity id={_short_id(self.id)} title={self.title} type={self.type}>"


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

    def __repr__(self) -> str:
        return (
            f"<ActivitySession id={_short_id(self.id)} "
            f"activity_id={_short_id(self.activity_id)} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Phase 9A — Content Library Models
# ---------------------------------------------------------------------------


class ClassContentAssignment(TimestampMixin, SchoolScopedMixin, Base):
    """Teacher assigns platform/school content to a class.

    Unique per (class_id, content_item_id) — no duplicate assignments.
    """

    __tablename__ = "class_content_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    content_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "content_item_id",
            name="uq_class_content_assignments_class_content",
        ),
        Index("idx_class_content_assignments_teacher", "teacher_id"),
        Index("idx_class_content_assignments_class", "class_id"),
        Index("idx_class_content_assignments_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClassContentAssignment id={_short_id(self.id)} "
            f"class_id={_short_id(self.class_id)}>"
        )


class ContentSubmission(TimestampMixin, SchoolScopedMixin, Base):
    """Teacher submits school-scoped content for platform promotion review.

    Workflow: PENDING → UNDER_REVIEW → APPROVED/REJECTED
    On approval, promoted_content_id links to the platform copy.
    """

    __tablename__ = "content_submissions"

    content_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ContentSubmissionStatus.PENDING.value
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    promoted_content_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("idx_content_submissions_status", "status"),
        Index("idx_content_submissions_submitted_by", "submitted_by"),
        Index("idx_content_submissions_school", "school_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContentSubmission id={_short_id(self.id)} "
            f"submitted_by={_short_id(self.submitted_by)} status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Phase 9B — Quiz Engine Models
# ---------------------------------------------------------------------------


class Quiz(TimestampMixin, NullableSchoolScopedMixin, Base):
    """Quiz — created by CONTENT_MGR (platform-wide) or TCH (school-scoped).

    school_id=NULL means platform-wide (visible to all schools).
    """

    __tablename__ = "quizzes"

    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    level_band: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(20), nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=QuizStatus.DRAFT.value
    )

    # Relationships
    questions: Mapped[list["QuizQuestion"]] = relationship(
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizQuestion.order",
    )
    attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_quizzes_school_status", "school_id", "status"),
        Index("idx_quizzes_created_by", "created_by"),
        Index("idx_quizzes_subject", "subject"),
    )

    @property
    def is_active(self) -> bool:
        if self.status != QuizStatus.PUBLISHED.value:
            return False
        now = datetime.now(timezone.utc)
        start_at = getattr(self, "start_at", None) or getattr(self, "starts_at", None)
        end_at = getattr(self, "end_at", None) or getattr(self, "ends_at", None)
        if start_at is not None and now < start_at:
            return False
        if end_at is not None and now > end_at:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<Quiz id={_short_id(self.id)} title={self.title} "
            f"published={self.status == QuizStatus.PUBLISHED.value}>"
        )


class QuizQuestion(TimestampMixin, Base):
    """Question within a quiz. Supports 5 types with JSONB options/answers."""

    __tablename__ = "quiz_questions"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_media_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    options: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
    responses: Mapped[list["QuizResponse"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_quiz_questions_points"),
        Index("idx_quiz_questions_quiz_order", "quiz_id", "order"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuizQuestion id={_short_id(self.id)} quiz_id={_short_id(self.quiz_id)}>"
        )


class QuizAttempt(TimestampMixin, Base):
    """Student attempt at a quiz. Unique per (quiz, student, attempt_no)."""

    __tablename__ = "quiz_attempts"

    quiz_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    score: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=QuizAttemptStatus.STARTED.value
    )

    # Relationships
    quiz: Mapped["Quiz"] = relationship(back_populates="attempts")
    responses: Mapped[list["QuizResponse"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "quiz_id",
            "student_id",
            "attempt_no",
            name="uq_quiz_attempts_quiz_student_attempt",
        ),
        Index("idx_quiz_attempts_student", "student_id"),
        Index("idx_quiz_attempts_quiz_status", "quiz_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuizAttempt id={_short_id(self.id)} student_id={_short_id(self.student_id)} "
            f"status={self.status}>"
        )


class QuizResponse(TimestampMixin, Base):
    """Student response to a single quiz question within an attempt."""

    __tablename__ = "quiz_responses"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False
    )
    student_answer: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    points_earned: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )

    # Relationships
    attempt: Mapped["QuizAttempt"] = relationship(back_populates="responses")
    question: Mapped["QuizQuestion"] = relationship(back_populates="responses")

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_quiz_responses_attempt_question",
        ),
        Index("idx_quiz_responses_attempt", "attempt_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuizResponse id={_short_id(self.id)} attempt_id={_short_id(self.attempt_id)}>"
        )


class QuestionBankItem(TimestampMixin, SchoolScopedMixin, Base):
    """Reusable school question bank item for quiz generation."""

    __tablename__ = "question_bank_items"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    question_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(80)),
        nullable=False,
        default=list,
    )
    usage_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("idx_qb_school_subject", "school_id", "subject"),
        Index("idx_qb_school_difficulty", "school_id", "difficulty"),
        Index("idx_qb_teacher", "teacher_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionBankItem id={_short_id(self.id)} subject={self.subject} "
            f"difficulty={self.difficulty}>"
        )
