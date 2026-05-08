"""Unit tests for ReportsService._payment_receipt_context()."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.reports import ReportsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(*, locale: str = "fr", payment_id: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        type="payment_receipt",
        parameters={
            "payment_id": payment_id or str(uuid.uuid4()),
            "locale": locale,
        },
    )


def _make_payment(*, invoice_id: uuid.UUID | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        invoice_id=invoice_id or uuid.uuid4(),
        parent_id=uuid.uuid4(),
        amount=Decimal("3000.00"),
        method="card",
        transaction_reference="TXN-20260201-001",
        status="succeeded",
        finalized_at=datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
    )


def _make_invoice() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        issued_date=date(2026, 2, 1),
        total_amount=Decimal("3000.00"),
        currency="MAD",
    )


def _make_school() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Ecole Benani",
        address="123 Rue Hassan II",
        phone="+212522000000",
        email="contact@ecole-benani.ma",
        rib=None,
        iban=None,
        bic=None,
        bank_name=None,
    )


def _make_parent() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        full_name="Parent Alaoui",
        email="parent.alaoui@gmail.com",
    )


def _setup_service(
    *,
    payment: SimpleNamespace | None = None,
    invoice: SimpleNamespace | None = None,
    school: SimpleNamespace | None = None,
    parent: SimpleNamespace | None = None,
) -> ReportsService:
    service = ReportsService(AsyncMock())
    service.billing_repo = AsyncMock()
    service.school_repo = AsyncMock()
    service.repo = AsyncMock()
    service.billing_repo.get_payment_by_id.return_value = payment
    service.billing_repo.get_invoice_by_id.return_value = invoice
    service.school_repo.get_school.return_value = school
    service.repo.get_user_in_school.return_value = parent
    return service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPaymentReceiptContext:
    @pytest.mark.asyncio
    async def test_returns_all_required_keys(self) -> None:
        payment = _make_payment()
        service = _setup_service(
            payment=payment,
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._payment_receipt_context(_make_job())

        required = {
            "lang",
            "is_rtl",
            "school",
            "payment",
            "invoice",
            "parent",
            "generated_at",
            "report_title",
        }
        assert required.issubset(ctx.keys())

    @pytest.mark.asyncio
    async def test_lang_fr_and_ltr_by_default(self) -> None:
        service = _setup_service(
            payment=_make_payment(),
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._payment_receipt_context(_make_job(locale="fr"))

        assert ctx["lang"] == "fr"
        assert ctx["is_rtl"] is False

    @pytest.mark.asyncio
    async def test_lang_ar_sets_rtl_true(self) -> None:
        service = _setup_service(
            payment=_make_payment(),
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._payment_receipt_context(_make_job(locale="ar"))

        assert ctx["lang"] == "ar"
        assert ctx["is_rtl"] is True

    @pytest.mark.asyncio
    async def test_payment_fields_in_context(self) -> None:
        payment = _make_payment()
        service = _setup_service(
            payment=payment,
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._payment_receipt_context(_make_job())

        assert ctx["payment"]["id"] == str(payment.id)
        assert ctx["payment"]["amount"] == pytest.approx(float(payment.amount))
        assert ctx["payment"]["method"] == payment.method
        assert ctx["payment"]["status"] == payment.status
        assert ctx["payment"]["receipt_number"].startswith("RCP-")

    @pytest.mark.asyncio
    async def test_invoice_reference_in_context(self) -> None:
        invoice = _make_invoice()
        payment = _make_payment(invoice_id=invoice.id)
        service = _setup_service(
            payment=payment,
            invoice=invoice,
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._payment_receipt_context(_make_job())

        assert ctx["invoice"]["id"] == str(invoice.id)
        assert ctx["invoice"]["total_amount"] == pytest.approx(
            float(invoice.total_amount)
        )
        assert ctx["invoice"]["currency"] == invoice.currency

    @pytest.mark.asyncio
    async def test_parent_fields_in_context(self) -> None:
        parent = _make_parent()
        service = _setup_service(
            payment=_make_payment(),
            invoice=_make_invoice(),
            school=_make_school(),
            parent=parent,
        )

        ctx = await service._payment_receipt_context(_make_job())

        assert ctx["parent"]["full_name"] == parent.full_name
        assert ctx["parent"]["email"] == parent.email

    @pytest.mark.asyncio
    async def test_raises_not_found_when_payment_missing(self) -> None:
        service = _setup_service(
            payment=None,
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        with pytest.raises(NotFoundError):
            await service._payment_receipt_context(_make_job())

    @pytest.mark.asyncio
    async def test_raises_not_found_when_invoice_missing(self) -> None:
        service = _setup_service(
            payment=_make_payment(),
            invoice=None,
            school=_make_school(),
            parent=_make_parent(),
        )

        with pytest.raises(NotFoundError):
            await service._payment_receipt_context(_make_job())

    @pytest.mark.asyncio
    async def test_raises_not_found_when_school_missing(self) -> None:
        service = _setup_service(
            payment=_make_payment(),
            invoice=_make_invoice(),
            school=None,
            parent=_make_parent(),
        )

        with pytest.raises(NotFoundError):
            await service._payment_receipt_context(_make_job())

    @pytest.mark.asyncio
    async def test_raises_not_found_when_parent_missing(self) -> None:
        service = _setup_service(
            payment=_make_payment(),
            invoice=_make_invoice(),
            school=_make_school(),
            parent=None,
        )

        with pytest.raises(NotFoundError):
            await service._payment_receipt_context(_make_job())
