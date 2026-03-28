"""G27a — IAM impersonation, login history, and session limits.

Revision ID: 7b8c9d0e1f2a
Revises: 6a7b8c9d0e1f
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7b8c9d0e1f2a"
down_revision: Union[str, None] = "6a7b8c9d0e1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("impersonator_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_sessions_impersonator_id_users",
        "sessions",
        "users",
        ["impersonator_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_sessions_impersonator_id",
        "sessions",
        ["impersonator_id"],
        unique=False,
    )

    op.create_table(
        "login_history",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("device_name", sa.String(length=200), nullable=True),
        sa.Column("device_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=50), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=50), nullable=True),
        sa.Column(
            "is_new_device",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_login_history_user_created",
        "login_history",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_login_history_school",
        "login_history",
        ["school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_login_history_school", table_name="login_history")
    op.drop_index("idx_login_history_user_created", table_name="login_history")
    op.drop_table("login_history")

    op.drop_index("idx_sessions_impersonator_id", table_name="sessions")
    op.drop_constraint(
        "fk_sessions_impersonator_id_users",
        "sessions",
        type_="foreignkey",
    )
    op.drop_column("sessions", "impersonator_id")
