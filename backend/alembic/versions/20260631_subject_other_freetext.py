"""Add subject_other free-text companion (#enum-other escape hatch).

``subject`` is the native ``content_subject_enum`` which includes ``other``. When
``subject = 'other'`` (a school-specific matière not in the official MEN list),
the actual name is stored in this free-text ``subject_other`` column — enum for
the closed set + free text for the open tail (same pattern as
``MicroSchool.type`` / ``type_detail``). Additive + nullable; no data migration.

Revision ID: 20260631_subject_other
Revises: 20260630_content_quiz_topic
Create Date: 2026-06-30
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260631_subject_other"
down_revision: Union[str, None] = "20260630_content_quiz_topic"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("content_items", "quizzes", "question_bank_items")


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table, sa.Column("subject_other", sa.String(length=120), nullable=True)
        )


def downgrade() -> None:
    for table in reversed(_TABLES):
        op.drop_column(table, "subject_other")
