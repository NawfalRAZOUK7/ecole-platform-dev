"""Persist quiz provenance for Feature B.

Adds:
- quiz_questions.source       : where a question came from
                                ("ai" | "template" | "teacher" | "bank"), nullable
                                so existing rows stay valid.
- quizzes.source_content_id   : nullable FK to the content item a quiz was
                                generated from (SET NULL on content delete).

Additive only — no existing column or constraint is changed.

Revision ID: add_quiz_source_columns
Revises: merge_b_quiz_heads_2026_06
Create Date: 2026-06-05 00:10:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_quiz_source_columns"
down_revision = "merge_b_quiz_heads_2026_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quiz_questions",
        sa.Column("source", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "quizzes",
        sa.Column(
            "source_content_id",
            sa.UUID(),
            sa.ForeignKey("content_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_quizzes_source_content",
        "quizzes",
        ["source_content_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_quizzes_source_content", table_name="quizzes")
    op.drop_column("quizzes", "source_content_id")
    op.drop_column("quiz_questions", "source")
