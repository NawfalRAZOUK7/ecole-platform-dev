"""RBAC tests for MEN compliance endpoints."""

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
        email=f"{label}-{suffix}@compliance-rbac.ma",
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
        source="pytest-compliance-rbac",
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
async def compliance_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"CRB-{uuid.uuid4().hex[:6].upper()}",
            name="Compliance RBAC School",
            city="Rabat",
        )
        academic_year = await AcademicYearFactory.create(session=session, school=school)
        school_class = await ClassFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
        )
        actors = {}
        for role, label in (
            (RoleCode.ADM.value, "admin"),
            (RoleCode.DIR.value, "director"),
            (RoleCode.TCH.value, "teacher"),
            (RoleCode.STD.value, "student"),
            (RoleCode.SUP.value, "superadmin"),
            (RoleCode.SYS.value, "system"),
        ):
            actors[label] = await _create_actor(session, school=school, role=role, label=label)

        course = await CourseFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            class_obj=school_class,
            teacher=actors["teacher"]["user"],
        )
        curriculum = await MenCurriculumFactory.create(
            session=session,
            subject=f"rbac_subject_{uuid.uuid4().hex[:6]}",
        )
        objective = await MenObjectiveFactory.create(
            session=session,
            curriculum=curriculum,
            code=f"RBAC-{uuid.uuid4().hex[:6].upper()}-01",
        )
        await session.commit()

    return {
        **actors,
        "academic_year": academic_year,
        "course": course,
        "curriculum": curriculum,
        "objective": objective,
    }


@pytest.mark.asyncio
async def test_teacher_cannot_create_curriculum(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/curricula",
        headers=auth_header(compliance_rbac_context["teacher"]["token"]),
        json={
            "level": "college",
            "grade": "3eme",
            "subject": f"history_{uuid.uuid4().hex[:6]}",
            "academic_year": "2025-2026",
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_student_cannot_create_mapping(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/mappings",
        headers=auth_header(compliance_rbac_context["student"]["token"]),
        json={
            "objective_id": str(compliance_rbac_context["objective"].id),
            "course_id": str(compliance_rbac_context["course"].id),
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_can_create_mapping(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/mappings",
        headers=auth_header(compliance_rbac_context["teacher"]["token"]),
        json={
            "objective_id": str(compliance_rbac_context["objective"].id),
            "course_id": str(compliance_rbac_context["course"].id),
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_generate_report(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/reports/generate",
        headers=auth_header(compliance_rbac_context["teacher"]["token"]),
        json={
            "curriculum_id": str(compliance_rbac_context["curriculum"].id),
            "academic_year_id": str(compliance_rbac_context["academic_year"].id),
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_director_can_read_dashboard(client, compliance_rbac_context):
    response = await client.get(
        "/compliance/dashboard",
        headers=auth_header(compliance_rbac_context["director"]["token"]),
        params={"academic_year_id": str(compliance_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_admin_can_generate_report(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/reports/generate",
        headers=auth_header(compliance_rbac_context["admin"]["token"]),
        json={
            "curriculum_id": str(compliance_rbac_context["curriculum"].id),
            "academic_year_id": str(compliance_rbac_context["academic_year"].id),
        },
    )

    assert response.status_code == 202, response.text


@pytest.mark.asyncio
async def test_superadmin_can_create_curriculum(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/curricula",
        headers=auth_header(compliance_rbac_context["superadmin"]["token"]),
        json={
            "level": "college",
            "grade": "3eme",
            "subject": f"physics_{uuid.uuid4().hex[:6]}",
            "academic_year": "2025-2026",
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_system_can_create_curriculum(client, compliance_rbac_context):
    response = await client.post(
        "/compliance/curricula",
        headers=auth_header(compliance_rbac_context["system"]["token"]),
        json={
            "level": "college",
            "grade": "3eme",
            "subject": f"arabic_{uuid.uuid4().hex[:6]}",
            "academic_year": "2025-2026",
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_compliance_routes_require_token(client, compliance_rbac_context):
    response = await client.get("/compliance/curricula")

    assert response.status_code == 401, response.text
