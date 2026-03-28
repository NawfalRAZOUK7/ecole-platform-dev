"""COM domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-065 to S-067
Phase 11C: Added Conversation, Message, ReadReceipt, Announcement schemas.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Notification (S-065)
# ---------------------------------------------------------------------------
class NotificationResponse(BaseModel):
    id: str
    school_id: str
    parent_id: str
    event_ref: str | None = None
    title: str
    body: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Consent (S-066)
# ---------------------------------------------------------------------------
class ConsentUpdateRequest(BaseModel):
    status: str = Field(..., pattern="^(opted_in|opted_out)$")


class ConsentResponse(BaseModel):
    id: str
    user_id: str
    school_id: str
    topic: str
    channel: str
    scope_type: str
    scope_ref_id: str | None = None
    status: str


# ---------------------------------------------------------------------------
# Feed (S-067)
# ---------------------------------------------------------------------------
class FeedItemResponse(BaseModel):
    id: str
    school_id: str
    parent_id: str
    student_id: str | None = None
    source_type: str
    source_ref: str | None = None
    title: str
    body: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Conversations (Phase 11C)
# ---------------------------------------------------------------------------
class ConversationCreateRequest(BaseModel):
    """Start a new conversation (DIRECT or GROUP)."""

    participant_ids: list[uuid.UUID] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="User IDs of the other participants (not including initiator)",
    )
    type: str = Field("DIRECT", pattern="^(DIRECT|GROUP)$")
    subject: str | None = Field(None, max_length=300)
    initial_message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="First message body to send in the conversation",
    )


class ConversationParticipantResponse(BaseModel):
    user_id: str
    role_in_conversation: str
    joined_at: str
    muted: bool


class ConversationResponse(BaseModel):
    id: str
    school_id: str
    type: str
    created_by: str
    subject: str | None = None
    participants: list[ConversationParticipantResponse] = []
    last_message_at: str | None = None
    created_at: str


# ---------------------------------------------------------------------------
# Messages (Phase 11C)
# ---------------------------------------------------------------------------
class MessageCreateRequest(BaseModel):
    """Send a message in a conversation."""

    body: str = Field(..., min_length=1, max_length=5000)
    attachment_id: uuid.UUID | None = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    body: str
    sent_at: str
    edited_at: str | None = None
    created_at: str


class ReadReceiptResponse(BaseModel):
    user_id: str
    read_at: str


class MarkReadRequest(BaseModel):
    """Mark messages as read up to a given message."""

    message_id: uuid.UUID


# ---------------------------------------------------------------------------
# Announcements (Phase 11C)
# ---------------------------------------------------------------------------
class AnnouncementCreateRequest(BaseModel):
    """Create a new announcement (draft)."""

    title: str = Field(..., min_length=1, max_length=300)
    body: str = Field(..., min_length=1, max_length=10000)
    target_roles: list[str] = Field(
        ...,
        min_length=1,
        description="Target role codes, e.g. ['PAR', 'STD']",
    )
    target_class_ids: list[uuid.UUID] | None = Field(
        None,
        description="Target class UUIDs — NULL means all classes",
    )


class AnnouncementUpdateRequest(BaseModel):
    """Update a draft announcement."""

    title: str | None = Field(None, max_length=300)
    body: str | None = Field(None, max_length=10000)
    target_roles: list[str] | None = None
    target_class_ids: list[uuid.UUID] | None = None


class AnnouncementResponse(BaseModel):
    id: str
    school_id: str
    author_id: str
    title: str
    body: str
    target_roles: list[str]
    target_class_ids: list[str] | None = None
    published_at: str | None = None
    status: str
    created_at: str
    updated_at: str | None = None
