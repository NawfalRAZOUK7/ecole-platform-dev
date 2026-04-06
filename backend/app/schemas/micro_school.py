"""Pydantic schemas for the micro-school domain."""

import uuid
from datetime import date as date_type
from datetime import datetime as datetime_type

from pydantic import BaseModel, Field


class MicroSchoolCreateRequest(BaseModel):
    """Payload for creating a micro-school."""

    educator_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=200)
    neighborhood: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=8, max_length=20)
    max_capacity: int = Field(20, gt=0)
    status: str = Field("active", pattern="^(active|suspended|closed)$")


class MicroSchoolUpdateRequest(BaseModel):
    """Payload for updating a micro-school."""

    name: str | None = Field(None, min_length=1, max_length=200)
    neighborhood: str | None = Field(None, min_length=1, max_length=200)
    city: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, min_length=8, max_length=20)
    max_capacity: int | None = Field(None, gt=0)
    status: str | None = Field(None, pattern="^(active|suspended|closed)$")


class MicroSchoolResponse(BaseModel):
    """Serialized micro-school response."""

    id: str
    educator_id: str
    name: str
    neighborhood: str
    city: str
    phone: str
    max_capacity: int
    status: str
    created_at: str
    updated_at: str | None = None


class MicroGroupCreateRequest(BaseModel):
    """Payload for creating a micro-group."""

    micro_school_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    age_range_min: int = Field(..., ge=2, le=6)
    age_range_max: int = Field(..., ge=2, le=6)


class MicroGroupUpdateRequest(BaseModel):
    """Payload for updating a micro-group."""

    name: str | None = Field(None, min_length=1, max_length=100)
    age_range_min: int | None = Field(None, ge=2, le=6)
    age_range_max: int | None = Field(None, ge=2, le=6)


class MicroGroupResponse(BaseModel):
    """Serialized micro-group response."""

    id: str
    micro_school_id: str
    name: str
    age_range_min: int
    age_range_max: int
    created_at: str
    updated_at: str | None = None


class MicroEnrollmentCreateRequest(BaseModel):
    """Payload for creating a micro-enrollment."""

    micro_group_id: uuid.UUID
    child_name: str = Field(..., min_length=1, max_length=200)
    parent_id: uuid.UUID
    date_of_birth: date_type
    enrolled_at: datetime_type | None = None
    status: str = Field("active", pattern="^(active|withdrawn)$")


class MicroEnrollmentUpdateRequest(BaseModel):
    """Payload for updating a micro-enrollment."""

    child_name: str | None = Field(None, min_length=1, max_length=200)
    parent_id: uuid.UUID | None = None
    date_of_birth: date_type | None = None
    enrolled_at: datetime_type | None = None
    status: str | None = Field(None, pattern="^(active|withdrawn)$")


class MicroEnrollmentResponse(BaseModel):
    """Serialized micro-enrollment response."""

    id: str
    micro_group_id: str
    parent_id: str
    child_name: str
    date_of_birth: str
    enrolled_at: str
    status: str
    created_at: str
    updated_at: str | None = None


class MicroPaymentCreateRequest(BaseModel):
    """Payload for creating a micro-payment."""

    micro_school_id: uuid.UUID
    parent_id: uuid.UUID
    child_enrollment_id: uuid.UUID
    amount: float = Field(..., gt=0)
    currency: str = Field("MAD", min_length=3, max_length=3)
    period_type: str = Field("monthly", pattern="^(weekly|monthly)$")
    period_start: date_type
    period_end: date_type
    paid_at: datetime_type | None = None
    status: str = Field("pending", pattern="^(pending|paid|overdue)$")


class MicroPaymentUpdateRequest(BaseModel):
    """Payload for updating a micro-payment."""

    amount: float | None = Field(None, gt=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    period_type: str | None = Field(None, pattern="^(weekly|monthly)$")
    period_start: date_type | None = None
    period_end: date_type | None = None
    paid_at: datetime_type | None = None
    status: str | None = Field(None, pattern="^(pending|paid|overdue)$")


class MicroPaymentResponse(BaseModel):
    """Serialized micro-payment response."""

    id: str
    micro_school_id: str
    parent_id: str
    child_enrollment_id: str
    amount: float
    currency: str
    period_type: str
    period_start: str
    period_end: str
    paid_at: str | None = None
    status: str
    created_at: str
    updated_at: str | None = None


class MicroResourceCreateRequest(BaseModel):
    """Payload for creating a micro-resource."""

    title: str = Field(..., min_length=1, max_length=300)
    description: str | None = Field(None, max_length=4000)
    resource_type: str = Field(
        ...,
        pattern="^(activity_sheet|song|game|lesson_plan)$",
    )
    age_group: str = Field(..., min_length=1, max_length=20)
    language: str = Field("ar", pattern="^(ar|fr|en)$")
    file_url: str | None = Field(None, max_length=500)
    is_premium: bool = False


class MicroResourceUpdateRequest(BaseModel):
    """Payload for updating a micro-resource."""

    title: str | None = Field(None, min_length=1, max_length=300)
    description: str | None = Field(None, max_length=4000)
    resource_type: str | None = Field(
        None,
        pattern="^(activity_sheet|song|game|lesson_plan)$",
    )
    age_group: str | None = Field(None, min_length=1, max_length=20)
    language: str | None = Field(None, pattern="^(ar|fr|en)$")
    file_url: str | None = Field(None, max_length=500)
    is_premium: bool | None = None


class MicroResourceResponse(BaseModel):
    """Serialized micro-resource response."""

    id: str
    title: str
    description: str | None = None
    resource_type: str
    age_group: str
    language: str
    file_url: str | None = None
    is_premium: bool
    created_at: str
    updated_at: str | None = None


class MicroProgressLogCreateRequest(BaseModel):
    """Payload for creating a micro progress log."""

    micro_enrollment_id: uuid.UUID
    educator_id: uuid.UUID | None = None
    date: date_type
    note: str = Field(..., min_length=1, max_length=4000)
    photo_url: str | None = Field(None, max_length=500)
    milestone_tag: str | None = Field(None, max_length=50)


class MicroProgressLogUpdateRequest(BaseModel):
    """Payload for updating a micro progress log."""

    date: date_type | None = None
    note: str | None = Field(None, min_length=1, max_length=4000)
    photo_url: str | None = Field(None, max_length=500)
    milestone_tag: str | None = Field(None, max_length=50)


class MicroProgressLogResponse(BaseModel):
    """Serialized micro progress log response."""

    id: str
    micro_enrollment_id: str
    educator_id: str
    date: str
    note: str
    photo_url: str | None = None
    milestone_tag: str | None = None
    created_at: str
    updated_at: str | None = None


__all__ = [
    "MicroSchoolCreateRequest",
    "MicroSchoolUpdateRequest",
    "MicroSchoolResponse",
    "MicroGroupCreateRequest",
    "MicroGroupUpdateRequest",
    "MicroGroupResponse",
    "MicroEnrollmentCreateRequest",
    "MicroEnrollmentUpdateRequest",
    "MicroEnrollmentResponse",
    "MicroPaymentCreateRequest",
    "MicroPaymentUpdateRequest",
    "MicroPaymentResponse",
    "MicroResourceCreateRequest",
    "MicroResourceUpdateRequest",
    "MicroResourceResponse",
    "MicroProgressLogCreateRequest",
    "MicroProgressLogUpdateRequest",
    "MicroProgressLogResponse",
]
