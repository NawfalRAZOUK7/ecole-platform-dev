"""API v1 router — aggregates all sub-routers and health check.

Reference: Pack D5 — API Implementation Plan
Routes:
  /health                       — Health check (public)
  /auth/*                       — Authentication (login, refresh, logout, me)
  /invites/*                    — Invitation code management
  /recovery/*                   — Account recovery flow
  /classes/*                    — Class endpoints (ERP)
  /enrollments/*                — Enrollment endpoints (ERP)
  /class-assignments/*          — Teacher assignment endpoints (ERP)
  /attendance/*                 — Attendance + justifications (ERP)
  /courses/*                    — Course endpoints (LMS)
  /assignments/*                — Assignment endpoints (LMS)
  /submissions/*                — Submission + grading (LMS)
  /results/*                    — Results listing (LMS)
  /content-items/*              — Content items + progress (LMS)
  /activities/*                 — Activities + sessions (LMS)
  /assessments/*                — Assessments + results (LMS)
  /invoices/*                   — Invoice listing (Billing)
  /payments/*                   — Payment + webhook (Billing)
  /notifications/*              — Notifications (COM)
  /consents/*                   — Consent preferences (COM)
  /feed/*                       — Parent feed (COM)
  /timetable/*                  — Timetable slots + exceptions (ERP, Phase 11A)
  /billing/*                    — Fee structures, assignments, invoice generation (Phase 11B)
  /messages/*                   — Conversations + messaging (Phase 11C)
  /announcements/*              — Announcements CRUD + publish (Phase 11C)
  /progress/*                   — Student progress visualization (Phase 11D)
  /features/*                   — Feature toggles management (Phase 11E)
"""

from datetime import datetime, timezone

from fastapi import APIRouter

# Phase 2 routers
from app.api.v1.auth import router as auth_router
from app.api.v1.classes import router as classes_router
from app.api.v1.enrollments import router as enrollments_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.recovery import router as recovery_router

# Phase 3 — ERP routers
from app.api.v1.class_assignments import router as class_assignments_router
from app.api.v1.attendance import router as attendance_router

# Phase 3 — LMS routers
from app.api.v1.courses import router as courses_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.submissions import router as submissions_router
from app.api.v1.results import router as results_router
from app.api.v1.content import legacy_router as legacy_content_router
from app.api.v1.content import router as content_router
from app.api.v1.activities import router as activities_router
from app.api.v1.assessments import router as assessments_router

# Phase 3 — Billing routers
from app.api.v1.invoices import router as invoices_router
from app.api.v1.payments import router as payments_router

# Phase 3 — COM routers
from app.api.v1.devices import router as devices_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.consents import router as consents_router
from app.api.v1.feed import router as feed_router

# Phase 3C — WebSocket
from app.api.v1.ws import router as ws_router

# Phase 4A — Admin dashboard
from app.api.v1.admin import router as admin_router

# Phase 4B — Teacher dashboard
from app.api.v1.teacher import router as teacher_router

# Phase 8 — AI & Data routers
from app.api.v1.ai import router as ai_router

# Phase 8A — GDPR compliance
from app.api.v1.gdpr import router as gdpr_router

# Phase 1B — Role-specific profiles
from app.api.v1.profiles import router as profiles_router

# Phase 9A — CMS + Content Library
from app.api.v1.cms import router as cms_router
from app.api.v1.content_library import router as content_library_router

# Phase 9B — Quiz Engine
from app.api.v1.quizzes import router as quizzes_router

# Phase 11A — Timetable
from app.api.v1.timetable import router as timetable_router

# Phase 11B — Billing Enhancements
from app.api.v1.billing import router as billing_router

# Phase 11C — Messaging & Announcements
from app.api.v1.messaging import router as messaging_router
from app.api.v1.announcements import router as announcements_router

# Phase 11D — Student Progress
from app.api.v1.progress import router as progress_router

# Phase 11E — Feature Toggles
from app.api.v1.features import router as features_router

router = APIRouter()


# Health check (public, no auth)
@router.get(
    "/health",
    tags=["system"],
    summary="Health check",
    response_description="Service status, version, and timestamp",
)
async def health_check():
    """Health check endpoint.

    Returns service status and version. Used by Docker health checks
    and monitoring systems (Pack F2).
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Mount sub-routers — Phase 2
router.include_router(auth_router)
router.include_router(invitations_router)
router.include_router(recovery_router)
router.include_router(classes_router)
router.include_router(enrollments_router)

# Mount sub-routers — Phase 3 ERP
router.include_router(class_assignments_router)
router.include_router(attendance_router)

# Mount sub-routers — Phase 3 LMS
router.include_router(courses_router)
router.include_router(assignments_router)
router.include_router(submissions_router)
router.include_router(results_router)
router.include_router(content_router)
router.include_router(legacy_content_router)
router.include_router(activities_router)
router.include_router(assessments_router)

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

# Mount sub-routers — Phase 11B Billing Enhancements
router.include_router(billing_router)

# Mount sub-routers — Phase 11C Messaging & Announcements
router.include_router(messaging_router)
router.include_router(announcements_router)

# Mount sub-routers — Phase 11D Student Progress
router.include_router(progress_router)

# Mount sub-routers — Phase 11E Feature Toggles
router.include_router(features_router)
