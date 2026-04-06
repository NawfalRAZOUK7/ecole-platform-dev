"""Micro-school API endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import (
    PERM_MICRO_ENROLLMENT_CREATE,
    PERM_MICRO_ENROLLMENT_READ,
    PERM_MICRO_GROUP_CREATE,
    PERM_MICRO_GROUP_READ,
    PERM_MICRO_PAYMENT_CREATE,
    PERM_MICRO_PAYMENT_READ,
    PERM_MICRO_PROGRESS_CREATE,
    PERM_MICRO_PROGRESS_READ,
    PERM_MICRO_RESOURCE_MANAGE,
    PERM_MICRO_RESOURCE_READ,
    PERM_MICRO_SCHOOL_CREATE,
    PERM_MICRO_SCHOOL_MANAGE,
    PERM_MICRO_SCHOOL_READ,
)
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.micro_school import (
    MicroEnrollmentCreateRequest,
    MicroGroupCreateRequest,
    MicroPaymentCreateRequest,
    MicroProgressLogCreateRequest,
    MicroResourceCreateRequest,
    MicroSchoolCreateRequest,
    MicroSchoolUpdateRequest,
)
from app.services.micro_school_service import (
    MicroGroupService,
    MicroPaymentService,
    MicroProgressService,
    MicroSchoolService,
)

router = APIRouter(prefix="/micro", tags=["micro-school"])


@router.post(
    "/schools",
    status_code=201,
    summary="Create micro-school",
    description="Creates a micro-school under the authenticated school and returns the newly created record with its configured capacity and operating details.",
    response_description="Created micro-school",
)
async def create_micro_school(
    body: MicroSchoolCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_SCHOOL_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a micro-school managed by the authenticated school."""
    service = MicroSchoolService(db)
    return success_response(
        await service.create_micro_school(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/schools",
    summary="List micro-schools",
    description="Returns micro-schools visible to the authenticated school. Supports optional filtering by educator, city, and operating status.",
    response_description="List of micro-schools",
)
async def list_micro_schools(
    educator_id: uuid.UUID | None = Query(None),
    city: str | None = Query(None),
    status: str | None = Query(None, pattern="^(active|suspended|closed)$"),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List micro-schools visible within the authenticated school."""
    service = MicroSchoolService(db)
    items = await service.list_micro_schools(
        auth=auth,
        educator_id=educator_id,
        city=city,
        status=status,
    )
    return list_response(items)


@router.put(
    "/schools/{micro_school_id}",
    summary="Update micro-school",
    description="Updates an existing micro-school within the caller's school scope and returns the latest persisted configuration.",
    response_description="Updated micro-school",
)
async def update_micro_school(
    micro_school_id: uuid.UUID,
    body: MicroSchoolUpdateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_SCHOOL_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Update a micro-school within the authenticated school."""
    service = MicroSchoolService(db)
    return success_response(
        await service.update_micro_school(
            micro_school_id=micro_school_id,
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.post(
    "/groups",
    status_code=201,
    summary="Create micro-group",
    description="Creates a micro-group within a micro-school and returns the saved group record for scheduling and enrollment workflows.",
    response_description="Created micro-group",
)
async def create_micro_group(
    body: MicroGroupCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_GROUP_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a micro-group inside a micro-school."""
    service = MicroGroupService(db)
    return success_response(
        await service.create_group(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/schools/{micro_school_id}/groups",
    summary="List micro-groups",
    description="Lists the micro-groups attached to a specific micro-school within the authenticated user's school boundary.",
    response_description="List of micro-groups",
)
async def list_micro_groups(
    micro_school_id: uuid.UUID,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_GROUP_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List micro-groups for a micro-school."""
    service = MicroGroupService(db)
    return list_response(
        await service.list_groups(
            micro_school_id=micro_school_id,
            auth=auth,
        )
    )


@router.post(
    "/enrollments",
    status_code=201,
    summary="Create micro-enrollment",
    description="Enrolls a child into a micro-group and returns the created enrollment record, including the current enrollment status.",
    response_description="Created micro-enrollment",
)
async def create_micro_enrollment(
    body: MicroEnrollmentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_ENROLLMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Enroll a child into a micro-group."""
    service = MicroGroupService(db)
    return success_response(
        await service.create_enrollment(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/enrollments",
    summary="List micro-enrollments",
    description="Returns micro-school enrollments for the authenticated school. Supports filtering by micro-group, parent, and enrollment status.",
    response_description="List of micro-enrollments",
)
async def list_micro_enrollments(
    micro_group_id: uuid.UUID | None = Query(None),
    parent_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(active|withdrawn)$"),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_ENROLLMENT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List micro-enrollments for the authenticated school."""
    service = MicroGroupService(db)
    return list_response(
        await service.list_enrollments(
            auth=auth,
            micro_group_id=micro_group_id,
            parent_id=parent_id,
            status=status,
        )
    )


@router.post(
    "/payments",
    status_code=201,
    summary="Create micro-payment",
    description="Records a micro-school payment for the authenticated school and returns the stored payment entry with its current status.",
    response_description="Created micro-payment",
)
async def create_micro_payment(
    body: MicroPaymentCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_PAYMENT_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record a micro-school payment."""
    service = MicroPaymentService(db)
    return success_response(
        await service.create_payment(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/payments",
    summary="List micro-payments",
    description="Lists micro-school payments within the authenticated school scope with optional filters for school, parent, enrollment, and payment state.",
    response_description="List of micro-payments",
)
async def list_micro_payments(
    micro_school_id: uuid.UUID | None = Query(None),
    parent_id: uuid.UUID | None = Query(None),
    child_enrollment_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None, pattern="^(pending|paid|overdue)$"),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_PAYMENT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List micro-school payments for the authenticated school."""
    service = MicroPaymentService(db)
    return list_response(
        await service.list_payments(
            auth=auth,
            micro_school_id=micro_school_id,
            parent_id=parent_id,
            child_enrollment_id=child_enrollment_id,
            status=status,
        )
    )


@router.get(
    "/payments/analytics",
    summary="Get micro-payment analytics",
    description="Returns aggregate micro-school payment analytics for the authenticated school, optionally scoped to a specific micro-school.",
    response_description="Micro-payment analytics",
)
async def get_micro_payment_analytics(
    micro_school_id: uuid.UUID | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_PAYMENT_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Return aggregate analytics for micro-school payments."""
    service = MicroPaymentService(db)
    return success_response(
        await service.get_payment_analytics(
            auth=auth,
            micro_school_id=micro_school_id,
        )
    )


@router.post(
    "/resources",
    status_code=201,
    summary="Create micro-resource",
    description="Creates a learning resource for the micro-school program and returns the saved resource metadata for catalog management.",
    response_description="Created micro-resource",
)
async def create_micro_resource(
    body: MicroResourceCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_RESOURCE_MANAGE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a micro-school learning resource."""
    service = MicroSchoolService(db)
    return success_response(
        await service.create_resource(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/resources",
    summary="List micro-resources",
    description="Returns micro-school resources available to the authenticated school. Supports filtering by type, language, age group, and premium status.",
    response_description="List of micro-resources",
)
async def list_micro_resources(
    resource_type: str | None = Query(
        None,
        pattern="^(activity_sheet|song|game|lesson_plan)$",
    ),
    language: str | None = Query(None, pattern="^(ar|fr|en)$"),
    age_group: str | None = Query(None),
    is_premium: bool | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_RESOURCE_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List micro-school resources with optional filters."""
    service = MicroSchoolService(db)
    return list_response(
        await service.list_resources(
            auth=auth,
            resource_type=resource_type,
            language=language,
            age_group=age_group,
            is_premium=is_premium,
        )
    )


@router.post(
    "/progress-logs",
    status_code=201,
    summary="Create micro progress log",
    description="Creates a progress log entry for a micro-enrollment and returns the recorded observation for follow-up and reporting.",
    response_description="Created micro progress log",
)
async def create_micro_progress_log(
    body: MicroProgressLogCreateRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_PROGRESS_CREATE)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a progress log for a micro-enrollment."""
    service = MicroProgressService(db)
    return success_response(
        await service.create_progress_log(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )


@router.get(
    "/progress-logs",
    summary="List micro progress logs",
    description="Lists progress logs for micro-enrollments visible to the authenticated school, with optional filters for enrollment, educator, and date range.",
    response_description="List of micro progress logs",
)
async def list_micro_progress_logs(
    micro_enrollment_id: uuid.UUID | None = Query(None),
    educator_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    auth: AuthContext = Depends(requires_permission(PERM_MICRO_PROGRESS_READ)),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List progress logs for micro-enrollments."""
    service = MicroProgressService(db)
    return list_response(
        await service.list_progress_logs(
            auth=auth,
            micro_enrollment_id=micro_enrollment_id,
            educator_id=educator_id,
            date_from=date_from,
            date_to=date_to,
        )
    )
