"""Integration tests for local-first sync API endpoints."""

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
from app.models.sync_queue import SyncQueueStatus
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.school import SchoolFactory
from tests.factories.sync_queue import (
    SyncCheckpointFactory,
    SyncDeviceFactory,
    SyncQueueFactory,
)


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
        email=f"{label}-{suffix}@sync-api.ma",
        full_name=f"{label.title()} Sync {suffix}",
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
        source="pytest-sync-api",
    )
    token = create_access_token(user.id, role, school.id, auth_session.id)
    return {"user": user, "token": token}


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
async def sync_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"SAP-{uuid.uuid4().hex[:6].upper()}",
            name="Sync API School",
            city="Rabat",
        )
        admin = await _create_actor(session, school=school, role=RoleCode.ADM.value, label="admin")
        director = await _create_actor(
            session,
            school=school,
            role=RoleCode.DIR.value,
            label="director",
        )
        teacher = await _create_actor(
            session,
            school=school,
            role=RoleCode.TCH.value,
            label="teacher",
        )
        parent = await _create_actor(
            session,
            school=school,
            role=RoleCode.PAR.value,
            label="parent",
        )
        student = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="student",
        )
        device = await SyncDeviceFactory.create(
            session=session,
            school=school,
            device_name="shared-tablet",
        )
        peer_device = await SyncDeviceFactory.create(
            session=session,
            school=school,
            device_name="peer-tablet",
        )
        synced_item = await SyncQueueFactory.create(
            session=session,
            device=peer_device,
            status=SyncQueueStatus.SYNCED.value,
            entity_type="grade",
            payload={"score": 18},
        )
        checkpoint = await SyncCheckpointFactory.create(
            session=session,
            device=device,
            last_entity_type="grade",
            last_entity_id=synced_item.entity_id,
            records_synced=1,
        )
        await session.commit()

    return {
        "school": school,
        "admin": admin,
        "director": director,
        "teacher": teacher,
        "parent": parent,
        "student": student,
        "device": device,
        "peer_device": peer_device,
        "synced_item": synced_item,
        "checkpoint": checkpoint,
    }


async def _create_conflict(client, context) -> dict[str, object]:
    shared_entity_id = str(uuid.uuid4())
    first = await client.post(
        "/sync/push",
        headers=auth_header(context["teacher"]["token"]),
        params={"device_id": str(context["device"].id)},
        json={
            "items": [
                {
                    "entity_type": "attendance",
                    "entity_id": shared_entity_id,
                    "operation": "create",
                    "payload": {"status": "absent"},
                }
            ]
        },
    )
    assert first.status_code == 202, first.text
    second = await client.post(
        "/sync/push",
        headers=auth_header(context["teacher"]["token"]),
        params={"device_id": str(context["device"].id)},
        json={
            "items": [
                {
                    "entity_type": "attendance",
                    "entity_id": shared_entity_id,
                    "operation": "create",
                    "payload": {"status": "present"},
                }
            ]
        },
    )
    assert second.status_code == 202, second.text
    return second.json()["data"]


class TestSyncApi:
    @pytest.mark.asyncio
    async def test_admin_can_register_device(self, client, sync_api_context):
        response = await client.post(
            "/sync/devices",
            headers=auth_header(sync_api_context["admin"]["token"]),
            json={
                "device_name": "lab-browser",
                "device_type": "browser",
                "firmware_version": "2.0.0",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["device_name"] == "lab-browser"

    @pytest.mark.asyncio
    async def test_director_can_list_devices(self, client, sync_api_context):
        response = await client.get(
            "/sync/devices",
            headers=auth_header(sync_api_context["director"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_push_changes(self, client, sync_api_context):
        response = await client.post(
            "/sync/push",
            headers=auth_header(sync_api_context["teacher"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
            json={
                "items": [
                    {
                        "entity_type": "attendance",
                        "entity_id": str(uuid.uuid4()),
                        "operation": "create",
                        "payload": {"status": "present"},
                    }
                ]
            },
        )

        assert response.status_code == 202, response.text
        assert response.json()["data"]["accepted_count"] == 1

    @pytest.mark.asyncio
    async def test_teacher_conflicting_push_returns_conflict_count(self, client, sync_api_context):
        payload = await _create_conflict(client, sync_api_context)

        assert payload["conflict_count"] == 1
        assert len(payload["conflict_ids"]) == 1

    @pytest.mark.asyncio
    async def test_parent_cannot_push_changes(self, client, sync_api_context):
        response = await client.post(
            "/sync/push",
            headers=auth_header(sync_api_context["parent"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
            json={
                "items": [
                    {
                        "entity_type": "attendance",
                        "entity_id": str(uuid.uuid4()),
                        "operation": "create",
                        "payload": {"status": "present"},
                    }
                ]
            },
        )

        assert response.status_code == 403, response.text

    @pytest.mark.asyncio
    async def test_parent_can_pull_changes(self, client, sync_api_context):
        response = await client.post(
            "/sync/pull",
            headers=auth_header(sync_api_context["parent"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]["changes"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_get_status(self, client, sync_api_context):
        await client.post(
            "/sync/push",
            headers=auth_header(sync_api_context["teacher"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
            json={
                "items": [
                    {
                        "entity_type": "grade",
                        "entity_id": str(uuid.uuid4()),
                        "operation": "create",
                        "payload": {"score": 15},
                    }
                ]
            },
        )

        response = await client.get(
            "/sync/status",
            headers=auth_header(sync_api_context["teacher"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["pending_count"] >= 1

    @pytest.mark.asyncio
    async def test_admin_can_list_conflicts(self, client, sync_api_context):
        await _create_conflict(client, sync_api_context)

        response = await client.get(
            "/sync/conflicts",
            headers=auth_header(sync_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_director_can_resolve_conflict(self, client, sync_api_context):
        payload = await _create_conflict(client, sync_api_context)
        conflict_id = payload["conflict_ids"][0]

        response = await client.post(
            f"/sync/conflicts/{conflict_id}/resolve",
            headers=auth_header(sync_api_context["director"]["token"]),
            json={"resolution": "manual"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["resolution"] == "manual"

    @pytest.mark.asyncio
    async def test_admin_can_create_checkpoint(self, client, sync_api_context):
        response = await client.post(
            "/sync/checkpoint",
            headers=auth_header(sync_api_context["admin"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
            json={
                "last_entity_type": "attendance",
                "last_entity_id": str(uuid.uuid4()),
                "records_synced": 2,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["records_synced"] == 2

    @pytest.mark.asyncio
    async def test_admin_can_list_checkpoints(self, client, sync_api_context):
        response = await client.get(
            "/sync/checkpoints",
            headers=auth_header(sync_api_context["admin"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_parent_can_get_health(self, client, sync_api_context):
        response = await client.get(
            "/sync/health",
            headers=auth_header(sync_api_context["parent"]["token"]),
            params={"device_id": str(sync_api_context["device"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["health"] in {"healthy", "degraded", "stale"}

    @pytest.mark.asyncio
    async def test_sync_status_requires_token(self, client, sync_api_context):
        response = await client.get(
            "/sync/status",
            params={"device_id": str(sync_api_context["device"].id)},
        )

        assert response.status_code == 401, response.text
