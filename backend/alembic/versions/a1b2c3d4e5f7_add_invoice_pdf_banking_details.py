"""G50E — Invoice PDF Banking Details & TVA Fields.

Adds banking, TVA, and branding fields to schools table for invoice PDF generation.
Adds TVA breakdown fields to invoice_items table.

Revision ID: a1b2c3d4e5f7
Revises: 8670b612eb3e
Create Date: 2026-05-05
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f7"
down_revision = "8670b612eb3e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- schools table: banking details --
    op.add_column("schools", sa.Column("rib", sa.String(50), nullable=True))
    op.add_column("schools", sa.Column("iban", sa.String(34), nullable=True))
    op.add_column("schools", sa.Column("bic", sa.String(11), nullable=True))
    op.add_column("schools", sa.Column("bank_name", sa.String(255), nullable=True))

    # -- schools table: TVA compliance fields --
    op.add_column("schools", sa.Column("tva_number", sa.String(50), nullable=True))
    op.add_column("schools", sa.Column("tax_id", sa.String(50), nullable=True))

    # -- schools table: branding fields --
    op.add_column("schools", sa.Column("brand_color", sa.String(7), nullable=True))
    op.add_column("schools", sa.Column("footer_text", sa.Text(), nullable=True))
    op.add_column("schools", sa.Column("stamp_image_url", sa.Text(), nullable=True))
    op.add_column("schools", sa.Column("signature_image_url", sa.Text(), nullable=True))

    # -- invoice_items table: TVA breakdown fields --
    op.add_column(
        "invoice_items",
        sa.Column("tva_rate", sa.Numeric(5, 2), nullable=True, server_default=sa.text("0.00")),
    )
    op.add_column(
        "invoice_items",
        sa.Column("tva_amount", sa.Numeric(12, 2), nullable=True, server_default=sa.text("0.00")),
    )
    op.add_column(
        "invoice_items",
        sa.Column("amount_ht", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
    )
    op.add_column(
        "invoice_items",
        sa.Column("amount_ttc", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
    )


def downgrade() -> None:
    # -- invoice_items table: drop TVA fields --
    op.drop_column("invoice_items", "amount_ttc")
    op.drop_column("invoice_items", "amount_ht")
    op.drop_column("invoice_items", "tva_amount")
    op.drop_column("invoice_items", "tva_rate")

    # -- schools table: drop branding fields --
    op.drop_column("schools", "signature_image_url")
    op.drop_column("schools", "stamp_image_url")
    op.drop_column("schools", "footer_text")
    op.drop_column("schools", "brand_color")

    # -- schools table: drop TVA fields --
    op.drop_column("schools", "tax_id")
    op.drop_column("schools", "tva_number")

    # -- schools table: drop banking fields --
    op.drop_column("schools", "bank_name")
    op.drop_column("schools", "bic")
    op.drop_column("schools", "iban")
    op.drop_column("schools", "rib")
