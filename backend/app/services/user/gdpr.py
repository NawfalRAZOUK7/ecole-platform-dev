"""GDPR and consent service."""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext, verify_school_boundary
from app.core.exceptions import AuthorizationError, NotFoundError
from app.core.permissions import PERM_GDPR_CONSENT_MANAGE, PERM_GDPR_DATA_DELETE
from app.core.response import clamp_page_size, decode_cursor, encode_cursor
from app.core.unit_of_work import UnitOfWork
from app.repositories.user_gdpr import GDPRRepository
from app.services.platform.audit import AuditService


def _anonymize(value: str) -> str:
    return hashlib.sha256(f"anon:{value}".encode()).hexdigest()[:16]


class GDPRService:
    """Business logic for GDPR exports, anonymization, and consent updates."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = GDPRRepository(db)
        self.audit = AuditService(db)

    def _can_manage_user_data(self, auth: AuthContext) -> bool:
        return PERM_GDPR_DATA_DELETE in auth.permissions

    def _can_manage_consents(self, auth: AuthContext) -> bool:
        return PERM_GDPR_CONSENT_MANAGE in auth.permissions

    async def _get_target_user(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        admin_only: bool = False,
    ):
        is_self = auth.user_id == user_id
        can_manage_any = self._can_manage_user_data(auth)

        if admin_only and not can_manage_any:
            raise AuthorizationError(
                "Only administrators can perform this action",
                error_code="ERR-GDPR-403",
            )

        if not can_manage_any and not is_self:
            raise AuthorizationError(
                "You can only access your own data",
                error_code="ERR-GDPR-403",
            )

        user = await self.repo.get_user_in_school(
            user_id=user_id,
            school_id=auth.school_id,
        )
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-GDPR-404")
        return user

    async def data_export(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        user = await self._get_target_user(user_id=user_id, auth=auth)
        memberships = await self.repo.list_memberships(user_id)
        sessions = await self.repo.list_sessions(user_id=user_id, limit=100)
        audit_logs = await self.repo.list_actor_audit_logs(user_id=user_id, limit=200)
        submissions = await self.repo.list_submissions(student_id=user_id, limit=200)
        grades = await self.repo.list_grades(student_id=user_id, limit=200)
        notifications = await self.repo.list_notifications(user_id=user_id, limit=200)
        invoices = await self.repo.list_invoices(user_id=user_id, limit=100)
        consents = await self.repo.list_consent_preferences(user_id=user_id)

        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="GDPR_DATA_EXPORT",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=client_ip,
        )

        return {
            "user_id": str(user_id),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "profile": {
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
            },
            "memberships": [
                {
                    "id": str(membership.id),
                    "school_id": str(membership.school_id),
                    "role_code": membership.role_code,
                    "status": membership.status,
                    "created_at": membership.created_at.isoformat()
                    if membership.created_at
                    else None,
                }
                for membership in memberships
            ],
            "sessions": [
                {
                    "id": str(session.id),
                    "source": session.source,
                    "device_name": session.device_name,
                    "ip_address": session.ip_address,
                    "created_at": session.created_at.isoformat()
                    if session.created_at
                    else None,
                    "revoke_at": session.revoke_at.isoformat()
                    if session.revoke_at
                    else None,
                }
                for session in sessions
            ],
            "audit_logs": [
                {
                    "id": str(log.id),
                    "action_type": log.action_type,
                    "outcome": log.outcome,
                    "target_type": log.target_type,
                    "target_id": str(log.target_id) if log.target_id else None,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat()
                    if log.created_at
                    else None,
                }
                for log in audit_logs
            ],
            "submissions": [
                {
                    "id": str(submission.id),
                    "assignment_id": str(submission.assignment_id),
                    "status": submission.status,
                    "submitted_at": submission.submitted_at.isoformat()
                    if submission.submitted_at
                    else None,
                    "created_at": submission.created_at.isoformat()
                    if submission.created_at
                    else None,
                }
                for submission in submissions
            ],
            "grades": [
                {
                    "id": str(grade.id),
                    "submission_id": str(grade.submission_id),
                    "score": float(grade.score) if grade.score is not None else None,
                    "feedback_text": grade.feedback_text,
                    "published_at": grade.published_at.isoformat()
                    if grade.published_at
                    else None,
                    "created_at": grade.created_at.isoformat()
                    if grade.created_at
                    else None,
                }
                for grade in grades
            ],
            "notifications": [
                {
                    "id": str(notification.id),
                    "type": notification.category,
                    "subject": notification.title,
                    "created_at": notification.created_at.isoformat()
                    if notification.created_at
                    else None,
                }
                for notification in notifications
            ],
            "invoices": [
                {
                    "id": str(invoice.id),
                    "status": invoice.status,
                    "total_amount": str(invoice.total_amount)
                    if invoice.total_amount is not None
                    else None,
                    "currency": invoice.currency,
                    "issued_at": invoice.issued_date.isoformat()
                    if invoice.issued_date
                    else None,
                    "due_at": invoice.due_date.isoformat()
                    if invoice.due_date
                    else None,
                }
                for invoice in invoices
            ],
            "consent_preferences": [
                {
                    "id": str(consent.id),
                    "topic": consent.topic,
                    "channel": consent.channel,
                    "status": consent.status,
                    "created_at": consent.created_at.isoformat()
                    if consent.created_at
                    else None,
                    "updated_at": consent.updated_at.isoformat()
                    if consent.updated_at
                    else None,
                }
                for consent in consents
            ],
        }

    async def data_deletion(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        user = await self._get_target_user(
            user_id=user_id,
            auth=auth,
            admin_only=True,
        )
        if user.id == auth.user_id:
            raise AuthorizationError(
                "Cannot anonymize your own account",
                error_code="ERR-GDPR-422",
            )

        entity_before = {
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "status": user.status,
        }
        anon_id = _anonymize(str(user.id))
        user.email = f"deleted-{anon_id}@anonymized.local"
        user.full_name = f"Deleted User {anon_id[:8]}"
        user.phone = None
        user.password_hash = ""
        user.status = "inactive"
        user.totp_secret = None
        user.totp_enabled = False
        user.backup_codes = None

        anonymized_at = datetime.now(timezone.utc)
        entity_after = {
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "status": user.status,
        }
        async with UnitOfWork(self.db) as uow:
            repo = GDPRRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_user(user)
            await repo.revoke_active_sessions(user_id=user_id, revoked_at=anonymized_at)
            await repo.deactivate_active_memberships(user_id)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="GDPR_DATA_DELETION",
                outcome="success",
                target_type="user",
                target_id=user_id,
                entity_before=entity_before,
                entity_after=entity_after,
                ip_address=client_ip,
            )
            await uow.commit()
        return {
            "user_id": str(user_id),
            "anonymized_at": anonymized_at.isoformat(),
            "status": "anonymized",
            "message": "User PII has been anonymized. Audit records preserved.",
        }

    async def consent_log(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        await self._get_target_user(user_id=user_id, auth=auth)
        current_consents = await self.repo.list_consent_preferences(user_id=user_id)
        change_history = await self.repo.list_consent_audit_logs(
            school_id=auth.school_id,
            limit=200,
        )
        await self.audit.log_event(
            school_id=auth.school_id,
            actor_id=auth.user_id,
            action_type="GDPR_CONSENT_LOG_ACCESS",
            outcome="success",
            target_type="user",
            target_id=user_id,
            ip_address=client_ip,
        )
        return {
            "user_id": str(user_id),
            "current_consents": [
                {
                    "id": str(consent.id),
                    "topic": consent.topic,
                    "channel": consent.channel,
                    "scope_type": consent.scope_type,
                    "status": consent.status,
                    "created_at": consent.created_at.isoformat()
                    if consent.created_at
                    else None,
                    "updated_at": consent.updated_at.isoformat()
                    if consent.updated_at
                    else None,
                }
                for consent in current_consents
            ],
            "change_history": [
                {
                    "id": str(log.id),
                    "action_type": log.action_type,
                    "outcome": log.outcome,
                    "target_id": str(log.target_id) if log.target_id else None,
                    "entity_before": log.entity_before,
                    "entity_after": log.entity_after,
                    "actor_id": str(log.actor_id) if log.actor_id else None,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat()
                    if log.created_at
                    else None,
                }
                for log in change_history
            ],
        }

    async def list_consents(
        self,
        *,
        auth: AuthContext,
        cursor: str | None,
        limit: int | None,
    ) -> tuple[list[dict], str | None, bool]:
        page_size = clamp_page_size(limit)
        after_id = None
        if cursor:
            after_id, _ = decode_cursor(cursor)
        rows = await self.repo.list_consents(
            school_id=auth.school_id,
            user_id=None if self._can_manage_consents(auth) else auth.user_id,
            after_id=after_id,
            limit=page_size,
        )
        has_more = len(rows) > page_size
        if has_more:
            rows = rows[:page_size]

        items = [
            {
                "id": str(consent.id),
                "user_id": str(consent.user_id),
                "school_id": str(consent.school_id),
                "topic": consent.topic,
                "channel": consent.channel,
                "scope_type": consent.scope_type,
                "scope_ref_id": str(consent.scope_ref_id)
                if consent.scope_ref_id
                else None,
                "status": consent.status,
            }
            for consent in rows
        ]
        next_cursor = encode_cursor(rows[-1].id) if has_more and rows else None
        return items, next_cursor, has_more

    async def update_consent(
        self,
        *,
        consent_id: uuid.UUID,
        status: str,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        consent = await self.repo.get_consent_preference(consent_id)
        if consent is None:
            raise NotFoundError(
                "Consent preference not found", error_code="ERR-COM-404"
            )

        verify_school_boundary(consent.school_id, auth)
        if not self._can_manage_consents(auth) and consent.user_id != auth.user_id:
            raise NotFoundError(
                "Consent preference not found", error_code="ERR-COM-404"
            )

        old_status = consent.status
        consent.status = status
        async with UnitOfWork(self.db) as uow:
            repo = GDPRRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.save_consent_preference(consent)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="CONSENT_UPDATED",
                outcome="success",
                target_type="consent_preference",
                target_id=consent.id,
                entity_before={"status": old_status},
                entity_after={"status": status},
                ip_address=client_ip,
            )
            await uow.commit()
        return {
            "id": str(consent.id),
            "user_id": str(consent.user_id),
            "school_id": str(consent.school_id),
            "topic": consent.topic,
            "channel": consent.channel,
            "scope_type": consent.scope_type,
            "scope_ref_id": str(consent.scope_ref_id) if consent.scope_ref_id else None,
            "status": consent.status,
        }
