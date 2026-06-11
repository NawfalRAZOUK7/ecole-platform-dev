"""Factory for AI providers.

Selection order (mock by default, ready to upgrade automatically):

  AI_PROVIDER=claude → paid Anthropic Claude API (best Arabic quality) if a key
                       is set, otherwise mock.
  AI_PROVIDER=open   → free / self-hosted OpenAI-compatible model if a base URL
                       is set, otherwise mock.
  AI_PROVIDER=auto   → the code decides: use Claude if an API key is present,
                       else the open model if a base URL is present, else mock.
                       (Claude is preferred first because Arabic quality matters.)
  AI_PROVIDER=mock / unset / unknown → the free deterministic mock provider.

Every real provider falls back to the mock on failure, so nothing breaks if a
backend is missing or offline.
"""

from __future__ import annotations

from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.mock_provider import MockProvider
from app.services.ai.open_model_provider import OpenModelProvider

_DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"


def _make_claude(api_key: str, model: str):
    return ClaudeProvider(api_key, model or _DEFAULT_CLAUDE_MODEL)


def _make_open(base_url: str, model: str, api_key: str):
    return OpenModelProvider(base_url, model, api_key)


def create_ai_provider(settings):
    """Create the configured AI provider, defaulting to the mock provider."""

    provider_name = str(getattr(settings, "ai_provider", "mock") or "mock").lower()
    api_key = str(getattr(settings, "ai_api_key", "") or "")
    model = str(getattr(settings, "ai_model", "") or "")
    open_base_url = str(getattr(settings, "ai_open_base_url", "") or "")
    open_model = str(getattr(settings, "ai_open_model", "") or "")
    open_api_key = str(getattr(settings, "ai_open_api_key", "") or "")

    if provider_name == "claude":
        return _make_claude(api_key, model) if api_key else MockProvider()

    if provider_name == "open":
        return (
            _make_open(open_base_url, open_model, open_api_key)
            if open_base_url
            else MockProvider()
        )

    if provider_name == "auto":
        # The code "searches" for the best configured backend, Arabic-first:
        # paid Claude (strongest Arabic) → free open model → mock.
        if api_key:
            return _make_claude(api_key, model)
        if open_base_url:
            return _make_open(open_base_url, open_model, open_api_key)
        return MockProvider()

    # "mock", unset, or anything unrecognized → free deterministic mock.
    return MockProvider()
