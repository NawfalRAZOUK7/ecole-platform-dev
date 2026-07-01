"""Add topic (sujet) to content_items + quizzes (#32 — matière→sujet link).

The curriculum tree is cycle → niveau → matière → **sujet (topic)**. Content and
quizzes already carry the matière (``subject``) and niveau (``level_band``); this
adds the ``topic`` (sujet) — the chapter within the matière. It is **open user
input** (suggestions come from ``curriculum.topics_for(level, subject)``), so it
is a free ``String`` by design, not an enum. Additive + nullable; no data
migration.

Revision ID: 20260630_content_quiz_topic
Revises: 20260629_custom_subject_i18n
Create Date: 2026-06-30
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_content_quiz_topic"
down_revision: Union[str, None] = "20260629_custom_subject_i18n"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_items", sa.Column("topic", sa.String(length=200), nullable=True)
    )
    op.add_column(
        "quizzes", sa.Column("topic", sa.String(length=200), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("quizzes", "topic")
    op.drop_column("content_items", "topic")
