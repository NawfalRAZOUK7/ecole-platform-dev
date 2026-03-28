"""Typed UUID wrappers to prevent ID mixups."""

from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> UserId:
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class SchoolId:
    value: uuid.UUID

    @classmethod
    def from_str(cls, s: str) -> SchoolId:
        return cls(uuid.UUID(s))

    def __str__(self) -> str:
        return str(self.value)
