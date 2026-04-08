"""Integration tests for budget API endpoints."""

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
    BudgetTransactionFactory,
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
        email=f"{label}-{suffix}@budget.ecole.ma",
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
        source="pytest-budget-api",
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
async def budget_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"BUD-{uuid.uuid4().hex[:6].upper()}",
            name="Budget API School",
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
            code="3A",
            name="3eme A",
        )
        admin = await _create_actor(
            session,
            school=school,
            role=RoleCode.ADM.value,
            label="admin",
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

        budget = await MicroBudgetFactory.create(
            session=session,
            school=school,
            academic_year=academic_year,
            creator=admin["user"],
            total_amount=10000,
            allocated_amount=2500,
            remaining_amount=7500,
        )
        allocation = await BudgetAllocationFactory.create(
            session=session,
            budget=budget,
            school_class=school_class,
            teacher=teacher["user"],
            allocator=director["user"],
            amount=2500,
            spent=500,
            remaining=2000,
        )
        request = await BudgetRequestFactory.create(
            session=session,
            allocation=allocation,
            requester=teacher["user"],
            amount=300,
        )
        transaction = await BudgetTransactionFactory.create(
            session=session,
            allocation=allocation,
            request=request,
            recorder=director["user"],
            amount=500,
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
        "budget": budget,
        "allocation": allocation,
        "request": request,
        "transaction": transaction,
    }


class TestBudgetApi:
    @pytest.mark.asyncio
    async def test_admin_can_create_budget(self, client, budget_api_context):
        response = await client.post(
            "/budgets",
            headers=auth_header(budget_api_context["admin"]["token"]),
            json={
                "academic_year_id": str(budget_api_context["academic_year"].id),
                "total_amount": 12000,
            },
        )

        assert response.status_code == 201, response.text
        payload = response.json()["data"]
        assert payload["total_amount"] == 12000.0

    @pytest.mark.asyncio
    async def test_teacher_can_list_budgets(self, client, budget_api_context):
        response = await client.get(
            "/budgets",
            headers=auth_header(budget_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_director_can_get_budget_detail(self, client, budget_api_context):
        response = await client.get(
            f"/budgets/{budget_api_context['budget'].id}",
            headers=auth_header(budget_api_context["director"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["id"] == str(budget_api_context["budget"].id)

    @pytest.mark.asyncio
    async def test_director_can_create_allocation(self, client, budget_api_context):
        response = await client.post(
            f"/budgets/{budget_api_context['budget'].id}/allocations",
            headers=auth_header(budget_api_context["director"]["token"]),
            json={
                "class_id": str(budget_api_context["school_class"].id),
                "teacher_id": str(budget_api_context["teacher"]["user"].id),
                "label": "Budget Sciences",
                "amount": 1000,
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["label"] == "Budget Sciences"

    @pytest.mark.asyncio
    async def test_teacher_can_list_allocations(self, client, budget_api_context):
        response = await client.get(
            f"/budgets/{budget_api_context['budget'].id}/allocations",
            headers=auth_header(budget_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_teacher_can_get_allocation(self, client, budget_api_context):
        response = await client.get(
            f"/budgets/allocations/{budget_api_context['allocation'].id}",
            headers=auth_header(budget_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["id"] == str(budget_api_context["allocation"].id)

    @pytest.mark.asyncio
    async def test_teacher_can_create_budget_request(self, client, budget_api_context):
        response = await client.post(
            f"/budgets/allocations/{budget_api_context['allocation'].id}/requests",
            headers=auth_header(budget_api_context["teacher"]["token"]),
            json={
                "amount": 250,
                "description": "Achat de cahiers",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_teacher_can_list_budget_requests(self, client, budget_api_context):
        response = await client.get(
            f"/budgets/allocations/{budget_api_context['allocation'].id}/requests",
            headers=auth_header(budget_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_director_can_approve_budget_request(
        self, client, budget_api_context
    ):
        response = await client.post(
            f"/budgets/requests/{budget_api_context['request'].id}/approve",
            headers=auth_header(budget_api_context["director"]["token"]),
            json={"review_comment": "Valide"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_director_can_reject_budget_request(self, client, budget_api_context):
        create_response = await client.post(
            f"/budgets/allocations/{budget_api_context['allocation'].id}/requests",
            headers=auth_header(budget_api_context["teacher"]["token"]),
            json={
                "amount": 150,
                "description": "Achat de feutres",
            },
        )
        request_id = create_response.json()["data"]["id"]

        response = await client.post(
            f"/budgets/requests/{request_id}/reject",
            headers=auth_header(budget_api_context["director"]["token"]),
            json={"review_comment": "Hors perimetre"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_director_can_get_budget_request_detail(
        self, client, budget_api_context
    ):
        response = await client.get(
            f"/budgets/requests/{budget_api_context['request'].id}",
            headers=auth_header(budget_api_context["director"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["id"] == str(budget_api_context["request"].id)

    @pytest.mark.asyncio
    async def test_director_can_record_budget_transaction(
        self, client, budget_api_context
    ):
        response = await client.post(
            f"/budgets/allocations/{budget_api_context['allocation'].id}/transactions",
            headers=auth_header(budget_api_context["director"]["token"]),
            json={
                "amount": 100,
                "transaction_type": "expense",
                "description": "Achat de cartons",
            },
        )

        assert response.status_code == 201, response.text
        assert response.json()["data"]["transaction_type"] == "expense"

    @pytest.mark.asyncio
    async def test_teacher_can_list_budget_transactions(
        self, client, budget_api_context
    ):
        response = await client.get(
            f"/budgets/allocations/{budget_api_context['allocation'].id}/transactions",
            headers=auth_header(budget_api_context["teacher"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_director_can_get_budget_analytics(self, client, budget_api_context):
        response = await client.get(
            "/budgets/analytics",
            headers=auth_header(budget_api_context["director"]["token"]),
            params={"academic_year_id": str(budget_api_context["academic_year"].id)},
        )

        assert response.status_code == 200, response.text
        payload = response.json()["data"]
        assert payload["budget_count"] == 1
        assert payload["allocation_count"] == 1
