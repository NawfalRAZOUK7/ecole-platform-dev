"""Moroccan Dirham money value object."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass(frozen=True, slots=True)
class Money:
    """Immutable monetary value in MAD (Moroccan Dirham)."""

    amount: Decimal
    currency: str = "MAD"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError(f"Money cannot be negative: {self.amount}")

    @classmethod
    def from_float(cls, v: float, currency: str = "MAD") -> Money:
        return cls(
            Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            currency,
        )

    @classmethod
    def zero(cls, currency: str = "MAD") -> Money:
        return cls(Decimal("0.00"), currency)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} + {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} - {other.currency}")
        result = self.amount - other.amount
        if result < Decimal("0"):
            raise ValueError("Result would be negative")
        return Money(result, self.currency)

    def __mul__(self, factor: int | float | Decimal) -> Money:
        result = (self.amount * Decimal(str(factor))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return Money(result, self.currency)

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
