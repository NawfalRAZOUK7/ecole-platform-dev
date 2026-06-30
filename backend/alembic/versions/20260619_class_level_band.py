"""Add canonical level_band + cycle columns to classes.

P0.2 — ``Class`` had no level/cycle column; teacher CMS-library scoping derived
the level by string-parsing the class ``code`` (fragile for non-standard codes).
This adds the canonical columns (additive, nullable). The seed now populates
them; legacy rows fall back to code parsing in
``repositories/lms.py:list_teacher_level_bands`` until backfilled.

Backfill for existing rows (run once, after deploy):
    UPDATE classes SET level_band = ... ;  -- via the app parser or a data script

Revision ID: 20260619_class_level_band
Revises: 20260618_taxonomy_constraints
Create Date: 2026-06-19
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260619_class_level_band"
down_revision: Union[str, None] = "20260618_taxonomy_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LEVEL_BANDS = (
    "maternelle", "CP", "CE1", "CE2", "CM1", "CM2", "primaire",
    "6eme", "5eme", "4eme", "3eme", "college", "2nde", "1ere",
    "Terminale", "lycee",
)
_CYCLES = ("maternelle", "primaire", "college", "lycee", "informel")


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def upgrade() -> None:
    op.add_column("classes", sa.Column("level_band", sa.String(length=50), nullable=True))
    op.add_column("classes", sa.Column("cycle", sa.String(length=20), nullable=True))
    op.execute(
        f"""
        ALTER TABLE classes
        ADD CONSTRAINT ck_classes_level_band
        CHECK (level_band IS NULL OR level_band IN ({_in(_LEVEL_BANDS)}))
        NOT VALID
        """
    )
    op.execute(
        f"""
        ALTER TABLE classes
        ADD CONSTRAINT ck_classes_cycle
        CHECK (cycle IS NULL OR cycle IN ({_in(_CYCLES)}))
        NOT VALID
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE classes DROP CONSTRAINT IF EXISTS ck_classes_cycle")
    op.execute("ALTER TABLE classes DROP CONSTRAINT IF EXISTS ck_classes_level_band")
    op.drop_column("classes", "cycle")
    op.drop_column("classes", "level_band")
