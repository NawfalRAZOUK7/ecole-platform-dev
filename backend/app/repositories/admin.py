"""Repository helpers for admin dashboard and user management."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, update

from app.models.audit import AuditLog
from app.models.erp import AbsenceJustification
from app.models.iam import InvitationCode, Membership, ParentChildLink, Session, User
from app.repositories.base import BaseRepository


class AdminRepository(BaseRepository):
    """Data access for admin dashboard, users, invitations, and links."""

    async def count_school_users(self, school_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.school_id == school_id)
        )
        return int(result.scalar() or 0)

    async def count_active_sessions(self, school_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Session)
            .where(Session.school_id == school_id, Session.revoke_at.is_(None))
        )
        return int(result.scalar() or 0)

    async def count_active_invitations(
        self,
        *,
        school_id: uuid.UUID,
        now: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(InvitationCode)
            .where(
                InvitationCode.school_id == school_id,
                InvitationCode.consumed_at.is_(None),
                InvitationCode.expires_at > now,
            )
        )
        return int(result.scalar() or 0)

    async def count_recent_audit_events(
        self,
        *,
        school_id: uuid.UUID,
        audit_cutoff: datetime,
    ) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(
                AuditLog.school_id == school_id,
                AuditLog.created_at >= audit_cutoff,
            )
        )
        return int(result.scalar() or 0)

    async def count_pending_justifications(self, school_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(AbsenceJustification)
            .where(
                AbsenceJustification.school_id == school_id,
                AbsenceJustification.status == "pending",
            )
        )
        return int(result.scalar() or 0)

    async def get_role_counts(self, school_id: uuid.UUID) -> dict[str, int]:
        result = await self.db.execute(
            select(Membership.role_code, func.count())
            .where(Membership.school_id == school_id, Membership.status == "active")
            .group_by(Membership.role_code)
        )
        return {role_code: int(count or 0) for role_code, count in result.all()}

    async def list_users(
        self,
        *,
        school_id: uuid.UUID,
        search: str | None,
        role: str | None,
        status: str | None,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[User]:
        query = select(User).where(User.school_id == school_id)

        if search:
            pattern = f"%{search}%"
            query = query.where(
                User.full_name.ilike(pattern) | User.email.ilike(pattern)
            )

        if status:
            query = query.where(User.status == status)

        if role:
            query = query.where(
                User.id.in_(
                    select(Membership.user_id).where(
                        Membership.school_id == school_id,
                        Membership.role_code == role,
                        Membership.status == "active",
                    )
                )
            )

        if cursor_dt:
            query = query.where(User.created_at < cursor_dt)

        result = await self.db.execute(
            query.order_by(User.created_at.desc()).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def list_active_memberships_for_users(
        self,
        *,
        user_ids: list[uuid.UUID],
        school_id: uuid.UUID,
    ) -> list[Membership]:
        if not user_ids:
            return []
        result = await self.db.execute(
            select(Membership).where(
                Membership.user_id.in_(user_ids),
                Membership.school_id == school_id,
                Membership.status == "active",
            )
        )
        return list(result.scalars().all())

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

    async def get_user_by_email_in_school(
        self,
        *,
        email: str,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_user_with_role(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role_code: str,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                User.id == user_id,
                User.school_id == school_id,
                Membership.school_id == school_id,
                Membership.role_code == role_code,
                Membership.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def set_user_status(self, user: User, status: str) -> User:
        user.status = status
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_active_membership_role(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        role_code: str,
    ) -> None:
        await self.db.execute(
            update(Membership)
            .where(
                Membership.user_id == user_id,
                Membership.school_id == school_id,
                Membership.status == "active",
            )
            .values(role_code=role_code)
        )
        await self.db.flush()

    async def list_invitations(
        self,
        *,
        school_id: uuid.UUID,
        status: str | None,
        now: datetime,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[InvitationCode]:
        query = select(InvitationCode).where(InvitationCode.school_id == school_id)

        if status == "active":
            query = query.where(
                InvitationCode.consumed_at.is_(None),
                InvitationCode.expires_at > now,
            )
        elif status == "consumed":
            query = query.where(InvitationCode.consumed_at.isnot(None))
        elif status == "expired":
            query = query.where(
                InvitationCode.consumed_at.is_(None),
                InvitationCode.expires_at <= now,
            )

        if cursor_dt:
            query = query.where(InvitationCode.created_at < cursor_dt)

        result = await self.db.execute(
            query.order_by(InvitationCode.created_at.desc()).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def list_audit_logs(
        self,
        *,
        school_id: uuid.UUID,
        action_type: str | None,
        correlation_id: uuid.UUID | None,
        date_from: datetime | None,
        date_to: datetime | None,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[AuditLog]:
        query = select(AuditLog).where(AuditLog.school_id == school_id)

        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        if correlation_id:
            query = query.where(AuditLog.correlation_id == correlation_id)
        if date_from:
            query = query.where(AuditLog.created_at >= date_from)
        if date_to:
            query = query.where(AuditLog.created_at <= date_to)
        if cursor_dt:
            query = query.where(AuditLog.created_at < cursor_dt)

        result = await self.db.execute(
            query.order_by(AuditLog.created_at.desc()).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def list_justifications(
        self,
        *,
        school_id: uuid.UUID,
        status: str | None,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[AbsenceJustification]:
        query = select(AbsenceJustification).where(
            AbsenceJustification.school_id == school_id
        )
        if status:
            query = query.where(AbsenceJustification.status == status)
        if cursor_dt:
            query = query.where(AbsenceJustification.created_at < cursor_dt)
        result = await self.db.execute(
            query.order_by(AbsenceJustification.created_at.desc()).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_membership(self, membership: Membership) -> Membership:
        self.db.add(membership)
        await self.db.flush()
        return membership

    async def create_invitation(self, invitation: InvitationCode) -> InvitationCode:
        self.db.add(invitation)
        await self.db.flush()
        return invitation

    async def create_parent_child_link(
        self,
        link: ParentChildLink,
    ) -> ParentChildLink:
        self.db.add(link)
        await self.db.flush()
        return link

    async def get_active_parent_child_link(
        self,
        *,
        parent_user_id: uuid.UUID,
        child_user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> ParentChildLink | None:
        result = await self.db.execute(
            select(ParentChildLink).where(
                ParentChildLink.parent_user_id == parent_user_id,
                ParentChildLink.child_user_id == child_user_id,
                ParentChildLink.school_id == school_id,
                ParentChildLink.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def list_parent_child_links(
        self,
        *,
        school_id: uuid.UUID,
        parent_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
        status: str | None,
        cursor_dt: datetime | None,
        limit: int,
    ) -> list[ParentChildLink]:
        query = select(ParentChildLink).where(ParentChildLink.school_id == school_id)
        if parent_id:
            query = query.where(ParentChildLink.parent_user_id == parent_id)
        if student_id:
            query = query.where(ParentChildLink.child_user_id == student_id)
        if status:
            query = query.where(ParentChildLink.status == status)
        if cursor_dt:
            query = query.where(ParentChildLink.linked_at < cursor_dt)
        result = await self.db.execute(
            query.order_by(ParentChildLink.linked_at.desc()).limit(limit + 1)
        )
        return list(result.scalars().all())

    async def get_parent_child_link(
        self,
        *,
        link_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> ParentChildLink | None:
        result = await self.db.execute(
            select(ParentChildLink).where(
                ParentChildLink.id == link_id,
                ParentChildLink.school_id == school_id,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_parent_child_link(self, link: ParentChildLink) -> ParentChildLink:
        link.status = "revoked"
        self.db.add(link)
        await self.db.flush()
        return link
