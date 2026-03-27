"""Repository helpers for GDPR exports, anonymization, and consent management."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update

from app.models.ai import AIPreference
from app.models.audit import AuditLog
from app.models.billing import Invoice
from app.models.com import ConsentPreference, Notification
from app.models.iam import Membership, Session, User
from app.models.lms import Grade, Submission
from app.repositories.base import BaseRepository


class GDPRRepository(BaseRepository):
    """Data access for GDPR exports and consent preferences."""

    async def get_user_in_school(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def list_memberships(self, user_id: uuid.UUID) -> list[Membership]:
        result = await self.db.execute(
            select(Membership).where(Membership.user_id == user_id)
        )
        return list(result.scalars().all())

    async def list_sessions(
        self,
        *,
        user_id: uuid.UUID,
        limit: int,
    ) -> list[Session]:
        result = await self.db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_actor_audit_logs(
        self,
        *,
        user_id: uuid.UUID,
        limit: int,
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_submissions(
        self,
        *,
        student_id: uuid.UUID,
        limit: int,
    ) -> list[Submission]:
        result = await self.db.execute(
            select(Submission)
            .where(Submission.student_id == student_id)
            .order_by(Submission.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_grades(
        self,
        *,
        student_id: uuid.UUID,
        limit: int,
    ) -> list[Grade]:
        result = await self.db.execute(
            select(Grade)
            .where(Grade.student_id == student_id)
            .order_by(Grade.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_notifications(
        self,
        *,
        user_id: uuid.UUID,
        limit: int,
    ) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.parent_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_invoices(
        self,
        *,
        user_id: uuid.UUID,
        limit: int,
    ) -> list[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.parent_id == user_id)
            .order_by(Invoice.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_consent_preferences(
        self,
        *,
        user_id: uuid.UUID,
    ) -> list[ConsentPreference]:
        result = await self.db.execute(
            select(ConsentPreference)
            .where(ConsentPreference.user_id == user_id)
            .order_by(ConsentPreference.created_at.desc())
        )
        return list(result.scalars().all())

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def revoke_active_sessions(
        self,
        *,
        user_id: uuid.UUID,
        revoked_at: datetime,
    ) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.user_id == user_id, Session.revoke_at.is_(None))
            .values(revoke_at=revoked_at)
        )
        await self.db.flush()

    async def deactivate_active_memberships(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Membership)
            .where(Membership.user_id == user_id, Membership.status == "active")
            .values(status="inactive")
        )
        await self.db.flush()

    async def list_consent_audit_logs(
        self,
        *,
        school_id: uuid.UUID,
        limit: int,
    ) -> list[AuditLog]:
        result = await self.db.execute(
            select(AuditLog)
            .where(
                AuditLog.school_id == school_id,
                AuditLog.target_type == "consent_preference",
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_consent_preference(
        self,
        consent_id: uuid.UUID,
    ) -> ConsentPreference | None:
        result = await self.db.execute(
            select(ConsentPreference).where(ConsentPreference.id == consent_id)
        )
        return result.scalar_one_or_none()

    async def save_consent_preference(
        self,
        consent: ConsentPreference,
    ) -> ConsentPreference:
        self.db.add(consent)
        await self.db.flush()
        return consent

    async def list_consents(
        self,
        *,
        school_id: uuid.UUID,
        user_id: uuid.UUID | None,
        after_id: uuid.UUID | None,
        limit: int,
    ) -> list[ConsentPreference]:
        query = select(ConsentPreference).where(
            ConsentPreference.school_id == school_id
        )
        if user_id:
            query = query.where(ConsentPreference.user_id == user_id)
        if after_id:
            query = query.where(ConsentPreference.id > after_id)
        result = await self.db.execute(
            query.order_by(ConsentPreference.id).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def get_ai_preference(
        self,
        *,
        user_id: uuid.UUID,
        target_user_id: uuid.UUID,
    ) -> AIPreference | None:
        result = await self.db.execute(
            select(AIPreference).where(
                AIPreference.user_id == user_id,
                AIPreference.target_user_id == target_user_id,
            )
        )
        return result.scalar_one_or_none()
