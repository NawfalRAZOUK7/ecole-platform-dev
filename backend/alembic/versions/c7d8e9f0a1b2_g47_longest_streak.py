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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("student_rewards")}
    constraints = {
        constraint["name"]
        for constraint in inspector.get_check_constraints("student_rewards")
        if constraint["name"]
    }

    if "longest_streak" not in columns:
        op.add_column(
            "student_rewards",
            sa.Column(
                "longest_streak",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )

    if "ck_student_rewards_longest_streak_non_negative" not in constraints:
        op.create_check_constraint(
            "ck_student_rewards_longest_streak_non_negative",
            "student_rewards",
            "longest_streak >= 0",
        )

    # Initialize longest_streak to current streak_days (best known value)
    op.execute(
        sa.text(
            """
            UPDATE student_rewards
            SET longest_streak = GREATEST(COALESCE(longest_streak, 0), streak_days)
            """
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_student_rewards_longest_streak_non_negative",
        "student_rewards",
        type_="check",
    )
    op.drop_column("student_rewards", "longest_streak")
