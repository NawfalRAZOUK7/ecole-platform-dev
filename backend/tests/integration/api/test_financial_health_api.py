"""Integration tests for financial health API endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.database import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.billing import InvoiceStatus, PaymentAttemptStatus
from app.models.iam import RoleCode
from tests.factories.billing import InvoiceFactory, PaymentAttemptFactory
from tests.factories.budget import (
    BudgetAllocationFactory,
    BudgetRequestFactory,
    BudgetTransactionFactory,
    MicroBudgetFactory,
)
from tests.factories.erp import (
    AcademicYearFactory,
    ClassFactory,
    EnrollmentFactory,
    PeriodFactory,
)
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
        email=f"{label}-{suffix}@finhealth-api.ma",
        full_name=f"{label.title()} Financial Health {suffix}",
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
        source="pytest-finhealth-api",
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
async def finhealth_api_context(session_factory):
    async with session_factory() as session:
        school = await SchoolFactory.create(
            session=session,
            code=f"FHA-{uuid.uuid4().hex[:6].upper()}",
            name="Financial Health API School",
            city="Rabat",
        )
        admin = await _create_actor(
            session, school=school, role=RoleCode.ADM.value, label="admin"
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

        previous_year = await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2024-2025",
            date_start=date(2024, 9, 1),
            date_end=date(2025, 7, 15),
        )
        current_year = await AcademicYearFactory.create(
            session=session,
            school=school,
            label="2025-2026",
            date_start=date(2025, 9, 1),
            date_end=date(2026, 7, 15),
        )
        previous_period = await PeriodFactory.create(
            session=session,
            school=school,
            academic_year=previous_year,
            label="Trimester 1",
            date_start=date(2024, 9, 1),
            date_end=date(2024, 12, 31),
        )
        previous_class = await ClassFactory.create(
            session=session,
            school=school,
            academic_year=previous_year,
            code="PREV-01",
            name="Classe Precedente",
        )
        current_period = await PeriodFactory.create(
            session=session,
            school=school,
            academic_year=current_year,
            label="Trimester 1",
            date_start=date(2025, 9, 1),
            date_end=date(2025, 12, 31),
        )
        current_class = await ClassFactory.create(
            session=session,
            school=school,
            academic_year=current_year,
            code="CURR-01",
            name="Classe Courante",
        )

        continuing_students = [
            await UserFactory.create(
                session=session,
                school=school,
                email=f"continuing-{index}-{uuid.uuid4().hex[:6]}@students.ma",
            )
            for index in range(2)
        ]
        withdrawn_student = await UserFactory.create(
            session=session,
            school=school,
            email=f"withdrawn-{uuid.uuid4().hex[:6]}@students.ma",
        )
        new_students = [
            await UserFactory.create(
                session=session,
                school=school,
                email=f"new-{index}-{uuid.uuid4().hex[:6]}@students.ma",
            )
            for index in range(2)
        ]

        for student in continuing_students + [withdrawn_student]:
            await EnrollmentFactory.create(
                session=session,
                school=school,
                academic_year=previous_year,
                class_obj=previous_class,
                period=previous_period,
                student=student,
            )
        for student in continuing_students + new_students:
            await EnrollmentFactory.create(
                session=session,
                school=school,
                academic_year=current_year,
                class_obj=current_class,
                period=current_period,
                student=student,
            )

        parent_user = parent["user"]
        paid_invoice = await InvoiceFactory.create(
            session=session,
            school=school,
            parent=parent_user,
            period_id=current_period.id,
            status=InvoiceStatus.PAID.value,
            total_amount=15000.0,
            issued_date=date.today() - timedelta(days=25),
            due_date=date.today().replace(day=1),
        )
        await PaymentAttemptFactory.create(
            session=session,
            invoice=paid_invoice,
            school_id=school.id,
            parent_id=parent_user.id,
            status=PaymentAttemptStatus.PAID.value,
            finalized_at=datetime.now(UTC) - timedelta(days=2),
        )
        await InvoiceFactory.create(
            session=session,
            school=school,
            parent=parent_user,
            period_id=current_period.id,
            status=InvoiceStatus.PENDING.value,
            total_amount=5000.0,
            issued_date=date.today() - timedelta(days=20),
            due_date=date.today() - timedelta(days=5),
        )
        await InvoiceFactory.create(
            session=session,
            school=school,
            parent=parent_user,
            period_id=current_period.id,
            status=InvoiceStatus.PENDING.value,
            total_amount=2000.0,
            issued_date=date.today(),
            due_date=date.today() + timedelta(days=20),
        )

        budget = await MicroBudgetFactory.create(
            session=session,
            school=school,
            academic_year=current_year,
            creator=admin["user"],
            total_amount=20000.0,
            allocated_amount=12000.0,
            remaining_amount=8000.0,
        )
        allocation = await BudgetAllocationFactory.create(
            session=session,
            budget=budget,
            school_class=current_class,
            teacher=teacher["user"],
            allocator=admin["user"],
            amount=12000.0,
            remaining=0.0,
            spent=12000.0,
        )
        budget_request = await BudgetRequestFactory.create(
            session=session,
            allocation=allocation,
            requester=teacher["user"],
            reviewer=admin["user"],
        )
        await BudgetTransactionFactory.create(
            session=session,
            allocation=allocation,
            request=budget_request,
            recorder=admin["user"],
            amount=12000.0,
            transaction_type="expense",
            recorded_at=datetime.now(UTC) - timedelta(days=1),
        )
        await session.commit()

    return {
        "school": school,
        "admin": admin,
        "teacher": teacher,
        "parent": parent,
        "previous_year": previous_year,
        "current_year": current_year,
    }


class TestFinancialHealthApi:
    @pytest.mark.asyncio
    async def test_admin_can_compute_retention(self, client, finhealth_api_context):
        response = await client.post(
            "/financial-health/retention/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={
                "academic_year_from": "2024-2025",
                "academic_year_to": "2025-2026",
            },
        )

        assert response.status_code == 202, response.text
        assert response.json()["data"]["retained"] == 2

    @pytest.mark.asyncio
    async def test_admin_can_list_retention_metrics(
        self, client, finhealth_api_context
    ):
        await client.post(
            "/financial-health/retention/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={
                "academic_year_from": "2024-2025",
                "academic_year_to": "2025-2026",
            },
        )

        response = await client.get(
            "/financial-health/retention",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) == 1

    @pytest.mark.asyncio
    async def test_admin_can_compute_cashflow(self, client, finhealth_api_context):
        response = await client.post(
            "/financial-health/cashflow/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={"months_ahead": 3},
        )

        assert response.status_code == 202, response.text
        assert len(response.json()["data"]) == 3

    @pytest.mark.asyncio
    async def test_admin_can_list_cashflow(self, client, finhealth_api_context):
        await client.post(
            "/financial-health/cashflow/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={"months_ahead": 2},
        )

        response = await client.get(
            "/financial-health/cashflow",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert len(response.json()["data"]) >= 2

    @pytest.mark.asyncio
    async def test_admin_can_compute_cost_per_student(
        self, client, finhealth_api_context
    ):
        response = await client.post(
            "/financial-health/cost-per-student/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={"academic_year_id": str(finhealth_api_context["current_year"].id)},
        )

        assert response.status_code == 202, response.text
        assert response.json()["data"]["total_students"] == 4

    @pytest.mark.asyncio
    async def test_admin_can_get_cost_per_student_analysis(
        self, client, finhealth_api_context
    ):
        response = await client.get(
            "/financial-health/cost-per-student",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            params={"academic_year_id": str(finhealth_api_context["current_year"].id)},
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["margin_per_student"] >= 0

    @pytest.mark.asyncio
    async def test_admin_can_compute_snapshot(self, client, finhealth_api_context):
        response = await client.post(
            "/financial-health/snapshot/compute",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            json={"snapshot_date": date.today().isoformat()},
        )

        assert response.status_code == 202, response.text
        assert response.json()["data"]["overdue_count"] == 1

    @pytest.mark.asyncio
    async def test_admin_can_get_snapshot(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/snapshot",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.json()["data"]["total_collected"] >= 15000.0

    @pytest.mark.asyncio
    async def test_admin_can_get_dashboard(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/dashboard",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert "snapshot" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_admin_can_get_trends(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/trends",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
            params={"months": 6},
        )

        assert response.status_code == 200, response.text
        assert "retention_metrics" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_admin_can_export_csv(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/export/csv",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("text/csv")
        assert b"collection_rate" in response.content

    @pytest.mark.asyncio
    async def test_admin_can_export_pdf(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/export/pdf",
            headers=auth_header(finhealth_api_context["admin"]["token"]),
        )

        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("application/pdf")
        assert b"Financial Health Dashboard" in response.content

    @pytest.mark.asyncio
    async def test_teacher_cannot_read_retention(self, client, finhealth_api_context):
        response = await client.get(
            "/financial-health/retention",
            headers=auth_header(finhealth_api_context["teacher"]["token"]),
        )

        assert response.status_code == 403, response.text
