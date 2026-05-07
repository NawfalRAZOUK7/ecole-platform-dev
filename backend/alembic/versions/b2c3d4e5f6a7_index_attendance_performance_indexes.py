"""G51a — Attendance Performance Indexes.

Adds indexes on attendance_records and attendance_sessions to support
efficient absence trend queries for large classes (1000+ students).

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f7
Create Date: 2026-05-06
"""

from __future__ import annotations

from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # attendance_session_id: primary join column in all analytics queries; had no index
    op.create_index(
        "ix_attendance_records_session_id",
        "attendance_records",
        ["attendance_session_id"],
    )
    # status: used in absence rate calculations and trend filters
    op.create_index(
        "ix_attendance_records_status",
        "attendance_records",
        ["status"],
    )
    # compound (period_id, session_date): covers range scans in get_absence_trends
    op.create_index(
        "ix_attendance_sessions_period_date",
        "attendance_sessions",
        ["period_id", "session_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_sessions_period_date", table_name="attendance_sessions")
    op.drop_index("ix_attendance_records_status", table_name="attendance_records")
    op.drop_index("ix_attendance_records_session_id", table_name="attendance_records")
