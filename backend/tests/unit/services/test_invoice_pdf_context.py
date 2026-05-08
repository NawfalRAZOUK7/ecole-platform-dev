"""Unit tests for ReportsService._invoice_pdf_context()."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.reports import ReportsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_job(*, locale: str = "fr", invoice_id: str | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        school_id=uuid.uuid4(),
        type="invoice_pdf",
        parameters={
            "invoice_id": invoice_id or str(uuid.uuid4()),
            "locale": locale,
        },
    )


def _make_item(
    *,
    amount_ht: float = 2500.0,
    tva_rate: float = 20.0,
    tva_amount: float = 500.0,
    amount_ttc: float = 3000.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        description="Frais de scolarite",
        quantity=1,
        unit_price=Decimal(str(amount_ht)),
        amount_ht=Decimal(str(amount_ht)),
        tva_rate=Decimal(str(tva_rate)),
        tva_amount=Decimal(str(tva_amount)),
        amount_ttc=Decimal(str(amount_ttc)),
    )


def _make_invoice(
    *,
    parent_id: uuid.UUID | None = None,
    items: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        parent_id=parent_id or uuid.uuid4(),
        issued_date=date(2026, 2, 1),
        due_date=date(2026, 2, 28),
        status="pending",
        total_amount=Decimal("3000.00"),
        currency="MAD",
        items=items if items is not None else [_make_item()],
    )


def _make_school() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="Ecole Benani",
        name_ar="مدرسة بناني",
        address="123 Rue Hassan II",
        city="Casablanca",
        region="Grand Casablanca",
        phone="+212522000000",
        email="contact@ecole-benani.ma",
        logo_path=None,
        rib=None,
        iban=None,
        bic=None,
        bank_name=None,
        tva_number=None,
        tax_id=None,
        brand_color=None,
        footer_text=None,
        stamp_image_url=None,
        signature_image_url=None,
    )


def _make_parent() -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        full_name="Parent Alaoui",
        email="parent.alaoui@gmail.com",
    )


def _setup_service(
    *,
    invoice: SimpleNamespace | None = None,
    school: SimpleNamespace | None = None,
    parent: SimpleNamespace | None = None,
) -> ReportsService:
    service = ReportsService(AsyncMock())
    service.billing_repo = AsyncMock()
    service.school_repo = AsyncMock()
    service.repo = AsyncMock()
    service.billing_repo.get_invoice_by_id.return_value = invoice
    service.school_repo.get_school.return_value = school
    service.repo.get_user_in_school.return_value = parent
    return service


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestInvoicePdfContext:
    @pytest.mark.asyncio
    async def test_returns_all_required_keys(self) -> None:
        service = _setup_service(
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._invoice_pdf_context(_make_job())

        required = {
            "lang",
            "is_rtl",
            "school",
            "invoice",
            "items",
            "parent",
            "totals",
            "generated_at",
            "report_title",
        }
        assert required.issubset(ctx.keys())

    @pytest.mark.asyncio
    async def test_lang_fr_and_ltr_by_default(self) -> None:
        service = _setup_service(
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._invoice_pdf_context(_make_job(locale="fr"))

        assert ctx["lang"] == "fr"
        assert ctx["is_rtl"] is False

    @pytest.mark.asyncio
    async def test_lang_ar_sets_rtl_true(self) -> None:
        service = _setup_service(
            invoice=_make_invoice(),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._invoice_pdf_context(_make_job(locale="ar"))

        assert ctx["lang"] == "ar"
        assert ctx["is_rtl"] is True

    @pytest.mark.asyncio
    async def test_tva_breakdown_summed_correctly(self) -> None:
        item1 = _make_item(amount_ht=1000.0, tva_amount=200.0, amount_ttc=1200.0)
        item2 = _make_item(amount_ht=500.0, tva_amount=100.0, amount_ttc=600.0)
        service = _setup_service(
            invoice=_make_invoice(items=[item1, item2]),
            school=_make_school(),
            parent=_make_parent(),
        )

        ctx = await service._invoice_pdf_context(_make_job())

        assert ctx["totals"]["ht"] == pytest.approx(1500.0)
        assert ctx["totals"]["tva"] == pytest.approx(300.0)
        assert ctx["totals"]["ttc"] == pytest.approx(1800.0)
        # items list mirrors line-item breakdown
        assert len(ctx["items"]) == 2
        assert ctx["items"][0]["amount_ht"] == pytest.approx(1000.0)
        assert ctx["items"][1]["tva_amount"] == pytest.approx(100.0)

    @pytest.mark.asyncio
    async def test_parent_fields_in_context(self) -> None:
        parent = _make_parent()
        service = _setup_service(
            invoice=_make_invoice(),
            school=_make_school(),
            parent=parent,
        )

        ctx = await service._invoice_pdf_context(_make_job())

        assert ctx["parent"]["full_name"] == parent.full_name
        assert ctx["parent"]["email"] == parent.email
        assert ctx["parent"]["id"] == str(parent.id)

    @pytest.mark.asyncio
    async def test_school_fields_in_context(self) -> None:
        school = _make_school()
        service = _setup_service(
            invoice=_make_invoice(),
            school=school,
            parent=_make_parent(),
        )

        ctx = await service._invoice_pdf_context(_make_job())

        assert ctx["school"]["name"] == school.name
        assert ctx["school"]["email"] == school.email
        assert ctx["school"]["city"] == school.city

    @pytest.mark.asyncio
    async def test_raises_not_found_when_invoice_missing(self) -> None:
        service = _setup_service(
            invoice=None, school=_make_school(), parent=_make_parent()
        )

        with pytest.raises(NotFoundError):
            await service._invoice_pdf_context(_make_job())

    @pytest.mark.asyncio
    async def test_raises_not_found_when_school_missing(self) -> None:
        service = _setup_service(
            invoice=_make_invoice(), school=None, parent=_make_parent()
        )

        with pytest.raises(NotFoundError):
            await service._invoice_pdf_context(_make_job())

    @pytest.mark.asyncio
    async def test_raises_not_found_when_parent_missing(self) -> None:
        service = _setup_service(
            invoice=_make_invoice(), school=_make_school(), parent=None
        )

        with pytest.raises(NotFoundError):
            await service._invoice_pdf_context(_make_job())
