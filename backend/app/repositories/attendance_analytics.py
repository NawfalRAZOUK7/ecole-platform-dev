"""Repository helpers for attendance analytics and threshold alerts."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import case, func, select

from app.models.erp import (
    AttendanceAlert,
    AttendanceRecord,
    AttendanceSession,
    Enrollment,
)
from app.models.iam import User
from app.repositories.base import BaseRepository


class AttendanceAnalyticsRepository(BaseRepository):
    """Attendance analytics queries and alert persistence."""

    async def compute_student_absence_count(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> tuple[int, int]:
        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status != "excused", 1), else_=0)),
                    0,
                ),
            )
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceRecord.student_id == student_id,
                AttendanceSession.period_id == period_id,
            )
        )
        absence_count, total_sessions = result.one()
        return int(absence_count or 0), int(total_sessions or 0)

    async def list_class_students(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:
        result = await self.db.execute(
            select(Enrollment.student_id, User.full_name)
            .join(User, User.id == Enrollment.student_id)
            .where(
                Enrollment.class_id == class_id,
                Enrollment.period_id == period_id,
                Enrollment.status == "active",
            )
            .order_by(User.full_name.asc())
        )
        return [(student_id, full_name) for student_id, full_name in result.all()]

    async def compute_class_absence_rates(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, int, int]]:
        result = await self.db.execute(
            select(
                AttendanceRecord.student_id,
                func.coalesce(
                    func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)),
                    0,
                ),
                func.coalesce(
                    func.sum(case((AttendanceRecord.status != "excused", 1), else_=0)),
                    0,
                ),
            )
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.period_id == period_id,
            )
            .group_by(AttendanceRecord.student_id)
        )
        return [
            (student_id, int(absence_count or 0), int(total_sessions or 0))
            for student_id, absence_count, total_sessions in result.all()
        ]

    async def get_absence_trends(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        granularity: str = "weekly",
    ) -> list[tuple[date, int, int]]:
        result = await self.db.execute(
            select(AttendanceSession.session_date, AttendanceRecord.status)
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.period_id == period_id,
            )
            .order_by(AttendanceSession.session_date.asc())
        )

        aggregates: dict[date, dict[str, int]] = {}
        for session_date, status in result.all():
            if status == "excused":
                continue
            bucket = (
                session_date
                if granularity == "daily"
                else session_date - timedelta(days=session_date.weekday())
            )
            aggregates.setdefault(
                bucket,
                {"absent_count": 0, "total_sessions": 0},
            )
            aggregates[bucket]["total_sessions"] += 1
            if status == "absent":
                aggregates[bucket]["absent_count"] += 1

        return [
            (bucket, values["absent_count"], values["total_sessions"])
            for bucket, values in sorted(aggregates.items())
        ]

    async def get_attendance_alert(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        threshold_exceeded: str,
    ) -> AttendanceAlert | None:
        result = await self.db.execute(
            select(AttendanceAlert).where(
                AttendanceAlert.student_id == student_id,
                AttendanceAlert.period_id == period_id,
                AttendanceAlert.threshold_exceeded == threshold_exceeded,
            )
        )
        return result.scalar_one_or_none()

    async def create_attendance_alert(
        self,
        **kwargs: Any,
    ) -> AttendanceAlert:
        alert = AttendanceAlert(**kwargs)
        self.db.add(alert)
        await self.db.flush()
        return alert

    async def list_alerts(
        self,
        *,
        school_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
        threshold_exceeded: str | None = None,
    ) -> list[AttendanceAlert]:
        query = select(AttendanceAlert).where(AttendanceAlert.school_id == school_id)
        if period_id is not None:
            query = query.where(AttendanceAlert.period_id == period_id)
        if threshold_exceeded is not None:
            query = query.where(
                AttendanceAlert.threshold_exceeded == threshold_exceeded
            )
        result = await self.db.execute(
            query.order_by(
                AttendanceAlert.created_at.desc(),
                AttendanceAlert.absence_rate.desc(),
            )
        )
        return list(result.scalars().all())

    async def list_period_students(
        self,
        *,
        school_id: uuid.UUID,
        period_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, str]]:
        result = await self.db.execute(
            select(Enrollment.student_id, User.full_name)
            .join(User, User.id == Enrollment.student_id)
            .where(
                Enrollment.school_id == school_id,
                Enrollment.period_id == period_id,
                Enrollment.status == "active",
            )
            .order_by(User.full_name.asc())
        )
        return [(student_id, full_name) for student_id, full_name in result.all()]

    async def list_user_names(
        self,
        *,
        user_ids: list[uuid.UUID],
    ) -> dict[uuid.UUID, str]:
        if not user_ids:
            return {}
        result = await self.db.execute(
            select(User.id, User.full_name).where(User.id.in_(user_ids))
        )
        return {user_id: full_name for user_id, full_name in result.all()}
