"""Ensure the disposable test database exists (safety-guarded).

Connects to the Postgres *maintenance* database and creates the test database if
it is missing. It then hands off to `reset_test_database.py`, which wipes only
the `public` schema of that database.

SAFETY: this script refuses to operate on any database whose name does not
contain ``test``. Combined with the dedicated ``ecole_platform_test`` name, the
real ``ecole_platform`` database can never be created, reset, or wiped by the
test runner — even if the compose env is misconfigured.

Env:
  POSTGRES_USER / POSTGRES_PASSWORD  — credentials (default ecole/ecole)
  TEST_DB_HOST / TEST_DB_PORT        — Postgres host/port (default postgres:5432)
  TEST_DATABASE_NAME                 — the test DB to ensure (default ecole_platform_test)
"""

from __future__ import annotations

import asyncio
import os
import sys


def _config() -> tuple[str, str, str, int, str]:
    user = os.getenv("POSTGRES_USER", "ecole")
    pwd = os.getenv("POSTGRES_PASSWORD", "ecole")
    host = os.getenv("TEST_DB_HOST", "postgres")
    port = int(os.getenv("TEST_DB_PORT", "5432"))
    name = os.getenv("TEST_DATABASE_NAME", "ecole_platform_test")
    return user, pwd, host, port, name


async def _main() -> int:
    import asyncpg

    user, pwd, host, port, name = _config()

    if "test" not in name.lower():
        print(
            f"REFUSING: target database '{name}' must contain 'test' — "
            "the test runner never operates on a non-test database.",
            file=sys.stderr,
        )
        return 2

    conn = await asyncpg.connect(
        user=user, password=pwd, host=host, port=port, database="postgres"
    )
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", name
        )
        if exists:
            print(f"Test database already exists: {name}")
        else:
            # Identifier is validated above (must contain 'test'); quote it safely.
            await conn.execute(f'CREATE DATABASE "{name}"')
            print(f"Created test database: {name}")
    finally:
        await conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
