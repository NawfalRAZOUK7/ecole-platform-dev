"""Billing factories."""

from __future__ import annotations

import secrets
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import factory

from app.models.billing import (
    FeeFrequency,
    FeeStructure,
    Installment,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    PaymentAttempt,
    PaymentAttemptStatus,
    PaymentPlan,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _today() -> date:
    return date.today()


class InvoiceFactory(AsyncSQLAlchemyFactory):
    """Factory for invoices."""

    class Meta:
        model = Invoice
        exclude = ("school", "parent")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    parent = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    parent_id = factory.LazyAttribute(lambda o: o.parent.id)
    period_id = None
    status = InvoiceStatus.PENDING.value
    total_amount = Decimal("500.00")
    currency = "MAD"
    issued_date = factory.LazyFunction(_today)
    due_date = factory.LazyFunction(lambda: _today() + timedelta(days=30))
    reminder_sent_at = None
    reminder_count = 0
    fee_structure_id = None


class InvoiceItemFactory(AsyncSQLAlchemyFactory):
    """Factory for invoice line items."""

    class Meta:
        model = InvoiceItem
        exclude = ("invoice",)

    id = factory.LazyFunction(uuid.uuid4)
    invoice = factory.SubFactory(InvoiceFactory)
    invoice_id = factory.LazyAttribute(lambda o: o.invoice.id)
    description = "Frais de scolarité"
    amount = Decimal("500.00")
    unit_price = Decimal("500.00")
    quantity = 1


class PaymentAttemptFactory(AsyncSQLAlchemyFactory):
    """Factory for payment attempts."""

    class Meta:
        model = PaymentAttempt
        exclude = ("invoice",)

    id = factory.LazyFunction(uuid.uuid4)
    invoice = factory.SubFactory(InvoiceFactory)
    school_id = factory.LazyAttribute(lambda o: o.invoice.school_id)
    invoice_id = factory.LazyAttribute(lambda o: o.invoice.id)
    parent_id = factory.LazyAttribute(lambda o: o.invoice.parent_id)
    idempotency_key = factory.LazyFunction(lambda: secrets.token_urlsafe(24))
    status = PaymentAttemptStatus.PENDING.value
    finalized_at = None
    retry_count = 0
    next_retry_at = None
    last_retry_error = None


class FeeStructureFactory(AsyncSQLAlchemyFactory):
    """Factory for fee structures."""

    class Meta:
        model = FeeStructure
        exclude = ("school", "academic_year")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory, school=factory.SelfAttribute("..school")
    )
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    name = "Frais standard"
    amount = Decimal("500.00")
    currency = "MAD"
    frequency = FeeFrequency.MONTHLY.value
    due_day = 5
    applies_to_level = None
    status = "ACTIVE"


class PaymentPlanFactory(AsyncSQLAlchemyFactory):
    """Factory for payment plans."""

    class Meta:
        model = PaymentPlan
        exclude = ("invoice",)

    id = factory.LazyFunction(uuid.uuid4)
    invoice = factory.SubFactory(InvoiceFactory)
    school_id = factory.LazyAttribute(lambda o: o.invoice.school_id)
    invoice_id = factory.LazyAttribute(lambda o: o.invoice.id)
    total_installments = 3
    status = "active"


class InstallmentFactory(AsyncSQLAlchemyFactory):
    """Factory for individual installments."""

    class Meta:
        model = Installment
        exclude = ("plan",)

    id = factory.LazyFunction(uuid.uuid4)
    plan = factory.SubFactory(PaymentPlanFactory)
    plan_id = factory.LazyAttribute(lambda o: o.plan.id)
    installment_number = 1
    amount = Decimal("166.67")
    due_date = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=30))
    paid_at = None
    status = "pending"
