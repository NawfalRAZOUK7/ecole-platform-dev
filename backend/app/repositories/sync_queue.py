"""Repository helpers for local-first sync workflows."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.sync_queue import (
    SyncCheckpoint,
    SyncConflict,
    SyncDevice,
    SyncQueue,
)
from app.repositories.base import BaseRepository


class SyncQueueRepository(BaseRepository):
    """Data access for registered devices, queue items, conflicts, and checkpoints."""

    async def get_device(
        self,
        device_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_relations: bool = False,
    ) -> SyncDevice | None:
        query = select(SyncDevice).where(SyncDevice.id == device_id)
        if school_id is not None:
            query = query.where(SyncDevice.school_id == school_id)
        if include_relations:
            query = query.options(
                selectinload(SyncDevice.queue_items),
                selectinload(SyncDevice.checkpoints),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_devices(
        self,
        *,
        school_id: uuid.UUID,
        is_active: bool | None = None,
        device_type: str | None = None,
    ) -> list[SyncDevice]:
        query = select(SyncDevice).where(SyncDevice.school_id == school_id)
        if is_active is not None:
            query = query.where(SyncDevice.is_active.is_(is_active))
        if device_type is not None:
            query = query.where(SyncDevice.device_type == device_type)
        result = await self.db.execute(
            query.order_by(SyncDevice.last_seen_at.desc(), SyncDevice.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_device(self, device: SyncDevice) -> SyncDevice:
        self.db.add(device)
        await self.db.flush()
        return device

    async def save_device(self, device: SyncDevice) -> SyncDevice:
        self.db.add(device)
        await self.db.flush()
        return device

    async def get_queue_item(
        self,
        queue_item_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_conflicts: bool = False,
    ) -> SyncQueue | None:
        query = select(SyncQueue).where(SyncQueue.id == queue_item_id)
        if school_id is not None:
            query = query.where(SyncQueue.school_id == school_id)
        if include_conflicts:
            query = query.options(selectinload(SyncQueue.conflicts))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_queue_item(
        self,
        *,
        school_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
    ) -> SyncQueue | None:
        result = await self.db.execute(
            select(SyncQueue)
            .where(
                SyncQueue.school_id == school_id,
                SyncQueue.entity_type == entity_type,
                SyncQueue.entity_id == entity_id,
            )
            .order_by(SyncQueue.created_at.desc(), SyncQueue.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_queue_items(
        self,
        *,
        school_id: uuid.UUID,
        device_id: uuid.UUID | None = None,
        exclude_device_id: uuid.UUID | None = None,
        status: str | None = None,
        entity_type: str | None = None,
        since_created_at: datetime | None = None,
        limit: int = 100,
    ) -> list[SyncQueue]:
        query = select(SyncQueue).where(SyncQueue.school_id == school_id)
        if device_id is not None:
            query = query.where(SyncQueue.device_id == device_id)
        if exclude_device_id is not None:
            query = query.where(SyncQueue.device_id != exclude_device_id)
        if status is not None:
            query = query.where(SyncQueue.status == status)
        if entity_type is not None:
            query = query.where(SyncQueue.entity_type == entity_type)
        if since_created_at is not None:
            query = query.where(SyncQueue.created_at > since_created_at)
        result = await self.db.execute(
            query.order_by(SyncQueue.created_at.asc(), SyncQueue.id.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create_queue_item(self, queue_item: SyncQueue) -> SyncQueue:
        self.db.add(queue_item)
        await self.db.flush()
        return queue_item

    async def save_queue_item(self, queue_item: SyncQueue) -> SyncQueue:
        self.db.add(queue_item)
        await self.db.flush()
        return queue_item

    async def get_conflict(
        self,
        conflict_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
        include_queue_item: bool = False,
    ) -> SyncConflict | None:
        query = select(SyncConflict).where(SyncConflict.id == conflict_id)
        if school_id is not None:
            query = query.where(SyncConflict.school_id == school_id)
        if include_queue_item:
            query = query.options(selectinload(SyncConflict.queue_item))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_conflicts(
        self,
        *,
        school_id: uuid.UUID,
        resolution: str | None = None,
        limit: int = 100,
    ) -> list[SyncConflict]:
        query = select(SyncConflict).where(SyncConflict.school_id == school_id)
        if resolution is not None:
            query = query.where(SyncConflict.resolution == resolution)
        result = await self.db.execute(
            query.order_by(SyncConflict.created_at.desc(), SyncConflict.id.asc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create_conflict(self, conflict: SyncConflict) -> SyncConflict:
        self.db.add(conflict)
        await self.db.flush()
        return conflict

    async def save_conflict(self, conflict: SyncConflict) -> SyncConflict:
        self.db.add(conflict)
        await self.db.flush()
        return conflict

    async def get_checkpoint(
        self,
        checkpoint_id: uuid.UUID,
        *,
        school_id: uuid.UUID | None = None,
    ) -> SyncCheckpoint | None:
        query = select(SyncCheckpoint).where(SyncCheckpoint.id == checkpoint_id)
        if school_id is not None:
            query = query.where(SyncCheckpoint.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_checkpoint(
        self,
        device_id: uuid.UUID,
    ) -> SyncCheckpoint | None:
        result = await self.db.execute(
            select(SyncCheckpoint)
            .where(SyncCheckpoint.device_id == device_id)
            .order_by(SyncCheckpoint.last_sync_at.desc(), SyncCheckpoint.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_checkpoints(
        self,
        *,
        school_id: uuid.UUID,
        device_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[SyncCheckpoint]:
        query = select(SyncCheckpoint).where(SyncCheckpoint.school_id == school_id)
        if device_id is not None:
            query = query.where(SyncCheckpoint.device_id == device_id)
        result = await self.db.execute(
            query.order_by(SyncCheckpoint.last_sync_at.desc(), SyncCheckpoint.id.desc()).limit(
                limit
            )
        )
        return list(result.scalars().all())

    async def create_checkpoint(self, checkpoint: SyncCheckpoint) -> SyncCheckpoint:
        self.db.add(checkpoint)
        await self.db.flush()
        return checkpoint

    async def save_checkpoint(self, checkpoint: SyncCheckpoint) -> SyncCheckpoint:
        self.db.add(checkpoint)
        await self.db.flush()
        return checkpoint


__all__ = ["SyncQueueRepository"]
