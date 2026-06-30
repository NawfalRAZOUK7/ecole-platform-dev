"""Add optional student user link to micro enrollments.

Revision ID: 20260616_micro_student_user
Revises: add_user_activation_token
Create Date: 2026-06-16 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260616_micro_student_user"
down_revision = "add_user_activation_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "micro_enrollments",
        sa.Column("student_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_micro_enrollments_student_user_id_users",
        "micro_enrollments",
        "users",
        ["student_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_micro_enrollments_student_user",
        "micro_enrollments",
        ["student_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_micro_enrollments_student_user", table_name="micro_enrollments")
    op.drop_constraint(
        "fk_micro_enrollments_student_user_id_users",
        "micro_enrollments",
        type_="foreignkey",
    )
    op.drop_column("micro_enrollments", "student_user_id")
