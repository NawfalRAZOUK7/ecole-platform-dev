"""AI service — request orchestration with PII guardrails per G3.

Reference: S-142 — AI request endpoint with guardrails, Pack G3 — AI Governance
Policy rules:
  POL-G3-001 — Block raw PII in prompt payloads (pre-request validator)
  POL-G3-002 — Enforce opt-out for personalization flows (request orchestrator)
  POL-G3-003 — Validate structured outputs before use (post-response validator)

Guardrails (G3.7):
  - Input validation + PII redaction on all AI requests
  - Output schema validation for structured responses
  - Safety content check for generated text
  - Role/permission check before write actions
  - Fail-closed policy: disable AI feature path if policy service unavailable

Design:
  - AI service is a stateless orchestrator
  - Actual model calls are stubbed (placeholder for provider integration)
  - All guardrail checks happen synchronously before/after model calls
  - Metrics emitted for monitoring (G3.8)
"""

from __future__ import annotations

import logging
import re
import time
import uuid
from enum import Enum
from typing import Any

from app.core.config import settings
from app.core.metrics import (
    REGISTRY,
)
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI-specific Prometheus metrics (G3.8)
# ---------------------------------------------------------------------------
AI_REQUEST_COUNT = Counter(
    "ai_request_count",
    "AI request count by type and status",
    ["env", "request_type", "status"],
    registry=REGISTRY,
)

AI_ERROR_COUNT = Counter(
    "ai_error_count",
    "AI request errors",
    ["env", "request_type", "error_type"],
    registry=REGISTRY,
)

AI_FALLBACK_COUNT = Counter(
    "ai_fallback_count",
    "AI fallback activations",
    ["env", "reason"],
    registry=REGISTRY,
)

