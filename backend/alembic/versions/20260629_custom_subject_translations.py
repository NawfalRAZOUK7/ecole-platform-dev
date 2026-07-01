"""Add translations JSONB to custom_subjects (#33 — trilingual titles).

Custom matières become trilingual like the official ones: ``title`` stays the
canonical/fallback name and ``translations`` (TranslatableMixin) holds per-locale
overrides — ``{"title": {"fr": ..., "ar": ..., "en": ...}}``. Additive + nullable;
no data migration needed (existing rows fall back to ``title``).

Revision ID: 20260629_custom_subject_i18n
Revises: 20260628_custom_subjects
Create Date: 2026-06-29
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260629_custom_subject_i18n"
down_revision: Union[str, None] = "20260628_custom_subjects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "custom_subjects",
        sa.Column("translations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("custom_subjects", "translations")
