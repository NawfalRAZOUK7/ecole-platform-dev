"""Anthropic Claude provider with mock fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_base import Recommendation, WritingFeedback

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import anthropic
except ImportError:  # pragma: no cover - dependency is optional
    anthropic = None


class ClaudeProvider:
    """Real Claude provider with safe fallback to the mock provider."""

    # Activate by setting AI_PROVIDER=claude and AI_API_KEY in .env
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514") -> None:
        self._api_key = api_key
        self._model = model or "claude-sonnet-4-20250514"
        self._fallback = MockProvider()
        self._client = (
            anthropic.AsyncAnthropic(api_key=api_key)
            if anthropic is not None and api_key
            else None
        )

    def _extract_text(self, response: Any) -> str:
        parts = []
        for item in getattr(response, "content", []) or []:
            text = getattr(item, "text", None)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()

    async def complete(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        if self._client is None:
            return await self._fallback.complete(prompt, system, max_tokens=max_tokens)
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            text = self._extract_text(response)
            return text or await self._fallback.complete(
                prompt, system, max_tokens=max_tokens
            )
        except Exception:
            logger.exception("Claude complete() failed, using mock fallback")
            return await self._fallback.complete(prompt, system, max_tokens=max_tokens)

    async def analyze_writing(self, text: str, language: str) -> WritingFeedback:
        prompt = (
            "Analyze the following student writing and return JSON with keys "
            '"suggestion" (string) and "hints" (array of up to 3 strings).\n\n'
            f"Language: {language}\nText:\n{text}"
        )
        system = (
            "You are a pedagogical writing assistant for a K-12 school in Morocco. "
            "Respond with strict JSON only."
        )
        try:
            result = await self.complete(prompt, system, max_tokens=500)
            parsed = json.loads(result)
            suggestion = parsed.get("suggestion")
            hints = parsed.get("hints") or []
            if isinstance(suggestion, str) and isinstance(hints, list):
                return {
                    "suggestion": suggestion,
                    "hints": [str(item) for item in hints[:3]],
                }
        except Exception:
            logger.exception("Claude analyze_writing() failed, using mock fallback")
        return await self._fallback.analyze_writing(text, language)

    async def generate_recommendations(
        self,
        student_data: dict[str, Any],
    ) -> list[Recommendation]:
        prompt = (
            "Generate up to 3 student recommendations as JSON array. "
            "Each item must contain title, reason_code, priority, and content_type.\n\n"
            f"Student data:\n{json.dumps(student_data, ensure_ascii=False)}"
        )
        system = (
            "You are an educational recommendation engine for a Moroccan K-12 platform. "
            "Respond with strict JSON only."
        )
        try:
            result = await self.complete(prompt, system, max_tokens=700)
            parsed = json.loads(result)
            if isinstance(parsed, list) and parsed:
                cleaned: list[Recommendation] = []
                for item in parsed[:3]:
                    if not isinstance(item, dict):
                        continue
                    cleaned.append(
                        {
                            "title": str(item.get("title") or "").strip(),
                            "reason_code": str(item.get("reason_code") or "").strip(),
                            "priority": str(item.get("priority") or "medium").strip(),
                            "content_type": (
                                str(item.get("content_type")).strip()
                                if item.get("content_type") is not None
                                else None
                            ),
                        }
                    )
                if cleaned and all(
                    item["title"] and item["reason_code"] for item in cleaned
                ):
                    return cleaned
        except Exception:
            logger.exception(
                "Claude generate_recommendations() failed, using mock fallback"
            )
        return await self._fallback.generate_recommendations(student_data)

    async def compute_kpi_insights(self, metrics: dict[str, Any]) -> list[str]:
        prompt = (
            "Review these KPI metrics and return a JSON array of up to 4 concise operational insights.\n\n"
            f"Metrics:\n{json.dumps(metrics, ensure_ascii=False)}"
        )
        system = (
            "You are an analytics copilot for a school platform. "
            "Return actionable, concise insights as strict JSON."
        )
        try:
            result = await self.complete(prompt, system, max_tokens=500)
            parsed = json.loads(result)
            if isinstance(parsed, list) and parsed:
                return [str(item) for item in parsed[:4] if str(item).strip()]
        except Exception:
            logger.exception(
                "Claude compute_kpi_insights() failed, using mock fallback"
            )
        return await self._fallback.compute_kpi_insights(metrics)
