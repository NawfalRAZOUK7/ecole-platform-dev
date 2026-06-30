"""Constrain content_items.level_band / subject to the canonical taxonomy.

Adds CHECK constraints enforcing the ``ContentLevelBand`` / ``ContentSubject``
value sets (see ``app/models/lms.py``). The columns stay ``String`` (they are
written as raw strings by seeds/imports and are shared with ``Quiz``), so a
CHECK constraint — not a native PG enum swap — is used here.

The constraints are added ``NOT VALID``: existing rows are left untouched (no
risk of failing on legacy data), while every new INSERT/UPDATE is enforced.
Once data is confirmed clean (the seed already is), they can be promoted with
``ALTER TABLE content_items VALIDATE CONSTRAINT ...``.

Revision ID: 20260617_content_taxonomy_check
Revises: 20260616_micro_student_user
Create Date: 2026-06-17
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260617_content_taxonomy_check"
down_revision: Union[str, None] = "20260616_micro_student_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Snapshot of the canonical taxonomy at migration time. Kept in sync with
# ContentLevelBand / ContentSubject in app/models/lms.py. Migrations are
# immutable snapshots, so the values are intentionally inlined (not imported).
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


def _in_list(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def upgrade() -> None:
    op.execute(
        f"""
        ALTER TABLE content_items
        ADD CONSTRAINT ck_content_items_level_band
        CHECK (level_band IS NULL OR level_band IN ({_in_list(_LEVEL_BANDS)}))
        NOT VALID
        """
    )
    op.execute(
        f"""
        ALTER TABLE content_items
        ADD CONSTRAINT ck_content_items_subject
        CHECK (subject IS NULL OR subject IN ({_in_list(_SUBJECTS)}))
        NOT VALID
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE content_items DROP CONSTRAINT IF EXISTS ck_content_items_subject"
    )
    op.execute(
        "ALTER TABLE content_items DROP CONSTRAINT IF EXISTS ck_content_items_level_band"
    )
