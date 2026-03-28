"""Unit of Work — transaction boundary for services."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Manages a single database transaction.

    Usage:
        async with UnitOfWork(db) as uow:
            repo = UserRepository(uow.session)
            await repo.create(...)
            await uow.commit()
        # If exception occurs, rollback is automatic.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._committed = False

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aenter__(self) -> UnitOfWork:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None and not self._committed:
            await self.rollback()
