"""Phase 13 notification center schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NotificationPreferenceItem(BaseModel):
    channel: str
    category: str
    enabled: bool
    digest_frequency: str = "off"


class NotificationPreferencesResponse(BaseModel):
    user_id: str
    preferences: list[NotificationPreferenceItem]


class NotificationPreferencesUpdateRequest(BaseModel):
    preferences: list[NotificationPreferenceItem] = Field(..., min_length=1)


class DigestPreferenceRequest(BaseModel):
    digest_frequency: str = Field(..., pattern="^(off|daily|weekly)$")


class DigestPreferenceResponse(BaseModel):
    user_id: str
    digest_frequency: str
    send_hour: int = 7
    timezone: str = "Africa/Casablanca"


class DeviceRegistrationRequest(BaseModel):
    token: str = Field(..., min_length=20, max_length=4096)
    platform: str = Field(..., pattern="^(android|ios|web)$")
    device_name: str | None = Field(None, max_length=200)


class DeviceResponse(BaseModel):
    id: str
    user_id: str
    platform: str
    device_name: str | None = None
    token_preview: str
    last_active_at: str
    created_at: str


class NotificationReadRequest(BaseModel):
    read: bool = True


class NotificationBatchRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    body: str | None = Field(None, max_length=5000)
    category: str = Field(
        ..., pattern="^(academic|billing|attendance|system|announcement)$"
    )
    priority: str = Field(..., pattern="^(low|normal|high|critical)$")
    channels: list[str] | None = Field(
        None,
        description="Optional preferred channels. Defaults to routed preferences.",
    )
    user_ids: list[uuid.UUID] = Field(default_factory=list)
    role_codes: list[str] = Field(default_factory=list)
    class_ids: list[uuid.UUID] = Field(default_factory=list)
    action_url: str | None = Field(None, max_length=500)
    action_payload: dict[str, Any] | None = None
    event_ref: str | None = Field(None, max_length=200)
    silent_push: bool = False
    idempotency_key: str | None = Field(None, max_length=255)


class NotificationHistoryItem(BaseModel):
    id: str
    school_id: str
    user_id: str
    parent_id: str
    event_ref: str | None = None
    title: str
    body: str | None = None
    category: str
    priority: str
    action_url: str | None = None
    action_payload: dict[str, Any] | None = None
    is_read: bool
    read_at: str | None = None
    deleted_at: str | None = None
    created_at: str
    updated_at: str | None = None
    channels: list[str] = Field(default_factory=list)


class NotificationCountResponse(BaseModel):
    unread_count: int
    cached: bool
    cache_ttl_seconds: int = 30


class NotificationMutationResponse(BaseModel):
    id: str
    read: bool
    read_at: str | None = None
    deleted: bool = False


class NotificationBatchResponse(BaseModel):
    requested_recipients: int
    notifications_created: int
    routed_channels: list[str]


class NotificationDigestEmailContext(BaseModel):
    title: str
    unsubscribe_url: str
    open_tracking_url: str | None = None
    locale: str = "fr"
    is_rtl: bool = False
    grouped_notifications: dict[str, list[NotificationHistoryItem]]
    generated_at: datetime
