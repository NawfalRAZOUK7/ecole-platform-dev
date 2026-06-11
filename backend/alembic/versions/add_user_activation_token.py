"""Add user activation token (set-password link for approved onboarding owners).

When a SuperAdmin approves an application, the owner account is created in an
INACTIVE state with a one-time activation token; the owner sets their password
via /activate?token=… which flips them to ACTIVE.

Additive, nullable — existing users unaffected.

Revision ID: add_user_activation_token
Revises: add_onboarding_applications
Create Date: 2026-06-05 00:40:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "add_user_activation_token"
down_revision = "add_onboarding_applications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("activation_token_hash", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "activation_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index(
        "idx_users_activation_token",
        "users",
        ["activation_token_hash"],
    )


def downgrade() -> None:
    op.drop_index("idx_users_activation_token", table_name="users")
    op.drop_column("users", "activation_expires_at")
    op.drop_column("users", "activation_token_hash")
