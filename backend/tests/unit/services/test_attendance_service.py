"""Unit tests for attendance analytics service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError
from app.schemas.attendance_analytics import AttendanceThresholdCheckRequest
from app.services import attendance_analytics as attendance_module
from app.services.attendance_analytics import AttendanceAnalyticsService


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


def make_alert(
    school_id: uuid.UUID,
    period_id: uuid.UUID,
    student_id: uuid.UUID,
    *,
    threshold_exceeded: str = "critical",
):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        student_id=student_id,
        school_id=school_id,
        period_id=period_id,
        absence_count=4,
        total_sessions=10,
        absence_rate=0.4,
        threshold_exceeded=threshold_exceeded,
        notified_at=now,
        created_at=now,
        updated_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = AttendanceAnalyticsService(AsyncMock())
    service.repo = AsyncMock()
    service.erp_repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(attendance_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        attendance_module,
        "AttendanceAnalyticsRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(attendance_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, audit, uow


class TestAttendanceHelpers:
    def test_mention_for_rate_uses_warning_and_critical_thresholds(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service = AttendanceAnalyticsService(AsyncMock())
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_warning_threshold",
            0.1,
            raising=False,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_critical_threshold",
            0.25,
            raising=False,
        )

        assert service._mention_for_rate(0.05) == "good"
        assert service._mention_for_rate(0.1) == "warning"
        assert service._mention_for_rate(0.25) == "critical"

    def test_threshold_for_rate_returns_none_below_warning(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service = AttendanceAnalyticsService(AsyncMock())
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_warning_threshold",
            0.1,
            raising=False,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_critical_threshold",
            0.25,
            raising=False,
        )

        assert service._threshold_for_rate(0.09) is None
        assert service._threshold_for_rate(0.15) == "warning"
        assert service._threshold_for_rate(0.30) == "critical"


class TestAttendanceRatesAndTrends:
    @pytest.mark.asyncio
    async def test_compute_student_absence_rate_rounds_and_sets_mention(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        student_id = uuid.uuid4()
        period_id = uuid.uuid4()
        service._ensure_student_scope = AsyncMock(
            return_value=(
                SimpleNamespace(id=student_id, full_name="Amina"),
                SimpleNamespace(id=period_id),
            )
        )
        service.repo.compute_student_absence_count.return_value = (3, 7)
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_warning_threshold",
            0.1,
            raising=False,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_critical_threshold",
            0.4,
            raising=False,
        )

        result = await service.compute_student_absence_rate(
            student_id=student_id,
            period_id=period_id,
            auth=auth,
        )

        assert result["student_name"] == "Amina"
        assert result["absence_rate"] == 0.4286
        assert result["mention"] == "critical"

    @pytest.mark.asyncio
    async def test_compute_class_absence_rates_sorts_descending(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("TCH")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        class_id = uuid.uuid4()
        period_id = uuid.uuid4()
        student_high = uuid.uuid4()
        student_zero = uuid.uuid4()
        service._ensure_class_scope = AsyncMock(
            return_value=(SimpleNamespace(id=class_id), SimpleNamespace(id=period_id))
        )
        service.repo.list_class_students.return_value = [
            (student_zero, "Bilal"),
            (student_high, "Amina"),
        ]
        service.repo.compute_class_absence_rates.return_value = [
            (student_high, 2, 4),
        ]

        result = await service.compute_class_absence_rates(
            class_id=class_id,
            period_id=period_id,
            auth=auth,
        )

        assert [row["student_name"] for row in result["students"]] == ["Amina", "Bilal"]
        assert result["students"][0]["absence_rate"] == 0.5
        assert result["students"][1]["absence_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_absence_trends_handles_zero_totals(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        class_id = uuid.uuid4()
        period_id = uuid.uuid4()
        service._ensure_class_scope = AsyncMock(
            return_value=(SimpleNamespace(id=class_id), SimpleNamespace(id=period_id))
        )
        service.repo.get_absence_trends.return_value = [
            (datetime(2026, 3, 1, tzinfo=timezone.utc), 2, 10),
            (datetime(2026, 3, 8, tzinfo=timezone.utc), 0, 0),
        ]

        result = await service.get_absence_trends(
            class_id=class_id,
            period_id=period_id,
            granularity="weekly",
            auth=auth,
        )

        assert result["points"][0]["absence_rate"] == 0.2
        assert result["points"][1]["absence_rate"] == 0.0


class TestAttendanceAlerts:
    @pytest.mark.asyncio
    async def test_list_alerts_requires_admin(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)

        with pytest.raises(NotFoundError, match="Attendance alerts not found"):
            await service.list_alerts(auth=auth)

    @pytest.mark.asyncio
    async def test_list_alerts_enriches_student_names(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        period_id = uuid.uuid4()
        student_id = uuid.uuid4()
        alert = make_alert(auth.school_id, period_id, student_id)
        service.erp_repo.get_period.return_value = SimpleNamespace(
            id=period_id,
            school_id=auth.school_id,
        )
        service.repo.list_alerts.return_value = [alert]
        service.repo.list_user_names.return_value = {student_id: "Amina"}

        result = await service.list_alerts(auth=auth, period_id=period_id)

        assert result[0]["student_name"] == "Amina"
        assert result[0]["threshold_exceeded"] == "critical"

    @pytest.mark.asyncio
    async def test_check_thresholds_requires_admin_or_sys(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)

        with pytest.raises(NotFoundError, match="Attendance threshold check not found"):
            await service.check_thresholds_and_alert(
                body=AttendanceThresholdCheckRequest(period_id=uuid.uuid4()),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_check_thresholds_creates_only_new_threshold_breaches(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        period_id = uuid.uuid4()
        period = SimpleNamespace(id=period_id, school_id=auth.school_id)
        student_new = uuid.uuid4()
        student_existing = uuid.uuid4()
        student_below = uuid.uuid4()
        student_empty = uuid.uuid4()
        service.erp_repo.get_period.return_value = period
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_warning_threshold",
            0.1,
            raising=False,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_critical_threshold",
            0.25,
            raising=False,
        )
        repo_in_uow.list_period_students.return_value = [
            (student_new, "Amina"),
            (student_existing, "Bilal"),
            (student_below, "Celia"),
            (student_empty, "Dina"),
        ]
        repo_in_uow.list_alerts.return_value = [
            make_alert(
                auth.school_id,
                period_id,
                student_existing,
                threshold_exceeded="critical",
            )
        ]

        counts = {
            student_new: (4, 10),
            student_existing: (4, 10),
            student_below: (0, 10),
            student_empty: (0, 0),
        }

        async def compute_student_absence_count(*, student_id, period_id):
            return counts[student_id]

        repo_in_uow.compute_student_absence_count.side_effect = (
            compute_student_absence_count
        )
        created_alert = make_alert(auth.school_id, period_id, student_new)
        repo_in_uow.create_attendance_alert.return_value = created_alert

        result = await service.check_thresholds_and_alert(
            body=AttendanceThresholdCheckRequest(period_id=period_id),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["created"] == 1
        assert result["skipped"] == 3
        assert result["alerts"][0]["student_id"] == str(student_new)
        audit.log_event.assert_awaited_once()
        service._dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_check_thresholds_ignores_dispatch_failures(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("SYS")
        service, repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        period_id = uuid.uuid4()
        student_id = uuid.uuid4()
        service.erp_repo.get_period.return_value = SimpleNamespace(
            id=period_id,
            school_id=auth.school_id,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_warning_threshold",
            0.1,
            raising=False,
        )
        monkeypatch.setattr(
            attendance_module.settings,
            "attendance_critical_threshold",
            0.25,
            raising=False,
        )
        repo_in_uow.list_period_students.return_value = [(student_id, "Amina")]
        repo_in_uow.list_alerts.return_value = []
        repo_in_uow.compute_student_absence_count.return_value = (3, 10)
        repo_in_uow.create_attendance_alert.return_value = make_alert(
            auth.school_id,
            period_id,
            student_id,
            threshold_exceeded="critical",
        )
        service._dispatcher.dispatch.side_effect = RuntimeError("broker unavailable")

        result = await service.check_thresholds_and_alert(
            body=AttendanceThresholdCheckRequest(period_id=period_id),
            auth=auth,
            ip_address=None,
        )

        assert result["created"] == 1
        assert result["skipped"] == 0
