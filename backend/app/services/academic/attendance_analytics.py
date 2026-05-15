"""Attendance analytics service for rates, trends, and threshold alerts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_metrics import active_students, attendance_rate
from app.core.config import settings
from app.core.dependencies import (
    AuthContext,
    verify_parent_child_ownership,
    verify_school_boundary,
    verify_teacher_assignment,
)
from app.core.exceptions import NotFoundError
from app.core.permissions import ADM, PAR, STD, SYS, TCH
from app.core.unit_of_work import UnitOfWork
from app.domain.events.erp import AttendanceThresholdExceeded
from app.repositories.academic_attendance_analytics import AttendanceAnalyticsRepository
from app.repositories.erp import ERPRepository
from app.schemas.academic.attendance_analytics import (
    AbsenceTrendPointResponse,
    AbsenceTrendResponse,
    AttendanceAlertResponse,
    AttendanceThresholdCheckRequest,
    AttendanceThresholdCheckResponse,
    ClassAbsenceRateResponse,
    StudentAbsenceRateResponse,
)
from app.services.platform.audit import AuditService
from app.services.communication.event_dispatcher import EventDispatcher


class AttendanceAnalyticsService:
    """Computes attendance statistics and threshold-driven alerts."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AttendanceAnalyticsRepository(db)
        self.erp_repo = ERPRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _mention_for_rate(self, rate: float) -> str:
        if rate >= settings.attendance_critical_threshold:
            return "critical"
        if rate >= settings.attendance_warning_threshold:
            return "warning"
        return "good"

    def _threshold_for_rate(self, rate: float) -> str | None:
        if rate >= settings.attendance_critical_threshold:
            return "critical"
        if rate >= settings.attendance_warning_threshold:
            return "warning"
        return None

    def _student_rate_to_response(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        absence_count: int,
        total_sessions: int,
        student_name: str | None = None,
    ) -> dict:
        rate = round((absence_count / total_sessions), 4) if total_sessions else 0.0
        return StudentAbsenceRateResponse(
            student_id=str(student_id),
            student_name=student_name,
            period_id=str(period_id),
            absence_count=absence_count,
            total_sessions=total_sessions,
            absence_rate=rate,
            mention=self._mention_for_rate(rate),
        ).model_dump()

    def _alert_to_response(
        self,
        alert,
        *,
        student_name: str | None = None,
    ) -> dict:
        return AttendanceAlertResponse(
            id=str(alert.id),
            student_id=str(alert.student_id),
            student_name=student_name,
            school_id=str(alert.school_id),
            period_id=str(alert.period_id),
            absence_count=alert.absence_count,
            total_sessions=alert.total_sessions,
            absence_rate=round(float(alert.absence_rate), 4),
            threshold_exceeded=alert.threshold_exceeded,
            notified_at=alert.notified_at.isoformat() if alert.notified_at else None,
            created_at=alert.created_at.isoformat(),
            updated_at=alert.updated_at.isoformat() if alert.updated_at else None,
        ).model_dump()

    async def _load_period(self, period_id: uuid.UUID):
        period = await self.erp_repo.get_period(period_id)
        if period is None:
            raise NotFoundError("Period not found", error_code="ERR-ERP-404")
        return period

    async def _load_class(self, class_id: uuid.UUID):
        class_room = await self.erp_repo.get_class(class_id)
        if class_room is None:
            raise NotFoundError("Class not found", error_code="ERR-ERP-404")
        return class_room

    async def _ensure_student_scope(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> tuple[object, object]:
        student = await self.erp_repo.get_user_by_id(student_id)
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-ERP-404")
        verify_school_boundary(student.school_id, auth)

        period = await self._load_period(period_id)
        verify_school_boundary(period.school_id, auth)

        if auth.role == STD and student_id != auth.user_id:
            raise NotFoundError(
                "Attendance analytics not found", error_code="ERR-ERP-404"
            )
        if auth.role == PAR:
            child_ids = await self.erp_repo.list_parent_child_ids(
                parent_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_parent_child_ownership(student_id, child_ids)
        if auth.role == TCH:
            enrollment = await self.erp_repo.get_active_enrollment_for_student_period(
                student_id=student_id,
                period_id=period_id,
                school_id=auth.school_id,
            )
            if enrollment is None:
                raise NotFoundError(
                    "Attendance analytics not found", error_code="ERR-ERP-404"
                )
            teacher_class_ids = await self.erp_repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(enrollment.class_id, teacher_class_ids)

        return student, period

    async def _ensure_class_scope(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> tuple[object, object]:
        class_room = await self._load_class(class_id)
        period = await self._load_period(period_id)
        verify_school_boundary(class_room.school_id, auth)
        verify_school_boundary(period.school_id, auth)

        if auth.role in {PAR, STD}:
            raise NotFoundError(
                "Attendance analytics not found", error_code="ERR-ERP-404"
            )
        if auth.role == TCH:
            teacher_class_ids = await self.erp_repo.list_teacher_class_ids(
                teacher_id=auth.user_id,
                school_id=auth.school_id,
            )
            verify_teacher_assignment(class_id, teacher_class_ids)

        return class_room, period

    async def compute_student_absence_rate(
        self,
        *,
        student_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        student, _period = await self._ensure_student_scope(
            student_id=student_id,
            period_id=period_id,
            auth=auth,
        )
        absence_count, total_sessions = await self.repo.compute_student_absence_count(
            student_id=student_id,
            period_id=period_id,
        )
        return self._student_rate_to_response(
            student_id=student_id,
            period_id=period_id,
            absence_count=absence_count,
            total_sessions=total_sessions,
            student_name=student.full_name,
        )

    async def compute_class_absence_rates(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict:
        await self._ensure_class_scope(
            class_id=class_id, period_id=period_id, auth=auth
        )
        students = await self.repo.list_class_students(
            class_id=class_id, period_id=period_id
        )
        counts = {
            student_id: (absence_count, total_sessions)
            for student_id, absence_count, total_sessions in (
                await self.repo.compute_class_absence_rates(
                    class_id=class_id,
                    period_id=period_id,
                )
            )
        }

        rows = [
            self._student_rate_to_response(
                student_id=student_id,
                period_id=period_id,
                absence_count=counts.get(student_id, (0, 0))[0],
                total_sessions=counts.get(student_id, (0, 0))[1],
                student_name=student_name,
            )
            for student_id, student_name in students
        ]
        rows.sort(key=lambda item: (-item["absence_rate"], item["student_name"] or ""))
        average_absence_rate = (
            sum(row["absence_rate"] for row in rows) / len(rows) if rows else 0.0
        )
        active_students.labels(school_id=str(auth.school_id)).set(len(rows))
        attendance_rate.labels(school_id=str(auth.school_id)).set(
            max(0.0, min(1.0, 1.0 - average_absence_rate))
        )

        return ClassAbsenceRateResponse(
            class_id=str(class_id),
            period_id=str(period_id),
            students=[StudentAbsenceRateResponse(**row) for row in rows],
        ).model_dump()

    async def get_absence_trends(
        self,
        *,
        class_id: uuid.UUID,
        period_id: uuid.UUID,
        granularity: str,
        auth: AuthContext,
    ) -> dict:
        await self._ensure_class_scope(
            class_id=class_id, period_id=period_id, auth=auth
        )
        rows = await self.repo.get_absence_trends(
            class_id=class_id,
            period_id=period_id,
            granularity=granularity,
        )
        points = [
            AbsenceTrendPointResponse(
                bucket_start=bucket.isoformat(),
                absent_count=absent_count,
                total_sessions=total_sessions,
                absence_rate=round((absent_count / total_sessions), 4)
                if total_sessions
                else 0.0,
            )
            for bucket, absent_count, total_sessions in rows
        ]
        return AbsenceTrendResponse(
            class_id=str(class_id),
            period_id=str(period_id),
            granularity=granularity,
            points=points,
        ).model_dump()

    async def list_alerts(
        self,
        *,
        auth: AuthContext,
        period_id: uuid.UUID | None = None,
        threshold_exceeded: str | None = None,
        program_id: uuid.UUID | None = None,
    ) -> list[dict]:
        if auth.role != ADM:
            raise NotFoundError("Attendance alerts not found", error_code="ERR-ERP-404")
        if period_id is not None:
            period = await self._load_period(period_id)
            verify_school_boundary(period.school_id, auth)

        alerts = await self.repo.list_alerts(
            school_id=auth.school_id,
            period_id=period_id,
            threshold_exceeded=threshold_exceeded,
            program_id=program_id,
        )
        student_names = await self.repo.list_user_names(
            user_ids=list({alert.student_id for alert in alerts})
        )
        return [
            self._alert_to_response(
                alert,
                student_name=student_names.get(alert.student_id),
            )
            for alert in alerts
        ]

    async def check_thresholds_and_alert(
        self,
        *,
        body: AttendanceThresholdCheckRequest,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict:
        if auth.role not in {ADM, SYS}:
            raise NotFoundError(
                "Attendance threshold check not found",
                error_code="ERR-ERP-404",
            )
        period = await self._load_period(body.period_id)
        verify_school_boundary(period.school_id, auth)

        event_queue: list[AttendanceThresholdExceeded] = []
        now = datetime.now(timezone.utc)

        async with UnitOfWork(self.db) as uow:
            repo = AttendanceAnalyticsRepository(uow.session)
            audit = AuditService(uow.session)
            students = await repo.list_period_students(
                school_id=auth.school_id,
                period_id=body.period_id,
            )
            existing_alerts = await repo.list_alerts(
                school_id=auth.school_id,
                period_id=body.period_id,
            )
            existing_keys = {
                (alert.student_id, alert.threshold_exceeded)
                for alert in existing_alerts
            }

            created_alerts = []
            skipped = 0

            for student_id, student_name in students:
                (
                    absence_count,
                    total_sessions,
                ) = await repo.compute_student_absence_count(
                    student_id=student_id,
                    period_id=body.period_id,
                )
                if total_sessions <= 0:
                    skipped += 1
                    continue

                absence_rate = absence_count / total_sessions
                threshold = self._threshold_for_rate(absence_rate)
                if threshold is None:
                    skipped += 1
                    continue

                key = (student_id, threshold)
                if key in existing_keys:
                    skipped += 1
                    continue

                alert = await repo.create_attendance_alert(
                    student_id=student_id,
                    school_id=auth.school_id,
                    period_id=body.period_id,
                    absence_count=absence_count,
                    total_sessions=total_sessions,
                    absence_rate=round(absence_rate, 4),
                    threshold_exceeded=threshold,
                    notified_at=now,
                )
                created_alerts.append((alert, student_name))
                existing_keys.add(key)
                event_queue.append(
                    AttendanceThresholdExceeded(
                        school_id=auth.school_id,
                        actor_id=auth.user_id,
                        student_id=student_id,
                        period_id=body.period_id,
                        student_name=student_name,
                        absence_count=absence_count,
                        total_sessions=total_sessions,
                        absence_rate=round(absence_rate, 4),
                        threshold_exceeded=threshold,
                    )
                )

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="attendance.thresholds.check",
                target_type="period",
                target_id=body.period_id,
                outcome="success",
                entity_after={
                    "period_id": str(body.period_id),
                    "created": len(created_alerts),
                    "skipped": skipped,
                },
                ip_address=ip_address,
            )
            await uow.commit()

        for event in event_queue:
            try:
                await self._dispatcher.dispatch(event)
            except Exception:
                # Notification delivery must not fail the threshold check result.
                pass

        return AttendanceThresholdCheckResponse(
            created=len(event_queue),
            skipped=skipped,
            alerts=[
                AttendanceAlertResponse(
                    **self._alert_to_response(alert, student_name=student_name)
                )
                for alert, student_name in created_alerts
            ],
        ).model_dump()
