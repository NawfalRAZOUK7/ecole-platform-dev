"""Add school_type to schools.

Revision ID: b8c9d0e1f2a3
Revises: 9d2b3c4e5f6a
Create Date: 2026-06-05 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b8c9d0e1f2a3"
down_revision = "9d2b3c4e5f6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "schools",
        sa.Column(
            "school_type",
            sa.String(length=20),
            nullable=False,
            server_default="formal",
        ),
    )
    op.alter_column("schools", "school_type", server_default=None)


def downgrade() -> None:
    op.drop_column("schools", "school_type")
