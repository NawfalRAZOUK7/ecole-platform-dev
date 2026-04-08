"""Phase 14 PDF report generation service."""

from __future__ import annotations

import hashlib
import io
import json
import re
import uuid
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
from app.core.storage import storage
from app.core.unit_of_work import UnitOfWork
from app.models.erp import Class
from app.models.iam import User
from app.models.reporting import ReportJob, ReportJobStatus, ReportType
from app.repositories.reports import ReportsRepository
from app.schemas.reports import ReportGenerateRequest
from app.services.dashboard_analytics import DashboardAnalyticsService
from app.services.notification_hub import NotificationHubService

try:  # pragma: no cover - optional runtime dependency
    from weasyprint import HTML
except Exception:  # pragma: no cover - handled at runtime
    HTML = None

try:  # pragma: no cover - optional fallback dependency
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - handled at runtime
    A4 = None
    canvas = None


TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

DOWNLOAD_ACTION = "reports.download"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_report_type(value: str | ReportType) -> str:
    if isinstance(value, ReportType):
        return value.value
    if isinstance(value, str):
        if value in ReportType._value2member_map_:
            return value
        if value.startswith("ReportType."):
            member_name = value.split(".", 1)[1]
            if member_name in ReportType.__members__:
                return ReportType[member_name].value
    return str(value)


def _datetime_bounds(from_date: date, to_date: date) -> tuple[datetime, datetime]:
    start_dt = datetime.combine(from_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(
        to_date + timedelta(days=1), time.min, tzinfo=timezone.utc
    )
    return start_dt, end_dt


def _format_decimal(value: Any, digits: int = 2) -> str:
    if value is None:
        return "—"
    try:
        rendered = f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)
    return rendered.rstrip("0").rstrip(".")


def _format_report_date(value: Any) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
                "%d/%m/%Y"
            )
        except ValueError:
            try:
                return date.fromisoformat(value).strftime("%d/%m/%Y")
            except ValueError:
                return value
    return str(value)


def _format_report_datetime(value: Any) -> str:
    if value in (None, ""):
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %H:%M")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return _format_report_date(value)
    return str(value)


def _format_grade(value: Any) -> str:
    if value is None:
        return "—"
    return f"{_format_decimal(value)}/20"


def _academic_year_label(value: dict[str, Any] | None) -> str | None:
    if not value:
        return None
    if value.get("label"):
        return str(value["label"])
    start = value.get("date_start") or value.get("academic_year_start")
    end = value.get("date_end") or value.get("academic_year_end")
    if start and end:
        return f"{_format_report_date(start)} - {_format_report_date(end)}"
    return None


_jinja_env.globals.update(
    fmt_date=_format_report_date,
    fmt_datetime=_format_report_datetime,
    fmt_grade=_format_grade,
    fmt_number=_format_decimal,
    academic_year_label=_academic_year_label,
)


