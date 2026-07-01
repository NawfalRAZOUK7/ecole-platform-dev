"""Normalize + constrain difficulty, and extend content taxonomy to quizzes.

P0.1 — ``difficulty`` previously stored both ``EASY`` and ``easy`` for the same
concept (data-integrity bug). This migration:
  * normalizes every ``difficulty`` value to UPPERCASE (the canonical
    ``DifficultyLevel`` form), then
  * adds a CHECK constraint ``difficulty IN ('EASY','MEDIUM','HARD')`` on each
    table that owns the column (game_configs, activities, quizzes,
    question_bank_items).

P0.3 — extends the curriculum-taxonomy CHECKs (already on ``content_items``) to
``quizzes`` and ``question_bank_items`` (``subject`` / ``level_band``), which use
the same coded vocabulary.

CHECKs are ``NOT VALID`` (existing rows untouched, new writes enforced). The
``difficulty`` UPDATE fixes the legacy rows in place; promote with
``VALIDATE CONSTRAINT`` once confirmed.

Revision ID: 20260618_taxonomy_constraints
Revises: 20260617_content_taxonomy_check
Create Date: 2026-06-18
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260618_taxonomy_constraints"
down_revision: Union[str, None] = "20260617_content_taxonomy_check"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Snapshot of the canonical taxonomy (kept in sync with app/models/taxonomy.py).
_DIFFICULTY = ("EASY", "MEDIUM", "HARD")
_LEVEL_BANDS = (
    "maternelle", "CP", "CE1", "CE2", "CM1", "CM2", "primaire",
    "6eme", "5eme", "4eme", "3eme", "college", "2nde", "1ere",
    "Terminale", "lycee",
)
_SUBJECTS = (
    "math", "french", "arabic", "arabic_letters", "english", "science",
    "physics", "chemistry", "biology", "history", "geography", "philosophy",
    "technology", "islamic", "civic", "art", "music", "sport",
    "vocabulary", "literacy", "pedagogy",
)

_DIFFICULTY_TABLES = ("game_configs", "activities", "quizzes", "question_bank_items")
# Only `quizzes` carries the coded subject + level_band taxonomy. `question_bank_items`
# has no `level_band` column and its `subject` is free-form String(120) (topic text),
# so it is intentionally excluded from the strict taxonomy CHECK.
_TAXONOMY_TABLES = ("quizzes",)


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def upgrade() -> None:
    # 1) Normalize legacy difficulty case in place (fixes EASY/easy split).
    for table in _DIFFICULTY_TABLES:
        op.execute(
            f"UPDATE {table} SET difficulty = upper(difficulty) "
            f"WHERE difficulty IS NOT NULL"
        )
        op.execute(
            f"""
            ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_difficulty
            CHECK (difficulty IS NULL OR difficulty IN ({_in(_DIFFICULTY)}))
            NOT VALID
            """
        )

    # 2) Extend curriculum taxonomy CHECKs to quizzes + question_bank_items.
    for table in _TAXONOMY_TABLES:
        op.execute(
            f"""
            ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_level_band
            CHECK (level_band IS NULL OR level_band IN ({_in(_LEVEL_BANDS)}))
            NOT VALID
            """
        )
        op.execute(
            f"""
            ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_subject
            CHECK (subject IS NULL OR subject IN ({_in(_SUBJECTS)}))
            NOT VALID
            """
        )

    # 3) question_bank_items reform — align with the coded taxonomy (no free text):
    #    rename `level` -> `level_band`, narrow `subject` String(120) -> String(50),
    #    and add the same CHECKs. (Prod with long/free-form subjects must normalize
    #    them to ContentSubject codes before this migration.)
    op.alter_column("question_bank_items", "level", new_column_name="level_band")
    op.alter_column(
        "question_bank_items",
        "subject",
        existing_type=sa.String(length=120),
        type_=sa.String(length=50),
    )
    op.execute(
        f"""
        ALTER TABLE question_bank_items
        ADD CONSTRAINT ck_question_bank_items_level_band
        CHECK (level_band IS NULL OR level_band IN ({_in(_LEVEL_BANDS)}))
        NOT VALID
        """
    )
    op.execute(
        f"""
        ALTER TABLE question_bank_items
        ADD CONSTRAINT ck_question_bank_items_subject
        CHECK (subject IS NULL OR subject IN ({_in(_SUBJECTS)}))
        NOT VALID
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE question_bank_items "
        "DROP CONSTRAINT IF EXISTS ck_question_bank_items_subject"
    )
    op.execute(
        "ALTER TABLE question_bank_items "
        "DROP CONSTRAINT IF EXISTS ck_question_bank_items_level_band"
    )
    op.alter_column(
        "question_bank_items",
        "subject",
        existing_type=sa.String(length=50),
        type_=sa.String(length=120),
    )
    op.alter_column("question_bank_items", "level_band", new_column_name="level")
    for table in _TAXONOMY_TABLES:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_subject")
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_level_band"
        )
    for table in _DIFFICULTY_TABLES:
        op.execute(
            f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_difficulty"
        )
    # Difficulty case normalization is intentionally not reverted.
