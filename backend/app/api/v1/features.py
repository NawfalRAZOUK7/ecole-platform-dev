"""Feature toggle API endpoints — Phase 11E.

Reference: Phase 11E — Feature Toggles
Endpoints:
  POST   /features           — Create toggle (SYS/CONTENT_MGR)
  GET    /features           — List all toggles (SYS/CONTENT_MGR)
  GET    /features/active    — Active features for current user (any authenticated)
  GET    /features/{id}      — Get single toggle (SYS/CONTENT_MGR)
  PUT    /features/{id}      — Update toggle (SYS/CONTENT_MGR)
  DELETE /features/{id}      — Delete toggle (SYS/CONTENT_MGR)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    requires_permission,
)
from app.core.exceptions import ConflictError, NotFoundError
from app.core.feature_flags import (
    get_active_features,
    invalidate_feature_cache,
)
from app.core.response import list_response, success_response
from app.models.feature import FeatureToggle
from app.schemas.feature import (
    FeatureToggleCreateRequest,
    FeatureToggleResponse,
    FeatureToggleUpdateRequest,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/features", tags=["features"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _toggle_to_response(toggle: FeatureToggle) -> dict:
    """Convert a FeatureToggle model to response dict."""
    return {
        "id": str(toggle.id),
        "feature_key": toggle.feature_key,
        "display_name": toggle.display_name,
        "description": toggle.description,
        "enabled_globally": toggle.enabled_globally,
        "enabled_school_ids": toggle.enabled_school_ids or [],
        "enabled_role_codes": toggle.enabled_role_codes or [],
        "created_at": toggle.created_at.isoformat() if toggle.created_at else None,
        "updated_at": toggle.updated_at.isoformat() if toggle.updated_at else None,
    }


def _toggle_snapshot(toggle: FeatureToggle) -> dict:
    """Snapshot for audit trail entity_before/entity_after."""
    return {
        "id": str(toggle.id),
        "feature_key": toggle.feature_key,
        "enabled_globally": toggle.enabled_globally,
        "enabled_school_ids": toggle.enabled_school_ids or [],
        "enabled_role_codes": toggle.enabled_role_codes or [],
    }


# ---------------------------------------------------------------------------
# GET /features/active — Active features for current user (any authenticated)
# ---------------------------------------------------------------------------
@router.get(
    "/active",
    summary="Get active features for current user",
    response_description="List of active feature keys",
)
async def get_active_features_for_user(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns list of feature keys that are enabled for the current user's
    school and role. Used by frontend for conditional feature rendering.
    """
    features = await get_active_features(db, school_id=auth.school_id, role_code=auth.role)
    return success_response({"features": features})


