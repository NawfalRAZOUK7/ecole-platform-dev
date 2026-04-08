"""Local-first sync models for offline device registration and queue replay."""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base, SchoolScopedMixin, TimestampMixin


def _short_id(value: object | None) -> str:
    return str(value)[:8] if value is not None else "None"


def _enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [item.value for item in enum_cls]


class SyncDeviceType(str, enum.Enum):
    """Device categories supported by the sync engine."""

    LOCAL_SERVER = "local_server"
    MOBILE = "mobile"
    BROWSER = "browser"


class SyncQueueOperation(str, enum.Enum):
    """CRUD operations represented in the sync queue."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncQueueStatus(str, enum.Enum):
    """Processing states for queued sync items."""

    PENDING = "pending"
    SYNCED = "synced"
    CONFLICT = "conflict"
    FAILED = "failed"


class SyncConflictResolution(str, enum.Enum):
    """Resolution outcomes available for sync conflicts."""

    PENDING = "pending"
    CLIENT_WINS = "client_wins"
    SERVER_WINS = "server_wins"
    MANUAL = "manual"


class SyncDevice(TimestampMixin, SchoolScopedMixin, Base):
    """Offline-capable device registered against a school."""

    __tablename__ = "sync_devices"

    device_name: Mapped[str] = mapped_column(String(200), nullable=False)
    device_type: Mapped[str] = mapped_column(
        PgEnum(
            SyncDeviceType,
            name="sync_device_type_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=SyncDeviceType.BROWSER.value,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    queue_items: Mapped[list["SyncQueue"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="SyncQueue.created_at",
    )
    checkpoints: Mapped[list["SyncCheckpoint"]] = relationship(
        back_populates="device",
        cascade="all, delete-orphan",
        order_by="SyncCheckpoint.last_sync_at",
    )

    __table_args__ = (
        Index("idx_sync_devices_school_active", "school_id", "is_active"),
        Index("idx_sync_devices_type_seen", "device_type", "last_seen_at"),
    )

    @validates("device_name")
    def validate_device_name(self, key: str, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Device name is required")
        return cleaned

    @validates("firmware_version")
    def validate_firmware_version(self, key: str, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    def __repr__(self) -> str:
        return (
            f"<SyncDevice id={_short_id(self.id)} name={self.device_name} "
            f"type={self.device_type}>"
        )


class SyncQueue(TimestampMixin, SchoolScopedMixin, Base):
    """Pending or processed sync payload uploaded by a device."""

    __tablename__ = "sync_queue"

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sync_devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    operation: Mapped[str] = mapped_column(
        PgEnum(
            SyncQueueOperation,
            name="sync_queue_operation_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=SyncQueueOperation.CREATE.value,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        PgEnum(
            SyncQueueStatus,
            name="sync_queue_status_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=SyncQueueStatus.PENDING.value,
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    device: Mapped["SyncDevice"] = relationship(back_populates="queue_items")
    conflicts: Mapped[list["SyncConflict"]] = relationship(
        back_populates="queue_item",
        cascade="all, delete-orphan",
        order_by="SyncConflict.created_at",
    )

    __table_args__ = (
        CheckConstraint(
            "retry_count >= 0 AND retry_count <= 5",
            name="ck_sync_queue_retry_count",
        ),
        Index("idx_sync_queue_device_id", "device_id"),
        Index("idx_sync_queue_device_status", "device_id", "status"),
        Index("idx_sync_queue_school_entity", "school_id", "entity_type", "entity_id"),
        Index("idx_sync_queue_pending_created_at", "status", "created_at"),
    )

    @validates("entity_type")
    def validate_entity_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("Entity type is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<SyncQueue id={_short_id(self.id)} entity={self.entity_type} "
            f"status={self.status}>"
        )


class SyncConflict(TimestampMixin, SchoolScopedMixin, Base):
    """Conflict detected while applying a queued sync payload."""

    __tablename__ = "sync_conflicts"

    queue_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sync_queue.id", ondelete="CASCADE"),
        nullable=False,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    client_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    server_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    resolution: Mapped[str] = mapped_column(
        PgEnum(
            SyncConflictResolution,
            name="sync_conflict_resolution_enum",
            create_type=False,
            values_callable=_enum_values,
        ),
        nullable=False,
        default=SyncConflictResolution.PENDING.value,
    )
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    queue_item: Mapped["SyncQueue"] = relationship(back_populates="conflicts")
    resolver = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        Index("idx_sync_conflicts_queue_item_id", "queue_item_id"),
        Index("idx_sync_conflicts_resolved_by", "resolved_by"),
        Index("idx_sync_conflicts_school_resolution", "school_id", "resolution"),
        Index("idx_sync_conflicts_entity", "entity_type", "entity_id"),
    )

    @validates("entity_type")
    def validate_entity_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("Entity type is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<SyncConflict id={_short_id(self.id)} entity={self.entity_type} "
            f"resolution={self.resolution}>"
        )


class SyncCheckpoint(TimestampMixin, SchoolScopedMixin, Base):
    """Cursor-like checkpoint for incremental device pull operations."""

    __tablename__ = "sync_checkpoints"

    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sync_devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_sync_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )
    last_entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    last_entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    records_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    device: Mapped["SyncDevice"] = relationship(back_populates="checkpoints")

    __table_args__ = (
        CheckConstraint(
            "records_synced >= 0",
            name="ck_sync_checkpoints_records_synced",
        ),
        Index("idx_sync_checkpoints_device_id", "device_id"),
        Index("idx_sync_checkpoints_device_last_sync", "device_id", "last_sync_at"),
        Index("idx_sync_checkpoints_school_entity", "school_id", "last_entity_type"),
    )

    @validates("last_entity_type")
    def validate_last_entity_type(self, key: str, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned:
            raise ValueError("Last entity type is required")
        return cleaned

    def __repr__(self) -> str:
        return (
            f"<SyncCheckpoint id={_short_id(self.id)} device_id={_short_id(self.device_id)} "
            f"records_synced={self.records_synced}>"
        )
