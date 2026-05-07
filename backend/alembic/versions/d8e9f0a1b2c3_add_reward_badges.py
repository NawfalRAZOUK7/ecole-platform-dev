"""g47b reward badges

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-04-18 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "d8e9f0a1b2c3"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = set(inspector.get_table_names())

    if "reward_badges" not in table_names:
        op.create_table(
            "reward_badges",
            sa.Column(
                "id",
                sa.Uuid(),
                nullable=False,
                server_default=sa.text("gen_random_uuid()"),
            ),
            sa.Column("code", sa.String(length=50), nullable=False),
            sa.Column("title_en", sa.String(length=200), nullable=True),
            sa.Column("title_fr", sa.String(length=200), nullable=True),
            sa.Column("title_ar", sa.String(length=200), nullable=True),
            sa.Column("description_en", sa.Text(), nullable=True),
            sa.Column("description_fr", sa.Text(), nullable=True),
            sa.Column("description_ar", sa.Text(), nullable=True),
            sa.Column("icon", sa.String(length=500), nullable=True),
            sa.Column("criteria_type", sa.String(length=50), nullable=True),
            sa.Column("criteria_value", sa.Integer(), nullable=True),
            sa.Column(
                "display_order",
                sa.SmallInteger(),
                nullable=False,
                server_default=sa.text("0"),
            ),
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
            sa.CheckConstraint(
                "criteria_value IS NULL OR criteria_value >= 0",
                name="ck_reward_badges_criteria_value_non_negative",
            ),
            sa.CheckConstraint(
                "display_order >= 0",
                name="ck_reward_badges_display_order_non_negative",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("code", name="uq_reward_badges_code"),
        )
        op.create_index(
            "idx_reward_badges_display_order",
            "reward_badges",
            ["display_order"],
        )
        return

    columns = {column["name"] for column in inspector.get_columns("reward_badges")}
    indexes = {index["name"] for index in inspector.get_indexes("reward_badges")}

    if "updated_at" not in columns:
        op.add_column(
            "reward_badges",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("now()"),
            ),
        )

    op.alter_column(
        "reward_badges",
        "title_en",
        existing_type=sa.String(length=200),
        nullable=True,
    )
    op.alter_column(
        "reward_badges",
        "title_fr",
        existing_type=sa.String(length=200),
        nullable=True,
    )
    op.alter_column(
        "reward_badges",
        "title_ar",
        existing_type=sa.String(length=200),
        nullable=True,
    )
    op.alter_column(
        "reward_badges",
        "criteria_type",
        existing_type=sa.String(length=50),
        nullable=True,
    )
    op.alter_column(
        "reward_badges",
        "criteria_value",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "reward_badges",
        "display_order",
        existing_type=sa.Integer(),
        type_=sa.SmallInteger(),
        nullable=False,
        existing_nullable=False,
    )

    if "idx_reward_badges_active_order" in indexes:
        op.drop_index("idx_reward_badges_active_order", table_name="reward_badges")

    if "idx_reward_badges_display_order" not in indexes:
        op.create_index(
            "idx_reward_badges_display_order",
            "reward_badges",
            ["display_order"],
        )


def downgrade() -> None:
    op.drop_index("idx_reward_badges_display_order", table_name="reward_badges")
    op.drop_table("reward_badges")
