"""G13 — Phase 9C: PDF exercise workflow fields.

Revision ID: a1b2c3d4e5f6
Revises: f7a8b9c0d1e2
Create Date: 2026-03-22

Adds:
- assignments.exercise_pdf_path (String 500, nullable) — stores the downloadable exercise PDF
- submission_files.file_type_hint (String 30, nullable) — SOLUTION_SCAN/SOLUTION_PHOTO/DOCUMENT
"""

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assignments",
        sa.Column("exercise_pdf_path", sa.String(500), nullable=True),
    )
    op.add_column(
        "submission_files",
        sa.Column("file_type_hint", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submission_files", "file_type_hint")
    op.drop_column("assignments", "exercise_pdf_path")
