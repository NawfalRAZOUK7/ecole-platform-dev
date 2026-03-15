"""API v1 router — aggregates all sub-routers and health check.

Reference: Pack D5 — API Implementation Plan
Routes:
  /health         — Health check (public)
  /auth/*         — Authentication (login, refresh, logout, me)
  /invites/*      — Invitation code management
  /recovery/*     — Account recovery flow
  /classes/*      — Class endpoints (ERP)
  /enrollments/*  — Enrollment endpoints (ERP)
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.classes import router as classes_router
from app.api.v1.enrollments import router as enrollments_router
from app.api.v1.invitations import router as invitations_router
from app.api.v1.recovery import router as recovery_router

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


# Mount sub-routers
router.include_router(auth_router)
router.include_router(invitations_router)
router.include_router(recovery_router)
router.include_router(classes_router)
router.include_router(enrollments_router)
