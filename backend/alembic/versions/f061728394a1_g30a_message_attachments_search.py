"""G30a — Message attachments and full-text search index.

Revision ID: f061728394a1
Revises: ef5a6b7c8d90
Create Date: 2026-03-28
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f061728394a1"
down_revision: Union[str, None] = "ef5a6b7c8d90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("attachment_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_messages_attachment_id_documents",
        "messages",
        "documents",
        ["attachment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_messages_attachment_id",
        "messages",
        ["attachment_id"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX idx_messages_body_gin "
        "ON messages USING gin (to_tsvector('simple', body))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_messages_body_gin")
    op.drop_index("idx_messages_attachment_id", table_name="messages")
    op.drop_constraint(
        "fk_messages_attachment_id_documents",
        "messages",
        type_="foreignkey",
    )
    op.drop_column("messages", "attachment_id")
