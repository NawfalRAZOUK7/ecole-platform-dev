"""G25 — Phase 16 document management.

Revision ID: 5f6a7b8c9d0e
Revises: 4e5f6a7b8c9d
Create Date: 2026-03-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "5f6a7b8c9d0e"
down_revision: Union[str, None] = "4e5f6a7b8c9d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=150), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("thumbnail_path", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=40), nullable=False, server_default="other"),
        sa.Column("linked_student_id", sa.Uuid(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["linked_student_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_documents_school_created", "documents", ["school_id", "created_at"], unique=False)
    op.create_index("idx_documents_school_category", "documents", ["school_id", "category"], unique=False)
    op.create_index("idx_documents_school_sha", "documents", ["school_id", "sha256"], unique=False)
    op.create_index("idx_documents_linked_student", "documents", ["linked_student_id"], unique=False)
    op.create_index("idx_documents_deleted_at", "documents", ["deleted_at"], unique=False)
    op.create_index("idx_documents_expires_at", "documents", ["expires_at"], unique=False)

    op.create_table(
        "resources",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("subject", sa.String(length=120), nullable=True),
        sa.Column("level", sa.String(length=120), nullable=True),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String(length=80)),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False, server_default="school"),
        sa.Column("class_id", sa.Uuid(), nullable=True),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["file_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploader_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_resources_school_created", "resources", ["school_id", "created_at"], unique=False)
    op.create_index("idx_resources_school_type", "resources", ["school_id", "type"], unique=False)
    op.create_index(
        "idx_resources_school_subject_level",
        "resources",
        ["school_id", "subject", "level"],
        unique=False,
    )
    op.create_index("idx_resources_school_visibility", "resources", ["school_id", "visibility"], unique=False)
    op.create_index("idx_resources_class_id", "resources", ["class_id"], unique=False)
    op.create_index("idx_resources_deleted_at", "resources", ["deleted_at"], unique=False)
    # Resource search currently combines ILIKE filters with ARRAY overlap on tags.
    # A plain GIN index on tags is safe on PostgreSQL and avoids non-immutable
    # expression index failures during migration.
    op.execute(
        """
        CREATE INDEX idx_resources_search_gin ON resources
        USING gin (tags)
        """
    )

    op.create_table(
        "resource_ratings",
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_id", "user_id", name="uq_resource_ratings_resource_user"),
    )
    op.create_index("idx_resource_ratings_resource", "resource_ratings", ["resource_id"], unique=False)
    op.create_index("idx_resource_ratings_user", "resource_ratings", ["user_id"], unique=False)

    op.create_table(
        "student_document_requirements",
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "school_id",
            "category",
            name="uq_student_document_requirements_school_category",
        ),
    )
    op.create_index(
        "idx_student_document_requirements_school",
        "student_document_requirements",
        ["school_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_student_document_requirements_school", table_name="student_document_requirements")
    op.drop_table("student_document_requirements")

    op.drop_index("idx_resource_ratings_user", table_name="resource_ratings")
    op.drop_index("idx_resource_ratings_resource", table_name="resource_ratings")
    op.drop_table("resource_ratings")

    op.execute("DROP INDEX IF EXISTS idx_resources_search_gin")
    op.drop_index("idx_resources_deleted_at", table_name="resources")
    op.drop_index("idx_resources_class_id", table_name="resources")
    op.drop_index("idx_resources_school_visibility", table_name="resources")
    op.drop_index("idx_resources_school_subject_level", table_name="resources")
    op.drop_index("idx_resources_school_type", table_name="resources")
    op.drop_index("idx_resources_school_created", table_name="resources")
    op.drop_table("resources")

    op.drop_index("idx_documents_expires_at", table_name="documents")
    op.drop_index("idx_documents_deleted_at", table_name="documents")
    op.drop_index("idx_documents_linked_student", table_name="documents")
    op.drop_index("idx_documents_school_sha", table_name="documents")
    op.drop_index("idx_documents_school_category", table_name="documents")
    op.drop_index("idx_documents_school_created", table_name="documents")
    op.drop_table("documents")
