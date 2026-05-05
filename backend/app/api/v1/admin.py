"""Admin API endpoints — dashboard stats, user management, audit logs, settings, justifications."""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_current_user,
    requires_permission,
    requires_role,
)
from app.core.permissions import (
    ADM,
    DIR,
    PERM_ADM_AUDIT_READ,
    PERM_ADM_DASHBOARD_READ,
    PERM_ADM_IMPERSONATE,
    PERM_ADM_INVITATION_READ,
    PERM_ADM_USER_CREATE,
    PERM_ADM_USER_MANAGE,
    PERM_ADM_USER_READ,
    PERM_ERP_ABSENCE_REVIEW,
    PERM_ERP_ENROLLMENT_READ,
    PERM_IAM_PARENT_LINK_CREATE,
    PERM_IAM_PARENT_LINK_DELETE,
    PERM_IAM_PARENT_LINK_READ,
    SUP,
)
from app.core.redis import get_redis
from app.core.request_utils import get_client_ip, parse_device_name
from app.core.response import list_response, success_response
from app.schemas.auth import BatchRegisterRequest
from app.services.admin import AdminService
from app.services.auth import AuthService
from app.services.program_service import ProgramService

router = APIRouter(prefix="/admin", tags=["admin"])


def _set_auth_cookies(response: Response, result: dict) -> None:
    max_age = int(
        result.get("refresh_expires_in", settings.refresh_token_expire_days * 86400)
    )
    response.set_cookie(
        key="refresh_token",
        value=result["refresh_token"],
        httponly=True,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=max_age,
    )
    response.set_cookie(
        key="csrf_token",
        value=result["csrf_token"],
        httponly=False,
        secure=True,
        samesite="lax",
        path="/api/v1/auth",
        max_age=max_age,
    )


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


@router.get(
    "/enrollments",
    summary="List enrollments in school (admin/director)",
    response_description=(
        "Paginated school-wide enrollments with student, class, period, "
        "academic year and program embedded. Supports class_id, period_id, "
        "status, and missing_program filters."
    ),
)
async def list_enrollments_admin(
    auth: AuthContext = Depends(requires_permission(PERM_ERP_ENROLLMENT_READ)),
    db: AsyncSession = Depends(get_db),
    class_id: uuid.UUID | None = Query(None, description="Filter by class id."),
    period_id: uuid.UUID | None = Query(None, description="Filter by period id."),
    status: str | None = Query(
        None,
        description=(
            "Filter by enrollment status. One of: active, transferred, dropped."
        ),
    ),
    missing_program: bool = Query(
        False,
        description=(
            "If true, return only enrollments without an assigned program "
            "(the 'needs program assignment' backlog)."
        ),
    ),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Admin/Director enrollment list — used by the EnrollmentsPage UI.

    Distinct from the legacy ``GET /enrollments`` (which returns the
    *current student's* active enrollments — a backward-compatibility shim).
    """
    service = ProgramService(db)
    items, next_cursor, has_more = await service.list_enrollments_for_admin(
        auth=auth,
        class_id=class_id,
        period_id=period_id,
        status=status,
        missing_program=missing_program,
        cursor=cursor,
        limit=limit,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


@router.post(
    "/impersonate/{user_id}",
    summary="Start impersonating a user",
    response_description="Access token for the impersonated user",
)
async def impersonate_user(
    user_id: uuid.UUID,
    request: Request,
    response: Response,
    auth: AuthContext = Depends(requires_permission(PERM_ADM_IMPERSONATE)),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    user_agent = request.headers.get("User-Agent")
    result = await service.impersonate(
        target_user_id=user_id,
        admin_auth=auth,
        source="impersonation",
        ip_address=get_client_ip(request),
        user_agent=user_agent,
        device_name=parse_device_name(user_agent),
    )
    _set_auth_cookies(response, result)
    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "impersonation_active": result["impersonation_active"],
        }
    )


@router.post(
    "/stop-impersonation",
    summary="Stop impersonating and return to the admin session",
    response_description="Access token for the admin user",
)
async def stop_impersonation(
    request: Request,
    response: Response,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    user_agent = request.headers.get("User-Agent")
    result = await service.stop_impersonation(
        auth.session_id,
        source="impersonation_return",
        ip_address=get_client_ip(request),
        user_agent=user_agent,
        device_name=parse_device_name(user_agent),
    )
    _set_auth_cookies(response, result)
    return success_response(
        {
            "access_token": result["access_token"],
            "token_type": result["token_type"],
            "expires_in": result["expires_in"],
            "impersonation_active": result["impersonation_active"],
        }
    )


@router.get(
    "/users/{user_id}/login-history",
    summary="List a user's login history",
    response_description="Paginated login history for the target user",
)
async def list_user_login_history(
    user_id: uuid.UUID,
    auth: AuthContext = Depends(requires_role(ADM, DIR, SUP)),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    service = AuthService(db, redis)
    items, next_cursor, has_more = await service.list_login_history(
        target_user_id=user_id,
        auth=auth,
        limit=limit,
        cursor=cursor,
    )
    return list_response(items, next_cursor=next_cursor, has_more=has_more)


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
