"""Phase 14 analytics dashboard API."""

from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import (
    AuthContext,
    get_teacher_class_ids,
    requires_permission,
    verify_teacher_assignment,
)
from app.core.permissions import PERM_REP_ANALYTICS_READ
from app.core.response import success_response
from app.services.dashboard_analytics import DashboardAnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _resolve_window(
    *,
    from_date: date | None,
    to_date: date | None,
    period: str | None,
) -> tuple[date, date]:
    if from_date and to_date:
        return from_date, to_date

    today = date.today()
    if period == "this_week":
        return today - timedelta(days=today.weekday()), today
    if period == "this_month":
        return today.replace(day=1), today
    if period == "this_period":
        return today - timedelta(days=30), today
    return today - timedelta(days=29), today


async def _verify_teacher_class_scope(
    *,
    auth: AuthContext,
    db: AsyncSession,
    class_id: uuid.UUID | None,
) -> None:
    if auth.role != "TCH" or class_id is None:
        return
    teacher_classes = await get_teacher_class_ids(auth.user_id, auth.school_id, db)
    verify_teacher_assignment(class_id, teacher_classes)


@router.get("/overview", summary="School-wide KPI overview")
async def analytics_overview(
    period: str | None = Query(None),
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    compare: bool = Query(False),
    auth: AuthContext = Depends(requires_permission(PERM_REP_ANALYTICS_READ)),
    db: AsyncSession = Depends(get_db),
):
    start_date, end_date = _resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=period,
    )
    service = DashboardAnalyticsService(db)
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
    await _verify_teacher_class_scope(auth=auth, db=db, class_id=class_id)
    service = DashboardAnalyticsService(db)
    start_date, end_date = _resolve_window(
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
    start_date, end_date = _resolve_window(
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
    start_date, end_date = _resolve_window(
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
    start_date, end_date = _resolve_window(
        from_date=from_date,
        to_date=to_date,
        period=period,
    )
    return success_response(
        await service.get_engagement(
            school_id=auth.school_id,
            from_date=start_date,
            to_date=end_date,
            compare=compare,
        )
    )
