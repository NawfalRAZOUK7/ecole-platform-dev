"""G14: Timetable slots + exceptions (Phase 11A)

Revision ID: a8b9c0d1e2f3
Revises: a1b2c3d4e5f6
Create Date: 2026-03-22

New tables:
  - timetable_slots: recurring class schedule slots
  - timetable_exceptions: per-date overrides (cancel, substitute, room change)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a8b9c0d1e2f3"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- timetable_slots --
    op.create_table(
        "timetable_slots",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("class_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("room", sa.String(100), nullable=True),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint("end_time > start_time", name="ck_timetable_slots_times"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_timetable_slots_day_of_week"),
        sa.UniqueConstraint(
            "class_id", "day_of_week", "start_time", "academic_year_id",
            name="uq_timetable_slots_class_day_time_year",
        ),
    )
    op.create_index("idx_timetable_slots_school", "timetable_slots", ["school_id"])
    op.create_index("idx_timetable_slots_class_year", "timetable_slots", ["class_id", "academic_year_id"])
    op.create_index("idx_timetable_slots_teacher", "timetable_slots", ["teacher_id"])

    # -- timetable_exceptions --
    op.create_table(
        "timetable_exceptions",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("timetable_slot_id", sa.Uuid(), nullable=False),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("exception_type", sa.String(20), nullable=False),
        sa.Column("substitute_teacher_id", sa.Uuid(), nullable=True),
        sa.Column("new_room", sa.String(100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["timetable_slot_id"], ["timetable_slots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["substitute_teacher_id"], ["users.id"], ondelete="SET NULL"),
        sa.CheckConstraint(
            "exception_type IN ('CANCELED', 'SUBSTITUTED', 'ROOM_CHANGED')",
            name="ck_timetable_exceptions_type",
        ),
        sa.UniqueConstraint(
            "timetable_slot_id", "exception_date",
            name="uq_timetable_exceptions_slot_date",
        ),
    )
    op.create_index("idx_timetable_exceptions_school", "timetable_exceptions", ["school_id"])
    op.create_index("idx_timetable_exceptions_date", "timetable_exceptions", ["exception_date"])


def downgrade() -> None:
    op.drop_table("timetable_exceptions")
    op.drop_table("timetable_slots")
