"""G12 — Role-specific profile tables + invitation target_student_id (Phase 1B).

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-03-21

Creates:
- student_profiles (user_id FK unique, school_id, student_number unique/school, etc.)
- parent_profiles (user_id FK unique, school_id, relationship_type, cin_number, etc.)
- teacher_profiles (user_id FK unique, school_id, employee_id, subject_specialty, etc.)
- Adds target_student_id nullable FK column to invitation_codes
"""

import sqlalchemy as sa
from alembic import op

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- student_profiles --
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("student_number", sa.String(50), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=True),
        sa.Column("class_level", sa.String(50), nullable=True),
        sa.Column("nationality", sa.String(100), nullable=True),
        sa.Column("guardian_notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_number", "school_id", name="uq_student_profiles_number_school"),
    )
    op.create_index("idx_student_profiles_user", "student_profiles", ["user_id"])
    op.create_index("idx_student_profiles_school", "student_profiles", ["school_id"])

    # -- parent_profiles --
    op.create_table(
        "parent_profiles",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(20), nullable=True),
        sa.Column("cin_number", sa.String(30), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("profession", sa.String(200), nullable=True),
        sa.Column("emergency_phone", sa.String(20), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_parent_profiles_user", "parent_profiles", ["user_id"])
    op.create_index("idx_parent_profiles_school", "parent_profiles", ["school_id"])

    # -- teacher_profiles --
    op.create_table(
        "teacher_profiles",
        sa.Column("id", sa.Uuid(), nullable=False, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=True),
        sa.Column("subject_specialty", sa.String(200), nullable=True),
        sa.Column("qualification", sa.String(200), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_teacher_profiles_user", "teacher_profiles", ["user_id"])
    op.create_index("idx_teacher_profiles_school", "teacher_profiles", ["school_id"])

    # -- Add target_student_id to invitation_codes --
    op.add_column(
        "invitation_codes",
        sa.Column("target_student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("invitation_codes", "target_student_id")
    op.drop_table("teacher_profiles")
    op.drop_table("parent_profiles")
    op.drop_table("student_profiles")
