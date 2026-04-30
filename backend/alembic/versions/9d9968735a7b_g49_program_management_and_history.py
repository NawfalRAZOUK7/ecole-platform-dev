"""g49 program management and student academic history

Adds:
- programs:                          school-scoped catalog of academic programs (Filières)
                                     with lightweight versioning shim (version_label,
                                     effective_from) for forward compatibility.
- enrollments.program_id:            nullable FK so existing rows keep working;
                                     RESTRICT delete to preserve historical truth.
- program_assignment_events:         append-only log of every program change for a
                                     student (initial / transfer / promotion / correction
                                     / readmission). Enforced as append-only via a
                                     PostgreSQL trigger (defence-in-depth).

Reference: Hybrid L2 + L3 versioning shim — Academic Program Management & Student
           Academic History design.
Migration group: G49 (additive — no existing constraint or column changes).

Revision ID: 9d9968735a7b
Revises: f4e5d6c7b8a9
Create Date: 2026-04-28 00:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d9968735a7b"
down_revision = "f4e5d6c7b8a9"
branch_labels = None
depends_on = None


PROGRAM_ASSIGNMENT_REASON_CODES = (
    "INITIAL",
    "TRANSFER",
    "PROMOTION",
    "CORRECTION",
    "READMISSION",
)


def upgrade() -> None:
    # -----------------------------------------------------------------------
    # programs — school-scoped catalog of filières / tracks
    # -----------------------------------------------------------------------
    op.create_table(
        "programs",
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
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("level", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        # Lightweight versioning shim (L3 — forward-compat, no separate table).
        # When curriculum drift becomes meaningful, promote these into a
        # program_versions table without breaking the API contract.
        sa.Column(
            "version_label",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'1.0'"),
        ),
        sa.Column("effective_from", sa.Date(), nullable=True),
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
            "code",
            name="uq_programs_school_code",
        ),
    )
    op.create_index(
        "idx_programs_school_active",
        "programs",
        ["school_id", "is_active"],
    )
    op.create_index(
        "idx_programs_school_level",
        "programs",
        ["school_id", "level"],
    )

    # -----------------------------------------------------------------------
    # enrollments.program_id — nullable FK (additive, no constraint changes)
    # -----------------------------------------------------------------------
    # NOTE: nullable=True so the column backfills cleanly to NULL on existing
    # rows. ondelete=RESTRICT prevents losing historical truth via cascading
    # program deletes (we soft-delete programs via is_active = false instead).
    op.add_column(
        "enrollments",
        sa.Column(
            "program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_enrollments_school_student_program",
        "enrollments",
        ["school_id", "student_id", "program_id"],
    )

    # -----------------------------------------------------------------------
    # program_assignment_events — append-only audit log of program changes
    # -----------------------------------------------------------------------
    op.create_table(
        "program_assignment_events",
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
        sa.Column(
            "period_id",
            sa.UUID(),
            sa.ForeignKey("periods.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "from_program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "to_program_id",
            sa.UUID(),
            sa.ForeignKey("programs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "from_enrollment_id",
            sa.UUID(),
            sa.ForeignKey("enrollments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "to_enrollment_id",
            sa.UUID(),
            sa.ForeignKey("enrollments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason_code", sa.String(30), nullable=False),
        sa.Column("reason_note", sa.Text(), nullable=True),
        sa.Column(
            "actor_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "reason_code IN ("
            + ", ".join(f"'{r}'" for r in PROGRAM_ASSIGNMENT_REASON_CODES)
            + ")",
            name="ck_prog_assignment_events_reason_code",
        ),
        sa.CheckConstraint(
            "from_program_id IS DISTINCT FROM to_program_id",
            name="ck_prog_assignment_events_changed",
        ),
    )
    op.create_index(
        "idx_prog_events_school_student_occurred",
        "program_assignment_events",
        ["school_id", "student_id", sa.text("occurred_at DESC")],
    )
    op.create_index(
        "idx_prog_events_school_year",
        "program_assignment_events",
        ["school_id", "academic_year_id"],
    )
    op.create_index(
        "idx_prog_events_to_program",
        "program_assignment_events",
        ["to_program_id"],
    )

    # -----------------------------------------------------------------------
    # Append-only enforcement at the database level.
    # The service layer never UPDATEs/DELETEs these rows, but a trigger gives
    # us defence-in-depth: any direct DML attempt fails loudly.
    # -----------------------------------------------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION program_assignment_events_append_only()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION
                'program_assignment_events is append-only (operation: %)',
                TG_OP
                USING ERRCODE = 'check_violation';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_program_assignment_events_no_update
        BEFORE UPDATE ON program_assignment_events
        FOR EACH ROW
        EXECUTE FUNCTION program_assignment_events_append_only();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_program_assignment_events_no_delete
        BEFORE DELETE ON program_assignment_events
        FOR EACH ROW
        EXECUTE FUNCTION program_assignment_events_append_only();
        """
    )


def downgrade() -> None:
    # Remove triggers + function first.
    op.execute(
        "DROP TRIGGER IF EXISTS trg_program_assignment_events_no_update "
        "ON program_assignment_events;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_program_assignment_events_no_delete "
        "ON program_assignment_events;"
    )
    op.execute("DROP FUNCTION IF EXISTS program_assignment_events_append_only();")

    op.drop_index(
        "idx_prog_events_to_program",
        table_name="program_assignment_events",
    )
    op.drop_index(
        "idx_prog_events_school_year",
        table_name="program_assignment_events",
    )
    op.drop_index(
        "idx_prog_events_school_student_occurred",
        table_name="program_assignment_events",
    )
    op.drop_table("program_assignment_events")

    op.drop_index(
        "idx_enrollments_school_student_program",
        table_name="enrollments",
    )
    op.drop_column("enrollments", "program_id")

    op.drop_index("idx_programs_school_level", table_name="programs")
    op.drop_index("idx_programs_school_active", table_name="programs")
    op.drop_table("programs")
