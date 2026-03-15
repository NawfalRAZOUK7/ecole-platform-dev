"""COM domain models — Consent, notifications, deliveries, parent feed.

Reference: Pack C4 (Data Model — COM section), Sprint 1 story S-017.
Migration group: G4-COM (depends on G1-IAM for user FKs).
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
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
            "user_id", "topic", "channel", "scope_type", "scope_ref_id",
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
