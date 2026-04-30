"""g50a program_versions — promote the lightweight version_label shim into a
real versioning entity (Phase 3.1).

Adds:
- program_versions: per-program version metadata (version_label,
  effective_from, retired_at, description, is_active).
- enrollments.program_version_id: nullable FK so existing rows backfill
  cleanly. RESTRICT on delete to preserve historical truth.
- program_assignment_events.{from,to}_program_version_id: nullable FKs.

Backfill:
- For every existing programs row, insert a v1.0 program_versions row
  carrying that program's existing (version_label, effective_from). This
  preserves "what version was a student studying?" continuity for any
  enrollment created before this migration.

The legacy ``programs.version_label`` and ``programs.effective_from`` are
intentionally LEFT IN PLACE. They become a redundant cache of the
"primary version" — clients that haven't migrated to versions still work.
A future cleanup can drop them once the frontend has fully migrated.

Revision ID: cb375ca25f1b
Revises: 9d9968735a7b
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "cb375ca25f1b"
down_revision = "9d9968735a7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # program_versions
    # -----------------------------------------------------------------------
    op.create_table(
        "program_versions",
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
            "program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_label", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("retired_at", sa.Date(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
            "program_id",
            "version_label",
            name="uq_program_versions_program_label",
        ),
    )
    op.create_index(
        "idx_program_versions_school_program",
        "program_versions",
        ["school_id", "program_id"],
    )
    op.create_index(
        "idx_program_versions_program_active",
        "program_versions",
        ["program_id", "is_active"],
    )

    # -----------------------------------------------------------------------
    # Backfill: every existing programs row gets a v1.0 program_versions row.
    # -----------------------------------------------------------------------
    op.execute(
        """
        INSERT INTO program_versions
            (id, school_id, program_id, version_label, description,
             effective_from, retired_at, is_active, created_at)
        SELECT
            gen_random_uuid(),
            p.school_id,
            p.id,
            COALESCE(p.version_label, '1.0'),
            NULL,
            p.effective_from,
            NULL,
            TRUE,
            now()
        FROM programs p
        ON CONFLICT (program_id, version_label) DO NOTHING;
        """
    )

    # -----------------------------------------------------------------------
    # enrollments.program_version_id (nullable FK)
    # -----------------------------------------------------------------------
    op.add_column(
        "enrollments",
        sa.Column(
            "program_version_id",
            sa.UUID(),
            sa.ForeignKey("program_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_enrollments_program_version",
        "enrollments",
        ["program_version_id"],
    )

    # Backfill: any existing enrollment that already has a program_id gets
    # mapped to the v1.0 version we just inserted. Future writes by the
    # service layer will set both.
    op.execute(
        """
        UPDATE enrollments e
        SET program_version_id = pv.id
        FROM program_versions pv
        WHERE e.program_id IS NOT NULL
          AND pv.program_id = e.program_id
          AND pv.version_label = COALESCE(
              (SELECT version_label FROM programs WHERE programs.id = e.program_id),
              '1.0'
          );
        """
    )

    # -----------------------------------------------------------------------
    # program_assignment_events.{from,to}_program_version_id (nullable FK)
    # -----------------------------------------------------------------------
    op.add_column(
        "program_assignment_events",
        sa.Column(
            "from_program_version_id",
            sa.UUID(),
            sa.ForeignKey("program_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "program_assignment_events",
        sa.Column(
            "to_program_version_id",
            sa.UUID(),
            sa.ForeignKey("program_versions.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_prog_events_to_version",
        "program_assignment_events",
        ["to_program_version_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_prog_events_to_version",
        table_name="program_assignment_events",
    )
    op.drop_column("program_assignment_events", "to_program_version_id")
    op.drop_column("program_assignment_events", "from_program_version_id")

    op.drop_index(
        "idx_enrollments_program_version",
        table_name="enrollments",
    )
    op.drop_column("enrollments", "program_version_id")

    op.drop_index(
        "idx_program_versions_program_active",
        table_name="program_versions",
    )
    op.drop_index(
        "idx_program_versions_school_program",
        table_name="program_versions",
    )
    op.drop_table("program_versions")
