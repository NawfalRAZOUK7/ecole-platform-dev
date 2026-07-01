"""Integration tests for life-skills passport API endpoints."""

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
from tests.factories.erp import (
    AcademicYearFactory,
    ClassFactory,
    EnrollmentFactory,
    PeriodFactory,
)
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
        email=f"{label}-{suffix}@skills.ecole.ma",
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
        source="pytest-skills-api",
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
async def skill_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"SKL-{uuid.uuid4().hex[:6].upper()}",
            name="Skill API School",
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
            code="4A",
            name="4eme A",
        )
        admin = await _create_actor(
            session, school=school, role=RoleCode.ADM.value, label="admin"
        )
        director = await _create_actor(
            session, school=school, role=RoleCode.DIR.value, label="director"
        )
        teacher = await _create_actor(
            session, school=school, role=RoleCode.TCH.value, label="teacher"
        )
        parent = await _create_actor(
            session, school=school, role=RoleCode.PAR.value, label="parent"
        )
        student = await _create_actor(
            session, school=school, role=RoleCode.STD.value, label="student"
        )

        await ParentChildLinkFactory.create(
            session=session,
            school=school,
            parent=parent["user"],
            child=student["user"],
            linked_by=admin["user"].id,
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
            student=student["user"],
        )
        course = await CourseFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            class_obj=school_class,
            teacher=teacher["user"],
        )
        assignment = await AssignmentFactory.create(
            session=session,
            course=course,
            due_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        await SubmissionFactory.create(
            session=session,
            assignment=assignment,
            student=student["user"],
            status=SubmissionStatus.SUBMITTED.value,
            submitted_at=datetime.now(timezone.utc),
        )
        dimension_code = f"autonomy_{uuid.uuid4().hex[:6]}"
        dimension = await SkillDimensionFactory.create(
            session=session,
            code=dimension_code,
            name_fr="Autonomie",
            name_ar="الاستقلالية",
            name_en="Autonomy",
        )
        milestone = await SkillMilestoneFactory.create(
            session=session,
            dimension=dimension,
            code=f"{dimension_code}_level_1",
            level=1,
            rule_config={
                "metric": "submissions_on_time",
                "threshold": 1,
                "period_days": 30,
            },
        )
        await session.commit()

    return {
        "school": school,
        "academic_year": academic_year,
        "school_class": school_class,
        "admin": admin,
        "director": director,
        "teacher": teacher,
        "parent": parent,
        "student": student,
        "dimension": dimension,
        "milestone": milestone,
    }


class TestSkillPassportApi:
    @pytest.mark.asyncio
    async def test_admin_can_create_skill_dimension(self, client, skill_api_context):
        response = await client.post(
            "/skills/dimensions",
            headers=auth_header(skill_api_context["admin"]["token"]),
            json={
                "code": f"curiosity_{uuid.uuid4().hex[:6]}",
                "name_fr": "Curiosite",
                "name_ar": "الفضول",
                "name_en": "Curiosity",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["code"].startswith("curiosity_")

    @pytest.mark.asyncio
    async def test_admin_can_create_skill_milestone(self, client, skill_api_context):
        response = await client.post(
            "/skills/milestones",
            headers=auth_header(skill_api_context["admin"]["token"]),
            json={
                "dimension_id": str(skill_api_context["dimension"].id),
                "code": f"autonomy_level_{uuid.uuid4().hex[:4]}",
                "name_fr": "Niveau 2",
                "name_ar": "المستوى 2",
                "level": 2,
                "rule_config": {
                    "metric": "submissions_on_time",
                    "threshold": 1,
                    "period_days": 30,
                },
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["dimension_id"] == str(
            skill_api_context["dimension"].id
        )

    @pytest.mark.asyncio
    async def test_teacher_can_list_dimensions(self, client, skill_api_context):
        response = await client.get(
            "/skills/dimensions",
            headers=auth_header(skill_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_evaluate_student(self, client, skill_api_context):
        response = await client.post(
            f"/skills/evaluate/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["unlocked_milestones"] >= 1
        assert len(payload["progress_items"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_get_student_progress(self, client, skill_api_context):
        await client.post(
            f"/skills/evaluate/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        response = await client.get(
            f"/skills/progress/student/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_can_generate_passport(self, client, skill_api_context):
        response = await client.post(
            f"/skills/passport/{skill_api_context['student']['user'].id}/generate",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["overall_score"] >= 100.0

    @pytest.mark.asyncio
    async def test_parent_can_read_generated_passport(self, client, skill_api_context):
        await client.post(
            f"/skills/passport/{skill_api_context['student']['user'].id}/generate",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        response = await client.get(
            f"/skills/passport/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["parent"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["student_id"] == str(
            skill_api_context["student"]["user"].id
        )

    @pytest.mark.asyncio
    async def test_student_can_download_generated_passport_pdf(
        self, client, skill_api_context
    ):
        await client.post(
            f"/skills/passport/{skill_api_context['student']['user'].id}/generate",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        response = await client.get(
            f"/skills/passport/{skill_api_context['student']['user'].id}/download",
            headers=auth_header(skill_api_context["student"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-1.4")

    @pytest.mark.asyncio
    async def test_teacher_can_get_class_analytics(self, client, skill_api_context):
        await client.post(
            f"/skills/evaluate/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        response = await client.get(
            f"/skills/analytics/class/{skill_api_context['school_class'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["student_count"] == 1

    @pytest.mark.asyncio
    async def test_teacher_can_get_leaderboard(self, client, skill_api_context):
        await client.post(
            f"/skills/evaluate/{skill_api_context['student']['user'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        response = await client.get(
            f"/skills/leaderboard/{skill_api_context['school_class'].id}",
            headers=auth_header(skill_api_context["teacher"]["token"]),
            params={"academic_year_id": str(skill_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"][0]["alias"] == "Student 1"
