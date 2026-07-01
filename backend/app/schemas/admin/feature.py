"""Feature toggle Pydantic schemas — Phase 11E.

Reference: Phase 11E — Feature Toggles
Request/response models for feature toggle CRUD and active features listing.
"""

from __future__ import annotations


from pydantic import BaseModel, Field


class FeatureToggleCreateRequest(BaseModel):
    """Create a new feature toggle."""

    feature_key: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique snake_case key, e.g. 'content_library'",
    )
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    enabled_globally: bool = Field(False)
    enabled_school_ids: list[str] = Field(
        default_factory=list,
        description="List of school UUID strings to enable for",
    )
    enabled_role_codes: list[str] = Field(
        default_factory=list,
        description="List of role codes to enable for, e.g. ['ADM', 'TCH']",
    )


class FeatureToggleUpdateRequest(BaseModel):
    """Update an existing feature toggle (partial)."""

    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)
    enabled_globally: bool | None = None
    enabled_school_ids: list[str] | None = Field(
        None,
        description="List of school UUID strings to enable for",
    )
    enabled_role_codes: list[str] | None = Field(
        None,
        description="List of role codes to enable for",
    )


class FeatureToggleResponse(BaseModel):
    """Response for a single feature toggle."""

    id: str
    feature_key: str
    display_name: str
    description: str | None = None
    enabled_globally: bool
    enabled_school_ids: list[str]
    enabled_role_codes: list[str]
    created_at: str
    updated_at: str | None = None


class ActiveFeaturesResponse(BaseModel):
    """Response listing active feature keys for current user context."""

    features: list[str] = Field(..., description="List of active feature keys")
