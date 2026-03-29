"""Phase 14 analytics dashboard service."""

from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import AuthContext, verify_teacher_assignment
from app.core.permissions import TCH
from app.core.redis import redis_client
from app.repositories.analytics import AnalyticsRepository


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


def _series_bucket(period: str | None, *, default: str = "weekly") -> str:
    return period if period in {"daily", "weekly", "monthly"} else default


class DashboardAnalyticsService:
    """Cached analytics aggregations for the admin dashboard."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AnalyticsRepository(db)

    @staticmethod
    def resolve_window(
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

    async def verify_teacher_class_scope(
        self,
        *,
        auth: AuthContext,
        class_id: uuid.UUID | None,
    ) -> None:
        if auth.role != TCH or class_id is None:
            return
        teacher_classes = await self.repo.list_teacher_class_ids(
            teacher_id=auth.user_id,
            school_id=auth.school_id,
        )
        verify_teacher_assignment(class_id, teacher_classes)

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
        attendance_rate = (present_records / total_records * 100) if total_records > 0 else 0.0
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
            previous = await self.get_overview(
                school_id=school_id,
                from_date=from_date - timedelta(days=period_days),
                to_date=from_date - timedelta(days=1),
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

        bucket = {"daily": "day", "weekly": "week", "monthly": "month"}.get(period, "day")
        rows = await self.repo.list_attendance_series(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
            class_id=class_id,
            bucket=bucket,
        )
        total = 0
        present = 0
        series = []
        for row in rows:
            total += row["total"]
            present += row["present"]
            bucket_dt = row["bucket"]
            series.append(
                {
                    "label": bucket_dt.date().isoformat(),
                    "value": round((row["present"] / row["total"] * 100) if row["total"] else 0, 2),
                    "extra": {
                        "total": row["total"],
                        "present": row["present"],
                        "absent": row["absent"],
                        "excused": row["excused"],
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
        scores = await self.repo.list_grade_scores(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
            subject=subject,
        )
        buckets = {"0-5": 0, "5-10": 0, "10-15": 0, "15-20": 0}
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

        bucket = {"daily": "day", "weekly": "week", "monthly": "month"}.get(period, "month")
        rows = await self.repo.list_billing_series(
            school_id=school_id,
            from_date=from_date,
            to_date=to_date,
            bucket=bucket,
        )
        series = [
            {
                "label": row["bucket"].date().isoformat(),
                "value": row["invoiced"],
                "extra": {
                    "paid": row["paid"],
                    "outstanding": max(row["invoiced"] - row["paid"], 0),
                },
            }
            for row in rows
        ]
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
        period: str,
        compare: bool,
    ) -> dict[str, Any]:
        cache_key = self._cache_key(
            school_id,
            "engagement",
            from_date=from_date.isoformat(),
            to_date=to_date.isoformat(),
            period=period,
            compare=str(compare).lower(),
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        from_dt, to_dt = _utc_day_bounds(from_date, to_date)
        bucket = {"daily": "day", "weekly": "week", "monthly": "month"}.get(
            _series_bucket(period),
            "week",
        )
        registered, active, engaged = await self.repo.engagement_summary(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        active_series = await self.repo.list_active_user_series(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
            bucket=bucket,
        )
        engaged_series = await self.repo.list_engaged_user_series(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
            bucket=bucket,
            outcome="success",
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
            "notifications": [
                "notification.batch.create",
                "notification.preferences.update",
            ],
            "billing": ["fee_assignment.create", "payment.initiated"],
        }
        feature_adoption = []
        for feature, action_types in feature_specs.items():
            users = await self.repo.count_distinct_audit_users(
                school_id=school_id,
                from_dt=from_dt,
                to_dt=to_dt,
                action_types=action_types,
            )
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
                period=period,
                compare=False,
            )
            previous_active = previous_data["summary"]["active_users"]["current"]

        series_map: dict[str, dict[str, Any]] = {}
        for row in active_series:
            label = row["bucket"].date().isoformat()
            series_map[label] = {
                "label": label,
                "active_users": row["active_users"],
                "engaged_users": 0,
            }
        for row in engaged_series:
            label = row["bucket"].date().isoformat()
            bucket_item = series_map.setdefault(
                label,
                {
                    "label": label,
                    "active_users": 0,
                    "engaged_users": 0,
                },
            )
            bucket_item["engaged_users"] = row["engaged_users"]

        series = []
        for label in sorted(series_map):
            item = series_map[label]
            active_users = item["active_users"]
            engaged_users = item["engaged_users"]
            series.append(
                {
                    **item,
                    "engagement_rate": round(
                        (engaged_users / active_users) * 100 if active_users else 0.0,
                        2,
                    ),
                }
            )

        response = {
            "from_date": from_date.isoformat(),
            "to_date": to_date.isoformat(),
            "period": period,
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
            "series": series,
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
            "enrollment_by_class": await self.repo.list_enrollment_by_class(
                school_id=school_id
            ),
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
