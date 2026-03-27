"""G22 — Phase 13 notification center.

Revision ID: 2c3d4e5f6a7b
Revises: 1b2c3d4e5f6a
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "2c3d4e5f6a7b"
down_revision: Union[str, None] = "1b2c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notifications",
        sa.Column(
            "category",
            sa.String(length=30),
            nullable=False,
            server_default="system",
        ),
    )
    op.add_column(
        "notifications",
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            server_default="normal",
        ),
    )
    op.add_column(
        "notifications",
        sa.Column("action_url", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("action_payload", JSONB, nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notifications",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_notifications_school_parent_created",
        "notifications",
        ["school_id", "parent_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_school_parent_read",
        "notifications",
        ["school_id", "parent_id", "read_at"],
        unique=False,
    )
    op.create_index(
        "idx_notifications_school_category_created",
        "notifications",
        ["school_id", "category", "created_at"],
        unique=False,
    )
    op.alter_column("notifications", "category", server_default=None)
    op.alter_column("notifications", "priority", server_default=None)

    op.create_table(
        "notification_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "digest_frequency",
            sa.String(length=20),
            nullable=False,
            server_default="off",
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "channel",
            "category",
            name="uq_notification_preferences_user_channel_category",
        ),
    )
    op.create_index(
        "idx_notification_preferences_school_user",
        "notification_preferences",
        ["school_id", "user_id"],
        unique=False,
    )

    op.create_table(
        "device_tokens",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=4096), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("device_name", sa.String(length=200), nullable=True),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        "idx_device_tokens_school_user",
        "device_tokens",
        ["school_id", "user_id"],
        unique=False,
    )
    op.create_index(
        "idx_device_tokens_last_active",
        "device_tokens",
        ["last_active_at"],
        unique=False,
    )

    op.add_column(
        "notification_deliveries",
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("clicked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "notification_deliveries",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_deliveries_school_channel_status",
        "notification_deliveries",
        ["school_id", "channel", "status"],
        unique=False,
    )
    op.alter_column("notification_deliveries", "retry_count", server_default=None)


def downgrade() -> None:
    op.drop_index(
        "idx_deliveries_school_channel_status",
        table_name="notification_deliveries",
    )
    op.drop_column("notification_deliveries", "last_error")
    op.drop_column("notification_deliveries", "provider_message_id")
    op.drop_column("notification_deliveries", "retry_count")
    op.drop_column("notification_deliveries", "clicked_at")
    op.drop_column("notification_deliveries", "delivered_at")

    op.drop_index("idx_device_tokens_last_active", table_name="device_tokens")
    op.drop_index("idx_device_tokens_school_user", table_name="device_tokens")
    op.drop_table("device_tokens")

    op.drop_index(
        "idx_notification_preferences_school_user",
        table_name="notification_preferences",
    )
    op.drop_table("notification_preferences")

    op.drop_index(
        "idx_notifications_school_category_created",
        table_name="notifications",
    )
    op.drop_index("idx_notifications_school_parent_read", table_name="notifications")
    op.drop_index(
        "idx_notifications_school_parent_created",
        table_name="notifications",
    )
    op.drop_column("notifications", "deleted_at")
    op.drop_column("notifications", "read_at")
    op.drop_column("notifications", "action_payload")
    op.drop_column("notifications", "action_url")
    op.drop_column("notifications", "priority")
    op.drop_column("notifications", "category")
