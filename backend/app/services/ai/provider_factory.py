"""Factory for AI providers."""

from __future__ import annotations

from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.mock_provider import MockProvider


def create_ai_provider(settings):
    """Create the configured AI provider, defaulting to the mock provider."""

    provider_name = str(getattr(settings, "ai_provider", "mock") or "mock").lower()
    api_key = str(getattr(settings, "ai_api_key", "") or "")
    model = str(getattr(settings, "ai_model", "") or "")

    if provider_name == "claude" and api_key:
        return ClaudeProvider(api_key, model or "claude-sonnet-4-20250514")
    return MockProvider()
