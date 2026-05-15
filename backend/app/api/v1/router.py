"""API v1 router — aggregates all sub-routers and health check.

Reference: Pack D5 — API Implementation Plan
Routes:
  /health                       — Health check (public)
  /auth/*                       — Authentication (login, refresh, logout, me)
  /schools/*                    — School management
  /invites/*                    — Invitation code management
  /recovery/*                   — Account recovery flow
  /classes/*                    — Class endpoints (ERP)
  /enrollments/*                — Enrollment endpoints (ERP)
  /class-assignments/*          — Teacher assignment endpoints (ERP)
  /attendance/*                 — Attendance + justifications (ERP)
  /analytics/attendance/*       — Attendance analytics + alerts (ERP)
  /courses/*                    — Course endpoints (LMS)
  /assignments/*                — Assignment endpoints (LMS)
  /submissions/*                — Submission + grading (LMS)
  /results/*                    — Results listing (LMS)
  /content-items/*              — Content items + progress (LMS)
  /student-work/*               — Unified student work views (LMS)
  /activities/*                 — Activities + sessions (LMS)
  /assessments/*                — Assessments + results (LMS)
  /rubrics/*                    — Rubric engine (LMS)
  /gradebook/*                  — Weighted gradebook (LMS)
  /question-bank/*              — Reusable quiz question bank (LMS)
  /invoices/*                   — Invoice listing (Billing)
  /payments/*                   — Payment + webhook (Billing)
  /notifications/*              — Notifications (COM)
  /consents/*                   — Consent preferences (COM)
  /feed/*                       — Parent feed (COM)
  /timetable/*                  — Timetable slots, exceptions, constraints, generation (ERP)
  /billing/*                    — Fee structures, assignments, invoice generation, policies, payment plans
  /budgets/*                    — Class micro-budget envelopes, allocations, requests, transactions, analytics
  /skills/*                     — Life-skills dimensions, milestones, evaluation, passports, analytics
  /rewards/*                    — Student rewards, XP, badges, and class leaderboards
  /games/*                      — Mobile game configs, filters, and completion rewards
  /compliance/*                 — MEN curriculum mapping, dashboards, and compliance reports
  /sync/*                       — Local-first device registration, queue push/pull, conflicts, checkpoints
  /financial-health/*           — Retention, cashflow, cost-per-student, snapshots, exports
  /messages/*                   — Conversations + messaging (Phase 11C)
  /announcements/*              — Announcements CRUD + publish (Phase 11C)
  /progress/*                   — Student progress visualization (Phase 11D)
  /features/*                   — Feature toggles management (Phase 11E)
  /events/*                     — Calendar events, RSVP, reminders (Phase 15)
  /calendar/*                   — Calendar feeds and options (Phase 15)
  /micro/*                      — Micro-school management, enrollments, payments, resources, progress
"""

from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

# Phase 2 routers
from app.api.v1.auth.auth import router as auth_router
from app.api.v1.auth.webauthn import router as webauthn_router
from app.api.v1.auth.oauth import router as oauth_router
from app.api.v1.auth.sms_2fa import router as sms_2fa_router
from app.api.v1.school.classes import router as classes_router
from app.api.v1.lms.enrollments import router as enrollments_router
from app.api.v1.admin.invitations import router as invitations_router
from app.api.v1.user.recovery import router as recovery_router
from app.api.v1.school.schools import router as schools_router

# Phase 3 — ERP routers
from app.api.v1.lms.class_assignments import router as class_assignments_router
from app.api.v1.academic.attendance import router as attendance_router
from app.api.v1.reports.attendance_analytics import router as attendance_analytics_router

# Phase 3 — LMS routers
from app.api.v1.lms.courses import router as courses_router
from app.api.v1.lms.assignments import router as assignments_router
from app.api.v1.lms.submissions import router as submissions_router
from app.api.v1.academic.results import router as results_router
from app.api.v1.lms.content import legacy_router as legacy_content_router
from app.api.v1.lms.content import router as content_router
from app.api.v1.lms.content import student_work_router
from app.api.v1.ai.activities import router as activities_router
from app.api.v1.lms.assessments import router as assessments_router
from app.api.v1.academic.gradebook import router as gradebook_router
from app.api.v1.lms.question_bank import router as question_bank_router
from app.api.v1.lms.rubrics import router as rubrics_router

# Phase 3 — Billing routers
from app.api.v1.billing.invoices import router as invoices_router
from app.api.v1.billing.payments import router as payments_router