class ReportsService:
    """Report job orchestration, rendering, and download security."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ReportsRepository(db)
        self.analytics = DashboardAnalyticsService(db)

    async def submit_report_job(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
        request: ReportGenerateRequest,
    ) -> tuple[dict[str, Any], bool]:
        parameters = await self._resolve_parameters(
            school_id=school_id,
            requester_id=requester_id,
            requester_role=requester_role,
            request=request,
        )
        report_type = _normalize_report_type(request.type)
        parameters_hash = hashlib.sha256(
            json.dumps(parameters, sort_keys=True).encode("utf-8")
        ).hexdigest()
        now = _utc_now()
        cached_job = await self.repo.find_cached_report(
            school_id=school_id,
            requester_id=requester_id,
            report_type=report_type,
            parameters_hash=parameters_hash,
            since=now - timedelta(hours=settings.report_cache_ttl_hours),
            now=now,
        )
        if (
            cached_job
            and cached_job.file_path
            and await storage.exists(cached_job.file_path)
        ):
            return self.serialize_job(cached_job, cache_hit=True), True

        async with UnitOfWork(self.db) as uow:
            repo = ReportsRepository(uow.session)
            job = ReportJob(
                school_id=school_id,
                requester_id=requester_id,
                type=report_type,
                parameters=parameters,
                parameters_hash=parameters_hash,
                status=ReportJobStatus.PENDING.value,
            )
            await repo.create_report_job(job)
            await uow.commit()
            return self.serialize_job(job), False

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
    ) -> tuple[list[dict[str, Any]], str | None, bool]:
        jobs, next_cursor, has_more = await self.repo.list_report_jobs(
            school_id=school_id,
            requester_id=requester_id,
            requester_role=requester_role,
            report_type=report_type,
            period_id=period_id,
            status=status,
            cursor=cursor,
            limit=limit,
        )
        return [self.serialize_job(job) for job in jobs], next_cursor, has_more

    async def get_report_options(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
        report_type: str | None = None,
        class_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        periods = await self.repo.list_periods(school_id=school_id)
        classes: list[Class] = []
        students: list[User] = []
        parents: list[User] = []

        if requester_role == TCH:
            classes = await self.repo.list_classes_for_teacher(
                teacher_id=requester_id,
                school_id=school_id,
            )
            if class_id:
                teacher_class_ids = {item.id for item in classes}
                if class_id not in teacher_class_ids:
                    raise NotFoundError("Class not found", error_code="ERR-REPORT-404")
                students = await self.repo.list_students_for_class(
                    class_id=class_id,
                    school_id=school_id,
                )
        elif requester_role in {ADM, DIR}:
            classes = await self.repo.list_classes(school_id=school_id)
            if report_type == ReportType.BILLING_STATEMENT.value:
                parents = await self.repo.list_users_by_role(
                    school_id=school_id,
                    role_code=PAR,
                )
            elif report_type == ReportType.STUDENT_REPORT_CARD.value:
                students = await self.repo.list_users_by_role(
                    school_id=school_id,
                    role_code=STD,
                )
            elif class_id:
                students = await self.repo.list_students_for_class(
                    class_id=class_id,
                    school_id=school_id,
                )
        elif requester_role == PAR:
            students = await self.repo.list_children(
                parent_id=requester_id,
                school_id=school_id,
            )
        elif requester_role == STD:
            student = await self.repo.get_user_in_school(
                user_id=requester_id,
                school_id=school_id,
            )
            students = [student] if student else []

        return {
            "classes": [
                {"id": str(item.id), "code": item.code, "name": item.name}
                for item in classes
            ],
            "periods": [
                {
                    "id": str(item.id),
                    "label": item.label or f"{item.date_start} - {item.date_end}",
                    "date_start": item.date_start.isoformat(),
                    "date_end": item.date_end.isoformat(),
                }
                for item in periods
            ],
            "students": [
                {
                    "id": str(item.id),
                    "full_name": item.full_name,
                    "email": item.email,
                }
                for item in students
            ],
            "parents": [
                {
                    "id": str(item.id),
                    "full_name": item.full_name,
                    "email": item.email,
                }
                for item in parents
            ],
        }

    async def get_job_for_reader(
        self,
        *,
        job_id: uuid.UUID,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
    ) -> ReportJob:
        job = await self.repo.get_report_job(job_id)
        if job is None or job.school_id != school_id:
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")
        if requester_role not in {ADM, DIR} and job.requester_id != requester_id:
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")
        return job

    async def get_job_for_token(self, *, token: str) -> ReportJob:
        job_id = self.parse_download_token(token)
        job = await self.repo.get_report_job(job_id)
        if job is None:
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")
        if job.expires_at and job.expires_at <= _utc_now():
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")
        return job

    def serialize_job(
        self, job: ReportJob, *, cache_hit: bool = False
    ) -> dict[str, Any]:
        report_type = _normalize_report_type(job.type)
        download_url = None
        if (
            job.status == ReportJobStatus.READY.value
            and job.file_path
            and (job.expires_at is None or job.expires_at > _utc_now())
        ):
            token = self.build_download_token(job.id, job.expires_at)
            download_url = f"/api/v1/reports/{job.id}/download?token={token}"
        return {
            "id": str(job.id),
            "type": report_type,
            "status": job.status,
            "parameters": job.parameters,
            "file_path": job.file_path,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "expires_at": job.expires_at.isoformat() if job.expires_at else None,
            "download_url": download_url,
            "cache_hit": cache_hit,
        }

    def build_download_token(
        self,
        job_id: uuid.UUID,
        expires_at: datetime | None,
    ) -> str:
        exp = expires_at or (
            _utc_now() + timedelta(hours=settings.report_download_ttl_hours)
        )
        payload = {
            "job_id": str(job_id),
            "action": DOWNLOAD_ACTION,
            "exp": exp,
        }
        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    def parse_download_token(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError as exc:
            raise NotFoundError(
                "Report job not found", error_code="ERR-REPORT-404"
            ) from exc
        if payload.get("action") != DOWNLOAD_ACTION:
            raise NotFoundError("Report job not found", error_code="ERR-REPORT-404")
        return uuid.UUID(payload["job_id"])

    async def generate_report_job(self, job_id: uuid.UUID) -> ReportJob | None:
        async with UnitOfWork(self.db) as uow:
            repo = ReportsRepository(uow.session)
            job = await repo.get_report_job(job_id)
            if job is None:
                return None
            job.status = ReportJobStatus.GENERATING.value
            job.error_message = None
            await repo.save_report_job(job)
            await uow.commit()

        try:
            context = await self._build_context(job)
            report_type = _normalize_report_type(job.type)
            html = self._render_template(report_type, context)
            pdf_bytes = self._render_pdf_bytes(html)
            relative_path, _checksum, file_size = await storage.save(
                io.BytesIO(pdf_bytes),
                f"{report_type}_{job.id}.pdf",
                subdirectory=settings.report_storage_subdirectory,
            )
            async with UnitOfWork(self.db) as uow:
                repo = ReportsRepository(uow.session)
                job = await repo.get_report_job(job_id)
                if job is None:
                    return None
                job.status = ReportJobStatus.READY.value
                job.file_path = relative_path
                job.file_size = file_size
                job.mime_type = "application/pdf"
                job.completed_at = _utc_now()
                job.expires_at = _utc_now() + timedelta(
                    hours=settings.report_download_ttl_hours
                )
                await repo.save_report_job(job)
                await uow.commit()
            await self._notify_report_ready(job)
        except Exception as exc:
            async with UnitOfWork(self.db) as uow:
                repo = ReportsRepository(uow.session)
                job = await repo.get_report_job(job_id)
                if job is None:
                    return None
                job.status = ReportJobStatus.FAILED.value
                job.error_message = str(exc)
                job.completed_at = _utc_now()
                await repo.save_report_job(job)
                await uow.commit()
            await self._notify_report_failed(job)

        return job

    async def cleanup_expired_reports(self) -> int:
        jobs = await self.repo.list_expired_report_jobs(now=_utc_now())
        cleaned = 0
        async with UnitOfWork(self.db) as uow:
            repo = ReportsRepository(uow.session)
            for job in jobs:
                if job.file_path:
                    await storage.delete(job.file_path)
                    job.file_path = None
                    await repo.save_report_job(job)
                    cleaned += 1
            await uow.commit()
            return cleaned

    async def _resolve_parameters(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
        request: ReportGenerateRequest,
    ) -> dict[str, Any]:
        period = None
        if request.period_id:
            period = await self.repo.get_period_in_school(
                period_id=request.period_id,
                school_id=school_id,
            )
            if period is None:
                raise NotFoundError("Period not found", error_code="ERR-REPORT-404")

        report_type = _normalize_report_type(request.type)
        parameters: dict[str, Any] = {
            "locale": request.locale,
            "compare": request.compare,
            "period_id": str(request.period_id) if request.period_id else None,
            "from_date": request.from_date.isoformat() if request.from_date else None,
            "to_date": request.to_date.isoformat() if request.to_date else None,
        }

        if report_type == ReportType.STUDENT_REPORT_CARD.value:
            if requester_role not in {STD, PAR, ADM, DIR}:
                raise AuthorizationError(
                    "This role cannot generate report cards",
                    error_code="ERR-REPORT-403",
                )
            target_student_id = await self._resolve_student_report_target(
                school_id=school_id,
                requester_id=requester_id,
                requester_role=requester_role,
                requested_student_id=request.student_id,
            )
            parameters["student_id"] = str(target_student_id)

        elif report_type in {
            ReportType.CLASS_SUMMARY.value,
            ReportType.ATTENDANCE_REPORT.value,
        }:
            if requester_role not in {TCH, ADM, DIR}:
                raise AuthorizationError(
                    "This role cannot generate class reports",
                    error_code="ERR-REPORT-403",
                )
            if request.class_id is None:
                raise ValidationError(
                    "class_id is required for this report",
                    error_code="ERR-REPORT-422",
                )
            class_obj = await self.repo.get_class_in_school(
                class_id=request.class_id,
                school_id=school_id,
            )
            if class_obj is None:
                raise NotFoundError("Class not found", error_code="ERR-REPORT-404")
            if requester_role == TCH:
                teacher_classes = await self.repo.list_teacher_class_ids(
                    teacher_id=requester_id,
                    school_id=school_id,
                )
                if request.class_id not in teacher_classes:
                    raise NotFoundError("Class not found", error_code="ERR-REPORT-404")
            parameters["class_id"] = str(request.class_id)

        elif report_type == ReportType.BILLING_STATEMENT.value:
            if requester_role not in {PAR, ADM, DIR}:
                raise AuthorizationError(
                    "This role cannot generate billing statements",
                    error_code="ERR-REPORT-403",
                )
            if requester_role == PAR:
                if request.parent_id and request.parent_id != requester_id:
                    raise NotFoundError("Parent not found", error_code="ERR-REPORT-404")
                target_parent_id = requester_id
            else:
                if request.parent_id is None:
                    raise ValidationError(
                        "parent_id is required for billing statements",
                        error_code="ERR-REPORT-422",
                    )
                parent = await self.repo.get_user_in_school(
                    user_id=request.parent_id,
                    school_id=school_id,
                )
                if parent is None:
                    raise NotFoundError("Parent not found", error_code="ERR-REPORT-404")
                target_parent_id = request.parent_id
            parameters["parent_id"] = str(target_parent_id)

        elif report_type == ReportType.SCHOOL_ANALYTICS.value:
            if requester_role not in {ADM, DIR}:
                raise AuthorizationError(
                    "This role cannot generate school analytics reports",
                    error_code="ERR-REPORT-403",
                )

        else:
            raise ValidationError(
                "Unsupported report type",
                error_code="ERR-REPORT-422",
            )

        if period:
            parameters["period_label"] = period.label
            parameters["from_date"] = period.date_start.isoformat()
            parameters["to_date"] = period.date_end.isoformat()

        return parameters

    async def _resolve_student_report_target(
        self,
        *,
        school_id: uuid.UUID,
        requester_id: uuid.UUID,
        requester_role: str,
        requested_student_id: uuid.UUID | None,
    ) -> uuid.UUID:
        if requester_role == STD:
            if requested_student_id and requested_student_id != requester_id:
                raise NotFoundError("Student not found", error_code="ERR-REPORT-404")
            return requester_id

        if requester_role == PAR:
            child_ids = await self.repo.list_parent_child_ids(
                parent_id=requester_id,
                school_id=school_id,
            )
            if requested_student_id:
                if requested_student_id not in child_ids:
                    raise NotFoundError(
                        "Student not found", error_code="ERR-REPORT-404"
                    )
                return requested_student_id
            if len(child_ids) == 1:
                return next(iter(child_ids))
            raise ValidationError(
                "student_id is required when multiple children are linked",
                error_code="ERR-REPORT-422",
            )

        if requested_student_id is None:
            raise ValidationError(
                "student_id is required for this report",
                error_code="ERR-REPORT-422",
            )
        student = await self.repo.get_user_in_school(
            user_id=requested_student_id,
            school_id=school_id,
        )
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-REPORT-404")
        return requested_student_id

    async def _build_context(self, job: ReportJob) -> dict[str, Any]:
        report_type = _normalize_report_type(job.type)
        if report_type == ReportType.STUDENT_REPORT_CARD.value:
            return await self._student_report_context(job)
        if report_type == ReportType.CLASS_SUMMARY.value:
            return await self._class_summary_context(job)
        if report_type == ReportType.ATTENDANCE_REPORT.value:
            return await self._attendance_report_context(job)
        if report_type == ReportType.BILLING_STATEMENT.value:
            return await self._billing_statement_context(job)
        if report_type == ReportType.SCHOOL_ANALYTICS.value:
            return await self._school_analytics_context(job)
        raise ValidationError("Unsupported report type", error_code="ERR-REPORT-422")

    async def _student_report_context(self, job: ReportJob) -> dict[str, Any]:
        student_id = uuid.UUID(job.parameters["student_id"])
        student = await self.repo.get_user_in_school(
            user_id=student_id,
            school_id=job.school_id,
        )
        if student is None:
            raise NotFoundError("Student not found", error_code="ERR-REPORT-404")

        from_date, to_date = self._resolve_window(job.parameters)
        from_dt, to_dt = _datetime_bounds(from_date, to_date)
        period_id = (
            uuid.UUID(job.parameters["period_id"])
            if job.parameters.get("period_id")
            else None
        )
        class_context = await self.repo.get_student_class_context(
            student_id=student_id,
            school_id=job.school_id,
            period_id=period_id,
        )
        class_average_map: dict[str, float] = {}
        if class_context is not None:
            class_subject_rows = await self.repo.list_class_subject_averages(
                school_id=job.school_id,
                class_id=class_context["class_id"],
                from_dt=from_dt,
                to_dt=to_dt,
            )
            class_average_map = {
                item["subject"]: round(item["average_grade"], 2)
                for item in class_subject_rows
            }

        grade_rows = await self.repo.list_student_report_grade_rows(
            school_id=job.school_id,
            student_id=student_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )

        subjects: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"assignments": [], "scores": [], "comments": []}
        )
        for row in grade_rows:
            subjects[row.subject]["assignments"].append(
                {
                    "title": row.assignment_title,
                    "score": float(row.score or 0),
                    "total_points": int(row.total_points or 0),
                    "published_at": row.published_at.isoformat()
                    if row.published_at
                    else None,
                }
            )
            subjects[row.subject]["scores"].append(float(row.score or 0))
            if row.feedback:
                subjects[row.subject]["comments"].append(row.feedback)

        subject_rows = []
        all_scores = []
        comments = []
        for subject, payload in subjects.items():
            scores = payload["scores"]
            all_scores.extend(scores)
            comments.extend(payload["comments"])
            subject_rows.append(
                {
                    "subject": subject,
                    "average": round(sum(scores) / len(scores), 2) if scores else 0.0,
                    "class_average": class_average_map.get(subject),
                    "assignments": payload["assignments"],
                    "comments": payload["comments"][:3],
                }
            )
        subject_rows.sort(key=lambda item: item["subject"])

        (
            total_records,
            present_records,
            absent_records,
            excused_records,
            late_records,
        ) = await self.repo.get_student_report_attendance_summary(
            school_id=job.school_id,
            student_id=student_id,
            from_date=from_date,
            to_date=to_date,
        )
        attendance_rate = (
            ((present_records + late_records) / total_records) * 100
            if total_records
            else 0.0
        )

        return {
            "lang": job.parameters.get("locale", "fr"),
            "is_rtl": job.parameters.get("locale") == "ar",
            "generated_at": _utc_now().isoformat(),
            "report_title": self._report_title(
                job.type, job.parameters.get("locale", "fr")
            ),
            "student": {
                "id": str(student.id),
                "full_name": student.full_name,
                "email": student.email,
                "class_code": class_context["class_code"] if class_context else None,
                "class_name": class_context["class_name"] if class_context else None,
                "academic_year": _academic_year_label(class_context),
            },
            "period": self._period_label(job.parameters, from_date, to_date),
            "subject_rows": subject_rows,
            "summary": {
                "average_grade": round(sum(all_scores) / len(all_scores), 2)
                if all_scores
                else 0.0,
                "attendance_rate": round(attendance_rate, 2),
                "assignment_count": sum(
                    len(item["assignments"]) for item in subject_rows
                ),
                "attendance": {
                    "total_records": total_records,
                    "present_records": present_records,
                    "absent_records": absent_records,
                    "excused_records": excused_records,
                    "late_records": late_records,
                },
                "teacher_comments": comments[:5],
            },
        }

    async def _class_summary_context(self, job: ReportJob) -> dict[str, Any]:
        class_id = uuid.UUID(job.parameters["class_id"])
        class_obj = await self.repo.get_class_in_school(
            class_id=class_id,
            school_id=job.school_id,
        )
        if class_obj is None:
            raise NotFoundError("Class not found", error_code="ERR-REPORT-404")

        from_date, to_date = self._resolve_window(job.parameters)
        from_dt, to_dt = _datetime_bounds(from_date, to_date)
        academic_year = await self.repo.get_class_academic_year(
            class_id=class_id,
            school_id=job.school_id,
        )
        student_ids = await self._class_student_ids(class_id, job)
        student_names = await self.repo.list_user_names_by_ids(student_ids)
        grade_map = await self.repo.list_class_student_grade_averages(
            school_id=job.school_id,
            class_id=class_id,
            student_ids=student_ids,
            from_dt=from_dt,
            to_dt=to_dt,
        )
        attendance_map = await self.repo.list_class_student_attendance_rates(
            school_id=job.school_id,
            class_id=class_id,
            student_ids=student_ids,
            from_date=from_date,
            to_date=to_date,
        )
        subject_breakdown = await self.repo.list_class_subject_averages(
            school_id=job.school_id,
            class_id=class_id,
            from_dt=from_dt,
            to_dt=to_dt,
        )

        rows = []
        for student_id in student_ids:
            rows.append(
                {
                    "student_id": str(student_id),
                    "student_name": student_names.get(student_id, "Unknown"),
                    "average_grade": round(grade_map.get(student_id, 0.0), 2),
                    "attendance_rate": attendance_map.get(student_id, 0.0),
                }
            )

        ranked = sorted(rows, key=lambda item: item["average_grade"], reverse=True)
        ranking_rows = [
            {
                "rank": index + 1,
                **item,
            }
            for index, item in enumerate(ranked)
        ]
        return {
            "lang": job.parameters.get("locale", "fr"),
            "is_rtl": job.parameters.get("locale") == "ar",
            "generated_at": _utc_now().isoformat(),
            "report_title": self._report_title(
                job.type, job.parameters.get("locale", "fr")
            ),
            "class": {
                "id": str(class_obj.id),
                "code": class_obj.code,
                "name": class_obj.name,
                "academic_year": _academic_year_label(academic_year),
            },
            "period": self._period_label(job.parameters, from_date, to_date),
            "students": sorted(rows, key=lambda item: item["student_name"]),
            "rankings": ranking_rows,
            "subject_breakdown": subject_breakdown,
            "summary": {
                "student_count": len(rows),
                "class_average": round(
                    sum(item["average_grade"] for item in rows) / len(rows),
                    2,
                )
                if rows
                else 0.0,
                "attendance_average": round(
                    sum(item["attendance_rate"] for item in rows) / len(rows),
                    2,
                )
                if rows
                else 0.0,
                "top_performers": ranked[:5],
                "bottom_performers": sorted(
                    rows,
                    key=lambda item: item["average_grade"],
                )[:5],
                "support_count": len(
                    [item for item in rows if item["average_grade"] < 10]
                ),
            },
        }

    async def _attendance_report_context(self, job: ReportJob) -> dict[str, Any]:
        class_id = uuid.UUID(job.parameters["class_id"])
        class_obj = await self.repo.get_class_in_school(
            class_id=class_id,
            school_id=job.school_id,
        )
        if class_obj is None:
            raise NotFoundError("Class not found", error_code="ERR-REPORT-404")

        from_date, to_date = self._resolve_window(job.parameters)
        student_ids = await self._class_student_ids(class_id, job)

        student_names = await self.repo.list_user_names_by_ids(student_ids)
        summary_rows = await self.repo.list_attendance_summary_rows(
            school_id=job.school_id,
            class_id=class_id,
            student_ids=student_ids,
            from_date=from_date,
            to_date=to_date,
        )

        student_rows = [
            {
                "student_id": str(row.student_id),
                "student_name": student_names.get(row.student_id, "Unknown"),
                "total_records": int(row.total_records or 0),
                "present": int(row.present or 0),
                "absences": int(row.absences or 0),
                "excused": int(row.excused or 0),
                "late": int(row.late or 0),
                "justified": int(row.justified or 0),
                "pending": int(row.pending or 0),
                "unjustified": max(int(row.absences or 0) - int(row.justified or 0), 0),
                "attendance_rate": round(
                    (
                        (int(row.present or 0) + int(row.late or 0))
                        / int(row.total_records or 1)
                    )
                    * 100,
                    2,
                )
                if row.total_records
                else 0.0,
            }
            for row in summary_rows
        ]

        trend_rows = await self.repo.list_attendance_trends(
            school_id=job.school_id,
            class_id=class_id,
            from_date=from_date,
            to_date=to_date,
        )

        return {
            "lang": job.parameters.get("locale", "fr"),
            "is_rtl": job.parameters.get("locale") == "ar",
            "generated_at": _utc_now().isoformat(),
            "report_title": self._report_title(
                job.type, job.parameters.get("locale", "fr")
            ),
            "class": {
                "id": str(class_obj.id),
                "code": class_obj.code,
                "name": class_obj.name,
            },
            "period": self._period_label(job.parameters, from_date, to_date),
            "students": student_rows,
            "trends": [
                {
                    "label": row.session_date.isoformat(),
                    "absent": int(row.absent or 0),
                    "excused": int(row.excused or 0),
                    "late": int(row.late or 0),
                }
                for row in trend_rows
            ],
            "summary": {
                "student_count": len(student_rows),
                "average_attendance_rate": round(
                    sum(item["attendance_rate"] for item in student_rows)
                    / len(student_rows),
                    2,
                )
                if student_rows
                else 0.0,
                "total_absences": sum(item["absences"] for item in student_rows),
                "total_late": sum(item["late"] for item in student_rows),
            },
        }

    async def _billing_statement_context(self, job: ReportJob) -> dict[str, Any]:
        parent_id = uuid.UUID(job.parameters["parent_id"])
        parent = await self.repo.get_user_in_school(
            user_id=parent_id,
            school_id=job.school_id,
        )
        if parent is None:
            raise NotFoundError("Parent not found", error_code="ERR-REPORT-404")

        from_date, to_date = self._resolve_window(job.parameters)
        invoices = await self.repo.list_invoices_for_parent(
            school_id=job.school_id,
            parent_id=parent_id,
            from_date=from_date,
            to_date=to_date,
        )
        children = await self.repo.list_children(
            parent_id=parent_id,
            school_id=job.school_id,
        )
        invoice_ids = [invoice.id for invoice in invoices]

        payments_map: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
        for payment in await self.repo.list_payment_attempts_for_invoice_ids(
            invoice_ids
        ):
            payments_map[payment.invoice_id].append(
                {
                    "id": str(payment.id),
                    "status": payment.status,
                    "retry_count": payment.retry_count,
                    "finalized_at": payment.finalized_at.isoformat()
                    if payment.finalized_at
                    else None,
                }
            )

        invoice_rows = []
        payment_history = []
        total_invoiced = 0.0
        total_outstanding = 0.0
        for invoice in invoices:
            amount = float(invoice.total_amount or 0)
            total_invoiced += amount
            if invoice.status != "paid":
                total_outstanding += amount
            invoice_rows.append(
                {
                    "id": str(invoice.id),
                    "status": invoice.status,
                    "issued_date": invoice.issued_date.isoformat(),
                    "due_date": invoice.due_date.isoformat(),
                    "amount": amount,
                    "balance_due": 0.0 if invoice.status == "paid" else amount,
                    "currency": invoice.currency,
                    "payments": payments_map.get(invoice.id, []),
                }
            )
            for payment in payments_map.get(invoice.id, []):
                payment_history.append(
                    {
                        "invoice_id": str(invoice.id),
                        "invoice_status": invoice.status,
                        "payment_status": payment["status"],
                        "retry_count": payment["retry_count"],
                        "finalized_at": payment["finalized_at"],
                    }
                )

        return {
            "lang": job.parameters.get("locale", "fr"),
            "is_rtl": job.parameters.get("locale") == "ar",
            "generated_at": _utc_now().isoformat(),
            "report_title": self._report_title(
                job.type, job.parameters.get("locale", "fr")
            ),
            "parent": {
                "id": str(parent.id),
                "full_name": parent.full_name,
                "email": parent.email,
            },
            "students": [
                {
                    "id": str(child.id),
                    "full_name": child.full_name,
                }
                for child in children
            ],
            "period": self._period_label(job.parameters, from_date, to_date),
            "invoices": invoice_rows,
            "payment_history": sorted(
                payment_history,
                key=lambda item: item["finalized_at"] or "",
                reverse=True,
            ),
            "summary": {
                "invoice_count": len(invoice_rows),
                "total_invoiced": round(total_invoiced, 2),
                "outstanding_balance": round(total_outstanding, 2),
                "payment_count": len(payment_history),
                "currency": "MAD",
            },
        }

    async def _school_analytics_context(self, job: ReportJob) -> dict[str, Any]:
        from_date, to_date = self._resolve_window(job.parameters)
        snapshot = await self.analytics.get_school_analytics_snapshot(
            school_id=job.school_id,
            from_date=from_date,
            to_date=to_date,
        )
        return {
            "lang": job.parameters.get("locale", "fr"),
            "is_rtl": job.parameters.get("locale") == "ar",
            "generated_at": _utc_now().isoformat(),
            "report_title": self._report_title(
                job.type, job.parameters.get("locale", "fr")
            ),
            "period": self._period_label(job.parameters, from_date, to_date),
            "snapshot": snapshot,
        }

    async def _class_student_ids(
        self, class_id: uuid.UUID, job: ReportJob
    ) -> list[uuid.UUID]:
        return await self.repo.list_class_student_ids(
            class_id=class_id,
            school_id=job.school_id,
            period_id=uuid.UUID(job.parameters["period_id"])
            if job.parameters.get("period_id")
            else None,
        )

    def _resolve_window(self, parameters: dict[str, Any]) -> tuple[date, date]:
        from_date = (
            date.fromisoformat(parameters["from_date"])
            if parameters.get("from_date")
            else (_utc_now() - timedelta(days=30)).date()
        )
        to_date = (
            date.fromisoformat(parameters["to_date"])
            if parameters.get("to_date")
            else _utc_now().date()
        )
        return from_date, to_date

    def _period_label(
        self, parameters: dict[str, Any], from_date: date, to_date: date
    ) -> str:
        if parameters.get("period_label"):
            return str(parameters["period_label"])
        return f"{_format_report_date(from_date)} → {_format_report_date(to_date)}"

    def _render_template(self, report_type: str, context: dict[str, Any]) -> str:
        template = _jinja_env.get_template(
            f"reports/{_normalize_report_type(report_type)}.html"
        )
        return template.render(**context)

    def _render_pdf_bytes(self, html: str) -> bytes:
        if HTML is not None:  # pragma: no branch
            return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()

        if canvas is None or A4 is None:  # pragma: no cover
            raise RuntimeError(
                "No PDF renderer available. Install weasyprint or reportlab."
            )

        plain_text = re.sub(r"<[^>]+>", "", html)
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 40
        for line in plain_text.splitlines():
            text = line.strip()
            if not text:
                continue
            pdf.drawString(40, y, text[:120])
            y -= 14
            if y < 40:
                pdf.showPage()
                y = height - 40
        pdf.save()
        return buffer.getvalue()

    async def _notify_report_ready(self, job: ReportJob) -> None:
        hub = NotificationHubService(self.db)
        await hub.create_single_notification(
            school_id=job.school_id,
            user_id=job.requester_id,
            title="Report ready",
            body="Your report is ready to download.",
            category="system",
            priority="normal",
            action_url="/reports",
            action_payload={"report_job_id": str(job.id)},
            event_ref="report.ready",
            preferred_channels=["in_app", "push"],
        )

    async def _notify_report_failed(self, job: ReportJob) -> None:
        hub = NotificationHubService(self.db)
        await hub.create_single_notification(
            school_id=job.school_id,
            user_id=job.requester_id,
            title="Report failed",
            body="The requested report could not be generated.",
            category="system",
            priority="high",
            action_url="/reports",
            action_payload={"report_job_id": str(job.id)},
            event_ref="report.failed",
            preferred_channels=["in_app", "push"],
        )

    def _report_title(self, report_type: str, locale: str) -> str:
        normalized_report_type = _normalize_report_type(report_type)
        titles = {
            "fr": {
                ReportType.STUDENT_REPORT_CARD.value: "Bulletin de l'élève",
                ReportType.CLASS_SUMMARY.value: "Résumé de classe",
                ReportType.ATTENDANCE_REPORT.value: "Rapport de présence",
                ReportType.BILLING_STATEMENT.value: "Relevé de facturation",
                ReportType.SCHOOL_ANALYTICS.value: "Analyse de l'école",
            },
            "ar": {
                ReportType.STUDENT_REPORT_CARD.value: "كشف نقاط التلميذ",
                ReportType.CLASS_SUMMARY.value: "ملخص القسم",
                ReportType.ATTENDANCE_REPORT.value: "تقرير الحضور",
                ReportType.BILLING_STATEMENT.value: "كشف الفوترة",
                ReportType.SCHOOL_ANALYTICS.value: "تحليلات المؤسسة",
            },
            "en": {
                ReportType.STUDENT_REPORT_CARD.value: "Student report card",
                ReportType.CLASS_SUMMARY.value: "Class summary report",
                ReportType.ATTENDANCE_REPORT.value: "Attendance report",
                ReportType.BILLING_STATEMENT.value: "Billing statement",
                ReportType.SCHOOL_ANALYTICS.value: "School analytics report",
            },
        }
        return titles.get(locale, titles["fr"]).get(normalized_report_type, "Report")
