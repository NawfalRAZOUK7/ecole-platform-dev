# AI Service

AI integration layer using the Strategy pattern to support multiple LLM providers.

## Files

- **provider_base.py** — Abstract base class defining the AI provider interface
- **claude_provider.py** — Anthropic Claude implementation
- **mock_provider.py** — Deterministic mock for testing (no API calls)
- **provider_factory.py** — Factory selecting provider based on configuration
- **ai_service.py** — High-level service consumed by API endpoints

## Architecture

The factory pattern allows swapping providers without changing business logic. In tests, `MockProvider` returns predictable responses. In production, `ClaudeProvider` calls the Anthropic API.
