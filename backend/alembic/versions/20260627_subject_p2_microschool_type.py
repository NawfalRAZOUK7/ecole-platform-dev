"""Subject enums Phase 2 + MicroSchool.type (B2, task 13).

Phase 2 promotes the remaining curriculum ``subject`` columns to the native
``content_subject_enum`` (created in 20260626):

  * resources.subject              (was nullable String(120), free-text)
  * difficulty_adaptations.subject (was NOT NULL String(100), audit log)

Legacy / display-name values are remapped to Moroccan codes before the cast
(same map as 20260626). ``resources.subject`` was genuinely free-text, so any
value that is neither a known legacy code nor a valid Moroccan code is set to
NULL (the column is nullable) rather than failing the migration.

Also adds the informal-provider type to micro-schools:

  * micro_schools.type        (micro_school_type_enum: rawd/msid/non_formel/general)
  * micro_schools.type_detail (String, free text — only meaningful for `general`,
                               the user-input exception)

Intentionally excluded: ``timetable_slots`` (its own activity-model redesign — a
slot is an activity that may attach to 0..N matières or a free-text title) and
``men_curricula`` (keeps its own official MEN subject vocabulary).

Revision ID: 20260627_subj_p2_micro_type
Revises: 20260626_subj_level_enums
Create Date: 2026-06-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260627_subj_p2_micro_type"
down_revision: Union[str, None] = "20260626_subj_level_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Snapshot of the Moroccan content_subject_enum (created by 20260626) +
# the legacy->Moroccan subject remap, kept in parity with taxonomy.py.
_SUBJECTS = (
    "arabic", "french", "english", "math",
    "activite_scientifique", "svt", "physique_chimie",
    "histoire_geo", "civic", "philosophy", "islamic",
    "art", "music", "sport",
    "informatique", "technology", "economics", "accounting",
    "arabic_letters", "literacy", "vocabulary", "pedagogy",
)
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
    "branding": "pedagogy",
}

_MICRO_SCHOOL_TYPES = ("rawd", "msid", "non_formel", "general")

CONTENT_SUBJECT_ENUM = postgresql.ENUM(
    *_SUBJECTS, name="content_subject_enum", create_type=False
)
MICRO_SCHOOL_TYPE_ENUM = postgresql.ENUM(
    *_MICRO_SCHOOL_TYPES, name="micro_school_type_enum"
)

# (table, column, existing String length, nullable)
_SUBJECT_COLUMNS = [
    ("resources", "subject", 120, True),
    ("difficulty_adaptations", "subject", 100, False),
]


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def _coerce_subject(table: str, col: str, *, nullable: bool) -> None:
    """Remap legacy subject codes, then (for nullable cols) NULL out unknowns."""
    for old, new in _SUBJECT_REMAP.items():
        o = old.replace("'", "''")
        n = new.replace("'", "''")
        op.execute(
            f'UPDATE "{table}" SET "{col}" = \'{n}\' WHERE "{col}" = \'{o}\''
        )
    if nullable:
        op.execute(
            f'UPDATE "{table}" SET "{col}" = NULL '
            f'WHERE "{col}" IS NOT NULL AND "{col}" NOT IN ({_in(_SUBJECTS)})'
        )


def upgrade() -> None:
    bind = op.get_bind()

    # --- Phase 2 subject columns -> content_subject_enum ---
    for table, col, length, nullable in _SUBJECT_COLUMNS:
        _coerce_subject(table, col, nullable=nullable)
        op.alter_column(
            table,
            col,
            existing_type=sa.String(length=length),
            type_=CONTENT_SUBJECT_ENUM,
            existing_nullable=nullable,
            postgresql_using=f"{col}::text::content_subject_enum",
        )

    # --- MicroSchool.type (+ free-text type_detail) ---
    MICRO_SCHOOL_TYPE_ENUM.create(bind, checkfirst=True)
    op.add_column(
        "micro_schools",
        sa.Column(
            "type",
            MICRO_SCHOOL_TYPE_ENUM,
            nullable=False,
            server_default="general",
        ),
    )
    op.add_column(
        "micro_schools",
        sa.Column("type_detail", sa.String(length=200), nullable=True),
    )
    # Match the project convention (Python-side default, no DB server default).
    op.alter_column("micro_schools", "type", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_column("micro_schools", "type_detail")
    op.drop_column("micro_schools", "type")
    MICRO_SCHOOL_TYPE_ENUM.drop(bind, checkfirst=True)

    for table, col, length, nullable in reversed(_SUBJECT_COLUMNS):
        op.alter_column(
            table,
            col,
            existing_type=CONTENT_SUBJECT_ENUM,
            type_=sa.String(length=length),
            existing_nullable=nullable,
            postgresql_using=f"{col}::text",
        )
