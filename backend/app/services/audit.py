"""Audit trail service — async write to audit_logs table.

Reference: S-038 — Audit trail service, D6 — Security Enforcement
- All 401/403/404 (scope-masked) responses trigger audit with outcome=denied
- Sensitive allow events logged: payment state changes, support access grants, IA requests
- Correlation_id from X-Correlation-Id always included
- Actor_id null only for SYS-originated events (INV-AUDIT-ACTOR)
- Audit writes are async (don't block API response)
- Entity before/after snapshots stored as JSONB
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.middleware import get_correlation_id
from app.models.audit import AuditLog
from app.repositories.audit import AuditRepository

logger = logging.getLogger(__name__)


class AuditService:
    """Service for recording security-relevant events to audit_logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditRepository(db)

    async def log_event(
        self,
        *,
        school_id: uuid.UUID,
        action_type: str,
        outcome: str,
        actor_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: uuid.UUID | None = None,
        error_code: str | None = None,
        entity_before: dict[str, Any] | None = None,
        entity_after: dict[str, Any] | None = None,
        ip_address: str | None = None,
        correlation_id: uuid.UUID | None = None,
    ) -> AuditLog:
        """Write an audit event to the audit_logs table.

        This method commits to the database independently to ensure audit
        entries persist even if the main transaction rolls back.
        """
        # Use the request correlation ID if not explicitly provided
        cid = correlation_id
        if cid is None:
            raw_cid = get_correlation_id()
            if raw_cid:
                try:
                    cid = uuid.UUID(raw_cid)
                except ValueError:
                    cid = None

        entry = await self.repo.create_log(
            school_id=school_id,
            actor_id=actor_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            entity_before=entity_before,
            entity_after=entity_after,
            outcome=outcome,
            error_code=error_code,
            correlation_id=cid,
            ip_address=ip_address,
        )

        logger.info(
            "Audit: action=%s outcome=%s actor=%s target=%s/%s cid=%s",
            action_type,
            outcome,
            actor_id,
            target_type,
            target_id,
            cid,
        )
        return entry


# ---------------------------------------------------------------------------
# Convenience functions for common audit patterns
# ---------------------------------------------------------------------------
async def log_auth_event(
    db: AsyncSession,
    *,
    action_type: str,
    outcome: str,
    school_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    error_code: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Log an authentication/authorization event."""
    service = AuditService(db)
    return await service.log_event(
        school_id=school_id,
        action_type=action_type,
        outcome=outcome,
        actor_id=actor_id,
        target_type="session",
        error_code=error_code,
        ip_address=ip_address,
    )


async def log_deny_event(
    db: AsyncSession,
    *,
    action_type: str,
    school_id: uuid.UUID,
    actor_id: uuid.UUID | None = None,
    error_code: str = "ERR-AUTHZ-001",
    target_type: str | None = None,
    target_id: uuid.UUID | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Log a denied access event (401/403/404)."""
    service = AuditService(db)
    return await service.log_event(
        school_id=school_id,
        action_type=action_type,
        outcome="denied",
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        error_code=error_code,
        ip_address=ip_address,
    )
