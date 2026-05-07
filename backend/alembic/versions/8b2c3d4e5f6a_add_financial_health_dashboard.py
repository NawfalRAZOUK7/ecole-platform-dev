"""G36a - financial health dashboard models.

Revision ID: 8b2c3d4e5f6a
Revises: 7a1b2c3d4e5f
Create Date: 2026-04-05
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b2c3d4e5f6a"
down_revision: Union[str, None] = "7a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retention_metrics",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_from", sa.String(length=10), nullable=False),
        sa.Column("academic_year_to", sa.String(length=10), nullable=False),
        sa.Column("total_students_start", sa.Integer(), nullable=False),
        sa.Column("total_students_end", sa.Integer(), nullable=False),
        sa.Column("retained", sa.Integer(), nullable=False),
        sa.Column(
            "new_enrollments",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "withdrawals",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("retention_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_students_start >= 0",
            name="ck_retention_metrics_total_students_start",
        ),
        sa.CheckConstraint(
            "total_students_end >= 0",
            name="ck_retention_metrics_total_students_end",
        ),
        sa.CheckConstraint("retained >= 0", name="ck_retention_metrics_retained"),
        sa.CheckConstraint(
            "new_enrollments >= 0",
            name="ck_retention_metrics_new_enrollments",
        ),
        sa.CheckConstraint(
            "withdrawals >= 0",
            name="ck_retention_metrics_withdrawals",
        ),
        sa.CheckConstraint(
            "retention_rate >= 0 AND retention_rate <= 100",
            name="ck_retention_metrics_retention_rate",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "academic_year_from",
            "academic_year_to",
            name="uq_retention_metrics_school_year_pair",
        ),
    )
    op.create_index(
        "ix_retention_metrics_school_id",
        "retention_metrics",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_retention_metrics_school_computed_at",
        "retention_metrics",
        ["school_id", "computed_at"],
        unique=False,
    )
    op.create_index(
        "idx_retention_metrics_school_year_pair",
        "retention_metrics",
        ["school_id", "academic_year_from", "academic_year_to"],
        unique=False,
    )

    op.create_table(
        "cashflow_forecasts",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("forecast_month", sa.Date(), nullable=False),
        sa.Column("expected_income", sa.Numeric(14, 2), nullable=False),
        sa.Column("expected_expenses", sa.Numeric(14, 2), nullable=False),
        sa.Column("actual_income", sa.Numeric(14, 2), nullable=True),
        sa.Column("actual_expenses", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expected_income >= 0",
            name="ck_cashflow_forecasts_expected_income",
        ),
        sa.CheckConstraint(
            "expected_expenses >= 0",
            name="ck_cashflow_forecasts_expected_expenses",
        ),
        sa.CheckConstraint(
            "actual_income IS NULL OR actual_income >= 0",
            name="ck_cashflow_forecasts_actual_income",
        ),
        sa.CheckConstraint(
            "actual_expenses IS NULL OR actual_expenses >= 0",
            name="ck_cashflow_forecasts_actual_expenses",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="ck_cashflow_forecasts_confidence_score",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "forecast_month",
            name="uq_cashflow_forecasts_school_month",
        ),
    )
    op.create_index(
        "ix_cashflow_forecasts_school_id",
        "cashflow_forecasts",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_cashflow_forecasts_school_month",
        "cashflow_forecasts",
        ["school_id", "forecast_month"],
        unique=False,
    )
    op.create_index(
        "idx_cashflow_forecasts_school_computed_at",
        "cashflow_forecasts",
        ["school_id", "computed_at"],
        unique=False,
    )

    op.create_table(
        "cost_per_student",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("total_operational_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_students", sa.Integer(), nullable=False),
        sa.Column("cost_per_student", sa.Numeric(10, 2), nullable=False),
        sa.Column("revenue_per_student", sa.Numeric(10, 2), nullable=False),
        sa.Column("margin_per_student", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_operational_cost >= 0",
            name="ck_cost_per_student_total_operational_cost",
        ),
        sa.CheckConstraint(
            "total_students > 0",
            name="ck_cost_per_student_total_students",
        ),
        sa.CheckConstraint(
            "cost_per_student >= 0",
            name="ck_cost_per_student_cost_per_student",
        ),
        sa.CheckConstraint(
            "revenue_per_student >= 0",
            name="ck_cost_per_student_revenue_per_student",
        ),
        sa.ForeignKeyConstraint(
            ["academic_year_id"],
            ["academic_years.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "academic_year_id",
            name="uq_cost_per_student_school_year",
        ),
    )
    op.create_index(
        "ix_cost_per_student_school_id",
        "cost_per_student",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_cost_per_student_school_year",
        "cost_per_student",
        ["school_id", "academic_year_id"],
        unique=False,
    )
    op.create_index(
        "idx_cost_per_student_school_computed_at",
        "cost_per_student",
        ["school_id", "computed_at"],
        unique=False,
    )

    op.create_table(
        "financial_snapshots",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("total_receivable", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_collected", sa.Numeric(14, 2), nullable=False),
        sa.Column("collection_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("overdue_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("overdue_count", sa.Integer(), nullable=False),
        sa.Column("avg_payment_delay_days", sa.Numeric(6, 2), nullable=True),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "total_receivable >= 0",
            name="ck_financial_snapshots_total_receivable",
        ),
        sa.CheckConstraint(
            "total_collected >= 0",
            name="ck_financial_snapshots_total_collected",
        ),
        sa.CheckConstraint(
            "collection_rate >= 0 AND collection_rate <= 100",
            name="ck_financial_snapshots_collection_rate",
        ),
        sa.CheckConstraint(
            "overdue_amount >= 0",
            name="ck_financial_snapshots_overdue_amount",
        ),
        sa.CheckConstraint(
            "overdue_count >= 0",
            name="ck_financial_snapshots_overdue_count",
        ),
        sa.CheckConstraint(
            "avg_payment_delay_days IS NULL OR avg_payment_delay_days >= 0",
            name="ck_financial_snapshots_avg_payment_delay_days",
        ),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "snapshot_date",
            name="uq_financial_snapshots_school_date",
        ),
    )
    op.create_index(
        "ix_financial_snapshots_school_id",
        "financial_snapshots",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_financial_snapshots_school_date",
        "financial_snapshots",
        ["school_id", "snapshot_date"],
        unique=False,
    )
    op.create_index(
        "idx_financial_snapshots_school_computed_at",
        "financial_snapshots",
        ["school_id", "computed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "idx_financial_snapshots_school_computed_at",
        table_name="financial_snapshots",
    )
    op.drop_index("idx_financial_snapshots_school_date", table_name="financial_snapshots")
    op.drop_index("ix_financial_snapshots_school_id", table_name="financial_snapshots")
    op.drop_table("financial_snapshots")

    op.drop_index(
        "idx_cost_per_student_school_computed_at",
        table_name="cost_per_student",
    )
    op.drop_index("idx_cost_per_student_school_year", table_name="cost_per_student")
    op.drop_index("ix_cost_per_student_school_id", table_name="cost_per_student")
    op.drop_table("cost_per_student")

    op.drop_index(
        "idx_cashflow_forecasts_school_computed_at",
        table_name="cashflow_forecasts",
    )
    op.drop_index(
        "idx_cashflow_forecasts_school_month",
        table_name="cashflow_forecasts",
    )
    op.drop_index("ix_cashflow_forecasts_school_id", table_name="cashflow_forecasts")
    op.drop_table("cashflow_forecasts")

    op.drop_index(
        "idx_retention_metrics_school_year_pair",
        table_name="retention_metrics",
    )
    op.drop_index(
        "idx_retention_metrics_school_computed_at",
        table_name="retention_metrics",
    )
    op.drop_index("ix_retention_metrics_school_id", table_name="retention_metrics")
    op.drop_table("retention_metrics")
