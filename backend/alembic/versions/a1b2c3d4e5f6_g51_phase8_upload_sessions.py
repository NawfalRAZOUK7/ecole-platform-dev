"""G51 — Phase 8: upload_sessions table for direct-to-MinIO uploads.

Revision ID: a1b2c3d4e5f6
Revises: 748989a9f381
Create Date: 2026-05-05

Single new table; no changes to existing tables.
Downgrade: drop_table (safe — no FK references from other tables).
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "748989a9f381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "upload_sessions",
        sa.Column("upload_state", sa.String(length=20), nullable=False),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=True),
        sa.Column("scope_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("target_kind", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        # TimestampMixin columns
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploader_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_upload_sessions_state",
        "upload_sessions",
        ["upload_state"],
        unique=False,
    )
    op.create_index(
        "idx_upload_sessions_school",
        "upload_sessions",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_upload_sessions_uploader",
        "upload_sessions",
        ["uploader_id"],
        unique=False,
    )
    op.create_index(
        "idx_upload_sessions_created",
        "upload_sessions",
        ["created_at"],
        unique=False,
    )

    op.execute(
        "COMMENT ON TABLE upload_sessions IS "
        "'Phase 8: direct-to-MinIO upload lifecycle tracking'"
    )

    # Default value for scope_data JSONB column
    op.execute(
        "ALTER TABLE upload_sessions "
        "ALTER COLUMN scope_data SET DEFAULT '{}'"
    )
    # Default value for upload_state
    op.execute(
        "ALTER TABLE upload_sessions "
        "ALTER COLUMN upload_state SET DEFAULT 'uploading'"
    )


def downgrade() -> None:
    op.drop_index("idx_upload_sessions_created", table_name="upload_sessions")
    op.drop_index("idx_upload_sessions_uploader", table_name="upload_sessions")
    op.drop_index("idx_upload_sessions_school", table_name="upload_sessions")
    op.drop_index("idx_upload_sessions_state", table_name="upload_sessions")
    op.drop_table("upload_sessions")
