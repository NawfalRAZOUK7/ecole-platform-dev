"""Pydantic schemas for role-specific profile endpoints (Phase 1B).

Reference: Phase 1B — Role-Specific Profile Tables
Schemas for StudentProfile, ParentProfile, TeacherProfile CRUD.
"""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = Field(None, max_length=20)
    avatar_url: str | None = None


class ProfileResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    school_id: UUID
    phone: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ProfileAvatarResponse(BaseModel):
    avatar_url: str
    updated_at: datetime


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------
class StudentProfileUpdate(BaseModel):
    student_number: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: str | None = Field(None, pattern="^(male|female|other)$")
    class_level: str | None = Field(None, max_length=50)
    nationality: str | None = Field(None, max_length=100)
    guardian_notes: str | None = None


class StudentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    school_id: UUID
    student_number: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    class_level: str | None = None
    nationality: str | None = None
    guardian_notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Parent Profile
# ---------------------------------------------------------------------------
class ParentProfileUpdate(BaseModel):
    relationship_type: str | None = Field(
        None, pattern="^(father|mother|guardian|other)$"
    )
    cin_number: str | None = Field(None, max_length=30)
    address: str | None = None
    profession: str | None = Field(None, max_length=200)
    emergency_phone: str | None = Field(None, max_length=20)


class ParentProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    school_id: UUID
    relationship_type: str | None = None
    cin_number: str | None = None
    address: str | None = None
    profession: str | None = None
    emergency_phone: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Teacher Profile
# ---------------------------------------------------------------------------
class TeacherProfileUpdate(BaseModel):
    employee_id: str | None = Field(None, max_length=50)
    subject_specialty: str | None = Field(None, max_length=200)
    qualification: str | None = Field(None, max_length=200)
    hire_date: date | None = None


class TeacherProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    school_id: UUID
    employee_id: str | None = None
    subject_specialty: str | None = None
    qualification: str | None = None
    hire_date: date | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Combined profile response (wraps user + role-specific data)
# ---------------------------------------------------------------------------
class UserProfileResponse(BaseModel):
    """Combined user + role-specific profile for GET /me/profile."""

    user_id: UUID
    email: str
    full_name: str
    phone: str | None = None
    role: str
    school_id: UUID
    student_profile: StudentProfileResponse | None = None
    parent_profile: ParentProfileResponse | None = None
    teacher_profile: TeacherProfileResponse | None = None
