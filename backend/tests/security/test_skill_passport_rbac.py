"""RBAC tests for life-skills passport endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.iam import RoleCode
from app.models.lms import SubmissionStatus
from tests.factories.erp import AcademicYearFactory, ClassFactory, EnrollmentFactory, PeriodFactory
from tests.factories.iam import (
    MembershipFactory,
    ParentChildLinkFactory,
    SessionFactory,
    UserFactory,
)
from tests.factories.lms import AssignmentFactory, CourseFactory, SubmissionFactory
from tests.factories.school import SchoolFactory
from tests.factories.skill_passport import SkillDimensionFactory, SkillMilestoneFactory


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
        email=f"{label}-{suffix}@skills-rbac.ma",
        full_name=f"{label.title()} Skills {suffix}",
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
        source="pytest-skills-rbac",
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
async def skill_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"SRB-{uuid.uuid4().hex[:6].upper()}",
            name="Skills RBAC School",
            city="Casablanca",
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
            (RoleCode.PAR.value, "parent"),
            (RoleCode.STD.value, "student"),
            (RoleCode.SUP.value, "superadmin"),
        ):
            actors[label] = await _create_actor(session, school=school, role=role, label=label)

        await ParentChildLinkFactory.create(
            session=session,
            school=school,
            parent=actors["parent"]["user"],
            child=actors["student"]["user"],
            linked_by=actors["admin"]["user"].id,
        )
        period = await PeriodFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
        )
        await EnrollmentFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            class_obj=school_class,
            period=period,
            student=actors["student"]["user"],
        )
        course = await CourseFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            class_obj=school_class,
            teacher=actors["teacher"]["user"],
        )
        assignment = await AssignmentFactory.create(
            session=session,
            course=course,
            due_at=datetime.now(timezone.utc) + timedelta(days=2),
        )
        await SubmissionFactory.create(
            session=session,
            assignment=assignment,
            student=actors["student"]["user"],
            status=SubmissionStatus.SUBMITTED.value,
            submitted_at=datetime.now(timezone.utc),
        )
        dimension_code = f"regularity_{uuid.uuid4().hex[:6]}"
        dimension = await SkillDimensionFactory.create(
            session=session,
            code=dimension_code,
        )
        await SkillMilestoneFactory.create(
            session=session,
            dimension=dimension,
            code=f"{dimension_code}_level_1",
            rule_config={"metric": "submissions_on_time", "threshold": 1, "period_days": 30},
        )
        await session.commit()

    return {
        **actors,
        "academic_year": academic_year,
        "school_class": school_class,
        "student_user": actors["student"]["user"],
        "dimension": dimension,
    }


@pytest.mark.asyncio
async def test_teacher_cannot_create_dimension(client, skill_rbac_context):
    response = await client.post(
        "/skills/dimensions",
        headers=auth_header(skill_rbac_context["teacher"]["token"]),
        json={
            "code": "collaboration",
            "name_fr": "Collaboration",
            "name_ar": "التعاون",
            "name_en": "Collaboration",
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_cannot_create_milestone(client, skill_rbac_context):
    response = await client.post(
        "/skills/milestones",
        headers=auth_header(skill_rbac_context["parent"]["token"]),
        json={
            "dimension_id": str(skill_rbac_context["dimension"].id),
            "code": "regularity_level_2",
            "name_fr": "Niveau 2",
            "name_ar": "المستوى 2",
            "level": 2,
            "rule_config": {"metric": "submissions_on_time", "threshold": 1, "period_days": 30},
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_cannot_evaluate_student(client, skill_rbac_context):
    response = await client.post(
        f"/skills/evaluate/{skill_rbac_context['student_user'].id}",
        headers=auth_header(skill_rbac_context["parent"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_can_evaluate_student(client, skill_rbac_context):
    response = await client.post(
        f"/skills/evaluate/{skill_rbac_context['student_user'].id}",
        headers=auth_header(skill_rbac_context["teacher"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_director_can_generate_passport(client, skill_rbac_context):
    response = await client.post(
        f"/skills/passport/{skill_rbac_context['student_user'].id}/generate",
        headers=auth_header(skill_rbac_context["director"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_parent_can_read_generated_passport(client, skill_rbac_context):
    await client.post(
        f"/skills/passport/{skill_rbac_context['student_user'].id}/generate",
        headers=auth_header(skill_rbac_context["teacher"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    response = await client.get(
        f"/skills/passport/{skill_rbac_context['student_user'].id}",
        headers=auth_header(skill_rbac_context["parent"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_student_cannot_read_school_analytics(client, skill_rbac_context):
    response = await client.get(
        "/skills/analytics/school",
        headers=auth_header(skill_rbac_context["student"]["token"]),
        params={"academic_year_id": str(skill_rbac_context["academic_year"].id)},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_skill_routes_require_token(client, skill_rbac_context):
    response = await client.get("/skills/dimensions")

    assert response.status_code == 401, response.text
