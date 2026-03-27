"""GDPR compliance endpoints — data export, data deletion (anonymization), consent log.

Reference: Phase 8A — GDPR Compliance
Endpoints:
  GET  /users/{id}/data-export  — Export all user data as JSON (ADM or self)
  POST /users/{id}/data-deletion — Anonymize PII, keep audit structure (ADM only)
  GET  /users/{id}/consent-log   — Full consent change history
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import AuthContext, requires_permission
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.response import success_response
from app.core.request_utils import get_client_ip
from app.models.audit import AuditLog
from app.models.billing import Invoice
from app.models.com import ConsentPreference, Notification
from app.models.iam import Membership, Session, User
from app.models.lms import Grade, Submission
from app.services.audit import AuditService

router = APIRouter(prefix="/users", tags=["gdpr"])

# Permission: ADM can access any user, others can only access self
ADMIN_ROLES = ("ADM", "DIR")



def _anonymize(value: str) -> str:
    """Hash a PII value for anonymization. One-way, deterministic."""
    return hashlib.sha256(f"anon:{value}".encode()).hexdigest()[:16]


async def _get_target_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    auth: AuthContext,
    *,
    admin_only: bool = False,
) -> User:
    """Fetch target user, enforcing access: ADM or self (unless admin_only)."""
    is_admin = auth.role in ADMIN_ROLES
    is_self = auth.user_id == user_id

    if admin_only and not is_admin:
        raise AuthorizationError(
            "Only administrators can perform this action",
            error_code="ERR-GDPR-403",
        )

    if not is_admin and not is_self:
        raise AuthorizationError(
            "You can only access your own data",
            error_code="ERR-GDPR-403",
        )

    user = (
        await db.execute(
            select(User).where(
                User.id == user_id,
                User.school_id == auth.school_id,
            )
        )
    ).scalar_one_or_none()

    if user is None:
        raise NotFoundError("User not found", error_code="ERR-GDPR-404")

    return user


# ---------------------------------------------------------------------------
# GET /users/{user_id}/data-export
# ---------------------------------------------------------------------------
@router.get("/{user_id}/data-export", summary="Export all user data (GDPR)")
async def data_export(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:session:list")),
    db: AsyncSession = Depends(get_db),
):
    """Export complete user data as JSON. Available to ADM or the user themselves.

    Includes: profile, memberships, sessions, audit logs, submissions,
    grades, notifications, invoices, payments, consent preferences.
    """
    user = await _get_target_user(db, user_id, auth)

    # --- Profile ---
    profile = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
        "school_id": str(user.school_id),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "email_verified_at": user.email_verified_at.isoformat()
        if user.email_verified_at
        else None,
        "totp_enabled": user.totp_enabled,
    }

    # --- Memberships ---
    memberships_result = await db.execute(
        select(Membership).where(Membership.user_id == user_id)
    )
    memberships = [
        {
            "id": str(m.id),
            "school_id": str(m.school_id),
            "role_code": m.role_code,
            "status": m.status,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in memberships_result.scalars().all()
    ]

    # --- Sessions ---
    sessions_result = await db.execute(
        select(Session)
        .where(Session.user_id == user_id)
        .order_by(Session.created_at.desc())
        .limit(100)
    )
    sessions = [
        {
            "id": str(s.id),
            "source": s.source,
            "device_name": s.device_name,
            "ip_address": s.ip_address,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "revoke_at": s.revoke_at.isoformat() if s.revoke_at else None,
        }
        for s in sessions_result.scalars().all()
    ]

    # --- Audit logs (where user is actor) ---
    audit_result = await db.execute(
        select(AuditLog)
        .where(AuditLog.actor_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )
    audit_logs = [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "outcome": a.outcome,
            "target_type": a.target_type,
            "target_id": str(a.target_id) if a.target_id else None,
            "ip_address": a.ip_address,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audit_result.scalars().all()
    ]

    # --- Submissions ---
    submissions_result = await db.execute(
        select(Submission)
        .where(Submission.student_id == user_id)
        .order_by(Submission.created_at.desc())
        .limit(200)
    )
    submissions = [
        {
            "id": str(sub.id),
            "assignment_id": str(sub.assignment_id),
            "status": sub.status,
            "submitted_at": sub.submitted_at.isoformat() if sub.submitted_at else None,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }
        for sub in submissions_result.scalars().all()
    ]

    # --- Grades ---
    grades_result = await db.execute(
        select(Grade)
        .where(Grade.student_id == user_id)
        .order_by(Grade.created_at.desc())
        .limit(200)
    )
    grades = [
        {
            "id": str(g.id),
            "submission_id": str(g.submission_id),
            "score": float(g.score) if g.score is not None else None,
            "feedback_text": g.feedback_text,
            "published_at": g.published_at.isoformat() if g.published_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        }
        for g in grades_result.scalars().all()
    ]

    # --- Notifications ---
    notifications_result = await db.execute(
        select(Notification)
        .where(Notification.recipient_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(200)
    )
    notifications = [
        {
            "id": str(n.id),
            "type": n.type,
            "subject": n.subject,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifications_result.scalars().all()
    ]

    # --- Invoices ---
    invoices_result = await db.execute(
        select(Invoice)
        .where(Invoice.payer_id == user_id)
        .order_by(Invoice.created_at.desc())
        .limit(100)
    )
    invoices = [
        {
            "id": str(inv.id),
            "status": inv.status,
            "total_amount": str(inv.total_amount)
            if inv.total_amount is not None
            else None,
            "currency": inv.currency,
            "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
            "due_at": inv.due_at.isoformat() if inv.due_at else None,
        }
        for inv in invoices_result.scalars().all()
    ]

    # --- Consent preferences ---
    consent_result = await db.execute(
        select(ConsentPreference)
        .where(ConsentPreference.user_id == user_id)
        .order_by(ConsentPreference.created_at.desc())
    )
    consents = [
        {
            "id": str(c.id),
            "topic": c.topic,
            "channel": c.channel,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in consent_result.scalars().all()
    ]

    # --- Audit trail for this GDPR action ---
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="GDPR_DATA_EXPORT",
        outcome="success",
        target_type="user",
        target_id=user_id,
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "user_id": str(user_id),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "profile": profile,
            "memberships": memberships,
            "sessions": sessions,
            "audit_logs": audit_logs,
            "submissions": submissions,
            "grades": grades,
            "notifications": notifications,
            "invoices": invoices,
            "consent_preferences": consents,
        }
    )


# ---------------------------------------------------------------------------
# POST /users/{user_id}/data-deletion
# ---------------------------------------------------------------------------
@router.post("/{user_id}/data-deletion", summary="Anonymize user data (GDPR)")
async def data_deletion(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:session:list")),
    db: AsyncSession = Depends(get_db),
):
    """Anonymize user PII. ADM only. Keeps audit structure intact.

    Replaces: email, full_name, phone with hashed values.
    Revokes all sessions. Clears TOTP secrets and backup codes.
    Does NOT delete audit log entries (required for compliance).
    """
    user = await _get_target_user(db, user_id, auth, admin_only=True)

    if user.id == auth.user_id:
        raise AuthorizationError(
            "Cannot anonymize your own account",
            error_code="ERR-GDPR-422",
        )

    # Store entity_before for audit trail
    entity_before = {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
    }

    # Anonymize PII fields
    anon_id = _anonymize(str(user.id))
    user.email = f"deleted-{anon_id}@anonymized.local"
    user.full_name = f"Deleted User {anon_id[:8]}"
    user.phone = None
    user.password_hash = ""
    user.status = "inactive"

    # Clear 2FA
    user.totp_secret = None
    user.totp_enabled = False
    user.backup_codes = None

    # Revoke all sessions
    await db.execute(
        update(Session)
        .where(Session.user_id == user_id, Session.revoke_at.is_(None))
        .values(revoke_at=datetime.now(timezone.utc))
    )

    # Deactivate memberships
    await db.execute(
        update(Membership)
        .where(Membership.user_id == user_id, Membership.status == "active")
        .values(status="inactive")
    )

    await db.flush()

    entity_after = {
        "email": user.email,
        "full_name": user.full_name,
        "phone": user.phone,
        "status": user.status,
    }

    # Audit trail
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="GDPR_DATA_DELETION",
        outcome="success",
        target_type="user",
        target_id=user_id,
        entity_before=entity_before,
        entity_after=entity_after,
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "user_id": str(user_id),
            "anonymized_at": datetime.now(timezone.utc).isoformat(),
            "status": "anonymized",
            "message": "User PII has been anonymized. Audit records preserved.",
        }
    )


# ---------------------------------------------------------------------------
# GET /users/{user_id}/consent-log
# ---------------------------------------------------------------------------
@router.get("/{user_id}/consent-log", summary="Consent change history (GDPR)")
async def consent_log(
    user_id: uuid.UUID,
    request: Request,
    auth: AuthContext = Depends(requires_permission("PERM-IAM:session:list")),
    db: AsyncSession = Depends(get_db),
):
    """Full consent change history for a user. ADM or self.

    Returns all audit log entries where the target is a consent preference
    belonging to this user, plus current consent preferences.
    """
    await _get_target_user(db, user_id, auth)

    # Current consent preferences
    consent_result = await db.execute(
        select(ConsentPreference)
        .where(ConsentPreference.user_id == user_id)
        .order_by(ConsentPreference.updated_at.desc())
    )
    current_consents = [
        {
            "id": str(c.id),
            "topic": c.topic,
            "channel": c.channel,
            "scope_type": c.scope_type,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in consent_result.scalars().all()
    ]

    # Consent change history from audit logs
    audit_result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.school_id == auth.school_id,
            AuditLog.target_type == "consent_preference",
        )
        .order_by(AuditLog.created_at.desc())
        .limit(200)
    )

    change_history = [
        {
            "id": str(a.id),
            "action_type": a.action_type,
            "outcome": a.outcome,
            "target_id": str(a.target_id) if a.target_id else None,
            "entity_before": a.entity_before,
            "entity_after": a.entity_after,
            "actor_id": str(a.actor_id) if a.actor_id else None,
            "ip_address": a.ip_address,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in audit_result.scalars().all()
    ]

    # Audit this access
    audit = AuditService(db)
    await audit.log_event(
        school_id=auth.school_id,
        actor_id=auth.user_id,
        action_type="GDPR_CONSENT_LOG_ACCESS",
        outcome="success",
        target_type="user",
        target_id=user_id,
        ip_address=get_client_ip(request),
    )

    return success_response(
        {
            "user_id": str(user_id),
            "current_consents": current_consents,
            "change_history": change_history,
        }
    )
