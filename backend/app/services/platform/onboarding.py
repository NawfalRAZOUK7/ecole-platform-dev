"""Onboarding application service — public create, SUP review, approve+provision.

On approval we provision the tenant (School, formal or informal) AND the owner
account in one step: a User is created in the INACTIVE state with a one-time
activation token, plus a Membership granting the owner role (ADM or EDUCATOR).
The applicant receives an emailed activation link (`/activate?token=…`) where
they set their own password; doing so flips the account to ACTIVE. No separate
invitation-code/register round-trip is required.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import hash_password
from app.core.storage import storage
from app.core.unit_of_work import UnitOfWork
from app.models.iam import Membership, User, UserStatus
from app.models.onboarding import (
    ApplicationStatus,
    ApplicationType,
    AttachmentKind,
    SchoolApplication,
    SchoolApplicationAttachment,
)
from app.models.school import SchoolType
from app.repositories.auth import AuthRepository
from app.repositories.school import SchoolRepository
from app.services.platform.audit import AuditService

_ROLE_BY_TYPE = {
    ApplicationType.FORMAL_SCHOOL.value: "ADM",
    ApplicationType.MICRO_SCHOOL.value: "EDUCATOR",
}
_SCHOOL_TYPE_BY_APP = {
    ApplicationType.FORMAL_SCHOOL.value: SchoolType.FORMAL.value,
    ApplicationType.MICRO_SCHOOL.value: SchoolType.INFORMAL.value,
}


def _school_code(org_name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9]", "", org_name).upper()[:6] or "SCHOOL"
    return f"{base}-{secrets.token_hex(3).upper()}"


class OnboardingService:
    def __init__(self, db) -> None:
        self.db = db

    @staticmethod
    def _to_dict(app: SchoolApplication) -> dict[str, Any]:
        return {
            "id": str(app.id),
            "application_type": app.application_type,
            "status": app.status,
            "applicant_name": app.applicant_name,
            "applicant_email": app.applicant_email,
            "applicant_phone": app.applicant_phone,
            "city": app.city,
            "language": app.language,
            "org_name": app.org_name,
            "address": app.address,
            "neighborhood": app.neighborhood,
            "max_capacity": app.max_capacity,
            "level_band": app.level_band,
            "subjects": app.subjects,
            "notes": app.notes,
            "review_notes": app.review_notes,
            "created_school_id": (
                str(app.created_school_id) if app.created_school_id else None
            ),
            "created_at": app.created_at.isoformat() if app.created_at else None,
            "attachments": [
                {
                    "id": str(a.id),
                    "file_path": a.file_path,
                    "mime_type": a.mime_type,
                    "file_size": a.file_size,
                    "kind": a.kind,
                }
                for a in (app.attachments or [])
            ],
        }

    async def create_application(
        self, *, application_type: str, body: Any
    ) -> dict[str, Any]:
        async with UnitOfWork(self.db) as uow:
            app = SchoolApplication(
                application_type=application_type,
                status=ApplicationStatus.PENDING.value,
                applicant_name=body.applicant_name,
                applicant_email=str(body.applicant_email),
                applicant_phone=getattr(body, "applicant_phone", None),
                city=getattr(body, "city", None),
                language=getattr(body, "language", None),
                org_name=body.org_name,
                address=getattr(body, "address", None),
                neighborhood=getattr(body, "neighborhood", None),
                max_capacity=getattr(body, "max_capacity", None),
                level_band=getattr(body, "level_band", None),
                subjects=getattr(body, "subjects", None),
                notes=getattr(body, "notes", None),
            )
            uow.session.add(app)
            await uow.session.flush()
            app_id = app.id
            await uow.commit()
        return await self.get_application(app_id)

    async def add_attachment(
        self,
        *,
        application_id: uuid.UUID,
        file: Any,
        kind: str,
    ) -> dict[str, Any]:
        allowed_kinds = {item.value for item in AttachmentKind}
        kind = kind if kind in allowed_kinds else AttachmentKind.OTHER.value
        content_type = getattr(file, "content_type", None) or "application/octet-stream"
        allowed_mime = (
            content_type.startswith("image/") or content_type == "application/pdf"
        )
        if not allowed_mime:
            raise ValidationError(
                "Only images and PDF files are allowed",
                error_code="ERR-UPLOAD-MIME",
            )

        relative_path, _checksum, file_size = await storage.save(
            file.file,
            getattr(file, "filename", "attachment"),
            subdirectory=f"applications/{application_id}",
        )
        max_bytes = 10 * 1024 * 1024  # 10 MB cap
        if file_size > max_bytes:
            await storage.delete(relative_path)
            raise ValidationError(
                "File too large (max 10 MB)", error_code="ERR-UPLOAD-SIZE"
            )

        async with UnitOfWork(self.db) as uow:
            app = await uow.session.get(SchoolApplication, application_id)
            if app is None:
                raise NotFoundError(
                    "Application not found", error_code="ERR-APP-404"
                )
            attachment = SchoolApplicationAttachment(
                application_id=application_id,
                file_path=relative_path,
                mime_type=content_type,
                file_size=file_size,
                kind=kind,
            )
            uow.session.add(attachment)
            await uow.session.flush()
            attachment_id = attachment.id
            await uow.commit()

        return {
            "id": str(attachment_id),
            "file_path": relative_path,
            "mime_type": content_type,
            "file_size": file_size,
            "kind": kind,
        }

    async def list_applications(
        self, *, status: str | None, application_type: str | None
    ) -> list[dict[str, Any]]:
        query = (
            select(SchoolApplication)
            .options(selectinload(SchoolApplication.attachments))
            .order_by(SchoolApplication.created_at.desc())
        )
        if status:
            query = query.where(SchoolApplication.status == status)
        if application_type:
            query = query.where(
                SchoolApplication.application_type == application_type
            )
        result = await self.db.execute(query)
        return [self._to_dict(a) for a in result.scalars().all()]

    async def get_application(self, application_id: uuid.UUID) -> dict[str, Any]:
        result = await self.db.execute(
            select(SchoolApplication)
            .options(selectinload(SchoolApplication.attachments))
            .where(SchoolApplication.id == application_id)
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundError("Application not found", error_code="ERR-APP-404")
        return self._to_dict(app)

    async def approve(
        self, *, application_id: uuid.UUID, auth: AuthContext, ip_address: str | None
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        # One-time activation token (URL-safe). Only the SHA-256 hash is stored;
        # the plaintext travels in the emailed link and the API response.
        plaintext_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plaintext_token.encode()).hexdigest()

        async with UnitOfWork(self.db) as uow:
            app = await uow.session.get(SchoolApplication, application_id)
            if app is None:
                raise NotFoundError("Application not found", error_code="ERR-APP-404")
            if app.status == ApplicationStatus.APPROVED.value:
                raise ValidationError(
                    "Application already approved", error_code="ERR-APP-409"
                )

            role_target = _ROLE_BY_TYPE.get(app.application_type, "ADM")
            school_type = _SCHOOL_TYPE_BY_APP.get(
                app.application_type, SchoolType.FORMAL.value
            )

            repo = SchoolRepository(uow.session)
            school = await repo.create_school(
                {
                    "name": app.org_name,
                    "code": _school_code(app.org_name),
                    "school_type": school_type,
                    "city": app.city,
                    "address": app.address,
                    "email": app.applicant_email,
                    "phone": app.applicant_phone,
                    "default_language": app.language or "fr",
                }
            )

            # Email is unique *per school* (uq_users_email_school), and every
            # approval creates a brand-new school, so provisioning the owner is
            # always safe — the same person may legitimately own multiple schools
            # (e.g. an educator who also runs a formal school). The defensive
            # per-school check below therefore never trips for a fresh tenant but
            # documents the invariant.
            auth_repo = AuthRepository(uow.session)
            clash = await auth_repo.get_user_by_email(
                app.applicant_email, school.id
            )
            if clash is not None:
                raise ValidationError(
                    "An account with this email already exists for this school.",
                    error_code="ERR-APP-EMAIL-EXISTS",
                )

            # Provision the owner account INACTIVE with the activation token. The
            # password is a throwaway random hash; the owner sets a real one via
            # the activation link.
            owner_kwargs: dict[str, Any] = {
                "email": app.applicant_email,
                "full_name": app.applicant_name,
                "school_id": school.id,
                "password_hash": hash_password(secrets.token_urlsafe(24)),
                "status": UserStatus.INACTIVE.value,
                "activation_token_hash": token_hash,
                "activation_expires_at": now + timedelta(hours=72),
            }
            phone = (app.applicant_phone or "").strip()
            if phone.startswith("+"):
                owner_kwargs["phone"] = phone
            owner = await auth_repo.create_user(**owner_kwargs)
            await auth_repo.create_membership(
                user_id=owner.id,
                school_id=school.id,
                role_code=role_target,
                status="active",
            )

            app.status = ApplicationStatus.APPROVED.value
            app.reviewed_by = auth.user_id
            app.reviewed_at = now
            app.created_school_id = school.id
            app.created_user_id = owner.id

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type="ONBOARDING_APPLICATION_APPROVED",
                outcome="success",
                target_type="school_application",
                target_id=app.id,
                entity_after={
                    "school_id": str(school.id),
                    "school_type": school_type,
                    "role_target": role_target,
                    "owner_user_id": str(owner.id),
                },
                ip_address=ip_address,
            )
            applicant_email = app.applicant_email
            applicant_name = app.applicant_name
            org_name = app.org_name
            language = app.language or "fr"
            await uow.commit()
            school_id = school.id
            owner_id = owner.id

        activation_url = (
            f"{settings.web_app_base_url}/activate?token={plaintext_token}"
        )

        # Best-effort: email the activation link. The plaintext token is also
        # returned (dev convention, like mock SMS) so the reviewer can relay the
        # link if email delivery is unavailable.
        try:
            from app.services.auth.email import email_service

            await email_service.send_email(
                to=applicant_email,
                template_name="application_approved",
                lang=language,
                applicant_name=applicant_name,
                org_name=org_name,
                role=role_target,
                activation_url=activation_url,
            )
        except Exception:  # pragma: no cover - email is best-effort
            import logging

            logging.getLogger(__name__).exception(
                "Approval email failed (best-effort)"
            )

        result = {
            "application_id": str(application_id),
            "status": ApplicationStatus.APPROVED.value,
            "created_school_id": str(school_id),
            "created_user_id": str(owner_id),
            "role_target": role_target,
            "activation_url": activation_url,
        }
        # Surface the raw token only outside production (dev convenience, mirrors
        # how the mock email OTP is exposed). In production the link is delivered
        # by email and the SUP console can still copy the activation_url.
        if settings.app_env != "production":
            result["activation_token"] = plaintext_token
        return result

    async def resend_activation(
        self, *, application_id: uuid.UUID, auth: AuthContext, ip_address: str | None
    ) -> dict[str, Any]:
        """Re-issue an activation link for an approved app whose owner is still
        INACTIVE (e.g. the original 72h link expired). Generates a fresh token,
        re-emails the link, and invalidates the previous one.
        """
        now = datetime.now(timezone.utc)
        plaintext_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(plaintext_token.encode()).hexdigest()

        async with UnitOfWork(self.db) as uow:
            app = await uow.session.get(SchoolApplication, application_id)
            if app is None:
                raise NotFoundError("Application not found", error_code="ERR-APP-404")
            if app.status != ApplicationStatus.APPROVED.value:
                raise ValidationError(
                    "Only approved applications can have an activation link resent.",
                    error_code="ERR-APP-NOT-APPROVED",
                )
            if app.created_user_id is None:
                raise ValidationError(
                    "No owner account is associated with this application.",
                    error_code="ERR-APP-NO-OWNER",
                )
            owner = await uow.session.get(User, app.created_user_id)
            if owner is None:
                raise NotFoundError(
                    "Owner account not found", error_code="ERR-APP-OWNER-404"
                )
            if owner.status == UserStatus.ACTIVE.value:
                raise ValidationError(
                    "This account is already activated; no link is needed.",
                    error_code="ERR-APP-ALREADY-ACTIVE",
                )

            # Fresh token invalidates the previous one (single active link).
            owner.activation_token_hash = token_hash
            owner.activation_expires_at = now + timedelta(hours=72)

            role_target = _ROLE_BY_TYPE.get(app.application_type, "ADM")
            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=app.created_school_id,
                actor_id=auth.user_id,
                action_type="ONBOARDING_ACTIVATION_RESENT",
                outcome="success",
                target_type="user",
                target_id=owner.id,
                entity_after={"activation_expires_at": owner.activation_expires_at.isoformat()},
                ip_address=ip_address,
            )
            applicant_email = app.applicant_email
            applicant_name = app.applicant_name
            org_name = app.org_name
            language = app.language or "fr"
            await uow.commit()
            owner_id = owner.id

        activation_url = (
            f"{settings.web_app_base_url}/activate?token={plaintext_token}"
        )
        try:
            from app.services.auth.email import email_service

            await email_service.send_email(
                to=applicant_email,
                template_name="application_approved",
                lang=language,
                applicant_name=applicant_name,
                org_name=org_name,
                role=role_target,
                activation_url=activation_url,
            )
        except Exception:  # pragma: no cover - email is best-effort
            import logging

            logging.getLogger(__name__).exception(
                "Resend-activation email failed (best-effort)"
            )

        result = {
            "application_id": str(application_id),
            "status": ApplicationStatus.APPROVED.value,
            "created_user_id": str(owner_id),
            "role_target": role_target,
            "activation_url": activation_url,
        }
        if settings.app_env != "production":
            result["activation_token"] = plaintext_token
        return result

    async def activate_account(
        self, *, token: str, password: str, ip_address: str | None
    ) -> dict[str, Any]:
        """Set the owner's password using a one-time activation token.

        Verifies the token hash against an INACTIVE user, checks expiry, sets the
        new password, flips the account to ACTIVE and clears the token (single
        use). Errors are deliberately generic so the endpoint does not reveal
        whether a token exists.
        """
        now = datetime.now(timezone.utc)
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        async with UnitOfWork(self.db) as uow:
            result = await uow.session.execute(
                select(User).where(User.activation_token_hash == token_hash)
            )
            user = result.scalar_one_or_none()
            if user is None or user.status != UserStatus.INACTIVE.value:
                raise ValidationError(
                    "Invalid or already-used activation link.",
                    error_code="ERR-ACTIVATE-INVALID",
                )
            if (
                user.activation_expires_at is None
                or user.activation_expires_at < now
            ):
                raise ValidationError(
                    "This activation link has expired.",
                    error_code="ERR-ACTIVATE-EXPIRED",
                )

            # Enforce the same password policy as register/reset (Phase 2A).
            from app.core.password_policy import password_validator

            password_validator.validate(
                password, email=user.email, full_name=user.full_name
            )

            user.password_hash = hash_password(password)
            user.status = UserStatus.ACTIVE.value
            user.activation_token_hash = None
            user.activation_expires_at = None

            # Audit against the owner's school (AuditLog.school_id is NOT NULL).
            school_row = await uow.session.execute(
                select(Membership.school_id)
                .where(Membership.user_id == user.id)
                .limit(1)
            )
            audit_school_id = school_row.scalar_one_or_none()
            if audit_school_id is not None:
                audit = AuditService(uow.session)
                await audit.log_event(
                    school_id=audit_school_id,
                    actor_id=user.id,
                    action_type="ONBOARDING_ACCOUNT_ACTIVATED",
                    outcome="success",
                    target_type="user",
                    target_id=user.id,
                    entity_after={"status": UserStatus.ACTIVE.value},
                    ip_address=ip_address,
                )
            user_id = user.id
            email = user.email
            await uow.commit()

        return {"user_id": user_id, "email": email, "status": "active"}

    async def review(
        self,
        *,
        application_id: uuid.UUID,
        new_status: str,
        body: Any,
        auth: AuthContext,
        ip_address: str | None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with UnitOfWork(self.db) as uow:
            app = await uow.session.get(SchoolApplication, application_id)
            if app is None:
                raise NotFoundError("Application not found", error_code="ERR-APP-404")
            if app.status == ApplicationStatus.APPROVED.value:
                raise ValidationError(
                    "Approved applications cannot be changed",
                    error_code="ERR-APP-409",
                )
            app.status = new_status
            app.review_notes = getattr(body, "review_notes", None)
            app.reviewed_by = auth.user_id
            app.reviewed_at = now

            audit = AuditService(uow.session)
            await audit.log_event(
                school_id=auth.school_id,
                actor_id=auth.user_id,
                action_type=f"ONBOARDING_APPLICATION_{new_status.upper()}",
                outcome="success",
                target_type="school_application",
                target_id=app.id,
                entity_after={"status": new_status},
                ip_address=ip_address,
            )
            await uow.commit()
        return await self.get_application(application_id)
