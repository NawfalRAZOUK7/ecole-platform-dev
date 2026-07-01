"""Add invoice and payment report enum values.

Revision ID: 8c1a2b3d4e5f
Revises: 5465fdab5ca4
Create Date: 2026-05-15
"""

from __future__ import annotations

from alembic import op


revision = "8c1a2b3d4e5f"
down_revision = "5465fdab5ca4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE report_type_enum ADD VALUE IF NOT EXISTS 'invoice_pdf'")
    op.execute("ALTER TYPE report_type_enum ADD VALUE IF NOT EXISTS 'payment_receipt'")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values without rebuilding the enum type.
    pass
