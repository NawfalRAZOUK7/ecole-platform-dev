"""Add onboarding applications (public school/educator registration requests).

Two tables:
- school_applications            : pending formal-school / micro-école requests
- school_application_attachments : documents/photos attached to an application

Additive only. SuperAdmin reviews these and provisions the tenant on approval.

Revision ID: add_onboarding_applications
Revises: add_quiz_language
Create Date: 2026-06-05 00:30:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "add_onboarding_applications"
down_revision = "add_quiz_language"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_applications",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("application_type", sa.String(length=30), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("applicant_name", sa.String(length=200), nullable=False),
        sa.Column("applicant_email", sa.String(length=255), nullable=False),
        sa.Column("applicant_phone", sa.String(length=30), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("org_name", sa.String(length=250), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("neighborhood", sa.String(length=200), nullable=True),
        sa.Column("max_capacity", sa.Integer(), nullable=True),
        sa.Column("level_band", sa.String(length=50), nullable=True),
        sa.Column(
            "subjects",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "reviewed_by",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_school_id",
            sa.UUID(),
            sa.ForeignKey("schools.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_school_applications_status_type",
        "school_applications",
        ["status", "application_type"],
    )
    op.create_index(
        "idx_school_applications_email",
        "school_applications",
        ["applicant_email"],
    )

    op.create_table(
        "school_application_attachments",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "application_id",
            sa.UUID(),
            sa.ForeignKey("school_applications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column(
            "kind",
            sa.String(length=30),
            nullable=False,
            server_default="other",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_school_app_attachments_application",
        "school_application_attachments",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_school_app_attachments_application",
        table_name="school_application_attachments",
    )
    op.drop_table("school_application_attachments")
    op.drop_index("idx_school_applications_email", table_name="school_applications")
    op.drop_index(
        "idx_school_applications_status_type", table_name="school_applications"
    )
    op.drop_table("school_applications")
