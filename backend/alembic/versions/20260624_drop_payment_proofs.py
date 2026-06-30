"""Drop the unused payment_proofs table (B4).

``payment_proofs`` was created in the initial schema (9f7257bc8dd1) and seeded,
but never wired into a repository/service/API — no read path ever consumed it
(BACKEND_DB_AUDIT.md §11 B4). Dropped here until a real payment-verification
flow exists; the downgrade recreates the exact original table + FK index so the
migration is fully reversible.

Revision ID: 20260624_drop_payment_proofs
Revises: 20260623_rename_subjects
Create Date: 2026-06-24
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260624_drop_payment_proofs"
down_revision: Union[str, None] = "20260623_rename_subjects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("idx_payment_proofs_payment_attempt", table_name="payment_proofs")
    op.drop_table("payment_proofs")


def downgrade() -> None:
    op.create_table(
        "payment_proofs",
        sa.Column("payment_attempt_id", sa.Uuid(), nullable=False),
        sa.Column("proof_hash", sa.String(length=255), nullable=False),
        sa.Column("provider_ref", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["payment_attempt_id"], ["payment_attempts.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("payment_attempt_id"),
        sa.UniqueConstraint("proof_hash"),
    )
    op.create_index(
        "idx_payment_proofs_payment_attempt",
        "payment_proofs",
        ["payment_attempt_id"],
    )
