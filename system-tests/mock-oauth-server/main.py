#!/usr/bin/env python3
"""
Mock OAuth Provider Server for Testing

Mimics Google, Microsoft, and Apple OAuth endpoints without real credentials.
Used for E2E testing OAuth flows in Docker and CI.

Endpoints:
- /auth/{provider}/authorize - Returns fake authorization URL with mock state
- /token - Exchanges authorization code for mock JWT tokens
- /oauth2/v3/userinfo - Returns mock user profile (Google-style)
- /v1.0/me - Returns mock user profile (Microsoft-style)
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from jose import jwt

# Configuration
PORT = int(os.getenv("PORT", "9999"))
MOCK_USERS_FILE = os.getenv("MOCK_USERS_FILE", "/app/fixtures/oauth-users.json")
JWT_SECRET = "mock-oauth-secret-key-for-testing-only"
JWT_ALGORITHM = "HS256"

# Load mock users
MOCK_USERS: Dict[str, Dict[str, Any]] = {}

try:
    with open(MOCK_USERS_FILE, "r") as f:
        MOCK_USERS = json.load(f)
except FileNotFoundError:
    # Default fallback users
    MOCK_USERS = {
        "google": {
            "sub": "1234567890",
            "email": "mock.google@example.com",
            "name": "Mock Google User",
            "given_name": "Mock",
            "family_name": "Google User",
            "picture": "https://example.com/avatar-google.png",
        },
        "microsoft": {
            "sub": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "email": "mock.microsoft@example.com",
            "name": "Mock Microsoft User",
                },
        "apple": {
            "sub": "001234.abcd1234efgh5678ijkl9012mno3",
            "email": "mock.apple@example.com",
            "name": "Mock Apple User",
        },
    }

app = FastAPI(title="Mock OAuth Provider", version="1.0.0")


class TokenRequest(BaseModel):
    grant_type: str = "authorization_code"
    code: str
    redirect_uri: str
    client_id: str
    client_secret: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


# In-memory code store (for testing)
AUTHORIZATION_CODES: Dict[str, Dict[str, Any]] = {}


def generate_mock_token(user_data: Dict[str, Any], provider: str) -> str:
    """Generate a mock JWT token for testing."""
    now = datetime.utcnow()
    payload = {
        "iss": f"https://mock-{provider}.oauth.example.com",
        "sub": user_data["sub"],
        "aud": "mock-client-id",
        "exp": now + timedelta(hours=1),
        "iat": now,
        "email": user_data.get("email"),
        "name": user_data.get("name"),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@app.get("/auth/{provider}/authorize")
def authorize(provider: str, redirect_uri: str, state: str, response_type: str = "code"):
    """
    Mock OAuth authorization endpoint.
    Returns a redirect with an authorization code.
    """
    if provider not in ["google", "microsoft", "apple"]:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    # Generate mock authorization code
    code = f"mock_{provider}_code_{int(time.time())}"
    AUTHORIZATION_CODES[code] = {
        "provider": provider,
        "state": state,
        "redirect_uri": redirect_uri,
        "expires_at": time.time() + 600,  # 10 min expiry
    }

    # Redirect back with code and state
    redirect_url = f"{redirect_uri}?code={code}&state={state}"
    return RedirectResponse(url=redirect_url)


@app.post("/token")
def token(request: TokenRequest) -> TokenResponse:
    """
    Mock OAuth token endpoint.
    Exchanges authorization code for access token.
    """
    if request.code not in AUTHORIZATION_CODES:
        raise HTTPException(status_code=400, detail="Invalid authorization code")

    code_data = AUTHORIZATION_CODES[request.code]
    provider = code_data["provider"]

    # Validate state
    if code_data["redirect_uri"] != request.redirect_uri:
        raise HTTPException(status_code=400, detail="Redirect URI mismatch")

    # Clean up used code
    del AUTHORIZATION_CODES[request.code]

    # Get mock user data
    user_data = MOCK_USERS.get(provider, MOCK_USERS["google"])

    # Generate tokens
    access_token = generate_mock_token(user_data, provider)
    refresh_token = f"mock_refresh_{provider}_{int(time.time())}"

    # For Google/Apple, also include id_token
    id_token = None
    if provider in ["google", "apple"]:
        id_token = access_token

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        id_token=id_token,
    )


@app.get("/oauth2/v3/userinfo")
def google_userinfo(request: Request):
    """
    Mock Google userinfo endpoint.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Return mock Google user profile
    return {
        "sub": payload.get("sub", MOCK_USERS["google"]["sub"]),
        "email": payload.get("email", MOCK_USERS["google"]["email"]),
        "name": payload.get("name", MOCK_USERS["google"]["name"]),
        "given_name": MOCK_USERS["google"].get("given_name", "Mock"),
        "family_name": MOCK_USERS["google"].get("family_name", "User"),
        "picture": MOCK_USERS["google"].get("picture"),
    }


@app.get("/v1.0/me")
def microsoft_userinfo(request: Request):
    """
    Mock Microsoft userinfo endpoint.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Return mock Microsoft user profile
    return {
        "id": payload.get("sub", MOCK_USERS["microsoft"]["sub"]),
        "displayName": payload.get("name", MOCK_USERS["microsoft"]["name"]),
        "mail": payload.get("email", MOCK_USERS["microsoft"]["email"]),
    }


@app.get("/.well-known/openid-configuration")
def openid_config(provider: str = "google"):
    """
    Mock OpenID configuration endpoint.
    """
    base_url = f"https://mock-{provider}.oauth.example.com"
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/auth/{provider}/authorize",
        "token_endpoint": f"{base_url}/token",
        "userinfo_endpoint": f"{base_url}/oauth2/v3/userinfo" if provider == "google" else f"{base_url}/v1.0/me",
        "jwks_uri": f"{base_url}/.well-known/jwks.json",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
    }


@app.get("/")
def root():
    return {
        "service": "Mock OAuth Provider",
        "version": "1.0.0",
        "providers": ["google", "microsoft", "apple"],
        "endpoints": {
            "authorize": "/auth/{provider}/authorize",
            "token": "/token",
            "userinfo_google": "/oauth2/v3/userinfo",
            "userinfo_microsoft": "/v1.0/me",
            "openid_config": "/.well-known/openid-configuration",
        },
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
