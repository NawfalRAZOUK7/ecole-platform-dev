"""Additional value object tests to close coverage gaps."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.domain.value_objects.money import Money
from app.domain.value_objects.typed_id import SchoolId, UserId


class TestMoneyAdditional:
    def test_from_float_preserves_explicit_currency(self):
        money = Money.from_float(19.995, "EUR")

        assert money == Money(Decimal("20.00"), "EUR")

    def test_zero_preserves_explicit_currency(self):
        assert Money.zero("USD") == Money(Decimal("0.00"), "USD")

    def test_subtract_different_currencies_raises(self):
        with pytest.raises(ValueError, match="Cannot subtract MAD - EUR"):
            Money(Decimal("10.00"), "MAD") - Money(Decimal("5.00"), "EUR")

    @pytest.mark.parametrize(
        ("factor", "expected"),
        [
            (0, Decimal("0.00")),
            (1.5, Decimal("15.00")),
            ("2.345", Decimal("23.45")),
            (Decimal("3.333"), Decimal("33.33")),
        ],
    )
    def test_multiply_rounds_half_up(
        self,
        factor: int | float | str | Decimal,
        expected: Decimal,
    ):
        result = Money(Decimal("10.00"), "MAD") * factor

        assert result == Money(expected, "MAD")


class TestTypedIdAdditional:
    @pytest.mark.parametrize("typed_id_cls", [UserId, SchoolId])
    def test_from_str_round_trips_uuid(self, typed_id_cls):
        value = uuid.uuid4()

        typed_id = typed_id_cls.from_str(str(value))

        assert typed_id.value == value

    def test_user_id_str_returns_uuid_string(self):
        value = uuid.uuid4()

        assert str(UserId(value)) == str(value)

    def test_school_id_hash_matches_same_value(self):
        value = uuid.uuid4()

        assert hash(SchoolId(value)) == hash(SchoolId(value))

    def test_school_id_instances_work_in_sets(self):
        value = uuid.uuid4()
        ids = {SchoolId(value), SchoolId(value)}

        assert ids == {SchoolId(value)}

    def test_user_id_and_school_id_are_not_equal_even_with_same_uuid(self):
        value = uuid.uuid4()

        assert UserId(value) != SchoolId(value)
