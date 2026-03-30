"""Unit tests for billing and payment plan services."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.dependencies import AuthContext
from app.core.exceptions import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.schemas.billing import InvoiceGenerateRequest
from app.schemas.billing_enhancements import PaymentPlanCreateRequest
from app.services import billing as billing_module
from app.services import payment_plan as payment_plan_module
from app.services.billing import BillingService
from app.services.payment_plan import PaymentPlanService


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


def make_fee_structure(
    auth: AuthContext,
    *,
    amount: float = 500.0,
    currency: str = "MAD",
    status: str = "ACTIVE",
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=auth.school_id,
        academic_year_id=uuid.uuid4(),
        name="Scolarite 2026",
        amount=amount,
        currency=currency,
        frequency="MONTHLY",
        due_day=5,
        applies_to_level="6eme",
        status=status,
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
    )


def make_assignment(student_id: uuid.UUID, *, discount_percent: float | None = None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        fee_structure_id=uuid.uuid4(),
        student_id=student_id,
        school_id=uuid.uuid4(),
        discount_percent=discount_percent,
        discount_reason="Scholarship" if discount_percent else None,
        status="ACTIVE",
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
    )


def make_parent_link(child_user_id: uuid.UUID, parent_user_id: uuid.UUID):
    return SimpleNamespace(
        parent_user_id=parent_user_id,
        child_user_id=child_user_id,
    )


def make_sibling_policy(
    *,
    enabled: bool = True,
    second_child_percent: float = 10.0,
    third_child_percent: float = 20.0,
    fourth_plus_percent: float = 30.0,
    apply_to_oldest_first: bool = True,
):
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        enabled=enabled,
        second_child_percent=second_child_percent,
        third_child_percent=third_child_percent,
        fourth_plus_percent=fourth_plus_percent,
        apply_to_oldest_first=apply_to_oldest_first,
        created_at=now,
        updated_at=now,
    )


def make_invoice_item(description: str, amount: float):
    return SimpleNamespace(
        id=uuid.uuid4(),
        description=description,
        amount=amount,
        unit_price=amount,
        quantity=1,
    )


def make_invoice(
    school_id: uuid.UUID,
    parent_id: uuid.UUID,
    *,
    total_amount: float = 500.0,
    currency: str = "MAD",
    due_date: date = date(2026, 3, 20),
    status: str = "pending",
    items: list | None = None,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=school_id,
        parent_id=parent_id,
        period_id=uuid.uuid4(),
        status=status,
        total_amount=total_amount,
        currency=currency,
        issued_date=date(2026, 3, 1),
        due_date=due_date,
        items=list(items or []),
        fee_structure_id=uuid.uuid4(),
    )


def make_late_fee_policy(
    *,
    enabled: bool = True,
    fee_type: str = "fixed",
    amount: float = 5.0,
    frequency: str = "daily",
    grace_days: int = 0,
    max_fee: float | None = None,
):
    now = datetime(2026, 3, 1, tzinfo=timezone.utc)
    return SimpleNamespace(
        id=uuid.uuid4(),
        enabled=enabled,
        fee_type=fee_type,
        amount=amount,
        frequency=frequency,
        grace_days=grace_days,
        max_fee=max_fee,
        created_at=now,
        updated_at=now,
    )


def make_plan(invoice, *, installments: list | None = None, status: str = "active"):
    return SimpleNamespace(
        id=uuid.uuid4(),
        invoice_id=invoice.id,
        school_id=invoice.school_id,
        total_installments=len(installments or []),
        status=status,
        created_at=datetime(2026, 3, 3, tzinfo=timezone.utc),
        updated_at=datetime(2026, 3, 4, tzinfo=timezone.utc),
        invoice=invoice,
        installments=list(installments or []),
    )


def make_installment(
    plan,
    *,
    installment_number: int,
    amount: float = 100.0,
    status: str = "pending",
    paid_at: datetime | None = None,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        plan_id=plan.id,
        installment_number=installment_number,
        amount=Decimal(str(amount)),
        due_date=datetime(2026, 4, installment_number, tzinfo=timezone.utc),
        paid_at=paid_at,
        status=status,
        plan=plan,
    )


def setup_billing_service(monkeypatch: pytest.MonkeyPatch):
    service = BillingService(AsyncMock())
    service.repo = AsyncMock()
    service.enhancements_repo = AsyncMock()
    service.audit = AsyncMock()
    service._dispatcher = SimpleNamespace(dispatch=AsyncMock())

    repo_in_uow = AsyncMock()
    enhancements_repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(billing_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(billing_module, "BillingRepository", lambda _session: repo_in_uow)
    monkeypatch.setattr(
        billing_module,
        "BillingEnhancementsRepository",
        lambda _session: enhancements_repo_in_uow,
    )
    monkeypatch.setattr(billing_module, "AuditService", lambda _session: audit)

    return service, repo_in_uow, enhancements_repo_in_uow, audit, uow


def setup_payment_plan_service(monkeypatch: pytest.MonkeyPatch):
    service = PaymentPlanService(AsyncMock())
    service.billing_repo = AsyncMock()
    service.repo = AsyncMock()
    service.audit = AsyncMock()

    repo_in_uow = AsyncMock()
    billing_repo_in_uow = AsyncMock()
    audit = AsyncMock()
    uow = FakeUnitOfWork()

    monkeypatch.setattr(payment_plan_module, "UnitOfWork", lambda _db: uow)
    monkeypatch.setattr(
        payment_plan_module,
        "BillingEnhancementsRepository",
        lambda _session: repo_in_uow,
    )
    monkeypatch.setattr(
        payment_plan_module,
        "BillingRepository",
        lambda _session: billing_repo_in_uow,
    )
    monkeypatch.setattr(payment_plan_module, "AuditService", lambda _session: audit)
    monkeypatch.setattr(
        payment_plan_module,
        "role_has_permission",
        lambda _role, _perm: True,
    )

    return service, repo_in_uow, billing_repo_in_uow, audit, uow


class TestBillingHelpers:
    def test_sibling_discount_percent_by_rank(self):
        service = BillingService(AsyncMock())
        policy = make_sibling_policy()

        assert service._get_sibling_discount_percent(policy=policy, sibling_rank=1) == 0.0
        assert service._get_sibling_discount_percent(policy=policy, sibling_rank=2) == 10.0
        assert service._get_sibling_discount_percent(policy=policy, sibling_rank=3) == 20.0
        assert service._get_sibling_discount_percent(policy=policy, sibling_rank=4) == 30.0

    def test_order_assigned_siblings_prefers_birth_dates_then_names(self):
        service = BillingService(AsyncMock())
        student_old = uuid.uuid4()
        student_young = uuid.uuid4()
        student_unknown = uuid.uuid4()

        ordered = service._order_assigned_siblings(
            [
                (student_unknown, "Zina", None),
                (student_young, "Nadia", date(2013, 6, 5)),
                (student_old, "Amine", date(2011, 1, 10)),
            ],
            assigned_student_ids={student_unknown, student_young, student_old},
            oldest_first=True,
        )

        assert ordered == [student_old, student_young, student_unknown]

    def test_calculate_late_fee_target_fixed_policy_honors_max_fee(self):
        service = BillingService(AsyncMock())
        invoice = make_invoice(
            uuid.uuid4(),
            uuid.uuid4(),
            items=[make_invoice_item("Tuition", 500.0)],
            due_date=date(2026, 3, 10),
        )
        policy = make_late_fee_policy(amount=10.0, frequency="daily", max_fee=25.0)

        target_fee, overdue_days, fee_units = service._calculate_late_fee_target(
            invoice=invoice,
            policy=policy,
            as_of_date=date(2026, 3, 15),
        )

        assert float(target_fee.amount) == 25.0
        assert overdue_days == 5
        assert fee_units == 5

    def test_calculate_late_fee_target_percent_weekly_uses_principal(self):
        service = BillingService(AsyncMock())
        invoice = make_invoice(
            uuid.uuid4(),
            uuid.uuid4(),
            items=[make_invoice_item("Tuition", 400.0), make_invoice_item("Books", 100.0)],
            due_date=date(2026, 3, 1),
        )
        policy = make_late_fee_policy(
            fee_type="percent",
            amount=5.0,
            frequency="weekly",
            grace_days=0,
        )

        target_fee, overdue_days, fee_units = service._calculate_late_fee_target(
            invoice=invoice,
            policy=policy,
            as_of_date=date(2026, 3, 15),
        )

        assert float(target_fee.amount) == 50.0
        assert overdue_days == 14
        assert fee_units == 2


class TestGenerateInvoices:
    @pytest.mark.asyncio
    async def test_rejects_due_date_before_issued_date(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _enh_repo_in_uow, _audit, _uow = setup_billing_service(
            monkeypatch
        )

        with pytest.raises(ValidationError, match="due_date must be on or after"):
            await service.generate_invoices(
                body=InvoiceGenerateRequest(
                    fee_structure_id=uuid.uuid4(),
                    issued_date=date(2026, 4, 10),
                    due_date=date(2026, 4, 9),
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_returns_zero_summary_when_no_assignments(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _enh_repo_in_uow, _audit, _uow = setup_billing_service(
            monkeypatch
        )
        fee_structure = make_fee_structure(auth)
        service.repo.get_fee_structure.return_value = fee_structure
        service.repo.list_active_fee_assignments.return_value = []

        result = await service.generate_invoices(
            body=InvoiceGenerateRequest(
                fee_structure_id=fee_structure.id,
                issued_date=date(2026, 4, 1),
                due_date=date(2026, 4, 10),
            ),
            auth=auth,
            ip_address=None,
        )

        assert result == {"generated": 0, "skipped": 0, "total_amount": 0}

    @pytest.mark.asyncio
    async def test_rejects_inactive_fee_structure(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth()
        service, _repo_in_uow, _enh_repo_in_uow, _audit, _uow = setup_billing_service(
            monkeypatch
        )
        service.repo.get_fee_structure.return_value = make_fee_structure(auth, status="ARCHIVED")

        with pytest.raises(ValidationError, match="not active"):
            await service.generate_invoices(
                body=InvoiceGenerateRequest(
                    fee_structure_id=uuid.uuid4(),
                    issued_date=date(2026, 4, 1),
                    due_date=date(2026, 4, 10),
                ),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_generates_invoices_with_manual_and_sibling_discounts(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, repo_in_uow, _enh_repo_in_uow, audit, uow = setup_billing_service(
            monkeypatch
        )
        fee_structure = make_fee_structure(auth)
        parent_id = uuid.uuid4()
        student_old = uuid.uuid4()
        student_young = uuid.uuid4()
        assignments = [
            make_assignment(student_old, discount_percent=5.0),
            make_assignment(student_young),
        ]
        for assignment in assignments:
            assignment.school_id = auth.school_id
            assignment.fee_structure_id = fee_structure.id

        service.repo.get_fee_structure.return_value = fee_structure
        service.repo.list_active_fee_assignments.return_value = assignments
        service.repo.list_parent_links_for_students.return_value = [
            make_parent_link(student_old, parent_id),
            make_parent_link(student_young, parent_id),
        ]
        sibling_policy = make_sibling_policy()
        service.enhancements_repo.get_sibling_discount_policy.return_value = sibling_policy
        service.enhancements_repo.get_siblings_by_parent.return_value = [
            (student_old, "Amina", date(2011, 5, 1)),
            (student_young, "Bilal", date(2013, 8, 1)),
        ]

        invoice_one = make_invoice(auth.school_id, parent_id, total_amount=475.0)
        invoice_two = make_invoice(auth.school_id, parent_id, total_amount=450.0)
        repo_in_uow.create_invoice.side_effect = [invoice_one, invoice_two]

        result = await service.generate_invoices(
            body=InvoiceGenerateRequest(
                fee_structure_id=fee_structure.id,
                period_id=uuid.uuid4(),
                issued_date=date(2026, 4, 1),
                due_date=date(2026, 4, 10),
            ),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result == {
            "generated": 2,
            "skipped": 0,
            "total_amount": 925.0,
            "currency": "MAD",
        }
        descriptions = [
            call.kwargs["description"] for call in repo_in_uow.create_invoice_item.await_args_list
        ]
        assert "manual 5%" in descriptions[0]
        assert "sibling 10%" in descriptions[1]
        audit.log_event.assert_awaited_once()
        assert service._dispatcher.dispatch.await_count == 2
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_skips_missing_parent_and_zero_amount_invoices(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, repo_in_uow, _enh_repo_in_uow, _audit, _uow = setup_billing_service(
            monkeypatch
        )
        fee_structure = make_fee_structure(auth)
        student_no_parent = uuid.uuid4()
        student_full_discount = uuid.uuid4()
        assignments = [
            make_assignment(student_no_parent),
            make_assignment(student_full_discount, discount_percent=100.0),
        ]
        for assignment in assignments:
            assignment.school_id = auth.school_id
            assignment.fee_structure_id = fee_structure.id

        service.repo.get_fee_structure.return_value = fee_structure
        service.repo.list_active_fee_assignments.return_value = assignments
        service.repo.list_parent_links_for_students.return_value = [
            make_parent_link(student_full_discount, uuid.uuid4())
        ]
        service.enhancements_repo.get_sibling_discount_policy.return_value = None

        result = await service.generate_invoices(
            body=InvoiceGenerateRequest(
                fee_structure_id=fee_structure.id,
                issued_date=date(2026, 4, 1),
                due_date=date(2026, 4, 10),
            ),
            auth=auth,
            ip_address=None,
        )

        assert result["generated"] == 0
        assert result["skipped"] == 2
        repo_in_uow.create_invoice.assert_not_awaited()


class TestApplyLateFees:
    @pytest.mark.asyncio
    async def test_returns_zero_when_policy_is_disabled(self, monkeypatch: pytest.MonkeyPatch):
        service, _repo_in_uow, _enh_repo_in_uow, _audit, _uow = setup_billing_service(
            monkeypatch
        )
        service.enhancements_repo.get_late_fee_policy.return_value = make_late_fee_policy(
            enabled=False
        )

        result = await service.apply_late_fees(school_id=uuid.uuid4())

        assert result == {"checked": 0, "updated": 0, "total_fee_applied": 0.0}

    @pytest.mark.asyncio
    async def test_applies_only_delta_fee_above_existing_late_fees(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth()
        service, repo_in_uow, enh_repo_in_uow, audit, uow = setup_billing_service(
            monkeypatch
        )
        policy = make_late_fee_policy(amount=5.0, frequency="daily")
        invoice = make_invoice(
            auth.school_id,
            uuid.uuid4(),
            total_amount=505.0,
            due_date=date(2026, 3, 20),
            items=[
                make_invoice_item("Tuition", 500.0),
                make_invoice_item("Late fee (once, existing)", 5.0),
            ],
        )
        service.enhancements_repo.get_late_fee_policy.return_value = policy
        enh_repo_in_uow.get_late_fee_policy.return_value = policy
        enh_repo_in_uow.list_overdue_invoices_for_late_fees.return_value = [invoice]

        result = await service.apply_late_fees(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            as_of_date=date(2026, 3, 23),
        )

        assert result == {"checked": 1, "updated": 1, "total_fee_applied": 10.0}
        assert invoice.total_amount == 515.0
        repo_in_uow.create_invoice_item.assert_awaited_once()
        assert repo_in_uow.create_invoice_item.await_args.kwargs["amount"] == 10.0
        repo_in_uow.save_invoice.assert_awaited_once_with(invoice)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True


class TestPaymentPlanService:
    @pytest.mark.parametrize(
        ("total", "count", "expected"),
        [
            (500.0, 3, [166.67, 166.67, 166.66]),
            (100.0, 4, [25.0, 25.0, 25.0, 25.0]),
            (20.0, 1, [20.0]),
        ],
    )
    def test_split_amounts_preserves_total_and_currency(
        self,
        total: float,
        count: int,
        expected: list[float],
    ):
        service = PaymentPlanService(AsyncMock())
        amounts = service._split_amounts(
            total=payment_plan_module.Money.from_float(total, "MAD"),
            count=count,
        )

        assert [float(item.amount) for item in amounts] == expected
        assert all(item.currency == "MAD" for item in amounts)

    @pytest.mark.parametrize(
        ("source", "months", "expected"),
        [
            (date(2026, 1, 31), 1, date(2026, 2, 28)),
            (date(2026, 10, 31), 4, date(2027, 2, 28)),
            (date(2024, 2, 29), 12, date(2025, 2, 28)),
            (date(2026, 3, 15), 6, date(2026, 9, 15)),
        ],
    )
    def test_add_months_clamps_end_of_month(self, source: date, months: int, expected: date):
        service = PaymentPlanService(AsyncMock())
        assert service._add_months(source, months) == expected

    def test_to_due_datetime_normalizes_to_utc_midnight(self):
        service = PaymentPlanService(AsyncMock())

        due_at = service._to_due_datetime(date(2026, 9, 1))

        assert due_at == datetime(2026, 9, 1, tzinfo=timezone.utc)

    @pytest.mark.parametrize("paid_at", [None, datetime(2026, 4, 2, tzinfo=timezone.utc)])
    def test_installment_to_response_serializes_paid_and_unpaid(
        self,
        paid_at: datetime | None,
    ):
        service = PaymentPlanService(AsyncMock())
        plan = make_plan(make_invoice(uuid.uuid4(), uuid.uuid4()))
        installment = make_installment(plan, installment_number=2, paid_at=paid_at)

        result = service._installment_to_response(installment)

        assert result["installment_number"] == 2
        assert result["amount"] == 100.0
        assert result["paid_at"] == (paid_at.isoformat() if paid_at else None)

    def test_plan_to_summary_counts_paid_and_pending_installments(self):
        service = PaymentPlanService(AsyncMock())
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4(), total_amount=900.0)
        plan = make_plan(
            invoice,
            installments=[
                SimpleNamespace(status="paid"),
                SimpleNamespace(status="pending"),
                SimpleNamespace(status="paid"),
            ],
        )
        plan.total_installments = 3

        result = service._plan_to_summary(plan)

        assert result["currency"] == "MAD"
        assert result["installments_paid"] == 2
        assert result["installments_pending"] == 1

    def test_plan_to_detail_sorts_installments_by_number(self):
        service = PaymentPlanService(AsyncMock())
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4())
        plan = make_plan(
            invoice,
            installments=[
                make_installment(
                    SimpleNamespace(id=uuid.uuid4()),
                    installment_number=3,
                    amount=120.0,
                ),
                make_installment(
                    SimpleNamespace(id=uuid.uuid4()),
                    installment_number=1,
                    amount=80.0,
                ),
            ],
        )
        plan.installments[0].plan_id = plan.id
        plan.installments[1].plan_id = plan.id

        result = service._plan_to_detail(plan)

        assert [item["installment_number"] for item in result["installments"]] == [1, 3]

    @pytest.mark.parametrize("role", ["STD", "PAR"])
    def test_ensure_can_create_raises_for_missing_permission(self, monkeypatch: pytest.MonkeyPatch, role: str):
        auth = make_auth(role)
        service = PaymentPlanService(AsyncMock())
        monkeypatch.setattr(payment_plan_module, "role_has_permission", lambda *_args: False)

        with pytest.raises(AuthorizationError, match="Insufficient permissions"):
            service._ensure_can_create(auth)

    @pytest.mark.parametrize("role", ["STD", "TCH"])
    def test_ensure_can_read_raises_for_missing_permission(self, monkeypatch: pytest.MonkeyPatch, role: str):
        auth = make_auth(role)
        service = PaymentPlanService(AsyncMock())
        monkeypatch.setattr(payment_plan_module, "role_has_permission", lambda *_args: False)

        with pytest.raises(AuthorizationError, match="Insufficient permissions"):
            service._ensure_can_read(auth)

    @pytest.mark.asyncio
    async def test_create_plan_hides_other_parent_invoice(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("PAR")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4())
        service.billing_repo.get_invoice_by_id.return_value = invoice

        with pytest.raises(NotFoundError, match="Invoice not found"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_rejects_without_permission(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        monkeypatch.setattr(payment_plan_module, "role_has_permission", lambda *_args: False)

        with pytest.raises(AuthorizationError, match="Insufficient permissions"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=uuid.uuid4(), num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_raises_when_invoice_missing(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        service.billing_repo.get_invoice_by_id.return_value = None

        with pytest.raises(NotFoundError, match="Invoice not found"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=uuid.uuid4(), num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_masks_other_school_invoice(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4())
        service.billing_repo.get_invoice_by_id.return_value = invoice

        with pytest.raises(NotFoundError, match="Resource not found"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_rejects_paid_invoice(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4(), status="paid")
        service.billing_repo.get_invoice_by_id.return_value = invoice

        with pytest.raises(ConflictError, match="paid invoice"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_rejects_existing_active_plan(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4())
        service.billing_repo.get_invoice_by_id.return_value = invoice
        service.repo.get_active_payment_plan_for_invoice.return_value = SimpleNamespace(
            id=uuid.uuid4()
        )

        with pytest.raises(ConflictError, match="already exists"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=3),
                auth=auth,
                ip_address=None,
            )

    @pytest.mark.asyncio
    async def test_create_plan_creates_installments_and_returns_detail(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, repo_in_uow, _billing_repo_in_uow, audit, uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4(), total_amount=500.0)
        service.billing_repo.get_invoice_by_id.return_value = invoice
        service.repo.get_active_payment_plan_for_invoice.return_value = None

        created_plan = SimpleNamespace(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            school_id=invoice.school_id,
        )
        repo_in_uow.create_payment_plan.return_value = created_plan
        saved_plan = make_plan(
            invoice,
            installments=[
                SimpleNamespace(
                    id=uuid.uuid4(),
                    plan_id=created_plan.id,
                    installment_number=1,
                    amount=Decimal("166.67"),
                    due_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
                    paid_at=None,
                    status="pending",
                ),
                SimpleNamespace(
                    id=uuid.uuid4(),
                    plan_id=created_plan.id,
                    installment_number=2,
                    amount=Decimal("166.67"),
                    due_date=datetime(2026, 4, 1, tzinfo=timezone.utc),
                    paid_at=None,
                    status="pending",
                ),
                SimpleNamespace(
                    id=uuid.uuid4(),
                    plan_id=created_plan.id,
                    installment_number=3,
                    amount=Decimal("166.66"),
                    due_date=datetime(2026, 5, 1, tzinfo=timezone.utc),
                    paid_at=None,
                    status="pending",
                ),
            ],
        )
        saved_plan.id = created_plan.id
        saved_plan.total_installments = 3
        repo_in_uow.get_payment_plan.return_value = saved_plan

        result = await service.create_plan(
            body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=3),
            auth=auth,
            ip_address="127.0.0.1",
        )

        assert result["invoice_id"] == str(invoice.id)
        assert result["currency"] == "MAD"
        assert len(result["installments"]) == 3
        first_batch = repo_in_uow.create_installments.await_args.args[0]
        assert [item["due_date"].month for item in first_batch] == [3, 4, 5]
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_create_plan_raises_when_saved_plan_missing(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, repo_in_uow, _billing_repo_in_uow, audit, uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4(), total_amount=300.0)
        service.billing_repo.get_invoice_by_id.return_value = invoice
        service.repo.get_active_payment_plan_for_invoice.return_value = None
        repo_in_uow.create_payment_plan.return_value = SimpleNamespace(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            school_id=invoice.school_id,
        )
        repo_in_uow.get_payment_plan.return_value = None

        with pytest.raises(NotFoundError, match="Payment plan not found"):
            await service.create_plan(
                body=PaymentPlanCreateRequest(invoice_id=invoice.id, num_installments=2),
                auth=auth,
                ip_address="127.0.0.1",
            )

        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_list_plans_scopes_to_parent(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("PAR")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, auth.user_id)
        plan = make_plan(
            invoice,
            installments=[
                SimpleNamespace(status="pending"),
                SimpleNamespace(status="paid"),
            ],
        )
        service.repo.list_payment_plans.return_value = [plan]

        result = await service.list_plans(auth=auth, parent_id=uuid.uuid4())

        assert result[0]["parent_id"] == str(auth.user_id)
        assert service.repo.list_payment_plans.await_args.kwargs["parent_id"] == auth.user_id

    @pytest.mark.asyncio
    async def test_list_plans_rejects_without_permission(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        monkeypatch.setattr(payment_plan_module, "role_has_permission", lambda *_args: False)

        with pytest.raises(AuthorizationError, match="Insufficient permissions"):
            await service.list_plans(auth=auth)

    @pytest.mark.asyncio
    async def test_list_plans_preserves_explicit_parent_filter_for_admin(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        parent_id = uuid.uuid4()
        service.repo.list_payment_plans.return_value = []

        result = await service.list_plans(auth=auth, parent_id=parent_id)

        assert result == []
        assert service.repo.list_payment_plans.await_args.kwargs["parent_id"] == parent_id

    @pytest.mark.asyncio
    async def test_get_plan_hides_other_parent(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("PAR")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4())
        plan = make_plan(invoice)
        service.repo.get_payment_plan.return_value = plan

        with pytest.raises(NotFoundError, match="Payment plan not found"):
            await service.get_plan(plan_id=plan.id, auth=auth)

    @pytest.mark.asyncio
    async def test_get_plan_rejects_without_permission(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("STD")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        monkeypatch.setattr(payment_plan_module, "role_has_permission", lambda *_args: False)

        with pytest.raises(AuthorizationError, match="Insufficient permissions"):
            await service.get_plan(plan_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_get_plan_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        service.repo.get_payment_plan.return_value = None

        with pytest.raises(NotFoundError, match="Payment plan not found"):
            await service.get_plan(plan_id=uuid.uuid4(), auth=auth)

    @pytest.mark.asyncio
    async def test_get_plan_masks_other_school(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4())
        plan = make_plan(invoice)
        service.repo.get_payment_plan.return_value = plan

        with pytest.raises(NotFoundError, match="Resource not found"):
            await service.get_plan(plan_id=plan.id, auth=auth)

    @pytest.mark.asyncio
    async def test_get_plan_returns_detail_for_admin(self, monkeypatch: pytest.MonkeyPatch):
        auth = make_auth("ADM")
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(auth.school_id, uuid.uuid4())
        plan = make_plan(
            invoice,
            installments=[
                make_installment(SimpleNamespace(id=uuid.uuid4()), installment_number=2),
                make_installment(SimpleNamespace(id=uuid.uuid4()), installment_number=1),
            ],
        )
        for installment in plan.installments:
            installment.plan_id = plan.id
        service.repo.get_payment_plan.return_value = plan

        result = await service.get_plan(plan_id=plan.id, auth=auth)

        assert result["id"] == str(plan.id)
        assert [item["installment_number"] for item in result["installments"]] == [1, 2]

    @pytest.mark.asyncio
    async def test_mark_installment_paid_is_idempotent_for_paid_installment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4())
        plan = make_plan(invoice)
        paid_at = datetime(2026, 3, 10, tzinfo=timezone.utc)
        installment = make_installment(
            plan,
            installment_number=1,
            status="paid",
            paid_at=paid_at,
        )
        service.repo.get_installment.return_value = installment

        result = await service.mark_installment_paid(installment_id=installment.id)

        assert result["status"] == "paid"
        assert result["paid_at"] == paid_at.isoformat()

    @pytest.mark.asyncio
    async def test_mark_installment_paid_raises_when_missing_before_uow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, _repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        service.repo.get_installment.return_value = None

        with pytest.raises(NotFoundError, match="Installment not found"):
            await service.mark_installment_paid(installment_id=uuid.uuid4())

    @pytest.mark.asyncio
    async def test_mark_installment_paid_raises_when_missing_inside_uow(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, repo_in_uow, _billing_repo_in_uow, _audit, _uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4())
        plan = make_plan(invoice)
        installment = make_installment(plan, installment_number=1, status="pending")
        service.repo.get_installment.return_value = installment
        repo_in_uow.get_installment.return_value = None

        with pytest.raises(NotFoundError, match="Installment not found"):
            await service.mark_installment_paid(installment_id=installment.id)

    @pytest.mark.asyncio
    async def test_mark_installment_paid_completes_plan_and_invoice(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, repo_in_uow, billing_repo_in_uow, audit, uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4(), status="pending")
        plan = make_plan(invoice)
        installment_one = make_installment(plan, installment_number=1, status="pending")
        installment_two = make_installment(
            plan,
            installment_number=2,
            status="paid",
            paid_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
        )
        plan.installments = [installment_one, installment_two]
        installment_one.plan = plan
        installment_two.plan = plan
        service.repo.get_installment.return_value = installment_one
        repo_in_uow.get_installment.return_value = installment_one

        result = await service.mark_installment_paid(
            installment_id=installment_one.id,
            actor_id=uuid.uuid4(),
        )

        assert result["status"] == "paid"
        assert plan.status == "completed"
        assert invoice.status == "paid"
        repo_in_uow.save_payment_plan.assert_awaited_once_with(plan)
        billing_repo_in_uow.save_invoice.assert_awaited_once_with(invoice)
        audit.log_event.assert_awaited_once()
        assert uow.committed is True

    @pytest.mark.asyncio
    async def test_mark_installment_paid_leaves_plan_active_when_items_remain(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        service, repo_in_uow, billing_repo_in_uow, audit, uow = setup_payment_plan_service(
            monkeypatch
        )
        invoice = make_invoice(uuid.uuid4(), uuid.uuid4(), status="pending")
        plan = make_plan(invoice)
        installment_one = make_installment(plan, installment_number=1, status="pending")
        installment_two = make_installment(plan, installment_number=2, status="pending")
        plan.installments = [installment_one, installment_two]
        installment_one.plan = plan
        installment_two.plan = plan
        service.repo.get_installment.return_value = installment_one
        repo_in_uow.get_installment.return_value = installment_one
        paid_at = datetime(2026, 3, 12, tzinfo=timezone.utc)

        result = await service.mark_installment_paid(
            installment_id=installment_one.id,
            paid_at=paid_at,
        )

        assert result["paid_at"] == paid_at.isoformat()
        assert plan.status == "active"
        assert invoice.status == "pending"
        repo_in_uow.save_payment_plan.assert_not_awaited()
        billing_repo_in_uow.save_invoice.assert_not_awaited()
        audit.log_event.assert_awaited_once()
        assert uow.committed is True
