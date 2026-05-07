"""G23 — Phase 14 reports and analytics.

Revision ID: 3d4e5f6a7b8c
Revises: 2c3d4e5f6a7b
Create Date: 2026-03-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "3d4e5f6a7b8c"
down_revision: Union[str, None] = "2c3d4e5f6a7b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_jobs",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("parameters", JSONB, nullable=False),
        sa.Column("parameters_hash", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_report_jobs_school_requester_created",
        "report_jobs",
        ["school_id", "requester_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_report_jobs_school_type_status",
        "report_jobs",
        ["school_id", "type", "status"],
        unique=False,
    )
    op.create_index(
        "idx_report_jobs_school_params_hash_created",
        "report_jobs",
        ["school_id", "parameters_hash", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_report_jobs_expires_at",
        "report_jobs",
        ["expires_at"],
        unique=False,
    )
    op.alter_column("report_jobs", "status", server_default=None)

    op.create_table(
        "data_exports",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("entity", sa.String(length=50), nullable=False),
        sa.Column("filters", JSONB, nullable=False),
        sa.Column("format", sa.String(length=10), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_data_exports_school_created",
        "data_exports",
        ["school_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_data_exports_requester_created",
        "data_exports",
        ["requester_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_data_exports_entity_format",
        "data_exports",
        ["entity", "format"],
        unique=False,
    )
    op.alter_column("data_exports", "row_count", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_data_exports_entity_format", table_name="data_exports")
    op.drop_index("idx_data_exports_requester_created", table_name="data_exports")
    op.drop_index("idx_data_exports_school_created", table_name="data_exports")
    op.drop_table("data_exports")

    op.drop_index("idx_report_jobs_expires_at", table_name="report_jobs")
    op.drop_index(
        "idx_report_jobs_school_params_hash_created",
        table_name="report_jobs",
    )
    op.drop_index("idx_report_jobs_school_type_status", table_name="report_jobs")
    op.drop_index(
        "idx_report_jobs_school_requester_created",
        table_name="report_jobs",
    )
    op.drop_table("report_jobs")
