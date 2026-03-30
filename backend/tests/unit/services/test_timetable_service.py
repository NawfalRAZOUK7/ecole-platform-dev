"""Unit tests for timetable generator service."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.timetable_generation import (
    TimetableConstraintInput,
    TimetableConstraintSetRequest,
)
from app.services import timetable_generator as timetable_module
from app.services.timetable_generator import TimetableGeneratorService


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


def make_constraint(auth: AuthContext, academic_year_id: uuid.UUID):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=academic_year_id,
        constraint_type="room_capacity",
        entity_id=None,
        params={"room": "Lab A", "max_students": 30},
        created_at=now,
        updated_at=now,
    )


def make_job(
    auth: AuthContext,
    *,
    status: str = "completed",
    payload: dict | None = None,
):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=uuid.uuid4(),
        status=status,
        result_payload=payload or {},
        result_slot_count=1,
        conflicts_found=0,
        started_at=now,
        completed_at=now,
        error_message=None,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = TimetableGeneratorService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(timetable_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        timetable_module,
        "TimetableGenerationRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(timetable_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, audit, uow


class TestTimetableConstraints:
    @pytest.mark.asyncio
    async def test_set_constraints_requires_admin(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("TCH")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)

        with pytest.raises(NotFoundError, match="Timetable generation not found"):
            await service.set_constraints(
                body=TimetableConstraintSetRequest(
                    academic_year_id=uuid.uuid4(),
                    constraints=[],
                ),
                auth=auth,
                ip_address=None,
            )

    def test_validate_constraint_input_rejects_invalid_teacher_unavailable_window(self):
        service = TimetableGeneratorService(AsyncMock())

        with pytest.raises(ValidationError, match="end time must be after start time"):
            service._validate_constraint_input(
                TimetableConstraintInput(
                    constraint_type="teacher_unavailable",
                    entity_id=uuid.uuid4(),
                    params={"day": 1, "start": "11:00", "end": "10:00"},
                )
            )

    @pytest.mark.asyncio
    async def test_set_constraints_replaces_existing_constraints(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        academic_year_id = uuid.uuid4()
        created_constraint = make_constraint(auth, academic_year_id)
        service._load_academic_year = AsyncMock(return_value=SimpleNamespace(id=academic_year_id))
        repo_in_uow.create_constraint.return_value = created_constraint

        result = await service.set_constraints(
            body=TimetableConstraintSetRequest(
                academic_year_id=academic_year_id,
                constraints=[
                    TimetableConstraintInput(
                        constraint_type="room_capacity",
                        params={"room": "Lab A", "max_students": 30},
                    )
                ],
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result[0]["constraint_type"] == "room_capacity"
        repo_in_uow.delete_constraints.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestTimetablePreviewAndApply:
    @pytest.mark.asyncio
    async def test_preview_generated_returns_slots_and_conflicts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        job = make_job(
            auth,
            payload={
                "slots": [
                    {
                        "class_id": str(uuid.uuid4()),
                        "class_name": "6A",
                        "academic_year_id": str(uuid.uuid4()),
                        "day_of_week": 1,
                        "start_time": "08:00",
                        "end_time": "09:00",
                        "subject": "Math",
                        "teacher_id": str(uuid.uuid4()),
                    }
                ],
                "conflicts": [{"detail": "No room for science"}],
            },
        )
        service.repo.get_job.return_value = job

        result = await service.preview_generated(job_id=job.id, auth=auth)

        assert result["job"]["id"] == str(job.id)
        assert len(result["slots"]) == 1
        assert result["conflicts"][0]["detail"] == "No room for science"

    @pytest.mark.asyncio
    async def test_apply_generated_rejects_non_completed_job(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _uow = setup_service(monkeypatch)
        job = make_job(auth, status="running")
        service.repo.get_job.return_value = job

        with pytest.raises(ConflictError, match="not ready to apply"):
            await service.apply_generated(job_id=job.id, auth=auth, ip_address=None)

    @pytest.mark.asyncio
    async def test_apply_generated_persists_slots_and_marks_job_applied(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, audit, uow = setup_service(monkeypatch)
        slot = {
            "class_id": str(uuid.uuid4()),
            "academic_year_id": str(uuid.uuid4()),
            "day_of_week": 1,
            "start_time": "08:00",
            "end_time": "09:00",
            "subject": "Math",
            "teacher_id": str(uuid.uuid4()),
            "room": "Lab A",
            "is_recurring": True,
            "effective_from": date(2026, 9, 1).isoformat(),
            "effective_until": date(2026, 12, 31).isoformat(),
        }
        job = make_job(auth, payload={"slots": [slot], "conflicts": []})
        service.repo.get_job.return_value = job
        repo_in_uow.get_job.return_value = job

        result = await service.apply_generated(job_id=job.id, auth=auth, ip_address="127.0.0.1")

        assert result == {"job_id": str(job.id), "status": "applied", "created_count": 1}
        assert job.status == "applied"
        repo_in_uow.create_timetable_slot.assert_awaited_once()
        repo_in_uow.save_job.assert_awaited_once_with(job)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
