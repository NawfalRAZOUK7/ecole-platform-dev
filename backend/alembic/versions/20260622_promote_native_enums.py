"""Promote closed-set string columns to native PostgreSQL enums.

Queued item #1 from ``BACKEND_DB_AUDIT.md`` §9. The NOT VALID CHECK constraints
added in 618/619/620 have pinned the four closed vocabularies; this migration
promotes them to native PG enums (precedent: ``1c42d3e4f5a6``), matching the
project's other 40+ ``*_enum`` columns.

Enums created and the columns converted:

* ``difficulty_enum``   (EASY, MEDIUM, HARD)
    game_configs, activities, quizzes, question_bank_items
* ``language_enum``     (fr, ar, en)
    content_items, quizzes, micro_resources, school_applications
* ``currency_enum``     (MAD, EUR, USD)
    invoices, fee_structures, micro_budgets, budget_allocations,
    budget_requests, cashflow_forecasts, cost_per_student,
    financial_snapshots, micro_payments
* ``school_cycle_enum`` (maternelle, primaire, college, lycee, informel)
    classes.cycle

The per-table CHECK constraints from 618/619/620 are redundant once the column
is a native enum (the enum type enforces the domain), so they are dropped here
and re-created ``NOT VALID`` on downgrade. ``classes.level_band`` and the quiz
``subject``/``level_band`` CHECKs are intentionally left in place — those stay
String+CHECK (shared, open-ish vocabularies), per the audit.

The only DB view that depends on a converted column is ``vw_invoice_balance``
(selects ``invoices.currency``); it is dropped before the conversion and
recreated afterwards with the exact definition from ``1c42d3e4f5a6``. Plain
b-tree indexes that include a converted column (e.g.
``idx_content_items_type_level_lang``, ``idx_qb_school_difficulty``,
``idx_micro_resources_type_language_age``) are rebuilt automatically by
``ALTER COLUMN ... TYPE`` and need no manual handling.

Column DEFAULTs in this schema are Python-side (SQLAlchemy ``default=``), not DB
``server_default``, so most columns have no DEFAULT clause to manage. The
catalog-driven ``_load_string_defaults``/``_restore_defaults`` helpers still run
defensively: any server-side default that does exist is dropped before the type
swap and restored with an enum cast — so the migration is correct either way.

Revision ID: 20260622_promote_native_enums
Revises: 20260621_i18n_translations
Create Date: 2026-06-22
"""

from __future__ import annotations

import re
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260622_promote_native_enums"
down_revision: Union[str, None] = "20260621_i18n_translations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# --- Enum types (kept in sync with app/models/taxonomy.py) -------------------

DIFFICULTY_ENUM = postgresql.ENUM(
    "EASY", "MEDIUM", "HARD", name="difficulty_enum"
)
LANGUAGE_ENUM = postgresql.ENUM("fr", "ar", "en", name="language_enum")
CURRENCY_ENUM = postgresql.ENUM("MAD", "EUR", "USD", name="currency_enum")
SCHOOL_CYCLE_ENUM = postgresql.ENUM(
    "maternelle", "primaire", "college", "lycee", "informel",
    name="school_cycle_enum",
)

ENUM_TYPES = [DIFFICULTY_ENUM, LANGUAGE_ENUM, CURRENCY_ENUM, SCHOOL_CYCLE_ENUM]


# --- Column conversions: (table, column, enum_type, existing String length) --

COLUMN_CONVERSIONS: list[tuple[str, str, postgresql.ENUM, int]] = [
    # difficulty
    ("game_configs", "difficulty", DIFFICULTY_ENUM, 20),
    ("activities", "difficulty", DIFFICULTY_ENUM, 20),
    ("quizzes", "difficulty", DIFFICULTY_ENUM, 20),
    ("question_bank_items", "difficulty", DIFFICULTY_ENUM, 20),
    # language
    ("content_items", "language", LANGUAGE_ENUM, 10),
    ("quizzes", "language", LANGUAGE_ENUM, 10),
    ("micro_resources", "language", LANGUAGE_ENUM, 5),
    ("school_applications", "language", LANGUAGE_ENUM, 10),
    # currency
    ("invoices", "currency", CURRENCY_ENUM, 3),
    ("fee_structures", "currency", CURRENCY_ENUM, 3),
    ("micro_budgets", "currency", CURRENCY_ENUM, 3),
    ("budget_allocations", "currency", CURRENCY_ENUM, 3),
    ("budget_requests", "currency", CURRENCY_ENUM, 3),
    ("cashflow_forecasts", "currency", CURRENCY_ENUM, 3),
    ("cost_per_student", "currency", CURRENCY_ENUM, 3),
    ("financial_snapshots", "currency", CURRENCY_ENUM, 3),
    ("micro_payments", "currency", CURRENCY_ENUM, 3),
    # cycle
    ("classes", "cycle", SCHOOL_CYCLE_ENUM, 20),
]


