"""h2 difficulty adaptations table

Revision ID: a1b2c3d4e5f6
Revises: f6e5d4c3b2a1
Create Date: 2026-04-19 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "f6e5d4c3b2a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "difficulty_adaptations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("previous_difficulty", sa.String(20), nullable=False),
        sa.Column("new_difficulty", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_diff_adapt_student_subject",
        "difficulty_adaptations",
        ["student_id", "subject"],
    )


def downgrade() -> None:
    op.drop_index("idx_diff_adapt_student_subject", table_name="difficulty_adaptations")
    op.drop_table("difficulty_adaptations")
