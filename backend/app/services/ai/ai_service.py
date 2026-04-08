"""AI service — request orchestration with provider abstraction and guardrails."""

from __future__ import annotations

import logging
import re
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from prometheus_client import Counter, Histogram
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.metrics import REGISTRY
from app.core.unit_of_work import UnitOfWork
from app.models.ai import AIPreference, WritingAttempt
from app.repositories.ai import AIRepository
from app.services.ai.provider_factory import create_ai_provider
from app.services.analytics import (
    SCHEMA_VERSION,
    _EVENT_PROPERTY_WHITELIST,
    emit_event,
    pseudonymize_actor_id,
)
from app.services.audit import AuditService
from app.services.kpi import compute_all_kpis

logger = logging.getLogger(__name__)

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
    ["env", "action"],
    registry=REGISTRY,
)


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


_PII_PATTERNS = [
    re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    re.compile(r"(?:\+?212|0)[5-7]\d{8}"),
    re.compile(r"\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}"),
    re.compile(r"\b[A-Z]{1,2}\d{5,7}\b"),
]

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
    detected: list[str] = []
    for pattern in _PII_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern[:30])
    return detected


def detect_pii_in_payload(payload: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    for key in payload:
        if key.lower() in _PII_FIELD_NAMES:
            violations.append(f"pii_field:{key}")
    return violations


def redact_pii_from_text(text: str) -> str:
    result = text
    for pattern in _PII_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result


def validate_ai_input(
    text: str,
    context: dict[str, Any] | None = None,
    request_type: str = "general",
) -> tuple[str, dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    text_pii = detect_pii_in_text(text)
    if text_pii:
        warnings.append(f"pii_detected_in_text:{len(text_pii)}_patterns")
        text = redact_pii_from_text(text)

    sanitized_context = context
    if context:
        payload_pii = detect_pii_in_payload(context)
        if payload_pii:
            warnings.extend(payload_pii)
            sanitized_context = {
                key: value
                for key, value in context.items()
                if key.lower() not in _PII_FIELD_NAMES
            }

    max_length = 5000 if request_type == "writing_assist" else 2000
    if len(text) > max_length:
        text = text[:max_length]
        warnings.append(f"text_truncated_to_{max_length}")
    return text, sanitized_context, warnings


def validate_ai_output(
    output: dict[str, Any],
    expected_fields: set[str] | None = None,
) -> tuple[dict[str, Any], bool]:
    if not isinstance(output, dict):
        return {"error": "invalid_output_type"}, False
    if expected_fields:
        missing = expected_fields - set(output.keys())
        if missing:
            return {"error": "missing_fields", "missing": list(missing)}, False
    for key, value in output.items():
        if isinstance(value, str):
            pii = detect_pii_in_text(value)
            if pii:
                output[key] = redact_pii_from_text(value)
    return output, True


_UNSAFE_PATTERNS = [
    re.compile(
        r"(?:password|mot de passe|كلمة المرور)\s*(?:is|est|هي)\s*[:=]", re.IGNORECASE
    ),
    re.compile(r"(?:hack|exploit|inject|xss|sql\s*injection)", re.IGNORECASE),
]


def check_content_safety(text: str) -> tuple[bool, str | None]:
    for pattern in _UNSAFE_PATTERNS:
        if pattern.search(text):
            return False, f"unsafe_pattern:{pattern.pattern[:30]}"
    return True, None


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
    AI_FALLBACK_COUNT.labels(env=settings.app_env, reason=reason).inc()
    return _FALLBACK_RESPONSES.get(request_type, _FALLBACK_RESPONSES["general"])


_PROMPT_TEMPLATES: dict[str, dict[str, Any]] = {
    "PROMPT-G3-001": {
        "purpose": "Recommendation summary",
        "version": 1,
    },
    "PROMPT-G3-002": {
        "purpose": "Writing assist",
        "version": 1,
    },
    "PROMPT-G3-003": {
        "purpose": "Safety fallback response",
        "version": 1,
    },
}


def get_prompt_template(prompt_id: str) -> dict[str, Any] | None:
    return _PROMPT_TEMPLATES.get(prompt_id)


class AIService:
    """AI request orchestrator with pluggable provider backends."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.env = settings.app_env
        self.repo = AIRepository(db)
        self.audit = AuditService(db)
        self._provider = create_ai_provider(settings)

    def _resolve_language(self, text: str, explicit_language: str | None = None) -> str:
        normalized = str(explicit_language or "").lower()
        if normalized in {"fr", "ar", "en"}:
            return normalized
        if any("\u0600" <= char <= "\u06ff" for char in text):
            return "ar"
        lowered = text.lower()
        if any(
            token in lowered for token in (" le ", " la ", " les ", " pour ", " avec ")
        ):
            return "fr"
        return "en"

    async def process_writing_assist(
        self,
        *,
        text: str,
        subject: str | None = None,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        language: str | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        request_type = "writing_assist"

        try:
            sanitized_text, _, warnings = validate_ai_input(
                text, request_type=request_type
            )
            prompt_template = get_prompt_template("PROMPT-G3-002")
            if prompt_template is None:
                return get_fallback_response(request_type, "missing_prompt_template")

            resolved_language = self._resolve_language(sanitized_text, language)
            result = await self._provider.analyze_writing(
                sanitized_text, resolved_language
            )
            validated, is_valid = validate_ai_output(
                result,
                expected_fields={"suggestion", "hints"},
            )
            if not is_valid:
                AI_ERROR_COUNT.labels(
                    env=self.env,
                    request_type=request_type,
                    error_type="invalid_output",
                ).inc()
                return get_fallback_response(request_type, "invalid_output")

            suggestion = validated.get("suggestion") or ""
            if suggestion:
                is_safe, violation = check_content_safety(suggestion)
                if not is_safe:
                    AI_ERROR_COUNT.labels(
                        env=self.env,
                        request_type=request_type,
                        error_type="safety_violation",
                    ).inc()
                    return get_fallback_response(request_type, f"safety:{violation}")

            AI_REQUEST_COUNT.labels(
                env=self.env,
                request_type=request_type,
                status="completed",
            ).inc()
            return {
                "status": "completed",
                "suggestion": validated.get("suggestion"),
                "hints": validated.get("hints", []),
                "prompt_id": "PROMPT-G3-002",
                "prompt_version": prompt_template["version"],
                "warnings": warnings,
            }
        except Exception:
            logger.exception("AI writing assist failed")
            AI_ERROR_COUNT.labels(
                env=self.env,
                request_type=request_type,
                error_type="exception",
            ).inc()
            return get_fallback_response(request_type, "exception")
        finally:
            AI_LATENCY.labels(env=self.env, request_type=request_type).observe(
                time.perf_counter() - start
            )

    async def process_recommendation(
        self,
        *,
        student_id: uuid.UUID,
        school_id: uuid.UUID,
        completed_count: int = 0,
        level_band: str | None = None,
        recent_topics: list[str] | None = None,
        average_grade: float | None = None,
    ) -> dict[str, Any]:
        start = time.perf_counter()
        request_type = "recommendation"

        try:
            prompt_template = get_prompt_template("PROMPT-G3-001")
            if prompt_template is None:
                return get_fallback_response(request_type, "missing_prompt_template")

            recommendations = await self._provider.generate_recommendations(
                {
                    "student_id": str(student_id),
                    "school_id": str(school_id),
                    "completed_count": completed_count,
                    "level_band": level_band,
                    "recent_topics": recent_topics or [],
                    "average_grade": average_grade,
                }
            )

            for item in recommendations:
                if "reason_code" not in item:
                    AI_ERROR_COUNT.labels(
                        env=self.env,
                        request_type=request_type,
                        error_type="missing_reason_code",
                    ).inc()
                    return get_fallback_response(request_type, "missing_reason_code")

            AI_REQUEST_COUNT.labels(
                env=self.env,
                request_type=request_type,
                status="completed",
            ).inc()
            return {
                "status": "completed",
                "recommendations": recommendations,
                "prompt_id": "PROMPT-G3-001",
                "prompt_version": prompt_template["version"],
                "expires_at": None,
            }
        except Exception:
            logger.exception("AI recommendation failed")
            AI_ERROR_COUNT.labels(
                env=self.env,
                request_type=request_type,
                error_type="exception",
            ).inc()
            return get_fallback_response(request_type, "exception")
        finally:
            AI_LATENCY.labels(env=self.env, request_type=request_type).observe(
                time.perf_counter() - start
            )

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
            async with UnitOfWork(self.db) as uow:
                repo = AIRepository(uow.session)
                attempt = await repo.create_writing_attempt(
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
                await uow.commit()
            emit_event(
                "ai_fallback_used",
                actor_id=auth.user_id,
                actor_role=auth.role,
                properties={"reason": "opt_out", "request_type": "writing_assist"},
            )
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
            language=getattr(body, "language", None),
        )
        async with UnitOfWork(self.db) as uow:
            repo = AIRepository(uow.session)
            audit = AuditService(uow.session)
            attempt = await repo.create_writing_attempt(
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
            await audit.log_event(
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
            await uow.commit()
        emit_event(
            "writing_attempt_created",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={
                "subject": body.subject or "general",
                "word_count": attempt.input_word_count,
            },
        )
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
        else:
            old_value = None
            existing = AIPreference(
                user_id=auth.user_id,
                target_user_id=target_user_id,
                school_id=auth.school_id,
                opt_out=body.opt_out,
            )

        action = "opt_out" if body.opt_out else "opt_in"
        AI_OPT_OUT_COUNT.labels(env=settings.app_env, action=action).inc()
        async with UnitOfWork(self.db) as uow:
            repo = AIRepository(uow.session)
            audit = AuditService(uow.session)
            preference = await repo.save_ai_preference(existing)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="AI_OPT_OUT_UPDATED",
                outcome="success",
                target_type="ai_preference",
                target_id=preference.id,
                entity_before={"opt_out": old_value} if old_value is not None else None,
                entity_after={
                    "opt_out": body.opt_out,
                    "target_user_id": str(target_user_id),
                },
                ip_address=client_ip,
            )
            await uow.commit()
        emit_event(
            "ai_opt_out_updated",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={
                "opt_out": body.opt_out,
                "target_user_id_hash": pseudonymize_actor_id(target_user_id),
            },
        )
        return {
            "id": str(preference.id),
            "user_id": str(preference.user_id),
            "target_user_id": str(preference.target_user_id),
            "opt_out": preference.opt_out,
            "updated_at": (
                preference.updated_at.isoformat()
                if preference.updated_at
                else preference.created_at.isoformat()
            ),
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
        try:
            insights = await self._provider.compute_kpi_insights(
                {"kpis": kpis, "period": period}
            )
            logger.debug("Computed %d KPI insights from provider", len(insights))
        except Exception:
            logger.exception("AI KPI insights failed; returning raw KPIs only")
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
                    "pii_risk": (
                        "medium"
                        if "invoice" in event_name or "payment" in event_name
                        else "low"
                    ),
                    "status": "known",
                }
            )
        return {
            "schema_version": SCHEMA_VERSION,
            "events": events,
            "total": len(events),
        }
