"""G51b - Add shared_review_comments table.

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c1d2e3f4a5b6"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shared_review_comments",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("emoji", sa.String(length=10), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_shared_review_comments_school_id",
        "shared_review_comments",
        ["school_id"],
    )
    op.create_index(
        "idx_shared_review_comments_session",
        "shared_review_comments",
        ["session_id"],
    )
    op.create_index(
        "idx_shared_review_comments_child",
        "shared_review_comments",
        ["child_id"],
    )
    op.create_index(
        "idx_shared_review_comments_author",
        "shared_review_comments",
        ["author_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_shared_review_comments_author", table_name="shared_review_comments"
    )
    op.drop_index(
        "idx_shared_review_comments_child", table_name="shared_review_comments"
    )
    op.drop_index(
        "idx_shared_review_comments_session", table_name="shared_review_comments"
    )
    op.drop_index(
        "ix_shared_review_comments_school_id", table_name="shared_review_comments"
    )
    op.drop_table("shared_review_comments")
