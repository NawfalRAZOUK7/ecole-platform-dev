"""g43 game config

Revision ID: b71f4d2c8e9a
Revises: 6d3f2a91b4c8
Create Date: 2026-04-13 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "b71f4d2c8e9a"
down_revision = "6d3f2a91b4c8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_configs",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("game_type", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("title_ar", sa.String(length=300), nullable=True),
        sa.Column("title_fr", sa.String(length=300), nullable=True),
        sa.Column("subject", sa.String(length=50), nullable=True),
        sa.Column(
            "difficulty",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'easy'"),
        ),
        sa.Column("target_age_min", sa.SmallInteger(), nullable=True),
        sa.Column("target_age_max", sa.SmallInteger(), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "reward_stars",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("10"),
        ),
        sa.Column(
            "reward_xp",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("15"),
        ),
        sa.Column("school_id", sa.Uuid(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_game_configs_type", "game_configs", ["game_type"])
    op.create_index(
        "idx_game_configs_active",
        "game_configs",
        ["is_active"],
        unique=False,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index("idx_game_configs_active", table_name="game_configs")
    op.drop_index("idx_game_configs_type", table_name="game_configs")
    op.drop_table("game_configs")
