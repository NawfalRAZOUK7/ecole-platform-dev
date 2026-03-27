"""Repository helpers for dashboard analytics and KPI computation."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import case, func, select

from app.models.audit import AuditLog
from app.models.billing import Invoice
from app.models.erp import AttendanceRecord, AttendanceSession, Class, Enrollment
from app.models.iam import InvitationCode, Session, User
from app.models.lms import Assignment, Course, Grade, Submission
from app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    """Low-level analytics queries for dashboards and KPIs."""

    async def count_active_users(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Session.user_id))).where(
                Session.school_id == school_id,
                Session.created_at >= from_dt,
                Session.created_at <= to_dt,
            )
        )
        return int(result.scalar_one() or 0)

    async def list_active_user_series(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        bucket: str,
    ) -> list[dict[str, Any]]:
        result = await self.db.execute(
            select(
                func.date_trunc(bucket, Session.created_at).label("bucket"),
                func.count(func.distinct(Session.user_id)).label("active_users"),
            )
            .where(
                Session.school_id == school_id,
                Session.created_at >= from_dt,
                Session.created_at <= to_dt,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        return [
            {
                "bucket": row.bucket,
                "active_users": int(row.active_users or 0),
            }
            for row in result
        ]

    async def count_users(
        self,
        *,
        school_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(User.id)).where(User.school_id == school_id)
        )
        return int(result.scalar_one() or 0)

    async def count_active_accounts(
        self,
        *,
        school_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(User.id))).where(
                User.school_id == school_id,
                User.status == "active",
            )
        )
        return int(result.scalar_one() or 0)

    async def attendance_summary(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        class_id: uuid.UUID | None = None,
    ) -> tuple[int, int]:
        query = (
            select(
                func.count(AttendanceRecord.id),
                func.count().filter(AttendanceRecord.status == "present"),
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
        )
        if class_id:
            query = query.where(AttendanceSession.class_id == class_id)
        result = await self.db.execute(query)
        total, present = result.one()
        return int(total or 0), int(present or 0)

    async def list_attendance_series(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        class_id: uuid.UUID | None,
        bucket: str,
    ) -> list[dict]:
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
        return [
            {
                "bucket": row.bucket,
                "total": int(row.total or 0),
                "present": int(row.present or 0),
                "absent": int(row.absent or 0),
                "excused": int(row.excused or 0),
            }
            for row in result
        ]

    async def average_grade(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        class_id: uuid.UUID | None = None,
        subject: str | None = None,
    ) -> float:
        query = (
            select(func.avg(Grade.score))
            .select_from(Grade)
            .join(Submission, Submission.id == Grade.submission_id)
            .join(Assignment, Assignment.id == Submission.assignment_id)
            .join(Course, Course.id == Assignment.course_id)
            .where(
                Course.school_id == school_id,
                Grade.created_at >= from_dt,
                Grade.created_at <= to_dt,
            )
        )
        if class_id:
            query = query.where(Course.class_id == class_id)
        if subject:
            query = query.where(Course.title == subject)
        result = await self.db.execute(query)
        return float(result.scalar_one() or 0)

    async def list_grade_scores(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        subject: str | None,
    ) -> list[float]:
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
        return [float(score) for score in result.scalars().all() if score is not None]

    async def billing_summary(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
    ) -> tuple[float, float, float]:
        invoiced_result = await self.db.execute(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.school_id == school_id,
                Invoice.issued_date >= from_date,
                Invoice.issued_date <= to_date,
            )
        )
        paid_result = await self.db.execute(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.school_id == school_id,
                Invoice.status == "paid",
                Invoice.issued_date >= from_date,
                Invoice.issued_date <= to_date,
            )
        )
        outstanding_result = await self.db.execute(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.school_id == school_id,
                Invoice.status != "paid",
                Invoice.issued_date >= from_date,
                Invoice.issued_date <= to_date,
            )
        )
        return (
            float(invoiced_result.scalar_one() or 0),
            float(paid_result.scalar_one() or 0),
            float(outstanding_result.scalar_one() or 0),
        )

    async def list_billing_series(
        self,
        *,
        school_id: uuid.UUID,
        from_date: date,
        to_date: date,
        bucket: str,
    ) -> list[dict]:
        result = await self.db.execute(
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
        return [
            {
                "bucket": row.bucket,
                "invoiced": float(row.invoiced or 0),
                "paid": float(row.paid or 0),
            }
            for row in result
        ]

    async def count_distinct_audit_users(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        action_types: list[str] | None = None,
        outcome: str | None = None,
    ) -> int:
        query = select(func.count(func.distinct(AuditLog.actor_id))).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= from_dt,
            AuditLog.created_at <= to_dt,
        )
        if action_types:
            query = query.where(AuditLog.action_type.in_(action_types))
        if outcome:
            query = query.where(AuditLog.outcome == outcome)
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

    async def list_engaged_user_series(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
        bucket: str,
        outcome: str | None = None,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                func.date_trunc(bucket, AuditLog.created_at).label("bucket"),
                func.count(func.distinct(AuditLog.actor_id)).label("engaged_users"),
            )
            .where(
                AuditLog.school_id == school_id,
                AuditLog.created_at >= from_dt,
                AuditLog.created_at <= to_dt,
            )
            .group_by("bucket")
            .order_by("bucket")
        )
        if outcome:
            query = query.where(AuditLog.outcome == outcome)
        result = await self.db.execute(query)
        return [
            {
                "bucket": row.bucket,
                "engaged_users": int(row.engaged_users or 0),
            }
            for row in result
        ]

    async def count_audit_events(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        action_types: list[str] | None = None,
        outcomes: list[str] | None = None,
    ) -> int:
        query = select(func.count()).where(
            AuditLog.school_id == school_id,
            AuditLog.created_at >= from_dt,
        )
        if action_types:
            query = query.where(AuditLog.action_type.in_(action_types))
        if outcomes:
            query = query.where(AuditLog.outcome.in_(outcomes))
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

    async def engagement_summary(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
        to_dt: datetime,
    ) -> tuple[int, int, int]:
        registered = await self.count_users(school_id=school_id)
        active = await self.count_active_users(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        engaged = await self.count_distinct_audit_users(
            school_id=school_id,
            from_dt=from_dt,
            to_dt=to_dt,
            outcome="success",
        )
        return registered, active, engaged

    async def count_invitations_created(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                InvitationCode.school_id == school_id,
                InvitationCode.created_at >= from_dt,
            )
        )
        return int(result.scalar() or 0)

    async def count_invitations_consumed(
        self,
        *,
        school_id: uuid.UUID,
        from_dt: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                InvitationCode.school_id == school_id,
                InvitationCode.created_at >= from_dt,
                InvitationCode.consumed_at.isnot(None),
            )
        )
        return int(result.scalar() or 0)

    async def list_enrollment_by_class(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[dict]:
        result = await self.db.execute(
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
        return [
            {
                "class_code": row.code,
                "student_count": int(row.student_count or 0),
            }
            for row in result
        ]

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        from app.models.erp import TeacherAssignment

        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())
