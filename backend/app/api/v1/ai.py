"""AI & Data endpoints — writing assistance, opt-out, recommendations, KPIs.

Reference:
  S-142 — AI request endpoint with guardrails
  S-143 — Writing assistance endpoint (POST /writing-attempts)
  S-144 — AI opt-out preference (POST /ai/preferences/opt-out)
  S-145 — Learning recommendations (GET /recommendations)
  S-140 — KPI computation queries
  S-146 — Event schema registry
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.response import success_response
from app.models.ai import AIPreference, WritingAttempt
from app.schemas.ai import (
    AIOptOutRequest,
    WritingAttemptRequest,
)
from app.services.ai import AIService, AI_OPT_OUT_COUNT
from app.services.analytics import (
    SCHEMA_VERSION,
    emit_event,
    _EVENT_PROPERTY_WHITELIST,
)
from app.services.audit import AuditService
from app.services.kpi import compute_all_kpis

router = APIRouter(tags=["ai"])


def _get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


# ---------------------------------------------------------------------------
# S-143: POST /writing-attempts — Writing assistance (STD)
# ---------------------------------------------------------------------------
@router.post(
    "/writing-attempts",
    status_code=200,
    summary="Create writing attempt",
    response_description="AI writing feedback",
)
async def create_writing_attempt(
    body: WritingAttemptRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IA:writing-attempt:create")),
    db: AsyncSession = Depends(get_db),
):
    """Submit text for AI-assisted writing feedback.

    Guardrails (G3):
      - Input sanitized for PII (POL-G3-001)
      - Opt-out checked (POL-G3-002)
      - Output validated (POL-G3-003)
      - Audit trail recorded
    """
    audit = AuditService(db)
    ai_service = AIService()

    # Check opt-out preference (POL-G3-002)
    optout_result = await db.execute(
        select(AIPreference).where(
            AIPreference.target_user_id == auth.user_id,
            AIPreference.opt_out.is_(True),
        )
    )
    if optout_result.scalar_one_or_none() is not None:
        # User has opted out — return fallback without AI processing
        from app.services.ai import get_fallback_response

        fallback = get_fallback_response("writing_assist", "opt_out")

        # Still record the attempt
        attempt = WritingAttempt(
            student_id=auth.user_id,
            school_id=auth.school_id,
            subject=body.subject,
            input_text="[opted_out]",
            input_word_count=len(body.text.split()),
            status="fallback",
            prompt_id=None,
        )
        db.add(attempt)
        await db.flush()

        emit_event(
            "ai_fallback_used",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={"reason": "opt_out", "request_type": "writing_assist"},
        )

        return success_response(
            {
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
        )

    # Process with AI service
    result = await ai_service.process_writing_assist(
        text=body.text,
        subject=body.subject,
        student_id=auth.user_id,
        school_id=auth.school_id,
    )

    # Persist attempt
    attempt = WritingAttempt(
        student_id=auth.user_id,
        school_id=auth.school_id,
        subject=body.subject,
        input_text=body.text[:500],  # Truncate for storage (privacy)
        input_word_count=len(body.text.split()),
        status=result.get("status", "completed"),
        suggestion=result.get("suggestion"),
        hints=result.get("hints"),
        prompt_id=result.get("prompt_id"),
        prompt_version=result.get("prompt_version"),
        warnings=result.get("warnings"),
    )
    db.add(attempt)
    await db.flush()

    # Audit
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
        ip_address=_get_client_ip(request),
    )

    # Analytics event
    emit_event(
        "writing_attempt_created",
        actor_id=auth.user_id,
        actor_role=auth.role,
        properties={
            "subject": body.subject or "general",
            "word_count": attempt.input_word_count,
        },
    )

    return success_response(
        {
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
    )


# ---------------------------------------------------------------------------
# S-144: POST /ai/preferences/opt-out — AI opt-out (PAR)
# ---------------------------------------------------------------------------
@router.post(
    "/ai/preferences/opt-out",
    status_code=200,
    summary="Update AI opt-out preference",
    response_description="Updated AI preferences",
)
async def update_ai_opt_out(
    body: AIOptOutRequest,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IA:preference:update")),
    db: AsyncSession = Depends(get_db),
):
    """Update AI personalization opt-out preference.

    Parents can opt out of AI personalization for their children.
    Per G3.3: POST /ai/preferences/opt-out is contractual in OpenAPI.
    Idempotent — upserts the preference.
    """
    audit = AuditService(db)
    target_user_id = body.target_user_id or auth.user_id

    # Upsert preference
    existing_result = await db.execute(
        select(AIPreference).where(
            AIPreference.user_id == auth.user_id,
            AIPreference.target_user_id == target_user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing is not None:
        old_value = existing.opt_out
        existing.opt_out = body.opt_out
        await db.flush()
        pref = existing
    else:
        pref = AIPreference(
            user_id=auth.user_id,
            target_user_id=target_user_id,
            school_id=auth.school_id,
            opt_out=body.opt_out,
        )
        db.add(pref)
        await db.flush()
        old_value = None

    # Metrics
    action = "opt_out" if body.opt_out else "opt_in"
    from app.core.config import settings

    AI_OPT_OUT_COUNT.labels(env=settings.app_env, action=action).inc()

    # Audit
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="AI_OPT_OUT_UPDATED",
        outcome="success",
        target_type="ai_preference",
        target_id=pref.id,
        entity_before={"opt_out": old_value} if old_value is not None else None,
        entity_after={"opt_out": body.opt_out, "target_user_id": str(target_user_id)},
        ip_address=_get_client_ip(request),
    )

    # Analytics event (G3.3)
    from app.services.analytics import pseudonymize_actor_id

    emit_event(
        "ai_opt_out_updated",
        actor_id=auth.user_id,
        actor_role=auth.role,
        properties={
            "opt_out": body.opt_out,
            "target_user_id_hash": pseudonymize_actor_id(target_user_id),
        },
    )

    return success_response(
        {
            "id": str(pref.id),
            "user_id": str(pref.user_id),
            "target_user_id": str(pref.target_user_id),
            "opt_out": pref.opt_out,
            "updated_at": pref.updated_at.isoformat()
            if pref.updated_at
            else pref.created_at.isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# S-145: GET /recommendations — Learning recommendations (STD, PAR)
# ---------------------------------------------------------------------------
@router.get(
    "/recommendations",
    summary="Get learning recommendations",
    response_description="Personalized recommendations",
)
async def get_recommendations(
    auth: AuthContext = Depends(requires_permission("PERM-IA:recommendation:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized learning recommendations.

    Guardrails:
      - Opt-out checked (POL-G3-002): returns empty if opted out
      - Reason code mandatory on each recommendation (G3)
    """
    ai_service = AIService()

    # Check opt-out (POL-G3-002)
    optout_result = await db.execute(
        select(AIPreference).where(
            AIPreference.target_user_id == auth.user_id,
            AIPreference.opt_out.is_(True),
        )
    )
    if optout_result.scalar_one_or_none() is not None:
        emit_event(
            "ai_fallback_used",
            actor_id=auth.user_id,
            actor_role=auth.role,
            properties={"reason": "opt_out", "request_type": "recommendation"},
        )
        return success_response(
            {
                "status": "fallback",
                "recommendations": [],
                "prompt_id": None,
                "prompt_version": None,
                "expires_at": None,
                "message": "AI recommendations disabled by preference.",
            }
        )

    # Get student activity stats for context
    from app.models.lms import ContentProgress

    progress_result = await db.execute(
        select(func.count()).where(
            ContentProgress.student_id == auth.user_id,
            ContentProgress.status == "completed",
        )
    )
    completed_count = progress_result.scalar() or 0

    # Process recommendations
    result = await ai_service.process_recommendation(
        student_id=auth.user_id,
        school_id=auth.school_id,
        completed_count=completed_count,
    )

    # Analytics
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

    return success_response(result)


