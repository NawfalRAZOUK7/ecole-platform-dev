"""Factories for local-first sync models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import factory

from app.models.sync_queue import (
    SyncCheckpoint,
    SyncConflict,
    SyncConflictResolution,
    SyncDevice,
    SyncDeviceType,
    SyncQueue,
    SyncQueueOperation,
    SyncQueueStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class SyncDeviceFactory(AsyncSQLAlchemyFactory):
    """Factory for sync devices."""

    class Meta:
        model = SyncDevice
        exclude = ("school",)

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    device_name = factory.Sequence(lambda n: f"device-{n:03d}")
    device_type = SyncDeviceType.BROWSER.value
    last_seen_at = factory.LazyFunction(_utc_now)
    firmware_version = "1.0.0"
    is_active = True


class SyncQueueFactory(AsyncSQLAlchemyFactory):
    """Factory for sync queue items."""

    class Meta:
        model = SyncQueue
        exclude = ("device",)

    id = factory.LazyFunction(uuid.uuid4)
    device = factory.SubFactory(SyncDeviceFactory)
    school_id = factory.LazyAttribute(lambda o: o.device.school_id)
    device_id = factory.LazyAttribute(lambda o: o.device.id)
    entity_type = "attendance"
    entity_id = factory.LazyFunction(uuid.uuid4)
    operation = SyncQueueOperation.CREATE.value
    payload = factory.LazyFunction(lambda: {"field": "value"})
    synced_at = None
    status = SyncQueueStatus.PENDING.value
    retry_count = 0
    created_at = factory.LazyFunction(_utc_now)


class SyncConflictFactory(AsyncSQLAlchemyFactory):
    """Factory for sync conflicts."""

    class Meta:
        model = SyncConflict
        exclude = ("queue_item", "resolver")

    id = factory.LazyFunction(uuid.uuid4)
    queue_item = factory.SubFactory(SyncQueueFactory)
    resolver = factory.SubFactory(
        UserFactory, school_id=factory.SelfAttribute("..queue_item.school_id")
    )
    school_id = factory.LazyAttribute(lambda o: o.queue_item.school_id)
    queue_item_id = factory.LazyAttribute(lambda o: o.queue_item.id)
    entity_type = factory.LazyAttribute(lambda o: o.queue_item.entity_type)
    entity_id = factory.LazyAttribute(lambda o: o.queue_item.entity_id)
    client_payload = factory.LazyFunction(lambda: {"value": "client"})
    server_payload = factory.LazyFunction(lambda: {"value": "server"})
    resolution = SyncConflictResolution.PENDING.value
    resolved_by = None
    resolved_at = None


class SyncCheckpointFactory(AsyncSQLAlchemyFactory):
    """Factory for sync checkpoints."""

    class Meta:
        model = SyncCheckpoint
        exclude = ("device",)

    id = factory.LazyFunction(uuid.uuid4)
    device = factory.SubFactory(SyncDeviceFactory)
    school_id = factory.LazyAttribute(lambda o: o.device.school_id)
    device_id = factory.LazyAttribute(lambda o: o.device.id)
    last_sync_at = factory.LazyFunction(_utc_now)
    last_entity_type = "attendance"
    last_entity_id = factory.LazyFunction(uuid.uuid4)
    records_synced = 3


__all__ = [
    "SyncDeviceFactory",
    "SyncQueueFactory",
    "SyncConflictFactory",
    "SyncCheckpointFactory",
]
