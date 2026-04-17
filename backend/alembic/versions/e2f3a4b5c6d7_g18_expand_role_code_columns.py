"""G18 — Expand IAM role code columns for CONTENT_MGR.

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-03-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "d1e2f3a4b5c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_vw_user_permissions() -> None:
    op.execute(
        sa.text("""
        CREATE OR REPLACE VIEW vw_user_permissions AS
        SELECT
            u.id AS user_id,
            u.email,
            u.full_name,
            u.status AS user_status,
            u.school_id,
            m.role_code,
            m.status AS membership_status,
            m.created_at AS membership_since
        FROM users u
        INNER JOIN memberships m ON m.user_id = u.id
        WHERE m.status = 'active'
          AND u.status = 'active'
    """)
    )


def _create_vw_active_sessions() -> None:
    op.execute(
        sa.text("""
        CREATE OR REPLACE VIEW vw_active_sessions AS
        SELECT
            s.id AS session_id,
            s.user_id,
            u.email,
            u.full_name,
            u.school_id,
            m.role_code,
            s.source,
            s.correlation_id,
            s.created_at AS session_started_at,
            EXTRACT(EPOCH FROM (now() - s.created_at)) / 3600.0 AS hours_active
        FROM sessions s
        INNER JOIN users u ON u.id = s.user_id
        LEFT JOIN memberships m ON m.user_id = u.id AND m.status = 'active'
        WHERE s.revoke_at IS NULL
    """)
    )


def upgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS vw_active_sessions"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_user_permissions"))

    op.alter_column(
        "memberships",
        "role_code",
        existing_type=sa.String(length=10),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.alter_column(
        "invitation_codes",
        "role_target",
        existing_type=sa.String(length=10),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    _create_vw_user_permissions()
    _create_vw_active_sessions()


def downgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS vw_active_sessions"))
    op.execute(sa.text("DROP VIEW IF EXISTS vw_user_permissions"))

    op.alter_column(
        "invitation_codes",
        "role_target",
        existing_type=sa.String(length=20),
        type_=sa.String(length=10),
        existing_nullable=False,
    )
    op.alter_column(
        "memberships",
        "role_code",
        existing_type=sa.String(length=20),
        type_=sa.String(length=10),
        existing_nullable=False,
    )
    _create_vw_user_permissions()
    _create_vw_active_sessions()
