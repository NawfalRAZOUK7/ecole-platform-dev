"""G21 — Add content library fields and models.

Revision ID: 1b2c3d4e5f6a
Revises: 0a1b2c3d4e5f
Create Date: 2026-03-27

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1b2c3d4e5f6a"
down_revision: Union[str, None] = "0a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "content_items",
        sa.Column("subject", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column(
            "created_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "content_items",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "content_items",
        sa.Column(
            "origin",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'PLATFORM'"),
        ),
    )
    op.alter_column("content_items", "origin", server_default=None)
    op.add_column(
        "content_items",
        sa.Column(
            "original_content_id",
            sa.Uuid(),
            sa.ForeignKey("content_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "idx_content_items_subject", "content_items", ["subject"], unique=False
    )
    op.create_index(
        "idx_content_items_origin", "content_items", ["origin"], unique=False
    )
    op.create_index(
        "idx_content_items_created_by", "content_items", ["created_by"], unique=False
    )

    op.create_table(
        "class_content_assignments",
        sa.Column(
            "teacher_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "class_id",
            sa.Uuid(),
            sa.ForeignKey("classes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "content_item_id",
            sa.Uuid(),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "class_id",
            "content_item_id",
            name="uq_class_content_assignments_class_content",
        ),
    )
    op.create_index(
        "idx_class_content_assignments_teacher",
        "class_content_assignments",
        ["teacher_id"],
        unique=False,
    )
    op.create_index(
        "idx_class_content_assignments_class",
        "class_content_assignments",
        ["class_id"],
        unique=False,
    )
    op.create_index(
        "idx_class_content_assignments_school",
        "class_content_assignments",
        ["school_id"],
        unique=False,
    )

    op.create_table(
        "content_submissions",
        sa.Column(
            "content_item_id",
            sa.Uuid(),
            sa.ForeignKey("content_items.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "submitted_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "reviewed_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column(
            "promoted_content_id",
            sa.Uuid(),
            sa.ForeignKey("content_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_content_submissions_status",
        "content_submissions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "idx_content_submissions_submitted_by",
        "content_submissions",
        ["submitted_by"],
        unique=False,
    )
    op.create_index(
        "idx_content_submissions_school",
        "content_submissions",
        ["school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_content_submissions_school", table_name="content_submissions")
    op.drop_index(
        "idx_content_submissions_submitted_by", table_name="content_submissions"
    )
    op.drop_index("idx_content_submissions_status", table_name="content_submissions")
    op.drop_table("content_submissions")

    op.drop_index(
        "idx_class_content_assignments_school",
        table_name="class_content_assignments",
    )
    op.drop_index(
        "idx_class_content_assignments_class",
        table_name="class_content_assignments",
    )
    op.drop_index(
        "idx_class_content_assignments_teacher",
        table_name="class_content_assignments",
    )
    op.drop_table("class_content_assignments")

    op.drop_index("idx_content_items_created_by", table_name="content_items")
    op.drop_index("idx_content_items_origin", table_name="content_items")
    op.drop_index("idx_content_items_subject", table_name="content_items")
    op.drop_column("content_items", "original_content_id")
    op.drop_column("content_items", "origin")
    op.drop_column("content_items", "thumbnail_path")
    op.drop_column("content_items", "description")
    op.drop_column("content_items", "created_by")
    op.drop_column("content_items", "subject")
