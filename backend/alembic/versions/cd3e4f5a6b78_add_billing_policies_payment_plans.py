"""G27b — Billing sibling discounts, late fees, and payment plans.

Revision ID: cd3e4f5a6b78
Revises: bc2d3e4f5a67
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cd3e4f5a6b78"
down_revision: Union[str, None] = "bc2d3e4f5a67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sibling_discount_policies",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "second_child_percent",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("10.00"),
        ),
        sa.Column(
            "third_child_percent",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("20.00"),
        ),
        sa.Column(
            "fourth_plus_percent",
            sa.Numeric(5, 2),
            nullable=False,
            server_default=sa.text("30.00"),
        ),
        sa.Column(
            "apply_to_oldest_first",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "second_child_percent >= 0 AND second_child_percent <= 100",
            name="ck_sibling_discount_second_percent",
        ),
        sa.CheckConstraint(
            "third_child_percent >= 0 AND third_child_percent <= 100",
            name="ck_sibling_discount_third_percent",
        ),
        sa.CheckConstraint(
            "fourth_plus_percent >= 0 AND fourth_plus_percent <= 100",
            name="ck_sibling_discount_fourth_percent",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id"),
    )
    op.create_index(
        "idx_sdp_school",
        "sibling_discount_policies",
        ["school_id"],
        unique=False,
    )

    op.create_table(
        "late_fee_policies",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column(
            "enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "fee_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'fixed'"),
        ),
        sa.Column(
            "amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column(
            "frequency",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'once'"),
        ),
        sa.Column(
            "grace_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("5"),
        ),
        sa.Column("max_fee", sa.Numeric(12, 2), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "fee_type IN ('fixed', 'percent')",
            name="ck_late_fee_policies_type",
        ),
        sa.CheckConstraint(
            "frequency IN ('once', 'daily', 'weekly')",
            name="ck_late_fee_policies_frequency",
        ),
        sa.CheckConstraint("amount >= 0", name="ck_late_fee_policies_amount"),
        sa.CheckConstraint(
            "grace_days >= 0",
            name="ck_late_fee_policies_grace_days",
        ),
        sa.CheckConstraint(
            "max_fee IS NULL OR max_fee >= 0",
            name="ck_late_fee_policies_max_fee",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id"),
    )
    op.create_index(
        "idx_late_fee_policies_school",
        "late_fee_policies",
        ["school_id"],
        unique=False,
    )

    op.create_table(
        "payment_plans",
        sa.Column("invoice_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("total_installments", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'completed', 'canceled')",
            name="ck_payment_plans_status",
        ),
        sa.CheckConstraint(
            "total_installments > 0",
            name="ck_payment_plans_total_installments",
        ),
        sa.ForeignKeyConstraint(
            ["invoice_id"],
            ["invoices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_payment_plans_school",
        "payment_plans",
        ["school_id"],
        unique=False,
    )
    op.create_index(
        "idx_payment_plans_invoice",
        "payment_plans",
        ["invoice_id"],
        unique=False,
    )

    op.create_table(
        "installments",
        sa.Column("plan_id", sa.Uuid(), nullable=False),
        sa.Column("installment_number", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount >= 0", name="ck_installments_amount"),
        sa.CheckConstraint(
            "installment_number > 0",
            name="ck_installments_number",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'paid', 'overdue')",
            name="ck_installments_status",
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["payment_plans.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "plan_id",
            "installment_number",
            name="uq_installments_plan_number",
        ),
    )
    op.create_index(
        "idx_installments_plan",
        "installments",
        ["plan_id"],
        unique=False,
    )
    op.create_index(
        "idx_installments_due_status",
        "installments",
        ["due_date", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_installments_due_status", table_name="installments")
    op.drop_index("idx_installments_plan", table_name="installments")
    op.drop_table("installments")

    op.drop_index("idx_payment_plans_invoice", table_name="payment_plans")
    op.drop_index("idx_payment_plans_school", table_name="payment_plans")
    op.drop_table("payment_plans")

    op.drop_index("idx_late_fee_policies_school", table_name="late_fee_policies")
    op.drop_table("late_fee_policies")

    op.drop_index("idx_sdp_school", table_name="sibling_discount_policies")
    op.drop_table("sibling_discount_policies")
