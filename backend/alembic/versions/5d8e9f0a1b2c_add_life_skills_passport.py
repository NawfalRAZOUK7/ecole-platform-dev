"""G33a - life skills passport models.

Revision ID: 5d8e9f0a1b2c
Revises: 4c6d8e0f1a2b
Create Date: 2026-04-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5d8e9f0a1b2c"
down_revision: Union[str, None] = "4c6d8e0f1a2b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SKILL_PROGRESS_STATUS_ENUM = postgresql.ENUM(
    "locked",
    "in_progress",
    "unlocked",
    name="skill_progress_status_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    SKILL_PROGRESS_STATUS_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "skill_dimensions",
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name_fr", sa.String(length=200), nullable=False),
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=False),
        sa.Column("description_fr", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column(
            "display_order",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_skill_dimensions_display_order",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_skill_dimensions_code"),
    )
    op.create_index(
        "idx_skill_dimensions_active_order",
        "skill_dimensions",
        ["is_active", "display_order"],
        unique=False,
    )

    op.create_table(
        "skill_milestones",
        sa.Column("dimension_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name_fr", sa.String(length=200), nullable=False),
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column(
            "rule_config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("badge_icon", sa.String(length=50), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("level >= 1", name="ck_skill_milestones_level_min"),
        sa.CheckConstraint("level <= 5", name="ck_skill_milestones_level_max"),
        sa.ForeignKeyConstraint(
            ["dimension_id"],
            ["skill_dimensions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "dimension_id",
            "code",
            name="uq_skill_milestones_dimension_code",
        ),
    )
    op.create_index(
        "idx_skill_milestones_dimension_level",
        "skill_milestones",
        ["dimension_id", "level"],
        unique=False,
    )
    op.create_index(
        "idx_skill_milestones_active",
        "skill_milestones",
        ["is_active"],
        unique=False,
    )

    op.create_table(
        "skill_progress",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("milestone_id", sa.Uuid(), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "current_value",
            sa.Numeric(6, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "status",
            SKILL_PROGRESS_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'locked'"),
        ),
        sa.Column(
            "evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "current_value >= 0",
            name="ck_skill_progress_current_value_min",
        ),
        sa.CheckConstraint(
            "current_value <= 100",
            name="ck_skill_progress_current_value_max",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["milestone_id"], ["skill_milestones.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "milestone_id",
            "academic_year_id",
            name="uq_skill_progress_student_milestone_year",
        ),
    )
    op.create_index(
        "idx_skill_progress_school_student_status",
        "skill_progress",
        ["school_id", "student_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_skill_progress_year_milestone",
        "skill_progress",
        ["academic_year_id", "milestone_id"],
        unique=False,
    )

    op.create_table(
        "skill_passports",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pdf_url", sa.String(length=500), nullable=True),
        sa.Column(
            "total_milestones",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "unlocked_milestones",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "overall_score",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_milestones >= 0",
            name="ck_skill_passports_total_milestones",
        ),
        sa.CheckConstraint(
            "unlocked_milestones >= 0",
            name="ck_skill_passports_unlocked_milestones",
        ),
        sa.CheckConstraint(
            "unlocked_milestones <= total_milestones",
            name="ck_skill_passports_unlocked_lte_total",
        ),
        sa.CheckConstraint(
            "overall_score >= 0",
            name="ck_skill_passports_overall_score_min",
        ),
        sa.CheckConstraint(
            "overall_score <= 100",
            name="ck_skill_passports_overall_score_max",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "academic_year_id",
            name="uq_skill_passports_student_year",
        ),
    )
    op.create_index(
        "idx_skill_passports_school_student_year",
        "skill_passports",
        ["school_id", "student_id", "academic_year_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_skill_passports_school_student_year", table_name="skill_passports")
    op.drop_table("skill_passports")

    op.drop_index("idx_skill_progress_year_milestone", table_name="skill_progress")
    op.drop_index("idx_skill_progress_school_student_status", table_name="skill_progress")
    op.drop_table("skill_progress")

    op.drop_index("idx_skill_milestones_active", table_name="skill_milestones")
    op.drop_index("idx_skill_milestones_dimension_level", table_name="skill_milestones")
    op.drop_table("skill_milestones")

    op.drop_index("idx_skill_dimensions_active_order", table_name="skill_dimensions")
    op.drop_table("skill_dimensions")

    bind = op.get_bind()
    SKILL_PROGRESS_STATUS_ENUM.drop(bind, checkfirst=True)
