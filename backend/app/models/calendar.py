"""Calendar and events domain models — Phase 15."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, SchoolScopedMixin, SoftDeleteMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


class EventType(str, enum.Enum):
    HOLIDAY = "holiday"
    EXAM = "exam"
    MEETING = "meeting"
    EXCURSION = "excursion"
    CEREMONY = "ceremony"
    CUSTOM = "custom"


class EventVisibility(str, enum.Enum):
    SCHOOL = "school"
    CLASS = "class"
    ROLE = "role"


class EventRsvpStatus(str, enum.Enum):
    ATTENDING = "attending"
    DECLINED = "declined"
    MAYBE = "maybe"


class EventReminderChannel(str, enum.Enum):
    IN_APP = "in_app"
    PUSH = "push"


class Event(TimestampMixin, SchoolScopedMixin, SoftDeleteMixin, Base):
    """Calendar event created by a user within a school."""

    __tablename__ = "events"

    title_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    visibility: Mapped[str] = mapped_column(String(30), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rsvp_deadline: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    recurrence_rule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("classes.id", ondelete="SET NULL"),
        nullable=True,
    )
    role_codes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    __table_args__ = (
        CheckConstraint("end_at >= start_at", name="ck_events_end_after_start"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_events_capacity_positive"),
        Index("idx_events_school_start", "school_id", "start_at"),
        Index("idx_events_school_type_start", "school_id", "type", "start_at"),
        Index("idx_events_school_class_start", "school_id", "class_id", "start_at"),
        Index("idx_events_school_visibility_start", "school_id", "visibility", "start_at"),
        Index("idx_events_class_id", "class_id"),
        Index("idx_events_created_by", "created_by"),
    )

    @property
    def is_past(self) -> bool:
        return self.end_at < datetime.now(timezone.utc)

    def __repr__(self) -> str:
        return (
            f"<Event id={_short_id(self.id)} title={self.title_fr} "
            f"start={self.start_at}>"
        )


class EventRSVP(TimestampMixin, Base):
    """Per-user RSVP state for an event."""

    __tablename__ = "event_rsvps"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="uq_event_rsvps_event_user"),
        Index("idx_event_rsvps_event_status", "event_id", "status"),
        Index("idx_event_rsvps_user_responded", "user_id", "responded_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EventRSVP id={_short_id(self.id)} event_id={_short_id(self.event_id)} "
            f"status={self.status}>"
        )


class EventReminder(TimestampMixin, Base):
    """Scheduled reminder dispatches for upcoming event instances."""

    __tablename__ = "event_reminders"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    occurrence_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "remind_at",
            "channel",
            name="uq_event_reminders_event_remind_channel",
        ),
        Index("idx_event_reminders_due_sent", "sent", "remind_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<EventReminder id={_short_id(self.id)} event_id={_short_id(self.event_id)} "
            f"channel={self.channel}>"
        )


class EventReminderPreference(TimestampMixin, SchoolScopedMixin, Base):
    """Per-user event reminder preference by event type."""

    __tablename__ = "event_reminder_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint(
            "school_id",
            "user_id",
            "event_type",
            name="uq_event_reminder_prefs_school_user_type",
        ),
        Index("idx_event_reminder_preferences_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<EventReminderPreference id={_short_id(self.id)} "
            f"user_id={_short_id(self.user_id)} event_type={self.event_type}>"
        )


class MoroccanHoliday(TimestampMixin, Base):
    """Global holiday seed rows used to auto-populate school calendars."""

    __tablename__ = "moroccan_holidays"

    code: Mapped[str] = mapped_column(String(100), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False)
    name_fr: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint("code", "holiday_date", name="uq_moroccan_holidays_code_date"),
        Index("idx_moroccan_holidays_date", "holiday_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<MoroccanHoliday id={_short_id(self.id)} code={self.code} "
            f"holiday_date={self.holiday_date}>"
        )
