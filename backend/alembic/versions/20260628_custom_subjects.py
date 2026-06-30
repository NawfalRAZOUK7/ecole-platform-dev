"""Custom matières — subject enum → validated String, add custom_subjects table.

To let schools add their own (non-official) matières (e.g. "Chant"), the
``subject`` columns can no longer be a *closed* native enum. This migration:

  1. converts the 5 ``content_subject_enum`` columns back to ``String`` (every
     enum value is valid text, so the cast is lossless):
       content_items, quizzes, question_bank_items, resources,
       difficulty_adaptations ``.subject``
  2. drops the now-unused ``content_subject_enum`` type
  3. creates ``custom_subjects`` (per-school user-defined matières).

Official matières remain the source of truth **in code**
(``app/models/curriculum.py``); validity = official ∪ a school's custom rows is
enforced in the service/schema layer (not the DB), which is why no CHECK
replaces the enum.

Revision ID: 20260628_custom_subjects
Revises: 20260627_subj_p2_micro_type
Create Date: 2026-06-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260628_custom_subjects"
down_revision: Union[str, None] = "20260627_subj_p2_micro_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SUBJECT_COLUMNS = (
    "content_items",
    "quizzes",
    "question_bank_items",
    "resources",
    "difficulty_adaptations",
)
_CONTENT_SUBJECT_ENUM = postgresql.ENUM(name="content_subject_enum", create_type=False)


def upgrade() -> None:
    # 1) enum -> String (official ∪ custom values now fit)
    for table in _SUBJECT_COLUMNS:
        op.alter_column(
            table,
            "subject",
            existing_type=_CONTENT_SUBJECT_ENUM,
            type_=sa.String(length=50),
            postgresql_using="subject::text",
        )
    # 2) drop the now-unused enum type
    op.execute("DROP TYPE IF EXISTS content_subject_enum")

    # 3) custom_subjects (school-defined matières)
    op.create_table(
        "custom_subjects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("cycle", sa.String(length=20), nullable=True),
        sa.Column("level_band", sa.String(length=50), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "code", name="uq_custom_subjects_school_code"),
    )
    op.create_index(
        "ix_custom_subjects_school_id", "custom_subjects", ["school_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_custom_subjects_school_id", table_name="custom_subjects")
    op.drop_table("custom_subjects")
    # Recreate the enum from the canonical taxonomy and convert columns back.
    from app.models.taxonomy import CONTENT_SUBJECTS

    enum_type = postgresql.ENUM(*CONTENT_SUBJECTS, name="content_subject_enum")
    enum_type.create(op.get_bind(), checkfirst=True)
    for table in reversed(_SUBJECT_COLUMNS):
        op.alter_column(
            table,
            "subject",
            existing_type=sa.String(length=50),
            type_=enum_type,
            postgresql_using="subject::text::content_subject_enum",
        )
