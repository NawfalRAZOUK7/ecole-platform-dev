"""G28d — Late submission penalty columns on assignments and grades.

Revision ID: bc2d3e4f5a67
Revises: ab1c2d3e4f56
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bc2d3e4f5a67"
down_revision: Union[str, None] = "ab1c2d3e4f56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assignments",
        sa.Column(
            "grace_period_hours",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "assignments",
        sa.Column(
            "late_penalty_per_day",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
    )
    op.add_column(
        "assignments",
        sa.Column("max_late_days", sa.Integer(), nullable=True),
    )
    op.add_column(
        "assignments",
        sa.Column(
            "allow_late",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )

    op.add_column(
        "grades",
        sa.Column("original_score", sa.Numeric(6, 2), nullable=True),
    )
    op.add_column(
        "grades",
        sa.Column(
            "late_penalty",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0.0"),
        ),
    )
    op.add_column(
        "grades",
        sa.Column(
            "late_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "grades",
        sa.Column(
            "penalty_overridden",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("grades", "penalty_overridden")
    op.drop_column("grades", "late_days")
    op.drop_column("grades", "late_penalty")
    op.drop_column("grades", "original_score")

    op.drop_column("assignments", "allow_late")
    op.drop_column("assignments", "max_late_days")
    op.drop_column("assignments", "late_penalty_per_day")
    op.drop_column("assignments", "grace_period_hours")
