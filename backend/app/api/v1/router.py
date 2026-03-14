"""API v1 router with health check endpoint.

Reference: Pack D5 — API Implementation Plan
"""

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()


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
