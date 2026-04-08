"""Integration tests for BillingRepository."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.filtering import FilterSpec, SortSpec
from app.models.billing import PaymentAttemptStatus
from app.repositories.billing import BillingRepository
from tests.factories.erp import (
    AcademicYearFactory,
    ClassFactory,
    EnrollmentFactory,
    PeriodFactory,
)
from tests.factories.iam import ParentChildLinkFactory, UserFactory
from tests.factories.school import SchoolFactory


def _uuid(n: int) -> UUID:
    return UUID(f"20000000-0000-4000-8000-{n:012d}")


async def _create_billing_context(
    db_session,
    base: int,
) -> tuple[UUID, UUID, UUID, UUID, UUID, UUID]:
    school = await SchoolFactory.create(
        session=db_session,
        id=_uuid(base),
        code=f"billing-school-{base}",
    )
    year = await AcademicYearFactory.create(
        session=db_session,
        id=_uuid(base + 1),
        school_id=school.id,
    )
    period = await PeriodFactory.create(
        session=db_session,
        id=_uuid(base + 2),
        school_id=school.id,
        academic_year_id=year.id,
    )
    klass = await ClassFactory.create(
        session=db_session,
        id=_uuid(base + 3),
        school_id=school.id,
        academic_year_id=year.id,
        code=f"CLS-{base}",
    )
    parent = await UserFactory.create(
        session=db_session,
        id=_uuid(base + 4),
        school_id=school.id,
        email=f"parent-{base}@ecole.ma",
    )
    student = await UserFactory.create(
        session=db_session,
        id=_uuid(base + 5),
        school_id=school.id,
        email=f"student-{base}@ecole.ma",
    )
    return school.id, year.id, period.id, klass.id, parent.id, student.id


@pytest.mark.asyncio
async def test_fee_structure_queries_create_and_filter_rows(db_session):
    repo = BillingRepository(db_session)
    school_id, year_id, _, _, _, _ = await _create_billing_context(db_session, 1)

    seed = await repo.create_fee_structure(
        id=_uuid(10),
        school_id=school_id,
        academic_year_id=year_id,
        name="Mensualite College",
        amount=Decimal("500.00"),
        currency="MAD",
        frequency="MONTHLY",
        due_day=5,
        applies_to_level="6EME",
        status="ACTIVE",
    )
    await repo.create_fee_structure(
        id=_uuid(11),
        school_id=school_id,
        academic_year_id=year_id,
        name="Archive",
        amount=Decimal("500.00"),
        currency="MAD",
        frequency="MONTHLY",
        due_day=5,
        applies_to_level="6EME",
        status="ARCHIVED",
    )

    active_rows = await repo.list_fee_structures(
        school_id=school_id,
        academic_year_id=year_id,
        status="ACTIVE",
        applies_to_level="6EME",
    )

    assert [row.id for row in active_rows] == [seed.id]
    assert await repo.get_fee_structure(seed.id) is not None


@pytest.mark.asyncio
async def test_fee_assignment_queries_cover_existing_student_helpers(db_session):
    repo = BillingRepository(db_session)
    school_id, year_id, _, _, _, student_id = await _create_billing_context(
        db_session, 20
    )
    fee_structure = await repo.create_fee_structure(
        id=_uuid(30),
        school_id=school_id,
        academic_year_id=year_id,
        name="Frais standard",
        amount=Decimal("500.00"),
        currency="MAD",
        frequency="MONTHLY",
        due_day=5,
        applies_to_level=None,
        status="ACTIVE",
    )

    assignment = await repo.create_fee_assignment(
        id=_uuid(31),
        school_id=school_id,
        fee_structure_id=fee_structure.id,
        student_id=student_id,
        discount_percent=Decimal("10.00"),
        discount_reason="Sibling",
        status="ACTIVE",
    )

    fetched = await repo.get_fee_assignment(
        fee_structure_id=fee_structure.id,
        student_id=student_id,
    )
    listed = await repo.list_fee_assignments(
        school_id=school_id,
        fee_structure_id=fee_structure.id,
        student_id=student_id,
        status="ACTIVE",
    )
    existing = await repo.list_existing_assignment_student_ids(
        fee_structure_id=fee_structure.id,
        student_ids=[student_id, _uuid(99)],
    )

    assert fetched is not None
    assert assignment.id == fetched.id
    assert [row.id for row in listed] == [assignment.id]
    assert existing == {student_id}


@pytest.mark.asyncio
async def test_parent_and_enrollment_lookup_helpers_return_active_relationships(
    db_session,
):
    repo = BillingRepository(db_session)
    (
        school_id,
        year_id,
        period_id,
        class_id,
        parent_id,
        student_id,
    ) = await _create_billing_context(
        db_session,
        40,
    )

    await ParentChildLinkFactory.create(
        session=db_session,
        id=_uuid(50),
        school_id=school_id,
        parent_user_id=parent_id,
        child_user_id=student_id,
        linked_by=parent_id,
    )
    await EnrollmentFactory.create(
        session=db_session,
        id=_uuid(51),
        school_id=school_id,
        class_id=class_id,
        period_id=period_id,
        student_id=student_id,
        status="active",
    )

    parent_child_ids = await repo.list_parent_child_ids(
        parent_id=parent_id,
        school_id=school_id,
    )
    enrolled_ids = await repo.list_active_enrollment_student_ids_for_class(
        class_id=class_id,
        school_id=school_id,
    )

    assert parent_child_ids == {student_id}
    assert enrolled_ids == [student_id]


@pytest.mark.asyncio
async def test_create_invoice_and_load_items(db_session):
    repo = BillingRepository(db_session)
    school_id, _, period_id, _, parent_id, _ = await _create_billing_context(
        db_session, 60
    )

    invoice = await repo.create_invoice(
        id=_uuid(70),
        school_id=school_id,
        parent_id=parent_id,
        period_id=period_id,
        status="pending",
        total_amount=Decimal("330.00"),
        currency="MAD",
        issued_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        reminder_sent_at=None,
        reminder_count=0,
        fee_structure_id=None,
    )
    await repo.create_invoice_item(
        id=_uuid(71),
        invoice_id=invoice.id,
        description="Mensualite septembre",
        amount=Decimal("250.00"),
        unit_price=Decimal("250.00"),
        quantity=1,
    )
    await repo.create_invoice_item(
        id=_uuid(72),
        invoice_id=invoice.id,
        description="Transport",
        amount=Decimal("80.00"),
        unit_price=Decimal("80.00"),
        quantity=1,
    )

    loaded = await repo.get_invoice_by_id(invoice.id, include_items=True)

    assert loaded is not None
    assert loaded.id == invoice.id
    assert sorted(item.description for item in loaded.items) == [
        "Mensualite septembre",
        "Transport",
    ]


@pytest.mark.asyncio
async def test_list_invoices_applies_parent_scope_status_and_cursor(db_session):
    repo = BillingRepository(db_session)
    school_id, _, period_id, _, parent_id, _ = await _create_billing_context(
        db_session, 80
    )
    other_parent = await UserFactory.create(
        session=db_session,
        id=_uuid(89),
        school_id=school_id,
        email="other-parent@ecole.ma",
    )

    base = await repo.create_invoice(
        id=_uuid(90),
        school_id=school_id,
        parent_id=parent_id,
        period_id=period_id,
        status="pending",
        total_amount=Decimal("500.00"),
        currency="MAD",
        issued_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        reminder_sent_at=None,
        reminder_count=0,
        fee_structure_id=None,
    )
    second = await repo.create_invoice(
        id=_uuid(91),
        school_id=school_id,
        parent_id=parent_id,
        period_id=period_id,
        status="pending",
        total_amount=Decimal("500.00"),
        currency="MAD",
        issued_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        reminder_sent_at=None,
        reminder_count=0,
        fee_structure_id=None,
    )
    await repo.create_invoice(
        id=_uuid(92),
        school_id=school_id,
        parent_id=other_parent.id,
        period_id=period_id,
        status="paid",
        total_amount=Decimal("500.00"),
        currency="MAD",
        issued_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        reminder_sent_at=None,
        reminder_count=0,
        fee_structure_id=None,
    )

    page_one, cursor, has_more = await repo.list_invoices(
        school_id=school_id,
        role="PAR",
        user_id=parent_id,
        status="pending",
        cursor=None,
        limit=1,
        filters=FilterSpec(),
        sort=SortSpec(fields=[("id", "asc")]),
        search=None,
    )

    assert [invoice.id for invoice in page_one] == [base.id]
    assert cursor is not None
    assert has_more is True

    page_two, _, second_has_more = await repo.list_invoices(
        school_id=school_id,
        role="PAR",
        user_id=parent_id,
        status="pending",
        cursor=cursor,
        limit=10,
        filters=FilterSpec(),
        sort=SortSpec(fields=[("id", "asc")]),
        search=None,
    )

    assert [invoice.id for invoice in page_two] == [second.id]
    assert second_has_more is False


@pytest.mark.asyncio
async def test_payment_queries_support_idempotency_lookup_and_ordering(db_session):
    repo = BillingRepository(db_session)
    school_id, _, period_id, _, parent_id, _ = await _create_billing_context(
        db_session, 100
    )
    invoice = await repo.create_invoice(
        id=_uuid(110),
        school_id=school_id,
        parent_id=parent_id,
        period_id=period_id,
        status="pending",
        total_amount=Decimal("500.00"),
        currency="MAD",
        issued_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        reminder_sent_at=None,
        reminder_count=0,
        fee_structure_id=None,
    )
    first = await repo.create_payment(
        id=_uuid(111),
        school_id=school_id,
        invoice_id=invoice.id,
        parent_id=parent_id,
        idempotency_key="idem-111",
        status=PaymentAttemptStatus.PENDING.value,
        finalized_at=None,
        retry_count=0,
        next_retry_at=None,
        last_retry_error=None,
    )
    second = await repo.create_payment(
        id=_uuid(112),
        school_id=school_id,
        invoice_id=invoice.id,
        parent_id=parent_id,
        idempotency_key="idem-112",
        status=PaymentAttemptStatus.PENDING.value,
        finalized_at=None,
        retry_count=0,
        next_retry_at=None,
        last_retry_error=None,
    )

    fetched = await repo.get_payment_by_idempotency_key("idem-112")
    listed = await repo.list_payments(invoice_id=invoice.id)

    assert fetched is not None
    assert fetched.id == second.id
    assert {payment.id for payment in listed} == {first.id, second.id}


@pytest.mark.asyncio
async def test_invoice_item_creation_enforces_foreign_keys(db_session):
    repo = BillingRepository(db_session)

    with pytest.raises(IntegrityError):
        await repo.create_invoice_item(
            id=_uuid(120),
            invoice_id=_uuid(121),
            description="Invalid FK",
            amount=Decimal("100.00"),
            unit_price=Decimal("100.00"),
            quantity=1,
        )

    await db_session.rollback()
