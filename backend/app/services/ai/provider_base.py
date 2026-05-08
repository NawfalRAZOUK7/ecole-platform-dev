"""Provider protocol for pluggable AI backends."""

from __future__ import annotations

from typing import Any, Protocol, TypedDict


class WritingFeedback(TypedDict):
    suggestion: str | None
    hints: list[str]
    word_count: int


class Recommendation(TypedDict, total=False):
    title: str
    reason_code: str
    priority: str
    content_type: str | None


class AIProvider(Protocol):
    """Provider interface shared by mock and real model backends."""

    async def complete(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        """Return a plain-text completion."""

    async def analyze_writing(self, text: str, language: str) -> WritingFeedback:
        """Return writing feedback with a suggestion and short hints."""

    async def generate_recommendations(
        self,
        student_data: dict[str, Any],
        language: str | None = None,
    ) -> list[Recommendation]:
        """Return structured learning recommendations."""

    async def compute_kpi_insights(self, metrics: dict[str, Any]) -> list[str]:
        """Return short narrative KPI insights."""
