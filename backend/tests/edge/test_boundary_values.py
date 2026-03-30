"""Boundary-value tests for numeric, string, Unicode, and pagination edges."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.core.response import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE, clamp_page_size, decode_cursor
from app.domain.value_objects.grade import MoroccanGrade
from app.models.billing import Invoice, InvoiceItem, SiblingDiscountPolicy
from app.models.iam import User
from app.schemas.billing import FeeAssignmentCreateRequest
from app.schemas.school import SchoolCreateRequest


class TestGradeBoundaries:
    @pytest.mark.parametrize(
        ("raw_value", "expected"),
        [
            (0, Decimal("0.00")),
            (20, Decimal("20.00")),
            (0.01, Decimal("0.01")),
            (19.99, Decimal("19.99")),
            (0.001, Decimal("0.00")),
        ],
    )
    def test_from_float_preserves_grade_boundaries(
        self,
        raw_value: float,
        expected: Decimal,
    ) -> None:
        grade = MoroccanGrade.from_float(raw_value)

        assert grade.value == expected

    def test_average_of_extreme_values_returns_boundary_midpoint(self) -> None:
        grade = MoroccanGrade.average(
            [
                MoroccanGrade.from_float(0),
                MoroccanGrade.from_float(20),
            ]
        )

        assert grade.value == Decimal("10.00")

    def test_average_empty_list_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Cannot average empty list"):
            MoroccanGrade.average([])


class TestInvoiceBoundaries:
    @pytest.mark.parametrize("amount", [0, 999999.99])
    def test_invoice_total_amount_accepts_numeric_boundaries(self, amount: float) -> None:
        invoice = Invoice()

        assert invoice.validate_total_amount("total_amount", amount) == amount

    @pytest.mark.parametrize(
        ("raw_currency", "expected"),
        [
            ("mad", "MAD"),
            (" eur ", "EUR"),
            ("usd", "USD"),
        ],
    )
    def test_invoice_currency_is_normalized(self, raw_currency: str, expected: str) -> None:
        invoice = Invoice()

        assert invoice.validate_currency("currency", raw_currency) == expected

    def test_invoice_item_allows_zero_amount(self) -> None:
        item = InvoiceItem()

        assert item.validate_amount("amount", 0.0) == 0.0


class TestDiscountBoundaries:
    @pytest.mark.parametrize("discount_percent", [0.0, 100.0])
    def test_fee_assignment_schema_accepts_discount_percent_boundaries(
        self,
        discount_percent: float,
    ) -> None:
        payload = FeeAssignmentCreateRequest(
            fee_structure_id="10000000-0000-4000-8000-000000000001",
            student_id="10000000-0000-4000-8000-000000000002",
            discount_percent=discount_percent,
        )

        assert payload.discount_percent == discount_percent

    @pytest.mark.parametrize("discount_percent", [-1.0, 101.0])
    def test_fee_assignment_schema_rejects_out_of_range_discount_percent(
        self,
        discount_percent: float,
    ) -> None:
        with pytest.raises(PydanticValidationError):
            FeeAssignmentCreateRequest(
                fee_structure_id="10000000-0000-4000-8000-000000000001",
                student_id="10000000-0000-4000-8000-000000000002",
                discount_percent=discount_percent,
            )

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("second_child_percent", 0.0),
            ("second_child_percent", 100.0),
            ("third_child_percent", 0.0),
            ("third_child_percent", 100.0),
            ("fourth_plus_percent", 0.0),
            ("fourth_plus_percent", 100.0),
        ],
    )
    def test_sibling_discount_policy_accepts_extreme_percentages(
        self,
        field_name: str,
        value: float,
    ) -> None:
        policy = SiblingDiscountPolicy()

        assert policy.validate_discount_percent(field_name, value) == value


class TestStringAndUnicodeBoundaries:
    @pytest.mark.parametrize("raw_email", ["", "   "])
    def test_user_rejects_empty_email(self, raw_email: str) -> None:
        user = User()

        with pytest.raises(ValueError, match="Invalid email format"):
            user.validate_email("email", raw_email)

    @pytest.mark.parametrize("raw_phone", ["", "   "])
    def test_user_rejects_empty_phone(self, raw_phone: str) -> None:
        user = User()

        with pytest.raises(ValueError, match="Phone must start with country code"):
            user.validate_phone("phone", raw_phone)

    def test_school_create_request_rejects_empty_name(self) -> None:
        with pytest.raises(PydanticValidationError):
            SchoolCreateRequest(name="", code="SCH-EDGE-001")

    def test_school_create_request_accepts_255_character_name(self) -> None:
        payload = SchoolCreateRequest(name="N" * 255, code="SCH-EDGE-002")

        assert len(payload.name) == 255

    def test_school_create_request_rejects_256_character_name(self) -> None:
        with pytest.raises(PydanticValidationError):
            SchoolCreateRequest(name="N" * 256, code="SCH-EDGE-003")

    def test_school_create_request_accepts_500_character_website(self) -> None:
        website = f"https://{('a' * 489)}.ma"
        payload = SchoolCreateRequest(
            name="Edge School",
            code="SCH-EDGE-004",
            website=website,
        )

        assert payload.website == website

    def test_school_create_request_rejects_501_character_website(self) -> None:
        website = f"https://{('a' * 490)}.ma"

        with pytest.raises(PydanticValidationError):
            SchoolCreateRequest(
                name="Edge School",
                code="SCH-EDGE-005",
                website=website,
            )

    @pytest.mark.parametrize(
        ("name", "code"),
        [
            ("أحمد المغربي", "SCH-AR-001"),
            ("Francois Cote", "SCH-FR-ASCII-001"),
            ("François Côté", "SCH-FR-001"),
        ],
    )
    def test_school_create_request_accepts_unicode_names(self, name: str, code: str) -> None:
        payload = SchoolCreateRequest(
            name=name,
            code=code,
            city="Casablanca",
            email="contact@example.ma",
        )

        assert payload.name == name


class TestPaginationBoundaries:
    def test_clamp_page_size_defaults_when_limit_missing(self) -> None:
        assert clamp_page_size(None) == DEFAULT_PAGE_SIZE

    def test_clamp_page_size_raises_small_limit_to_one(self) -> None:
        assert clamp_page_size(0) == 1

    def test_clamp_page_size_caps_large_limit(self) -> None:
        assert clamp_page_size(1000) == MAX_PAGE_SIZE

    def test_decode_cursor_rejects_invalid_cursor_payload(self) -> None:
        with pytest.raises(ValueError, match="Invalid cursor"):
            decode_cursor("invalid")

    def test_decode_cursor_rejects_non_uuid_base64_payload(self) -> None:
        bad_payload = base64.urlsafe_b64encode(b"not-a-uuid|sort").decode()

        with pytest.raises(ValueError, match="Invalid cursor"):
            decode_cursor(bad_payload)

    def test_boundary_inputs_do_not_mutate_default_timezone_expectation(self) -> None:
        payload = SchoolCreateRequest(
            name="Boundary School",
            code="SCH-EDGE-006",
            subscription_expires_at=datetime(2026, 3, 30, tzinfo=timezone.utc),
        )

        assert payload.timezone == "Africa/Casablanca"
