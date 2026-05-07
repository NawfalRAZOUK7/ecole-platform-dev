"""g42 student rewards

Revision ID: 6d3f2a91b4c8
Revises: a81c9e4f2b7d
Create Date: 2026-04-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "6d3f2a91b4c8"
down_revision = "a81c9e4f2b7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_rewards",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("xp", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("level", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "streak_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "badges",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("stars >= 0", name="ck_student_rewards_stars_non_negative"),
        sa.CheckConstraint("xp >= 0", name="ck_student_rewards_xp_non_negative"),
        sa.CheckConstraint("level >= 1", name="ck_student_rewards_level_min"),
        sa.CheckConstraint(
            "streak_days >= 0",
            name="ck_student_rewards_streak_days_non_negative",
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_student_rewards_student",
        "student_rewards",
        ["student_id"],
        unique=True,
    )

    op.create_table(
        "reward_events",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column(
            "stars_earned",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "xp_earned",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("source_type", sa.String(length=50), nullable=True),
        sa.Column("source_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "stars_earned >= 0",
            name="ck_reward_events_stars_earned_non_negative",
        ),
        sa.CheckConstraint(
            "xp_earned >= 0",
            name="ck_reward_events_xp_earned_non_negative",
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reward_events_student", "reward_events", ["student_id"])
    op.create_index("idx_reward_events_created", "reward_events", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_reward_events_created", table_name="reward_events")
    op.drop_index("idx_reward_events_student", table_name="reward_events")
    op.drop_table("reward_events")
    op.drop_index("uq_student_rewards_student", table_name="student_rewards")
    op.drop_table("student_rewards")