# ---------------------------------------------------------------------------
# S-140: GET /kpis — KPI dashboard (ADM)
# ---------------------------------------------------------------------------
@router.get(
    "/kpis",
    summary="Get school KPIs",
    response_description="Key performance indicators",
)
async def get_kpis(
    period: int = Query(default=7, ge=1, le=90, description="Period in days"),
    auth: AuthContext = Depends(requires_permission("PERM-IA:request:read")),
    db: AsyncSession = Depends(get_db),
):
    """Get computed KPIs for the school (G1 catalog).

    Returns KPI-G1-001 through KPI-G1-006 for the specified period.
    ADM, DIR, TCH roles can access.
    """
    kpis = await compute_all_kpis(db, school_id=auth.school_id, period_days=period)

    return success_response(
        {
            "kpis": kpis,
            "period": f"{period}d",
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# S-146: GET /events/schema — Event schema registry
# ---------------------------------------------------------------------------
@router.get(
    "/events/schema",
    summary="Get analytics event schema",
    response_description="Event schema definition",
)
async def get_event_schema(
    auth: AuthContext = Depends(requires_permission("PERM-IA:request:read")),
):
    """Get the analytics event schema registry.

    Returns all known events with their schema versions and property whitelists.
    Used for CI drift detection (S-146).
    """
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

    return success_response(
        {
            "schema_version": SCHEMA_VERSION,
            "events": events,
            "total": len(events),
        }
    )
