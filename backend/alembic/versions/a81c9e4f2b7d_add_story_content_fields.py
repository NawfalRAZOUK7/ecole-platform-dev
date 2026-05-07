"""g41 story content fields

Revision ID: a81c9e4f2b7d
Revises: d4a1f0c8b2e7
Create Date: 2026-04-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "a81c9e4f2b7d"
down_revision = "d4a1f0c8b2e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_items", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("content_items", sa.Column("letter", sa.String(length=10), nullable=True))
    op.add_column(
        "content_items",
        sa.Column("target_age_min", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("target_age_max", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("theme_color", sa.String(length=7), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_items", "theme_color")
    op.drop_column("content_items", "target_age_max")
    op.drop_column("content_items", "target_age_min")
    op.drop_column("content_items", "letter")
    op.drop_column("content_items", "page_count")
