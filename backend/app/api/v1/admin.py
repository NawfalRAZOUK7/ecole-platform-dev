"""Admin API endpoints — dashboard stats, user management, audit logs, settings, justifications."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_ADM_AUDIT_READ,
    PERM_ADM_DASHBOARD_READ,
    PERM_ADM_INVITATION_READ,
    PERM_ADM_USER_CREATE,
    PERM_ADM_USER_MANAGE,
    PERM_ADM_USER_READ,
    PERM_ERP_ABSENCE_REVIEW,
    PERM_IAM_PARENT_LINK_CREATE,
    PERM_IAM_PARENT_LINK_DELETE,
    PERM_IAM_PARENT_LINK_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.auth import BatchRegisterRequest
from app.services.admin import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/dashboard",
    summary="Admin dashboard statistics",
    response_description="Dashboard summary counts and role breakdowns",
)
async def dashboard_stats(
    auth: AuthContext = Depends(requires_permission(PERM_ADM_DASHBOARD_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(await service.get_dashboard_stats(auth))


@router.get(
    "/users",
    summary="List users in school",
    response_description="Paginated school user list",
)
async def list_users(
    auth: AuthContext = Depends(requires_permission(PERM_ADM_USER_READ)),
    db: AsyncSession = Depends(get_db),
    search: str | None = Query(None, description="Search by name or email"),
    role: str | None = Query(None, description="Filter by role code"),
    status: str | None = Query(None, description="Filter by status"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = AdminService(db)
    data, next_cursor, has_more = await service.list_users(
        auth=auth,
        search=search,
        role=role,
        status=status,
        cursor=cursor,
        limit=limit,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.put(
    "/users/{user_id}/suspend",
    summary="Suspend a user",
    response_description="Suspended user identifier and status",
)
async def suspend_user(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_USER_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.suspend_user(
            user_id=user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.put(
    "/users/{user_id}/activate",
    summary="Activate a user",
    response_description="Activated user identifier and status",
)
async def activate_user(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_USER_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.activate_user(
            user_id=user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.put(
    "/users/{user_id}/role",
    summary="Change user role",
    response_description="Updated user role",
)
async def change_user_role(
    user_id: uuid.UUID,
    request: Request,
    role: str = Query(..., description="New role code"),
    auth: AuthContext = Depends(requires_permission(PERM_ADM_USER_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.change_user_role(
            user_id=user_id,
            role=role,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.get(
    "/invitations",
    summary="List invitation codes",
    response_description="Paginated invitation code list",
)
async def list_invitations(
    auth: AuthContext = Depends(requires_permission(PERM_ADM_INVITATION_READ)),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query(None, description="Filter: active, consumed, expired"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = AdminService(db)
    data, next_cursor, has_more = await service.list_invitations(
        auth=auth,
        status=status,
        cursor=cursor,
        limit=limit,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/audit-logs",
    summary="List audit logs",
    response_description="Paginated audit log list",
)
async def list_audit_logs(
    auth: AuthContext = Depends(requires_permission(PERM_ADM_AUDIT_READ)),
    db: AsyncSession = Depends(get_db),
    action_type: str | None = Query(None),
    correlation_id: str | None = Query(None),
    date_from: str | None = Query(None, description="ISO date"),
    date_to: str | None = Query(None, description="ISO date"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = AdminService(db)
    data, next_cursor, has_more = await service.list_audit_logs(
        auth=auth,
        action_type=action_type,
        correlation_id=correlation_id,
        date_from=date_from,
        date_to=date_to,
        cursor=cursor,
        limit=limit,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.get(
    "/justifications",
    summary="List absence justifications",
    response_description="Paginated absence justifications",
)
async def list_justifications(
    auth: AuthContext = Depends(requires_permission(PERM_ERP_ABSENCE_REVIEW)),
    db: AsyncSession = Depends(get_db),
    status: str | None = Query("pending", description="Filter by status"),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = AdminService(db)
    data, next_cursor, has_more = await service.list_justifications(
        auth=auth,
        status=status,
        cursor=cursor,
        limit=limit,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.post(
    "/register-batch",
    status_code=201,
    summary="Bulk register users",
    response_description="Created users, temporary passwords, and validation errors",
)
async def register_batch(
    body: BatchRegisterRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_USER_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.register_batch(
            items=body.users,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.post(
    "/parent-child-links",
    status_code=201,
    summary="Create parent-child link",
    response_description="Created parent-child link",
)
async def create_parent_child_link(
    request: Request,
    parent_user_id: uuid.UUID = Query(..., description="Parent user ID"),
    child_user_id: uuid.UUID = Query(..., description="Student user ID"),
    auth: AuthContext = Depends(requires_permission(PERM_IAM_PARENT_LINK_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.create_parent_child_link(
            parent_user_id=parent_user_id,
            child_user_id=child_user_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )


@router.get(
    "/parent-child-links",
    summary="List parent-child links",
    response_description="Paginated parent-child link list",
)
async def list_parent_child_links(
    parent_id: uuid.UUID | None = Query(None, description="Filter by parent user ID"),
    student_id: uuid.UUID | None = Query(None, description="Filter by student user ID"),
    status: str | None = Query(None, description="Filter by status (active, revoked)"),
    cursor: str | None = Query(
        None, description="Cursor for pagination (linked_at ISO)"
    ),
    limit: int = Query(20, ge=1, le=100),
    auth: AuthContext = Depends(requires_permission(PERM_IAM_PARENT_LINK_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    data, next_cursor, has_more = await service.list_parent_child_links(
        parent_id=parent_id,
        student_id=student_id,
        status=status,
        cursor=cursor,
        limit=limit,
        auth=auth,
    )
    return list_response(data, next_cursor=next_cursor, has_more=has_more)


@router.delete(
    "/parent-child-links/{link_id}",
    summary="Revoke parent-child link",
    response_description="Revoked parent-child link status",
)
async def revoke_parent_child_link(
    link_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_IAM_PARENT_LINK_DELETE)),
    db: AsyncSession = Depends(get_db),
):
    service = AdminService(db)
    return success_response(
        await service.revoke_parent_child_link(
            link_id=link_id,
            auth=auth,
            client_ip=get_client_ip(request),
        )
    )
