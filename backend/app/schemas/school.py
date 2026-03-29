"""Pydantic schemas for school CRUD endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class SchoolCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    name_ar: str | None = Field(None, max_length=255)
    code: str = Field(..., min_length=1, max_length=50)
    massar_code: str | None = Field(None, max_length=50)
    status: str = Field("active", pattern="^(active|suspended|trial)$")
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    website: str | None = Field(None, max_length=500)
    logo_path: str | None = Field(None, max_length=500)
    max_students: int | None = Field(None, ge=0)
    max_teachers: int | None = Field(None, ge=0)
    subscription_plan: str | None = Field(None, max_length=50)
    subscription_expires_at: datetime | None = None
    timezone: str = Field("Africa/Casablanca", max_length=50)
    default_language: str = Field("fr", max_length=5)
    grading_scale: str = Field("moroccan_20", max_length=20)
    settings: dict[str, Any] = Field(default_factory=dict)


class SchoolUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    name_ar: str | None = Field(None, max_length=255)
    code: str | None = Field(None, min_length=1, max_length=50)
    massar_code: str | None = Field(None, max_length=50)
    status: str | None = Field(None, pattern="^(active|suspended|trial)$")
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    region: str | None = Field(None, max_length=100)
    phone: str | None = Field(None, max_length=30)
    email: EmailStr | None = None
    website: str | None = Field(None, max_length=500)
    logo_path: str | None = Field(None, max_length=500)
    max_students: int | None = Field(None, ge=0)
    max_teachers: int | None = Field(None, ge=0)
    subscription_plan: str | None = Field(None, max_length=50)
    subscription_expires_at: datetime | None = None
    timezone: str | None = Field(None, max_length=50)
    default_language: str | None = Field(None, max_length=5)
    grading_scale: str | None = Field(None, max_length=20)
    settings: dict[str, Any] | None = None


class SchoolResponse(BaseModel):
    id: str
    name: str
    name_ar: str | None = None
    code: str
    massar_code: str | None = None
    status: str
    address: str | None = None
    city: str | None = None
    region: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    logo_path: str | None = None
    max_students: int | None = None
    max_teachers: int | None = None
    subscription_plan: str | None = None
    subscription_expires_at: str | None = None
    timezone: str
    default_language: str
    grading_scale: str
    settings: dict[str, Any]
    is_active: bool
    is_subscription_valid: bool
    deleted_at: str | None = None
    created_at: str
    updated_at: str | None = None


class SchoolListResponse(BaseModel):
    items: list[SchoolResponse] = Field(default_factory=list)
