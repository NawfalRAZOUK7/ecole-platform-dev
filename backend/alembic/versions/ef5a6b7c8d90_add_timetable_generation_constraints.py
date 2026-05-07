"""G29b — Timetable constraints and generation jobs.

Revision ID: ef5a6b7c8d90
Revises: de4f5a6b7c89
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ef5a6b7c8d90"
down_revision: Union[str, None] = "de4f5a6b7c89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "timetable_constraints",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("constraint_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column(
            "params",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "constraint_type IN ("
            "'teacher_unavailable',"
            "'room_capacity',"
            "'max_hours_per_day',"
            "'subject_hours_per_week',"
            "'no_consecutive_same_subject'"
            ")",
            name="ck_timetable_constraints_type",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tc_school_year",
        "timetable_constraints",
        ["school_id", "academic_year_id"],
        unique=False,
    )

    op.create_table(
        "timetable_generation_jobs",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "constraints_snapshot",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "result_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("result_slot_count", sa.Integer(), nullable=True),
        sa.Column("conflicts_found", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'applied')",
            name="ck_timetable_generation_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_tgj_school_year",
        "timetable_generation_jobs",
        ["school_id", "academic_year_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_tgj_school_year", table_name="timetable_generation_jobs")
    op.drop_table("timetable_generation_jobs")
    op.drop_index("idx_tc_school_year", table_name="timetable_constraints")
    op.drop_table("timetable_constraints")
