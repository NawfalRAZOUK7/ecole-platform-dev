"""Unit tests for local-first sync service workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.models.sync_queue import (
    SyncConflictResolution,
    SyncDeviceType,
    SyncQueueStatus,
)
import app.services.sync.sync_queue_service as sync_module
from app.services.sync.sync_queue_service import SyncService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


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


def make_device(
    auth: AuthContext,
    *,
    is_active: bool = True,
    last_seen_at: datetime | None = None,
):
    now = last_seen_at or datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        device_name="device-a",
        device_type=SyncDeviceType.BROWSER.value,
        last_seen_at=now,
        firmware_version="1.0.0",
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )


def make_queue_item(
    auth: AuthContext,
    device_id: uuid.UUID,
    *,
    status: str = SyncQueueStatus.PENDING.value,
    entity_type: str = "attendance",
    operation: str = "create",
    payload: dict | None = None,
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        device_id=device_id,
        entity_type=entity_type,
        entity_id=uuid.uuid4(),
        operation=operation,
        payload=payload or {"value": "client"},
        status=status,
        retry_count=0,
        synced_at=now if status == SyncQueueStatus.SYNCED.value else None,
        created_at=now,
        updated_at=now,
        conflicts=[],
    )


def make_conflict(
    auth: AuthContext,
    queue_item,
    *,
    resolution: str = SyncConflictResolution.PENDING.value,
):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        queue_item_id=queue_item.id,
        entity_type=queue_item.entity_type,
        entity_id=queue_item.entity_id,
        client_payload={"value": "client"},
        server_payload={"value": "server"},
        resolution=resolution,
        resolved_by=None,
        resolved_at=None,
        created_at=now,
        updated_at=now,
        queue_item=queue_item,
    )


def make_checkpoint(auth: AuthContext, device_id: uuid.UUID):
    now = datetime.now(UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        device_id=device_id,
        last_sync_at=now,
        last_entity_type="attendance",
        last_entity_id=uuid.uuid4(),
        records_synced=4,
        created_at=now,
        updated_at=now,
    )


def setup_service(monkeypatch: pytest.MonkeyPatch):
    service = SyncService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    dispatcher = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(sync_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        sync_module, "SyncQueueRepository", lambda _session: repo_in_uow
    )
    monkeypatch.setattr(sync_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(sync_module, "EventDispatcher", lambda _session: dispatcher)

    return service, repo_in_uow, audit, dispatcher, uow


class TestSyncService:
    @pytest.mark.asyncio
    async def test_register_device_returns_serialized_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        device = make_device(auth)
        repo_in_uow.create_device.return_value = device

        result = await service.register_device(
            body=sync_module.RegisterDeviceRequest(
                device_name="Classroom iPad",
                device_type="mobile",
                firmware_version="1.2.0",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["device_name"] == "device-a"
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_devices_serializes_results(self) -> None:
        auth = make_auth()
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.list_devices.return_value = [make_device(auth), make_device(auth)]

        result = await service.list_devices(auth=auth, is_active=True)

        assert len(result) == 2
        assert result[0]["school_id"] == str(auth.school_id)

    @pytest.mark.asyncio
    async def test_push_changes_rejects_inactive_device(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, repo_in_uow, *_ = setup_service(monkeypatch)
        repo_in_uow.get_device.return_value = make_device(auth, is_active=False)

        with pytest.raises(ValidationError, match="inactive"):
            await service.push_changes(
                device_id=uuid.uuid4(),
                payload=sync_module.PushPayload(
                    items=[
                        sync_module.QueueItemCreateRequest(
                            entity_type="attendance",
                            entity_id=uuid.uuid4(),
                            operation="create",
                            payload={"status": "present"},
                        )
                    ]
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_push_changes_enqueues_pending_item_without_conflict(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        device = make_device(auth)
        queue_item = make_queue_item(
            auth, device.id, status=SyncQueueStatus.PENDING.value
        )
        repo_in_uow.get_device.return_value = device
        repo_in_uow.get_latest_queue_item.return_value = None
        repo_in_uow.create_queue_item.return_value = queue_item

        result = await service.push_changes(
            device_id=device.id,
            payload=sync_module.PushPayload(
                items=[
                    sync_module.QueueItemCreateRequest(
                        entity_type="attendance",
                        entity_id=queue_item.entity_id,
                        operation="create",
                        payload={"status": "present"},
                    )
                ]
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["accepted_count"] == 1
        assert result["conflict_count"] == 0
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_push_changes_creates_conflict_when_existing_pending_differs(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, repo_in_uow, _, dispatcher, _ = setup_service(monkeypatch)
        device = make_device(auth)
        existing = make_queue_item(
            auth,
            device.id,
            status=SyncQueueStatus.PENDING.value,
            payload={"status": "absent"},
        )
        queued = make_queue_item(
            auth,
            device.id,
            status=SyncQueueStatus.CONFLICT.value,
            payload={"status": "present"},
        )
        conflict = make_conflict(auth, queued)
        repo_in_uow.get_device.return_value = device
        repo_in_uow.get_latest_queue_item.return_value = existing
        repo_in_uow.create_queue_item.return_value = queued
        repo_in_uow.create_conflict.return_value = conflict

        result = await service.push_changes(
            device_id=device.id,
            payload=sync_module.PushPayload(
                items=[
                    sync_module.QueueItemCreateRequest(
                        entity_type="attendance",
                        entity_id=existing.entity_id,
                        operation="create",
                        payload={"status": "present"},
                    )
                ]
            ),
            auth=auth,
        )

        assert result["conflict_count"] == 1
        assert result["conflict_ids"] == [str(conflict.id)]
        assert dispatcher.dispatch.await_count == 2

    @pytest.mark.asyncio
    async def test_pull_changes_rejects_invalid_checkpoint_id(self) -> None:
        auth = make_auth(role="PAR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_device.return_value = make_device(auth)

        with pytest.raises(ValidationError, match="Invalid checkpoint identifier"):
            await service.pull_changes(
                device_id=uuid.uuid4(),
                auth=auth,
                since_checkpoint="not-a-uuid",
            )

    @pytest.mark.asyncio
    async def test_pull_changes_returns_since_checkpoint_results(self) -> None:
        auth = make_auth(role="PAR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(auth)
        checkpoint = make_checkpoint(auth, device.id)
        change = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.SYNCED.value
        )
        service.repo.get_device.return_value = device
        service.repo.get_checkpoint.return_value = checkpoint
        service.repo.list_queue_items.return_value = [change]
        service.repo.get_latest_checkpoint.return_value = checkpoint
        service.repo.list_conflicts.return_value = []

        result = await service.pull_changes(
            device_id=device.id,
            auth=auth,
            since_checkpoint=str(checkpoint.id),
        )

        assert result["since_checkpoint"] == str(checkpoint.id)
        assert len(result["changes"]) == 1

    @pytest.mark.asyncio
    async def test_get_sync_status_counts_statuses(self) -> None:
        auth = make_auth(role="TCH")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(auth)
        service.repo.get_device.return_value = device
        service.repo.list_queue_items.return_value = [
            make_queue_item(auth, device.id, status=SyncQueueStatus.PENDING.value),
            make_queue_item(auth, device.id, status=SyncQueueStatus.SYNCED.value),
            make_queue_item(auth, device.id, status=SyncQueueStatus.CONFLICT.value),
            make_queue_item(auth, device.id, status=SyncQueueStatus.FAILED.value),
        ]
        checkpoint = make_checkpoint(auth, device.id)
        service.repo.get_latest_checkpoint.return_value = checkpoint

        result = await service.get_sync_status(device_id=device.id, auth=auth)

        assert result["pending_count"] == 1
        assert result["synced_count"] == 1
        assert result["conflict_count"] == 1
        assert result["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_list_conflicts_defaults_to_pending(self) -> None:
        auth = make_auth(role="DIR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        queue_item = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.CONFLICT.value
        )
        service.repo.list_conflicts.return_value = [make_conflict(auth, queue_item)]

        result = await service.list_conflicts(auth=auth)

        assert len(result) == 1
        service.repo.list_conflicts.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_resolve_conflict_marks_queue_synced_for_client_wins(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="DIR")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        queue_item = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.CONFLICT.value
        )
        conflict = make_conflict(auth, queue_item)
        repo_in_uow.get_conflict.return_value = conflict
        repo_in_uow.save_conflict.return_value = conflict
        repo_in_uow.save_queue_item.return_value = queue_item

        result = await service.resolve_conflict(
            conflict_id=conflict.id,
            body=sync_module.ResolveConflictRequest(resolution="client_wins"),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["resolution"] == "client_wins"
        assert queue_item.status == SyncQueueStatus.SYNCED.value
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_resolve_conflict_marks_queue_failed_for_server_wins(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="ADM")
        service, repo_in_uow, *_ = setup_service(monkeypatch)
        queue_item = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.CONFLICT.value
        )
        conflict = make_conflict(auth, queue_item)
        repo_in_uow.get_conflict.return_value = conflict

        await service.resolve_conflict(
            conflict_id=conflict.id,
            body=sync_module.ResolveConflictRequest(resolution="server_wins"),
            auth=auth,
        )

        assert queue_item.status == SyncQueueStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_resolve_conflict_missing_conflict_raises(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="ADM")
        service, repo_in_uow, *_ = setup_service(monkeypatch)
        repo_in_uow.get_conflict.return_value = None

        with pytest.raises(NotFoundError, match="Sync conflict not found"):
            await service.resolve_conflict(
                conflict_id=uuid.uuid4(),
                body=sync_module.ResolveConflictRequest(resolution="manual"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_process_queue_item_marks_synced_when_no_pending_conflicts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="ADM")
        service, repo_in_uow, audit, _, uow = setup_service(monkeypatch)
        queue_item = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.PENDING.value
        )
        queue_item.conflicts = [make_conflict(auth, queue_item, resolution="manual")]
        repo_in_uow.get_queue_item.return_value = queue_item

        result = await service.process_queue_item(
            queue_item_id=queue_item.id,
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["status"] == SyncQueueStatus.SYNCED.value
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_process_queue_item_keeps_conflict_when_pending_conflicts_exist(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="ADM")
        service, repo_in_uow, *_ = setup_service(monkeypatch)
        queue_item = make_queue_item(
            auth, uuid.uuid4(), status=SyncQueueStatus.PENDING.value
        )
        queue_item.conflicts = [make_conflict(auth, queue_item, resolution="pending")]
        repo_in_uow.get_queue_item.return_value = queue_item

        result = await service.process_queue_item(
            queue_item_id=queue_item.id,
            auth=auth,
        )

        assert result["status"] == SyncQueueStatus.CONFLICT.value

    @pytest.mark.asyncio
    async def test_create_checkpoint_updates_device_and_dispatches(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth(role="TCH")
        service, repo_in_uow, audit, dispatcher, uow = setup_service(monkeypatch)
        device = make_device(auth)
        checkpoint = make_checkpoint(auth, device.id)
        repo_in_uow.get_device.return_value = device
        repo_in_uow.create_checkpoint.return_value = checkpoint

        result = await service.create_checkpoint(
            device_id=device.id,
            body=sync_module.SyncCheckpointCreateRequest(
                last_entity_type="grade",
                last_entity_id=uuid.uuid4(),
                records_synced=4,
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["device_id"] == str(device.id)
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_checkpoints_validates_device_scope(self) -> None:
        auth = make_auth(role="ADM")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(auth)
        checkpoint = make_checkpoint(auth, device.id)
        service.repo.get_device.return_value = device
        service.repo.list_checkpoints.return_value = [checkpoint]

        result = await service.list_checkpoints(auth=auth, device_id=device.id)

        assert len(result) == 1
        service.repo.get_device.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_device_health_returns_stale_for_inactive_device(self) -> None:
        auth = make_auth(role="PAR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(
            auth,
            is_active=False,
            last_seen_at=datetime.now(UTC) - timedelta(hours=30),
        )
        service.repo.get_device.return_value = device
        service.repo.list_queue_items.return_value = []
        service.repo.get_latest_checkpoint.return_value = None

        result = await service.get_device_health(device_id=device.id, auth=auth)

        assert result["health"] == "stale"

    @pytest.mark.asyncio
    async def test_get_device_health_returns_degraded_for_conflicts(self) -> None:
        auth = make_auth(role="PAR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(auth, last_seen_at=datetime.now(UTC))
        service.repo.get_device.return_value = device
        service.repo.list_queue_items.return_value = [
            make_queue_item(auth, device.id, status=SyncQueueStatus.CONFLICT.value)
        ]
        service.repo.get_latest_checkpoint.return_value = make_checkpoint(
            auth, device.id
        )

        result = await service.get_device_health(device_id=device.id, auth=auth)

        assert result["health"] == "degraded"

    @pytest.mark.asyncio
    async def test_get_device_health_returns_healthy_for_clean_queue(self) -> None:
        auth = make_auth(role="PAR")
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        device = make_device(auth, last_seen_at=datetime.now(UTC))
        service.repo.get_device.return_value = device
        service.repo.list_queue_items.return_value = [
            make_queue_item(auth, device.id, status=SyncQueueStatus.SYNCED.value)
        ]
        service.repo.get_latest_checkpoint.return_value = make_checkpoint(
            auth, device.id
        )

        result = await service.get_device_health(device_id=device.id, auth=auth)

        assert result["health"] == "healthy"
