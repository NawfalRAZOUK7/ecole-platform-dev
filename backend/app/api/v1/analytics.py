"""Analytics dashboard API."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.permissions import PERM_REP_ANALYTICS_READ
from app.core.response import success_response
from app.services.dashboard_analytics import DashboardAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", summary="School-wide KPI overview")
async def analytics_overview(
    period: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    start_date, end_date = service.resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=period,
    )
    return success_response(
        await service.get_overview(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            compare=compare,
        )
    )


@router.get("/attendance", summary="Attendance trends")
async def analytics_attendance(
    period: str = Query("weekly", pattern="^(daily|weekly|monthly)$"),
    class_id: uuid.UUID | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    await service.verify_teacher_class_scope(auth=auth, class_id=class_id)
    start_date, end_date = service.resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=None,
    )
    return success_response(
        await service.get_attendance(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            period=period,
            class_id=class_id,
            compare=compare,
        )
    )


@router.get("/grades", summary="Grade distribution analytics")
async def analytics_grades(
    period: str | None = Query(None),
    subject: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    start_date, end_date = service.resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=period,
    )
    return success_response(
        await service.get_grades(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            subject=subject,
            compare=compare,
        )
    )


@router.get("/billing", summary="Billing trend analytics")
async def analytics_billing(
    period: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    start_date, end_date = service.resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=None,
    )
    return success_response(
        await service.get_billing(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            period=period,
            compare=compare,
        )
    )


@router.get("/engagement", summary="Platform engagement analytics")
async def analytics_engagement(
    period: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardAnalyticsService(db)
    window_period = (
        period if period in {"this_week", "this_month", "this_period"} else None
    )
    bucket_period = period if period in {"daily", "weekly", "monthly"} else "weekly"
    start_date, end_date = service.resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=window_period,
    )
    return success_response(
        await service.get_engagement(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            period=bucket_period,
            compare=compare,
        )
    )
