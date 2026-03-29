"""Unit tests for MoroccanGrade."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.value_objects.grade import MoroccanGrade


class TestMoroccanGrade:
    def test_valid_grade_zero(self):
        assert MoroccanGrade(0).value == 0

    def test_valid_grade_twenty(self):
        assert MoroccanGrade(20).value == 20

    def test_valid_grade_decimal(self):
        assert MoroccanGrade(Decimal("15.75")).value == Decimal("15.75")

    def test_invalid_negative(self):
        with pytest.raises(ValueError, match="Grade must be 0-20"):
            MoroccanGrade(-1)

    def test_invalid_above_twenty(self):
        with pytest.raises(ValueError, match="Grade must be 0-20"):
            MoroccanGrade(21)

    def test_invalid_large_number(self):
        with pytest.raises(ValueError, match="Grade must be 0-20"):
            MoroccanGrade(100)

    @pytest.mark.parametrize(
        ("score", "expected_mention"),
        [
            (Decimal("20"), "Très Bien"),
            (Decimal("16"), "Très Bien"),
            (Decimal("15.99"), "Bien"),
            (Decimal("14"), "Bien"),
            (Decimal("13.99"), "Assez Bien"),
            (Decimal("12"), "Assez Bien"),
            (Decimal("11.99"), "Passable"),
            (Decimal("10"), "Passable"),
            (Decimal("9.99"), "Insuffisant"),
            (Decimal("0"), "Insuffisant"),
        ],
    )
    def test_mention_boundaries(self, score: Decimal, expected_mention: str):
        assert MoroccanGrade(score).mention == expected_mention

    def test_from_float_quantizes_two_decimals(self):
        grade = MoroccanGrade.from_float(15.756)

        assert grade.value == Decimal("15.76")

    def test_average_returns_two_decimal_grade(self):
        grade = MoroccanGrade.average(
            [
                MoroccanGrade(Decimal("12.50")),
                MoroccanGrade(Decimal("15.00")),
                MoroccanGrade(Decimal("17.50")),
            ]
        )

        assert grade.value == Decimal("15.00")
        assert grade.mention == "Bien"

    def test_average_empty_list_raises(self):
        with pytest.raises(ValueError, match="Cannot average empty list"):
            MoroccanGrade.average([])

    def test_float_cast_returns_native_float(self):
        assert float(MoroccanGrade(Decimal("14.25"))) == 14.25

    def test_str_formats_out_of_twenty(self):
        assert str(MoroccanGrade(Decimal("18.50"))) == "18.50/20"
