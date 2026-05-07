"""G28c — Question bank items.

Revision ID: ab1c2d3e4f56
Revises: 9d0e1f2a3b4c
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ab1c2d3e4f56"
down_revision: Union[str, None] = "9d0e1f2a3b4c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "question_bank_items",
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
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column(
            "teacher_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=True),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column(
            "question_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String(length=80)),
            nullable=False,
            server_default=sa.text("ARRAY[]::varchar[]"),
        ),
        sa.Column(
            "usage_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_qb_school_subject",
        "question_bank_items",
        ["school_id", "subject"],
        unique=False,
    )
    op.create_index(
        "idx_qb_school_difficulty",
        "question_bank_items",
        ["school_id", "difficulty"],
        unique=False,
    )
    op.create_index(
        "idx_qb_teacher",
        "question_bank_items",
        ["teacher_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_qb_teacher", table_name="question_bank_items")
    op.drop_index("idx_qb_school_difficulty", table_name="question_bank_items")
    op.drop_index("idx_qb_school_subject", table_name="question_bank_items")
    op.drop_table("question_bank_items")
