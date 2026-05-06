"""Unit tests for CMS service (announcements)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.com import AnnouncementCreateRequest, AnnouncementUpdateRequest
from app.services import cms as cms_module
from app.services.cms import CMSService


def make_auth(role: str = "ADM", school_id: uuid.UUID | None = None) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id or uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def make_announcement(
    school_id: uuid.UUID,
    *,
    status: str = "DRAFT",
    title: str = "Test Announcement",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        author_id=uuid.uuid4(),
        title=title,
        body="Announcement body.",
        target_roles=["PAR", "STD"],
        target_class_ids=None,
        published_at=None,
        status=status,
        created_at=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
        updated_at=None,
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        pass


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = CMSService(AsyncMock())
    service.repo = AsyncMock()

    uow = FakeUnitOfWork()
    inner_repo = AsyncMock()
    inner_audit = AsyncMock()
    monkeypatch.setattr(cms_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(cms_module, "CMSRepository", lambda _session: inner_repo)
    monkeypatch.setattr(cms_module, "AuditService", lambda _session: inner_audit)

    return service, inner_repo, inner_audit


class TestCMSServiceCreateAnnouncement:
    @pytest.mark.asyncio
    async def test_create_announcement_sets_draft_status(self, monkeypatch):
        service, inner_repo, inner_audit = setup_service(monkeypatch)
        auth = make_auth()
        announcement = make_announcement(auth.school_id, status="DRAFT")
        inner_repo.create_announcement.return_value = announcement
        inner_audit.log_event.return_value = None

        body = AnnouncementCreateRequest(
            title="Welcome Back",
            body="School resumes on Monday.",
            target_roles=["PAR", "STD"],
        )
        result = await service.create_announcement(
            body=body, auth=auth, ip_address="127.0.0.1"
        )

        assert result["status"] == "DRAFT"
        inner_repo.create_announcement.assert_called_once()
        call_kwargs = inner_repo.create_announcement.call_args.kwargs
        assert call_kwargs["status"] == "DRAFT"
        assert call_kwargs["school_id"] == auth.school_id

    @pytest.mark.asyncio
    async def test_create_announcement_rejects_invalid_target_role(self, monkeypatch):
        service, _inner_repo, _inner_audit = setup_service(monkeypatch)
        auth = make_auth()
        body = AnnouncementCreateRequest(
            title="Bad Role",
            body="Body.",
            target_roles=["INVALID_ROLE"],
        )
        with pytest.raises(ValidationError):
            await service.create_announcement(
                body=body, auth=auth, ip_address=None
            )


class TestCMSServiceUpdateAnnouncement:
    @pytest.mark.asyncio
    async def test_update_announcement_patches_title(self, monkeypatch):
        service, inner_repo, inner_audit = setup_service(monkeypatch)
        auth = make_auth()
        existing = make_announcement(auth.school_id, title="Old Title")

        # list_announcements returns the item from main repo
        service.repo.get_announcement.return_value = existing
        updated = make_announcement(auth.school_id, title="New Title")
        inner_repo.update_announcement.return_value = updated
        inner_audit.log_event.return_value = None

        body = AnnouncementUpdateRequest(title="New Title")
        result = await service.update_announcement(
            announcement_id=existing.id,
            body=body,
            auth=auth,
            ip_address=None,
        )

        assert result["title"] == "New Title"

    @pytest.mark.asyncio
    async def test_update_announcement_raises_if_not_found(self, monkeypatch):
        service, _inner_repo, _inner_audit = setup_service(monkeypatch)
        auth = make_auth()
        service.repo.get_announcement.return_value = None

        with pytest.raises(NotFoundError):
            await service.update_announcement(
                announcement_id=uuid.uuid4(),
                body=AnnouncementUpdateRequest(title="X"),
                auth=auth,
                ip_address=None,
            )
