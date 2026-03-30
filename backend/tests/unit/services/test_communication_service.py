"""Unit tests for communication service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.com import ConversationCreateRequest, MessageCreateRequest
from app.services import communication as communication_module
from app.services.communication import CommunicationService


def make_auth(role: str = "PAR") -> AuthContext:
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


def make_conversation(auth: AuthContext, *, participants: list | None = None):
    now = datetime(2026, 3, 30, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        type="DIRECT",
        created_by=auth.user_id,
        subject="Math feedback",
        participants=list(participants or []),
        created_at=now,
    )


def make_participant(user_id: uuid.UUID, *, muted: bool = False):
    return SimpleNamespace(
        user_id=user_id,
        role_in_conversation="PARTICIPANT",
        joined_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        muted=muted,
    )


def make_message(conversation_id: uuid.UUID, sender_id: uuid.UUID, *, body: str = "Bonjour"):
    now = datetime(2026, 3, 30, 10, 0, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        sender_id=sender_id,
        body=body,
        sent_at=now,
        edited_at=None,
        created_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = CommunicationService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._validate_messaging_abac = AsyncMock()
    service._validate_attachment_ownership = AsyncMock()

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    publish = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(communication_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        communication_module,
        "MessagingRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(communication_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(communication_module, "publish_message_created", publish)

    return service, repo_in_uow, audit, publish, uow


class TestCreateConversation:
    @pytest.mark.asyncio
    async def test_student_can_only_create_direct_conversations(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("STD")
        service, _repo_in_uow, _audit, _publish, _uow = setup_service(monkeypatch)

        with pytest.raises(ValidationError, match="Students can only create direct"):
            await service.create_conversation(
                body=ConversationCreateRequest(
                    participant_ids=[uuid.uuid4()],
                    type="GROUP",
                    initial_message="Bonjour",
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_direct_conversation_requires_one_other_participant(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, _repo_in_uow, _audit, _publish, _uow = setup_service(monkeypatch)

        with pytest.raises(ValidationError, match="require exactly 1 other participant"):
            await service.create_conversation(
                body=ConversationCreateRequest(
                    participant_ids=[uuid.uuid4(), uuid.uuid4()],
                    type="DIRECT",
                    initial_message="Bonjour",
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_conversation_rejects_missing_participant(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, _repo_in_uow, _audit, _publish, _uow = setup_service(monkeypatch)
        service.repo.get_membership.return_value = None

        with pytest.raises(NotFoundError, match="Participant not found"):
            await service.create_conversation(
                body=ConversationCreateRequest(
                    participant_ids=[uuid.uuid4()],
                    type="DIRECT",
                    initial_message="Bonjour",
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_conversation_creates_initial_message_and_notifies(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, repo_in_uow, audit, publish, uow = setup_service(monkeypatch)
        participant_id = uuid.uuid4()
        conversation = make_conversation(
            auth,
            participants=[
                make_participant(auth.user_id),
                make_participant(participant_id),
            ],
        )
        initial_message = make_message(conversation.id, auth.user_id, body="Bonjour")
        service.repo.get_membership.return_value = SimpleNamespace(user_id=participant_id)
        repo_in_uow.create_conversation.return_value = conversation
        repo_in_uow.get_conversation.return_value = conversation
        repo_in_uow.create_message.return_value = initial_message

        result = await service.create_conversation(
            body=ConversationCreateRequest(
                participant_ids=[participant_id],
                type="DIRECT",
                subject="Math feedback",
                initial_message="Bonjour",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(conversation.id)
        assert result["last_message_at"] is not None
        repo_in_uow.create_conversation.assert_awaited_once()
        repo_in_uow.create_conversation_participants.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        publish.assert_awaited_once()
        assert uow.committed is True


class TestMessagingFlows:
    @pytest.mark.asyncio
    async def test_send_message_notifies_only_unmuted_other_participants(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("TCH")
        service, repo_in_uow, audit, publish, uow = setup_service(monkeypatch)
        other_active = uuid.uuid4()
        other_muted = uuid.uuid4()
        conversation = make_conversation(
            auth,
            participants=[
                make_participant(auth.user_id),
                make_participant(other_active, muted=False),
                make_participant(other_muted, muted=True),
            ],
        )
        message = make_message(conversation.id, auth.user_id, body="Merci")
        service._verify_participant = AsyncMock(return_value=conversation)
        repo_in_uow.create_message.return_value = message

        result = await service.send_message(
            conversation_id=conversation.id,
            body=MessageCreateRequest(body="Merci"),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["id"] == str(message.id)
        service._validate_attachment_ownership.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        publish.assert_awaited_once()
        assert publish.await_args.kwargs["recipient_id"] == other_active
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_search_messages_requires_non_empty_query(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _audit, _publish, _uow = setup_service(monkeypatch)

        with pytest.raises(ValidationError, match="cannot be empty"):
            await service.search_messages(query_text="   ", limit=10, auth=auth)

    @pytest.mark.asyncio
    async def test_list_feed_checks_parent_child_access(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("PAR")
        service, _repo_in_uow, _audit, _publish, _uow = setup_service(monkeypatch)
        monkeypatch.setattr(
            communication_module,
            "validate_parent_child_access",
            AsyncMock(return_value=False),
        )

        with pytest.raises(NotFoundError, match="Student not found"):
            await service.list_feed(
                student_id=uuid.uuid4(),
                filters=[],
                sort=[],
                search=None,
                cursor=None,
                limit=10,
                auth=auth,
            )
