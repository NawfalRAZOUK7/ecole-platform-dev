"""G34a - MEN compliance checker models.

Revision ID: 6f0a1b2c3d4e
Revises: 5d8e9f0a1b2c
Create Date: 2026-04-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "6f0a1b2c3d4e"
down_revision: Union[str, None] = "5d8e9f0a1b2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "men_curricula",
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("grade", sa.String(length=20), nullable=False),
        sa.Column("subject", sa.String(length=100), nullable=False),
        sa.Column("academic_year", sa.String(length=10), nullable=False),
        sa.Column(
            "version",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'1.0'"),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "level",
            "grade",
            "subject",
            "academic_year",
            "version",
            name="uq_men_curricula_scope",
        ),
    )
    op.create_index(
        "idx_men_curricula_level_grade_subject",
        "men_curricula",
        ["level", "grade", "subject"],
        unique=False,
    )
    op.create_index(
        "idx_men_curricula_active_year",
        "men_curricula",
        ["is_active", "academic_year"],
        unique=False,
    )

    op.create_table(
        "men_objectives",
        sa.Column("curriculum_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title_fr", sa.String(length=500), nullable=False),
        sa.Column("title_ar", sa.String(length=500), nullable=False),
        sa.Column("description_fr", sa.Text(), nullable=True),
        sa.Column("trimester", sa.Integer(), nullable=False),
        sa.Column("unit_number", sa.Integer(), nullable=False),
        sa.Column(
            "is_mandatory",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("hours_recommended", sa.Numeric(6, 2), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("trimester >= 1", name="ck_men_objectives_trimester_min"),
        sa.CheckConstraint("trimester <= 3", name="ck_men_objectives_trimester_max"),
        sa.CheckConstraint("unit_number >= 1", name="ck_men_objectives_unit_number"),
        sa.CheckConstraint(
            "hours_recommended IS NULL OR hours_recommended >= 0",
            name="ck_men_objectives_hours_recommended",
        ),
        sa.CheckConstraint(
            "display_order >= 0",
            name="ck_men_objectives_display_order",
        ),
        sa.ForeignKeyConstraint(
            ["curriculum_id"],
            ["men_curricula.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "curriculum_id",
            "code",
            name="uq_men_objectives_curriculum_code",
        ),
    )
    op.create_index(
        "idx_men_objectives_curriculum_trimester",
        "men_objectives",
        ["curriculum_id", "trimester"],
        unique=False,
    )
    op.create_index(
        "idx_men_objectives_curriculum_order",
        "men_objectives",
        ["curriculum_id", "display_order"],
        unique=False,
    )

    op.create_table(
        "curriculum_mappings",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("objective_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=True),
        sa.Column("content_item_id", sa.Uuid(), nullable=True),
        sa.Column("mapped_by", sa.Uuid(), nullable=False),
        sa.Column("mapped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "coverage_percent",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("100"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "coverage_percent >= 0",
            name="ck_curriculum_mappings_coverage_percent_min",
        ),
        sa.CheckConstraint(
            "coverage_percent <= 100",
            name="ck_curriculum_mappings_coverage_percent_max",
        ),
        sa.CheckConstraint(
            "course_id IS NOT NULL OR content_item_id IS NOT NULL",
            name="ck_curriculum_mappings_target_present",
        ),
        sa.ForeignKeyConstraint(["content_item_id"], ["content_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["mapped_by"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["objective_id"],
            ["men_objectives.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "objective_id",
            "course_id",
            name="uq_curriculum_mappings_school_objective_course",
        ),
    )
    op.create_index(
        "idx_curriculum_mappings_school_objective",
        "curriculum_mappings",
        ["school_id", "objective_id"],
        unique=False,
    )
    op.create_index(
        "idx_curriculum_mappings_course",
        "curriculum_mappings",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "idx_curriculum_mappings_content_item",
        "curriculum_mappings",
        ["content_item_id"],
        unique=False,
    )

    op.create_table(
        "compliance_reports",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("curriculum_id", sa.Uuid(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_by", sa.Uuid(), nullable=False),
        sa.Column(
            "total_objectives",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "mapped_objectives",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "compliance_percent",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "unmapped_objectives",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("pdf_url", sa.String(length=500), nullable=True),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_objectives >= 0",
            name="ck_compliance_reports_total_objectives",
        ),
        sa.CheckConstraint(
            "mapped_objectives >= 0",
            name="ck_compliance_reports_mapped_objectives",
        ),
        sa.CheckConstraint(
            "mapped_objectives <= total_objectives",
            name="ck_compliance_reports_mapped_lte_total",
        ),
        sa.CheckConstraint(
            "compliance_percent >= 0",
            name="ck_compliance_reports_percent_min",
        ),
        sa.CheckConstraint(
            "compliance_percent <= 100",
            name="ck_compliance_reports_percent_max",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["curriculum_id"],
            ["men_curricula.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["generated_by"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_compliance_reports_school_year_curriculum",
        "compliance_reports",
        ["school_id", "academic_year_id", "curriculum_id"],
        unique=False,
    )
    op.create_index(
        "idx_compliance_reports_generated_by",
        "compliance_reports",
        ["generated_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_compliance_reports_generated_by",
        table_name="compliance_reports",
    )
    op.drop_index(
        "idx_compliance_reports_school_year_curriculum",
        table_name="compliance_reports",
    )
    op.drop_table("compliance_reports")

    op.drop_index(
        "idx_curriculum_mappings_content_item",
        table_name="curriculum_mappings",
    )
    op.drop_index(
        "idx_curriculum_mappings_course",
        table_name="curriculum_mappings",
    )
    op.drop_index(
        "idx_curriculum_mappings_school_objective",
        table_name="curriculum_mappings",
    )
    op.drop_table("curriculum_mappings")

    op.drop_index(
        "idx_men_objectives_curriculum_order",
        table_name="men_objectives",
    )
    op.drop_index(
        "idx_men_objectives_curriculum_trimester",
        table_name="men_objectives",
    )
    op.drop_table("men_objectives")

    op.drop_index(
        "idx_men_curricula_active_year",
        table_name="men_curricula",
    )
    op.drop_index(
        "idx_men_curricula_level_grade_subject",
        table_name="men_curricula",
    )
    op.drop_table("men_curricula")
