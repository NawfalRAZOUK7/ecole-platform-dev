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
from app.api.v1.content import router as content_router
from app.api.v1.activities import router as activities_router
from app.api.v1.assessments import router as assessments_router

# Phase 3 — Billing routers
from app.api.v1.invoices import router as invoices_router
from app.api.v1.payments import router as payments_router

# Phase 3 — COM routers
from app.api.v1.notifications import router as notifications_router
from app.api.v1.consents import router as consents_router
from app.api.v1.feed import router as feed_router

router = APIRouter()


# Health check (public, no auth)
@router.get("/health")
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
router.include_router(activities_router)
router.include_router(assessments_router)

# Mount sub-routers — Phase 3 Billing
router.include_router(invoices_router)
router.include_router(payments_router)

# Mount sub-routers — Phase 3 COM
router.include_router(notifications_router)
router.include_router(consents_router)
router.include_router(feed_router)
