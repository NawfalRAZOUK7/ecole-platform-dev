"""Edge and validation tests for sync models, schemas, and services."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from pydantic import ValidationError as PydanticValidationError

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.schemas.sync_queue import (
    PushPayload,
    RegisterDeviceRequest,
    ResolveConflictRequest,
    SyncCheckpointCreateRequest,
)
from app.services.sync_queue_service import SyncService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestSyncModelValidation:
    def test_device_name_rejects_blank_value(self) -> None:
        from app.models.sync_queue import SyncDevice

        device = SyncDevice()

        with pytest.raises(ValueError, match="Device name is required"):
            device.validate_device_name("device_name", "   ")

    def test_queue_entity_type_rejects_blank_value(self) -> None:
        from app.models.sync_queue import SyncQueue

        queue_item = SyncQueue()

        with pytest.raises(ValueError, match="Entity type is required"):
            queue_item.validate_entity_type("entity_type", "   ")

    def test_checkpoint_last_entity_type_rejects_blank_value(self) -> None:
        from app.models.sync_queue import SyncCheckpoint

        checkpoint = SyncCheckpoint()

        with pytest.raises(ValueError, match="Last entity type is required"):
            checkpoint.validate_last_entity_type("last_entity_type", "   ")


class TestSyncSchemaValidation:
    def test_register_device_request_rejects_invalid_device_type(self) -> None:
        with pytest.raises(PydanticValidationError):
            RegisterDeviceRequest(device_name="Tablet", device_type="desktop")

    def test_push_payload_rejects_empty_items(self) -> None:
        with pytest.raises(PydanticValidationError):
            PushPayload(items=[])

    def test_resolve_conflict_request_rejects_invalid_resolution(self) -> None:
        with pytest.raises(PydanticValidationError):
            ResolveConflictRequest(resolution="discard")

    def test_checkpoint_request_rejects_negative_records_synced(self) -> None:
        with pytest.raises(PydanticValidationError):
            SyncCheckpointCreateRequest(
                last_entity_type="attendance",
                last_entity_id=uuid.uuid4(),
                records_synced=-1,
            )


class TestSyncServiceEdges:
    @pytest.mark.asyncio
    async def test_pull_changes_invalid_checkpoint_raises_validation_error(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="PAR",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_device.return_value = type(
            "DeviceStub",
            (),
            {"id": uuid.uuid4(), "school_id": auth.school_id},
        )()

        with pytest.raises(ValidationError, match="Invalid checkpoint identifier"):
            await service.pull_changes(
                device_id=uuid.uuid4(),
                auth=auth,
                since_checkpoint="bad-checkpoint",
            )

    @pytest.mark.asyncio
    async def test_get_sync_status_missing_device_raises_not_found(self) -> None:
        auth = AuthContext(
            user_id=uuid.uuid4(),
            role="TCH",
            school_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            permissions=set(),
        )
        service = SyncService(AsyncMock())
        service.repo = AsyncMock()
        service.repo.get_device.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_sync_status(device_id=uuid.uuid4(), auth=auth)

    def test_is_conflicting_ignores_synced_existing_item(self) -> None:
        service = SyncService(AsyncMock())
        existing_item = type(
            "QueueStub",
            (),
            {
                "status": "synced",
                "operation": "create",
                "payload": {"value": "server"},
            },
        )()

        assert (
            service._is_conflicting(
                existing_item=existing_item,
                incoming_item=type(
                    "IncomingStub",
                    (),
                    {"operation": "create", "payload": {"value": "client"}},
                )(),
            )
            is False
        )
