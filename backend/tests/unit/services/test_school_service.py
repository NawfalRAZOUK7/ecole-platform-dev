"""Unit tests for school service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError
from app.schemas.school import SchoolCreateRequest, SchoolUpdateRequest
import app.services.school.school as school_module
from app.services.school.school import SchoolService


def make_auth(role: str = "SUP", school_id: uuid.UUID | None = None) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
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


def make_school(school_id: uuid.UUID | None = None):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    school_id = school_id or uuid.uuid4()
    return SimpleNamespace(
        id=school_id,
        name="Ecole Atlas",
        name_ar="مدرسة الأطلس",
        code="atlas-001",
        massar_code="MASSAR001",
        status="active",
        address="123 Rue Atlas",
        city="Casablanca",
        region="Casablanca-Settat",
        phone="+212600000000",
        email="contact@atlas.ma",
        website="https://atlas.ma",
        logo_path="/logos/atlas.png",
        max_students=600,
        max_teachers=45,
        subscription_plan="premium",
        subscription_expires_at=now,
        timezone="Africa/Casablanca",
        default_language="fr",
        grading_scale="moroccan_20",
        settings={"timezone": "Africa/Casablanca"},
        is_active=True,
        is_subscription_valid=True,
        deleted_at=None,
        created_at=now,
        updated_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = SchoolService(AsyncMock())
    service.repo = AsyncMock()

    repo_in_uow = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(school_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(school_module, "SchoolRepository", lambda _session: repo_in_uow)

    return service, repo_in_uow, uow


class TestSchoolService:
    @pytest.mark.asyncio
    async def test_create_school_requires_sup(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _uow = setup_service(monkeypatch)

        with pytest.raises(NotFoundError, match="School not found"):
            await service.create_school(
                body=SchoolCreateRequest(name="Atlas", code="atlas"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_school_returns_serialized_school(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth("SUP")
        service, repo_in_uow, uow = setup_service(monkeypatch)
        school = make_school()
        repo_in_uow.create_school.return_value = school

        result = await service.create_school(
            body=SchoolCreateRequest(
                name="Ecole Atlas",
                code="atlas-001",
                city="Casablanca",
                email="contact@atlas.ma",
            ),
            auth=auth,
        )

        assert result["id"] == str(school.id)
        assert result["city"] == "Casablanca"
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_schools_for_sup_returns_paged_items(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth("SUP")
        service, _repo_in_uow, _uow = setup_service(monkeypatch)
        school = make_school()
        service.repo.list_schools.return_value = ([school], "next-cursor", True)

        items, next_cursor, has_more = await service.list_schools(
            auth=auth,
            cursor=None,
            limit=10,
            status=None,
        )

        assert items[0]["name"] == "Ecole Atlas"
        assert next_cursor == "next-cursor"
        assert has_more is True

    @pytest.mark.asyncio
    async def test_list_schools_for_admin_returns_current_school_only(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        school = make_school()
        auth = make_auth("ADM", school_id=school.id)
        service, _repo_in_uow, _uow = setup_service(monkeypatch)
        service.repo.get_school.return_value = school

        items, next_cursor, has_more = await service.list_schools(
            auth=auth,
            cursor=None,
            limit=10,
            status="active",
        )

        assert [item["id"] for item in items] == [str(school.id)]
        assert next_cursor is None
        assert has_more is False

    @pytest.mark.asyncio
    async def test_update_school_requires_manage_scope(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        school = make_school()
        auth = make_auth("DIR", school_id=school.id)
        service, _repo_in_uow, _uow = setup_service(monkeypatch)
        service.repo.get_school.return_value = school

        with pytest.raises(NotFoundError, match="School not found"):
            await service.update_school(
                school_id=school.id,
                body=SchoolUpdateRequest(city="Rabat"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_deactivate_school_requires_sup(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _uow = setup_service(monkeypatch)

        with pytest.raises(NotFoundError, match="School not found"):
            await service.deactivate_school(school_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_deactivate_school_soft_deletes_and_commits(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("SUP")
        service, repo_in_uow, uow = setup_service(monkeypatch)
        school = make_school()
        school.deleted_at = datetime(2026, 4, 1, tzinfo=timezone.utc)
        school.is_active = False
        repo_in_uow.soft_delete_school.return_value = school

        result = await service.deactivate_school(school_id=school.id, auth=auth)

        assert result["deleted_at"] == school.deleted_at.isoformat()
        assert result["is_active"] is False
        assert uow.committed is True
