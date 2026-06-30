"""Promote subject / level_band to native enums — Phase 1 (B2), Moroccan values.

Phase 1 converts the curriculum columns to native PostgreSQL enums using the
**Moroccan national (MEN)** vocabulary. ``app/models/taxonomy.py`` is the source
of truth; the value tuples below are a snapshot kept in parity with it (asserted
by the task-13 validation script).

  * content_subject_enum     -> content_items.subject, quizzes.subject,
                                question_bank_items.subject
  * content_level_band_enum  -> content_items.level_band, quizzes.level_band,
                                question_bank_items.level_band, classes.level_band

Existing rows are remapped from the legacy French codes to the Moroccan codes
*before* the cast (see ``_LEVEL_REMAP`` / ``_SUBJECT_REMAP``), so the migration is
safe whether the DB still holds French-seeded data or has been reseeded to the
Moroccan codes. The mapping is stage-anchored (first->first, last->last; primary
French 5 grades -> Moroccan 6, leaving 5AEP without a French source; collège
French 4 -> Moroccan 3).

The per-table CHECKs from 617/618/619 are dropped (the enum now enforces the
domain) and re-created NOT VALID on downgrade. No dependent views reference these
columns; the multi-column index idx_content_items_type_level_lang is rebuilt
automatically by ALTER TYPE.

Phase 2 (resources.subject, difficulty_adaptations.subject) + MicroSchool.type
live in ``20260627``. ``timetable_slots`` (its own activity redesign) and
``men_curricula`` (its own official MEN vocabulary) are intentionally excluded.

Revision ID: 20260626_subj_level_enums
Revises: 20260625_rename_school_budgets
Create Date: 2026-06-26
"""

from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_subj_level_enums"
down_revision: Union[str, None] = "20260625_rename_school_budgets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Moroccan official (MEN) vocabulary — parity with app/models/taxonomy.py
# (ContentLevelBand / ContentSubject).
_LEVEL_BANDS = (
    "PS", "MS", "GS",
    "1AEP", "2AEP", "3AEP", "4AEP", "5AEP", "6AEP",
    "1AC", "2AC", "3AC",
    "TC", "1BAC", "2BAC",
)
_SUBJECTS = (
    "arabic", "french", "english", "math",
    "activite_scientifique", "svt", "physique_chimie",
    "histoire_geo", "civic", "philosophy", "islamic",
    "art", "music", "sport",
    "informatique", "technology", "economics", "accounting",
    "arabic_letters", "literacy", "vocabulary", "pedagogy",
    "other",  # escape hatch; real name lives in *.subject_other (free text)
)

# Legacy French -> Moroccan remap, applied to existing rows before the cast.
_LEVEL_REMAP = {
    "maternelle": "GS",
    "CP": "1AEP", "CE1": "2AEP", "CE2": "3AEP", "CM1": "4AEP", "CM2": "6AEP",
    "primaire": "1AEP",
    "6eme": "1AC", "5eme": "2AC", "4eme": "3AC", "3eme": "3AC",
    "college": "1AC",
    "2nde": "TC", "1ere": "1BAC", "Terminale": "2BAC",
    "lycee": "TC",
}
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

CONTENT_SUBJECT_ENUM = postgresql.ENUM(*_SUBJECTS, name="content_subject_enum")
CONTENT_LEVEL_BAND_ENUM = postgresql.ENUM(
    *_LEVEL_BANDS, name="content_level_band_enum"
)
ENUM_TYPES = [CONTENT_SUBJECT_ENUM, CONTENT_LEVEL_BAND_ENUM]

# (table, column, enum, existing String length)
COLUMN_CONVERSIONS: list[tuple[str, str, postgresql.ENUM, int]] = [
    ("content_items", "subject", CONTENT_SUBJECT_ENUM, 50),
    ("content_items", "level_band", CONTENT_LEVEL_BAND_ENUM, 50),
    ("quizzes", "subject", CONTENT_SUBJECT_ENUM, 50),
    ("quizzes", "level_band", CONTENT_LEVEL_BAND_ENUM, 50),
    ("question_bank_items", "subject", CONTENT_SUBJECT_ENUM, 50),
    ("question_bank_items", "level_band", CONTENT_LEVEL_BAND_ENUM, 50),
    ("classes", "level_band", CONTENT_LEVEL_BAND_ENUM, 50),
]

