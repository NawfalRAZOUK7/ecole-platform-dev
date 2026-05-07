"""G9: Phase 2A — Session device info columns for session management.

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-03-15 23:00:00.000000

Reference: Phase 2A — Password Policy & Session Management

Adds to sessions table:
  - user_agent VARCHAR(500) — full User-Agent string
  - ip_address VARCHAR(45)  — client IP (supports IPv6)
  - device_name VARCHAR(200) — parsed device/browser name
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add device info columns to sessions table
    op.add_column("sessions", sa.Column("user_agent", sa.String(500), nullable=True))
    op.add_column("sessions", sa.Column("ip_address", sa.String(45), nullable=True))
    op.add_column("sessions", sa.Column("device_name", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "device_name")
    op.drop_column("sessions", "ip_address")
    op.drop_column("sessions", "user_agent")
