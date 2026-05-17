"""Repository helpers for authentication, invitations, recovery, and 2FA."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, delete, distinct, or_, select, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.iam import (
    AccountRecoveryRequest,
    FailedLoginAttempt,
    InvitationCode,
    KnownDevice,
    KnownLocation,
    Membership,
    OAuthAccount,
    ParentChildLink,
    ParentProfile,
    PasswordHistory,
    Session,
    StudentProfile,
    TeacherProfile,
    User,
    WebAuthnCredential,
)
from app.models.school import School
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository):
    """Data access for IAM/auth domain workflows."""

    async def get_user_by_email(
        self,
        email: str,
        school_id: uuid.UUID | None = None,
    ) -> User | None:
        query = select(User).where(User.email == email)
        if school_id is not None:
            query = query.where(User.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_school_by_id(
        self,
        school_id: uuid.UUID,
    ) -> School | None:
        result = await self.db.execute(select(School).where(School.id == school_id))
        return result.scalar_one_or_none()

    async def get_user_in_school(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.school_id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_user_with_memberships(
        self,
        user_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.memberships))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(self, **kwargs: Any) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        return user

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def update_user(self, user_id: uuid.UUID, **kwargs: Any) -> User | None:
        await self.db.execute(update(User).where(User.id == user_id).values(**kwargs))
        return await self.get_user_by_id(user_id)

    async def create_membership(self, **kwargs: Any) -> Membership:
        membership = Membership(**kwargs)
        self.db.add(membership)
        await self.db.flush()
        return membership

    async def get_membership(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> Membership | None:
        query = select(Membership).where(
            Membership.user_id == user_id,
            Membership.school_id == school_id,
        )
        if active_only:
            query = query.where(Membership.status == "active")
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_memberships(
        self,
        user_id: uuid.UUID,
        *,
        active_only: bool = False,
    ) -> list[Membership]:
        query = select(Membership).where(Membership.user_id == user_id)
        if active_only:
            query = query.where(Membership.status == "active")
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_student_profile(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        **kwargs: Any,
    ) -> StudentProfile:
        profile = StudentProfile(user_id=user_id, school_id=school_id, **kwargs)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def create_parent_profile(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        **kwargs: Any,
    ) -> ParentProfile:
        profile = ParentProfile(user_id=user_id, school_id=school_id, **kwargs)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def create_teacher_profile(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
        **kwargs: Any,
    ) -> TeacherProfile:
        profile = TeacherProfile(user_id=user_id, school_id=school_id, **kwargs)
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def create_parent_child_link(self, **kwargs: Any) -> ParentChildLink:
        link = ParentChildLink(**kwargs)
        self.db.add(link)
        await self.db.flush()
        return link

    async def create_session(self, **kwargs: Any) -> Session:
        session = Session(**kwargs)
        self.db.add(session)
        await self.db.flush()
        return session

    async def save_session(self, session: Session) -> Session:
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_by_id(
        self,
        session_id: uuid.UUID,
        *,
        active_only: bool = False,
    ) -> Session | None:
        query = select(Session).where(Session.id == session_id)
        if active_only:
            query = query.where(Session.revoke_at.is_(None))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_active_sessions(
        self,
        *,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> list[Session]:
        result = await self.db.execute(
            select(Session)
            .where(
                Session.user_id == user_id,
                Session.school_id == school_id,
                Session.revoke_at.is_(None),
            )
            .order_by(Session.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_active_sessions(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Session.id)).where(
                Session.user_id == user_id,
                Session.school_id == school_id,
                Session.revoke_at.is_(None),
            )
        )
        return int(result.scalar_one() or 0)

    async def get_oldest_active_session(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> Session | None:
        result = await self.db.execute(
            select(Session)
            .where(
                Session.user_id == user_id,
                Session.school_id == school_id,
                Session.revoke_at.is_(None),
            )
            .order_by(Session.created_at.asc(), Session.id.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def revoke_session(
        self,
        session_id: uuid.UUID,
        revoked_at: datetime,
    ) -> None:
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id, Session.revoke_at.is_(None))
            .values(revoke_at=revoked_at)
        )

    async def revoke_all_sessions(
        self,
        user_id: uuid.UUID,
        revoked_at: datetime,
        *,
        exclude_session_id: uuid.UUID | None = None,
    ) -> int:
        query = (
            update(Session)
            .where(Session.user_id == user_id, Session.revoke_at.is_(None))
            .values(revoke_at=revoked_at)
        )
        if exclude_session_id is not None:
            query = query.where(Session.id != exclude_session_id)
        result = await self.db.execute(query)
        return int(result.rowcount or 0)

    async def get_invitation_by_code_hash(
        self,
        code_hash: str,
    ) -> InvitationCode | None:
        result = await self.db.execute(
            select(InvitationCode).where(InvitationCode.code_hash == code_hash)
        )
        return result.scalar_one_or_none()

    async def get_invitation_by_id(
        self,
        invite_id: uuid.UUID,
        school_id: uuid.UUID | None = None,
    ) -> InvitationCode | None:
        query = select(InvitationCode).where(InvitationCode.id == invite_id)
        if school_id is not None:
            query = query.where(InvitationCode.school_id == school_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_invitation(self, **kwargs: Any) -> InvitationCode:
        invite = InvitationCode(**kwargs)
        self.db.add(invite)
        await self.db.flush()
        return invite

    async def save_invitation(self, invite: InvitationCode) -> InvitationCode:
        self.db.add(invite)
        await self.db.flush()
        return invite

    async def consume_invitation(
        self,
        invitation_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        consumed_at: datetime,
    ) -> InvitationCode | None:
        invite = await self.get_invitation_by_id(invitation_id)
        if invite is None:
            return None
        invite.consumed_by = user_id
        invite.consumed_at = consumed_at
        await self.save_invitation(invite)
        return invite

    async def get_student_in_school(
        self,
        user_id: uuid.UUID,
        school_id: uuid.UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .join(Membership, Membership.user_id == User.id)
            .where(
                User.id == user_id,
                User.school_id == school_id,
                Membership.school_id == school_id,
                Membership.role_code == "STD",
            )
        )
        return result.scalar_one_or_none()

    async def create_recovery_request(self, **kwargs: Any) -> AccountRecoveryRequest:
        recovery = AccountRecoveryRequest(**kwargs)
        self.db.add(recovery)
        await self.db.flush()
        return recovery

    async def get_recovery_request(
        self,
        request_id: uuid.UUID,
    ) -> AccountRecoveryRequest | None:
        result = await self.db.execute(
            select(AccountRecoveryRequest).where(
                AccountRecoveryRequest.id == request_id
            )
        )
        return result.scalar_one_or_none()

    async def save_recovery_request(
        self,
        recovery: AccountRecoveryRequest,
    ) -> AccountRecoveryRequest:
        await self.db.merge(recovery)
        await self.db.flush()
        return recovery

    # ---------------------------------------------------------------------------
    # WebAuthn / Passkeys (Phase 10)
    # ---------------------------------------------------------------------------
    async def create_webauthn_credential(self, **kwargs: Any) -> WebAuthnCredential:
        credential = WebAuthnCredential(**kwargs)
        self.db.add(credential)
        await self.db.flush()
        return credential

    async def get_webauthn_credentials_by_user(
        self,
        user_id: uuid.UUID,
    ) -> list[WebAuthnCredential]:
        result = await self.db.execute(
            select(WebAuthnCredential)
            .where(WebAuthnCredential.user_id == user_id)
            .where(WebAuthnCredential.is_active)
        )
        return result.scalars().all()

    async def get_webauthn_credential_by_id(
        self,
        credential_id: str,
    ) -> WebAuthnCredential | None:
        result = await self.db.execute(
            select(WebAuthnCredential).where(
                WebAuthnCredential.credential_id == credential_id
            )
        )
        return result.scalar_one_or_none()

    async def update_webauthn_credential(
        self,
        credential: WebAuthnCredential,
    ) -> WebAuthnCredential:
        await self.db.merge(credential)
        await self.db.flush()
        return credential

    async def delete_webauthn_credential(
        self,
        credential_id: str,
    ) -> bool:
        result = await self.db.execute(
            delete(WebAuthnCredential).where(
                WebAuthnCredential.credential_id == credential_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    # ---------------------------------------------------------------------------
    # OAuth / Social Login (Phase 10)
    # ---------------------------------------------------------------------------
    async def create_oauth_account(self, **kwargs: Any) -> OAuthAccount:
        oauth_account = OAuthAccount(**kwargs)
        self.db.add(oauth_account)
        await self.db.flush()
        return oauth_account

    async def get_oauth_account_by_provider_user_id(
        self,
        provider: str,
        provider_user_id: str,
    ) -> OAuthAccount | None:
        result = await self.db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_oauth_accounts_by_user(
        self,
        user_id: uuid.UUID,
    ) -> list[OAuthAccount]:
        result = await self.db.execute(
            select(OAuthAccount).where(OAuthAccount.user_id == user_id)
        )
        return result.scalars().all()

    async def update_oauth_account(
        self,
        oauth_account: OAuthAccount,
    ) -> OAuthAccount:
        await self.db.merge(oauth_account)
        await self.db.flush()
        return oauth_account

    async def delete_oauth_account(
        self,
        oauth_account_id: uuid.UUID,
    ) -> bool:
        result = await self.db.execute(
            delete(OAuthAccount).where(OAuthAccount.id == oauth_account_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    # ---------------------------------------------------------------------------
    # Password History (Phase 11)
    # ---------------------------------------------------------------------------
    async def create_password_history(self, **kwargs: Any) -> PasswordHistory:
        password_history = PasswordHistory(**kwargs)
        self.db.add(password_history)
        await self.db.flush()
        return password_history

    async def get_password_history_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 5,
    ) -> list[PasswordHistory]:
        result = await self.db.execute(
            select(PasswordHistory)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_old_password_history(
        self,
        user_id: uuid.UUID,
        keep_count: int,
    ) -> None:
        """Delete old password history entries beyond the keep count."""
        cte = (
            select(PasswordHistory.id)
            .where(PasswordHistory.user_id == user_id)
            .order_by(PasswordHistory.created_at.desc())
            .offset(keep_count)
            .cte()
        )
        await self.db.execute(
            delete(PasswordHistory).where(PasswordHistory.id.in_(cte))
        )
        await self.db.commit()

    # ---------------------------------------------------------------------------
    # Failed Login Attempts (Phase 11)
    # ---------------------------------------------------------------------------
    async def create_failed_login_attempt(self, **kwargs: Any) -> FailedLoginAttempt | None:
        """Record a failed login attempt; return None if the school_id FK is invalid."""
        failed_attempt = FailedLoginAttempt(**kwargs)
        self.db.add(failed_attempt)
        try:
            await self.db.flush()
        except IntegrityError:
            await self.db.rollback()
            return None
        return failed_attempt

    async def count_failed_login_attempts(
        self,
        email: str,
        user_id: uuid.UUID | None = None,
        minutes: int = 15,
    ) -> int:
        """Count failed login attempts in the last N minutes."""
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        query = select(func.count(FailedLoginAttempt.id)).where(
            FailedLoginAttempt.email == email,
            FailedLoginAttempt.created_at >= cutoff_time,
        )

        if user_id is not None:
            query = query.where(FailedLoginAttempt.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def delete_old_failed_login_attempts(
        self,
        days: int = 7,
    ) -> None:
        """Delete old failed login attempts older than N days."""
        from datetime import timedelta

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days)
        await self.db.execute(
            delete(FailedLoginAttempt).where(
                FailedLoginAttempt.created_at < cutoff_time
            )
        )
        await self.db.commit()

    # ---------------------------------------------------------------------------
    # Suspicious Activity Detection (Phase 11)
    # ---------------------------------------------------------------------------
    async def create_known_location(self, **kwargs: Any) -> KnownLocation:
        location = KnownLocation(**kwargs)
        self.db.add(location)
        await self.db.flush()
        return location

    async def get_known_location_by_user_ip(
        self,
        user_id: uuid.UUID,
        ip_address: str,
    ) -> KnownLocation | None:
        result = await self.db.execute(
            select(KnownLocation).where(
                KnownLocation.user_id == user_id,
                KnownLocation.ip_address == ip_address,
            )
        )
        return result.scalar_one_or_none()

    async def get_known_locations_by_user(
        self,
        user_id: uuid.UUID,
    ) -> list[KnownLocation]:
        result = await self.db.execute(
            select(KnownLocation).where(KnownLocation.user_id == user_id)
        )
        return result.scalars().all()

    async def update_known_location(
        self,
        location: KnownLocation,
    ) -> KnownLocation:
        await self.db.merge(location)
        await self.db.flush()
        return location

    async def create_known_device(self, **kwargs: Any) -> KnownDevice:
        device = KnownDevice(**kwargs)
        self.db.add(device)
        await self.db.flush()
        return device

    async def get_known_device_by_user_fingerprint(
        self,
        user_id: uuid.UUID,
        device_fingerprint: str,
    ) -> KnownDevice | None:
        result = await self.db.execute(
            select(KnownDevice).where(
                KnownDevice.user_id == user_id,
                KnownDevice.device_fingerprint == device_fingerprint,
            )
        )
        return result.scalar_one_or_none()

    async def get_known_devices_by_user(
        self,
        user_id: uuid.UUID,
    ) -> list[KnownDevice]:
        result = await self.db.execute(
            select(KnownDevice).where(KnownDevice.user_id == user_id)
        )
        return result.scalars().all()

    async def update_known_device(
        self,
        device: KnownDevice,
    ) -> KnownDevice:
        await self.db.merge(device)
        await self.db.flush()
        return device
