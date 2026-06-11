"""Add quizzes.language for trilingual quiz audio.

Stores the quiz content language ("ar" | "fr" | "en") so the web/mobile players
can pick the right TTS voice (notably distinguishing French from English, which
share the Latin script). Nullable — existing quizzes keep working.

Revision ID: add_quiz_language
Revises: add_quiz_source_columns
Create Date: 2026-06-05 00:20:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_quiz_language"
down_revision = "add_quiz_source_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "quizzes",
        sa.Column("language", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("quizzes", "language")
