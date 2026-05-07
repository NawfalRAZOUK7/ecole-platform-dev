"""G28a — Rubric engine models and assignment linkage.

Revision ID: 8c9d0e1f2a3b
Revises: 7b8c9d0e1f2a
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c9d0e1f2a3b"
down_revision: Union[str, None] = "7b8c9d0e1f2a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "rubrics",
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
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "total_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("20"),
        ),
        sa.Column(
            "is_template",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.CheckConstraint("total_points >= 0", name="ck_rubrics_total_points"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rubrics_school_teacher",
        "rubrics",
        ["school_id", "teacher_id"],
        unique=False,
    )

    op.create_table(
        "rubric_criteria",
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
            "rubric_id",
            sa.Uuid(),
            sa.ForeignKey("rubrics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "weight",
            sa.Float(),
            nullable=False,
            server_default=sa.text("1.0"),
        ),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.CheckConstraint("weight >= 0", name="ck_rubric_criteria_weight"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rubric_criteria_rubric",
        "rubric_criteria",
        ["rubric_id"],
        unique=False,
    )

    op.create_table(
        "rubric_levels",
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
            "criterion_id",
            sa.Uuid(),
            sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("points", sa.Float(), nullable=False),
        sa.Column(
            "position",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.CheckConstraint("points >= 0", name="ck_rubric_levels_points"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rubric_levels_criterion",
        "rubric_levels",
        ["criterion_id"],
        unique=False,
    )

    op.create_table(
        "rubric_scores",
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
            "submission_id",
            sa.Uuid(),
            sa.ForeignKey("submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "criterion_id",
            sa.Uuid(),
            sa.ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "level_id",
            sa.Uuid(),
            sa.ForeignKey("rubric_levels.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("points_awarded", sa.Float(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "points_awarded >= 0",
            name="ck_rubric_scores_points_awarded",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id",
            "criterion_id",
            name="uq_rubric_scores_sub_criterion",
        ),
    )
    op.create_index(
        "idx_rubric_scores_submission",
        "rubric_scores",
        ["submission_id"],
        unique=False,
    )

    op.add_column("assignments", sa.Column("rubric_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_assignments_rubric_id_rubrics",
        "assignments",
        "rubrics",
        ["rubric_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_assignments_rubric",
        "assignments",
        ["rubric_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_assignments_rubric", table_name="assignments")
    op.drop_constraint(
        "fk_assignments_rubric_id_rubrics",
        "assignments",
        type_="foreignkey",
    )
    op.drop_column("assignments", "rubric_id")

    op.drop_index("idx_rubric_scores_submission", table_name="rubric_scores")
    op.drop_table("rubric_scores")

    op.drop_index("idx_rubric_levels_criterion", table_name="rubric_levels")
    op.drop_table("rubric_levels")

    op.drop_index("idx_rubric_criteria_rubric", table_name="rubric_criteria")
    op.drop_table("rubric_criteria")

    op.drop_index("idx_rubrics_school_teacher", table_name="rubrics")
    op.drop_table("rubrics")
