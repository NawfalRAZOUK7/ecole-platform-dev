"""g40 add residual FK indexes

Revision ID: d4a1f0c8b2e7
Revises: c9d5e3f7a1b4
Create Date: 2026-04-05 20:33:00.000000
"""

from __future__ import annotations

from alembic import op


# revision identifiers, used by Alembic.
revision = "d4a1f0c8b2e7"
down_revision = "c9d5e3f7a1b4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_enrollments_school_id ON enrollments (school_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_memberships_user_id ON memberships (user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_school_id ON sessions (school_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_submissions_assignment_id ON submissions (assignment_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_submissions_assignment_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_school_id")
    op.execute("DROP INDEX IF EXISTS idx_memberships_user_id")
    op.execute("DROP INDEX IF EXISTS idx_enrollments_school_id")
