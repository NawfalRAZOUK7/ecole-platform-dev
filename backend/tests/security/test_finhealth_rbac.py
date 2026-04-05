"""RBAC tests for financial health endpoints."""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.iam import RoleCode
from tests.factories.erp import AcademicYearFactory
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.school import SchoolFactory


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_actor(
    session: AsyncSession,
    *,
    school,
    role: str,
    label: str,
) -> dict[str, object]:
    suffix = uuid.uuid4().hex[:8]
    user = await UserFactory.create(
        session=session,
        school=school,
        email=f"{label}-{suffix}@finhealth-rbac.ma",
        full_name=f"{label.title()} Financial Health {suffix}",
    )
    await MembershipFactory.create(
        session=session,
        user=user,
        school_id=school.id,
        role_code=role,
    )
    auth_session = await SessionFactory.create(
        session=session,
        user=user,
        school_id=school.id,
        source="pytest-finhealth-rbac",
    )
    return {
        "user": user,
        "token": create_access_token(user.id, role, school.id, auth_session.id),
    }


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


@pytest_asyncio.fixture(loop_scope="function")
async def session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(loop_scope="function")
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver/api/v1",
    ) as api_client:
        yield api_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="function")
async def finhealth_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"FHR-{uuid.uuid4().hex[:6].upper()}",
            name="Financial Health RBAC School",
            city="Casablanca",
        )
        academic_year = await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2025-2026",
        )
        actors = {}
        for role, label in (
            (RoleCode.ADM.value, "admin"),
            (RoleCode.DIR.value, "director"),
            (RoleCode.TCH.value, "teacher"),
            (RoleCode.PAR.value, "parent"),
            (RoleCode.STD.value, "student"),
            (RoleCode.SUP.value, "superadmin"),
            (RoleCode.SYS.value, "system"),
        ):
            actors[label] = await _create_actor(session, school=school, role=role, label=label)
        await session.commit()

    return {"school": school, "academic_year": academic_year, **actors}


@pytest.mark.parametrize("actor_label", ["admin", "director", "superadmin", "system"])
@pytest.mark.asyncio
async def test_read_roles_can_list_retention(client, finhealth_rbac_context, actor_label):
    response = await client.get(
        "/financial-health/retention",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
    )

    assert response.status_code == 200, response.text


@pytest.mark.parametrize("actor_label", ["teacher", "parent", "student"])
@pytest.mark.asyncio
async def test_non_read_roles_cannot_list_retention(client, finhealth_rbac_context, actor_label):
    response = await client.get(
        "/financial-health/retention",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
    )

    assert response.status_code == 403, response.text


@pytest.mark.parametrize("actor_label", ["admin", "director", "superadmin", "system"])
@pytest.mark.asyncio
async def test_compute_roles_can_trigger_snapshot_compute(client, finhealth_rbac_context, actor_label):
    response = await client.post(
        "/financial-health/snapshot/compute",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
        json={"snapshot_date": "2026-04-05"},
    )

    assert response.status_code == 202, response.text


@pytest.mark.parametrize("actor_label", ["teacher", "parent", "student"])
@pytest.mark.asyncio
async def test_non_compute_roles_cannot_trigger_snapshot_compute(
    client,
    finhealth_rbac_context,
    actor_label,
):
    response = await client.post(
        "/financial-health/snapshot/compute",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
        json={"snapshot_date": "2026-04-05"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.parametrize("actor_label", ["admin", "director", "superadmin", "system"])
@pytest.mark.asyncio
async def test_export_roles_can_download_csv(client, finhealth_rbac_context, actor_label):
    response = await client.get(
        "/financial-health/export/csv",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
    )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("text/csv")


@pytest.mark.parametrize("actor_label", ["teacher", "parent", "student"])
@pytest.mark.asyncio
async def test_non_export_roles_cannot_download_csv(client, finhealth_rbac_context, actor_label):
    response = await client.get(
        "/financial-health/export/csv",
        headers=auth_header(finhealth_rbac_context[actor_label]["token"]),
    )

    assert response.status_code == 403, response.text
