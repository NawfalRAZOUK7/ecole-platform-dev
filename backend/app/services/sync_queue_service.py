"""Service layer for local-first sync workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.unit_of_work import UnitOfWork
from app.domain.events.sync_queue import (
    SyncCheckpointCreated,
    SyncConflictDetected,
    SyncConflictResolved,
    SyncDeviceRegistered,
    SyncQueueItemEnqueued,
)
from app.models.sync_queue import (
    SyncCheckpoint,
    SyncConflict,
    SyncConflictResolution,
    SyncDevice,
    SyncQueue,
    SyncQueueStatus,
)
from app.repositories.sync_queue import SyncQueueRepository
from app.schemas.sync_queue import (
    HealthResponse,
    PullResponse,
    PushPayload,
    PushResponse,
    QueueItemCreateRequest,
    QueueItemResponse,
    RegisterDeviceRequest,
    ResolveConflictRequest,
    SyncCheckpointCreateRequest,
    SyncCheckpointResponse,
    SyncConflictResponse,
    SyncDeviceResponse,
    SyncStatusResponse,
)
from app.services.audit import AuditService
from app.services.event_dispatcher import EventDispatcher

HEALTHY_DEVICE_WINDOW = timedelta(hours=24)


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


class SyncService:
    """Business logic for device registration, queue intake, and conflict handling."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = SyncQueueRepository(db)
        self.audit = AuditService(db)
        self._dispatcher = EventDispatcher(db)

    def _device_to_response(self, device: SyncDevice) -> dict[str, Any]:
        return SyncDeviceResponse(
            id=str(device.id),
            school_id=str(device.school_id),
            device_name=device.device_name,
            device_type=device.device_type,
            last_seen_at=_iso(device.last_seen_at) or "",
            firmware_version=device.firmware_version,
            is_active=device.is_active,
            created_at=_iso(device.created_at) or "",
            updated_at=_iso(device.updated_at),
        ).model_dump()

    def _queue_item_to_response(self, queue_item: SyncQueue) -> QueueItemResponse:
        return QueueItemResponse(
            id=str(queue_item.id),
            school_id=str(queue_item.school_id),
            device_id=str(queue_item.device_id),
            entity_type=queue_item.entity_type,
            entity_id=str(queue_item.entity_id),
            operation=queue_item.operation,
            payload=dict(queue_item.payload or {}),
            status=queue_item.status,
            retry_count=queue_item.retry_count,
            synced_at=_iso(queue_item.synced_at),
            created_at=_iso(queue_item.created_at) or "",
            updated_at=_iso(queue_item.updated_at),
        )

    def _conflict_to_response(self, conflict: SyncConflict) -> dict[str, Any]:
        return SyncConflictResponse(
            id=str(conflict.id),
            school_id=str(conflict.school_id),
            queue_item_id=str(conflict.queue_item_id),
            entity_type=conflict.entity_type,
            entity_id=str(conflict.entity_id),
            client_payload=dict(conflict.client_payload or {}),
            server_payload=dict(conflict.server_payload or {}),
            resolution=conflict.resolution,
            resolved_by=str(conflict.resolved_by)
            if conflict.resolved_by is not None
            else None,
            resolved_at=_iso(conflict.resolved_at),
            created_at=_iso(conflict.created_at) or "",
            updated_at=_iso(conflict.updated_at),
        ).model_dump()

    def _checkpoint_to_response(self, checkpoint: SyncCheckpoint) -> dict[str, Any]:
        return SyncCheckpointResponse(
            id=str(checkpoint.id),
            school_id=str(checkpoint.school_id),
            device_id=str(checkpoint.device_id),
            last_sync_at=_iso(checkpoint.last_sync_at) or "",
            last_entity_type=checkpoint.last_entity_type,
            last_entity_id=str(checkpoint.last_entity_id),
            records_synced=checkpoint.records_synced,
            created_at=_iso(checkpoint.created_at) or "",
            updated_at=_iso(checkpoint.updated_at),
        ).model_dump()

    async def _get_device_or_404(
        self,
        *,
        repo: SyncQueueRepository,
        device_id: uuid.UUID,
        auth: AuthContext,
    ) -> SyncDevice:
        device = await repo.get_device(device_id, school_id=auth.school_id)
        if device is None:
            raise NotFoundError("Sync device not found", error_code="ERR-SYNC-404")
        return device

    async def _get_checkpoint_or_404(
        self,
        *,
        repo: SyncQueueRepository,
        checkpoint_id: uuid.UUID,
        auth: AuthContext,
    ) -> SyncCheckpoint:
        checkpoint = await repo.get_checkpoint(checkpoint_id, school_id=auth.school_id)
        if checkpoint is None:
            raise NotFoundError("Sync checkpoint not found", error_code="ERR-SYNC-404")
        return checkpoint

    def _is_conflicting(
        self,
        *,
        existing_item: SyncQueue | None,
        incoming_item: QueueItemCreateRequest,
    ) -> bool:
        if existing_item is None:
            return False
        if existing_item.status not in {
            SyncQueueStatus.PENDING.value,
            SyncQueueStatus.CONFLICT.value,
        }:
            return False
        return existing_item.operation != incoming_item.operation or dict(
            existing_item.payload or {}
        ) != dict(incoming_item.payload or {})

    async def register_device(
        self,
        *,
        body: RegisterDeviceRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        async with UnitOfWork(self.db) as uow:
            repo = SyncQueueRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)

            device = SyncDevice(
                school_id=auth.school_id,
                device_name=body.device_name,
                device_type=body.device_type,
                firmware_version=body.firmware_version,
                last_seen_at=now,
                is_active=True,
            )
            device = await repo.create_device(device)
            response = self._device_to_response(device)

            await dispatcher.dispatch(
                SyncDeviceRegistered(
                    device_id=device.id,
                    school_id=device.school_id,
                    device_type=device.device_type,
                )
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="sync.device.register",
                target_type="sync_device",
                target_id=device.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()
        return response

    async def list_devices(
        self,
        *,
        auth: AuthContext,
        is_active: bool | None = None,
        device_type: str | None = None,
    ) -> list[dict[str, Any]]:
        devices = await self.repo.list_devices(
            school_id=auth.school_id,
            is_active=is_active,
            device_type=device_type,
        )
        return [self._device_to_response(device) for device in devices]

    async def push_changes(
        self,
        *,
        device_id: uuid.UUID,
        payload: PushPayload,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        async with UnitOfWork(self.db) as uow:
            repo = SyncQueueRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)

            device = await self._get_device_or_404(
                repo=repo, device_id=device_id, auth=auth
            )
            if not device.is_active:
                raise ValidationError(
                    "Sync device is inactive",
                    error_code="ERR-SYNC-422",
                )

            device.last_seen_at = now
            await repo.save_device(device)

            queue_items: list[QueueItemResponse] = []
            conflict_ids: list[str] = []

            for incoming in payload.items:
                created_at = incoming.created_at or now
                existing = await repo.get_latest_queue_item(
                    school_id=auth.school_id,
                    entity_type=incoming.entity_type.strip().lower(),
                    entity_id=incoming.entity_id,
                )
                status = (
                    SyncQueueStatus.CONFLICT.value
                    if self._is_conflicting(
                        existing_item=existing,
                        incoming_item=incoming,
                    )
                    else SyncQueueStatus.PENDING.value
                )
                queue_item = SyncQueue(
                    school_id=auth.school_id,
                    device_id=device.id,
                    entity_type=incoming.entity_type,
                    entity_id=incoming.entity_id,
                    operation=incoming.operation,
                    payload=dict(incoming.payload),
                    created_at=created_at,
                    status=status,
                    retry_count=0,
                )
                queue_item = await repo.create_queue_item(queue_item)
                queue_items.append(self._queue_item_to_response(queue_item))

                await dispatcher.dispatch(
                    SyncQueueItemEnqueued(
                        queue_item_id=queue_item.id,
                        device_id=device.id,
                        entity_type=queue_item.entity_type,
                        operation=queue_item.operation,
                    )
                )

                if status == SyncQueueStatus.CONFLICT.value and existing is not None:
                    conflict = SyncConflict(
                        school_id=auth.school_id,
                        queue_item_id=queue_item.id,
                        entity_type=queue_item.entity_type,
                        entity_id=queue_item.entity_id,
                        client_payload=dict(queue_item.payload or {}),
                        server_payload=dict(existing.payload or {}),
                        resolution=SyncConflictResolution.PENDING.value,
                    )
                    conflict = await repo.create_conflict(conflict)
                    conflict_ids.append(str(conflict.id))
                    await dispatcher.dispatch(
                        SyncConflictDetected(
                            conflict_id=conflict.id,
                            queue_item_id=queue_item.id,
                            entity_type=queue_item.entity_type,
                        )
                    )

            response = PushResponse(
                device_id=str(device.id),
                accepted_count=len(queue_items),
                conflict_count=len(conflict_ids),
                queued_items=queue_items,
                conflict_ids=conflict_ids,
            ).model_dump()

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="sync.push",
                target_type="sync_device",
                target_id=device.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        return response

    async def pull_changes(
        self,
        *,
        device_id: uuid.UUID,
        auth: AuthContext,
        since_checkpoint: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        device = await self._get_device_or_404(
            repo=self.repo, device_id=device_id, auth=auth
        )

        checkpoint = None
        since_created_at = None
        if since_checkpoint is not None:
            try:
                checkpoint_id = uuid.UUID(since_checkpoint)
            except ValueError as exc:
                raise ValidationError(
                    "Invalid checkpoint identifier",
                    error_code="ERR-SYNC-422",
                ) from exc
            checkpoint = await self._get_checkpoint_or_404(
                repo=self.repo,
                checkpoint_id=checkpoint_id,
                auth=auth,
            )
            since_created_at = checkpoint.last_sync_at

        changes = await self.repo.list_queue_items(
            school_id=auth.school_id,
            exclude_device_id=device.id,
            status=SyncQueueStatus.SYNCED.value,
            since_created_at=since_created_at,
            limit=limit,
        )
        latest_checkpoint = await self.repo.get_latest_checkpoint(device.id)
        pending_conflicts = await self.repo.list_conflicts(
            school_id=auth.school_id,
            resolution=SyncConflictResolution.PENDING.value,
        )

        return PullResponse(
            device_id=str(device.id),
            since_checkpoint=since_checkpoint,
            changes=[self._queue_item_to_response(item) for item in changes],
            next_checkpoint_id=str(latest_checkpoint.id)
            if latest_checkpoint is not None
            else None,
            conflict_count=len(pending_conflicts),
        ).model_dump()

    async def get_sync_status(
        self,
        *,
        device_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        device = await self._get_device_or_404(
            repo=self.repo, device_id=device_id, auth=auth
        )
        queue_items = await self.repo.list_queue_items(
            school_id=auth.school_id,
            device_id=device.id,
            limit=1000,
        )
        counts = {
            SyncQueueStatus.PENDING.value: 0,
            SyncQueueStatus.SYNCED.value: 0,
            SyncQueueStatus.CONFLICT.value: 0,
            SyncQueueStatus.FAILED.value: 0,
        }
        for item in queue_items:
            counts[item.status] = counts.get(item.status, 0) + 1

        latest_checkpoint = await self.repo.get_latest_checkpoint(device.id)
        return SyncStatusResponse(
            device_id=str(device.id),
            pending_count=counts[SyncQueueStatus.PENDING.value],
            synced_count=counts[SyncQueueStatus.SYNCED.value],
            conflict_count=counts[SyncQueueStatus.CONFLICT.value],
            failed_count=counts[SyncQueueStatus.FAILED.value],
            last_checkpoint_id=(
                str(latest_checkpoint.id) if latest_checkpoint is not None else None
            ),
            last_sync_at=_iso(latest_checkpoint.last_sync_at)
            if latest_checkpoint is not None
            else None,
        ).model_dump()

    async def list_conflicts(
        self,
        *,
        auth: AuthContext,
        resolution: str | None = SyncConflictResolution.PENDING.value,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conflicts = await self.repo.list_conflicts(
            school_id=auth.school_id,
            resolution=resolution,
            limit=limit,
        )
        return [self._conflict_to_response(conflict) for conflict in conflicts]

    async def resolve_conflict(
        self,
        *,
        conflict_id: uuid.UUID,
        body: ResolveConflictRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        async with UnitOfWork(self.db) as uow:
            repo = SyncQueueRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)

            conflict = await repo.get_conflict(
                conflict_id,
                school_id=auth.school_id,
                include_queue_item=True,
            )
            if conflict is None:
                raise NotFoundError(
                    "Sync conflict not found", error_code="ERR-SYNC-404"
                )

            conflict.resolution = body.resolution
            conflict.resolved_by = auth.user_id
            conflict.resolved_at = now
            await repo.save_conflict(conflict)

            queue_item = conflict.queue_item
            if queue_item is None:
                raise NotFoundError(
                    "Sync queue item not found", error_code="ERR-SYNC-404"
                )
            queue_item.status = (
                SyncQueueStatus.FAILED.value
                if body.resolution == SyncConflictResolution.SERVER_WINS.value
                else SyncQueueStatus.SYNCED.value
            )
            queue_item.synced_at = now
            await repo.save_queue_item(queue_item)

            response = self._conflict_to_response(conflict)
            await dispatcher.dispatch(
                SyncConflictResolved(
                    conflict_id=conflict.id,
                    resolution=conflict.resolution,
                    resolved_by=auth.user_id,
                )
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="sync.conflict.resolve",
                target_type="sync_conflict",
                target_id=conflict.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        return response

    async def process_queue_item(
        self,
        *,
        queue_item_id: uuid.UUID,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        async with UnitOfWork(self.db) as uow:
            repo = SyncQueueRepository(uow.session)
            audit = AuditService(uow.session)

            queue_item = await repo.get_queue_item(
                queue_item_id,
                school_id=auth.school_id,
                include_conflicts=True,
            )
            if queue_item is None:
                raise NotFoundError(
                    "Sync queue item not found", error_code="ERR-SYNC-404"
                )

            has_pending_conflict = any(
                conflict.resolution == SyncConflictResolution.PENDING.value
                for conflict in queue_item.conflicts
            )
            queue_item.status = (
                SyncQueueStatus.CONFLICT.value
                if has_pending_conflict
                else SyncQueueStatus.SYNCED.value
            )
            queue_item.synced_at = now if not has_pending_conflict else None
            await repo.save_queue_item(queue_item)
            response = self._queue_item_to_response(queue_item).model_dump(mode="json")

            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="sync.queue.process",
                target_type="sync_queue_item",
                target_id=queue_item.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        return response

    async def list_checkpoints(
        self,
        *,
        auth: AuthContext,
        device_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        if device_id is not None:
            await self._get_device_or_404(
                repo=self.repo, device_id=device_id, auth=auth
            )
        checkpoints = await self.repo.list_checkpoints(
            school_id=auth.school_id,
            device_id=device_id,
            limit=limit,
        )
        return [self._checkpoint_to_response(checkpoint) for checkpoint in checkpoints]

    async def create_checkpoint(
        self,
        *,
        device_id: uuid.UUID,
        body: SyncCheckpointCreateRequest,
        auth: AuthContext,
        ip_address: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(UTC)
        async with UnitOfWork(self.db) as uow:
            repo = SyncQueueRepository(uow.session)
            audit = AuditService(uow.session)
            dispatcher = EventDispatcher(uow.session)

            device = await self._get_device_or_404(
                repo=repo, device_id=device_id, auth=auth
            )
            device.last_seen_at = now
            await repo.save_device(device)

            checkpoint = SyncCheckpoint(
                school_id=auth.school_id,
                device_id=device.id,
                last_sync_at=now,
                last_entity_type=body.last_entity_type,
                last_entity_id=body.last_entity_id,
                records_synced=body.records_synced,
            )
            checkpoint = await repo.create_checkpoint(checkpoint)
            response = self._checkpoint_to_response(checkpoint)

            await dispatcher.dispatch(
                SyncCheckpointCreated(
                    checkpoint_id=checkpoint.id,
                    device_id=device.id,
                    records_synced=checkpoint.records_synced,
                )
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="sync.checkpoint.create",
                target_type="sync_checkpoint",
                target_id=checkpoint.id,
                outcome="success",
                entity_after=response,
                ip_address=ip_address,
            )
            await uow.commit()

        return response

    async def get_device_health(
        self,
        *,
        device_id: uuid.UUID,
        auth: AuthContext,
    ) -> dict[str, Any]:
        device = await self._get_device_or_404(
            repo=self.repo, device_id=device_id, auth=auth
        )
        queue_items = await self.repo.list_queue_items(
            school_id=auth.school_id,
            device_id=device.id,
            limit=1000,
        )
        latest_checkpoint = await self.repo.get_latest_checkpoint(device.id)

        pending_count = sum(
            1 for item in queue_items if item.status == SyncQueueStatus.PENDING.value
        )
        conflict_count = sum(
            1 for item in queue_items if item.status == SyncQueueStatus.CONFLICT.value
        )
        failed_count = sum(
            1 for item in queue_items if item.status == SyncQueueStatus.FAILED.value
        )

        age = datetime.now(UTC) - device.last_seen_at
        if not device.is_active or age > HEALTHY_DEVICE_WINDOW:
            health = "stale"
        elif conflict_count > 0 or failed_count > 0:
            health = "degraded"
        else:
            health = "healthy"

        return HealthResponse(
            device_id=str(device.id),
            health=health,
            is_active=device.is_active,
            pending_count=pending_count,
            conflict_count=conflict_count,
            failed_count=failed_count,
            last_seen_at=_iso(device.last_seen_at) or "",
            last_sync_at=_iso(latest_checkpoint.last_sync_at)
            if latest_checkpoint is not None
            else None,
        ).model_dump()


__all__ = ["SyncService"]
