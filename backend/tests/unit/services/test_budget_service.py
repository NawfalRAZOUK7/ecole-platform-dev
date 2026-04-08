"""Unit tests for budget service workflows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.budget import (
    BudgetAllocationCreateRequest,
    BudgetRequestCreateRequest,
    BudgetRequestReviewRequest,
    BudgetTransactionCreateRequest,
    MicroBudgetCreateRequest,
    MicroBudgetUpdateRequest,
)
from app.services import budget_service as budget_module
from app.services.budget_service import BudgetService


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


def make_auth(role: str = "ADM") -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self) -> None:
        self.committed = True


def make_budget(auth: AuthContext, *, total: float = 10000.0, allocated: float = 0.0):
    now = datetime(2026, 4, 4, 10, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=uuid.uuid4(),
        total_amount=total,
        allocated_amount=allocated,
        remaining_amount=total - allocated,
        currency="MAD",
        status="active",
        created_by=auth.user_id,
        created_at=now,
        updated_at=now,
        allocations=[],
    )


def make_allocation(
    auth: AuthContext,
    *,
    budget,
    amount: float = 2500.0,
    spent: float = 0.0,
    teacher_id: uuid.UUID | None = None,
    class_id: uuid.UUID | None = None,
):
    now = datetime(2026, 4, 4, 10, 30, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        budget_id=budget.id,
        class_id=class_id or uuid.uuid4(),
        teacher_id=teacher_id or uuid.uuid4(),
        label="Budget Arts",
        amount=amount,
        spent=spent,
        remaining=amount - spent,
        currency="MAD",
        allocated_by=auth.user_id,
        allocated_at=now,
        status="active",
        created_at=now,
        updated_at=now,
        budget=budget,
        requests=[],
        transactions=[],
    )


def make_request(
    *,
    allocation,
    requester_id: uuid.UUID,
    amount: float = 350.0,
    status: str = "pending",
):
    now = datetime(2026, 4, 4, 11, 0, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        allocation_id=allocation.id,
        requester_id=requester_id,
        amount=amount,
        currency="MAD",
        description="Achat de peinture",
        justification="Projet d'arts plastiques",
        status=status,
        reviewed_by=None,
        reviewed_at=None,
        review_comment=None,
        created_at=now,
        updated_at=now,
        allocation=allocation,
    )


def make_transaction(
    auth: AuthContext,
    *,
    allocation,
    amount: float = 350.0,
    transaction_type: str = "expense",
):
    now = datetime(2026, 4, 4, 11, 30, tzinfo=UTC)
    return SimpleNamespace(
        id=uuid.uuid4(),
        allocation_id=allocation.id,
        request_id=None,
        amount=amount,
        transaction_type=transaction_type,
        description="Operation budgetaire",
        receipt_url=None,
        recorded_by=auth.user_id,
        recorded_at=now,
        created_at=now,
        updated_at=now,
        allocation=allocation,
    )


def setup_budget_service(monkeypatch: pytest.MonkeyPatch):
    service = BudgetService(AsyncMock())
    service.repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    audit = AsyncMock()
    dispatcher = SimpleNamespace(dispatch=AsyncMock())
    uow = FakeUnitOfWork()

    monkeypatch.setattr(budget_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(budget_module, "BudgetRepository", lambda _session: repo_in_uow)
    monkeypatch.setattr(budget_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(budget_module, "EventDispatcher", lambda _session: dispatcher)

    return service, repo_in_uow, audit, dispatcher, uow


class TestBudgetService:
    @pytest.mark.asyncio
    async def test_create_budget_requires_existing_academic_year(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_budget_service(monkeypatch)
        service.repo.get_academic_year.return_value = None

        with pytest.raises(NotFoundError, match="Academic year not found"):
            await service.create_budget(
                body=MicroBudgetCreateRequest(
                    academic_year_id=uuid.uuid4(),
                    total_amount=15000,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_budget_returns_serialized_budget(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        academic_year = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        budget = make_budget(auth, total=15000)
        service.repo.get_academic_year.return_value = academic_year
        repo_in_uow.create_budget.return_value = budget

        result = await service.create_budget(
            body=MicroBudgetCreateRequest(
                academic_year_id=academic_year.id,
                total_amount=15000,
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["total_amount"] == 15000.0
        audit.log_event.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_update_budget_rejects_total_below_allocated(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=10000, allocated=4000)
        service.repo.get_budget.return_value = budget

        with pytest.raises(ValidationError, match="lower than allocated_amount"):
            await service.update_budget(
                budget_id=budget.id,
                body=MicroBudgetUpdateRequest(total_amount=3000),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_update_budget_recomputes_remaining_amount(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, _, uow = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=10000, allocated=2500)
        service.repo.get_budget.return_value = budget
        repo_in_uow.get_budget.return_value = budget
        repo_in_uow.save_budget.return_value = budget

        result = await service.update_budget(
            budget_id=budget.id,
            body=MicroBudgetUpdateRequest(total_amount=12000),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["remaining_amount"] == 9500.0
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_allocation_requires_budget_capacity(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=5000, allocated=4500)
        service.repo.get_budget.return_value = budget

        with pytest.raises(ValidationError, match="enough unallocated funds"):
            await service.create_allocation(
                budget_id=budget.id,
                body=BudgetAllocationCreateRequest(
                    teacher_id=uuid.uuid4(),
                    label="Budget Science",
                    amount=1000,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_allocation_rejects_missing_target(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_budget_service(monkeypatch)
        budget = make_budget(auth)
        service.repo.get_budget.return_value = budget

        with pytest.raises(ValidationError, match="target a class or a teacher"):
            await service.create_allocation(
                budget_id=budget.id,
                body=BudgetAllocationCreateRequest(
                    label="Budget Sans Cible",
                    amount=500,
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_allocation_updates_budget_and_creates_seed_transaction(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=5000, allocated=500)
        school_class = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        teacher = SimpleNamespace(id=uuid.uuid4(), school_id=auth.school_id)
        allocation = make_allocation(
            auth,
            budget=budget,
            amount=1000,
            teacher_id=teacher.id,
            class_id=school_class.id,
        )
        transaction = make_transaction(
            auth, allocation=allocation, amount=1000, transaction_type="allocation"
        )
        service.repo.get_budget.return_value = budget
        service.repo.get_class.return_value = school_class
        service.repo.get_user.return_value = teacher
        repo_in_uow.get_budget.return_value = budget
        repo_in_uow.create_allocation.return_value = allocation
        repo_in_uow.create_transaction.return_value = transaction

        result = await service.create_allocation(
            budget_id=budget.id,
            body=BudgetAllocationCreateRequest(
                class_id=school_class.id,
                teacher_id=teacher.id,
                label="Budget Arts",
                amount=1000,
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["amount"] == 1000.0
        assert budget.allocated_amount == 1500.0
        assert budget.remaining_amount == 3500.0
        repo_in_uow.save_budget.assert_awaited_once()
        assert dispatcher.dispatch.await_count == 2
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_update_allocation_rejects_amount_below_spent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth()
        service, *_ = setup_budget_service(monkeypatch)
        budget = make_budget(auth)
        allocation = make_allocation(auth, budget=budget, amount=1500, spent=800)
        service.repo.get_allocation.return_value = allocation

        with pytest.raises(ValidationError, match="lower than spent"):
            await service.update_allocation(
                allocation_id=allocation.id,
                body=budget_module.BudgetAllocationUpdateRequest(amount=700),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_request_rejects_overspend(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("TCH")
        service, *_ = setup_budget_service(monkeypatch)
        allocation = make_allocation(
            auth, budget=make_budget(auth), amount=1000, spent=900
        )
        service.repo.get_allocation.return_value = allocation

        with pytest.raises(ValidationError, match="enough remaining funds"):
            await service.create_request(
                allocation_id=allocation.id,
                body=BudgetRequestCreateRequest(
                    amount=200,
                    description="Achat de papier",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_create_request_dispatches_event(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("TCH")
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        allocation = make_allocation(auth, budget=make_budget(auth))
        request = make_request(allocation=allocation, requester_id=auth.user_id)
        service.repo.get_allocation.return_value = allocation
        repo_in_uow.create_request.return_value = request

        result = await service.create_request(
            allocation_id=allocation.id,
            body=BudgetRequestCreateRequest(
                amount=350,
                description="Achat de peinture",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "pending"
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_update_request_requires_pending_status(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("TCH")
        service, *_ = setup_budget_service(monkeypatch)
        allocation = make_allocation(auth, budget=make_budget(auth))
        request = make_request(
            allocation=allocation,
            requester_id=auth.user_id,
            status="approved",
        )
        service.repo.get_request.return_value = request

        with pytest.raises(ConflictError, match="pending budget requests"):
            await service.update_request(
                request_id=request.id,
                body=budget_module.BudgetRequestUpdateRequest(description="Revision"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_approve_request_rejects_non_pending(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        auth = make_auth("DIR")
        service, *_ = setup_budget_service(monkeypatch)
        allocation = make_allocation(auth, budget=make_budget(auth))
        request = make_request(
            allocation=allocation,
            requester_id=uuid.uuid4(),
            status="approved",
        )
        service.repo.get_request.return_value = request

        with pytest.raises(ConflictError, match="already been reviewed"):
            await service.approve_request(
                request_id=request.id,
                body=BudgetRequestReviewRequest(review_comment="ok"),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_approve_request_deducts_allocation_and_creates_transaction(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        approver = make_auth("DIR")
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        budget = make_budget(approver)
        allocation = make_allocation(approver, budget=budget, amount=800, spent=500)
        request = make_request(
            allocation=allocation, requester_id=uuid.uuid4(), amount=300
        )
        transaction = make_transaction(approver, allocation=allocation, amount=300)
        service.repo.get_request.return_value = request
        repo_in_uow.get_request.return_value = request
        repo_in_uow.save_request.return_value = request
        repo_in_uow.save_allocation.return_value = allocation
        repo_in_uow.create_transaction.return_value = transaction

        result = await service.approve_request(
            request_id=request.id,
            body=BudgetRequestReviewRequest(review_comment="Approuve"),
            auth=approver,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "approved"
        assert allocation.spent == 800.0
        assert allocation.remaining == 0
        assert allocation.status == "exhausted"
        repo_in_uow.save_request.assert_awaited_once()
        repo_in_uow.save_allocation.assert_awaited_once()
        assert dispatcher.dispatch.await_count == 2
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_reject_request_updates_review_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        approver = make_auth("DIR")
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        request = make_request(
            allocation=make_allocation(approver, budget=make_budget(approver)),
            requester_id=uuid.uuid4(),
        )
        service.repo.get_request.return_value = request
        repo_in_uow.get_request.return_value = request
        repo_in_uow.save_request.return_value = request

        result = await service.reject_request(
            request_id=request.id,
            body=BudgetRequestReviewRequest(review_comment="Refus"),
            auth=approver,
            ip_address="127.0.0.1",
        )

        assert result["status"] == "rejected"
        assert request.reviewed_by == approver.user_id
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_record_transaction_rejects_expense_overspend(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("DIR")
        service, *_ = setup_budget_service(monkeypatch)
        allocation = make_allocation(
            auth, budget=make_budget(auth), amount=1000, spent=950
        )
        service.repo.get_allocation.return_value = allocation

        with pytest.raises(ValidationError, match="enough remaining funds"):
            await service.record_transaction(
                allocation_id=allocation.id,
                body=BudgetTransactionCreateRequest(
                    amount=100,
                    transaction_type="expense",
                    description="Achat urgent",
                ),
                auth=auth,
            )

    @pytest.mark.asyncio
    async def test_record_transaction_adjustment_tops_up_budget_allocation(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("DIR")
        service, repo_in_uow, audit, dispatcher, uow = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=5000, allocated=1000)
        allocation = make_allocation(auth, budget=budget, amount=1000, spent=200)
        transaction = make_transaction(
            auth, allocation=allocation, amount=500, transaction_type="adjustment"
        )
        service.repo.get_allocation.return_value = allocation
        repo_in_uow.get_allocation.return_value = allocation
        repo_in_uow.create_transaction.return_value = transaction

        result = await service.record_transaction(
            allocation_id=allocation.id,
            body=BudgetTransactionCreateRequest(
                amount=500,
                transaction_type="adjustment",
                description="Top-up budget",
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["transaction_type"] == "adjustment"
        assert allocation.amount == 1500.0
        assert allocation.remaining == 1300.0
        assert budget.allocated_amount == 1500.0
        assert budget.remaining_amount == 3500.0
        repo_in_uow.save_budget.assert_awaited_once()
        repo_in_uow.save_allocation.assert_awaited_once()
        dispatcher.dispatch.assert_awaited_once()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_transactions_returns_serialized_rows(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("DIR")
        service, *_ = setup_budget_service(monkeypatch)
        allocation = make_allocation(auth, budget=make_budget(auth))
        service.repo.list_transactions.return_value = [
            make_transaction(auth, allocation=allocation, transaction_type="expense"),
        ]

        items = await service.list_transactions(
            auth=auth,
            allocation_id=allocation.id,
            request_id=None,
            transaction_type=None,
        )

        assert items[0]["allocation_id"] == str(allocation.id)

    @pytest.mark.asyncio
    async def test_budget_analytics_aggregates_budget_metrics(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        auth = make_auth("DIR")
        service, *_ = setup_budget_service(monkeypatch)
        budget = make_budget(auth, total=10000, allocated=4000)
        allocation = make_allocation(auth, budget=budget, amount=4000, spent=2500)
        pending_request = make_request(
            allocation=allocation,
            requester_id=uuid.uuid4(),
            amount=500,
            status="pending",
        )
        approved_request = make_request(
            allocation=allocation,
            requester_id=uuid.uuid4(),
            amount=300,
            status="approved",
        )
        transaction = make_transaction(auth, allocation=allocation, amount=2500)
        service.repo.list_budgets.return_value = [budget]
        service.repo.list_allocations.return_value = [allocation]
        service.repo.list_requests.return_value = [pending_request, approved_request]
        service.repo.list_transactions.return_value = [transaction]

        result = await service.get_budget_analytics(auth=auth, academic_year_id=None)

        assert result == {
            "school_id": str(auth.school_id),
            "academic_year_id": None,
            "budget_count": 1,
            "allocation_count": 1,
            "request_count": 2,
            "transaction_count": 1,
            "total_budget_amount": 10000.0,
            "total_allocated_amount": 4000.0,
            "total_remaining_unallocated": 6000.0,
            "total_spent_amount": 2500.0,
            "total_allocation_remaining": 1500.0,
            "pending_request_amount": 500.0,
            "approved_request_amount": 300.0,
            "utilization_rate": 62.5,
        }
