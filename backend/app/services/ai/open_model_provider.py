"""Free / self-hosted open-model provider (OpenAI-compatible) with mock fallback.

Talks to any OpenAI-compatible chat endpoint — Ollama, LM Studio, vLLM,
llama.cpp server, etc. — so you can run a free open model yourself with no
per-call cost and no paid API key. Activate by setting AI_OPEN_BASE_URL (and
optionally AI_OPEN_MODEL / AI_OPEN_API_KEY).

Like ClaudeProvider, every method degrades safely to the MockProvider on any
failure, so a missing/offline endpoint never breaks the app.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_base import Recommendation, WritingFeedback

logger = logging.getLogger(__name__)

try:  # pragma: no cover - optional dependency
    import httpx
except ImportError:  # pragma: no cover - dependency is optional
    httpx = None


class OpenModelProvider:
    """Real provider for a free/self-hosted OpenAI-compatible model."""

    def __init__(self, base_url: str, model: str = "", api_key: str = "") -> None:
        self._base_url = (base_url or "").rstrip("/")
        self._model = model or "local-model"
        self._api_key = api_key or ""
        self._fallback = MockProvider()
        self._enabled = bool(httpx is not None and self._base_url)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def complete(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        if not self._enabled:
            return await self._fallback.complete(prompt, system, max_tokens=max_tokens)
        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or [{}]
                text = (choices[0].get("message") or {}).get("content", "") or ""
                text = text.strip()
                return text or await self._fallback.complete(
                    prompt, system, max_tokens=max_tokens
                )
        except Exception:
            logger.exception("OpenModelProvider complete() failed, using mock fallback")
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
        words = [word for word in text.split() if word.strip()]
        word_count = len(words)
        try:
            result = await self.complete(prompt, system, max_tokens=500)
            parsed = json.loads(result)
            suggestion = parsed.get("suggestion")
            hints = parsed.get("hints") or []
            if isinstance(suggestion, str) and isinstance(hints, list):
                return {
                    "suggestion": suggestion,
                    "hints": [str(item) for item in hints[:3]],
                    "word_count": word_count,
                }
        except Exception:
            logger.exception("OpenModelProvider analyze_writing() failed, using mock")
        return await self._fallback.analyze_writing(text, language)

    async def generate_recommendations(
        self,
        student_data: dict[str, Any],
        language: str | None = None,
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
                "OpenModelProvider generate_recommendations() failed, using mock"
            )
        return await self._fallback.generate_recommendations(
            student_data, language=language
        )

    async def compute_kpi_insights(self, metrics: dict[str, Any]) -> list[str]:
        prompt = (
            "Review these KPI metrics and return a JSON array of up to 4 concise "
            "operational insights.\n\n"
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
                "OpenModelProvider compute_kpi_insights() failed, using mock"
            )
        return await self._fallback.compute_kpi_insights(metrics)
