"""Phase 14 analytics dashboard service."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import redis_client
from app.models.audit import AuditLog
from app.models.billing import Invoice
from app.models.erp import AttendanceRecord, AttendanceSession, Class, Enrollment
from app.models.lms import Assignment, Course, Grade, Submission
from app.repositories.reports import AnalyticsRepository


def _utc_day_bounds(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return start_dt, end_dt


def _change_percent(current: float, previous: float | None) -> float | None:
    if previous is None:
        return None
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def _trend(current: float, previous: float | None) -> str:
    if previous is None or current == previous:
        return "flat"
    return "up" if current > previous else "down"


def _comparison_metric(current: float, previous: float | None) -> dict[str, Any]:
    return {
        "current": round(current, 2),
        "previous": round(previous, 2) if previous is not None else None,
        "change_percent": _change_percent(current, previous),
        "trend": _trend(current, previous),
    }


class DashboardAnalyticsService:
    """Cached analytics aggregations for the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    async def get_overview(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "overview",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        from_dt, to_dt = _utc_day_bounds(from_date, to_date)
        active_users = await self.repo.count_active_users(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        total_records, present_records = await self.repo.attendance_summary(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
        )
        attendance_rate = (
            (present_records / total_records) * 100 if total_records > 0 else 0.0
        )
        average_grade = await self.repo.average_grade(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        invoiced, paid, _outstanding = await self.repo.billing_summary(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
        )
        collection_rate = (paid / invoiced) * 100 if invoiced > 0 else 0.0

        previous = None
        if compare:
            period_days = max((to_date - from_date).days + 1, 1)
            previous_from = from_date - timedelta(days=period_days)
            previous_to = from_date - timedelta(days=1)
            previous = await self.get_overview(
                school_id=school_id,
                from_date=previous_from,
                to_date=previous_to,
                compare=False,
            )

        previous_metrics = {
            item["key"]: item["value"]["current"] for item in previous["metrics"]
        } if previous else {}

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "metrics": [
                {
                    "key": "active_users",
                    "label": "Active users",
                    "value": _comparison_metric(
                        float(active_users),
                        previous_metrics.get("active_users"),
                    ),
                },
                {
                    "key": "attendance_rate",
                    "label": "Attendance rate",
                    "value": _comparison_metric(
                        attendance_rate,
                        previous_metrics.get("attendance_rate"),
                    ),
                },
                {
                    "key": "average_grade",
                    "label": "Average grade",
                    "value": _comparison_metric(
                        average_grade,
                        previous_metrics.get("average_grade"),
                    ),
                },
                {
                    "key": "collection_rate",
                    "label": "Collection rate",
                    "value": _comparison_metric(
                        collection_rate,
                        previous_metrics.get("collection_rate"),
                    ),
                },
            ],
        }
        await self._set_cached(cache_key, response)
        return response

    async def get_attendance(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        period: str,
        class_id: uuid.UUID | None,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "attendance",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            period=period,
            class_id=str(class_id) if class_id else "",
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        bucket = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }.get(period, "day")

        query = (
            select(
                func.date_trunc(bucket, AttendanceSession.session_date).label("bucket"),
                func.count(AttendanceRecord.id).label("total"),
                func.count().filter(AttendanceRecord.status == "present").label("present"),
                func.count().filter(AttendanceRecord.status == "absent").label("absent"),
                func.count().filter(AttendanceRecord.status == "excused").label("excused"),
            )
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceRecord.school_id == school_id,
                AttendanceSession.session_date >= from_date,
                AttendanceSession.session_date <= to_date,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        if class_id:
            query = query.where(AttendanceSession.class_id == class_id)
        result = await self.db.execute(query)
        series = []
        total = 0
        present = 0
        for row in result:
            total += int(row.total or 0)
            present += int(row.present or 0)
            series.append(
                {
                    "label": row.bucket.date().isoformat(),
                    "value": round(
                        ((row.present or 0) / row.total) * 100 if row.total else 0,
                        2,
                    ),
                    "extra": {
                        "total": int(row.total or 0),
                        "present": int(row.present or 0),
                        "absent": int(row.absent or 0),
                        "excused": int(row.excused or 0),
                    },
                }
            )

        previous_rate = None
        if compare:
            period_days = max((to_date - from_date).days + 1, 1)
            previous_data = await self.get_attendance(
                school_id=school_id,
                from_date=from_date - timedelta(days=period_days),
                to_date=from_date - timedelta(days=1),
                period=period,
                class_id=class_id,
                compare=False,
            )
            previous_rate = previous_data["summary"]["rate"]["current"]

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "period": period,
            "class_id": str(class_id) if class_id else None,
            "summary": {
                "rate": _comparison_metric(
                    (present / total) * 100 if total > 0 else 0.0,
                    previous_rate,
                ),
                "total_records": total,
            },
            "series": series,
        }
        await self._set_cached(cache_key, response)
        return response

    async def get_grades(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        subject: str | None,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "grades",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            subject=subject or "",
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        from_dt, to_dt = _utc_day_bounds(from_date, to_date)
        query = (
            select(Grade.score)
            .select_from(Grade)
            .join(Submission, Submission.id == Grade.submission_id)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Grade.created_at >= from_dt,
                Grade.created_at < to_dt,
            )
        )
        if subject:
            query = query.where(Course.title == subject)
        result = await self.db.execute(query)
        scores = [float(score) for score in result.scalars().all() if score is not None]

        buckets = {
            "0-5": 0,
            "5-10": 0,
            "10-15": 0,
            "15-20": 0,
        }
        for score in scores:
            if score < 5:
                buckets["0-5"] += 1
            elif score < 10:
                buckets["5-10"] += 1
            elif score < 15:
                buckets["10-15"] += 1
            else:
                buckets["15-20"] += 1

        current_average = round(sum(scores) / len(scores), 2) if scores else 0.0
        previous_average = None
        if compare:
            period_days = max((to_date - from_date).days + 1, 1)
            previous_data = await self.get_grades(
                school_id=school_id,
                from_date=from_date - timedelta(days=period_days),
                to_date=from_date - timedelta(days=1),
                subject=subject,
                compare=False,
            )
            previous_average = previous_data["summary"]["average"]["current"]

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "subject": subject,
            "summary": {
                "average": _comparison_metric(current_average, previous_average),
                "count": len(scores),
            },
            "distribution": [
                {"label": label, "count": count} for label, count in buckets.items()
            ],
        }
        await self._set_cached(cache_key, response)
        return response

    async def get_billing(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        period: str,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "billing",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            period=period,
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        bucket = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
        }.get(period, "month")

        series_query = (
            select(
                func.date_trunc(bucket, Invoice.issued_date).label("bucket"),
                func.sum(Invoice.total_amount).label("invoiced"),
                func.sum(
                    case((Invoice.status == "paid", Invoice.total_amount), else_=0)
                ).label("paid"),
            )
            .where(
                Invoice.school_id == school_id,
                Invoice.issued_date >= from_date,
                Invoice.issued_date <= to_date,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        result = await self.db.execute(series_query)
        series = []
        for row in result:
            invoiced = float(row.invoiced or 0)
            paid = float(row.paid or 0)
            series.append(
                {
                    "label": row.bucket.date().isoformat(),
                    "value": invoiced,
                    "extra": {
                        "paid": paid,
                        "outstanding": max(invoiced - paid, 0),
                    },
                }
            )

        invoiced, paid, outstanding = await self.repo.billing_summary(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
        )
        previous_collection = None
        if compare:
            period_days = max((to_date - from_date).days + 1, 1)
            previous_data = await self.get_billing(
                school_id=school_id,
                from_date=from_date - timedelta(days=period_days),
                to_date=from_date - timedelta(days=1),
                period=period,
                compare=False,
            )
            previous_collection = previous_data["summary"]["collection_rate"]["current"]

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "period": period,
            "summary": {
                "invoiced": round(invoiced, 2),
                "paid": round(paid, 2),
                "outstanding": round(outstanding, 2),
                "collection_rate": _comparison_metric(
                    (paid / invoiced) * 100 if invoiced > 0 else 0.0,
                    previous_collection,
                ),
            },
            "series": series,
        }
        await self._set_cached(cache_key, response)
        return response

    async def get_engagement(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "engagement",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        from_dt, to_dt = _utc_day_bounds(from_date, to_date)
        registered, active, engaged = await self.repo.engagement_summary(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )

        mau_from = max(to_date - timedelta(days=29), from_date)
        mau = await self.repo.count_active_users(
            school_id=school_id,
            from_dt=datetime.combine(mau_from, time.min, tzinfo=timezone.utc),
            to_dt=to_dt,
        )

        feature_specs = {
            "messages": ["conversation.create", "message.send"],
            "content": ["content.progress.update", "content.assign"],
            "notifications": ["notification.batch.create", "notification.preferences.update"],
            "billing": ["fee_assignment.create", "payment.initiated"],
        }
        feature_adoption = []
        for feature, action_types in feature_specs.items():
            result = await self.db.execute(
                select(func.count(func.distinct(AuditLog.actor_id))).where(
                    AuditLog.school_id == school_id,
                    AuditLog.created_at >= from_dt,
                    AuditLog.created_at <= to_dt,
                    AuditLog.action_type.in_(action_types),
                )
            )
            users = int(result.scalar_one() or 0)
            feature_adoption.append(
                {
                    "feature": feature,
                    "users": users,
                    "adoption_rate": round((users / active) * 100, 2) if active else 0.0,
                }
            )

        previous_active = None
        if compare:
            period_days = max((to_date - from_date).days + 1, 1)
            previous_data = await self.get_engagement(
                school_id=school_id,
                from_date=from_date - timedelta(days=period_days),
                to_date=from_date - timedelta(days=1),
                compare=False,
            )
            previous_active = previous_data["summary"]["active_users"]["current"]

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "summary": {
                "registered_users": registered,
                "dau": active,
                "mau": mau,
                "active_users": _comparison_metric(float(active), previous_active),
                "engaged_users": engaged,
            },
            "funnel": [
                {"label": "registered", "value": registered},
                {"label": "active", "value": active},
                {"label": "engaged", "value": engaged},
            ],
            "feature_adoption": feature_adoption,
        }
        await self._set_cached(cache_key, response)
        return response

    async def get_school_analytics_snapshot(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> dict[str, Any]:
        enrollments_result = await self.db.execute(
            select(
                Class.code,
                func.count(func.distinct(Enrollment.student_id)).label("student_count"),
            )
            .select_from(Enrollment)
            .join(Class, Class.id == Enrollment.class_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.status == "active",
            )
            .group_by(Class.code)
            .order_by(Class.code.asc())
        )
        return {
            "overview": await self.get_overview(
                school_id=school_id,
                from_date=from_date,
                to_date=to_date,
                compare=False,
            ),
            "attendance": await self.get_attendance(
                school_id=school_id,
                from_date=from_date,
                to_date=to_date,
                period="weekly",
                class_id=None,
                compare=False,
            ),
            "grades": await self.get_grades(
                school_id=school_id,
                from_date=from_date,
                to_date=to_date,
                subject=None,
                compare=False,
            ),
            "billing": await self.get_billing(
                school_id=school_id,
                from_date=from_date,
                to_date=to_date,
                period="monthly",
                compare=False,
            ),
            "enrollment_by_class": [
                {
                    "class_code": row.code,
                    "student_count": int(row.student_count or 0),
                }
                for row in enrollments_result
            ],
        }

    async def _get_cached(self, cache_key: str) -> dict[str, Any] | None:
        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
        return None

    async def _set_cached(self, cache_key: str, payload: dict[str, Any]) -> None:
        await redis_client.set(
            cache_key,
            json.dumps(payload),
            ex=settings.analytics_cache_ttl_seconds,
        )

    def _cache_key(self, school_id: uuid.UUID, name: str, **parts: str) -> str:
        serialized = ":".join(f"{key}={parts[key]}" for key in sorted(parts))
        return f"ecole:{school_id}:analytics:{name}:{serialized}"