# --- CHECK constraints superseded by the native enum -------------------------
# (table, column, constraint_name, allowed_values) — dropped on upgrade,
# recreated NOT VALID on downgrade (restores the post-620 schema contract).

_DIFFICULTY_VALUES = ("EASY", "MEDIUM", "HARD")
_LANGUAGE_VALUES = ("fr", "ar", "en")
_CURRENCY_VALUES = ("MAD", "EUR", "USD")
_CYCLE_VALUES = ("maternelle", "primaire", "college", "lycee", "informel")

CHECK_CONSTRAINTS: list[tuple[str, str, str, tuple[str, ...]]] = [
    ("game_configs", "difficulty", "ck_game_configs_difficulty", _DIFFICULTY_VALUES),
    ("activities", "difficulty", "ck_activities_difficulty", _DIFFICULTY_VALUES),
    ("quizzes", "difficulty", "ck_quizzes_difficulty", _DIFFICULTY_VALUES),
    (
        "question_bank_items",
        "difficulty",
        "ck_question_bank_items_difficulty",
        _DIFFICULTY_VALUES,
    ),
    ("content_items", "language", "ck_content_items_language", _LANGUAGE_VALUES),
    ("quizzes", "language", "ck_quizzes_language", _LANGUAGE_VALUES),
    ("micro_resources", "language", "ck_micro_resources_language", _LANGUAGE_VALUES),
    (
        "school_applications",
        "language",
        "ck_school_applications_language",
        _LANGUAGE_VALUES,
    ),
    ("invoices", "currency", "ck_invoices_currency", _CURRENCY_VALUES),
    ("fee_structures", "currency", "ck_fee_structures_currency", _CURRENCY_VALUES),
    ("micro_budgets", "currency", "ck_micro_budgets_currency", _CURRENCY_VALUES),
    (
        "budget_allocations",
        "currency",
        "ck_budget_allocations_currency",
        _CURRENCY_VALUES,
    ),
    ("budget_requests", "currency", "ck_budget_requests_currency", _CURRENCY_VALUES),
    (
        "cashflow_forecasts",
        "currency",
        "ck_cashflow_forecasts_currency",
        _CURRENCY_VALUES,
    ),
    ("cost_per_student", "currency", "ck_cost_per_student_currency", _CURRENCY_VALUES),
    (
        "financial_snapshots",
        "currency",
        "ck_financial_snapshots_currency",
        _CURRENCY_VALUES,
    ),
    ("micro_payments", "currency", "ck_micro_payments_currency", _CURRENCY_VALUES),
    ("classes", "cycle", "ck_classes_cycle", _CYCLE_VALUES),
]


# --- Dependent view (selects invoices.currency) ------------------------------
# Verbatim from 1c42d3e4f5a6 (the live definition). Dropped before converting
# invoices.currency and recreated afterwards.

VW_INVOICE_BALANCE_SQL = sa.text(
    """
    CREATE OR REPLACE VIEW vw_invoice_balance AS
    SELECT
        inv.id AS invoice_id,
        inv.school_id,
        inv.parent_id,
        u.full_name AS parent_name,
        inv.status AS invoice_status,
        inv.total_amount,
        inv.currency,
        inv.issued_date,
        inv.due_date,
        COALESCE(pay.paid_amount, 0) AS paid_amount,
        inv.total_amount - COALESCE(pay.paid_amount, 0) AS balance_due,
        COALESCE(pay.attempt_count, 0) AS payment_attempts,
        pay.last_attempt_at
    FROM invoices inv
    INNER JOIN users u ON u.id = inv.parent_id
    LEFT JOIN LATERAL (
        SELECT
            COUNT(*) AS attempt_count,
            SUM(CASE WHEN pa.status = 'paid' THEN inv.total_amount ELSE 0 END) AS paid_amount,
            MAX(pa.created_at) AS last_attempt_at
        FROM payment_attempts pa
        WHERE pa.invoice_id = inv.id
    ) pay ON true
    """
)

DEFAULT_LITERAL_RE = re.compile(r"'((?:[^']|'')*)'")


