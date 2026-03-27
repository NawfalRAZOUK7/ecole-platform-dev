"""COM domain models — Consent, notifications, deliveries, parent feed, messaging, announcements.

Reference: Pack C4 (Data Model — COM section), Sprint 1 story S-017.
Migration group: G4-COM (depends on G1-IAM for user FKs).
Phase 11C: Added Conversation, ConversationParticipant, Message, MessageReadReceipt, Announcement.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ConsentStatus(str, enum.Enum):
    OPTED_IN = "opted_in"
    OPTED_OUT = "opted_out"


class ConsentScopeType(str, enum.Enum):
    SCHOOL = "school"
    STUDENT = "student"


class DeliveryChannel(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class DeliveryStatus(str, enum.Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    FALLBACK = "fallback"
    SUPPRESSED = "suppressed"


class ConversationType(str, enum.Enum):
    """Phase 11C: Conversation type."""

    DIRECT = "DIRECT"
    GROUP = "GROUP"


class ParticipantRole(str, enum.Enum):
    """Phase 11C: Role in conversation."""

    INITIATOR = "INITIATOR"
    PARTICIPANT = "PARTICIPANT"


class AnnouncementStatus(str, enum.Enum):
    """Phase 11C: Announcement status."""

    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class ConsentPreference(TimestampMixin, Base):
    """Parent consent preference for a notification topic/channel.

    INV-COM-CONSENT: unique on full scope tuple (user, topic, channel, scope_type, scope_ref_id).
    """

    __tablename__ = "consent_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    topic: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_ref_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ConsentStatus.OPTED_IN.value
    )

    __table_args__ = (
        # INV-COM-CONSENT: unique on full scope tuple
        UniqueConstraint(
            "user_id",
            "topic",
            "channel",
            "scope_type",
            "scope_ref_id",
            name="uq_consent_user_topic_channel_scope",
        ),
        Index("idx_consent_school_user", "school_id", "user_id"),
    )


class Notification(TimestampMixin, Base):
    """Notification generated from a platform event.

    idempotency_key ensures no duplicate notifications for the same event.
    """

    __tablename__ = "notifications"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    deliveries: Mapped[list["NotificationDelivery"]] = relationship(
        back_populates="notification", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_notifications_school_parent", "school_id", "parent_id"),
    )


class NotificationDelivery(TimestampMixin, Base):
    """Delivery attempt for a notification via a specific channel."""

    __tablename__ = "notification_deliveries"

    notification_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DeliveryStatus.QUEUED.value
    )

    # Relationships
    notification: Mapped["Notification"] = relationship(back_populates="deliveries")

    __table_args__ = (
        Index(
            "idx_deliveries_school_notification_status",
            "school_id",
            "notification_id",
            "status",
        ),
    )


class ParentFeedItem(TimestampMixin, Base):
    """Parent feed item — aggregated view for parents.

    Derived from verified metier events; idempotent creation.
    """

    __tablename__ = "parent_feed_items"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    parent_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        # idx_feed_school_parent_created_desc — for chronological parent feed
        Index(
            "idx_feed_school_parent_created",
            "school_id",
            "parent_id",
            "created_at",
        ),
    )


# ---------------------------------------------------------------------------
# Messaging (Phase 11C)
# ---------------------------------------------------------------------------


class Conversation(TimestampMixin, Base):
    """Parent-teacher conversation (direct or group).

    ABAC enforced at API level: parents can only message teachers
    of their children's classes, and vice versa.
    """

    __tablename__ = "conversations"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ConversationType.DIRECT.value
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Relationships
    participants: Mapped[list["ConversationParticipant"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_conversations_school", "school_id"),
        Index("idx_conversations_created_by", "created_by"),
    )


class ConversationParticipant(TimestampMixin, Base):
    """Participant in a conversation."""

    __tablename__ = "conversation_participants"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_in_conversation: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ParticipantRole.PARTICIPANT.value
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    muted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="participants")

    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_conversation_participants_conv_user",
        ),
        Index("idx_conv_participants_user", "user_id"),
    )


class Message(TimestampMixin, Base):
    """Message within a conversation."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    read_receipts: Mapped[list["MessageReadReceipt"]] = relationship(
        back_populates="message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_messages_conv_sent", "conversation_id", "sent_at"),
        Index("idx_messages_sender", "sender_id"),
    )


class MessageReadReceipt(TimestampMixin, Base):
    """Read receipt for a message — tracks who read when."""

    __tablename__ = "message_read_receipts"

    message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    message: Mapped["Message"] = relationship(back_populates="read_receipts")

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            name="uq_message_read_receipts_msg_user",
        ),
        Index("idx_read_receipts_user", "user_id"),
    )


# ---------------------------------------------------------------------------
# Announcements (Phase 11C)
# ---------------------------------------------------------------------------


class Announcement(TimestampMixin, Base):
    """School-wide or targeted announcement from admin/director.

    target_roles: JSONB array of role codes — e.g. ["PAR", "STD"]
    target_class_ids: JSONB array of class UUIDs — NULL means all classes
    """

    __tablename__ = "announcements"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    target_roles: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    target_class_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=AnnouncementStatus.DRAFT.value
    )

    __table_args__ = (
        Index("idx_announcements_school_status", "school_id", "status"),
        Index("idx_announcements_author", "author_id"),
    )
