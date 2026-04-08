"""RBAC tests for budget endpoints."""

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
from tests.factories.budget import (
    BudgetAllocationFactory,
    BudgetRequestFactory,
    MicroBudgetFactory,
)
from tests.factories.erp import AcademicYearFactory, ClassFactory
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
        email=f"{label}-{suffix}@budget-rbac.ma",
        full_name=f"{label.title()} Budget {suffix}",
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
        source="pytest-budget-rbac",
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
async def budget_rbac_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"RBACB-{uuid.uuid4().hex[:6].upper()}",
            name="Budget RBAC School",
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
            (RoleCode.STD.value, "student"),
            (RoleCode.PAR.value, "parent"),
            (RoleCode.SUP.value, "superadmin"),
        ):
            actors[label] = await _create_actor(
                session,
                school=school,
                role=role,
                label=label,
            )

        budget = await MicroBudgetFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            creator=actors["admin"]["user"],
            total_amount=5000,
            allocated_amount=2000,
            remaining_amount=3000,
        )
        allocation = await BudgetAllocationFactory.create(
            session=session,
            budget=budget,
            school_class=school_class,
            teacher=actors["teacher"]["user"],
            allocator=actors["director"]["user"],
            amount=2000,
            spent=200,
            remaining=1800,
        )
        request = await BudgetRequestFactory.create(
            session=session,
            allocation=allocation,
            requester=actors["teacher"]["user"],
            amount=250,
        )
        await session.commit()

    return {
        **actors,
        "academic_year": academic_year,
        "budget": budget,
        "allocation": allocation,
        "request": request,
    }


@pytest.mark.asyncio
async def test_teacher_can_create_budget_request(client, budget_rbac_context):
    response = await client.post(
        f"/budgets/allocations/{budget_rbac_context['allocation'].id}/requests",
        headers=auth_header(budget_rbac_context["teacher"]["token"]),
        json={"amount": 100, "description": "Achat de feutres"},
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_create_budget(client, budget_rbac_context):
    response = await client.post(
        "/budgets",
        headers=auth_header(budget_rbac_context["teacher"]["token"]),
        json={
            "academic_year_id": str(budget_rbac_context["academic_year"].id),
            "total_amount": 6000,
        },
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_cannot_approve_budget_request(client, budget_rbac_context):
    response = await client.post(
        f"/budgets/requests/{budget_rbac_context['request'].id}/approve",
        headers=auth_header(budget_rbac_context["teacher"]["token"]),
        json={"review_comment": "Tentative"},
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_director_can_approve_budget_request(client, budget_rbac_context):
    response = await client.post(
        f"/budgets/requests/{budget_rbac_context['request'].id}/approve",
        headers=auth_header(budget_rbac_context["director"]["token"]),
        json={"review_comment": "Valide"},
    )

    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_student_cannot_list_budgets(client, budget_rbac_context):
    response = await client.get(
        "/budgets",
        headers=auth_header(budget_rbac_context["student"]["token"]),
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_parent_cannot_list_budgets(client, budget_rbac_context):
    response = await client.get(
        "/budgets",
        headers=auth_header(budget_rbac_context["parent"]["token"]),
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_superadmin_can_create_budget(client, budget_rbac_context):
    response = await client.post(
        "/budgets",
        headers=auth_header(budget_rbac_context["superadmin"]["token"]),
        json={
            "academic_year_id": str(budget_rbac_context["academic_year"].id),
            "total_amount": 9000,
        },
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_budget_routes_require_token(client, budget_rbac_context):
    response = await client.get("/budgets")

    assert response.status_code == 401, response.text


@pytest.mark.asyncio
async def test_teacher_can_list_budget_transactions(client, budget_rbac_context):
    response = await client.get(
        f"/budgets/allocations/{budget_rbac_context['allocation'].id}/transactions",
        headers=auth_header(budget_rbac_context["teacher"]["token"]),
    )

    assert response.status_code == 200, response.text
