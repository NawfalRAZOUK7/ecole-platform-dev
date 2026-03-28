"""Moroccan grading scale (0-20)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True, slots=True)
class MoroccanGrade:
    """Immutable grade value on the 0-20 Moroccan scale."""

    value: Decimal

    def __post_init__(self) -> None:
        if not (Decimal("0") <= self.value <= Decimal("20")):
            raise ValueError(f"Grade must be 0-20, got {self.value}")

    @classmethod
    def from_float(cls, v: float) -> MoroccanGrade:
        return cls(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    @classmethod
    def average(cls, grades: list[MoroccanGrade]) -> MoroccanGrade:
        if not grades:
            raise ValueError("Cannot average empty list")
        total = sum(g.value for g in grades)
        avg = (total / len(grades)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return cls(avg)

    @property
    def mention(self) -> str:
        """Moroccan mention based on grade."""
        if self.value >= Decimal("16"):
            return "Très Bien"
        if self.value >= Decimal("14"):
            return "Bien"
        if self.value >= Decimal("12"):
            return "Assez Bien"
        if self.value >= Decimal("10"):
            return "Passable"
        return "Insuffisant"

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return f"{self.value}/20"
