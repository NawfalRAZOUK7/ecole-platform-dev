"""Repository helpers for Phase 14 reports, analytics, and exports."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import decode_cursor, encode_cursor
from app.models.audit import AuditLog
from app.models.billing import Invoice, PaymentAttempt
from app.models.erp import (
    AbsenceJustification,
    AttendanceRecord,
    AttendanceSession,
    Class,
    Enrollment,
    Period,
    TeacherAssignment,
)
from app.models.iam import Membership, ParentChildLink, Session, User
from app.models.lms import Assignment, Course, Grade, Submission
from app.models.reporting import DataExport, ReportJob


class ReportsRepository:
    """Persistence and query helpers for report jobs and exports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_report_job(self, job: ReportJob) -> ReportJob:
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_report_job(self, job_id: uuid.UUID) -> ReportJob | None:
        result = await self.db.execute(
            select(ReportJob).where(ReportJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def find_cached_report(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        report_type: str,
        parameters_hash: str,
        since: datetime,
        now: datetime,
    ) -> ReportJob | None:
        result = await self.db.execute(
            select(ReportJob)
            .where(
                ReportJob.school_id == school_id,
                ReportJob.requester_id == requester_id,
                ReportJob.type == report_type,
                ReportJob.parameters_hash == parameters_hash,
                ReportJob.status == "ready",
                ReportJob.created_at >= since,
                or_(ReportJob.expires_at.is_(None), ReportJob.expires_at > now),
            )
            .order_by(ReportJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_report_jobs(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
        report_type: str | None,
        period_id: uuid.UUID | None,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[ReportJob], str | None, bool]:
        query = select(ReportJob).where(ReportJob.school_id == school_id)
        if requester_role not in {"ADM", "DIR"}:
            query = query.where(ReportJob.requester_id == requester_id)

        if report_type:
            query = query.where(ReportJob.type == report_type)
        if status:
            query = query.where(ReportJob.status == status)
        if period_id:
            query = query.where(ReportJob.parameters["period_id"].astext == str(period_id))

        query = query.order_by(ReportJob.created_at.desc(), ReportJob.id.desc())

        if cursor:
            last_id, last_created_at = decode_cursor(cursor)
            if last_created_at:
                cursor_dt = datetime.fromisoformat(last_created_at)
                query = query.where(
                    or_(
                        ReportJob.created_at < cursor_dt,
                        and_(
                            ReportJob.created_at == cursor_dt,
                            ReportJob.id < last_id,
                        ),
                    )
                )

        result = await self.db.execute(query.limit(limit + 1))
        rows = list(result.scalars().all())
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        next_cursor = None
        if rows and has_more:
            next_cursor = encode_cursor(rows[-1].id, rows[-1].created_at.isoformat())
        return rows, next_cursor, has_more

    async def list_expired_report_jobs(
        self,
        *,
        now: datetime,
    ) -> list[ReportJob]:
        result = await self.db.execute(
            select(ReportJob).where(
                ReportJob.file_path.is_not(None),
                ReportJob.expires_at.is_not(None),
                ReportJob.expires_at <= now,
            )
        )
        return list(result.scalars().all())

    async def create_export_log(self, export: DataExport) -> DataExport:
        self.db.add(export)
        await self.db.flush()
        return export

    async def get_user_in_school(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_period_in_school(
        self,
        *,
        period_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Period | None:
        result = await self.db.execute(
            select(Period).where(Period.id == period_id, Period.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_class_in_school(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Class | None:
        result = await self.db.execute(
            select(Class).where(Class.id == class_id, Class.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def list_parent_child_ids(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(ParentChildLink.child_user_id).where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return set(result.scalars().all())

    async def list_periods(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[Period]:
        result = await self.db.execute(
            select(Period)
            .where(Period.school_id == school_id)
            .order_by(Period.date_start.desc(), Period.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_classes(
        self,
        *,
        school_id: uuid.UUID,
    ) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .where(Class.school_id == school_id)
            .order_by(Class.name.asc(), Class.code.asc())
        )
        return list(result.scalars().all())

    async def list_classes_for_teacher(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[Class]:
        result = await self.db.execute(
            select(Class)
            .join(TeacherAssignment, TeacherAssignment.class_id == Class.id)
            .where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
                Class.school_id == school_id,
            )
            .distinct()
            .order_by(Class.name.asc(), Class.code.asc())
        )
        return list(result.scalars().all())

    async def list_students_for_class(
        self,
        *,
        class_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .join(Enrollment, Enrollment.student_id == User.id)
            .where(
                User.school_id == school_id,
                Enrollment.school_id == school_id,
                Enrollment.class_id == class_id,
                Enrollment.status == "active",
            )
            .order_by(User.full_name.asc())
        )
        return list(result.scalars().all())

    async def list_users_by_role(
        self,
        *,
        school_id: uuid.UUID,
        role_code: str,
        limit: int = 200,
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                User.school_id == school_id,
                Membership.school_id == school_id,
                Membership.role_code == role_code,
                Membership.status == "active",
            )
            .order_by(User.full_name.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_children(
        self,
        *,
        parent_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .join(ParentChildLink, ParentChildLink.child_user_id == User.id)
            .where(
                ParentChildLink.parent_user_id == parent_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
                User.school_id == school_id,
            )
            .order_by(User.full_name.asc())
        )
        return list(result.scalars().all())

    async def list_teacher_class_ids(
        self,
        *,
        teacher_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> set[uuid.UUID]:
        result = await self.db.execute(
            select(TeacherAssignment.class_id).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.school_id == school_id,
            )
        )
        return set(result.scalars().all())

    async def count_export_rows(
        self,
        *,
        school_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
    ) -> int:
        query = self._build_export_query(
            school_id=school_id,
            entity=entity,
            filters=filters,
            count_only=True,
        )
        result = await self.db.execute(query)
        return int(result.scalar_one() or 0)

    async def fetch_export_rows(
        self,
        *,
        school_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
        offset: int,
        limit: int,
    ) -> list[dict[str, Any]]:
        query = self._build_export_query(
            school_id=school_id,
            entity=entity,
            filters=filters,
            count_only=False,
        ).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return [dict(row._mapping) for row in result]

    def _build_export_query(
        self,
        *,
        school_id: uuid.UUID,
        entity: str,
        filters: dict[str, Any],
        count_only: bool,
    ):
        class_id = filters.get("class_id")
        student_id = filters.get("student_id")
        parent_id = filters.get("parent_id")
        period_id = filters.get("period_id")
        status = filters.get("status")
        from_date = filters.get("from_date")
        to_date = filters.get("to_date")
        if isinstance(from_date, str):
            from_date = date.fromisoformat(from_date)
        if isinstance(to_date, str):
            to_date = date.fromisoformat(to_date)

        if entity == "students":
            if count_only:
                query = (
                    select(func.count(func.distinct(User.id)))
                    .join(
                        Membership,
                        Membership.user_id == User.id,
                    )
                    .where(
                        User.school_id == school_id,
                        Membership.school_id == school_id,
                        Membership.role_code == "STD",
                        Membership.status == "active",
                    )
                )
            else:
                query = (
                    select(
                        User.id.label("student_id"),
                        User.full_name.label("student_name"),
                        User.email.label("student_email"),
                        Class.code.label("class_code"),
                        Period.label.label("period_label"),
                        User.status.label("status"),
                    )
                    .join(
                        Membership,
                        Membership.user_id == User.id,
                    )
                    .outerjoin(
                        Enrollment,
                        and_(
                            Enrollment.student_id == User.id,
                            Enrollment.school_id == school_id,
                            Enrollment.status == "active",
                        ),
                    )
                    .outerjoin(Class, Class.id == Enrollment.class_id)
                    .outerjoin(Period, Period.id == Enrollment.period_id)
                    .where(
                        User.school_id == school_id,
                        Membership.school_id == school_id,
                        Membership.role_code == "STD",
                        Membership.status == "active",
                    )
                    .order_by(User.full_name.asc())
                )
            if class_id:
                query = query.where(Enrollment.class_id == uuid.UUID(str(class_id)))
            if period_id:
                query = query.where(Enrollment.period_id == uuid.UUID(str(period_id)))
            if student_id:
                query = query.where(User.id == uuid.UUID(str(student_id)))
            return query

        if entity == "grades":
            if count_only:
                query = (
                    select(func.count(Grade.id))
                    .select_from(Grade)
                    .join(Submission, Submission.id == Grade.submission_id)
                    .join(Assignment, Assignment.id == Submission.assignment_id)
                    .join(Course, Course.id == Assignment.course_id)
                    .where(Course.school_id == school_id)
                )
            else:
                query = (
                    select(
                        Submission.student_id.label("student_id"),
                        Course.title.label("subject"),
                        Assignment.title.label("assignment_title"),
                        Grade.score.label("score"),
                        Assignment.total_points.label("total_points"),
                        Grade.feedback_text.label("feedback"),
                        Grade.published_at.label("published_at"),
                    )
                    .join(Submission, Submission.id == Grade.submission_id)
                    .join(Assignment, Assignment.id == Submission.assignment_id)
                    .join(Course, Course.id == Assignment.course_id)
                    .where(Course.school_id == school_id)
                    .order_by(Grade.published_at.desc().nullslast(), Grade.id.desc())
                )
            if student_id:
                query = query.where(Submission.student_id == uuid.UUID(str(student_id)))
            if class_id:
                query = query.where(Course.class_id == uuid.UUID(str(class_id)))
            if from_date:
                query = query.where(func.date(Grade.created_at) >= from_date)
            if to_date:
                query = query.where(func.date(Grade.created_at) <= to_date)
            return query

        if entity == "attendance":
            if count_only:
                query = (
                    select(func.count(AttendanceRecord.id))
                    .select_from(AttendanceRecord)
                    .join(
                        AttendanceSession,
                        AttendanceSession.id == AttendanceRecord.attendance_session_id,
                    )
                    .where(AttendanceRecord.school_id == school_id)
                )
            else:
                query = (
                    select(
                        AttendanceRecord.student_id.label("student_id"),
                        AttendanceSession.class_id.label("class_id"),
                        AttendanceSession.session_date.label("session_date"),
                        AttendanceSession.slot.label("slot"),
                        AttendanceRecord.status.label("status"),
                        AbsenceJustification.status.label("justification_status"),
                        AttendanceRecord.absence_reason.label("absence_reason"),
                    )
                    .join(
                        AttendanceSession,
                        AttendanceSession.id == AttendanceRecord.attendance_session_id,
                    )
                    .outerjoin(
                        AbsenceJustification,
                        AbsenceJustification.attendance_record_id == AttendanceRecord.id,
                    )
                    .where(AttendanceRecord.school_id == school_id)
                    .order_by(AttendanceSession.session_date.desc(), AttendanceRecord.id.desc())
                )
            if class_id:
                query = query.where(
                    AttendanceSession.class_id == uuid.UUID(str(class_id))
                )
            if student_id:
                query = query.where(
                    AttendanceRecord.student_id == uuid.UUID(str(student_id))
                )
            if status:
                query = query.where(AttendanceRecord.status == status)
            if from_date:
                query = query.where(AttendanceSession.session_date >= from_date)
            if to_date:
                query = query.where(AttendanceSession.session_date <= to_date)
            return query

        if entity == "invoices":
            if count_only:
                query = select(func.count(Invoice.id)).where(Invoice.school_id == school_id)
            else:
                query = (
                    select(
                        Invoice.id.label("invoice_id"),
                        Invoice.parent_id.label("parent_id"),
                        User.full_name.label("parent_name"),
                        Invoice.status.label("status"),
                        Invoice.total_amount.label("total_amount"),
                        Invoice.currency.label("currency"),
                        Invoice.issued_date.label("issued_date"),
                        Invoice.due_date.label("due_date"),
                    )
                    .join(User, User.id == Invoice.parent_id)
                    .where(Invoice.school_id == school_id)
                    .order_by(Invoice.issued_date.desc(), Invoice.id.desc())
                )
            if parent_id:
                query = query.where(Invoice.parent_id == uuid.UUID(str(parent_id)))
            if status:
                query = query.where(Invoice.status == status)
            if from_date:
                query = query.where(Invoice.issued_date >= from_date)
            if to_date:
                query = query.where(Invoice.issued_date <= to_date)
            return query

        if entity == "payments":
            if count_only:
                query = (
                    select(func.count(PaymentAttempt.id))
                    .select_from(PaymentAttempt)
                    .join(Invoice, Invoice.id == PaymentAttempt.invoice_id)
                    .where(PaymentAttempt.school_id == school_id)
                )
            else:
                query = (
                    select(
                        PaymentAttempt.id.label("payment_attempt_id"),
                        PaymentAttempt.invoice_id.label("invoice_id"),
                        PaymentAttempt.parent_id.label("parent_id"),
                        User.full_name.label("parent_name"),
                        PaymentAttempt.status.label("status"),
                        PaymentAttempt.retry_count.label("retry_count"),
                        PaymentAttempt.finalized_at.label("finalized_at"),
                        Invoice.total_amount.label("invoice_amount"),
                        Invoice.currency.label("currency"),
                    )
                    .join(Invoice, Invoice.id == PaymentAttempt.invoice_id)
                    .join(User, User.id == PaymentAttempt.parent_id)
                    .where(PaymentAttempt.school_id == school_id)
                    .order_by(
                        PaymentAttempt.created_at.desc(),
                        PaymentAttempt.id.desc(),
                    )
                )
            if parent_id:
                query = query.where(
                    PaymentAttempt.parent_id == uuid.UUID(str(parent_id))
                )
            if status:
                query = query.where(PaymentAttempt.status == status)
            if from_date:
                query = query.where(func.date(PaymentAttempt.created_at) >= from_date)
            if to_date:
                query = query.where(func.date(PaymentAttempt.created_at) <= to_date)
            return query

        raise ValueError(f"Unsupported export entity: {entity}")


class AnalyticsRepository:
    """Low-level analytics queries for the dashboard APIs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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

    async def count_users(
        self,
        *,
        school_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(User.id)).where(User.school_id == school_id)
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
        value = result.scalar_one()
        return float(value or 0)

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
        engaged_result = await self.db.execute(
            select(func.count(func.distinct(AuditLog.actor_id))).where(
                AuditLog.school_id == school_id,
                AuditLog.created_at >= from_dt,
                AuditLog.created_at <= to_dt,
                AuditLog.outcome == "success",
            )
        )
        return registered, active, int(engaged_result.scalar_one() or 0)
