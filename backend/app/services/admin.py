"""Admin domain service."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import AuthContext
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.permissions import ADM, DIR, PAR, STD, TCH
from app.core.security import hash_password
from app.core.unit_of_work import UnitOfWork
from app.models.iam import InvitationCode, Membership, ParentChildLink, User
from app.repositories.admin import AdminRepository
from app.services.audit import AuditService


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


class AdminService:
    """Business logic for admin dashboard and school user operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AdminRepository(db)
        self.audit = AuditService(db)

    async def get_dashboard_stats(self, auth: AuthContext) -> dict:
        now = datetime.now(timezone.utc)
        audit_cutoff = now - timedelta(hours=24)
        return {
            "users": await self.repo.count_school_users(auth.school_id),
            "active_sessions": await self.repo.count_active_sessions(auth.school_id),
            "active_invitations": await self.repo.count_active_invitations(
                school_id=auth.school_id,
                now=now,
            ),
            "audit_events_24h": await self.repo.count_recent_audit_events(
                school_id=auth.school_id,
                audit_cutoff=audit_cutoff,
            ),
            "pending_justifications": await self.repo.count_pending_justifications(
                auth.school_id
            ),
            "users_by_role": await self.repo.get_role_counts(auth.school_id),
        }

    async def list_users(
        self,
        *,
        auth: AuthContext,
        search: str | None,
        role: str | None,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        rows = await self.repo.list_users(
            school_id=auth.school_id,
            search=search,
            role=role,
            status=status,
            cursor_dt=_parse_iso_datetime(cursor),
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        memberships = await self.repo.list_active_memberships_for_users(
            user_ids=[user.id for user in rows],
            school_id=auth.school_id,
        )
        memberships_map = {membership.user_id: membership.role_code for membership in memberships}
        data = [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "status": user.status,
                "role": memberships_map.get(user.id, ""),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "email_verified": user.email_verified_at is not None,
                "totp_enabled": user.totp_enabled,
            }
            for user in rows
        ]
        next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def suspend_user(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        user = await self.repo.get_user_in_school(
            user_id=user_id,
            school_id=auth.school_id,
        )
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-ADMIN-404")
        if user.id == auth.user_id:
            raise ValidationError("Cannot suspend yourself", error_code="ERR-ADMIN-422")

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.set_user_status(user, "suspended")
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="USER_SUSPENDED",
                outcome="success",
                target_type="user",
                target_id=user_id,
                ip_address=client_ip,
            )
            await uow.commit()
        return {"id": str(user_id), "status": "suspended"}

    async def activate_user(
        self,
        *,
        user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        user = await self.repo.get_user_in_school(
            user_id=user_id,
            school_id=auth.school_id,
        )
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-ADMIN-404")

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.set_user_status(user, "active")
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="USER_ACTIVATED",
                outcome="success",
                target_type="user",
                target_id=user_id,
                ip_address=client_ip,
            )
            await uow.commit()
        return {"id": str(user_id), "status": "active"}

    async def change_user_role(
        self,
        *,
        user_id: uuid.UUID,
        role: str,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        valid_targets = {TCH, PAR, STD, DIR}
        if role not in valid_targets:
            raise ValidationError(
                f"Invalid role. Must be one of: {', '.join(sorted(valid_targets))}",
                error_code="ERR-ADMIN-422",
            )

        user = await self.repo.get_user_in_school(
            user_id=user_id,
            school_id=auth.school_id,
        )
        if user is None:
            raise NotFoundError("User not found", error_code="ERR-ADMIN-404")
        if user.id == auth.user_id:
            raise ValidationError("Cannot change your own role", error_code="ERR-ADMIN-422")

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.update_active_membership_role(
                user_id=user_id,
                school_id=auth.school_id,
                role_code=role,
            )
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="USER_ROLE_CHANGED",
                outcome="success",
                target_type="user",
                target_id=user_id,
                entity_after={"role": role},
                ip_address=client_ip,
            )
            await uow.commit()
        return {"id": str(user_id), "role": role}

    async def list_invitations(
        self,
        *,
        auth: AuthContext,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        now = datetime.now(timezone.utc)
        rows = await self.repo.list_invitations(
            school_id=auth.school_id,
            status=status,
            now=now,
            cursor_dt=_parse_iso_datetime(cursor),
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        data = [
            {
                "id": str(invitation.id),
                "role_target": invitation.role_target,
                "consumed_at": invitation.consumed_at.isoformat()
                if invitation.consumed_at
                else None,
                "consumed_by": str(invitation.consumed_by) if invitation.consumed_by else None,
                "expires_at": invitation.expires_at.isoformat(),
                "created_at": invitation.created_at.isoformat()
                if invitation.created_at
                else None,
                "issuer_user_id": str(invitation.issuer_user_id)
                if invitation.issuer_user_id
                else None,
                "status": (
                    "consumed"
                    if invitation.consumed_at
                    else ("expired" if invitation.expires_at <= now else "active")
                ),
            }
            for invitation in rows
        ]
        next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def list_audit_logs(
        self,
        *,
        auth: AuthContext,
        action_type: str | None,
        correlation_id: str | None,
        date_from: str | None,
        date_to: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        correlation_uuid = None
        if correlation_id:
            try:
                correlation_uuid = uuid.UUID(correlation_id)
            except ValueError:
                correlation_uuid = None

        rows = await self.repo.list_audit_logs(
            school_id=auth.school_id,
            action_type=action_type,
            correlation_id=correlation_uuid,
            date_from=_parse_iso_datetime(date_from),
            date_to=_parse_iso_datetime(date_to),
            cursor_dt=_parse_iso_datetime(cursor),
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        data = [
            {
                "id": str(log.id),
                "action_type": log.action_type,
                "outcome": log.outcome,
                "actor_id": str(log.actor_id) if log.actor_id else None,
                "target_type": log.target_type,
                "target_id": str(log.target_id) if log.target_id else None,
                "error_code": log.error_code,
                "correlation_id": str(log.correlation_id) if log.correlation_id else None,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in rows
        ]
        next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def list_justifications(
        self,
        *,
        auth: AuthContext,
        status: str | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[dict], str | None, bool]:
        rows = await self.repo.list_justifications(
            school_id=auth.school_id,
            status=status,
            cursor_dt=_parse_iso_datetime(cursor),
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        data = [
            {
                "id": str(justification.id),
                "attendance_record_id": str(justification.attendance_record_id),
                "parent_id": str(justification.parent_id),
                "status": justification.status,
                "reason": justification.reason,
                "rejection_reason": justification.rejection_reason,
                "created_at": justification.created_at.isoformat()
                if justification.created_at
                else None,
            }
            for justification in rows
        ]
        next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def register_batch(
        self,
        *,
        items: list,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        school_id = auth.school_id
        results: list[dict] = []
        errors: list[dict] = []
        valid_roles = {STD, PAR, TCH, ADM, DIR}
        now = datetime.now(timezone.utc)

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)

            for item in items:
                existing = await repo.get_user_by_email_in_school(
                    email=item.email,
                    school_id=school_id,
                )
                if existing is not None:
                    errors.append(
                        {
                            "email": item.email,
                            "error": "Email already exists for this school",
                        }
                    )
                    continue

                if item.role not in valid_roles:
                    errors.append(
                        {
                            "email": item.email,
                            "error": f"Invalid role: {item.role}",
                        }
                    )
                    continue

                temp_password = secrets.token_urlsafe(12) + "A1!"
                user = await repo.create_user(
                    User(
                        email=item.email,
                        full_name=item.full_name,
                        phone=item.phone,
                        password_hash=hash_password(temp_password),
                        status="active",
                        school_id=school_id,
                    )
                )
                await repo.create_membership(
                    Membership(
                        user_id=user.id,
                        school_id=school_id,
                        role_code=item.role,
                        status="active",
                    )
                )
                code_hash = hashlib.sha256(
                    secrets.token_hex(4).upper().encode()
                ).hexdigest()
                await repo.create_invitation(
                    InvitationCode(
                        school_id=school_id,
                        issuer_user_id=auth.user_id,
                        code_hash=code_hash,
                        role_target=item.role,
                        consumed_by=user.id,
                        consumed_at=now,
                        expires_at=now,
                        target_student_id=item.target_student_id
                        if item.role == PAR
                        else None,
                    )
                )

                if item.role == PAR and item.target_student_id:
                    student = await repo.get_user_with_role(
                        user_id=item.target_student_id,
                        school_id=school_id,
                        role_code=STD,
                    )
                    if student is not None:
                        await repo.create_parent_child_link(
                            ParentChildLink(
                                parent_user_id=user.id,
                                child_user_id=item.target_student_id,
                                school_id=school_id,
                                status="active",
                                linked_at=now,
                                linked_by=auth.user_id,
                            )
                        )

                await audit.log_event(
                    school_id=school_id,
                    actor_id=auth.user_id,
                    action_type="USER_BATCH_REGISTERED",
                    outcome="success",
                    target_type="user",
                    target_id=user.id,
                    ip_address=client_ip,
                )
                results.append(
                    {
                        "user_id": str(user.id),
                        "email": item.email,
                        "full_name": item.full_name,
                        "role": item.role,
                        "temp_password": temp_password,
                    }
                )

            await uow.commit()

        return {
            "created": results,
            "errors": errors,
            "total_created": len(results),
            "total_errors": len(errors),
        }

    async def create_parent_child_link(
        self,
        *,
        parent_user_id: uuid.UUID,
        child_user_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        school_id = auth.school_id
        parent = await self.repo.get_user_with_role(
            user_id=parent_user_id,
            school_id=school_id,
            role_code=PAR,
        )
        if parent is None:
            raise NotFoundError(
                "Parent user not found in this school",
                error_code="ERR-RES-404",
            )

        student = await self.repo.get_user_with_role(
            user_id=child_user_id,
            school_id=school_id,
            role_code=STD,
        )
        if student is None:
            raise NotFoundError(
                "Student user not found in this school",
                error_code="ERR-RES-404",
            )

        existing = await self.repo.get_active_parent_child_link(
            parent_user_id=parent_user_id,
            child_user_id=child_user_id,
            school_id=school_id,
        )
        if existing is not None:
            raise ConflictError(
                "Parent-child link already exists",
                error_code="ERR-CONFLICT-001",
            )

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)
            link = await repo.create_parent_child_link(
                ParentChildLink(
                    parent_user_id=parent_user_id,
                    child_user_id=child_user_id,
                    school_id=school_id,
                    status="active",
                    linked_at=datetime.now(timezone.utc),
                    linked_by=auth.user_id,
                )
            )
            await audit.log_event(
                school_id=school_id,
                actor_id=auth.user_id,
                action_type="PARENT_CHILD_LINKED",
                outcome="success",
                target_type="parent_child_link",
                target_id=link.id,
                ip_address=client_ip,
            )
            await uow.commit()
        return {
            "id": str(link.id),
            "parent_user_id": str(link.parent_user_id),
            "child_user_id": str(link.child_user_id),
            "school_id": str(link.school_id),
            "status": link.status,
            "linked_at": link.linked_at.isoformat(),
            "linked_by": str(link.linked_by) if link.linked_by else None,
        }

    async def list_parent_child_links(
        self,
        *,
        parent_id: uuid.UUID | None,
        student_id: uuid.UUID | None,
        status: str | None,
        cursor: str | None,
        limit: int,
        auth: AuthContext,
    ) -> tuple[list[dict], str | None, bool]:
        cursor_dt = datetime.fromisoformat(cursor) if cursor else None
        rows = await self.repo.list_parent_child_links(
            school_id=auth.school_id,
            parent_id=parent_id,
            student_id=student_id,
            status=status,
            cursor_dt=cursor_dt,
            limit=limit,
        )
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]
        data = [
            {
                "id": str(link.id),
                "parent_user_id": str(link.parent_user_id),
                "child_user_id": str(link.child_user_id),
                "school_id": str(link.school_id),
                "status": link.status,
                "linked_at": link.linked_at.isoformat() if link.linked_at else None,
                "linked_by": str(link.linked_by) if link.linked_by else None,
            }
            for link in rows
        ]
        next_cursor = rows[-1].linked_at.isoformat() if has_more and rows else None
        return data, next_cursor, has_more

    async def revoke_parent_child_link(
        self,
        *,
        link_id: uuid.UUID,
        auth: AuthContext,
        client_ip: str,
    ) -> dict:
        link = await self.repo.get_parent_child_link(
            link_id=link_id,
            school_id=auth.school_id,
        )
        if link is None:
            raise NotFoundError("Parent-child link not found", error_code="ERR-RES-404")
        if link.status == "revoked":
            return {"message": "Link already revoked", "id": str(link.id)}

        async with UnitOfWork(self.db) as uow:
            repo = AdminRepository(uow.session)
            audit = AuditService(uow.session)
            await repo.revoke_parent_child_link(link)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="PARENT_CHILD_UNLINKED",
                outcome="success",
                target_type="parent_child_link",
                target_id=link.id,
                ip_address=client_ip,
            )
            await uow.commit()
        return {
            "id": str(link.id),
            "status": link.status,
            "message": "Parent-child link revoked",
        }
