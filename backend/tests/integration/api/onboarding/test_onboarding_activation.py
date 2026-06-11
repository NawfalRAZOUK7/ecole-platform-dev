"""DB-backed service tests for the onboarding approve → activate → resend flow.

Exercises OnboardingService directly against a real (test) database session,
which avoids the SUP-token HTTP plumbing while still covering the substantive
logic:

  approve()           -> creates School + INACTIVE owner User + active Membership
                         + activation token; returns activation_url.
  activate_account()  -> valid token flips INACTIVE -> ACTIVE and clears token;
                         reused token rejected; expired token rejected; weak
                         password rejected (password policy).
  resend_activation() -> regenerates the token for a still-INACTIVE owner.

Requires the live test PostgreSQL (the `db_session` / `engine` fixtures in
tests/conftest.py). The activation token is only surfaced in the API result
outside production (settings.app_env != "production"), which holds in tests.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import hashlib

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.core.dependencies import AuthContext
from app.core.exceptions import ValidationError
from app.models.iam import Membership, User, UserStatus
from app.models.onboarding import (
    ApplicationStatus,
    ApplicationType,
    SchoolApplication,
)
from app.models.school import SchoolType
from app.services.platform.onboarding import OnboardingService
from tests.factories.iam import UserFactory
from tests.factories.school import SchoolFactory

pytestmark = pytest.mark.asyncio

STRONG_PASSWORD = "SecurePass123!"


async def _sup_auth(db_session) -> AuthContext:
    """SUP actor backed by a real User row so audit_logs FK is satisfied."""
    platform_school = await SchoolFactory.create(
        session=db_session,
        code=f"PLAT-{uuid.uuid4().hex[:6].upper()}",
        name="Platform Ops",
        city="Rabat",
    )
    sup_user = await UserFactory.create(
        session=db_session,
        school_id=platform_school.id,
    )
    await db_session.commit()
    return AuthContext(
        user_id=sup_user.id,
        role="SUP",
        school_id=platform_school.id,
        session_id=uuid.uuid4(),
        permissions=set(),
    )


async def _make_application(
    db_session,
    *,
    app_type: str = ApplicationType.MICRO_SCHOOL.value,
    email: str | None = None,
) -> SchoolApplication:
    app = SchoolApplication(
        application_type=app_type,
        status=ApplicationStatus.PENDING.value,
        applicant_name="Mr Idrissi",
        applicant_email=email or f"owner.{uuid.uuid4().hex[:8]}@example.ma",
        org_name="Micro-école Espoir",
        language="fr",
    )
    db_session.add(app)
    await db_session.commit()
    return app


class TestApprove:
    async def test_provisions_school_owner_and_token(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)

        result = await service.approve(
            application_id=app.id, auth=auth, ip_address="127.0.0.1"
        )

        assert result["status"] == ApplicationStatus.APPROVED.value
        assert result["role_target"] == "EDUCATOR"
        assert result["activation_url"].endswith(result.get("activation_token", ""))
        assert "/activate?token=" in result["activation_url"]

        owner = (
            await db_session.execute(
                select(User).where(User.id == uuid.UUID(result["created_user_id"]))
            )
        ).scalar_one()
        assert owner.status == UserStatus.INACTIVE.value
        assert owner.activation_token_hash is not None
        assert owner.activation_expires_at is not None
        assert owner.school_id == uuid.UUID(result["created_school_id"])

        membership = (
            await db_session.execute(
                select(Membership).where(Membership.user_id == owner.id)
            )
        ).scalar_one()
        assert membership.role_code == "EDUCATOR"

    async def test_formal_application_creates_adm_in_formal_school(
        self, db_session
    ) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(
            db_session, app_type=ApplicationType.FORMAL_SCHOOL.value
        )
        service = OnboardingService(db_session)
        result = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        assert result["role_target"] == "ADM"

    async def test_double_approve_rejected(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        await service.approve(application_id=app.id, auth=auth, ip_address=None)
        with pytest.raises(ValidationError):
            await service.approve(application_id=app.id, auth=auth, ip_address=None)


class TestActivate:
    async def test_valid_token_activates_and_clears(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        result = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        token = result["activation_token"]

        activated = await service.activate_account(
            token=token, password=STRONG_PASSWORD, ip_address=None
        )
        assert activated["status"] == "active"

        owner = (
            await db_session.execute(
                select(User).where(User.id == uuid.UUID(result["created_user_id"]))
            )
        ).scalar_one()
        assert owner.status == UserStatus.ACTIVE.value
        assert owner.activation_token_hash is None
        assert owner.activation_expires_at is None

    async def test_reused_token_rejected(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        result = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        token = result["activation_token"]
        await service.activate_account(
            token=token, password=STRONG_PASSWORD, ip_address=None
        )
        with pytest.raises(ValidationError):
            await service.activate_account(
                token=token, password=STRONG_PASSWORD, ip_address=None
            )

    async def test_expired_token_rejected(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        result = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        owner_id = uuid.UUID(result["created_user_id"])

        owner = (
            await db_session.execute(select(User).where(User.id == owner_id))
        ).scalar_one()
        owner.activation_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        with pytest.raises(ValidationError):
            await service.activate_account(
                token=result["activation_token"],
                password=STRONG_PASSWORD,
                ip_address=None,
            )

    async def test_weak_password_rejected(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        result = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        with pytest.raises(ValidationError):
            await service.activate_account(
                token=result["activation_token"],
                password="weakweakweak",  # 12 chars but no upper/digit/special
                ip_address=None,
            )

    async def test_invalid_token_rejected(self, db_session) -> None:
        service = OnboardingService(db_session)
        with pytest.raises(ValidationError):
            await service.activate_account(
                token="nonexistent-token-value-1234567890",
                password=STRONG_PASSWORD,
                ip_address=None,
            )


class TestResendActivation:
    async def test_resend_regenerates_token_and_works(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        approved = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        old_token = approved["activation_token"]

        resent = await service.resend_activation(
            application_id=app.id, auth=auth, ip_address=None
        )
        new_token = resent["activation_token"]
        assert new_token != old_token

        # Verify the old token hash is no longer stored (resend invalidated it).
        # We query the DB directly instead of calling activate_account(old_token),
        # because a failed UoW triggers session.rollback() which — inside the test's
        # outer-transaction fixture — would revert the resend_activation commit and
        # make the new token invisible to the next activate_account call.
        owner_row = (
            await db_session.execute(
                select(User).where(User.id == uuid.UUID(approved["created_user_id"]))
            )
        ).scalar_one()
        old_hash = hashlib.sha256(old_token.encode()).hexdigest()
        new_hash = hashlib.sha256(new_token.encode()).hexdigest()
        assert owner_row.activation_token_hash != old_hash
        assert owner_row.activation_token_hash == new_hash

        activated = await service.activate_account(
            token=new_token, password=STRONG_PASSWORD, ip_address=None
        )
        assert activated["status"] == "active"

    async def test_resend_after_activation_rejected(self, db_session) -> None:
        auth = await _sup_auth(db_session)
        app = await _make_application(db_session)
        service = OnboardingService(db_session)
        approved = await service.approve(
            application_id=app.id, auth=auth, ip_address=None
        )
        await service.activate_account(
            token=approved["activation_token"],
            password=STRONG_PASSWORD,
            ip_address=None,
        )
        with pytest.raises(ValidationError):
            await service.resend_activation(
                application_id=app.id, auth=auth, ip_address=None
            )


async def test_env_not_production_so_token_is_exposed() -> None:
    # The DB tests above rely on the activation token being present in the
    # service result, which only happens outside production.
    assert settings.app_env != "production"
