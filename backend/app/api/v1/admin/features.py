"""Feature toggle API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.permissions import PERM_SYS_FEATURE_MANAGE
from app.core.response import list_response, success_response
from app.schemas.admin.feature import FeatureToggleCreateRequest, FeatureToggleUpdateRequest
from app.services.admin.features import FeatureService

router = APIRouter(prefix="/features", tags=["features"])


@router.get(
    "/active",
    summary="Get active features for current user",
    response_description="List of active feature keys",
)
async def get_active_features_for_user(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return success_response(
        await service.get_active_features(
            school_id=auth.school_id,
            role_code=auth.role,
        )
    )


@router.post(
    "",
    status_code=201,
    summary="Create feature toggle",
    response_description="Created feature toggle",
)
async def create_feature_toggle(
    body: FeatureToggleCreateRequest,
    auth: AuthContext = Depends(requires_permission(PERM_SYS_FEATURE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return success_response(
        await service.create_feature_toggle(
            feature_key=body.feature_key,
            display_name=body.display_name,
            description=body.description,
            enabled_globally=body.enabled_globally,
            enabled_school_ids=body.enabled_school_ids,
            enabled_role_codes=body.enabled_role_codes,
            school_id=auth.school_id,
            actor_id=auth.user_id,
        )
    )


@router.get(
    "",
    summary="List all feature toggles",
    response_description="List of all feature toggles",
)
async def list_feature_toggles(
    auth: AuthContext = Depends(requires_permission(PERM_SYS_FEATURE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return list_response(await service.list_feature_toggles(), has_more=False)


@router.get(
    "/{toggle_id}",
    summary="Get feature toggle by ID",
    response_description="Feature toggle details",
)
async def get_feature_toggle(
    toggle_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_SYS_FEATURE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return success_response(await service.get_feature_toggle(toggle_id))


@router.put(
    "/{toggle_id}",
    summary="Update feature toggle",
    response_description="Updated feature toggle",
)
async def update_feature_toggle(
    toggle_id: uuid.UUID,
    body: FeatureToggleUpdateRequest,
    auth: AuthContext = Depends(requires_permission(PERM_SYS_FEATURE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return success_response(
        await service.update_feature_toggle(
            toggle_id=toggle_id,
            display_name=body.display_name,
            description=body.description,
            enabled_globally=body.enabled_globally,
            enabled_school_ids=body.enabled_school_ids,
            enabled_role_codes=body.enabled_role_codes,
            school_id=auth.school_id,
            actor_id=auth.user_id,
        )
    )


@router.delete(
    "/{toggle_id}",
    summary="Delete feature toggle",
    response_description="Deletion confirmation",
)
async def delete_feature_toggle(
    toggle_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_SYS_FEATURE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = FeatureService(db)
    return success_response(
        await service.delete_feature_toggle(
            toggle_id=toggle_id,
            school_id=auth.school_id,
            actor_id=auth.user_id,
        )
    )
