"""g50b program_equivalences (Phase 3.2).

Declares semantic equivalence between two programs (typically across a
curriculum revision boundary). Used by the transcript service to merge
"old SM" + "new SM v2" into a single career view.

Equivalence rows are *directional and explicit* — admins must declare
each equivalence. We intentionally do NOT infer transitive closures at
write time; the transcript service can compute reachability when needed.

Revision ID: ab873f7d5708
Revises: cb375ca25f1b
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "ab873f7d5708"
down_revision = "cb375ca25f1b"
branch_labels = None
depends_on = None


EQUIVALENCE_KINDS = ("EQUIVALENT", "SUPERSEDES", "PARTIAL")


def upgrade() -> None:
    op.create_table(
        "program_equivalences",
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
            "from_program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("ratified_at", sa.Date(), nullable=True),
        sa.Column(
            "ratified_by",
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
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "from_program_id",
            "to_program_id",
            name="uq_program_equivalences_school_pair",
        ),
        sa.CheckConstraint(
            "kind IN (" + ", ".join(f"'{k}'" for k in EQUIVALENCE_KINDS) + ")",
            name="ck_program_equivalences_kind",
        ),
        sa.CheckConstraint(
            "from_program_id <> to_program_id",
            name="ck_program_equivalences_distinct_programs",
        ),
    )
    op.create_index(
        "idx_program_equivalences_school_from",
        "program_equivalences",
        ["school_id", "from_program_id"],
    )
    op.create_index(
        "idx_program_equivalences_school_to",
        "program_equivalences",
        ["school_id", "to_program_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_program_equivalences_school_to",
        table_name="program_equivalences",
    )
    op.drop_index(
        "idx_program_equivalences_school_from",
        table_name="program_equivalences",
    )
    op.drop_table("program_equivalences")
