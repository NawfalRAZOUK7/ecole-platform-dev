"""G29a — Attendance analytics alerts.

Revision ID: de4f5a6b7c89
Revises: cd3e4f5a6b78
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "de4f5a6b7c89"
down_revision: Union[str, None] = "cd3e4f5a6b78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attendance_alerts",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("period_id", sa.Uuid(), nullable=False),
        sa.Column("absence_count", sa.Integer(), nullable=False),
        sa.Column("total_sessions", sa.Integer(), nullable=False),
        sa.Column("absence_rate", sa.Float(), nullable=False),
        sa.Column("threshold_exceeded", sa.String(length=20), nullable=False),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "absence_count >= 0",
            name="ck_attendance_alerts_absence_count",
        ),
        sa.CheckConstraint(
            "total_sessions >= 0",
            name="ck_attendance_alerts_total_sessions",
        ),
        sa.CheckConstraint(
            "absence_rate >= 0 AND absence_rate <= 1",
            name="ck_attendance_alerts_absence_rate",
        ),
        sa.CheckConstraint(
            "threshold_exceeded IN ('warning', 'critical')",
            name="ck_attendance_alerts_threshold",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["period_id"],
            ["periods.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "period_id",
            "threshold_exceeded",
            name="uq_aa_student_period_threshold",
        ),
    )
    op.create_index(
        "idx_attendance_alerts_school",
        "attendance_alerts",
        ["school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_attendance_alerts_school", table_name="attendance_alerts")
    op.drop_table("attendance_alerts")
