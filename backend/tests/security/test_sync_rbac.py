"""RBAC tests for local-first sync endpoints."""

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
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.school import SchoolFactory
from tests.factories.sync_queue import SyncConflictFactory, SyncDeviceFactory, SyncQueueFactory


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
        email=f"{label}-{suffix}@sync-rbac.ma",
        full_name=f"{label.title()} Sync RBAC {suffix}",
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
        source="pytest-sync-rbac",
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
async def sync_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"SRB-{uuid.uuid4().hex[:6].upper()}",
            name="Sync RBAC School",
            city="Casablanca",
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

        device = await SyncDeviceFactory.create(
            session=session,
            school=school,
            device_name="rbac-device",
        )
        queue_item = await SyncQueueFactory.create(
            session=session,
            device=device,
            entity_type="attendance",
            payload={"status": "present"},
        )
        conflict = await SyncConflictFactory.create(
            session=session,
            queue_item=queue_item,
        )
        await session.commit()

    return {
        **actors,
        "device": device,
        "queue_item": queue_item,
        "conflict": conflict,
    }


@pytest.mark.asyncio
async def test_teacher_cannot_register_device(client, sync_rbac_context):
    response = await client.post(
        "/sync/devices",
        headers=auth_header(sync_rbac_context["teacher"]["token"]),
        json={"device_name": "blocked", "device_type": "browser"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_can_push_changes(client, sync_rbac_context):
    response = await client.post(
        "/sync/push",
        headers=auth_header(sync_rbac_context["teacher"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
        json={
            "items": [
                {
                    "entity_type": "grade",
                    "entity_id": str(uuid.uuid4()),
                    "operation": "create",
                    "payload": {"score": 16},
                }
            ]
        },
    )

    assert response.status_code == 202, response.text


@pytest.mark.asyncio
async def test_parent_cannot_push_changes(client, sync_rbac_context):
    response = await client.post(
        "/sync/push",
        headers=auth_header(sync_rbac_context["parent"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
        json={
            "items": [
                {
                    "entity_type": "grade",
                    "entity_id": str(uuid.uuid4()),
                    "operation": "create",
                    "payload": {"score": 10},
                }
            ]
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_can_pull_changes(client, sync_rbac_context):
    response = await client.post(
        "/sync/pull",
        headers=auth_header(sync_rbac_context["parent"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_student_cannot_pull_changes(client, sync_rbac_context):
    response = await client.post(
        "/sync/pull",
        headers=auth_header(sync_rbac_context["student"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_can_get_health(client, sync_rbac_context):
    response = await client.get(
        "/sync/health",
        headers=auth_header(sync_rbac_context["teacher"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_student_cannot_get_health(client, sync_rbac_context):
    response = await client.get(
        "/sync/health",
        headers=auth_header(sync_rbac_context["student"]["token"]),
        params={"device_id": str(sync_rbac_context["device"].id)},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_list_conflicts(client, sync_rbac_context):
    response = await client.get(
        "/sync/conflicts",
        headers=auth_header(sync_rbac_context["teacher"]["token"]),
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_director_can_list_conflicts(client, sync_rbac_context):
    response = await client.get(
        "/sync/conflicts",
        headers=auth_header(sync_rbac_context["director"]["token"]),
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_resolve_conflict(client, sync_rbac_context):
    response = await client.post(
        f"/sync/conflicts/{sync_rbac_context['conflict'].id}/resolve",
        headers=auth_header(sync_rbac_context["teacher"]["token"]),
        json={"resolution": "manual"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_admin_can_resolve_conflict(client, sync_rbac_context):
    response = await client.post(
        f"/sync/conflicts/{sync_rbac_context['conflict'].id}/resolve",
        headers=auth_header(sync_rbac_context["admin"]["token"]),
        json={"resolution": "manual"},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/sync/devices", "/sync/conflicts", "/sync/health"])
async def test_sync_routes_require_token(client, sync_rbac_context, path: str):
    params = None
    if path == "/sync/health":
        params = {"device_id": str(sync_rbac_context["device"].id)}
    response = await client.get(path, params=params)

    assert response.status_code == 401, response.text
