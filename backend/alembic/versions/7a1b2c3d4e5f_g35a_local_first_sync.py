"""G35a - local-first sync models.

Revision ID: 7a1b2c3d4e5f
Revises: 6f0a1b2c3d4e
Create Date: 2026-04-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "7a1b2c3d4e5f"
down_revision: Union[str, None] = "6f0a1b2c3d4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYNC_DEVICE_TYPE_ENUM = postgresql.ENUM(
    "local_server",
    "mobile",
    "browser",
    name="sync_device_type_enum",
    create_type=False,
)
SYNC_QUEUE_OPERATION_ENUM = postgresql.ENUM(
    "create",
    "update",
    "delete",
    name="sync_queue_operation_enum",
    create_type=False,
)
SYNC_QUEUE_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "synced",
    "conflict",
    "failed",
    name="sync_queue_status_enum",
    create_type=False,
)
SYNC_CONFLICT_RESOLUTION_ENUM = postgresql.ENUM(
    "pending",
    "client_wins",
    "server_wins",
    "manual",
    name="sync_conflict_resolution_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    SYNC_DEVICE_TYPE_ENUM.create(bind, checkfirst=True)
    SYNC_QUEUE_OPERATION_ENUM.create(bind, checkfirst=True)
    SYNC_QUEUE_STATUS_ENUM.create(bind, checkfirst=True)
    SYNC_CONFLICT_RESOLUTION_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "sync_devices",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("device_name", sa.String(length=200), nullable=False),
        sa.Column(
            "device_type",
            SYNC_DEVICE_TYPE_ENUM,
            nullable=False,
            server_default=sa.text("'browser'"),
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("firmware_version", sa.String(length=50), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sync_devices_school_id",
        "sync_devices",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_devices_school_active",
        "sync_devices",
        ["school_id", "is_active"],
        unique=False,
    )
    op.create_index(
        "idx_sync_devices_type_seen",
        "sync_devices",
        ["device_type", "last_seen_at"],
        unique=False,
    )

    op.create_table(
        "sync_queue",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "operation",
            SYNC_QUEUE_OPERATION_ENUM,
            nullable=False,
            server_default=sa.text("'create'"),
        ),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            SYNC_QUEUE_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "retry_count >= 0 AND retry_count <= 5",
            name="ck_sync_queue_retry_count",
        ),
        sa.ForeignKeyConstraint(["device_id"], ["sync_devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_queue_school_id", "sync_queue", ["school_id"], unique=False)
    op.create_index(
        "idx_sync_queue_device_status",
        "sync_queue",
        ["device_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_sync_queue_school_entity",
        "sync_queue",
        ["school_id", "entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_queue_pending_created_at",
        "sync_queue",
        ["status", "created_at"],
        unique=False,
    )

    op.create_table(
        "sync_conflicts",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("queue_item_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "client_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "server_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "resolution",
            SYNC_CONFLICT_RESOLUTION_ENUM,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["queue_item_id"], ["sync_queue.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sync_conflicts_school_id",
        "sync_conflicts",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_conflicts_school_resolution",
        "sync_conflicts",
        ["school_id", "resolution"],
        unique=False,
    )
    op.create_index(
        "idx_sync_conflicts_entity",
        "sync_conflicts",
        ["entity_type", "entity_id"],
        unique=False,
    )

    op.create_table(
        "sync_checkpoints",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("device_id", sa.Uuid(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_entity_type", sa.String(length=100), nullable=False),
        sa.Column("last_entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "records_synced",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "records_synced >= 0",
            name="ck_sync_checkpoints_records_synced",
        ),
        sa.ForeignKeyConstraint(["device_id"], ["sync_devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_sync_checkpoints_school_id",
        "sync_checkpoints",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_sync_checkpoints_device_last_sync",
        "sync_checkpoints",
        ["device_id", "last_sync_at"],
        unique=False,
    )
    op.create_index(
        "idx_sync_checkpoints_school_entity",
        "sync_checkpoints",
        ["school_id", "last_entity_type"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("idx_sync_checkpoints_school_entity", table_name="sync_checkpoints")
    op.drop_index("idx_sync_checkpoints_device_last_sync", table_name="sync_checkpoints")
    op.drop_index("ix_sync_checkpoints_school_id", table_name="sync_checkpoints")
    op.drop_table("sync_checkpoints")

    op.drop_index("idx_sync_conflicts_entity", table_name="sync_conflicts")
    op.drop_index("idx_sync_conflicts_school_resolution", table_name="sync_conflicts")
    op.drop_index("ix_sync_conflicts_school_id", table_name="sync_conflicts")
    op.drop_table("sync_conflicts")

    op.drop_index("idx_sync_queue_pending_created_at", table_name="sync_queue")
    op.drop_index("idx_sync_queue_school_entity", table_name="sync_queue")
    op.drop_index("idx_sync_queue_device_status", table_name="sync_queue")
    op.drop_index("ix_sync_queue_school_id", table_name="sync_queue")
    op.drop_table("sync_queue")

    op.drop_index("idx_sync_devices_type_seen", table_name="sync_devices")
    op.drop_index("idx_sync_devices_school_active", table_name="sync_devices")
    op.drop_index("ix_sync_devices_school_id", table_name="sync_devices")
    op.drop_table("sync_devices")

    SYNC_CONFLICT_RESOLUTION_ENUM.drop(bind, checkfirst=True)
    SYNC_QUEUE_STATUS_ENUM.drop(bind, checkfirst=True)
    SYNC_QUEUE_OPERATION_ENUM.drop(bind, checkfirst=True)
    SYNC_DEVICE_TYPE_ENUM.drop(bind, checkfirst=True)
