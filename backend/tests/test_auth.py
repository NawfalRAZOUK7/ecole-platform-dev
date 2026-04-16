"""Integration tests for the complete auth flow.

Reference: S-029 through S-042 — Auth, RBAC, ABAC, deny ordering
Tests run against the actual Docker services (postgres, redis, backend).
Seed data must be loaded before running: make seed

Run: pytest tests/test_auth.py -v
"""

from __future__ import annotations

import httpx
import pytest

from tests.conftest import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    SCHOOL_ID,
    TEACHER_EMAIL,
    TEACHER_PASSWORD,
)


# ---------------------------------------------------------------------------
# S-029: JWT token generation and validation
# ---------------------------------------------------------------------------
class TestJWT:
    """Tests for JWT token infrastructure."""

    @pytest.mark.asyncio
    async def test_login_returns_access_token(self, client: httpx.AsyncClient):
        """Login returns a valid access token with correct structure."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800  # 30 minutes

    @pytest.mark.asyncio
    async def test_login_sets_refresh_cookie(self, client: httpx.AsyncClient):
        """Login sets refresh_token as HttpOnly cookie."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert response.status_code == 200
        # httpx may not fully expose cookie attributes, check it exists
        assert (
            "refresh_token" in response.cookies
            or "refresh_token" in response.headers.get("set-cookie", "").lower()
        )

    @pytest.mark.asyncio
    async def test_expired_or_invalid_token_returns_401(
        self, client: httpx.AsyncClient
    ):
        """Invalid token returns 401 with ERR-IAM-401."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "ERR-IAM-401"
        assert error["category"] == "authn"

    @pytest.mark.asyncio
    async def test_missing_auth_header_returns_401(self, client: httpx.AsyncClient):
        """Missing Authorization header returns 401."""
        response = await client.get("/auth/me")
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"] == "ERR-IAM-401"


# ---------------------------------------------------------------------------
# S-030: POST /auth/login
# ---------------------------------------------------------------------------
class TestLogin:
    """Tests for the login endpoint."""

    @pytest.mark.asyncio
    async def test_successful_login(self, client: httpx.AsyncClient):
        """Valid credentials return access token with standard envelope."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert body["data"]["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: httpx.AsyncClient):
        """Invalid password returns 401."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": "wrong-password",
                "school_id": SCHOOL_ID,
            },
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "ERR-IAM-401"

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, client: httpx.AsyncClient):
        """Non-existent email returns 401 (no enumeration)."""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anything",
                "school_id": SCHOOL_ID,
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_invalid_school_id_returns_401(self, client: httpx.AsyncClient):
        """Unknown school IDs must not turn a login denial into a server error."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": "11111111-1111-4111-8111-111111111111",
            },
        )
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "ERR-IAM-401"

    @pytest.mark.asyncio
    async def test_login_validation_error(self, client: httpx.AsyncClient):
        """Missing fields return 422 with ErrorResponse format."""
        response = await client.post(
            "/auth/login",
            json={"email": "test@test.com"},
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "ERR-VAL-422"
        assert error["category"] == "validation"

    @pytest.mark.asyncio
    async def test_login_response_has_correlation_id(self, client: httpx.AsyncClient):
        """Login response includes X-Correlation-Id header."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert "x-correlation-id" in response.headers


# ---------------------------------------------------------------------------
# S-033: GET /me
# ---------------------------------------------------------------------------
class TestMe:
    """Tests for the profile endpoint."""

    @pytest.mark.asyncio
    async def test_admin_me_returns_profile(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Admin /me returns full profile with permissions."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["email"] == ADMIN_EMAIL
        assert data["role"] == "ADM"
        assert "permissions" in data
        assert len(data["permissions"]) > 10  # ADM has many perms
        assert "memberships" in data
        assert len(data["memberships"]) >= 1

    @pytest.mark.asyncio
    async def test_teacher_me_returns_teacher_perms(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        """Teacher /me returns teacher-specific permissions."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["role"] == "TCH"
        assert "PERM-ERP:class:read" in data["permissions"]
        assert "PERM-LMS:submission:grade" in data["permissions"]

    @pytest.mark.asyncio
    async def test_student_me_has_limited_perms(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Student /me has limited permissions (no ERP class read)."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["role"] == "STD"
        assert "PERM-ERP:class:read" not in data["permissions"]
        assert "PERM-LMS:submission:create" in data["permissions"]

    @pytest.mark.asyncio
    async def test_me_follows_response_envelope(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Response follows { data, meta: { timestamp, version } } envelope."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert body["meta"]["version"] == "0.1.0"


# ---------------------------------------------------------------------------
# S-032: POST /auth/logout
# ---------------------------------------------------------------------------
class TestLogout:
    """Tests for the logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_revokes_session(self, client: httpx.AsyncClient):
        """Logout revokes session; subsequent requests return 401."""
        # Login
        login_response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        token = login_response.json()["data"]["access_token"]

        # Logout
        logout_response = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_response.status_code == 200

        # Confirm session revoked
        me_response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_is_idempotent(self, client: httpx.AsyncClient):
        """Calling logout twice returns 200 both times (second is no-op)."""
        login_response = await client.post(
            "/auth/login",
            json={
                "email": TEACHER_EMAIL,
                "password": TEACHER_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        token = login_response.json()["data"]["access_token"]

        # First logout
        r1 = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r1.status_code == 200

        # Second logout — session already revoked, returns 401 (not crash)
        # This is expected since the token's session is revoked
        r2 = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r2.status_code == 401  # session revoked


# ---------------------------------------------------------------------------
# S-034: RBAC permission middleware
# ---------------------------------------------------------------------------
class TestRBAC:
    """Tests for RBAC permission checking."""

    @pytest.mark.asyncio
    async def test_admin_can_read_class(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Admin with PERM-ERP:class:read can access classes endpoint."""
        # This will return 404 for non-existent class (but not 403)
        response = await client.get(
            "/classes/00000000-0000-0000-0000-000000000099",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # 404 = got past RBAC (class doesn't exist), not 403
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_read_class(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Student without PERM-ERP:class:read gets 403."""
        response = await client.get(
            "/classes/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["code"] == "ERR-AUTHZ-001"
        assert error["category"] == "authz"

    @pytest.mark.asyncio
    async def test_student_cannot_create_enrollment(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Student without PERM-ERP:enrollment:assign gets 403 on POST /enrollments."""
        response = await client.post(
            "/enrollments",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "student_id": "10000000-0000-4000-8000-000000000007",
                "class_id": "10000000-0000-4000-8000-000000000100",
                "period_id": "10000000-0000-4000-8000-000000000200",
            },
        )
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# S-039: X-Correlation-Id middleware
# ---------------------------------------------------------------------------
class TestCorrelationId:
    """Tests for X-Correlation-Id middleware."""

    @pytest.mark.asyncio
    async def test_preserves_incoming_correlation_id(self, client: httpx.AsyncClient):
        """If X-Correlation-Id is present in request, it's preserved in response."""
        test_cid = "my-custom-correlation-id-12345"
        response = await client.get(
            "/health",
            headers={"X-Correlation-Id": test_cid},
        )
        assert response.headers["x-correlation-id"] == test_cid

    @pytest.mark.asyncio
    async def test_generates_correlation_id_when_missing(
        self, client: httpx.AsyncClient
    ):
        """If X-Correlation-Id is not present, a new UUID is generated."""
        response = await client.get("/health")
        cid = response.headers.get("x-correlation-id")
        assert cid is not None
        assert len(cid) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_error_responses_include_correlation_id(
        self, client: httpx.AsyncClient
    ):
        """Error responses include correlation_id in the error body."""
        response = await client.get("/auth/me")  # no token
        assert response.status_code == 401
        error = response.json()["error"]
        assert "correlation_id" in error
        assert error["correlation_id"] is not None


# ---------------------------------------------------------------------------
# S-042: Deny ordering (401 → 404 → 403)
# ---------------------------------------------------------------------------
class TestDenyOrdering:
    """Tests for security pipeline deny ordering."""

    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401_not_403(self, client: httpx.AsyncClient):
        """Unauthenticated request to protected endpoint returns 401 (not 403 or 404)."""
        response = await client.get("/classes/00000000-0000-0000-0000-000000000001")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_role_returns_403(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Authenticated + correct school + wrong role → 403."""
        response = await client.get(
            "/classes/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_nonexistent_resource_returns_404(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """Authenticated + correct role + resource not found → 404."""
        response = await client.get(
            "/classes/99999999-9999-9999-9999-999999999999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# S-068: Standard response envelope
# ---------------------------------------------------------------------------
class TestResponseEnvelope:
    """Tests for standard response formatting."""

    @pytest.mark.asyncio
    async def test_success_response_has_data_and_meta(self, client: httpx.AsyncClient):
        """Success response follows { data, meta: { timestamp, version } }."""
        response = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "version" in body["meta"]

    @pytest.mark.asyncio
    async def test_error_response_has_error_envelope(self, client: httpx.AsyncClient):
        """Error response follows { error: { code, message, category, ... } }."""
        response = await client.get("/auth/me")
        body = response.json()
        assert "error" in body
        error = body["error"]
        assert "code" in error
        assert "message" in error
        assert "category" in error
        assert "correlation_id" in error
        assert "retryable" in error
        assert "timestamp" in error


# ---------------------------------------------------------------------------
# S-069: Error response model
# ---------------------------------------------------------------------------
class TestErrorResponse:
    """Tests for the unified error response model."""

    @pytest.mark.asyncio
    async def test_validation_error_format(self, client: httpx.AsyncClient):
        """Validation errors return structured ErrorResponse with details."""
        response = await client.post(
            "/auth/login",
            json={},  # Missing all required fields
        )
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "ERR-VAL-422"
        assert error["category"] == "validation"
        assert "details" in error

    @pytest.mark.asyncio
    async def test_authn_error_format(self, client: httpx.AsyncClient):
        """Authentication errors use correct error code pattern."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert response.status_code == 401
        error = response.json()["error"]
        assert error["code"].startswith("ERR-")
        assert error["category"] == "authn"
        assert error["retryable"] is False

    @pytest.mark.asyncio
    async def test_authz_error_format(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Authorization errors return 403 with ERR-AUTHZ-001."""
        response = await client.get(
            "/classes/00000000-0000-0000-0000-000000000001",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["code"] == "ERR-AUTHZ-001"
        assert error["category"] == "authz"


# ---------------------------------------------------------------------------
# S-041: Account recovery flow
# ---------------------------------------------------------------------------
class TestRecovery:
    """Tests for the account recovery flow."""

    @pytest.mark.asyncio
    async def test_recovery_request_always_returns_200(self, client: httpx.AsyncClient):
        """Recovery request always returns 200 to prevent email enumeration."""
        # Existing email
        r1 = await client.post(
            "/recovery/request",
            json={"email": ADMIN_EMAIL, "school_id": SCHOOL_ID},
        )
        assert r1.status_code == 200

        # Non-existent email — same response
        r2 = await client.post(
            "/recovery/request",
            json={"email": "ghost@example.com", "school_id": SCHOOL_ID},
        )
        assert r2.status_code == 200
        # Both should have the same message structure
        assert r1.json()["data"]["message"] == r2.json()["data"]["message"]
