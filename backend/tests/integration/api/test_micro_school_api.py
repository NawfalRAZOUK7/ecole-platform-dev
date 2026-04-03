"""Integration tests for micro-school API endpoints."""

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
from tests.factories.erp import AcademicYearFactory
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.micro_school import (
    MicroEnrollmentFactory,
    MicroGroupFactory,
    MicroPaymentFactory,
    MicroProgressLogFactory,
    MicroResourceFactory,
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
        email=f"{label}-{suffix}@micro.ecole.ma",
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
        source="pytest-micro-api",
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
async def micro_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"MICRO-{uuid.uuid4().hex[:6].upper()}",
            name="Micro API School",
            city="Casablanca",
        )
        await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2025-2026",
        )
        admin = await _create_actor(
            session,
            school=school,
            role=RoleCode.ADM.value,
            label="admin",
        )
        educator = await _create_actor(
            session,
            school=school,
            role=RoleCode.EDUCATOR.value,
            label="educator",
        )
        parent = await _create_actor(
            session,
            school=school,
            role=RoleCode.PAR.value,
            label="parent",
        )
        other_parent = await _create_actor(
            session,
            school=school,
            role=RoleCode.PAR.value,
            label="other-parent",
        )
        student = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="student",
        )

        micro_school = await MicroSchoolFactory.create(
            session=session,
            educator_id=educator["user"].id,
            name="Micro-Ecole Initiale",
            city="Casablanca",
            neighborhood="Maarif",
            phone="+212612345678",
        )
        group = await MicroGroupFactory.create(
            session=session,
            micro_school=micro_school,
            name="Groupe Initial",
        )
        enrollment = await MicroEnrollmentFactory.create(
            session=session,
            micro_group=group,
            parent_id=parent["user"].id,
            child_name="Lina",
        )
        payment = await MicroPaymentFactory.create(
            session=session,
            child_enrollment=enrollment,
            micro_school_id=micro_school.id,
            parent_id=parent["user"].id,
            status="paid",
            paid_at=datetime(2026, 4, 3, 10, 0, tzinfo=UTC),
            amount=350,
        )
        resource = await MicroResourceFactory.create(
            session=session,
            title="Comptines du matin",
            resource_type="song",
            language="fr",
        )
        progress = await MicroProgressLogFactory.create(
            session=session,
            micro_enrollment=enrollment,
            educator_id=educator["user"].id,
            milestone_tag="language",
        )
        await session.commit()

    return {
        "school": school,
        "admin": admin,
        "educator": educator,
        "parent": parent,
        "other_parent": other_parent,
        "student": student,
        "micro_school": micro_school,
        "group": group,
        "enrollment": enrollment,
        "payment": payment,
        "resource": resource,
        "progress": progress,
    }


