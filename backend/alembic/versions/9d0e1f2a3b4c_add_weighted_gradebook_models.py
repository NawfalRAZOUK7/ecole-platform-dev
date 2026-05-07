"""G28b — Weighted gradebook models and assignment linkage.

Revision ID: 9d0e1f2a3b4c
Revises: 8c9d0e1f2a3b
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9d0e1f2a3b4c"
down_revision: Union[str, None] = "8c9d0e1f2a3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "grade_categories",
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
            "class_id",
            sa.Uuid(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "period_id",
            sa.Uuid(),
            sa.ForeignKey("periods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="ck_grade_categories_weight",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_grade_categories_class_period",
        "grade_categories",
        ["class_id", "period_id"],
        unique=False,
    )

    op.create_table(
        "student_period_averages",
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
            "student_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "class_id",
            sa.Uuid(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "period_id",
            sa.Uuid(),
            sa.ForeignKey("periods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("weighted_average", sa.Float(), nullable=False),
        sa.Column("mention", sa.String(length=30), nullable=False),
        sa.Column("class_rank", sa.Integer(), nullable=True),
        sa.Column("total_students", sa.Integer(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "class_id",
            "period_id",
            name="uq_spa_student_class_period",
        ),
    )
    op.create_index(
        "idx_spa_class_period",
        "student_period_averages",
        ["class_id", "period_id"],
        unique=False,
    )

    op.add_column(
        "assignments",
        sa.Column("grade_category_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_assignments_grade_category_id_grade_categories",
        "assignments",
        "grade_categories",
        ["grade_category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_assignments_grade_category",
        "assignments",
        ["grade_category_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_assignments_grade_category", table_name="assignments")
    op.drop_constraint(
        "fk_assignments_grade_category_id_grade_categories",
        "assignments",
        type_="foreignkey",
    )
    op.drop_column("assignments", "grade_category_id")

    op.drop_index("idx_spa_class_period", table_name="student_period_averages")
    op.drop_table("student_period_averages")

    op.drop_index("idx_grade_categories_class_period", table_name="grade_categories")
    op.drop_table("grade_categories")