# (table, column, constraint_name, allowed_values) — dropped on upgrade,
# recreated NOT VALID on downgrade.
CHECK_CONSTRAINTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("content_items", "subject", "ck_content_items_subject", _SUBJECTS),
    ("content_items", "level_band", "ck_content_items_level_band", _LEVEL_BANDS),
    ("quizzes", "subject", "ck_quizzes_subject", _SUBJECTS),
    ("quizzes", "level_band", "ck_quizzes_level_band", _LEVEL_BANDS),
    (
        "question_bank_items",
        "subject",
        "ck_question_bank_items_subject",
        _SUBJECTS,
    ),
    (
        "question_bank_items",
        "level_band",
        "ck_question_bank_items_level_band",
        _LEVEL_BANDS,
    ),
    ("classes", "level_band", "ck_classes_level_band", _LEVEL_BANDS),
]

DEFAULT_LITERAL_RE = re.compile(r"'((?:[^']|'')*)'")


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def _drop_checks() -> None:
    for table, _col, name, _vals in CHECK_CONSTRAINTS:
        op.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"')


def _create_checks() -> None:
    for table, col, name, vals in CHECK_CONSTRAINTS:
        op.execute(
            f'ALTER TABLE "{table}" ADD CONSTRAINT "{name}" '
            f"CHECK ({col} IS NULL OR {col} IN ({_in(vals)})) NOT VALID"
        )


def _remap_legacy_values() -> None:
    """Convert any legacy French codes to Moroccan codes before the enum cast."""
    for table, col, enum_type, _len in COLUMN_CONVERSIONS:
        mapping = (
            _LEVEL_REMAP
            if enum_type is CONTENT_LEVEL_BAND_ENUM
            else _SUBJECT_REMAP
        )
        for old, new in mapping.items():
            o = old.replace("'", "''")
            n = new.replace("'", "''")
            op.execute(
                f'UPDATE "{table}" SET "{col}" = \'{n}\' WHERE "{col}" = \'{o}\''
            )


def _load_string_defaults(bind) -> dict[tuple[str, str], str]:
    defaults: dict[tuple[str, str], str] = {}
    for table, col, _enum, _len in COLUMN_CONVERSIONS:
        expr = bind.execute(
            sa.text(
                """
                SELECT column_default FROM information_schema.columns
                WHERE table_schema='public' AND table_name=:t AND column_name=:c
                """
            ),
            {"t": table, "c": col},
        ).scalar_one_or_none()
        if not expr:
            continue
        m = DEFAULT_LITERAL_RE.search(expr)
        if not m:
            continue
        defaults[(table, col)] = m.group(1).replace("''", "'")
        op.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" DROP DEFAULT')
    return defaults


def _restore_defaults(defaults, *, use_enum_casts: bool) -> None:
    lookup = {(t, c): e.name for t, c, e, _ in COLUMN_CONVERSIONS}
    remap = {"level_band": _LEVEL_REMAP, "subject": _SUBJECT_REMAP}
    for (table, col), val in defaults.items():
        # A stale French default would fail the enum cast — remap it too.
        if use_enum_casts:
            val = remap.get(col, {}).get(val, val)
        esc = val.replace("'", "''")
        sql = f"'{esc}'::{lookup[(table, col)]}" if use_enum_casts else f"'{esc}'"
        op.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{col}" SET DEFAULT {sql}')


def upgrade() -> None:
    bind = op.get_bind()
    _drop_checks()
    _remap_legacy_values()
    defaults = _load_string_defaults(bind)
    for enum_type in ENUM_TYPES:
        enum_type.create(bind, checkfirst=False)
    for table, col, enum_type, length in COLUMN_CONVERSIONS:
        op.alter_column(
            table,
            col,
            existing_type=sa.String(length=length),
            type_=enum_type,
            postgresql_using=f"{col}::text::{enum_type.name}",
        )
    _restore_defaults(defaults, use_enum_casts=True)


def downgrade() -> None:
    bind = op.get_bind()
    defaults = _load_string_defaults(bind)
    for table, col, enum_type, length in reversed(COLUMN_CONVERSIONS):
        op.alter_column(
            table,
            col,
            existing_type=enum_type,
            type_=sa.String(length=length),
            postgresql_using=f"{col}::text",
        )
    _restore_defaults(defaults, use_enum_casts=False)
    for enum_type in reversed(ENUM_TYPES):
        enum_type.drop(bind, checkfirst=False)
    _create_checks()
