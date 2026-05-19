import pytest

from app.api.v1.auth.oauth import get_oauth_url
from app.core.config import settings
from app.services.auth.oauth import OAuthService


class _FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"access_token": "mock-access-token"}


class _FakeOAuthClient:
    pass


class _FakeHttpClient:
    calls = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def post(self, url, data):
        self.calls.append({"url": url, "data": data})
        return _FakeResponse()


@pytest.mark.asyncio
async def test_mock_oauth_url_uses_public_authorize_url(monkeypatch):
    monkeypatch.setattr(settings, "mock_oauth_enabled", True)
    monkeypatch.setattr(settings, "mock_oauth_public_base_url", "http://localhost:9999")

    response = await get_oauth_url("google", "http://localhost:5173/login")

    auth_url = response["data"]["auth_url"]
    assert auth_url.startswith("http://localhost:9999/auth/google/authorize?")
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A5173%2Flogin" in auth_url


@pytest.mark.asyncio
async def test_oauth_token_exchange_sends_client_credentials(monkeypatch):
    service = OAuthService()
    _FakeHttpClient.calls = []
    monkeypatch.setattr(service, "get_client", lambda provider: _FakeOAuthClient())
    monkeypatch.setattr("app.services.auth.oauth.httpx.AsyncClient", _FakeHttpClient)
    monkeypatch.setattr(settings, "mock_oauth_enabled", True)
    monkeypatch.setattr(settings, "mock_oauth_base_url", "http://mock-oauth:9999")
    monkeypatch.setattr(settings, "google_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "client-secret")

    token = await service.exchange_code_for_token(
        "google",
        "mock_google_code",
        "http://localhost:5173/login",
    )

    assert token == {"access_token": "mock-access-token"}
    assert _FakeHttpClient.calls == [
        {
            "url": "http://mock-oauth:9999/token",
            "data": {
                "code": "mock_google_code",
                "redirect_uri": "http://localhost:5173/login",
                "grant_type": "authorization_code",
                "client_id": "client-id",
                "client_secret": "client-secret",
            },
        }
    ]


def test_normalize_mock_google_user_info_accepts_sub_identifier():
    service = OAuthService()

    normalized = service.normalize_user_info(
        "google",
        {"sub": "google-sub", "email": "mock.google@example.com", "name": "Mock Google"},
    )

    assert normalized["provider_user_id"] == "google-sub"
    assert normalized["email"] == "mock.google@example.com"
    assert normalized["name"] == "Mock Google"


def test_normalize_mock_microsoft_user_info_accepts_mail_field():
    service = OAuthService()

    normalized = service.normalize_user_info(
        "microsoft",
        {
            "id": "microsoft-id",
            "mail": "mock.microsoft@example.com",
            "displayName": "Mock Microsoft",
        },
    )

    assert normalized["provider_user_id"] == "microsoft-id"
    assert normalized["email"] == "mock.microsoft@example.com"
    assert normalized["name"] == "Mock Microsoft"
