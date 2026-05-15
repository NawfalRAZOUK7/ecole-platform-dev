"""Reset the disposable PostgreSQL database used by Dockerized tests."""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


def _database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Set TEST_DATABASE_URL or DATABASE_URL before resetting tests")

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


async def _reset() -> None:
    engine = create_async_engine(
        _database_url(),
        isolation_level="AUTOCOMMIT",
        connect_args={"statement_cache_size": 0},
    )
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto"'))
    finally:
        await engine.dispose()


def main() -> int:
    try:
        asyncio.run(_reset())
    except Exception as exc:
        print(f"Failed to reset test database: {exc}", file=sys.stderr)
        return 1
    print("Reset test database schema: public")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
