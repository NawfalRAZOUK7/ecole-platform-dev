"""Unit tests for AI service and provider factory.

Tests provider factory logic, MockProvider responses, prompt templates,
and metrics emission without network calls.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.ai.ai_service import (
    AIRequestType,
    AIRequestStatus,
    _sanitize_for_logging,
)
from app.services.ai.provider_factory import create_ai_provider
from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_base import WritingFeedback


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
class TestProviderFactory:
    """Tests for create_ai_provider factory function."""

    def test_default_returns_mock_provider(self) -> None:
        settings = MagicMock()
        settings.ai_provider = None
        settings.ai_api_key = None
        settings.ai_model = None
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockProvider)

    def test_claude_without_api_key_returns_mock(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "claude"
        settings.ai_api_key = ""
        settings.ai_model = "claude-sonnet"
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockProvider)

    def test_claude_with_api_key_returns_claude_provider(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "claude"
        settings.ai_api_key = "sk-ant-api03-test"
        settings.ai_model = "claude-sonnet-4-20250514"
        provider = create_ai_provider(settings)
        assert type(provider).__name__ == "ClaudeProvider"

    def test_explicit_mock_provider(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "mock"
        settings.ai_api_key = None
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockProvider)


# ---------------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------------
class TestMockProvider:
    """Tests for the default mock AI provider."""

    @pytest.fixture
    def provider(self) -> MockProvider:
        return MockProvider()

    @pytest.mark.asyncio
    async def test_complete_returns_string(self, provider: MockProvider) -> None:
        result = await provider.complete(
            prompt="What are the grades?",
            system="You are a helpful assistant",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_complete_french_detection(self, provider: MockProvider) -> None:
        result = await provider.complete(
            prompt="Quelles sont les notes?",
            system="Assistant",
        )
        assert "résultats" in result.lower() or "progression" in result.lower()

    @pytest.mark.asyncio
    async def test_complete_arabic_detection(self, provider: MockProvider) -> None:
        result = await provider.complete(
            prompt="ما هي النتائج؟",
            system="مساعد",
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_complete_english_fallback(self, provider: MockProvider) -> None:
        result = await provider.complete(
            prompt="How is attendance?",
            system="Assistant",
        )
        assert "attendance" in result.lower() or "summary" in result.lower()

    @pytest.mark.asyncio
    async def test_analyze_writing_short_text(self, provider: MockProvider) -> None:
        feedback = await provider.analyze_writing(
            text="Short text.",
            language="en",
        )
        assert isinstance(feedback, WritingFeedback)
        assert feedback.word_count < 20
        assert len(feedback.suggestions) > 0

    @pytest.mark.asyncio
    async def test_analyze_writing_long_text(self, provider: MockProvider) -> None:
        text = " ".join(["word"] * 100)
        feedback = await provider.analyze_writing(text=text, language="en")
        assert isinstance(feedback, WritingFeedback)
        assert feedback.word_count == 100

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, provider: MockProvider) -> None:
        recs = await provider.generate_recommendations(
            student_data={"grade": "CP", "subjects": ["math"]},
            language="en",
        )
        assert isinstance(recs, list)
        assert len(recs) > 0
        assert all(hasattr(r, "title") for r in recs)

    def test_resolve_language_explicit(self, provider: MockProvider) -> None:
        assert provider._resolve_language("fr", "hello") == "fr"
        assert provider._resolve_language("ar", "hello") == "ar"
        assert provider._resolve_language("en", "hello") == "en"

    def test_resolve_language_from_arabic_text(self, provider: MockProvider) -> None:
        assert provider._resolve_language(None, "مرحبا") == "ar"

    def test_resolve_language_from_french_text(self, provider: MockProvider) -> None:
        assert provider._resolve_language(None, "le test pour la classe") == "fr"


# ---------------------------------------------------------------------------
# AI service core
# ---------------------------------------------------------------------------
class TestAIServiceCore:
    """Tests for AIService business logic without DB."""

    def test_request_type_enum(self) -> None:
        assert AIRequestType.WRITING_ASSIST == "writing_assist"
        assert AIRequestType.RECOMMENDATION == "recommendation"
        assert AIRequestType.GENERAL == "general"

    def test_request_status_enum(self) -> None:
        assert AIRequestStatus.ACCEPTED == "accepted"
        assert AIRequestStatus.COMPLETED == "completed"
        assert AIRequestStatus.FAILED == "failed"
        assert AIRequestStatus.BLOCKED == "blocked"

    def test_sanitize_for_logging_masks_api_keys(self) -> None:
        raw = "Error calling Claude with sk-ant-api03-abc123"
        sanitized = _sanitize_for_logging(raw)
        assert "sk-ant-api03" not in sanitized
        assert "***" in sanitized

    def test_sanitize_for_logging_leaves_safe_text(self) -> None:
        raw = "Normal log message without secrets"
        assert _sanitize_for_logging(raw) == raw
