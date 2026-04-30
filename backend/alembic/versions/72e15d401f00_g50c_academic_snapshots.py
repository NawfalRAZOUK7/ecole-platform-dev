"""g50c academic_snapshots (Phase 3.3).

Frozen JSONB document of "everything about a student for a given academic
year". Lets the transcript service render an audit-grade record that is
reproducible byte-for-byte even if downstream tables drift.

Append-only by service convention (no UPDATEs from the application). We
intentionally do NOT install a database trigger to enforce that — admins
should be able to delete a bad snapshot and re-take it.

Revision ID: 72e15d401f00
Revises: ab873f7d5708
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "72e15d401f00"
down_revision = "ab873f7d5708"
branch_labels = None
depends_on = None


SNAPSHOT_KINDS = ("YEAR_END", "MID_YEAR", "MANUAL")


def upgrade() -> None:
    op.create_table(
        "academic_snapshots",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "school_id",
            sa.UUID(),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "academic_year_id",
            sa.UUID(),
            sa.ForeignKey("academic_years.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("snapshot_kind", sa.String(20), nullable=False),
        sa.Column(
            "snapshot_data",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "taken_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "taken_by",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "snapshot_kind IN ("
            + ", ".join(f"'{k}'" for k in SNAPSHOT_KINDS)
            + ")",
            name="ck_academic_snapshots_kind",
        ),
    )
    op.create_index(
        "idx_academic_snapshots_student_year",
        "academic_snapshots",
        ["school_id", "student_id", "academic_year_id"],
    )
    op.create_index(
        "idx_academic_snapshots_taken_at",
        "academic_snapshots",
        ["school_id", sa.text("taken_at DESC")],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_academic_snapshots_taken_at",
        table_name="academic_snapshots",
    )
    op.drop_index(
        "idx_academic_snapshots_student_year",
        table_name="academic_snapshots",
    )
    op.drop_table("academic_snapshots")
