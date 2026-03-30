"""Read/write database routing helpers."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_engine_options = {
    "pool_size": 20,
    "max_overflow": 10,
    "pool_pre_ping": True,
    "connect_args": {"statement_cache_size": 0},
}

engine_primary = create_async_engine(settings.database_url, **_engine_options)
engine_replica = create_async_engine(
    settings.database_replica_url or settings.database_url,
    **_engine_options,
)

AsyncSessionPrimary = async_sessionmaker(
    engine_primary,
    class_=AsyncSession,
    expire_on_commit=False,
)
AsyncSessionReplica = async_sessionmaker(
    engine_replica,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-only session, falling back to primary when no replica exists."""
    async with AsyncSessionReplica() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_write_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a read-write session backed by the primary database."""
    async with AsyncSessionPrimary() as session:
        try:
            yield session
        finally:
            await session.close()
