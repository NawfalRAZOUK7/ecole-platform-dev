"""i4 absence justification attachment url

Revision ID: d9e8f7a6b5c4
Revises: a3b4c5d6e7f8
Create Date: 2026-04-20 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d9e8f7a6b5c4"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "absence_justifications",
        sa.Column("attachment_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("absence_justifications", "attachment_url")
