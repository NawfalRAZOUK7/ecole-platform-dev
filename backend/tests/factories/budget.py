"""Budget factories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import factory

from app.models.budget import (
    BudgetAllocation,
    BudgetAllocationStatus,
    BudgetRequest,
    BudgetRequestStatus,
    BudgetTransaction,
    BudgetTransactionType,
    MicroBudget,
    MicroBudgetStatus,
)
from tests.factories.base import AsyncSQLAlchemyFactory
from tests.factories.erp import AcademicYearFactory, ClassFactory
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory


def _utc_now() -> datetime:
    return datetime.now(UTC)


class MicroBudgetFactory(AsyncSQLAlchemyFactory):
    """Factory for school budgets."""

    class Meta:
        model = MicroBudget
        exclude = ("school", "academic_year", "creator")

    id = factory.LazyFunction(uuid.uuid4)
    school = factory.SubFactory(SchoolFactory)
    academic_year = factory.SubFactory(
        AcademicYearFactory,
        school=factory.SelfAttribute("..school"),
    )
    creator = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..school"))
    school_id = factory.LazyAttribute(lambda o: o.school.id)
    academic_year_id = factory.LazyAttribute(lambda o: o.academic_year.id)
    total_amount = Decimal("10000.00")
    allocated_amount = Decimal("0.00")
    remaining_amount = Decimal("10000.00")
    currency = "MAD"
    status = MicroBudgetStatus.ACTIVE.value
    created_by = factory.LazyAttribute(lambda o: o.creator.id)


class BudgetAllocationFactory(AsyncSQLAlchemyFactory):
    """Factory for budget allocations."""

    class Meta:
        model = BudgetAllocation
        exclude = ("budget", "school_class", "teacher", "allocator")

    id = factory.LazyFunction(uuid.uuid4)
    budget = factory.SubFactory(MicroBudgetFactory)
    school_class = factory.SubFactory(
        ClassFactory,
        school=factory.SelfAttribute("..budget.school"),
        academic_year=factory.SelfAttribute("..budget.academic_year"),
    )
    teacher = factory.SubFactory(UserFactory, school=factory.SelfAttribute("..budget.school"))
    allocator = factory.LazyAttribute(lambda o: o.budget.creator)
    budget_id = factory.LazyAttribute(lambda o: o.budget.id)
    class_id = factory.LazyAttribute(lambda o: o.school_class.id)
    teacher_id = factory.LazyAttribute(lambda o: o.teacher.id)
    label = factory.Sequence(lambda n: f"Budget Classe {n + 1}")
    amount = Decimal("2500.00")
    spent = Decimal("0.00")
    remaining = Decimal("2500.00")
    currency = "MAD"
    allocated_by = factory.LazyAttribute(lambda o: o.allocator.id)
    allocated_at = factory.LazyFunction(_utc_now)
    status = BudgetAllocationStatus.ACTIVE.value


class BudgetRequestFactory(AsyncSQLAlchemyFactory):
    """Factory for budget requests."""

    class Meta:
        model = BudgetRequest
        exclude = ("allocation", "requester", "reviewer")

    id = factory.LazyFunction(uuid.uuid4)
    allocation = factory.SubFactory(BudgetAllocationFactory)
    requester = factory.LazyAttribute(lambda o: o.allocation.teacher)
    reviewer = factory.LazyAttribute(lambda o: o.allocation.allocator)
    allocation_id = factory.LazyAttribute(lambda o: o.allocation.id)
    requester_id = factory.LazyAttribute(lambda o: o.requester.id)
    amount = Decimal("350.00")
    currency = "MAD"
    description = "Achat de fournitures"
    justification = "Materiel manquant pour le projet"
    status = BudgetRequestStatus.PENDING.value
    reviewed_by = None
    reviewed_at = None
    review_comment = None


class BudgetTransactionFactory(AsyncSQLAlchemyFactory):
    """Factory for budget transactions."""

    class Meta:
        model = BudgetTransaction
        exclude = ("allocation", "request", "recorder")

    id = factory.LazyFunction(uuid.uuid4)
    allocation = factory.SubFactory(BudgetAllocationFactory)
    request = factory.SubFactory(
        BudgetRequestFactory,
        allocation=factory.SelfAttribute("..allocation"),
    )
    recorder = factory.LazyAttribute(lambda o: o.allocation.allocator)
    allocation_id = factory.LazyAttribute(lambda o: o.allocation.id)
    request_id = factory.LazyAttribute(lambda o: o.request.id)
    amount = Decimal("350.00")
    transaction_type = BudgetTransactionType.EXPENSE.value
    description = "Achat de peinture"
    receipt_url = factory.LazyFunction(lambda: f"https://cdn.ecole.ma/{uuid.uuid4().hex}.pdf")
    recorded_by = factory.LazyAttribute(lambda o: o.recorder.id)
    recorded_at = factory.LazyFunction(_utc_now)


__all__ = [
    "MicroBudgetFactory",
    "BudgetAllocationFactory",
    "BudgetRequestFactory",
    "BudgetTransactionFactory",
]
