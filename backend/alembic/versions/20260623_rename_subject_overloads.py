"""Rename the two non-curriculum ``subject`` columns (B1).

``subject`` was overloaded across the schema. Eight columns are genuine
curriculum subjects (kept). Two are *not* and are renamed for clarity /
grep-ability (BACKEND_DB_AUDIT.md §11 B1):

  * conversations.subject     -> subject_line  (a message-thread subject line)
  * writing_attempts.subject  -> topic         (an essay/writing topic)

Pure column renames — no type change, no data migration.

Revision ID: 20260623_rename_subjects
Revises: 20260622_promote_native_enums
Create Date: 2026-06-23
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20260623_rename_subjects"
down_revision: Union[str, None] = "20260622_promote_native_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("conversations", "subject", new_column_name="subject_line")
    op.alter_column("writing_attempts", "subject", new_column_name="topic")


def downgrade() -> None:
    op.alter_column("writing_attempts", "topic", new_column_name="subject")
    op.alter_column("conversations", "subject_line", new_column_name="subject")
