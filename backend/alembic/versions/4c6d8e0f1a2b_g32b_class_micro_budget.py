"""G32b - class micro-budget models.

Revision ID: 4c6d8e0f1a2b
Revises: 2e4f6a8b0c1d
Create Date: 2026-04-04
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4c6d8e0f1a2b"
down_revision: Union[str, None] = "2e4f6a8b0c1d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MICRO_BUDGET_STATUS_ENUM = postgresql.ENUM(
    "active",
    "frozen",
    "closed",
    name="micro_budget_status_enum",
    create_type=False,
)
BUDGET_ALLOCATION_STATUS_ENUM = postgresql.ENUM(
    "active",
    "exhausted",
    "frozen",
    name="budget_allocation_status_enum",
    create_type=False,
)
BUDGET_REQUEST_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    "cancelled",
    name="budget_request_status_enum",
    create_type=False,
)
BUDGET_TRANSACTION_TYPE_ENUM = postgresql.ENUM(
    "allocation",
    "expense",
    "refund",
    "adjustment",
    name="budget_transaction_type_enum",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()

    MICRO_BUDGET_STATUS_ENUM.create(bind, checkfirst=True)
    BUDGET_ALLOCATION_STATUS_ENUM.create(bind, checkfirst=True)
    BUDGET_REQUEST_STATUS_ENUM.create(bind, checkfirst=True)
    BUDGET_TRANSACTION_TYPE_ENUM.create(bind, checkfirst=True)

    op.create_table(
        "micro_budgets",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "allocated_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "remaining_amount",
            sa.Numeric(12, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column(
            "status",
            MICRO_BUDGET_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("total_amount >= 0", name="ck_micro_budgets_total_amount"),
        sa.CheckConstraint(
            "allocated_amount >= 0",
            name="ck_micro_budgets_allocated_amount",
        ),
        sa.CheckConstraint(
            "remaining_amount >= 0",
            name="ck_micro_budgets_remaining_amount",
        ),
        sa.CheckConstraint(
            "allocated_amount <= total_amount",
            name="ck_micro_budgets_allocated_lte_total",
        ),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_micro_budgets_school_year_status",
        "micro_budgets",
        ["school_id", "academic_year_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_micro_budgets_creator",
        "micro_budgets",
        ["created_by"],
        unique=False,
    )

    op.create_table(
        "budget_allocations",
        sa.Column("budget_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=True),
        sa.Column("teacher_id", sa.Uuid(), nullable=True),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "spent",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "remaining",
            sa.Numeric(10, 2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column("allocated_by", sa.Uuid(), nullable=False),
        sa.Column("allocated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            BUDGET_ALLOCATION_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'active'"),
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_budget_allocations_amount"),
        sa.CheckConstraint("spent >= 0", name="ck_budget_allocations_spent"),
        sa.CheckConstraint("remaining >= 0", name="ck_budget_allocations_remaining"),
        sa.CheckConstraint(
            "spent <= amount",
            name="ck_budget_allocations_spent_lte_amount",
        ),
        sa.CheckConstraint(
            "class_id IS NOT NULL OR teacher_id IS NOT NULL",
            name="ck_budget_allocations_target_present",
        ),
        sa.ForeignKeyConstraint(["allocated_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["budget_id"], ["micro_budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_budget_allocations_budget_status",
        "budget_allocations",
        ["budget_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_budget_allocations_class",
        "budget_allocations",
        ["class_id"],
        unique=False,
    )
    op.create_index(
        "idx_budget_allocations_teacher",
        "budget_allocations",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "budget_requests",
        sa.Column("allocation_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default=sa.text("'MAD'"),
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "status",
            BUDGET_REQUEST_STATUS_ENUM,
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_budget_requests_amount"),
        sa.ForeignKeyConstraint(["allocation_id"], ["budget_allocations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_budget_requests_allocation_status",
        "budget_requests",
        ["allocation_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_budget_requests_requester_status",
        "budget_requests",
        ["requester_id", "status"],
        unique=False,
    )

    op.create_table(
        "budget_transactions",
        sa.Column("allocation_id", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("transaction_type", BUDGET_TRANSACTION_TYPE_ENUM, nullable=False),
        sa.Column("description", sa.String(length=300), nullable=False),
        sa.Column("receipt_url", sa.String(length=500), nullable=True),
        sa.Column("recorded_by", sa.Uuid(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("amount > 0", name="ck_budget_transactions_amount"),
        sa.ForeignKeyConstraint(["allocation_id"], ["budget_allocations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["request_id"], ["budget_requests.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_budget_transactions_allocation_recorded",
        "budget_transactions",
        ["allocation_id", "recorded_at"],
        unique=False,
    )
    op.create_index(
        "idx_budget_transactions_request",
        "budget_transactions",
        ["request_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_budget_transactions_request", table_name="budget_transactions")
    op.drop_index(
        "idx_budget_transactions_allocation_recorded",
        table_name="budget_transactions",
    )
    op.drop_table("budget_transactions")

    op.drop_index("idx_budget_requests_requester_status", table_name="budget_requests")
    op.drop_index("idx_budget_requests_allocation_status", table_name="budget_requests")
    op.drop_table("budget_requests")

    op.drop_index("idx_budget_allocations_teacher", table_name="budget_allocations")
    op.drop_index("idx_budget_allocations_class", table_name="budget_allocations")
    op.drop_index(
        "idx_budget_allocations_budget_status",
        table_name="budget_allocations",
    )
    op.drop_table("budget_allocations")

    op.drop_index("idx_micro_budgets_creator", table_name="micro_budgets")
    op.drop_index(
        "idx_micro_budgets_school_year_status",
        table_name="micro_budgets",
    )
    op.drop_table("micro_budgets")

    bind = op.get_bind()
    BUDGET_TRANSACTION_TYPE_ENUM.drop(bind, checkfirst=True)
    BUDGET_REQUEST_STATUS_ENUM.drop(bind, checkfirst=True)
    BUDGET_ALLOCATION_STATUS_ENUM.drop(bind, checkfirst=True)
    MICRO_BUDGET_STATUS_ENUM.drop(bind, checkfirst=True)