# Phase 3 — COM routers
from app.api.v1.user.devices import router as devices_router
from app.api.v1.communication.notifications import router as notifications_router
from app.api.v1.user.consents import router as consents_router
from app.api.v1.content.feed import router as feed_router

# Phase 3C — WebSocket
from app.api.v1.ws import router as ws_router

# Phase 4A — Admin dashboard
from app.api.v1.admin.admin import router as admin_router

# Phase 4B — Teacher dashboard
from app.api.v1.academic.teacher import router as teacher_router

# Phase 8 — AI & Data routers
from app.api.v1.ai.ai import router as ai_router

# Phase 8A — GDPR compliance
from app.api.v1.user.gdpr import router as gdpr_router

# Phase 1B — Role-specific profiles
from app.api.v1.user.profiles import router as profiles_router

# Phase 9A — CMS + Content Library
from app.api.v1.content.cms import router as cms_router
from app.api.v1.content.content_library import router as content_library_router

# Phase 9B — Quiz Engine
from app.api.v1.lms.quizzes import router as quizzes_router

# Phase 11A — Timetable
from app.api.v1.academic.timetable import router as timetable_router
from app.api.v1.academic.timetable_generation import router as timetable_generation_router

# Phase 11B — Billing Enhancements
from app.api.v1.billing.billing import router as billing_router
from app.api.v1.billing.budgets import router as budgets_router
from app.api.v1.admin.compliance import router as compliance_router
from app.api.v1.reports.financial_health import router as financial_health_router
from app.api.v1.ai.games import router as games_router
from app.api.v1.school.micro_school import router as micro_school_router
from app.api.v1.ai.rewards import router as rewards_router
from app.api.v1.academic.skills import router as skills_router
from app.api.v1.sync.sync import router as sync_router

# Phase 11C — Messaging & Announcements
from app.api.v1.communication.messaging import router as messaging_router
from app.api.v1.admin.announcements import router as announcements_router

# Phase 11D — Student Progress
from app.api.v1.academic.progress import router as progress_router

# Phase 11E — Feature Toggles
from app.api.v1.admin.features import router as features_router

# Phase 14 — Reports & Analytics
from app.api.v1.reports.analytics import router as analytics_router
from app.api.v1.content.exports import router as exports_router
from app.api.v1.reports.reports import router as reports_router

# Phase 15 — Calendar & Events
from app.api.v1.admin.events import router as events_router

# Phase 16 — Documents
from app.api.v1.content.documents import router as documents_router

# Phase 8 — Direct uploads
from app.api.v1.content.uploads import router as uploads_router

# Phase B1 — Shared Review (parent-child)
from app.api.v1.lms.shared_review import router as shared_review_router

# G46 — Level-age mappings
from app.api.v1.lms.levels import router as levels_router

# G49 — Academic Program Management & Student Academic History
from app.api.v1.lms.programs import (
    enrollment_program_router as enrollment_program_router,
    program_equivalences_router as program_equivalences_router,
    programs_router as programs_router,
)
from app.api.v1.content.snapshots import (
    snapshots_router as snapshots_router,
    student_snapshots_router as student_snapshots_router,
)
from app.api.v1.lms.eligibility import (
    eligibility_router as eligibility_router,
    student_eligibility_router as student_eligibility_router,
)
from app.api.v1.academic.student_academic import router as student_academic_router
from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str
    version: str
    timestamp: str


class ReadinessResponse(BaseModel):
    """Readiness probe response payload."""

    status: str
    checks: dict[str, str]
    timestamp: str


