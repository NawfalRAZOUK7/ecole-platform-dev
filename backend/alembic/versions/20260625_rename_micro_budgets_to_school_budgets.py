"""Rename micro_budgets -> school_budgets (B3, naming §10).

``MicroBudget``/``micro_budgets`` is a *formal-school* budget envelope
(SchoolScoped), so the ``micro_`` prefix wrongly collides with the informal
``micro_school`` family. Per BACKEND_DB_AUDIT.md §10/§11 B3 the model is renamed
``SchoolBudget`` and the DB objects are renamed to match: table, the status enum
type, the four CHECK constraints, and the four indexes. The FK from
``budget_allocations.budget_id`` follows the table rename automatically.

Revision ID: 20260625_rename_school_budgets
Revises: 20260624_drop_payment_proofs
Create Date: 2026-06-25
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20260625_rename_school_budgets"
down_revision: Union[str, None] = "20260624_drop_payment_proofs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONSTRAINTS = (
    "total_amount",
    "allocated_amount",
    "remaining_amount",
    "allocated_lte_total",
)
_INDEXES = (
    "school_year_status",
    "creator",
    "academic_year_id",
    "created_by",
)


def upgrade() -> None:
    op.execute(
        "ALTER TYPE micro_budget_status_enum RENAME TO school_budget_status_enum"
    )
    op.rename_table("micro_budgets", "school_budgets")
    for suffix in _CONSTRAINTS:
        op.execute(
            f"ALTER TABLE school_budgets "
            f"RENAME CONSTRAINT ck_micro_budgets_{suffix} "
            f"TO ck_school_budgets_{suffix}"
        )
    for suffix in _INDEXES:
        op.execute(
            f"ALTER INDEX idx_micro_budgets_{suffix} "
            f"RENAME TO idx_school_budgets_{suffix}"
        )


def downgrade() -> None:
    for suffix in _INDEXES:
        op.execute(
            f"ALTER INDEX idx_school_budgets_{suffix} "
            f"RENAME TO idx_micro_budgets_{suffix}"
        )
    for suffix in _CONSTRAINTS:
        op.execute(
            f"ALTER TABLE school_budgets "
            f"RENAME CONSTRAINT ck_school_budgets_{suffix} "
            f"TO ck_micro_budgets_{suffix}"
        )
    op.rename_table("school_budgets", "micro_budgets")
    op.execute(
        "ALTER TYPE school_budget_status_enum RENAME TO micro_budget_status_enum"
    )
