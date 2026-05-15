"""OAuth / Social Login API endpoints (Phase 10).

Reference: Phase 10 — Social Login Support
Public endpoints: login URL generation, token exchange.
"""

from __future__ import annotations

import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.redis import get_redis
from app.core.response import ApiResponse, Meta, success_response
from app.repositories.auth import AuthRepository
from app.schemas.auth import OAuthLoginRequest
from app.services.auth.oauth import OAuthService

router = APIRouter(prefix="/auth/oauth", tags=["auth"])


# ---------------------------------------------------------------------------
# GET /auth/oauth/{provider}/url — Get authorization URL (public)
# ---------------------------------------------------------------------------
@router.get(
    "/{provider}/url",
    response_model=ApiResponse[dict],
    summary="Get OAuth authorization URL",
    response_description="URL to redirect the user to for OAuth consent",
)
async def get_oauth_url(
    provider: str,
    redirect_uri: str,
):
    """Generate the OAuth authorization URL for the requested provider."""
    if provider == "google" and not settings.google_oauth_enabled:
        raise ValidationError(
            "Google OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )
    if provider == "microsoft" and not settings.microsoft_oauth_enabled:
        raise ValidationError(
            "Microsoft OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )
    if provider == "apple" and not settings.apple_oauth_enabled:
        raise ValidationError(
            "Apple OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    # Standard OAuth 2.0 authorization endpoint URLs
    auth_urls = {
        "google": "https://accounts.google.com/o/oauth2/v2/auth",
        "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "apple": "https://appleid.apple.com/auth/authorize",
    }

    url = auth_urls.get(provider)
    if url is None:
        raise ValidationError(
            f"Unsupported OAuth provider: {provider}",
            error_code="ERR-OAUTH-PROVIDER",
        )

    # Build query params (client_id is required)
    client_id = getattr(settings, f"{provider}_oauth_client_id", "")
    if not client_id:
        raise ValidationError(
            f"OAuth client ID not configured for {provider}",
            error_code="ERR-OAUTH-CONFIG",
        )

    scope = {
        "google": "openid email profile",
        "microsoft": "openid email profile User.Read",
        "apple": "name email",
    }.get(provider, "openid email")

    import secrets

    state = secrets.token_urlsafe(32)

    from urllib.parse import urlencode

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "state": state,
    }
    if provider == "apple":
        params["response_mode"] = "form_post"

    auth_url = f"{url}?{urlencode(params)}"

    return success_response(
        {
            "auth_url": auth_url,
            "state": state,
        }
    )


# ---------------------------------------------------------------------------
# POST /auth/oauth/login — Exchange code for tokens (public)
# ---------------------------------------------------------------------------
@router.post(
    "/login",
    response_model=ApiResponse[dict],
    summary="OAuth login",
    response_description="JWT tokens after successful OAuth exchange",
)
async def oauth_login(
    body: OAuthLoginRequest,
    db: AsyncSession = Depends(get_db),
    redis_client: aioredis.Redis = Depends(get_redis),
):
    """Exchange an OAuth authorization code for access tokens and log the user in."""
    provider = body.provider
    if provider == "google" and not settings.google_oauth_enabled:
        raise ValidationError(
            "Google OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )
    if provider == "microsoft" and not settings.microsoft_oauth_enabled:
        raise ValidationError(
            "Microsoft OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )
    if provider == "apple" and not settings.apple_oauth_enabled:
        raise ValidationError(
            "Apple OAuth is not enabled",
            error_code="ERR-FEATURE-DISABLED",
        )

    service = OAuthService()

    # Exchange code for access token
    try:
        token_data = await service.exchange_code_for_token(
            provider=provider,
            code=body.code,
            redirect_uri=body.redirect_uri,
        )
    except Exception as exc:
        raise ValidationError(
            f"Failed to exchange OAuth code: {exc}",
            error_code="ERR-OAUTH-EXCHANGE",
        ) from exc

    access_token = token_data.get("access_token")
    if not access_token:
        raise ValidationError(
            "No access token received from OAuth provider",
            error_code="ERR-OAUTH-TOKEN",
        )

    # Get user info from provider
    try:
        user_info = await service.get_user_info(provider, access_token)
    except Exception as exc:
        raise ValidationError(
            f"Failed to fetch user info: {exc}",
            error_code="ERR-OAUTH-USERINFO",
        ) from exc

    normalized = service.normalize_user_info(provider, user_info)
    provider_user_id = normalized.get("provider_user_id")
    email = normalized.get("email")
    name = normalized.get("name")

    if not provider_user_id or not email:
        raise ValidationError(
            "Incomplete user info from OAuth provider",
            error_code="ERR-OAUTH-USERINFO",
        )

    repo = AuthRepository(db)

    # Look up existing OAuth account
    oauth_account = await repo.get_oauth_account_by_provider_user_id(
        provider, provider_user_id
    )

    if oauth_account is not None:
        # Existing user — issue tokens
        user = await repo.get_user_by_id(oauth_account.user_id)
        if user is None:
            raise NotFoundError(
                "User associated with OAuth account not found",
                error_code="ERR-IAM-404",
            )

        membership = await repo.get_membership(
            user.id,
            body.school_id,
        )
        if membership is None:
            raise NotFoundError(
                "No active membership for this school",
                error_code="ERR-IAM-404",
            )

        from app.services.auth.auth import AuthService

        auth_service = AuthService(db, redis_client)
        token_bundle = await auth_service._issue_token_bundle(
            user_id=user.id,
            role=membership.role_code,
            school_id=body.school_id,
            session_id=uuid.uuid4(),
        )
        return success_response(token_bundle)

    # New OAuth user — auto-create if email is not already used in this school
    existing_user = await repo.get_user_by_email(email, body.school_id)
    if existing_user is not None:
        # Link OAuth account to existing user
        await repo.create_oauth_account(
            user_id=existing_user.id,
            school_id=body.school_id,
            provider=provider,
            provider_user_id=provider_user_id,
            provider_email=email,
            access_token=access_token,
            token_expires_at=None,  # TODO: parse expires_in
        )

        membership = await repo.get_membership(
            existing_user.id,
            body.school_id,
        )
        if membership is None:
            raise NotFoundError(
                "No active membership for this school",
                error_code="ERR-IAM-404",
            )

        from app.services.auth.auth import AuthService

        auth_service = AuthService(db, redis_client)
        token_bundle = await auth_service._issue_token_bundle(
            user_id=existing_user.id,
            role=membership.role_code,
            school_id=body.school_id,
            session_id=uuid.uuid4(),
        )
        return success_response(token_bundle)

    # Completely new user — create user + membership + OAuth link
    from app.core.security import hash_password
    import secrets as pysecrets

    temp_password = pysecrets.token_urlsafe(32)
    user = await repo.create_user(
        email=email,
        full_name=name or email,
        password_hash=hash_password(temp_password),
        status="active",
        school_id=body.school_id,
    )
    membership = await repo.create_membership(
        user_id=user.id,
        school_id=body.school_id,
        role_code="STD",  # Default role for OAuth sign-ups
        status="active",
    )
    await repo.create_oauth_account(
        user_id=user.id,
        school_id=body.school_id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=email,
        access_token=access_token,
    )

    from app.services.auth import AuthService

    auth_service = AuthService(db, redis_client)
    token_bundle = await auth_service._issue_token_bundle(
        user_id=user.id,
        role=membership.role_code,
        school_id=body.school_id,
        session_id=uuid.uuid4(),
    )
    token_bundle["email_verification_required"] = True

    return success_response(token_bundle)
