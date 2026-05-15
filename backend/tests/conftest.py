"""Shared test fixtures for integration tests.

Uses the actual database and Redis instances running in Docker.
Seed data must be loaded before running tests (make seed).
"""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.core.feature_flags as feature_flags_module
import app.core.idempotency as idempotency_module
import app.core.rate_limit as rate_limit_module
import app.core.redis as core_redis_module
import app.services.reports.dashboard_analytics as dashboard_analytics_module
import app.services.communication.notification_hub as notification_hub_module
import app.services.academic.progress as progress_module
from app.core.config import settings
from app.core.database import Base, engine as app_engine
from app.core.dependencies import AuthContext
from app.core.permissions import get_permissions_for_role
from app.core.security import hash_password
from app.models.iam import User

# Fixed IDs from seed.py
SCHOOL_ID = "00000000-0000-4000-8000-000000000001"
ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000/api/v1")
TEST_REDIS_URL = os.getenv(
    "TEST_REDIS_URL",
    os.getenv(
        "REDIS_URL",
        f"redis://:{os.getenv('REDIS_PASSWORD', 'change-me-dev-redis')}@localhost:6379/0",
    ),
)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
LOGIN_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
_seed_attempted = False
_seed_auth_state_restored = False

SEED_AUTH_CREDENTIALS = {
    ADMIN_EMAIL: ADMIN_PASSWORD,
    TEACHER_EMAIL: TEACHER_PASSWORD,
    PARENT_EMAIL: PARENT_PASSWORD,
    STUDENT_EMAIL: STUDENT_PASSWORD,
}

LIVE_SEED_AUTH_FIXTURES = {
    "client",
    "admin_token",
    "teacher_token",
    "student_token",
    "parent_token",
}


def _requires_live_redis(request: pytest.FixtureRequest) -> bool:
    """Only integration-style suites should depend on a running Redis instance."""
    path = Path(str(request.node.fspath)).resolve()
    if "unit" in path.parts or path.name.startswith("test_unit_"):
        return False
    return True


def _uses_root_live_seed_auth(request: pytest.FixtureRequest) -> bool:
    """Return True for root integration tests that authenticate against dev seed users."""
    path = Path(str(request.node.fspath)).resolve()
    if path.parent != BACKEND_ROOT / "tests":
        return False
    return bool(LIVE_SEED_AUTH_FIXTURES.intersection(request.fixturenames))


def _mutates_seed_admin_password(request: pytest.FixtureRequest) -> bool:
    """Known live API tests that exercise password changes on the seeded admin."""
    return (
        "tests/test_security_audit.py::TestPasswordPolicy"
        in request.node.nodeid.replace("\\", "/")
    )


async def _restore_seed_auth_credentials(
    credentials: dict[str, str] | None = None,
) -> None:
    """Best-effort repair for shared dev seed credentials mutated by API tests."""
    selected_credentials = credentials or SEED_AUTH_CREDENTIALS
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.email.in_(list(selected_credentials)))
            )
            users_by_email = {user.email: user for user in result.scalars()}
            for email, password in selected_credentials.items():
                user = users_by_email.get(email)
                if user is not None:
                    user.password_hash = hash_password(password)
            await session.commit()
    except Exception:
        # Some isolated/unit suites run without the shared dev database.
        # Login-dependent tests will still fail clearly if seed data is unavailable.
        pass
    finally:
        await engine.dispose()


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Keep `-k "sync"` scoped to the sync feature slice.

    Pytest keyword matching treats ``sync`` as a substring of ``asyncio``, which
    unintentionally selects a large portion of the async suite. The roadmap uses
    the exact command ``pytest -k "sync"``, so narrow that specific keyword to
    files whose node ids intentionally target the sync feature.
    """

    keyword = (config.option.keyword or "").strip().lower()
    if keyword != "sync":
        return

    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        nodeid = item.nodeid.lower()
        if "test_sync_" in nodeid or "/sync_" in nodeid:
            selected.append(item)
        else:
            deselected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def school_id():
    return SCHOOL_ID


@pytest_asyncio.fixture(loop_scope="function")
async def client():
    """Async HTTP client for integration tests."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=LOGIN_TIMEOUT) as c:
        yield c


@pytest_asyncio.fixture(autouse=True)
async def restore_live_seed_auth_state(request: pytest.FixtureRequest):
    """Keep shared dev seed credentials stable across tests and reruns."""
    global _seed_auth_state_restored

    if not _uses_root_live_seed_auth(request):
        yield
        return

    if not _seed_auth_state_restored:
        await _restore_seed_auth_credentials()
        _seed_auth_state_restored = True

    try:
        yield
    finally:
        if _mutates_seed_admin_password(request):
            await _restore_seed_auth_credentials({ADMIN_EMAIL: ADMIN_PASSWORD})