def _in(values: Sequence[str]) -> str:
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def _drop_check_constraints() -> None:
    for table_name, _column, constraint_name, _values in CHECK_CONSTRAINTS:
        op.execute(
            f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}"'
        )


def _create_check_constraints() -> None:
    for table_name, column_name, constraint_name, values in CHECK_CONSTRAINTS:
        op.execute(
            f"""
            ALTER TABLE "{table_name}"
            ADD CONSTRAINT "{constraint_name}"
            CHECK ({column_name} IS NULL OR {column_name} IN ({_in(values)}))
            NOT VALID
            """
        )


def _load_string_defaults(
    bind, conversions: list[tuple[str, str, postgresql.ENUM, int]]
) -> dict[tuple[str, str], str]:
    """Read + drop any server-side DEFAULT so the column type can be swapped."""
    defaults: dict[tuple[str, str], str] = {}
    for table_name, column_name, _enum, _length in conversions:
        default_expr = bind.execute(
            sa.text(
                """
                SELECT column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                  AND column_name = :column_name
                """
            ),
            {"table_name": table_name, "column_name": column_name},
        ).scalar_one_or_none()
        if not default_expr:
            continue
        match = DEFAULT_LITERAL_RE.search(default_expr)
        if not match:
            continue
        defaults[(table_name, column_name)] = match.group(1).replace("''", "'")
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP DEFAULT'
            )
        )
    return defaults


def _restore_defaults(
    defaults: dict[tuple[str, str], str],
    *,
    use_enum_casts: bool,
) -> None:
    enum_by_col = {
        (table_name, column_name): enum_type
        for table_name, column_name, enum_type, _length in COLUMN_CONVERSIONS
    }
    for (table_name, column_name), default_value in defaults.items():
        if use_enum_casts:
            enum_type = enum_by_col[(table_name, column_name)]
            # The column VALUES were case-normalized (migration 618), but a legacy
            # server-side DEFAULT clause may not have been (e.g. game_configs had
            # difficulty DEFAULT 'easy'). Coerce the default to the matching enum
            # member case-insensitively so 'easy' -> 'EASY'.
            coerced = next(
                (v for v in enum_type.enums if v.lower() == default_value.lower()),
                default_value,
            )
            escaped = coerced.replace("'", "''")
            default_sql = f"'{escaped}'::{enum_type.name}"
        else:
            escaped = default_value.replace("'", "''")
            default_sql = f"'{escaped}'"
        op.execute(
            sa.text(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" '
                f"SET DEFAULT {default_sql}"
            )
        )


def upgrade() -> None:
    bind = op.get_bind()

    # 1) Drop the dependent view + the redundant CHECKs that would otherwise
    #    block / duplicate the native enum.
    op.execute(sa.text("DROP VIEW IF EXISTS vw_invoice_balance"))
    _drop_check_constraints()

    # 2) Stash + drop any server-side defaults, then create the enum types.
    defaults = _load_string_defaults(bind, COLUMN_CONVERSIONS)
    for enum_type in ENUM_TYPES:
        enum_type.create(bind, checkfirst=False)

    # 3) Convert each column String -> native enum.
    for table_name, column_name, enum_type, length in COLUMN_CONVERSIONS:
        op.alter_column(
            table_name,
            column_name,
            existing_type=sa.String(length=length),
            type_=enum_type,
            postgresql_using=f"{column_name}::text::{enum_type.name}",
        )

    # 4) Restore defaults (now enum-cast) + recreate the view.
    _restore_defaults(defaults, use_enum_casts=True)
    op.execute(VW_INVOICE_BALANCE_SQL)


def downgrade() -> None:
    bind = op.get_bind()

    op.execute(sa.text("DROP VIEW IF EXISTS vw_invoice_balance"))
    defaults = _load_string_defaults(bind, COLUMN_CONVERSIONS)

    # Convert each column back to String.
    for table_name, column_name, enum_type, length in reversed(COLUMN_CONVERSIONS):
        op.alter_column(
            table_name,
            column_name,
            existing_type=enum_type,
            type_=sa.String(length=length),
            postgresql_using=f"{column_name}::text",
        )

    _restore_defaults(defaults, use_enum_casts=False)

    for enum_type in reversed(ENUM_TYPES):
        enum_type.drop(bind, checkfirst=False)

    # Restore the post-620 schema contract: re-add the CHECKs + the view.
    _create_check_constraints()
    op.execute(VW_INVOICE_BALANCE_SQL)