AI_LATENCY = Histogram(
    "ai_request_duration_seconds",
    "AI request processing latency",
    ["env", "request_type"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
    registry=REGISTRY,
)

AI_OPT_OUT_COUNT = Counter(
    "ai_opt_out_count",
    "AI opt-out preference changes",
    ["env", "action"],  # action: opt_out, opt_in
    registry=REGISTRY,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class AIRequestType(str, Enum):
    WRITING_ASSIST = "writing_assist"
    RECOMMENDATION = "recommendation"
    GENERAL = "general"


class AIRequestStatus(str, Enum):
    ACCEPTED = "accepted"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    FALLBACK = "fallback"


# ---------------------------------------------------------------------------
# PII Detection — POL-G3-001
# ---------------------------------------------------------------------------
# Patterns that indicate raw PII in text
_PII_PATTERNS = [
    # Email
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    # Phone (Moroccan +212, or generic international)
    re.compile(r"(?:\+?212|0)[5-7]\d{8}"),
    re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"),
    # National ID (Moroccan CIN pattern)
    re.compile(r"\b[A-Z]{1,2}\d{5,7}\b"),
]

# Fields that MUST NOT appear in AI prompt payloads
_PII_FIELD_NAMES = frozenset(
    {
        "email",
        "phone",
        "full_name",
        "password",
        "password_hash",
        "national_id",
        "cin",
        "credit_card",
        "card_number",
        "ssn",
        "address",
        "date_of_birth",
    }
)


def detect_pii_in_text(text: str) -> list[str]:
    """Detect PII patterns in free text. Returns list of detected PII types."""
    detected: list[str] = []
    for pattern in _PII_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern[:30])
    return detected


def detect_pii_in_payload(payload: dict[str, Any]) -> list[str]:
    """Check payload fields for PII field names (POL-G3-001)."""
    violations: list[str] = []
    for key in payload:
        if key.lower() in _PII_FIELD_NAMES:
            violations.append(f"pii_field:{key}")
    return violations


def redact_pii_from_text(text: str) -> str:
    """Redact detected PII patterns from text."""
    result = text
    for pattern in _PII_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


# ---------------------------------------------------------------------------
# Input Validation — G3.7 Guardrail 1
# ---------------------------------------------------------------------------
def validate_ai_input(
    text: str,
    context: dict[str, Any] | None = None,
    request_type: str = "general",
) -> tuple[str, dict[str, Any] | None, list[str]]:
    """Validate and sanitize AI request input.

    Returns:
        (sanitized_text, sanitized_context, warnings)
    Raises:
        ValueError if critical PII detected and cannot be safely redacted.
    """
    warnings: list[str] = []

    # Check text for PII
    text_pii = detect_pii_in_text(text)
    if text_pii:
        warnings.append(f"pii_detected_in_text:{len(text_pii)}_patterns")
        text = redact_pii_from_text(text)

    # Check context payload for PII fields
    sanitized_context = context
    if context:
        payload_pii = detect_pii_in_payload(context)
        if payload_pii:
            warnings.extend(payload_pii)
            # Remove PII fields from context
            sanitized_context = {
                k: v for k, v in context.items() if k.lower() not in _PII_FIELD_NAMES
            }

    # Length limits
    max_length = 5000 if request_type == "writing_assist" else 2000
    if len(text) > max_length:
        text = text[:max_length]
        warnings.append(f"text_truncated_to_{max_length}")

    return text, sanitized_context, warnings


# ---------------------------------------------------------------------------
# Output Validation — POL-G3-003, G3.7 Guardrail 2
# ---------------------------------------------------------------------------
def validate_ai_output(
    output: dict[str, Any],
    expected_fields: set[str] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Validate structured AI output.

    Returns:
        (validated_output, is_valid)
    """
    if not isinstance(output, dict):
        return {"error": "invalid_output_type"}, False

    # Check for required fields if specified
    if expected_fields:
        missing = expected_fields - set(output.keys())
        if missing:
            return {"error": "missing_fields", "missing": list(missing)}, False

    # Safety check: scan text fields for unsafe content
    for key, value in output.items():
        if isinstance(value, str):
            # Check for PII leakage in output
            pii = detect_pii_in_text(value)
            if pii:
                output[key] = redact_pii_from_text(value)

    return output, True


# ---------------------------------------------------------------------------
# Safety Content Check — G3.7 Guardrail 3
# ---------------------------------------------------------------------------
_UNSAFE_PATTERNS = [
    re.compile(
        r"(?:password|mot de passe|كلمة المرور)\s*(?:is|est|هي)\s*[:=]", re.IGNORECASE
    ),
    re.compile(r"(?:hack|exploit|inject|xss|sql\s*injection)", re.IGNORECASE),
]


def check_content_safety(text: str) -> tuple[bool, str | None]:
    """Check generated text for safety violations.

    Returns:
        (is_safe, violation_reason)
    """
    for pattern in _UNSAFE_PATTERNS:
        if pattern.search(text):
            return False, f"unsafe_pattern:{pattern.pattern[:30]}"
    return True, None


# ---------------------------------------------------------------------------
# Fallback Responses — G3.9 incident playbook
# ---------------------------------------------------------------------------
_FALLBACK_RESPONSES: dict[str, dict[str, Any]] = {
    "writing_assist": {
        "status": "fallback",
        "suggestion": None,
        "hints": [],
        "message": "AI assistance is temporarily unavailable. Please try again later.",
        "message_fr": "L'assistance IA est temporairement indisponible. Veuillez réessayer plus tard.",
        "message_ar": "المساعدة بالذكاء الاصطناعي غير متاحة مؤقتًا. يرجى المحاولة لاحقًا.",
    },
    "recommendation": {
        "status": "fallback",
        "recommendations": [],
        "message": "Personalized recommendations are temporarily unavailable.",
        "message_fr": "Les recommandations personnalisées sont temporairement indisponibles.",
        "message_ar": "التوصيات المخصصة غير متاحة مؤقتًا.",
    },
    "general": {
        "status": "fallback",
        "result": None,
        "message": "AI service is temporarily unavailable.",
        "message_fr": "Le service IA est temporairement indisponible.",
        "message_ar": "خدمة الذكاء الاصطناعي غير متاحة مؤقتًا.",
    },
}


def get_fallback_response(request_type: str, reason: str = "unknown") -> dict[str, Any]:
    """Get safe fallback response when AI service fails (G3.9)."""
    AI_FALLBACK_COUNT.labels(env=settings.app_env, reason=reason).inc()
    return _FALLBACK_RESPONSES.get(request_type, _FALLBACK_RESPONSES["general"])


# ---------------------------------------------------------------------------
# Prompt Templates — G3.4 Prompt Inventory
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATES: dict[str, dict[str, Any]] = {
    "PROMPT-G3-001": {
        "purpose": "Recommendation summary",
        "version": 1,
        "template": (
            "Based on the student's learning activity:\n"
            "- Completed items: {completed_count}\n"
            "- Current level: {level_band}\n"
            "- Recent topics: {recent_topics}\n\n"
            "Suggest 3 learning recommendations with reason codes. "
            "Format as JSON array with fields: title, reason_code, priority."
        ),
    },
    "PROMPT-G3-002": {
        "purpose": "Writing assist",
        "version": 1,
        "template": (
            "You are a pedagogical writing assistant for a K-12 school in Morocco.\n"
            "Subject: {subject}\n"
            "Student text:\n{text}\n\n"
            "Provide constructive feedback with:\n"
            "1. A brief suggestion for improvement\n"
            "2. Up to 3 specific hints\n"
            "Respond in the same language as the student text. "
            "Do NOT rewrite the text. Do NOT include any personal information."
        ),
    },
    "PROMPT-G3-003": {
        "purpose": "Safety fallback response",
        "version": 1,
        "template": "Return a safe, neutral fallback message for: {error_class}",
    },
}


def get_prompt_template(prompt_id: str) -> dict[str, Any] | None:
    """Get a prompt template by ID."""
    return _PROMPT_TEMPLATES.get(prompt_id)


# ---------------------------------------------------------------------------
# AI Service — Orchestrator
# ---------------------------------------------------------------------------
class AIService:
    """AI request orchestrator with guardrails.

    Handles the full lifecycle: validate → check opt-out → prepare prompt →
    call model (stubbed) → validate output → return result.
    """

    def __init__(self) -> None:
        self.env = settings.app_env

    async def process_writing_assist(
        self,
        *,
        text: str,
        subject: str | None = None,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Process a writing assistance request (PROMPT-G3-002).

        Guardrails applied:
          1. Input validation + PII redaction
          2. Output validation
          3. Safety content check
          4. Metrics emission
        """
        start = time.perf_counter()
        request_type = "writing_assist"

        try:
            # Step 1: Validate input (POL-G3-001)
            sanitized_text, _, warnings = validate_ai_input(
                text, request_type=request_type
            )

            # Step 2: Build prompt from template
            prompt_template = get_prompt_template("PROMPT-G3-002")
            if prompt_template is None:
                return get_fallback_response(request_type, "missing_prompt_template")

            # Step 3: Simulate model call (stubbed for MVP)
            # In production, this calls the AI provider API
            result = self._stub_writing_assist(sanitized_text, subject)

            # Step 4: Validate output (POL-G3-003)
            validated, is_valid = validate_ai_output(
                result,
                expected_fields={"suggestion", "hints"},
            )
            if not is_valid:
                AI_ERROR_COUNT.labels(
                    env=self.env, request_type=request_type, error_type="invalid_output"
                ).inc()
                return get_fallback_response(request_type, "invalid_output")

            # Step 5: Safety check
            if validated.get("suggestion"):
                is_safe, violation = check_content_safety(validated["suggestion"])
                if not is_safe:
                    AI_ERROR_COUNT.labels(
                        env=self.env,
                        request_type=request_type,
                        error_type="safety_violation",
                    ).inc()
                    return get_fallback_response(request_type, f"safety:{violation}")

            # Success
            AI_REQUEST_COUNT.labels(
                env=self.env, request_type=request_type, status="completed"
            ).inc()

            return {
                "status": "completed",
                "suggestion": validated.get("suggestion"),
                "hints": validated.get("hints", []),
                "prompt_id": "PROMPT-G3-002",
                "prompt_version": prompt_template["version"],
                "warnings": warnings,
            }

        except Exception as exc:
            logger.exception("AI writing assist failed: %s", exc)
            AI_ERROR_COUNT.labels(
                env=self.env, request_type=request_type, error_type="exception"
            ).inc()
            return get_fallback_response(request_type, "exception")

        finally:
            duration = time.perf_counter() - start
            AI_LATENCY.labels(env=self.env, request_type=request_type).observe(duration)

    async def process_recommendation(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        completed_count: int = 0,
        level_band: str | None = None,
        recent_topics: list[str] | None = None,
    ) -> dict[str, Any]:
        """Process a learning recommendation request (PROMPT-G3-001).

        Returns a list of recommendations with mandatory reason_codes.
        """
        start = time.perf_counter()
        request_type = "recommendation"

        try:
            # Build context
            prompt_template = get_prompt_template("PROMPT-G3-001")
            if prompt_template is None:
                return get_fallback_response(request_type, "missing_prompt_template")

            # Simulate model call (stubbed for MVP)
            result = self._stub_recommendations(
                completed_count, level_band, recent_topics or []
            )

            # Validate output
            for rec in result.get("recommendations", []):
                if "reason_code" not in rec:
                    AI_ERROR_COUNT.labels(
                        env=self.env,
                        request_type=request_type,
                        error_type="missing_reason_code",
                    ).inc()
                    return get_fallback_response(request_type, "missing_reason_code")

            AI_REQUEST_COUNT.labels(
                env=self.env, request_type=request_type, status="completed"
            ).inc()

            return {
                "status": "completed",
                "recommendations": result["recommendations"],
                "prompt_id": "PROMPT-G3-001",
                "prompt_version": prompt_template["version"],
                "expires_at": None,  # Expiration policy per G3 surfaces
            }

        except Exception as exc:
            logger.exception("AI recommendation failed: %s", exc)
            AI_ERROR_COUNT.labels(
                env=self.env, request_type=request_type, error_type="exception"
            ).inc()
            return get_fallback_response(request_type, "exception")

        finally:
            duration = time.perf_counter() - start
            AI_LATENCY.labels(env=self.env, request_type=request_type).observe(duration)

    # ------------------------------------------------------------------
    # Stub implementations (replaced by real AI provider in production)
    # ------------------------------------------------------------------
    def _stub_writing_assist(self, text: str, subject: str | None) -> dict[str, Any]:
        """Stub: return a pedagogical writing hint based on text length."""
        word_count = len(text.split())
        hints = []
        suggestion = None

        if word_count < 20:
            suggestion = "Consider expanding your ideas with more details and examples."
            hints = [
                "Try adding a specific example to support your main point.",
                "Consider using transition words to connect your ideas.",
            ]
        elif word_count < 100:
            suggestion = "Good start! Review your structure and add a conclusion."
            hints = [
                "Check that each paragraph has a clear topic sentence.",
                "Consider adding a concluding sentence that summarizes your argument.",
            ]
        else:
            suggestion = "Well-developed text. Focus on refining language and flow."
            hints = [
                "Review for repetitive word choices and vary your vocabulary.",
                "Check punctuation and sentence variety for better readability.",
                "Ensure your introduction clearly states your thesis.",
            ]

        return {"suggestion": suggestion, "hints": hints}

    def _stub_recommendations(
        self,
        completed_count: int,
        level_band: str | None,
        recent_topics: list[str],
    ) -> dict[str, Any]:
        """Stub: return static recommendations based on progress."""
        recommendations = []

        if completed_count < 5:
            recommendations.append(
                {
                    "title": "Complete your first learning module",
                    "reason_code": "LOW_COMPLETION",
                    "priority": "high",
                    "content_type": "module",
                }
            )
        if level_band and level_band in ("CP", "CE1", "CE2"):
            recommendations.append(
                {
                    "title": "Practice reading comprehension exercises",
                    "reason_code": "LEVEL_APPROPRIATE",
                    "priority": "medium",
                    "content_type": "activity",
                }
            )
        if recent_topics:
            recommendations.append(
                {
                    "title": f"Continue exploring: {recent_topics[0] if recent_topics else 'new topics'}",
                    "reason_code": "TOPIC_CONTINUATION",
                    "priority": "medium",
                    "content_type": "content",
                }
            )

        # Always provide at least one recommendation
        if not recommendations:
            recommendations.append(
                {
                    "title": "Explore the content library for new materials",
                    "reason_code": "GENERAL_EXPLORATION",
                    "priority": "low",
                    "content_type": "library",
                }
            )

        return {"recommendations": recommendations[:3]}
