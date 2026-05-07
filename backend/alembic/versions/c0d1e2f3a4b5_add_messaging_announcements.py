"""G16: Conversations, messages, read receipts, announcements (Phase 11C)

Revision ID: c0d1e2f3a4b5
Revises: b9c0d1e2f3a4
Create Date: 2026-03-22

New tables:
  - conversations: parent-teacher conversations (direct or group)
  - conversation_participants: participants in a conversation
  - messages: messages within a conversation
  - message_read_receipts: read receipts for messages
  - announcements: school-wide or targeted announcements
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "c0d1e2f3a4b5"
down_revision = "b9c0d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- conversations --
    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="DIRECT"),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("subject", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "type IN ('DIRECT', 'GROUP')",
            name="ck_conversations_type",
        ),
    )
    op.create_index("idx_conversations_school", "conversations", ["school_id"])
    op.create_index("idx_conversations_created_by", "conversations", ["created_by"])

    # -- conversation_participants --
    op.create_table(
        "conversation_participants",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_in_conversation", sa.String(20), nullable=False, server_default="PARTICIPANT"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("muted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_conversation_participants_conv_user"),
        sa.CheckConstraint(
            "role_in_conversation IN ('INITIATOR', 'PARTICIPANT')",
            name="ck_conv_participants_role",
        ),
    )
    op.create_index("idx_conv_participants_user", "conversation_participants", ["user_id"])

    # -- messages --
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_messages_conv_sent", "messages", ["conversation_id", "sent_at"])
    op.create_index("idx_messages_sender", "messages", ["sender_id"])

    # -- message_read_receipts --
    op.create_table(
        "message_read_receipts",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_read_receipts_msg_user"),
    )
    op.create_index("idx_read_receipts_user", "message_read_receipts", ["user_id"])

    # -- announcements --
    op.create_table(
        "announcements",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("school_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("target_roles", JSONB, nullable=False),
        sa.Column("target_class_ids", JSONB, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')",
            name="ck_announcements_status",
        ),
    )
    op.create_index("idx_announcements_school_status", "announcements", ["school_id", "status"])
    op.create_index("idx_announcements_author", "announcements", ["author_id"])


def downgrade() -> None:
    op.drop_table("announcements")
    op.drop_table("message_read_receipts")
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
