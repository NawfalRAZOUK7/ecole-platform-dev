"""G30c — Report schedules.

Revision ID: f28394a5b6c7
Revises: f1728394a5b6
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f28394a5b6c7"
down_revision: Union[str, None] = "f1728394a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_schedules",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("report_type", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "recipient_roles",
            postgresql.ARRAY(sa.String(length=20)),
            nullable=False,
        ),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_report_schedules_school",
        "report_schedules",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_report_schedules_next_run",
        "report_schedules",
        ["next_run_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_report_schedules_next_run", table_name="report_schedules")
    op.drop_index("idx_report_schedules_school", table_name="report_schedules")
    op.drop_table("report_schedules")
