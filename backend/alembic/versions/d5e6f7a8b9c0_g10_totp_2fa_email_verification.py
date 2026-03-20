"""G10: Phase 2B — TOTP 2FA columns and email verification on users table.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-03-15 23:30:00.000000

Reference: Phase 2B — Two-Factor Authentication (TOTP) & Email Verification

Adds to users table:
  - totp_secret VARCHAR(255)     — encrypted TOTP secret (base32)
  - totp_enabled BOOLEAN         — whether 2FA is active (default false)
  - totp_verified_at TIMESTAMPTZ — when 2FA was first verified
  - backup_codes TEXT            — JSON array of bcrypt-hashed backup codes
  - email_verified_at TIMESTAMPTZ — when email was verified via OTP
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # TOTP 2FA columns
    op.add_column(
        "users",
        sa.Column("totp_secret", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("totp_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("totp_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("backup_codes", sa.Text(), nullable=True),
    )

    # Email verification column
    op.add_column(
        "users",
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
    op.drop_column("users", "backup_codes")
    op.drop_column("users", "totp_verified_at")
    op.drop_column("users", "totp_enabled")
    op.drop_column("users", "totp_secret")
