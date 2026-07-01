"""Mock-based unit tests for billing, billing_enhancements, and budget repositories."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.billing import BillingRepository
from app.repositories.billing_enhancements import BillingEnhancementsRepository
from app.repositories.budget import BudgetRepository


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


class _FR:
    def __init__(self, v=None, many=None, scalar=None, rowcount=1):
        self._v = v
        self._many = many or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._v

    def scalar_one(self):
        return self._v

    def scalar(self):
        return self._scalar

    def scalars(self):
        many = self._many
        v = self._v
        ns = SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))
        ns.unique = lambda: ns
        return ns

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None):
    r = result if result is not None else _FR()
    return SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        merge=AsyncMock(return_value=r._v),
    )


# ===========================================================================
# BillingRepository
# ===========================================================================


class TestBillingRepository:
    def repo(self, result=None):
        return BillingRepository(_db(result))

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_academic_year(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_fee_structure(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_fee_structure(_uid()) is obj

    @pytest.mark.asyncio
    async def test_list_fee_structures_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_structures(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_fee_structures_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_structures(
            school_id=_uid(),
            academic_year_id=_uid(),
            status="active",
            applies_to_level="primary",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_fee_structure(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.FeeStructure", return_value=fake):
            result = await BillingRepository(db).create_fee_structure(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_fee_structure(self):
        fs = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingRepository(db).save_fee_structure(fs)
        assert result is fs

    @pytest.mark.asyncio
    async def test_get_user_by_id(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_user_by_id(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_fee_assignment_no_student(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingRepository(db).get_fee_assignment(
            fee_structure_id=_uid(), student_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_fee_assignment_with_student(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingRepository(db).get_fee_assignment(
            fee_structure_id=_uid(), student_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_fee_assignments_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_assignments(
            fee_structure_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_fee_assignments_with_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_assignments(
            school_id=_uid(), fee_structure_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_existing_assignment_student_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await BillingRepository(db).list_existing_assignment_student_ids(
            fee_structure_id=_uid(), student_ids=ids
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_create_fee_assignment(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.FeeAssignment", return_value=fake):
            result = await BillingRepository(db).create_fee_assignment(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_fee_assignments(self):
        fake1 = SimpleNamespace(id=_uid())
        fake2 = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        with patch(
            "app.repositories.billing.FeeAssignment", side_effect=[fake1, fake2]
        ):
            result = await BillingRepository(db).create_fee_assignments(
                assignments_data=[
                    {
                        "school_id": _uid(),
                        "fee_structure_id": _uid(),
                        "student_id": _uid(),
                    },
                    {
                        "school_id": _uid(),
                        "fee_structure_id": _uid(),
                        "student_id": _uid(),
                    },
                ]
            )
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await BillingRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_active_enrollment_student_ids_for_class(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await BillingRepository(
            db
        ).list_active_enrollment_student_ids_for_class(
            class_id=_uid(), school_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_class_ids_by_level(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await BillingRepository(db).list_class_ids_by_level(
            school_id=_uid(), level="primary"
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_active_enrollment_student_ids_for_classes(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await BillingRepository(
            db
        ).list_active_enrollment_student_ids_for_classes(
            class_ids=[_uid()], school_id=_uid()
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_active_fee_assignments_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_active_fee_assignments(
            fee_structure_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_active_fee_assignments_with_student_id(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_active_fee_assignments(
            fee_structure_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_parent_links_for_students(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_parent_links_for_students(
            student_ids=[_uid()], school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_invoice(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.Invoice", return_value=fake):
            result = await BillingRepository(db).create_invoice(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_invoice(self):
        inv = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingRepository(db).save_invoice(inv)
        assert result is inv

    @pytest.mark.asyncio
    async def test_create_invoice_item(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.InvoiceItem", return_value=fake):
            result = await BillingRepository(db).create_invoice_item(invoice_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_invoice_by_id_no_school(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_invoice_by_id(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_invoice_by_id_with_school(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_invoice_by_id(_uid()) is obj

    @pytest.mark.asyncio
    async def test_list_invoices_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        from unittest.mock import MagicMock

        with (
            patch(
                "app.repositories.billing.apply_filters",
                side_effect=lambda q, *a, **kw: q,
            ),
            patch(
                "app.repositories.billing.apply_sort", side_effect=lambda q, *a, **kw: q
            ),
        ):
            result, cursor, has_more = await BillingRepository(db).list_invoices(
                school_id=_uid(),
                role="ADM",
                user_id=_uid(),
                status=None,
                cursor=None,
                limit=10,
                filters=MagicMock(),
                sort=MagicMock(),
                search=None,
            )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_invoices_with_filters_and_cursor(self):
        now = _now()
        items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(6)]
        db = _db(_FR(many=items))
        from unittest.mock import MagicMock

        with (
            patch(
                "app.repositories.billing.apply_filters",
                side_effect=lambda q, *a, **kw: q,
            ),
            patch(
                "app.repositories.billing.apply_sort", side_effect=lambda q, *a, **kw: q
            ),
            patch(
                "app.repositories.billing.decode_cursor",
                return_value=(_uid(), now.isoformat()),
            ),
        ):
            result, cursor, has_more = await BillingRepository(db).list_invoices(
                school_id=_uid(),
                role="ADM",
                user_id=_uid(),
                status="pending",
                cursor="cur",
                limit=5,
                filters=MagicMock(),
                sort=MagicMock(),
                search=None,
            )
        assert has_more is True

    @pytest.mark.asyncio
    async def test_get_payment_by_id(self):
        obj = object()
        assert await BillingRepository(_db(_FR(v=obj))).get_payment_by_id(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_payment_by_idempotency_key(self):
        obj = object()
        result = await BillingRepository(
            _db(_FR(v=obj))
        ).get_payment_by_idempotency_key("key")
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_payments_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_payments(invoice_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_payments_with_status(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_payments(invoice_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_create_payment(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.PaymentAttempt", return_value=fake):
            result = await BillingRepository(db).create_payment(invoice_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_payment(self):
        pay = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingRepository(db).save_payment(pay)
        assert result is pay

    @pytest.mark.asyncio
    async def test_get_webhook_event_by_provider_event_id(self):
        obj = object()
        result = await BillingRepository(
            _db(_FR(v=obj))
        ).get_webhook_event_by_provider_event_id("evt_123")
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_webhook_event(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.ProviderWebhookEvent", return_value=fake):
            result = await BillingRepository(db).create_webhook_event(
                event_id="evt_123"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_failed_attempts_no_cutoff(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).get_failed_attempts(
            now=_now(), max_retries=3
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_failed_attempts_with_cutoff(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).get_failed_attempts(
            now=_now(), max_retries=3, limit=50
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_overdue_invoices_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        from datetime import date as _date

        result = await BillingRepository(db).get_overdue_invoices(
            overdue_cutoff=_date.today(), reminder_cooldown=_now(), max_reminders=3
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_overdue_invoices_with_parent(self):
        items = [object()]
        db = _db(_FR(many=items))
        from datetime import date as _date

        result = await BillingRepository(db).get_overdue_invoices(
            overdue_cutoff=_date.today(), reminder_cooldown=_now(), max_reminders=3
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_billing_email_consent(self):
        obj = object()
        result = await BillingRepository(_db(_FR(v=obj))).get_billing_email_consent(
            user_id=_uid()
        )
        assert result is obj


# ===========================================================================
# BillingEnhancementsRepository
# ===========================================================================


class TestBillingEnhancementsRepository:
    @pytest.mark.asyncio
    async def test_get_sibling_discount_policy(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_sibling_discount_policy(
            school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_sibling_discount_policy(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch(
            "app.repositories.billing_enhancements.SiblingDiscountPolicy",
            return_value=fake,
        ):
            result = await BillingEnhancementsRepository(
                db
            ).create_sibling_discount_policy(school_id=_uid())
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_sibling_discount_policy(self):
        policy = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingEnhancementsRepository(db).save_sibling_discount_policy(
            policy
        )
        assert result is policy

    @pytest.mark.asyncio
    async def test_get_late_fee_policy(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_late_fee_policy(
            school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_late_fee_policy(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch(
            "app.repositories.billing_enhancements.LateFeePolicy", return_value=fake
        ):
            result = await BillingEnhancementsRepository(db).create_late_fee_policy(
                school_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_late_fee_policy(self):
        policy = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingEnhancementsRepository(db).save_late_fee_policy(policy)
        assert result is policy

    @pytest.mark.asyncio
    async def test_get_siblings_by_parent_no_exclude(self):
        items = [(_uid(), "Child", None)]
        db = _db(_FR(many=items))
        result = await BillingEnhancementsRepository(db).get_siblings_by_parent(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_siblings_by_parent_with_exclude(self):
        items = [(_uid(), "Child", None)]
        db = _db(_FR(many=items))
        result = await BillingEnhancementsRepository(db).get_siblings_by_parent(
            parent_id=_uid(), school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_overdue_invoices_for_late_fees(self):
        items = [object()]
        db = _db(_FR(many=items))
        from datetime import date as _date

        result = await BillingEnhancementsRepository(
            db
        ).list_overdue_invoices_for_late_fees(
            school_id=_uid(), overdue_before=_date.today()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_payment_plan_no_invoice(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_payment_plan(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_payment_plan_with_invoice(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_payment_plan(
            _uid(), include_installments=True
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_active_payment_plan_for_invoice(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(
            db
        ).get_active_payment_plan_for_invoice(invoice_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_payment_plans_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingEnhancementsRepository(db).list_payment_plans(
            school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_payment_plans_with_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingEnhancementsRepository(db).list_payment_plans(
            school_id=_uid(), parent_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_payment_plan(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch(
            "app.repositories.billing_enhancements.PaymentPlan", return_value=fake
        ):
            result = await BillingEnhancementsRepository(db).create_payment_plan(
                invoice_id=_uid()
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_payment_plan(self):
        plan = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingEnhancementsRepository(db).save_payment_plan(plan)
        assert result is plan

    @pytest.mark.asyncio
    async def test_create_installments(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        with patch(
            "app.repositories.billing_enhancements.Installment", return_value=fake
        ):
            await BillingEnhancementsRepository(db).create_installments(
                installments_data=[{"plan_id": str(_uid()), "amount": 100}]
            )
        db.flush.assert_awaited()

    @pytest.mark.asyncio
    async def test_get_installment(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_installment(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_installment_with_plan(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingEnhancementsRepository(db).get_installment(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_installment(self):
        inst = SimpleNamespace(id=_uid())
        db = _db()
        result = await BillingEnhancementsRepository(db).save_installment(inst)
        assert result is inst


# ===========================================================================
# BudgetRepository
# ===========================================================================


class TestBudgetRepository:
    @pytest.mark.asyncio
    async def test_get_user(self):
        obj = object()
        assert await BudgetRepository(_db(_FR(v=obj))).get_user(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        assert await BudgetRepository(_db(_FR(v=obj))).get_academic_year(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_class(self):
        obj = object()
        assert await BudgetRepository(_db(_FR(v=obj))).get_class(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_budget_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_budget(budget_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_budget_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_budget(
            budget_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_budgets_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_budgets(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_budgets_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_budgets(
            school_id=_uid(),
            academic_year_id=_uid(),
            status="approved",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_budget(self):
        budget = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).create_budget(budget)
        db.add.assert_called_once_with(budget)
        assert result is budget

    @pytest.mark.asyncio
    async def test_save_budget(self):
        budget = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).save_budget(budget)
        assert result is budget

    @pytest.mark.asyncio
    async def test_get_allocation(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_allocation(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_allocations_no_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_allocations(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_allocations_with_cursor_and_status(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_allocations(
            school_id=_uid(), budget_id=_uid(), status="approved"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_allocation(self):
        alloc = SimpleNamespace(id=_uid())
        db = _db()
        await BudgetRepository(db).create_allocation(alloc)
        db.add.assert_called_once_with(alloc)

    @pytest.mark.asyncio
    async def test_save_allocation(self):
        alloc = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).save_allocation(alloc)
        assert result is alloc

    @pytest.mark.asyncio
    async def test_get_request_no_budget(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_request(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_request_with_budget(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_request(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_requests_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_requests(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_requests_with_status_and_cursor(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_requests(
            school_id=_uid(), status="pending"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_request(self):
        req = SimpleNamespace(id=_uid())
        db = _db()
        await BudgetRepository(db).create_request(req)
        db.add.assert_called_once_with(req)

    @pytest.mark.asyncio
    async def test_save_request(self):
        req = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).save_request(req)
        assert result is req

    @pytest.mark.asyncio
    async def test_get_transaction(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_transaction(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_transactions_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_transactions(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_list_transactions_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_transactions(
            school_id=_uid(),
            transaction_type="debit",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_transaction(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).create_transaction(fake)
        db.add.assert_called_once_with(fake)
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_transaction(self):
        tx = SimpleNamespace(id=_uid())
        db = _db()
        result = await BudgetRepository(db).save_transaction(tx)
        assert result is tx
