"""Restore subject as native content_subject_enum (incl. ``other``).

Decision (owner): ``subject`` is a **closed native enum** that includes an
``other`` escape hatch; a school-specific matière is ``subject = 'other'`` + a
free-text ``subject_other`` name (added in 20260631). Migration 20260628 had
converted ``subject`` back to ``String`` and dropped ``content_subject_enum``;
this migration reverses that: recreate the enum (now incl. ``other``) and convert
the 5 ``subject`` columns back to it. ``custom_subjects`` is **kept** — it is now
the per-school *suggestion list* of ``other`` names (trilingual), not a content
validator.

Existing String rows are remapped (legacy French/display → Moroccan) and any
value still outside the enum is set to ``other`` (NULLs preserved) so the cast
never fails — safe for the NOT NULL columns too.

Revision ID: 20260632_subject_enum_other
Revises: 20260631_subject_other
Create Date: 2026-07-02
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260632_subject_enum_other"
down_revision: Union[str, None] = "20260631_subject_other"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Snapshot of content_subject_enum — parity with app/models/taxonomy.py
# (ContentSubject), INCLUDING the `other` escape hatch.
_SUBJECTS = (
    "arabic", "french", "english", "math",
    "activite_scientifique", "svt", "physique_chimie",
    "histoire_geo", "civic", "philosophy", "islamic",
    "art", "music", "sport",
    "informatique", "technology", "economics", "accounting",
    "arabic_letters", "literacy", "vocabulary", "pedagogy",
    "other",
)
# Legacy / display-name → Moroccan code (applied before the cast).
_SUBJECT_REMAP = {
    "science": "activite_scientifique",
    "Sciences": "activite_scientifique",
    "physics": "physique_chimie",
    "chemistry": "physique_chimie",
    "biology": "svt",
    "history": "histoire_geo",
    "geography": "histoire_geo",
    "Mathématiques": "math",
    "Français": "french",
    "Francais": "french",
}
_SUBJECT_COLUMNS = (
    "content_items",
    "quizzes",
    "question_bank_items",
    "resources",
    "difficulty_adaptations",
)

CONTENT_SUBJECT_ENUM = postgresql.ENUM(*_SUBJECTS, name="content_subject_enum")


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def upgrade() -> None:
    bind = op.get_bind()
    CONTENT_SUBJECT_ENUM.create(bind, checkfirst=True)
    for table in _SUBJECT_COLUMNS:
        for old, new in _SUBJECT_REMAP.items():
            op.execute(
                f"UPDATE \"{table}\" SET subject = '{new}' WHERE subject = "
                f"'{old.replace(chr(39), chr(39) * 2)}'"
            )
        # Anything still outside the enum becomes the 'other' escape hatch
        # (NULLs preserved; safe for NOT NULL columns).
        op.execute(
            f"UPDATE \"{table}\" SET subject = 'other' "
            f"WHERE subject IS NOT NULL AND subject NOT IN ({_in(_SUBJECTS)})"
        )
        op.alter_column(
            table,
            "subject",
            existing_type=sa.String(length=50),
            type_=CONTENT_SUBJECT_ENUM,
            postgresql_using="subject::text::content_subject_enum",
        )


def downgrade() -> None:
    for table in reversed(_SUBJECT_COLUMNS):
        op.alter_column(
            table,
            "subject",
            existing_type=CONTENT_SUBJECT_ENUM,
            type_=sa.String(length=50),
            postgresql_using="subject::text",
        )
    op.execute("DROP TYPE IF EXISTS content_subject_enum")
