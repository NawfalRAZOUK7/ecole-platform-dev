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
        self._info_key = "_uow_depth"

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self._session.rollback()

    async def __aenter__(self) -> UnitOfWork:
        depth = int(self._session.info.get(self._info_key, 0))
        self._session.info[self._info_key] = depth + 1
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None and not self._committed:
                await self.rollback()
        finally:
            depth = int(self._session.info.get(self._info_key, 0))
            if depth <= 1:
                self._session.info.pop(self._info_key, None)
            else:
                self._session.info[self._info_key] = depth - 1
