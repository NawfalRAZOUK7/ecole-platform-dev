"""Unit tests for Money."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.value_objects.money import Money


class TestMoney:
    def test_valid_mad(self):
        money = Money(Decimal("100.00"), "MAD")

        assert money.amount == Decimal("100.00")
        assert money.currency == "MAD"

    def test_valid_zero(self):
        money = Money.zero()

        assert money.amount == Decimal("0.00")
        assert money.currency == "MAD"

    def test_valid_eur(self):
        assert Money(Decimal("50.00"), "EUR").currency == "EUR"

    def test_valid_usd(self):
        assert Money(Decimal("75.00"), "USD").currency == "USD"

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="Money cannot be negative"):
            Money(Decimal("-1.00"), "MAD")

    def test_currency_is_stored_verbatim(self):
        assert Money(Decimal("100.00"), "XXX").currency == "XXX"

    def test_decimal_precision_preserved(self):
        money = Money(Decimal("499.99"), "MAD")

        assert money.amount == Decimal("499.99")

    def test_large_amount(self):
        assert Money(Decimal("999999.99"), "MAD").amount == Decimal("999999.99")

    def test_from_float_quantizes_two_decimals(self):
        money = Money.from_float(123.456)

        assert money.amount == Decimal("123.46")
        assert money.currency == "MAD"

    def test_add_same_currency(self):
        result = Money(Decimal("100.00"), "MAD") + Money(Decimal("50.00"), "MAD")

        assert result == Money(Decimal("150.00"), "MAD")

    def test_subtract_same_currency(self):
        result = Money(Decimal("100.00"), "MAD") - Money(Decimal("50.00"), "MAD")

        assert result == Money(Decimal("50.00"), "MAD")

    def test_multiply_by_factor(self):
        result = Money(Decimal("50.00"), "MAD") * 2

        assert result == Money(Decimal("100.00"), "MAD")

    def test_add_different_currencies_raises(self):
        with pytest.raises(ValueError, match="Cannot add MAD \\+ EUR"):
            Money(Decimal("10.00"), "MAD") + Money(Decimal("5.00"), "EUR")

    def test_subtract_to_negative_raises(self):
        with pytest.raises(ValueError, match="Result would be negative"):
            Money(Decimal("10.00"), "MAD") - Money(Decimal("50.00"), "MAD")

    def test_str_formats_amount_and_currency(self):
        assert str(Money(Decimal("42.50"), "MAD")) == "42.50 MAD"