# ---------------------------------------------------------------------------
# POST /features — Create toggle (SYS/CONTENT_MGR)
# ---------------------------------------------------------------------------
@router.post(
    "",
    summary="Create feature toggle",
    response_description="Created feature toggle",
    status_code=201,
)
async def create_feature_toggle(
    body: FeatureToggleCreateRequest,
    auth: AuthContext = Depends(requires_permission("PERM-SYS:feature:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new feature toggle. Only SYS and CONTENT_MGR roles can manage toggles."""
    # Check uniqueness
    existing = await db.execute(
        select(FeatureToggle).where(FeatureToggle.feature_key == body.feature_key)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(
            f"Feature toggle '{body.feature_key}' already exists",
            error_code="ERR-FEATURE-409",
        )

    toggle = FeatureToggle(
        feature_key=body.feature_key,
        display_name=body.display_name,
        description=body.description,
        enabled_globally=body.enabled_globally,
        enabled_school_ids=body.enabled_school_ids,
        enabled_role_codes=body.enabled_role_codes,
    )
    db.add(toggle)
    await db.flush()

    # Audit trail
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="feature_toggle.create",
        outcome="success",
        target_type="feature_toggle",
        target_id=toggle.id,
        entity_after=_toggle_snapshot(toggle),
    )

    return success_response(_toggle_to_response(toggle))


# ---------------------------------------------------------------------------
# GET /features — List all toggles (SYS/CONTENT_MGR)
# ---------------------------------------------------------------------------
@router.get(
    "",
    summary="List all feature toggles",
    response_description="List of all feature toggles",
)
async def list_feature_toggles(
    auth: AuthContext = Depends(requires_permission("PERM-SYS:feature:manage")),
    db: AsyncSession = Depends(get_db),
):
    """List all feature toggles. Only SYS and CONTENT_MGR roles."""
    result = await db.execute(
        select(FeatureToggle).order_by(FeatureToggle.feature_key)
    )
    toggles = result.scalars().all()

    items = [_toggle_to_response(t) for t in toggles]
    return list_response(items, has_more=False)


# ---------------------------------------------------------------------------
# GET /features/{toggle_id} — Get single toggle (SYS/CONTENT_MGR)
# ---------------------------------------------------------------------------
@router.get(
    "/{toggle_id}",
    summary="Get feature toggle by ID",
    response_description="Feature toggle details",
)
async def get_feature_toggle(
    toggle_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-SYS:feature:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Get a single feature toggle by ID."""
    result = await db.execute(
        select(FeatureToggle).where(FeatureToggle.id == toggle_id)
    )
    toggle = result.scalar_one_or_none()
    if toggle is None:
        raise NotFoundError(
            "Feature toggle not found", error_code="ERR-FEATURE-404"
        )

    return success_response(_toggle_to_response(toggle))


# ---------------------------------------------------------------------------
# PUT /features/{toggle_id} — Update toggle (SYS/CONTENT_MGR)
# ---------------------------------------------------------------------------
@router.put(
    "/{toggle_id}",
    summary="Update feature toggle",
    response_description="Updated feature toggle",
)
async def update_feature_toggle(
    toggle_id: uuid.UUID,
    body: FeatureToggleUpdateRequest,
    auth: AuthContext = Depends(requires_permission("PERM-SYS:feature:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Update a feature toggle. Partial update — only provided fields are changed."""
    result = await db.execute(
        select(FeatureToggle).where(FeatureToggle.id == toggle_id)
    )
    toggle = result.scalar_one_or_none()
    if toggle is None:
        raise NotFoundError(
            "Feature toggle not found", error_code="ERR-FEATURE-404"
        )

    # Snapshot before
    before = _toggle_snapshot(toggle)

    # Apply partial updates
    if body.display_name is not None:
        toggle.display_name = body.display_name
    if body.description is not None:
        toggle.description = body.description
    if body.enabled_globally is not None:
        toggle.enabled_globally = body.enabled_globally
    if body.enabled_school_ids is not None:
        toggle.enabled_school_ids = body.enabled_school_ids
    if body.enabled_role_codes is not None:
        toggle.enabled_role_codes = body.enabled_role_codes

    await db.flush()

    # Invalidate cache
    await invalidate_feature_cache(toggle.feature_key)

    # Audit trail
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="feature_toggle.update",
        outcome="success",
        target_type="feature_toggle",
        target_id=toggle.id,
        entity_before=before,
        entity_after=_toggle_snapshot(toggle),
    )

    return success_response(_toggle_to_response(toggle))


# ---------------------------------------------------------------------------
# DELETE /features/{toggle_id} — Delete toggle (SYS/CONTENT_MGR)
# ---------------------------------------------------------------------------
@router.delete(
    "/{toggle_id}",
    summary="Delete feature toggle",
    response_description="Deletion confirmation",
)
async def delete_feature_toggle(
    toggle_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission("PERM-SYS:feature:manage")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a feature toggle. Removes it entirely (not soft-delete)."""
    result = await db.execute(
        select(FeatureToggle).where(FeatureToggle.id == toggle_id)
    )
    toggle = result.scalar_one_or_none()
    if toggle is None:
        raise NotFoundError(
            "Feature toggle not found", error_code="ERR-FEATURE-404"
        )

    # Snapshot before deletion
    before = _toggle_snapshot(toggle)
    feature_key = toggle.feature_key

    await db.delete(toggle)
    await db.flush()

    # Invalidate cache
    await invalidate_feature_cache(feature_key)

    # Audit trail
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="feature_toggle.delete",
        outcome="success",
        target_type="feature_toggle",
        target_id=toggle_id,
        entity_before=before,
    )

    return success_response({"deleted": True, "feature_key": feature_key})
