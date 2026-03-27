"""Profile API endpoints — role-specific profile CRUD."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user, requires_permission
from app.core.permissions import PERM_PROF_ADMIN_READ, PERM_PROF_CHILD_READ
from app.core.request_utils import get_client_ip
from app.core.response import success_response
from app.services.profile import ProfileService

router = APIRouter(tags=["profiles"])


@router.get(
    "/me/profile",
    summary="Get current user's role-specific profile",
    response_description="User data with role-specific profile fields",
)
async def get_my_profile(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(await service.get_my_profile(auth))


@router.put(
    "/me/profile",
    summary="Update current user's role-specific profile",
    response_description="Updated profile",
)
async def update_my_profile(
    request: Request,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(
        await service.update_my_profile(
            auth=auth,
            body=await request.json(),
            client_ip=get_client_ip(request),
        )
    )


@router.get(
    "/admin/users/{user_id}/profile",
    summary="Admin: get any user's role-specific profile",
    response_description="User data with role-specific profile fields",
)
async def admin_get_user_profile(
    user_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_PROF_ADMIN_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(
        await service.get_admin_user_profile(user_id=user_id, auth=auth)
    )


@router.get(
    "/me/children",
    summary="List parent's linked children",
    response_description="Linked children with student profile data",
)
async def get_my_children(
    auth: AuthContext = Depends(requires_permission(PERM_PROF_CHILD_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = ProfileService(db)
    return success_response(await service.get_my_children(auth))
