"""Unit tests for reports and report scheduler services."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import ValidationError
from app.schemas.reports.report_schedule import ReportScheduleCreateRequest
from app.schemas.reports import ReportGenerateRequest
import app.services.reports.report_scheduler as scheduler_module
import app.services.reports.reports as reports_module
from app.services.reports.report_scheduler import ReportSchedulerService
from app.services.reports.reports import ReportsService


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_report_job(*, status: str = "ready", expires_in_hours: int = 24):
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        type="student_report_card",
        status=status,
        parameters={"student_id": str(uuid.uuid4())},
        file_path="reports/report.pdf",
        error_message=None,
        created_at=now,
        completed_at=now,
        expires_at=now + timedelta(hours=expires_in_hours),
    )


def make_schedule(auth: AuthContext):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        created_by=auth.user_id,
        report_type="student_report_card",
        frequency="weekly",
        parameters={"student_id": str(uuid.uuid4()), "locale": "fr"},
        recipient_roles=["PAR"],
        enabled=True,
        last_run_at=None,
        next_run_at=now + timedelta(days=7),
        created_at=now,
        updated_at=now,
    )


def setup_scheduler_service(monkeypatch: pytest.MonkeyPatch):
    service = ReportSchedulerService(AsyncMock())
    service.repo = AsyncMock()
    service.reports_repo = AsyncMock()
    service.audit = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(scheduler_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        scheduler_module,
        "ReportScheduleRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(scheduler_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, audit, uow


class TestReportsService:
    def test_serialize_job_includes_download_url_for_ready_job(self):
        service = ReportsService(AsyncMock())
        job = make_report_job(status="ready", expires_in_hours=24)

        payload = service.serialize_job(job)

        assert payload["id"] == str(job.id)
        assert payload["download_url"] is not None

    @pytest.mark.asyncio
    async def test_submit_report_job_returns_cached_payload_when_file_exists(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service = ReportsService(AsyncMock())
        job = make_report_job(status="ready", expires_in_hours=24)
        service.repo = AsyncMock()
        service.repo.find_cached_report.return_value = job
        service._resolve_parameters = AsyncMock(return_value={"student_id": "abc"})
        monkeypatch.setattr(
            reports_module.storage, "exists", AsyncMock(return_value=True)
        )

        payload, cache_hit = await service.submit_report_job(
            school_id=uuid.uuid4(),
            requester_id=uuid.uuid4(),
            requester_role="ADM",
            request=ReportGenerateRequest(type="student_report_card"),
        )

        assert cache_hit is True
        assert payload["cache_hit"] is True
        assert payload["id"] == str(job.id)


class TestReportSchedulerService:
    @pytest.mark.asyncio
    async def test_resolve_next_run_at_requires_period_for_end_of_period(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _repo_in_uow, _audit, _uow = setup_scheduler_service(monkeypatch)

        with pytest.raises(ValidationError, match="period_id is required"):
            await service._resolve_next_run_at(
                school_id=uuid.uuid4(),
                frequency="end_of_period",
                parameters={},
                requested_next_run_at=None,
                now=datetime(2026, 3, 30, tzinfo=timezone.utc),
            )

    @pytest.mark.asyncio
    async def test_create_schedule_persists_serialized_schedule(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_scheduler_service(monkeypatch)
        schedule = make_schedule(auth)
        next_run_at = datetime(2026, 4, 6, tzinfo=timezone.utc)
        service._validate_schedule_payload = AsyncMock(
            return_value=({"student_id": "abc", "locale": "fr"}, next_run_at)
        )
        repo_in_uow.create_schedule.return_value = schedule

        result = await service.create_schedule(
            body=ReportScheduleCreateRequest(
                report_type="student_report_card",
                frequency="weekly",
                parameters={"student_id": str(uuid.uuid4())},
                recipient_roles=["PAR"],
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(schedule.id)
        assert result["recipient_roles"] == ["PAR"]
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_disable_schedule_clears_next_run_at(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_scheduler_service(monkeypatch)
        schedule = make_schedule(auth)
        service._get_schedule_in_school = AsyncMock(return_value=schedule)
        repo_in_uow.get_schedule.return_value = schedule

        result = await service.disable_schedule(
            schedule_id=schedule.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["enabled"] is False
        assert result["next_run_at"] is None
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_run_schedule_returns_execute_result_and_audits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, audit, uow = setup_scheduler_service(monkeypatch)
        schedule = make_schedule(auth)
        run_result = {
            "schedule": {"id": str(schedule.id)},
            "job": {"id": str(uuid.uuid4()), "status": "ready"},
        }
        service._get_schedule_in_school = AsyncMock(return_value=schedule)
        service._execute_schedule = AsyncMock(return_value=run_result)

        result = await service.run_schedule(
            schedule_id=schedule.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result == run_result
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
