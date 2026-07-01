"""Constrain currency (ISO-4217 subset) and language to canonical sets.

P1 — ``currency`` (money-integrity: a stray ``Mad``/`` MAD `` corrupts totals)
and ``language`` were free strings. Adds CHECK constraints matching
``Currency`` / ``Language`` in ``app/models/taxonomy.py``. ``NOT VALID`` so
existing rows are untouched and only new writes are enforced.

Revision ID: 20260620_currency_language
Revises: 20260619_class_level_band
Create Date: 2026-06-20
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "20260620_currency_language"
down_revision: Union[str, None] = "20260619_class_level_band"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CURRENCIES = ("MAD", "EUR", "USD")
_LANGUAGES = ("fr", "ar", "en")

_CURRENCY_TABLES = (
    "invoices", "fee_structures", "micro_budgets", "budget_allocations",
    "budget_requests", "cashflow_forecasts", "cost_per_student",
    "financial_snapshots", "micro_payments",
)
_LANGUAGE_TABLES = ("content_items", "quizzes", "micro_resources", "school_applications")


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def upgrade() -> None:
    for table in _CURRENCY_TABLES:
        op.execute(
            f"""
            ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_currency
            CHECK (currency IS NULL OR currency IN ({_in(_CURRENCIES)}))
            NOT VALID
            """
        )
    for table in _LANGUAGE_TABLES:
        op.execute(
            f"""
            ALTER TABLE {table}
            ADD CONSTRAINT ck_{table}_language
            CHECK (language IS NULL OR language IN ({_in(_LANGUAGES)}))
            NOT VALID
            """
        )


def downgrade() -> None:
    for table in _LANGUAGE_TABLES:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_language")
    for table in _CURRENCY_TABLES:
        op.execute(f"ALTER TABLE {table} DROP CONSTRAINT IF EXISTS ck_{table}_currency")