# Health check (public, no auth)
@router.get(
    "/health",
    response_model=HealthResponse,
    tags=["system"],
    summary="Health check",
    response_description="Service status, version, and timestamp",
)
async def health_check():
    """Health check endpoint.

    Returns service status and version. Used by Docker health checks
    and monitoring systems (Pack F2).
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    tags=["system"],
    summary="Readiness probe",
    response_description="Database and Redis connectivity status",
)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """Readiness probe for container orchestration.

    Verifies that both PostgreSQL and Redis are reachable.
    Returns 200 if all dependencies are healthy, 503 if any are down.
    Used by Kubernetes readiness probes and load balancers.
    """
    checks: dict[str, str] = {}
    all_ok = True

    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar_one()
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {str(exc)[:100]}"
        all_ok = False

    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {str(exc)[:100]}"
        all_ok = False

    payload = ReadinessResponse(
        status="ready" if all_ok else "degraded",
        checks=checks,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    return JSONResponse(
        status_code=200 if all_ok else 503,
        content=payload.model_dump(mode="json"),
    )


@router.get(
    "/sentry-debug",
    tags=["system"],
    summary="Trigger a test error for Sentry",
    response_description="Intentionally raises an error to verify Sentry capture",
)
async def sentry_debug():
    """Trigger a ZeroDivisionError to verify Sentry error reporting."""
    from app.core.config import settings
    if settings.is_production:
        return {"error": "Debug endpoint disabled in production"}
    division_by_zero = 1 / 0  # noqa: F841
    return {"ok": True}


# Mount sub-routers — Phase 2
router.include_router(auth_router)
router.include_router(webauthn_router)
router.include_router(oauth_router)
router.include_router(sms_2fa_router)
router.include_router(schools_router)
router.include_router(invitations_router)
router.include_router(recovery_router)
router.include_router(classes_router)
router.include_router(enrollments_router)

# Mount sub-routers — Phase 3 ERP
router.include_router(class_assignments_router)
router.include_router(attendance_router)
router.include_router(attendance_analytics_router)

# Mount sub-routers — Phase 3 LMS
router.include_router(courses_router)
router.include_router(assignments_router)
router.include_router(submissions_router)
router.include_router(results_router)
router.include_router(content_router)
router.include_router(legacy_content_router)
router.include_router(student_work_router)
router.include_router(activities_router)
router.include_router(assessments_router)
router.include_router(rubrics_router)
router.include_router(gradebook_router)
router.include_router(question_bank_router)

# Mount sub-routers — Phase 3 Billing
router.include_router(invoices_router)
router.include_router(payments_router)

# Mount sub-routers — Phase 3 COM
router.include_router(notifications_router)
router.include_router(devices_router)
router.include_router(consents_router)
router.include_router(feed_router)

# Mount sub-routers — Phase 3C WebSocket
router.include_router(ws_router)

# Mount sub-routers — Phase 4A Admin
router.include_router(admin_router)

# Mount sub-routers — Phase 4B Teacher
router.include_router(teacher_router)

# Mount sub-routers — Phase 8 AI & Data
router.include_router(ai_router)

# Mount sub-routers — Phase 8A GDPR
router.include_router(gdpr_router)

# Mount sub-routers — Phase 1B Profiles
router.include_router(profiles_router)

# Mount sub-routers — Phase 9A CMS + Content Library
router.include_router(cms_router)
router.include_router(content_library_router)

# Mount sub-routers — Phase 9B Quiz Engine
router.include_router(quizzes_router)

# Mount sub-routers — Phase 11A Timetable
router.include_router(timetable_router)
router.include_router(timetable_generation_router)

# Mount sub-routers — Phase 11B Billing Enhancements
router.include_router(billing_router)
router.include_router(budgets_router)
router.include_router(micro_school_router)
router.include_router(skills_router)
router.include_router(rewards_router)
router.include_router(games_router)
router.include_router(compliance_router)
router.include_router(sync_router)
router.include_router(financial_health_router)

# Mount sub-routers — Phase 11C Messaging & Announcements
router.include_router(messaging_router)
router.include_router(announcements_router)

# Mount sub-routers — Phase 11D Student Progress
router.include_router(progress_router)

# Mount sub-routers — Phase 11E Feature Toggles
router.include_router(features_router)

# Mount sub-routers — Phase 14 Reports & Analytics
router.include_router(reports_router)
router.include_router(exports_router)
router.include_router(analytics_router)

# Mount sub-routers — Phase 15 Calendar & Events
router.include_router(events_router)

# Mount sub-routers — Phase 16 Documents
router.include_router(documents_router)

# Mount sub-routers — Phase 8 Direct uploads
router.include_router(uploads_router)

# Mount sub-routers — Phase B1 Shared Review
router.include_router(shared_review_router)

# Mount sub-routers — G46 Level-age mappings
router.include_router(levels_router)

# Mount sub-routers — G49 Academic Program Management
router.include_router(programs_router)
router.include_router(enrollment_program_router)
router.include_router(program_equivalences_router)
router.include_router(snapshots_router)
router.include_router(student_snapshots_router)
router.include_router(eligibility_router)
router.include_router(student_eligibility_router)
router.include_router(student_academic_router)
