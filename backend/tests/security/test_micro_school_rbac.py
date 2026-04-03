"""RBAC tests for micro-school endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.iam import RoleCode
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.micro_school import (
    MicroEnrollmentFactory,
    MicroGroupFactory,
    MicroPaymentFactory,
    MicroProgressLogFactory,
    MicroSchoolFactory,
)
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
        email=f"{label}-{suffix}@micro-rbac.ma",
        full_name=f"{label.title()} Micro {suffix}",
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
        source="pytest-micro-rbac",
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
async def micro_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"RBAC-{uuid.uuid4().hex[:6].upper()}",
            name="Micro RBAC School",
            city="Casablanca",
        )
        actors = {}
        for role, label in (
            (RoleCode.ADM.value, "admin"),
            (RoleCode.EDUCATOR.value, "educator"),
            (RoleCode.PAR.value, "parent"),
            (RoleCode.STD.value, "student"),
            (RoleCode.TCH.value, "teacher"),
            (RoleCode.SUP.value, "superadmin"),
            (RoleCode.SYS.value, "system"),
            (RoleCode.CONTENT_MGR.value, "content"),
        ):
            actors[label] = await _create_actor(
                session,
                school=school,
                role=role,
                label=label,
            )
        other_parent = await _create_actor(
            session,
            school=school,
            role=RoleCode.PAR.value,
            label="other-parent",
        )

        micro_school = await MicroSchoolFactory.create(
            session=session,
            educator_id=actors["educator"]["user"].id,
            name="Micro-Ecole Securite",
            city="Casablanca",
            neighborhood="Maarif",
            phone="+212612355555",
        )
        group = await MicroGroupFactory.create(session=session, micro_school=micro_school)
        enrollment = await MicroEnrollmentFactory.create(
            session=session,
            micro_group=group,
            parent_id=actors["parent"]["user"].id,
            child_name="Aya",
        )
        other_enrollment = await MicroEnrollmentFactory.create(
            session=session,
            micro_group=group,
            parent_id=other_parent["user"].id,
            child_name="Salma",
        )
        payment = await MicroPaymentFactory.create(
            session=session,
            child_enrollment=enrollment,
            micro_school_id=micro_school.id,
            parent_id=actors["parent"]["user"].id,
            status="paid",
            paid_at=datetime(2026, 4, 3, 11, 0, tzinfo=UTC),
        )
        progress = await MicroProgressLogFactory.create(
            session=session,
            micro_enrollment=enrollment,
            educator_id=actors["educator"]["user"].id,
            milestone_tag="language",
        )
        await MicroProgressLogFactory.create(
            session=session,
            micro_enrollment=other_enrollment,
            educator_id=actors["educator"]["user"].id,
            milestone_tag="social",
        )
        await session.commit()

    return {
        **actors,
        "other_parent": other_parent,
        "micro_school": micro_school,
        "group": group,
        "enrollment": enrollment,
        "other_enrollment": other_enrollment,
        "payment": payment,
        "progress": progress,
    }


@pytest.mark.asyncio
async def test_educator_can_create_micro_school(client, micro_rbac_context):
    response = await client.post(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["educator"]["token"]),
        json={
            "name": "Micro-Ecole Educateur",
            "neighborhood": "Bourgogne",
            "city": "Casablanca",
            "phone": "+212612344444",
            "max_capacity": 15,
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_parent_cannot_create_micro_school(client, micro_rbac_context):
    response = await client.post(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["parent"]["token"]),
        json={
            "name": "Tentative Parent",
            "neighborhood": "Maarif",
            "city": "Casablanca",
            "phone": "+212612344445",
            "max_capacity": 15,
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_admin_cannot_create_micro_school(client, micro_rbac_context):
    response = await client.post(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["admin"]["token"]),
        json={
            "name": "Tentative Admin",
            "neighborhood": "Maarif",
            "city": "Casablanca",
            "phone": "+212612344446",
            "max_capacity": 15,
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_admin_can_list_micro_schools(client, micro_rbac_context):
    response = await client.get(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["admin"]["token"]),
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_educator_can_list_micro_schools(client, micro_rbac_context):
    response = await client.get(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["educator"]["token"]),
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_student_cannot_list_micro_schools(client, micro_rbac_context):
    response = await client.get(
        "/micro/schools",
        headers=auth_header(micro_rbac_context["student"]["token"]),
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_can_read_micro_payments(client, micro_rbac_context):
    response = await client.get(
        "/micro/payments",
        headers=auth_header(micro_rbac_context["parent"]["token"]),
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"][0]["id"] == str(micro_rbac_context["payment"].id)


@pytest.mark.asyncio
async def test_parent_cannot_create_micro_payment(client, micro_rbac_context):
    response = await client.post(
        "/micro/payments",
        headers=auth_header(micro_rbac_context["parent"]["token"]),
        json={
            "micro_school_id": str(micro_rbac_context["micro_school"].id),
            "parent_id": str(micro_rbac_context["parent"]["user"].id),
            "child_enrollment_id": str(micro_rbac_context["enrollment"].id),
            "amount": 450.0,
            "period_start": "2026-04-01",
            "period_end": "2026-04-30",
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_can_read_progress_for_own_child(client, micro_rbac_context):
    response = await client.get(
        "/micro/progress-logs",
        headers=auth_header(micro_rbac_context["parent"]["token"]),
        params={"micro_enrollment_id": str(micro_rbac_context["enrollment"].id)},
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"][0]["id"] == str(micro_rbac_context["progress"].id)


@pytest.mark.asyncio
async def test_parent_cannot_read_progress_for_other_child(client, micro_rbac_context):
    response = await client.get(
        "/micro/progress-logs",
        headers=auth_header(micro_rbac_context["parent"]["token"]),
        params={"micro_enrollment_id": str(micro_rbac_context["other_enrollment"].id)},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_educator_can_create_progress_log(client, micro_rbac_context):
    response = await client.post(
        "/micro/progress-logs",
        headers=auth_header(micro_rbac_context["educator"]["token"]),
        json={
            "micro_enrollment_id": str(micro_rbac_context["enrollment"].id),
            "date": "2026-04-03",
            "note": "Observation securite",
            "milestone_tag": "language",
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_teacher_without_educator_role_cannot_create_progress_log(
    client,
    micro_rbac_context,
):
    response = await client.post(
        "/micro/progress-logs",
        headers=auth_header(micro_rbac_context["teacher"]["token"]),
        json={
            "micro_enrollment_id": str(micro_rbac_context["enrollment"].id),
            "date": "2026-04-03",
            "note": "Tentative enseignant standard",
            "milestone_tag": "language",
        },
    )

    assert response.status_code == 403, response.text
