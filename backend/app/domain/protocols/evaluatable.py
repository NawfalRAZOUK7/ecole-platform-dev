"""Protocol for any gradeable student work."""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class Evaluatable(Protocol):
    """Interface implemented by quiz, assignment, and assessment repositories."""

    async def list_for_class(
        self,
        school_id: UUID,
        class_id: UUID,
        *,
        status: str | None = None,
    ) -> list[dict]:
        """List all evaluatables for a class."""
        ...

    async def list_for_student(
        self,
        school_id: UUID,
        student_id: UUID,
    ) -> list[dict]:
        """List all evaluatables assigned to a student."""
        ...

    async def get_detail(self, item_id: UUID) -> dict | None:
        """Get full detail for one evaluatable."""
        ...

    async def get_results(self, item_id: UUID) -> list[dict]:
        """Get student results or submissions for one evaluatable."""
        ...
