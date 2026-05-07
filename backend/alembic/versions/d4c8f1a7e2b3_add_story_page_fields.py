"""g44 story page fields

Revision ID: d4c8f1a7e2b3
Revises: b71f4d2c8e9a
Create Date: 2026-04-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "d4c8f1a7e2b3"
down_revision = "b71f4d2c8e9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "content_item_assets",
        sa.Column("page_number", sa.Integer(), nullable=True),
    )
    op.add_column(
        "content_item_assets",
        sa.Column("narration_text", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_item_assets",
        sa.Column(
            "has_activity",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "content_item_assets",
        sa.Column("asset_type", sa.String(length=50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_item_assets", "asset_type")
    op.drop_column("content_item_assets", "has_activity")
    op.drop_column("content_item_assets", "narration_text")
    op.drop_column("content_item_assets", "page_number")
