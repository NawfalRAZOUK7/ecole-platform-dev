"""Repository helpers for attendance analytics and threshold alerts."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from sqlalchemy import Date, DateTime, case, cast, func, select

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
        if granularity == "weekly":
            # date_trunc needs a timestamp; cast date → timestamp, then back to date
            bucket_expr = func.date_trunc(
                "week",
                cast(AttendanceSession.session_date, DateTime),
            ).cast(Date)
        else:
            bucket_expr = AttendanceSession.session_date

        absent_count = func.sum(
            case((AttendanceRecord.status == "absent", 1), else_=0)
        ).label("absent_count")
        total_count = func.count(AttendanceRecord.id).label("total_sessions")

        stmt = (
            select(bucket_expr.label("bucket"), absent_count, total_count)
            .select_from(AttendanceRecord)
            .join(
                AttendanceSession,
                AttendanceSession.id == AttendanceRecord.attendance_session_id,
            )
            .where(
                AttendanceSession.class_id == class_id,
                AttendanceSession.period_id == period_id,
                AttendanceRecord.status != "excused",
            )
            .group_by(bucket_expr)
            .order_by(bucket_expr.asc())
        )
        result = await self.db.execute(stmt)
        return [
            (
                row.bucket.date() if hasattr(row.bucket, "date") else row.bucket,
                int(row.absent_count or 0),
                int(row.total_sessions or 0),
            )
            for row in result.all()
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
        program_id: uuid.UUID | None = None,
    ) -> list[AttendanceAlert]:
        query = select(AttendanceAlert).where(AttendanceAlert.school_id == school_id)
        if period_id is not None:
            query = query.where(AttendanceAlert.period_id == period_id)
        if threshold_exceeded is not None:
            query = query.where(
                AttendanceAlert.threshold_exceeded == threshold_exceeded
            )
        if program_id is not None:
            # G49 Phase 2.5: filter to alerts for students enrolled in the
            # given program for the alert's period.
            query = query.where(
                select(Enrollment.id)
                .where(
                    Enrollment.school_id == AttendanceAlert.school_id,
                    Enrollment.student_id == AttendanceAlert.student_id,
                    Enrollment.period_id == AttendanceAlert.period_id,
                    Enrollment.program_id == program_id,
                )
                .exists()
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
