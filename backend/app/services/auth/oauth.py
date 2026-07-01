"""OAuth / Social Login service for Google, Microsoft, Apple.

Reference: Phase 10 — Social Login Support
"""

from typing import Any, Optional

import httpx
from authlib.integrations.httpx_client import AsyncOAuth2Client

from app.core.config import settings


class OAuthService:
    """Service for OAuth social login operations."""

    def __init__(self):
        self.google_client = None
        self.microsoft_client = None
        self.apple_client = None

        if settings.google_oauth_enabled:
            self.google_client = AsyncOAuth2Client(
                settings.google_oauth_client_id,
                settings.google_oauth_client_secret,
                base_url="https://oauth2.googleapis.com/token",
            )

        if settings.microsoft_oauth_enabled:
            self.microsoft_client = AsyncOAuth2Client(
                settings.microsoft_oauth_client_id,
                settings.microsoft_oauth_client_secret,
                base_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            )

        if settings.apple_oauth_enabled:
            self.apple_client = AsyncOAuth2Client(
                settings.apple_oauth_client_id,
                settings.apple_oauth_client_secret,
                base_url="https://appleid.apple.com/auth/token",
            )

    def get_client(self, provider: str) -> Optional[AsyncOAuth2Client]:
        """Get OAuth client for the specified provider."""
        clients = {
            "google": self.google_client,
            "microsoft": self.microsoft_client,
            "apple": self.apple_client,
        }
        return clients.get(provider)

    async def exchange_code_for_token(
        self,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> dict[str, Any]:
        """Exchange OAuth authorization code for access token."""
        client = self.get_client(provider)
        if not client:
            raise ValueError(f"OAuth provider '{provider}' is not enabled")

        token_url = self._get_token_url(provider)
        params = {
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "client_id": getattr(settings, f"{provider}_oauth_client_id", ""),
            "client_secret": getattr(settings, f"{provider}_oauth_client_secret", ""),
        }

        async with httpx.AsyncClient(timeout=20.0) as http_client:
            response = await http_client.post(token_url, data=params)
            response.raise_for_status()
            return response.json()

    async def get_user_info(
        self,
        provider: str,
        access_token: str,
    ) -> dict[str, Any]:
        """Get user information from OAuth provider using access token."""
        user_info_url = self._get_user_info_url(provider)

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                user_info_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def _get_token_url(self, provider: str) -> str:
        """Get token endpoint URL for the provider."""
        if settings.mock_oauth_enabled:
            return f"{settings.mock_oauth_base_url}/token"
        urls = {
            "google": "https://oauth2.googleapis.com/token",
            "microsoft": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            "apple": "https://appleid.apple.com/auth/token",
        }
        return urls.get(provider)

    def _get_user_info_url(self, provider: str) -> str:
        """Get user info endpoint URL for the provider."""
        if settings.mock_oauth_enabled:
            if provider == "microsoft":
                return f"{settings.mock_oauth_base_url}/v1.0/me"
            return f"{settings.mock_oauth_base_url}/oauth2/v3/userinfo"
        urls = {
            "google": "https://www.googleapis.com/oauth2/v2/userinfo",
            "microsoft": "https://graph.microsoft.com/v1.0/me",
            "apple": "https://appleid.apple.com/v1/me",
        }
        return urls.get(provider)

    def normalize_user_info(
        self,
        provider: str,
        user_info: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize user info from different OAuth providers to a common format."""
        if provider == "google":
            return {
                "provider_user_id": user_info.get("id") or user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            }
        elif provider == "microsoft":
            return {
                "provider_user_id": user_info.get("id") or user_info.get("sub"),
                "email": user_info.get("userPrincipalName")
                or user_info.get("mail")
                or user_info.get("email"),
                "name": user_info.get("displayName"),
                "picture": None,
            }
        elif provider == "apple":
            return {
                "provider_user_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name", {}).get("firstName", "")
                + " "
                + user_info.get("name", {}).get("lastName", ""),
                "picture": None,
            }
        else:
            raise ValueError(f"Unknown OAuth provider: {provider}")
