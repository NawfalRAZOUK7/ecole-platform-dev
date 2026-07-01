"""Restore upload_sessions after security migration.

Revision ID: 9d2b3c4e5f6a
Revises: 8c1a2b3d4e5f
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op


revision = "9d2b3c4e5f6a"
down_revision = "8c1a2b3d4e5f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS upload_sessions (
            upload_state varchar(20) NOT NULL DEFAULT 'uploading',
            kind varchar(30) NOT NULL,
            object_key text NOT NULL,
            mime_type text NOT NULL,
            size_bytes bigint NOT NULL,
            sha256 varchar(64),
            school_id uuid NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            uploader_id uuid REFERENCES users(id) ON DELETE SET NULL,
            scope_data jsonb NOT NULL DEFAULT '{}'::jsonb,
            expires_at timestamptz NOT NULL,
            completed_at timestamptz,
            scanned_at timestamptz,
            target_id uuid,
            target_kind text,
            error_message text,
            id uuid PRIMARY KEY,
            created_at timestamptz NOT NULL,
            updated_at timestamptz
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE upload_sessions IS "
        "'Phase 8: direct-to-MinIO upload lifecycle tracking'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_sessions_state "
        "ON upload_sessions (upload_state)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_sessions_school "
        "ON upload_sessions (school_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_sessions_uploader "
        "ON upload_sessions (uploader_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_upload_sessions_created "
        "ON upload_sessions (created_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_upload_sessions_created")
    op.execute("DROP INDEX IF EXISTS idx_upload_sessions_uploader")
    op.execute("DROP INDEX IF EXISTS idx_upload_sessions_school")
    op.execute("DROP INDEX IF EXISTS idx_upload_sessions_state")
    op.execute("DROP TABLE IF EXISTS upload_sessions")
