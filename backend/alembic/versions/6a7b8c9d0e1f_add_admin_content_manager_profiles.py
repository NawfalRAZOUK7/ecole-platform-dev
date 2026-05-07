"""G26 — OOP admin and content manager profile tables.

Revision ID: 6a7b8c9d0e1f
Revises: 5f6a7b8c9d0e
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6a7b8c9d0e1f"
down_revision: Union[str, None] = "5f6a7b8c9d0e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_profiles",
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
            unique=True,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("management_level", sa.String(length=50), nullable=True),
        sa.Column(
            "can_approve_budgets",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_admin_profiles_user",
        "admin_profiles",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_admin_profiles_school",
        "admin_profiles",
        ["school_id"],
        unique=False,
    )

    op.create_table(
        "content_manager_profiles",
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
            unique=True,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("specialization", sa.String(length=200), nullable=True),
        sa.Column("languages_managed", sa.Text(), nullable=True),
        sa.Column("approved_subjects", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_content_manager_profiles_user",
        "content_manager_profiles",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_content_manager_profiles_school",
        "content_manager_profiles",
        ["school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_content_manager_profiles_school",
        table_name="content_manager_profiles",
    )
    op.drop_index(
        "idx_content_manager_profiles_user",
        table_name="content_manager_profiles",
    )
    op.drop_table("content_manager_profiles")

    op.drop_index("idx_admin_profiles_school", table_name="admin_profiles")
    op.drop_index("idx_admin_profiles_user", table_name="admin_profiles")
    op.drop_table("admin_profiles")
