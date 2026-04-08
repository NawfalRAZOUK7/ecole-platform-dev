"""Scheduled report generation and delivery service."""

from __future__ import annotations

import calendar as calendar_module
import logging
import uuid
from datetime import datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.models.reporting import ReportSchedule
from app.repositories.report_schedule import ReportScheduleRepository
from app.repositories.reports import ReportsRepository
from app.schemas.report_schedule import (
    ReportScheduleCreateRequest,
    ReportScheduleResponse,
    ReportScheduleUpdateRequest,
)
from app.schemas.reports import ReportGenerateRequest
from app.services.audit import AuditService
from app.services.email import email_service
from app.services.reports import ReportsService

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReportSchedulerService:
    """Manages scheduled report generation and recipient delivery."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ReportScheduleRepository(db)
        self.reports_repo = ReportsRepository(db)
        self.audit = AuditService(db)

    def _serialize_schedule(self, schedule: ReportSchedule) -> dict[str, Any]:
        return ReportScheduleResponse(
            id=str(schedule.id),
            school_id=str(schedule.school_id),
            created_by=str(schedule.created_by),
            report_type=schedule.report_type,
            frequency=schedule.frequency,
            parameters=schedule.parameters or {},
            recipient_roles=list(schedule.recipient_roles or []),
            enabled=bool(schedule.enabled),
            last_run_at=schedule.last_run_at.isoformat()
            if schedule.last_run_at
            else None,
            next_run_at=schedule.next_run_at.isoformat()
            if schedule.next_run_at
            else None,
            created_at=schedule.created_at.isoformat(),
            updated_at=schedule.updated_at.isoformat() if schedule.updated_at else None,
        ).model_dump()

    async def _get_schedule_in_school(
        self,
        *,
        schedule_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> ReportSchedule:
        schedule = await self.repo.get_schedule(schedule_id)
        if schedule is None:
            raise NotFoundError(
                "Report schedule not found", error_code="ERR-REPORT-404"
            )
        if schedule.school_id != school_id:
            raise NotFoundError(
                "Report schedule not found", error_code="ERR-REPORT-404"
            )
        return schedule

    def _add_month(self, value: datetime) -> datetime:
        year = value.year + (1 if value.month == 12 else 0)
        month = 1 if value.month == 12 else value.month + 1
        day = min(value.day, calendar_module.monthrange(year, month)[1])
        return value.replace(year=year, month=month, day=day)

    async def _resolve_next_run_at(
        self,
        *,
        school_id: uuid.UUID,
        frequency: str,
        parameters: dict[str, Any],
        requested_next_run_at: datetime | None,
        now: datetime,
        reschedule_after_run: bool = False,
    ) -> datetime | None:
        if requested_next_run_at is not None:
            return (
                requested_next_run_at
                if requested_next_run_at.tzinfo is not None
                else requested_next_run_at.replace(tzinfo=timezone.utc)
            )
        if frequency == "daily":
            return now + timedelta(days=1)
        if frequency == "weekly":
            return now + timedelta(days=7)
        if frequency == "monthly":
            return self._add_month(now)
        if frequency == "end_of_period":
            period_id = parameters.get("period_id")
            if not period_id:
                raise ValidationError(
                    "period_id is required for end_of_period schedules",
                    error_code="ERR-REPORT-422",
                )
            period = await self.reports_repo.get_period_in_school(
                period_id=uuid.UUID(str(period_id)),
                school_id=school_id,
            )
            if period is None:
                raise NotFoundError("Period not found", error_code="ERR-REPORT-404")
            next_run_at = datetime.combine(
                period.date_end, time(hour=6), tzinfo=timezone.utc
            )
            if next_run_at <= now:
                if reschedule_after_run:
                    return None
                raise ValidationError(
                    "end_of_period schedules must target an upcoming period",
                    error_code="ERR-REPORT-422",
                )
            return next_run_at
        raise ValidationError(
            "Unsupported schedule frequency", error_code="ERR-REPORT-422"
        )

    async def _validate_schedule_payload(
        self,
        *,
        school_id: uuid.UUID,
        report_type: str,
        parameters: dict[str, Any],
        frequency: str,
        next_run_at: datetime | None,
    ) -> tuple[dict[str, Any], datetime | None]:
        validated_request = ReportGenerateRequest.model_validate(
            {"type": report_type, **(parameters or {})}
        )
        normalized_parameters = validated_request.model_dump(
            mode="json", exclude={"type"}
        )
        resolved_next_run_at = await self._resolve_next_run_at(
            school_id=school_id,
            frequency=frequency,
            parameters=normalized_parameters,
            requested_next_run_at=next_run_at,
            now=_utc_now(),
            reschedule_after_run=False,
        )
        return normalized_parameters, resolved_next_run_at

    def _report_email_title(self, locale: str) -> str:
        titles = {
            "fr": "Rapport programmé disponible",
            "ar": "التقرير المجدول جاهز",
            "en": "Scheduled report ready",
        }
        return titles.get(locale, titles["fr"])

    def _report_email_body(self, *, locale: str, report_label: str) -> str:
        bodies = {
            "fr": f'Le rapport planifié "{report_label}" est prêt à être consulté ou téléchargé.',
            "ar": f'التقرير المجدول "{report_label}" جاهز للعرض أو التنزيل.',
            "en": f'The scheduled "{report_label}" report is ready to view or download.',
        }
        return bodies.get(locale, bodies["fr"])

    def _absolute_action_url(self, path: str | None) -> str:
        base = settings.web_app_base_url.rstrip("/")
        if not path:
            return f"{base}/reports"
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{base}{path}"

    async def _deliver_schedule_email(
        self,
        *,
        schedule: ReportSchedule,
        job_payload: dict[str, Any],
    ) -> int:
        if not job_payload.get("download_url"):
            return 0
        recipients = await self.repo.list_recipient_users(
            school_id=schedule.school_id,
            roles=list(schedule.recipient_roles or []),
        )
        if not recipients:
            return 0

        locale = str((schedule.parameters or {}).get("locale") or "fr")
        report_label = ReportsService(self.db)._report_title(
            schedule.report_type, locale
        )
        action_url = self._absolute_action_url(job_payload.get("download_url"))
        sent_count = 0
        for user in recipients:
            if not user.email:
                continue
            success = await email_service.send_email(
                to=user.email,
                template_name="notification_alert",
                lang=locale,
                title=self._report_email_title(locale),
                body=self._report_email_body(locale=locale, report_label=report_label),
                action_url=action_url,
                unsubscribe_url=f"{settings.web_app_base_url.rstrip('/')}/notifications",
                open_tracking_url=None,
                category="reports",
            )
            if success:
                sent_count += 1
        return sent_count

    async def _execute_schedule(self, schedule: ReportSchedule) -> dict[str, Any]:
        creator_role = await self.repo.get_active_role(
            user_id=schedule.created_by,
            school_id=schedule.school_id,
        )
        if creator_role is None:
            raise ValidationError(
                "Schedule creator no longer has an active role",
                error_code="ERR-REPORT-422",
            )

        report_service = ReportsService(self.db)
        request = ReportGenerateRequest.model_validate(
            {"type": schedule.report_type, **(schedule.parameters or {})}
        )
        payload, cache_hit = await report_service.submit_report_job(
            school_id=schedule.school_id,
            requester_id=schedule.created_by,
            requester_role=creator_role,
            request=request,
        )
        job_id = uuid.UUID(payload["id"])
        if cache_hit:
            job = await report_service.repo.get_report_job(job_id)
        else:
            job = await report_service.generate_report_job(job_id)
        if job is None:
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")

        job_payload = report_service.serialize_job(job, cache_hit=cache_hit)
        now = _utc_now()
        async with UnitOfWork(self.db) as uow:
            repo = ReportScheduleRepository(uow.session)
            stored = await repo.get_schedule(schedule.id)
            if stored is not None:
                stored.last_run_at = now
                stored.next_run_at = (
                    await self._resolve_next_run_at(
                        school_id=stored.school_id,
                        frequency=stored.frequency,
                        parameters=stored.parameters or {},
                        requested_next_run_at=None,
                        now=now,
                        reschedule_after_run=True,
                    )
                    if stored.enabled
                    else None
                )
                await repo.save_schedule(stored)
                await uow.commit()
                schedule = stored

        await self._deliver_schedule_email(schedule=schedule, job_payload=job_payload)
        return {
            "schedule": self._serialize_schedule(schedule),
            "job": job_payload,
        }

    async def create_schedule(
        self,
        *,
        body: ReportScheduleCreateRequest,
        auth: AuthContext,
        ip_address: str,
    ) -> dict[str, Any]:
        parameters, next_run_at = await self._validate_schedule_payload(
            school_id=auth.school_id,
            report_type=body.report_type,
            parameters=body.parameters,
            frequency=body.frequency,
            next_run_at=body.next_run_at if body.enabled else None,
        )
        async with UnitOfWork(self.db) as uow:
            repo = ReportScheduleRepository(uow.session)
            audit = AuditService(uow.session)
            schedule = await repo.create_schedule(
                ReportSchedule(
                    school_id=auth.school_id,
                    created_by=auth.user_id,
                    report_type=body.report_type,
                    frequency=body.frequency,
                    parameters=parameters,
                    recipient_roles=body.recipient_roles,
                    enabled=body.enabled,
                    next_run_at=next_run_at if body.enabled else None,
                )
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="report.schedule.create",
                target_type="report_schedule",
                target_id=schedule.id,
                outcome="success",
                entity_after=self._serialize_schedule(schedule),
                ip_address=ip_address,
            )
            await uow.commit()
            return self._serialize_schedule(schedule)

    async def list_schedules(self, *, auth: AuthContext) -> list[dict[str, Any]]:
        items = await self.repo.list_schedules(school_id=auth.school_id)
        return [self._serialize_schedule(item) for item in items]

    async def update_schedule(
        self,
        *,
        schedule_id: uuid.UUID,
        body: ReportScheduleUpdateRequest,
        auth: AuthContext,
        ip_address: str,
    ) -> dict[str, Any]:
        schedule = await self._get_schedule_in_school(
            schedule_id=schedule_id,
            school_id=auth.school_id,
        )
        report_type = body.report_type or schedule.report_type
        frequency = body.frequency or schedule.frequency
        parameters_input = (
            body.parameters
            if body.parameters is not None
            else (schedule.parameters or {})
        )
        parameters, computed_next_run_at = await self._validate_schedule_payload(
            school_id=auth.school_id,
            report_type=report_type,
            parameters=parameters_input,
            frequency=frequency,
            next_run_at=body.next_run_at,
        )
        enabled = schedule.enabled if body.enabled is None else body.enabled
        recipient_roles = (
            list(schedule.recipient_roles or [])
            if body.recipient_roles is None
            else body.recipient_roles
        )
        next_run_at = computed_next_run_at if enabled else None

        async with UnitOfWork(self.db) as uow:
            repo = ReportScheduleRepository(uow.session)
            audit = AuditService(uow.session)
            stored = await repo.get_schedule(schedule_id)
            if stored is None:
                raise NotFoundError(
                    "Report schedule not found", error_code="ERR-REPORT-404"
                )
            before = self._serialize_schedule(stored)
            stored.report_type = report_type
            stored.frequency = frequency
            stored.parameters = parameters
            stored.recipient_roles = recipient_roles
            stored.enabled = enabled
            stored.next_run_at = next_run_at
            await repo.save_schedule(stored)
            after = self._serialize_schedule(stored)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="report.schedule.update",
                target_type="report_schedule",
                target_id=stored.id,
                outcome="success",
                entity_before=before,
                entity_after=after,
                ip_address=ip_address,
            )
            await uow.commit()
            return after

    async def disable_schedule(
        self,
        *,
        schedule_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str,
    ) -> dict[str, Any]:
        await self._get_schedule_in_school(
            schedule_id=schedule_id, school_id=auth.school_id
        )
        async with UnitOfWork(self.db) as uow:
            repo = ReportScheduleRepository(uow.session)
            audit = AuditService(uow.session)
            stored = await repo.get_schedule(schedule_id)
            if stored is None:
                raise NotFoundError(
                    "Report schedule not found", error_code="ERR-REPORT-404"
                )
            before = self._serialize_schedule(stored)
            stored.enabled = False
            stored.next_run_at = None
            await repo.save_schedule(stored)
            after = self._serialize_schedule(stored)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="report.schedule.disable",
                target_type="report_schedule",
                target_id=stored.id,
                outcome="success",
                entity_before=before,
                entity_after=after,
                ip_address=ip_address,
            )
            await uow.commit()
            return after

    async def run_schedule(
        self,
        *,
        schedule_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str,
    ) -> dict[str, Any]:
        schedule = await self._get_schedule_in_school(
            schedule_id=schedule_id,
            school_id=auth.school_id,
        )
        result = await self._execute_schedule(schedule)
        async with UnitOfWork(self.db) as uow:
            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="report.schedule.run",
                target_type="report_schedule",
                target_id=schedule.id,
                outcome="success",
                entity_after=result,
                ip_address=ip_address,
            )
            await uow.commit()
        return result

    async def process_due_schedules(self) -> int:
        due = await self.repo.list_due_schedules(now=_utc_now())
        processed = 0
        for schedule in due:
            try:
                await self._execute_schedule(schedule)
                processed += 1
            except Exception:
                logger.exception("Failed to process report schedule %s", schedule.id)
                continue
        return processed
