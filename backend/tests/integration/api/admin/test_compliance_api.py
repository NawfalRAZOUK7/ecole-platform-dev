"""Integration tests for MEN compliance API endpoints."""

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
from tests.factories.erp import AcademicYearFactory, ClassFactory
from tests.factories.iam import MembershipFactory, SessionFactory, UserFactory
from tests.factories.lms import CourseFactory
from tests.factories.men_compliance import MenCurriculumFactory, MenObjectiveFactory
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
        email=f"{label}-{suffix}@compliance-api.ma",
        full_name=f"{label.title()} Compliance {suffix}",
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
        source="pytest-compliance-api",
    )
    token = create_access_token(user.id, role, school.id, auth_session.id)
    return {"user": user, "token": token}


async def _create_mapping(client, context) -> dict[str, object]:
    response = await client.post(
        "/compliance/mappings",
        headers=auth_header(context["teacher"]["token"]),
        json={
            "objective_id": str(context["objective"].id),
            "course_id": str(context["course"].id),
            "coverage_percent": 100,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]


async def _generate_report(client, context) -> dict[str, object]:
    response = await client.post(
        "/compliance/reports/generate",
        headers=auth_header(context["director"]["token"]),
        json={
            "curriculum_id": str(context["curriculum"].id),
            "academic_year_id": str(context["academic_year"].id),
        },
    )
    assert response.status_code == 202, response.text
    return response.json()["data"]


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
async def compliance_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"CAP-{uuid.uuid4().hex[:6].upper()}",
            name="Compliance API School",
            city="Casablanca",
        )
        academic_year = await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2025-2026",
        )
        school_class = await ClassFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            code="3C-A",
            name="3eme C API",
        )
        admin = await _create_actor(
            session, school=school, role=RoleCode.ADM.value, label="admin"
        )
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
        student = await _create_actor(
            session,
            school=school,
            role=RoleCode.STD.value,
            label="student",
        )
        superadmin = await _create_actor(
            session,
            school=school,
            role=RoleCode.SUP.value,
            label="superadmin",
        )
        system = await _create_actor(
            session,
            school=school,
            role=RoleCode.SYS.value,
            label="system",
        )
        course = await CourseFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            class_obj=school_class,
            teacher=teacher["user"],
            title="Mathematiques 3eme",
        )
        curriculum = await MenCurriculumFactory.create(
            session=session,
            subject=f"mathematics_api_{uuid.uuid4().hex[:6]}",
        )
        objective = await MenObjectiveFactory.create(
            session=session,
            curriculum=curriculum,
            code=f"API-{uuid.uuid4().hex[:6].upper()}-01",
        )
        await session.commit()

    return {
        "school": school,
        "academic_year": academic_year,
        "school_class": school_class,
        "admin": admin,
        "director": director,
        "teacher": teacher,
        "student": student,
        "superadmin": superadmin,
        "system": system,
        "course": course,
        "curriculum": curriculum,
        "objective": objective,
    }


class TestComplianceApi:
    @pytest.mark.asyncio
    async def test_superadmin_can_create_curriculum(
        self, client, compliance_api_context
    ):
        response = await client.post(
            "/compliance/curricula",
            headers=auth_header(compliance_api_context["superadmin"]["token"]),
            json={
                "level": "college",
                "grade": "3eme",
                "subject": f"science_{uuid.uuid4().hex[:6]}",
                "academic_year": "2025-2026",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["level"] == "college"

    @pytest.mark.asyncio
    async def test_teacher_can_list_curricula(self, client, compliance_api_context):
        response = await client.get(
            "/compliance/curricula",
            headers=auth_header(compliance_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_superadmin_can_create_objective(
        self, client, compliance_api_context
    ):
        response = await client.post(
            f"/compliance/curricula/{compliance_api_context['curriculum'].id}/objectives",
            headers=auth_header(compliance_api_context["superadmin"]["token"]),
            json={
                "code": f"API-{uuid.uuid4().hex[:6].upper()}-02",
                "title_fr": "Nouveau chapitre",
                "title_ar": "وحدة جديدة",
                "trimester": 2,
                "unit_number": 2,
                "display_order": 2,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["curriculum_id"] == str(
            compliance_api_context["curriculum"].id
        )

    @pytest.mark.asyncio
    async def test_teacher_can_list_objectives(self, client, compliance_api_context):
        response = await client.get(
            f"/compliance/curricula/{compliance_api_context['curriculum'].id}/objectives",
            headers=auth_header(compliance_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_create_mapping(self, client, compliance_api_context):
        response = await client.post(
            "/compliance/mappings",
            headers=auth_header(compliance_api_context["teacher"]["token"]),
            json={
                "objective_id": str(compliance_api_context["objective"].id),
                "course_id": str(compliance_api_context["course"].id),
                "coverage_percent": 100,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["objective_id"] == str(
            compliance_api_context["objective"].id
        )

    @pytest.mark.asyncio
    async def test_teacher_can_list_mappings(self, client, compliance_api_context):
        await _create_mapping(client, compliance_api_context)

        response = await client.get(
            "/compliance/mappings",
            headers=auth_header(compliance_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_director_can_get_dashboard(self, client, compliance_api_context):
        await _create_mapping(client, compliance_api_context)

        response = await client.get(
            "/compliance/dashboard",
            headers=auth_header(compliance_api_context["director"]["token"]),
            params={
                "academic_year_id": str(compliance_api_context["academic_year"].id)
            },
        )

        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        target_item = next(
            item
            for item in payload["items"]
            if item["curriculum_id"] == str(compliance_api_context["curriculum"].id)
        )
        assert target_item["compliance_percent"] >= 100.0

    @pytest.mark.asyncio
    async def test_director_can_generate_report(self, client, compliance_api_context):
        await _create_mapping(client, compliance_api_context)

        response = await client.post(
            "/compliance/reports/generate",
            headers=auth_header(compliance_api_context["director"]["token"]),
            json={
                "curriculum_id": str(compliance_api_context["curriculum"].id),
                "academic_year_id": str(compliance_api_context["academic_year"].id),
            },
        )

        assert response.status_code == 202, response.text
        assert response.json()["data"]["mapped_objectives"] >= 1

    @pytest.mark.asyncio
    async def test_director_can_list_reports(self, client, compliance_api_context):
        await _create_mapping(client, compliance_api_context)
        await _generate_report(client, compliance_api_context)

        response = await client.get(
            "/compliance/reports",
            headers=auth_header(compliance_api_context["director"]["token"]),
            params={
                "academic_year_id": str(compliance_api_context["academic_year"].id)
            },
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_director_can_get_report_detail(self, client, compliance_api_context):
        await _create_mapping(client, compliance_api_context)
        report = await _generate_report(client, compliance_api_context)

        response = await client.get(
            f"/compliance/reports/{report['id']}",
            headers=auth_header(compliance_api_context["director"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["id"] == report["id"]

    @pytest.mark.asyncio
    async def test_director_can_download_report_pdf(
        self, client, compliance_api_context
    ):
        await _create_mapping(client, compliance_api_context)
        report = await _generate_report(client, compliance_api_context)

        response = await client.get(
            f"/compliance/reports/{report['id']}/download",
            headers=auth_header(compliance_api_context["director"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-1.4")

    @pytest.mark.asyncio
    async def test_teacher_can_delete_mapping(self, client, compliance_api_context):
        mapping = await _create_mapping(client, compliance_api_context)

        response = await client.delete(
            f"/compliance/mappings/{mapping['id']}",
            headers=auth_header(compliance_api_context["teacher"]["token"]),
        )

        assert response.status_code == 204, response.text
