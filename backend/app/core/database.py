"""Async SQLAlchemy engine and session configuration.

Reference: Pack D2 — Repository Architecture, Pack D4 — Database Strategy
"""

import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.app_env == "development",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"statement_cache_size": 0},
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class TimestampMixin:
    """Mixin providing id (UUID PK), created_at, and updated_at columns.

    All domain models inherit from both Base and TimestampMixin.
    Reference: Pack C4 — all tables use UUID PKs and audit timestamps.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=_utc_now,
        onupdate=_utc_now,
        nullable=True,
    )


class SchoolScopedMixin:
    """Mixin providing a required school_id FK for school-scoped models."""

    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class NullableSchoolScopedMixin:
    """Nullable school_id variant for platform-wide content entities."""

    school_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )


class SoftDeleteMixin:
    """Mixin for soft-deletable models."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = _utc_now()

    def restore(self) -> None:
        self.deleted_at = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
