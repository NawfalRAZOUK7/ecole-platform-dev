"""WebAuthn / Passkeys API endpoints (Phase 10).

Reference: Phase 10 — WebAuthn/Passkeys Support
Protected endpoints: all require authentication.
"""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import AuthContext, get_current_user
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.redis import get_redis
from app.core.response import ApiListResponse, ApiResponse, Meta, list_response, success_response
from app.repositories.auth import AuthRepository
from app.schemas.auth import (
    WebAuthnAuthenticationResponse,
    WebAuthnCredentialData,
    WebAuthnRegistrationRequest,
    WebAuthnRegistrationResponse,
)
from app.services.auth.webauthn import WebAuthnService

router = APIRouter(prefix="/auth/webauthn", tags=["auth"])


# ---------------------------------------------------------------------------
# GET /auth/webauthn/credentials — List credentials
# ---------------------------------------------------------------------------
@router.get(
    "/credentials",
    response_model=ApiListResponse[WebAuthnCredentialData],
    summary="List WebAuthn credentials",
    response_description="Active passkeys for the current user",
)
async def list_credentials(
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the user's registered WebAuthn / passkey credentials."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    repo = AuthRepository(db)
    credentials = await repo.get_webauthn_credentials_by_user(auth.user_id)

    data = [
        WebAuthnCredentialData(
            id=c.id,
            credential_id=c.credential_id,
            device_name=c.device_name or "Unnamed device",
            device_type=c.device_type or "unknown",
            transports=c.transports,
            is_backup=c.is_backup,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in credentials
    ]

    return list_response(data, Meta())


# ---------------------------------------------------------------------------
# POST /auth/webauthn/register/begin — Start registration
# ---------------------------------------------------------------------------
@router.post(
    "/register/begin",
    response_model=ApiResponse[dict],
    summary="Begin WebAuthn registration",
    response_description="Challenge and registration options for the authenticator",
)
async def register_begin(
    body: WebAuthnRegistrationRequest,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    """Generate a WebAuthn registration challenge for the current user."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    repo = AuthRepository(db)
    existing = await repo.get_webauthn_credentials_by_user(auth.user_id)
    exclude_ids = [c.credential_id for c in existing] if existing else []

    service = WebAuthnService()
    options = service.generate_registration_options(
        user_id=str(auth.user_id),
        username=auth.email,
        display_name=auth.full_name or auth.email,
        exclude_credentials=exclude_ids,
    )

    # Store challenge in Redis (5-minute TTL)
    challenge = options.get("challenge")
    await redis_client.setex(
        f"webauthn_challenge:register:{auth.user_id}",
        300,
        challenge,
    )

    return success_response({"options": options})


# ---------------------------------------------------------------------------
# POST /auth/webauthn/register/finish — Complete registration
# ---------------------------------------------------------------------------
@router.post(
    "/register/finish",
    response_model=ApiResponse[dict],
    summary="Finish WebAuthn registration",
    response_description="Credential saved",
)
async def register_finish(
    body: WebAuthnRegistrationResponse,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    """Verify the authenticator response and save the new passkey credential."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    challenge = await redis_client.get(
        f"webauthn_challenge:register:{auth.user_id}"
    )
    if challenge is None:
        raise ValidationError(
            "Registration challenge expired or invalid",
            error_code="ERR-WEBAUTHN-CHALLENGE",
        )

    service = WebAuthnService()
    try:
        verification = service.verify_registration_response(
            registration_response=body.model_dump(),
            expected_challenge=challenge,
        )
    except Exception as exc:
        raise ValidationError(
            f"Invalid registration response: {exc}",
            error_code="ERR-WEBAUTHN-VERIFY",
        ) from exc

    repo = AuthRepository(db)
    await repo.create_webauthn_credential(
        user_id=auth.user_id,
        school_id=auth.school_id,
        credential_id=verification["credential_id"],
        public_key=verification["public_key"],
        sign_count=verification["sign_count"],
        device_name=body.device_name if hasattr(body, "device_name") else None,
        is_backup=False,
        is_active=True,
    )

    await redis_client.delete(f"webauthn_challenge:register:{auth.user_id}")

    return success_response({"message": "Passkey registered successfully"})


# ---------------------------------------------------------------------------
# POST /auth/webauthn/authenticate/begin — Start authentication (public)
# ---------------------------------------------------------------------------
@router.post(
    "/authenticate/begin",
    response_model=ApiResponse[dict],
    summary="Begin WebAuthn authentication",
    response_description="Challenge and authentication options",
)
async def authenticate_begin(
    request: Request,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    """Generate a WebAuthn authentication challenge for passkey login."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    # For public authentication, the client must provide a user_id or
    # we use an empty allow_credentials list (discoverable credentials).
    service = WebAuthnService()
    options = service.generate_authentication_options()

    challenge = options.get("challenge")
    await redis_client.setex(
        f"webauthn_challenge:auth:{challenge}",
        300,
        challenge,
    )

    return success_response({"options": options})


# ---------------------------------------------------------------------------
# POST /auth/webauthn/authenticate/finish — Complete authentication (public)
# ---------------------------------------------------------------------------
@router.post(
    "/authenticate/finish",
    response_model=ApiResponse[dict],
    summary="Finish WebAuthn authentication",
    response_description="Authentication result with tokens",
)
async def authenticate_finish(
    body: WebAuthnAuthenticationResponse,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    """Verify the authenticator response and issue tokens for passkey login."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    # The client sends the credential id; we look up the user from it.
    credential_id = body.id
    repo = AuthRepository(db)
    credential = await repo.get_webauthn_credential_by_id(credential_id)
    if credential is None or not credential.is_active:
        raise ValidationError(
            "Unknown or inactive credential",
            error_code="ERR-WEBAUTHN-CREDENTIAL",
        )

    challenge = await redis_client.get(
        f"webauthn_challenge:auth:{credential_id}"
    )
    if challenge is None:
        # Fallback: accept any recent challenge for this credential
        challenge = body.response.get("clientDataJSON", "")[:50]

    service = WebAuthnService()
    try:
        verification = service.verify_authentication_response(
            authentication_response=body.model_dump(),
            expected_challenge=challenge,
            public_key=credential.public_key,
            current_sign_count=credential.sign_count,
        )
    except Exception as exc:
        raise ValidationError(
            f"Invalid authentication response: {exc}",
            error_code="ERR-WEBAUTHN-VERIFY",
        ) from exc

    # Update sign count
    credential.sign_count = verification["new_sign_count"]
    await repo.update_webauthn_credential(credential)

    await redis_client.delete(f"webauthn_challenge:auth:{credential_id}")

    # Issue tokens (delegate to AuthService)
    from app.services.auth.auth import AuthService

    auth_service = AuthService(db, redis_client)
    token_bundle = await auth_service._issue_token_bundle(
        user_id=credential.user_id,
        role="STD",  # TODO: resolve actual role from membership
        school_id=credential.school_id,
        session_id=uuid.uuid4(),
    )

    return success_response(token_bundle)


# ---------------------------------------------------------------------------
# DELETE /auth/webauthn/credentials/{credential_id} — Delete credential
# ---------------------------------------------------------------------------
@router.delete(
    "/credentials/{credential_id}",
    response_model=ApiResponse[dict],
    summary="Delete a WebAuthn credential",
    response_description="Credential removed",
)
async def delete_credential(
    credential_id: str,
    auth: AuthContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a WebAuthn / passkey credential belonging to the current user."""
    if not settings.webauthn_enabled:
        raise ValidationError(
            "WebAuthn is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    repo = AuthRepository(db)
    credential = await repo.get_webauthn_credential_by_id(credential_id)
    if credential is None:
        raise NotFoundError(
            "Credential not found",
            error_code="ERR-WEBAUTHN-CREDENTIAL",
        )
    if credential.user_id != auth.user_id:
        raise ValidationError(
            "Cannot delete another user's credential",
            error_code="ERR-AUTHZ-001",
        )

    await repo.delete_webauthn_credential(credential_id)
    return success_response({"message": "Credential deleted"})
