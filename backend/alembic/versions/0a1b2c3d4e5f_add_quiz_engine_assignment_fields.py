"""G20 — Add quiz engine tables and assignment quiz fields.

Revision ID: 0a1b2c3d4e5f
Revises: f3a4b5c6d7e8
Create Date: 2026-03-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0a1b2c3d4e5f"
down_revision: Union[str, None] = "f3a4b5c6d7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quizzes",
        sa.Column("school_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=50), nullable=True),
        sa.Column("level_band", sa.String(length=50), nullable=True),
        sa.Column("difficulty", sa.String(length=20), nullable=True),
        sa.Column("time_limit_minutes", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("shuffle_questions", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_quizzes_school_status", "quizzes", ["school_id", "status"], unique=False
    )
    op.create_index("idx_quizzes_created_by", "quizzes", ["created_by"], unique=False)
    op.create_index("idx_quizzes_subject", "quizzes", ["subject"], unique=False)

    op.create_table(
        "quiz_questions",
        sa.Column(
            "quiz_id",
            sa.Uuid(),
            sa.ForeignKey("quizzes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_media_path", sa.String(length=500), nullable=True),
        sa.Column("options", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "correct_answer", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("points >= 0", name="ck_quiz_questions_points"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_quiz_questions_quiz_order",
        "quiz_questions",
        ["quiz_id", "order"],
        unique=False,
    )

    op.create_table(
        "quiz_attempts",
        sa.Column(
            "quiz_id",
            sa.Uuid(),
            sa.ForeignKey("quizzes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "quiz_id",
            "student_id",
            "attempt_no",
            name="uq_quiz_attempts_quiz_student_attempt",
        ),
    )
    op.create_index(
        "idx_quiz_attempts_student", "quiz_attempts", ["student_id"], unique=False
    )
    op.create_index(
        "idx_quiz_attempts_quiz_status",
        "quiz_attempts",
        ["quiz_id", "status"],
        unique=False,
    )

    op.create_table(
        "quiz_responses",
        sa.Column(
            "attempt_id",
            sa.Uuid(),
            sa.ForeignKey("quiz_attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("quiz_questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_answer", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("points_earned", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_quiz_responses_attempt_question",
        ),
    )
    op.create_index(
        "idx_quiz_responses_attempt", "quiz_responses", ["attempt_id"], unique=False
    )

    op.add_column(
        "assignments",
        sa.Column(
            "exercise_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'STANDARD'"),
        ),
    )
    op.alter_column("assignments", "exercise_type", server_default=None)
    op.add_column(
        "assignments",
        sa.Column(
            "quiz_id",
            sa.Uuid(),
            sa.ForeignKey("quizzes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("idx_assignments_quiz", "assignments", ["quiz_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_assignments_quiz", table_name="assignments")
    op.drop_column("assignments", "quiz_id")
    op.drop_column("assignments", "exercise_type")

    op.drop_index("idx_quiz_responses_attempt", table_name="quiz_responses")
    op.drop_table("quiz_responses")

    op.drop_index("idx_quiz_attempts_quiz_status", table_name="quiz_attempts")
    op.drop_index("idx_quiz_attempts_student", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")

    op.drop_index("idx_quiz_questions_quiz_order", table_name="quiz_questions")
    op.drop_table("quiz_questions")

    op.drop_index("idx_quizzes_subject", table_name="quizzes")
    op.drop_index("idx_quizzes_created_by", table_name="quizzes")
    op.drop_index("idx_quizzes_school_status", table_name="quizzes")
    op.drop_table("quizzes")
