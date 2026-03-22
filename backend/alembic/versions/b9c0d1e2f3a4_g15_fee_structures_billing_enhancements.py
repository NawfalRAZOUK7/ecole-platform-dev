"""G15: Fee structures, assignments, payment retry + reminder fields (Phase 11B)

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-03-22

New tables:
  - fee_structures: school fee definitions (amount, frequency, due day)
  - fee_assignments: fee-to-student assignments with optional discount

Altered tables:
  - payment_attempts: added retry_count, next_retry_at, last_retry_error
  - invoices: added reminder_sent_at, reminder_count, fee_structure_id
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- fee_structures --
    op.create_table(
        "fee_structures",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="MAD"),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="ANNUAL"),
        sa.Column("due_day", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("applies_to_level", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.CheckConstraint("amount > 0", name="ck_fee_structures_amount"),
        sa.CheckConstraint("due_day >= 1 AND due_day <= 28", name="ck_fee_structures_due_day"),
        sa.CheckConstraint(
            "frequency IN ('MONTHLY', 'TRIMESTRIAL', 'ANNUAL', 'ONE_TIME')",
            name="ck_fee_structures_frequency",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'ARCHIVED')",
            name="ck_fee_structures_status",
        ),
    )
    op.create_index("idx_fee_structures_school", "fee_structures", ["school_id"])
    op.create_index("idx_fee_structures_school_year", "fee_structures", ["school_id", "academic_year_id"])

    # -- fee_assignments --
    op.create_table(
        "fee_assignments",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("fee_structure_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("discount_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("discount_reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["fee_structure_id"], ["fee_structures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("fee_structure_id", "student_id", name="uq_fee_assignments_fee_student"),
        sa.CheckConstraint(
            "discount_percent IS NULL OR (discount_percent >= 0 AND discount_percent <= 100)",
            name="ck_fee_assignments_discount",
        ),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'EXEMPTED', 'ARCHIVED')",
            name="ck_fee_assignments_status",
        ),
    )
    op.create_index("idx_fee_assignments_school", "fee_assignments", ["school_id"])
    op.create_index("idx_fee_assignments_student", "fee_assignments", ["student_id"])

    # -- Add retry fields to payment_attempts --
    op.add_column("payment_attempts", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("payment_attempts", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("payment_attempts", sa.Column("last_retry_error", sa.Text(), nullable=True))

    # -- Add reminder fields to invoices --
    op.add_column("invoices", sa.Column("reminder_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("invoices", sa.Column("reminder_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("invoices", sa.Column("fee_structure_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_invoices_fee_structure",
        "invoices",
        "fee_structures",
        ["fee_structure_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint("ck_invoices_reminder_count", "invoices", "reminder_count >= 0")
    op.create_index("idx_invoices_due_date_status", "invoices", ["due_date", "status"])


def downgrade() -> None:
    # Remove invoice additions
    op.drop_index("idx_invoices_due_date_status", table_name="invoices")
    op.drop_constraint("ck_invoices_reminder_count", "invoices", type_="check")
    op.drop_constraint("fk_invoices_fee_structure", "invoices", type_="foreignkey")
    op.drop_column("invoices", "fee_structure_id")
    op.drop_column("invoices", "reminder_count")
    op.drop_column("invoices", "reminder_sent_at")

    # Remove payment_attempts additions
    op.drop_column("payment_attempts", "last_retry_error")
    op.drop_column("payment_attempts", "next_retry_at")
    op.drop_column("payment_attempts", "retry_count")

    # Drop new tables
    op.drop_table("fee_assignments")
    op.drop_table("fee_structures")
