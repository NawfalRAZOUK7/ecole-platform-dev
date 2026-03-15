"""COM domain Pydantic schemas — request/response models.

Reference: Pack D5 — API Implementation Plan, Sprint 3 stories S-065 to S-067
"""

from __future__ import annotations

import uuid
from datetime import datetime

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
