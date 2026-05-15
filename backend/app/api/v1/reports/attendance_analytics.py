"""Attendance analytics and alerting endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.request_utils import get_client_ip
from app.core.response import list_response, success_response
from app.schemas.academic.attendance_analytics import AttendanceThresholdCheckRequest
from app.services.academic.attendance_analytics import AttendanceAnalyticsService

router = APIRouter(prefix="/analytics/attendance", tags=["attendance-analytics"])


@router.get("/student/{student_id}", summary="Get attendance stats for a student")
async def get_student_attendance_analytics(
    student_id: uuid.UUID,
    period_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:attendance-analytics:read")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceAnalyticsService(db)
    return success_response(
        await service.compute_student_absence_rate(
            student_id=student_id,
            period_id=period_id,
            auth=auth,
        )
    )


@router.get("/class/{class_id}", summary="Get attendance stats for a class")
async def get_class_attendance_analytics(
    class_id: uuid.UUID,
    period_id: uuid.UUID = Query(...),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:attendance-analytics:read")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceAnalyticsService(db)
    return success_response(
        await service.compute_class_absence_rates(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
        )
    )


@router.get("/trends/{class_id}", summary="Get attendance trend data for a class")
async def get_attendance_trends(
    class_id: uuid.UUID,
    period_id: uuid.UUID = Query(...),
    granularity: str = Query("weekly", pattern="^(daily|weekly)$"),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:attendance-analytics:read")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceAnalyticsService(db)
    return success_response(
        await service.get_absence_trends(
            class_id=class_id,
            period_id=period_id,
            granularity=granularity,
            auth=auth,
        )
    )


@router.get("/alerts", summary="List attendance threshold alerts")
async def list_attendance_alerts(
    period_id: uuid.UUID | None = Query(None),
    threshold: str | None = Query(None, pattern="^(warning|critical)$"),
    program_id: uuid.UUID | None = Query(
        None,
        description=(
            "G49: filter to alerts for students enrolled in the given program "
            "for the alert's period."
        ),
    ),
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:attendance-alert:manage")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceAnalyticsService(db)
    items = await service.list_alerts(
        auth=auth,
        period_id=period_id,
        threshold_exceeded=threshold,
        program_id=program_id,
    )
    return list_response(items, next_cursor=None, has_more=False)


@router.post("/check-thresholds", summary="Run attendance threshold checks")
async def check_attendance_thresholds(
    body: AttendanceThresholdCheckRequest,
    request: Request,
    auth: AuthContext = Depends(
        requires_permission("PERM-ERP:attendance-alert:manage")
    ),
    db: AsyncSession = Depends(get_db),
):
    service = AttendanceAnalyticsService(db)
    return success_response(
        await service.check_thresholds_and_alert(
            body=body,
            auth=auth,
            ip_address=get_client_ip(request),
        )
    )
