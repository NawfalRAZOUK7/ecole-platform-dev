"""Unified i18n storage — add JSONB `translations` and backfill from *_fr/_ar/_en.

P1 (audit §2.1) — replaces the scattered ``<field>_fr/_ar/_en`` columns with a
single JSONB ``translations`` column (``TranslatableMixin``). This migration is
**additive + backfill only**: the legacy columns are kept so existing read paths
keep working (dual-read). Dropping them is a later, coordinated phase once every
serializer + web/mobile read site uses ``tr(...)``.

Shape: ``{"<field>": {"fr": ..., "ar": ..., "en": ...}}`` (nulls stripped).

Revision ID: 20260621_i18n_translations
Revises: 20260620_currency_language
Create Date: 2026-06-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260621_i18n_translations"
down_revision: Union[str, None] = "20260620_currency_language"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# table -> {json_field: (col_fr, col_ar, col_en)}  (None = column absent)
_BACKFILL = {
    "events": {"title": ("title_fr", "title_ar", "title_en")},
    "moroccan_holidays": {"name": ("name_fr", "name_ar", "name_en")},
    "game_configs": {"title": ("title_fr", "title_ar", None)},
    "level_age_mappings": {"label": ("label_fr", "label_ar", "label_en")},
    "men_objectives": {
        "title": ("title_fr", "title_ar", None),
        "description": ("description_fr", None, None),
    },
    "reward_badges": {
        "title": ("title_fr", "title_ar", "title_en"),
        "description": ("description_fr", "description_ar", "description_en"),
    },
    "skill_dimensions": {
        "name": ("name_fr", "name_ar", "name_en"),
        "description": ("description_fr", None, None),
    },
    "skill_milestones": {"name": ("name_fr", "name_ar", None)},
    "schools": {"name": ("name", "name_ar", None)},
}


def _field_obj(field: str, cols: tuple) -> str:
    fr, ar, en = cols
    pairs = []
    if fr:
        pairs.append(f"'fr', {fr}")
    if ar:
        pairs.append(f"'ar', {ar}")
    if en:
        pairs.append(f"'en', {en}")
    inner = f"jsonb_strip_nulls(jsonb_build_object({', '.join(pairs)}))"
    return f"'{field}', {inner}"


def upgrade() -> None:
    for table in _BACKFILL:
        op.add_column(
            table,
            sa.Column("translations", postgresql.JSONB(), nullable=True),
        )
    for table, fields in _BACKFILL.items():
        obj = ", ".join(_field_obj(f, cols) for f, cols in fields.items())
        op.execute(
            f"UPDATE {table} "
            f"SET translations = jsonb_strip_nulls(jsonb_build_object({obj}))"
        )


def downgrade() -> None:
    for table in _BACKFILL:
        op.drop_column(table, "translations")
