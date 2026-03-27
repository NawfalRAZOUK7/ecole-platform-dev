"""Phase 15 calendar, RSVP, and reminder schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EventRecurrenceRule(BaseModel):
    frequency: str = Field(..., pattern="^(weekly|annual)$")
    interval: int = Field(default=1, ge=1, le=52)
    until: datetime | None = None


class EventCreateRequest(BaseModel):
    title_fr: str = Field(..., min_length=1, max_length=255)
    title_ar: str | None = Field(default=None, max_length=255)
    title_en: str | None = Field(default=None, max_length=255)
    description: str | None = None
    type: str = Field(..., pattern="^(holiday|exam|meeting|excursion|ceremony|custom)$")
    visibility: str = Field(..., pattern="^(school|class|role)$")
    start_at: datetime
    end_at: datetime
    location: str | None = Field(default=None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = Field(default=None, ge=1, le=5000)
    rsvp_deadline: datetime | None = None
    recurrence_rule: EventRecurrenceRule | None = None
    class_id: uuid.UUID | None = None
    role_codes: list[str] | None = None
    is_all_day: bool = False
    reminder_offsets_minutes: list[int] = Field(default_factory=lambda: [1440, 60])

    @model_validator(mode="after")
    def validate_event(self):
        if self.end_at < self.start_at:
            raise ValueError("end_at must be after start_at")
        if self.rsvp_deadline and self.rsvp_deadline > self.start_at:
            raise ValueError("rsvp_deadline must be before start_at")
        if self.visibility == "class" and self.class_id is None:
            raise ValueError("class_id is required for class visibility")
        if self.visibility == "role" and not self.role_codes:
            raise ValueError("role_codes are required for role visibility")
        return self


class EventUpdateRequest(BaseModel):
    title_fr: str | None = Field(default=None, min_length=1, max_length=255)
    title_ar: str | None = Field(default=None, max_length=255)
    title_en: str | None = Field(default=None, max_length=255)
    description: str | None = None
    type: str | None = Field(default=None, pattern="^(holiday|exam|meeting|excursion|ceremony|custom)$")
    visibility: str | None = Field(default=None, pattern="^(school|class|role)$")
    start_at: datetime | None = None
    end_at: datetime | None = None
    location: str | None = Field(default=None, max_length=255)
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = Field(default=None, ge=1, le=5000)
    rsvp_deadline: datetime | None = None
    recurrence_rule: EventRecurrenceRule | None = None
    class_id: uuid.UUID | None = None
    role_codes: list[str] | None = None
    is_all_day: bool | None = None
    reminder_offsets_minutes: list[int] | None = None

    @model_validator(mode="after")
    def validate_times(self):
        if self.start_at and self.end_at and self.end_at < self.start_at:
            raise ValueError("end_at must be after start_at")
        if self.rsvp_deadline and self.start_at and self.rsvp_deadline > self.start_at:
            raise ValueError("rsvp_deadline must be before start_at")
        return self


class EventRSVPRequest(BaseModel):
    status: str = Field(..., pattern="^(attending|declined|maybe)$")


class ReminderPreferenceItem(BaseModel):
    event_type: str = Field(..., pattern="^(holiday|exam|meeting|excursion|ceremony|custom)$")
    enabled: bool = True


class ReminderPreferencesRequest(BaseModel):
    preferences: list[ReminderPreferenceItem]


class EventRSVPItem(BaseModel):
    user_id: str
    full_name: str
    role: str
    status: str
    responded_at: str


class EventListItem(BaseModel):
    id: str
    instance_id: str
    source: str
    title_fr: str
    title_ar: str | None = None
    title_en: str | None = None
    description: str | None = None
    type: str
    visibility: str
    start_at: str
    end_at: str
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    class_id: str | None = None
    role_codes: list[str] | None = None
    capacity: int | None = None
    rsvp_deadline: str | None = None
    attendee_count: int = 0
    maybe_count: int = 0
    declined_count: int = 0
    my_rsvp: str | None = None
    is_all_day: bool = False
    is_recurring: bool = False
    recurrence_rule: dict[str, Any] | None = None
    can_edit: bool = False
    can_delete: bool = False
    can_rsvp: bool = False
    is_holiday: bool = False


class EventDetailResponse(EventListItem):
    rsvps: list[EventRSVPItem] | None = None


class CalendarOptionsResponse(BaseModel):
    classes: list[dict[str, str]]
    ical_url: str
    reminder_preferences: list[dict[str, Any]]
