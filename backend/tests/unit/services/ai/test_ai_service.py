"""Unit tests for AI service and provider factory.

Tests provider factory logic, MockProvider responses, prompt templates,
PII detection, input/output validation, AIService orchestration methods,
and metrics emission without network calls.
"""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

import app.services.ai.ai_service as ai_module
from app.services.ai.ai_service import (
    AIRequestStatus,
    AIRequestType,
    AIService,
    _sanitize_for_logging,
    check_content_safety,
    detect_pii_in_payload,
    detect_pii_in_text,
    get_fallback_response,
    get_prompt_template,
    redact_pii_from_text,
    validate_ai_input,
    validate_ai_output,
)
from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_factory import create_ai_provider


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

    def test_open_with_base_url_returns_open_provider(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "open"
        settings.ai_api_key = ""
        settings.ai_open_base_url = "http://localhost:11434/v1"
        settings.ai_open_model = "qwen2.5"
        settings.ai_open_api_key = ""
        provider = create_ai_provider(settings)
        assert type(provider).__name__ == "OpenModelProvider"

    def test_open_without_base_url_returns_mock(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "open"
        settings.ai_api_key = ""
        settings.ai_open_base_url = ""
        provider = create_ai_provider(settings)
        assert isinstance(provider, MockProvider)

    def test_auto_prefers_claude_when_api_key_present(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "auto"
        settings.ai_api_key = "sk-ant-api03-test"
        settings.ai_model = "claude-sonnet-4-20250514"
        provider = create_ai_provider(settings)
        assert type(provider).__name__ == "ClaudeProvider"

    def test_auto_uses_open_model_when_only_base_url_present(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "auto"
        settings.ai_api_key = ""
        settings.ai_open_base_url = "http://localhost:11434/v1"
        settings.ai_open_model = "qwen2.5"
        settings.ai_open_api_key = ""
        provider = create_ai_provider(settings)
        assert type(provider).__name__ == "OpenModelProvider"

    def test_auto_falls_back_to_mock_when_nothing_configured(self) -> None:
        settings = MagicMock()
        settings.ai_provider = "auto"
        settings.ai_api_key = ""
        settings.ai_open_base_url = ""
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
        assert feedback["word_count"] < 20
        assert isinstance(feedback["hints"], list)
        assert len(feedback["hints"]) > 0

    @pytest.mark.asyncio
    async def test_analyze_writing_long_text(self, provider: MockProvider) -> None:
        text = " ".join(["word"] * 100)
        feedback = await provider.analyze_writing(text=text, language="en")
        assert feedback["word_count"] == 100

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, provider: MockProvider) -> None:
        recs = await provider.generate_recommendations(
            student_data={"grade": "CP", "subjects": ["math"]},
            language="en",
        )
        assert isinstance(recs, list)
        assert len(recs) > 0
        assert all("title" in r for r in recs)

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

    def test_ai_service_init_wires_up_deps(self) -> None:
        """Covers AIService.__init__ — ensures repo, audit, and provider are wired."""
        db = MagicMock()
        db.info = {}
        svc = AIService(db)
        assert svc.repo is not None
        assert svc.audit is not None
        assert svc._provider is not None


# ---------------------------------------------------------------------------
# PII detection & redaction
# ---------------------------------------------------------------------------


class TestPIIDetection:
    def test_detect_email_in_text(self):
        hits = detect_pii_in_text("Contact me at alice@example.com please")
        assert len(hits) >= 1

    def test_detect_moroccan_phone(self):
        hits = detect_pii_in_text("Call me on +212612345678")
        assert len(hits) >= 1

    def test_no_pii_returns_empty(self):
        hits = detect_pii_in_text("This is a normal sentence about maths.")
        assert hits == []

    def test_detect_pii_field_in_payload(self):
        violations = detect_pii_in_payload({"email": "x@y.com", "grade": 90})
        assert any("email" in v for v in violations)

    def test_no_pii_field_in_payload(self):
        violations = detect_pii_in_payload({"grade": 90, "subject": "math"})
        assert violations == []

    def test_context_with_non_pii_fields_preserved(self):
        """Covers the branch where context is provided but contains no PII field names."""
        ctx_in = {"grade": 18, "subject": "math"}
        _, ctx_out, warnings = validate_ai_input("hello", context=ctx_in)
        assert ctx_out == ctx_in
        assert not any("pii_field" in w for w in warnings)

    def test_redact_email_from_text(self):
        result = redact_pii_from_text("Send to bob@test.org now")
        assert "bob@test.org" not in result
        assert "[REDACTED]" in result

    def test_redact_clean_text_unchanged(self):
        original = "The student scored 18 out of 20"
        assert redact_pii_from_text(original) == original


# ---------------------------------------------------------------------------
# validate_ai_input
# ---------------------------------------------------------------------------


class TestValidateAIInput:
    def test_clean_text_passes_through(self):
        text, ctx, warnings = validate_ai_input("Normal text", request_type="general")
        assert text == "Normal text"
        assert warnings == []

    def test_pii_in_text_gets_redacted(self):
        text, ctx, warnings = validate_ai_input(
            "Email alice@example.com here", request_type="general"
        )
        assert "alice@example.com" not in text
        assert any("pii_detected" in w for w in warnings)

    def test_pii_in_context_gets_filtered(self):
        ctx_in = {"email": "x@y.com", "subject": "math"}
        _, ctx_out, warnings = validate_ai_input("hello", context=ctx_in)
        assert "email" not in ctx_out
        assert "subject" in ctx_out
        assert any("pii_field" in w for w in warnings)

    def test_general_text_truncated_at_2000(self):
        long_text = "x" * 3000
        text, _, warnings = validate_ai_input(long_text, request_type="general")
        assert len(text) == 2000
        assert any("truncated" in w for w in warnings)

    def test_writing_assist_truncated_at_5000(self):
        long_text = "x" * 6000
        text, _, warnings = validate_ai_input(long_text, request_type="writing_assist")
        assert len(text) == 5000
        assert any("truncated" in w for w in warnings)

    def test_none_context_stays_none(self):
        _, ctx_out, _ = validate_ai_input("text", context=None)
        assert ctx_out is None


# ---------------------------------------------------------------------------
# validate_ai_output
# ---------------------------------------------------------------------------


class TestValidateAIOutput:
    def test_non_dict_returns_invalid(self):
        out, valid = validate_ai_output("not a dict")
        assert not valid
        assert "invalid_output_type" in out["error"]

    def test_missing_required_fields(self):
        out, valid = validate_ai_output(
            {"suggestion": "ok"}, expected_fields={"suggestion", "hints"}
        )
        assert not valid
        assert "missing_fields" in out["error"]

    def test_all_fields_present_returns_valid(self):
        out, valid = validate_ai_output(
            {"suggestion": "good", "hints": []},
            expected_fields={"suggestion", "hints"},
        )
        assert valid

    def test_pii_in_string_values_gets_redacted(self):
        out, valid = validate_ai_output({"suggestion": "Email me at bob@test.org"})
        assert "bob@test.org" not in out["suggestion"]
        assert valid

    def test_no_expected_fields_always_valid(self):
        _, valid = validate_ai_output({"anything": "value"})
        assert valid


# ---------------------------------------------------------------------------
# check_content_safety
# ---------------------------------------------------------------------------


class TestCheckContentSafety:
    def test_safe_text_passes(self):
        safe, reason = check_content_safety("The student got a great grade!")
        assert safe is True
        assert reason is None

    def test_unsafe_password_pattern_blocked(self):
        safe, reason = check_content_safety("password is: secret123")
        assert safe is False
        assert reason is not None

    def test_unsafe_injection_pattern_blocked(self):
        safe, reason = check_content_safety("This is an SQL injection attempt")
        assert safe is False

    def test_xss_pattern_blocked(self):
        safe, reason = check_content_safety("alert XSS exploit here")
        assert safe is False


# ---------------------------------------------------------------------------
# get_fallback_response / get_prompt_template
# ---------------------------------------------------------------------------


class TestFallbackAndTemplates:
    def test_writing_assist_fallback_has_status_key(self):
        result = get_fallback_response("writing_assist", "test")
        assert result["status"] == "fallback"
        assert "suggestion" in result

    def test_recommendation_fallback_has_recommendations(self):
        result = get_fallback_response("recommendation", "test")
        assert "recommendations" in result

    def test_general_fallback_for_unknown_type(self):
        result = get_fallback_response("unknown_type", "test")
        assert result["status"] == "fallback"

    def test_prompt_template_known(self):
        t = get_prompt_template("PROMPT-G3-001")
        assert t is not None
        assert "version" in t

    def test_prompt_template_unknown_returns_none(self):
        assert get_prompt_template("NONEXISTENT") is None


# ---------------------------------------------------------------------------
# AIService._resolve_language
# ---------------------------------------------------------------------------


class TestResolveLanguage:
    def _make_svc(self):
        svc = AIService.__new__(AIService)
        svc.env = "test"
        svc._provider = MagicMock()
        svc.repo = AsyncMock()
        svc.audit = AsyncMock()
        svc.db = AsyncMock()
        return svc

    def test_explicit_fr(self):
        svc = self._make_svc()
        assert svc._resolve_language("hello", "fr") == "fr"

    def test_explicit_ar(self):
        svc = self._make_svc()
        assert svc._resolve_language("hello", "AR") == "ar"

    def test_explicit_en(self):
        svc = self._make_svc()
        assert svc._resolve_language("hello", "EN") == "en"

    def test_arabic_chars_detected(self):
        svc = self._make_svc()
        assert svc._resolve_language("مرحبا بالطلاب", None) == "ar"

    def test_french_tokens_detected(self):
        svc = self._make_svc()
        assert svc._resolve_language("le cours pour la classe", None) == "fr"

    def test_unknown_defaults_to_en(self):
        svc = self._make_svc()
        assert svc._resolve_language("hello world", None) == "en"

    def test_invalid_explicit_falls_back_to_detection(self):
        svc = self._make_svc()
        result = svc._resolve_language("la leçon pour les élèves", "xx")
        assert result == "fr"


# ---------------------------------------------------------------------------
# AIService — helper to build a service with all deps mocked
# ---------------------------------------------------------------------------


def _make_ai_service():
    db = AsyncMock()
    svc = AIService.__new__(AIService)
    svc.db = db
    svc.env = "test"
    svc._provider = AsyncMock()
    svc.repo = AsyncMock()
    svc.audit = AsyncMock()
    return svc


def _make_auth(user_id=None, school_id=None, role="STD"):
    return SimpleNamespace(
        user_id=user_id or uuid.uuid4(),
        school_id=school_id or uuid.uuid4(),
        role=role,
        session_id=uuid.uuid4(),
    )


# ---------------------------------------------------------------------------
# AIService.process_writing_assist
# ---------------------------------------------------------------------------


class TestProcessWritingAssist:
    @pytest.mark.asyncio
    async def test_missing_template_returns_fallback(self, monkeypatch):
        svc = _make_ai_service()
        monkeypatch.setattr(ai_module, "get_prompt_template", lambda _: None)
        result = await svc.process_writing_assist(
            text="hello", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_invalid_output_returns_fallback(self, monkeypatch):
        svc = _make_ai_service()
        svc._provider.analyze_writing = AsyncMock(return_value={"bad": "data"})
        result = await svc.process_writing_assist(
            text="hello", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_safety_violation_returns_fallback(self, monkeypatch):
        svc = _make_ai_service()
        svc._provider.analyze_writing = AsyncMock(
            return_value={"suggestion": "password is: secret", "hints": []}
        )
        result = await svc.process_writing_assist(
            text="hello", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_success_returns_completed(self):
        svc = _make_ai_service()
        svc._provider.analyze_writing = AsyncMock(
            return_value={"suggestion": "Good work!", "hints": ["Be concise"]}
        )
        result = await svc.process_writing_assist(
            text="My essay text", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "completed"
        assert result["suggestion"] == "Good work!"
        assert result["prompt_id"] == "PROMPT-G3-002"

    @pytest.mark.asyncio
    async def test_provider_exception_returns_fallback(self):
        svc = _make_ai_service()
        svc._provider.analyze_writing = AsyncMock(side_effect=RuntimeError("API error"))
        result = await svc.process_writing_assist(
            text="hello", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_empty_suggestion_skips_safety_check(self):
        svc = _make_ai_service()
        svc._provider.analyze_writing = AsyncMock(
            return_value={"suggestion": "", "hints": ["tip1"]}
        )
        result = await svc.process_writing_assist(
            text="hello", student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "completed"


# ---------------------------------------------------------------------------
# AIService.process_recommendation
# ---------------------------------------------------------------------------


class TestProcessRecommendation:
    @pytest.mark.asyncio
    async def test_missing_template_returns_fallback(self, monkeypatch):
        svc = _make_ai_service()
        monkeypatch.setattr(ai_module, "get_prompt_template", lambda _: None)
        result = await svc.process_recommendation(
            student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_missing_reason_code_returns_fallback(self):
        svc = _make_ai_service()
        svc._provider.generate_recommendations = AsyncMock(
            return_value=[{"title": "Learn Python"}]  # missing reason_code
        )
        result = await svc.process_recommendation(
            student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_success_returns_recommendations(self):
        svc = _make_ai_service()
        svc._provider.generate_recommendations = AsyncMock(
            return_value=[{"title": "Learn Python", "reason_code": "new_topic"}]
        )
        result = await svc.process_recommendation(
            student_id=uuid.uuid4(), school_id=uuid.uuid4(), completed_count=5
        )
        assert result["status"] == "completed"
        assert len(result["recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_provider_exception_returns_fallback(self):
        svc = _make_ai_service()
        svc._provider.generate_recommendations = AsyncMock(
            side_effect=RuntimeError("API down")
        )
        result = await svc.process_recommendation(
            student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_empty_recommendations_list(self):
        svc = _make_ai_service()
        svc._provider.generate_recommendations = AsyncMock(return_value=[])
        result = await svc.process_recommendation(
            student_id=uuid.uuid4(), school_id=uuid.uuid4()
        )
        assert result["status"] == "completed"
        assert result["recommendations"] == []


# ---------------------------------------------------------------------------
# AIService.create_writing_attempt
# ---------------------------------------------------------------------------


class FakeUow:
    def __init__(self, repo, audit=None):
        self._repo = repo
        self._audit = audit or AsyncMock()
        self.session = AsyncMock()
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def commit(self):
        self.committed = True


class TestCreateWritingAttempt:
    def _body(self, text="Hello world", subject="math"):
        return SimpleNamespace(text=text, subject=subject, language=None)

    @pytest.mark.asyncio
    async def test_opt_out_returns_fallback_attempt(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_opt_out_preference = AsyncMock(return_value=True)  # opted out

        attempt = SimpleNamespace(
            id=uuid.uuid4(),
            created_at=__import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        )
        inner_repo = AsyncMock()
        inner_repo.create_writing_attempt = AsyncMock(return_value=attempt)
        uow = FakeUow(inner_repo)
        monkeypatch.setattr(ai_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(ai_module, "AIRepository", lambda _: inner_repo)
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)

        result = await svc.create_writing_attempt(
            auth=auth, body=self._body(), client_ip="1.2.3.4"
        )
        assert result["status"] == "fallback"
        assert result["warnings"] == ["ai_opt_out_active"]

    @pytest.mark.asyncio
    async def test_normal_path_returns_completed(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_opt_out_preference = AsyncMock(return_value=None)
        svc._provider.analyze_writing = AsyncMock(
            return_value={"suggestion": "Great!", "hints": ["shorter"]}
        )

        from datetime import datetime, timezone

        attempt = SimpleNamespace(
            id=uuid.uuid4(),
            status="completed",
            input_word_count=2,
            prompt_id="PROMPT-G3-002",
            created_at=datetime.now(timezone.utc),
        )
        inner_repo = AsyncMock()
        inner_repo.create_writing_attempt = AsyncMock(return_value=attempt)
        inner_audit = AsyncMock()
        uow = FakeUow(inner_repo, inner_audit)
        monkeypatch.setattr(ai_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(ai_module, "AIRepository", lambda _: inner_repo)
        monkeypatch.setattr(ai_module, "AuditService", lambda _: inner_audit)
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)

        result = await svc.create_writing_attempt(
            auth=auth, body=self._body(), client_ip="1.2.3.4"
        )
        assert result["status"] == "completed"
        assert result["suggestion"] == "Great!"


# ---------------------------------------------------------------------------
# AIService.update_opt_out
# ---------------------------------------------------------------------------


class TestUpdateOptOut:
    def _body(self, opt_out=True, target_user_id=None):
        return SimpleNamespace(opt_out=opt_out, target_user_id=target_user_id)

    @pytest.mark.asyncio
    async def test_creates_new_preference(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_ai_preference = AsyncMock(return_value=None)

        from datetime import datetime, timezone

        saved_pref = SimpleNamespace(
            id=uuid.uuid4(),
            user_id=auth.user_id,
            target_user_id=auth.user_id,
            opt_out=True,
            updated_at=None,
            created_at=datetime.now(timezone.utc),
        )
        inner_repo = AsyncMock()
        inner_repo.save_ai_preference = AsyncMock(return_value=saved_pref)
        inner_audit = AsyncMock()
        uow = FakeUow(inner_repo, inner_audit)
        monkeypatch.setattr(ai_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(ai_module, "AIRepository", lambda _: inner_repo)
        monkeypatch.setattr(ai_module, "AuditService", lambda _: inner_audit)
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)
        monkeypatch.setattr(ai_module, "pseudonymize_actor_id", lambda _: "hash")

        result = await svc.update_opt_out(
            auth=auth, body=self._body(opt_out=True), client_ip="1.2.3.4"
        )
        assert result["opt_out"] is True

    @pytest.mark.asyncio
    async def test_updates_existing_preference(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        existing = SimpleNamespace(opt_out=False, id=uuid.uuid4())
        svc.repo.get_ai_preference = AsyncMock(return_value=existing)

        from datetime import datetime, timezone

        saved_pref = SimpleNamespace(
            id=existing.id,
            user_id=auth.user_id,
            target_user_id=auth.user_id,
            opt_out=True,
            updated_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        inner_repo = AsyncMock()
        inner_repo.save_ai_preference = AsyncMock(return_value=saved_pref)
        inner_audit = AsyncMock()
        uow = FakeUow(inner_repo, inner_audit)
        monkeypatch.setattr(ai_module, "UnitOfWork", lambda _: uow)
        monkeypatch.setattr(ai_module, "AIRepository", lambda _: inner_repo)
        monkeypatch.setattr(ai_module, "AuditService", lambda _: inner_audit)
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)
        monkeypatch.setattr(ai_module, "pseudonymize_actor_id", lambda _: "hash")

        result = await svc.update_opt_out(
            auth=auth, body=self._body(opt_out=True), client_ip="1.2.3.4"
        )
        assert result["id"] is not None


# ---------------------------------------------------------------------------
# AIService.get_recommendations_for_user
# ---------------------------------------------------------------------------


class TestGetRecommendationsForUser:
    @pytest.mark.asyncio
    async def test_opt_out_returns_fallback(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_opt_out_preference = AsyncMock(return_value=True)
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)

        result = await svc.get_recommendations_for_user(auth=auth)
        assert result["status"] == "fallback"
        assert result["recommendations"] == []

    @pytest.mark.asyncio
    async def test_normal_path_serves_recommendations(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_opt_out_preference = AsyncMock(return_value=None)
        svc.repo.count_completed_content_progress = AsyncMock(return_value=3)
        svc._provider.generate_recommendations = AsyncMock(
            return_value=[{"title": "Topic A", "reason_code": "seq"}]
        )
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)

        result = await svc.get_recommendations_for_user(auth=auth)
        assert result["status"] == "completed"
        assert len(result["recommendations"]) == 1

    @pytest.mark.asyncio
    async def test_empty_recommendations_emit_none_reason(self, monkeypatch):
        svc = _make_ai_service()
        auth = _make_auth()
        svc.repo.get_opt_out_preference = AsyncMock(return_value=None)
        svc.repo.count_completed_content_progress = AsyncMock(return_value=0)
        svc._provider.generate_recommendations = AsyncMock(return_value=[])
        monkeypatch.setattr(ai_module, "emit_event", lambda *_a, **_k: None)

        result = await svc.get_recommendations_for_user(auth=auth)
        assert result["recommendations"] == []


# ---------------------------------------------------------------------------
# AIService.get_kpis
# ---------------------------------------------------------------------------


class TestGetKpis:
    @pytest.mark.asyncio
    async def test_returns_kpis_with_period(self, monkeypatch):
        svc = _make_ai_service()
        svc._provider.compute_kpi_insights = AsyncMock(return_value=[{"insight": "up"}])
        monkeypatch.setattr(
            ai_module, "compute_all_kpis", AsyncMock(return_value={"active_users": 50})
        )

        result = await svc.get_kpis(school_id=uuid.uuid4(), period=7)
        assert result["period"] == "7d"
        assert "kpis" in result
        assert "computed_at" in result

    @pytest.mark.asyncio
    async def test_provider_exception_still_returns_kpis(self, monkeypatch):
        svc = _make_ai_service()
        svc._provider.compute_kpi_insights = AsyncMock(
            side_effect=RuntimeError("KPI provider down")
        )
        monkeypatch.setattr(
            ai_module, "compute_all_kpis", AsyncMock(return_value={"active_users": 10})
        )

        result = await svc.get_kpis(school_id=uuid.uuid4(), period=30)
        assert result["kpis"] == {"active_users": 10}
        assert result["period"] == "30d"


# ---------------------------------------------------------------------------
# AIService.get_event_schema
# ---------------------------------------------------------------------------


class TestGetEventSchema:
    @pytest.mark.asyncio
    async def test_returns_schema_with_events(self):
        svc = _make_ai_service()
        result = await svc.get_event_schema()
        assert "schema_version" in result
        assert "events" in result
        assert result["total"] == len(result["events"])

    @pytest.mark.asyncio
    async def test_payment_events_have_medium_pii_risk(self):
        svc = _make_ai_service()
        result = await svc.get_event_schema()
        payment_events = [e for e in result["events"] if "payment" in e["event_name"]]
        if payment_events:
            assert all(e["pii_risk"] == "medium" for e in payment_events)

    @pytest.mark.asyncio
    async def test_non_payment_events_have_low_pii_risk(self):
        svc = _make_ai_service()
        result = await svc.get_event_schema()
        other_events = [
            e
            for e in result["events"]
            if "payment" not in e["event_name"] and "invoice" not in e["event_name"]
        ]
        if other_events:
            assert all(e["pii_risk"] == "low" for e in other_events)