class TestMicroSchoolApi:
    @pytest.mark.asyncio
    async def test_educator_can_create_micro_school(self, client, micro_api_context):
        response = await client.post(
            "/micro/schools",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "educator_id": str(micro_api_context["educator"]["user"].id),
                "name": "Micro-Ecole Bourgogne",
                "neighborhood": "Bourgogne",
                "city": "Casablanca",
                "phone": "+212612300001",
                "max_capacity": 18,
            },
        )

        assert response.status_code == 201, response.text
        payload = response.json()["data"]
        assert payload["name"] == "Micro-Ecole Bourgogne"
        assert payload["educator_id"] == str(micro_api_context["educator"]["user"].id)

    @pytest.mark.asyncio
    async def test_admin_can_list_micro_schools(self, client, micro_api_context):
        response = await client.get(
            "/micro/schools",
            headers=auth_header(micro_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        items = response.json()["data"]
        assert len(items) == 1
        assert items[0]["id"] == str(micro_api_context["micro_school"].id)

    @pytest.mark.asyncio
    async def test_parent_cannot_create_micro_school(self, client, micro_api_context):
        response = await client.post(
            "/micro/schools",
            headers=auth_header(micro_api_context["parent"]["token"]),
            json={
                "name": "Tentative Parent",
                "neighborhood": "Maarif",
                "city": "Casablanca",
                "phone": "+212612300002",
                "max_capacity": 10,
            },
        )

        assert response.status_code == 403, response.text

    @pytest.mark.asyncio
    async def test_educator_can_create_micro_group(self, client, micro_api_context):
        response = await client.post(
            "/micro/groups",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "micro_school_id": str(micro_api_context["micro_school"].id),
                "name": "Groupe Papillons",
                "age_range_min": 2,
                "age_range_max": 4,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["name"] == "Groupe Papillons"

    @pytest.mark.asyncio
    async def test_educator_can_list_groups_for_micro_school(self, client, micro_api_context):
        response = await client.get(
            f"/micro/schools/{micro_api_context['micro_school'].id}/groups",
            headers=auth_header(micro_api_context["educator"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"][0]["id"] == str(micro_api_context["group"].id)

    @pytest.mark.asyncio
    async def test_educator_can_create_enrollment(self, client, micro_api_context):
        response = await client.post(
            "/micro/enrollments",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "micro_group_id": str(micro_api_context["group"].id),
                "child_name": "Safa",
                "parent_id": str(micro_api_context["parent"]["user"].id),
                "date_of_birth": "2022-08-04",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["child_name"] == "Safa"

    @pytest.mark.asyncio
    async def test_parent_cannot_create_enrollment(self, client, micro_api_context):
        response = await client.post(
            "/micro/enrollments",
            headers=auth_header(micro_api_context["parent"]["token"]),
            json={
                "micro_group_id": str(micro_api_context["group"].id),
                "child_name": "Safa",
                "parent_id": str(micro_api_context["parent"]["user"].id),
                "date_of_birth": "2022-08-04",
            },
        )

        assert response.status_code == 403, response.text

    @pytest.mark.asyncio
    async def test_educator_can_list_enrollments(self, client, micro_api_context):
        response = await client.get(
            "/micro/enrollments",
            headers=auth_header(micro_api_context["educator"]["token"]),
        )

        assert response.status_code == 200, response.text
        items = response.json()["data"]
        assert [item["id"] for item in items] == [str(micro_api_context["enrollment"].id)]

    @pytest.mark.asyncio
    async def test_educator_can_create_payment(self, client, micro_api_context):
        response = await client.post(
            "/micro/payments",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "micro_school_id": str(micro_api_context["micro_school"].id),
                "parent_id": str(micro_api_context["parent"]["user"].id),
                "child_enrollment_id": str(micro_api_context["enrollment"].id),
                "amount": 420.0,
                "period_start": "2026-04-01",
                "period_end": "2026-04-30",
                "status": "paid",
            },
        )

        assert response.status_code == 201, response.text
        payload = response.json()["data"]
        assert payload["status"] == "paid"
        assert payload["paid_at"] is not None

    @pytest.mark.asyncio
    async def test_parent_can_list_own_payments(self, client, micro_api_context):
        response = await client.get(
            "/micro/payments",
            headers=auth_header(micro_api_context["parent"]["token"]),
        )

        assert response.status_code == 200, response.text
        items = response.json()["data"]
        assert [item["id"] for item in items] == [str(micro_api_context["payment"].id)]

    @pytest.mark.asyncio
    async def test_educator_can_get_payment_analytics(self, client, micro_api_context):
        response = await client.get(
            "/micro/payments/analytics",
            headers=auth_header(micro_api_context["educator"]["token"]),
            params={"micro_school_id": str(micro_api_context["micro_school"].id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["collected_amount"] >= 350.0
        assert payload["paid_count"] >= 1

    @pytest.mark.asyncio
    async def test_educator_can_create_resource(self, client, micro_api_context):
        response = await client.post(
            "/micro/resources",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "title": "Puzzle des formes",
                "resource_type": "game",
                "age_group": "3-5",
                "language": "fr",
                "description": "Jeu simple sur les formes.",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["title"] == "Puzzle des formes"

    @pytest.mark.asyncio
    async def test_educator_can_list_resources(self, client, micro_api_context):
        response = await client.get(
            "/micro/resources",
            headers=auth_header(micro_api_context["educator"]["token"]),
        )

        assert response.status_code == 200, response.text
        items = response.json()["data"]
        assert any(item["id"] == str(micro_api_context["resource"].id) for item in items)

    @pytest.mark.asyncio
    async def test_educator_can_create_progress_log(self, client, micro_api_context):
        response = await client.post(
            "/micro/progress-logs",
            headers=auth_header(micro_api_context["educator"]["token"]),
            json={
                "micro_enrollment_id": str(micro_api_context["enrollment"].id),
                "date": "2026-04-03",
                "note": "Bonne participation au chant du matin.",
                "milestone_tag": "language",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["milestone_tag"] == "language"

    @pytest.mark.asyncio
    async def test_parent_can_list_progress_logs_for_own_child(self, client, micro_api_context):
        response = await client.get(
            "/micro/progress-logs",
            headers=auth_header(micro_api_context["parent"]["token"]),
            params={"micro_enrollment_id": str(micro_api_context["enrollment"].id)},
        )

        assert response.status_code == 200, response.text
        items = response.json()["data"]
        assert [item["id"] for item in items] == [str(micro_api_context["progress"].id)]

    @pytest.mark.asyncio
    async def test_micro_endpoints_require_token(self, client, micro_api_context):
        response = await client.get("/micro/schools")

        assert response.status_code == 401
