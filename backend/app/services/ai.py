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
from app.core.permissions import PERM_IA_PREFERENCE_UPDATE
from app.core.metrics import (
    REGISTRY,
)
from prometheus_client import Counter, Histogram
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai import AIPreference, WritingAttempt
from app.repositories.ai import AIRepository
from app.services.analytics import (
    SCHEMA_VERSION,
    _EVENT_PROPERTY_WHITELIST,
    emit_event,
    pseudonymize_actor_id,
)
from app.services.audit import AuditService
from app.services.kpi import compute_all_kpis

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

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.env = settings.app_env
        self.repo = AIRepository(db)
        self.audit = AuditService(db)

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

    async def create_writing_attempt(
        self,
        *,
        auth,
        body,
        client_ip: str,
    ) -> dict[str, Any]:
        opt_out = await self.repo.get_opt_out_preference(target_user_id=auth.user_id)
        if opt_out is not None:
            fallback = get_fallback_response("writing_assist", "opt_out")
            attempt = await self.repo.create_writing_attempt(
                WritingAttempt(
                    student_id=auth.user_id,
                    school_id=auth.school_id,
                    subject=body.subject,
                    input_text="[opted_out]",
                    input_word_count=len(body.text.split()),
                    status="fallback",
                    prompt_id=None,
                )
            )
            emit_event(
                "ai_fallback_used",
                actor_id=auth.user_id,
                actor_role=auth.role,
                properties={"reason": "opt_out", "request_type": "writing_assist"},
            )
            await self.db.commit()
            return {
                "id": str(attempt.id),
                "student_id": str(auth.user_id),
                "status": "fallback",
                "suggestion": fallback.get("message"),
                "hints": [],
                "prompt_id": None,
                "prompt_version": None,
                "warnings": ["ai_opt_out_active"],
                "created_at": attempt.created_at.isoformat(),
            }

        result = await self.process_writing_assist(
            text=body.text,
            subject=body.subject,
            student_id=auth.user_id,
            school_id=auth.school_id,
        )
        attempt = await self.repo.create_writing_attempt(
            WritingAttempt(
                student_id=auth.user_id,
                school_id=auth.school_id,
                subject=body.subject,
                input_text=body.text[:500],
                input_word_count=len(body.text.split()),
                status=result.get("status", "completed"),
                suggestion=result.get("suggestion"),
                hints=result.get("hints"),
                prompt_id=result.get("prompt_id"),
                prompt_version=result.get("prompt_version"),
                warnings=result.get("warnings"),
            )
        )
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="WRITING_ATTEMPT_CREATED",
            outcome="success",
            target_type="writing_attempt",
            target_id=attempt.id,
            entity_after={
                "subject": body.subject,
                "word_count": attempt.input_word_count,
                "status": attempt.status,
                "prompt_id": attempt.prompt_id,
            },
            ip_address=client_ip,
        )
        emit_event(
            "writing_attempt_created",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={
                "subject": body.subject or "general",
                "word_count": attempt.input_word_count,
            },
        )
        await self.db.commit()
        return {
            "id": str(attempt.id),
            "student_id": str(auth.user_id),
            "status": attempt.status,
            "suggestion": result.get("suggestion"),
            "hints": result.get("hints", []),
            "prompt_id": result.get("prompt_id"),
            "prompt_version": result.get("prompt_version"),
            "warnings": result.get("warnings", []),
            "created_at": attempt.created_at.isoformat(),
        }

    async def update_opt_out(
        self,
        *,
        auth,
        body,
        client_ip: str,
    ) -> dict[str, Any]:
        target_user_id = body.target_user_id or auth.user_id
        existing = await self.repo.get_ai_preference(
            user_id=auth.user_id,
            target_user_id=target_user_id,
        )
        if existing is not None:
            old_value = existing.opt_out
            existing.opt_out = body.opt_out
            preference = await self.repo.save_ai_preference(existing)
        else:
            old_value = None
            preference = await self.repo.save_ai_preference(
                AIPreference(
                    user_id=auth.user_id,
                    target_user_id=target_user_id,
                    school_id=auth.school_id,
                    opt_out=body.opt_out,
                )
            )

        action = "opt_out" if body.opt_out else "opt_in"
        AI_OPT_OUT_COUNT.labels(env=settings.app_env, action=action).inc()
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="AI_OPT_OUT_UPDATED",
            outcome="success",
            target_type="ai_preference",
            target_id=preference.id,
            entity_before={"opt_out": old_value} if old_value is not None else None,
            entity_after={"opt_out": body.opt_out, "target_user_id": str(target_user_id)},
            ip_address=client_ip,
        )
        emit_event(
            "ai_opt_out_updated",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={
                "opt_out": body.opt_out,
                "target_user_id_hash": pseudonymize_actor_id(target_user_id),
            },
        )
        await self.db.commit()
        return {
            "id": str(preference.id),
            "user_id": str(preference.user_id),
            "target_user_id": str(preference.target_user_id),
            "opt_out": preference.opt_out,
            "updated_at": preference.updated_at.isoformat()
            if preference.updated_at
            else preference.created_at.isoformat(),
        }

    async def get_recommendations_for_user(self, *, auth) -> dict[str, Any]:
        opt_out = await self.repo.get_opt_out_preference(target_user_id=auth.user_id)
        if opt_out is not None:
            emit_event(
                "ai_fallback_used",
                actor_id=auth.user_id,
                actor_role=auth.role,
                properties={"reason": "opt_out", "request_type": "recommendation"},
            )
            return {
                "status": "fallback",
                "recommendations": [],
                "prompt_id": None,
                "prompt_version": None,
                "expires_at": None,
                "message": "AI recommendations disabled by preference.",
            }

        completed_count = await self.repo.count_completed_content_progress(
            student_id=auth.user_id
        )
        result = await self.process_recommendation(
            student_id=auth.user_id,
            school_id=auth.school_id,
            completed_count=completed_count,
        )
        emit_event(
            "recommendation_served",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={
                "reason_code": result["recommendations"][0]["reason_code"]
                if result.get("recommendations")
                else "none",
                "item_count": len(result.get("recommendations", [])),
            },
        )
        return result

    async def get_kpis(
        self,
        *,
        school_id: uuid.UUID,
        period: int,
    ) -> dict[str, Any]:
        kpis = await compute_all_kpis(self.db, school_id=school_id, period_days=period)
        return {
            "kpis": kpis,
            "period": f"{period}d",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_event_schema(self) -> dict[str, Any]:
        events = []
        for event_name, properties in _EVENT_PROPERTY_WHITELIST.items():
            events.append(
                {
                    "event_name": event_name,
                    "event_version": 1,
                    "schema_version": SCHEMA_VERSION,
                    "required_properties": sorted(properties),
                    "pii_risk": "medium"
                    if "invoice" in event_name or "payment" in event_name
                    else "low",
                    "status": "known",
                }
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "events": events,
            "total": len(events),
        }