def _reseed_dev_database() -> None:
    try:
        subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                "infra/docker-compose.dev.yml",
                "exec",
                "-T",
                "backend",
                "python",
                "-m",
                "app.seed",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        # Docker may not be available; fall back to direct seed if possible.
        try:
            subprocess.run(
                [sys.executable, "-m", "app.seed"],
                cwd=BACKEND_ROOT,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            pass  # Seed data should already be loaded; tests will fail clearly if not.


async def _login_with_seed_retry(
    client: httpx.AsyncClient,
    *,
    email: str,
    password: str,
) -> str:
    global _seed_attempted

    payload = {
        "email": email,
        "password": password,
        "school_id": SCHOOL_ID,
    }
    try:
        response = await client.post("/auth/login", json=payload, timeout=LOGIN_TIMEOUT)
    except httpx.ReadTimeout:
        if not _seed_attempted:
            _seed_attempted = True
            _reseed_dev_database()
        response = await client.post("/auth/login", json=payload, timeout=LOGIN_TIMEOUT)
    if response.status_code == 401 and not _seed_attempted:
        _seed_attempted = True
        _reseed_dev_database()
        response = await client.post("/auth/login", json=payload, timeout=LOGIN_TIMEOUT)

    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture(loop_scope="function")
async def admin_token(client: httpx.AsyncClient) -> str:
    """Get an admin access token."""
    return await _login_with_seed_retry(
        client,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def teacher_token(client: httpx.AsyncClient) -> str:
    """Get a teacher access token."""
    return await _login_with_seed_retry(
        client,
        email=TEACHER_EMAIL,
        password=TEACHER_PASSWORD,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def student_token(client: httpx.AsyncClient) -> str:
    """Get a student access token."""
    return await _login_with_seed_retry(
        client,
        email=STUDENT_EMAIL,
        password=STUDENT_PASSWORD,
    )


@pytest_asyncio.fixture(loop_scope="function")
async def parent_token(client: httpx.AsyncClient) -> str:
    """Get a parent access token."""
    return await _login_with_seed_retry(
        client,
        email=PARENT_EMAIL,
        password=PARENT_PASSWORD,
    )


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """PostgreSQL URL for integration-style tests.

    Uses the disposable test database on the shared dev postgres container
    (ecole-postgres) instead of spinning up a new container per session.
    This cuts ~2-3 minutes off every test run.
    """
    dev_url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://ecole:change-me@localhost:5432/ecole_platform_test",
    )
    return dev_url


@pytest_asyncio.fixture(loop_scope="function")
async def engine(postgres_url: str):
    """Async SQLAlchemy engine bound to the disposable PostgreSQL instance."""
    eng = create_async_engine(postgres_url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(_create_postgres_enum_types)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(engine) -> AsyncSession:
    """Per-test SQLAlchemy session wrapped in a rollback-only outer transaction."""
    async with engine.connect() as conn:
        transaction = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    """Avoid cross-event-loop asyncpg reuse in tests that import app.core.database.async_session."""
    await app_engine.dispose()
    try:
        yield
    finally:
        await app_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache(request: pytest.FixtureRequest):
    """Keep Redis-backed caches and throttles deterministic across test reruns."""
    if not _requires_live_redis(request):
        yield
        return

    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    redis_patterns = (
        "ecole:*:analytics:*",
        "ratelimit:*",
        "login_attempts:*",
        "notifications:unread-count:*",
        "idem:*",
    )

    async def _clear() -> None:
        keys: list[str] = []
        for pattern in redis_patterns:
            keys.extend(await client.keys(pattern))
        if keys:
            await client.delete(*sorted(set(keys)))

    await _clear()
    try:
        yield
    finally:
        await _clear()


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
):
    """Point local service-layer Redis calls at the authenticated dev Redis instance."""
    if not _requires_live_redis(request):
        yield
        return

    client = redis.from_url(TEST_REDIS_URL, decode_responses=True)
    for module in (
        core_redis_module,
        dashboard_analytics_module,
        progress_module,
        notification_hub_module,
        feature_flags_module,
        idempotency_module,
        rate_limit_module,
    ):
        monkeypatch.setattr(module, "redis_client", client)
    yield


def _build_auth_context(role: str) -> AuthContext:
    school_id = uuid.uuid4()
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=school_id,
        session_id=uuid.uuid4(),
        permissions=get_permissions_for_role(role),
    )


def _create_postgres_enum_types(sync_conn) -> None:
    """Create native PostgreSQL enum types required by models with create_type=False."""
    created_names: set[str] = set()
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            column_type = column.type
            if not isinstance(column_type, PgEnum) or column_type.name in created_names:
                continue
            PgEnum(
                *column_type.enums,
                name=column_type.name,
            ).create(sync_conn, checkfirst=True)
            created_names.add(column_type.name)


@pytest.fixture
def admin_auth() -> AuthContext:
    return _build_auth_context("ADM")


@pytest.fixture
def teacher_auth() -> AuthContext:
    return _build_auth_context("TCH")


@pytest.fixture
def student_auth() -> AuthContext:
    return _build_auth_context("STD")


@pytest.fixture
def parent_auth() -> AuthContext:
    return _build_auth_context("PAR")


@pytest.fixture
def sup_auth() -> AuthContext:
    return _build_auth_context("SUP")
