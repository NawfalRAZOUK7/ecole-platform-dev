"""g47 add longest_streak to student_rewards

Revision ID: c7d8e9f0a1b2
Revises: f6e5d4c3b2a1
Create Date: 2026-04-17 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "f6e5d4c3b2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "student_rewards",
        sa.Column(
            "longest_streak",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.create_check_constraint(
        "ck_student_rewards_longest_streak_non_negative",
        "student_rewards",
        "longest_streak >= 0",
    )
    # Initialize longest_streak to current streak_days (best known value)
    op.execute(
        sa.text("UPDATE student_rewards SET longest_streak = streak_days")
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_student_rewards_longest_streak_non_negative",
        "student_rewards",
        type_="check",
    )
    op.drop_column("student_rewards", "longest_streak")
