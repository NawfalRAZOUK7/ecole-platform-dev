"""Add Phase 11 security columns to users table.

Revision ID: add_phase11_security_columns
Revises: c1d2e3f4a5b6
Create Date: 2026-05-13

Reference: Phase 11 — Security Enhancements

Adds security columns to users table:
  - phone_verified_at TIMESTAMP
  - phone_otp_secret VARCHAR(255)
  - phone_otp_enabled BOOLEAN
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "add_phase11_security_columns"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("phone_otp_secret", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("phone_otp_enabled", sa.Boolean(), nullable=False, server_default="false"))


def downgrade() -> None:
    op.drop_column("users", "phone_otp_enabled")
    op.drop_column("users", "phone_otp_secret")
    op.drop_column("users", "phone_verified_at")
