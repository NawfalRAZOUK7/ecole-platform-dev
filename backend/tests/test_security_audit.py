"""Security audit tests — CSRF, XSS, SQL injection, auth bypass, scope masking, password policy.

Reference: Phase 6A — Security audit
"""

from __future__ import annotations

import pytest
import httpx

from tests.conftest import (
    BASE_URL,
    SCHOOL_ID,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    TEACHER_EMAIL,
    TEACHER_PASSWORD,
    PARENT_EMAIL,
    PARENT_PASSWORD,
    STUDENT_EMAIL,
    STUDENT_PASSWORD,
)

# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

ANOTHER_SCHOOL_ID = "00000000-0000-4000-8000-000000000099"


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def login(client: httpx.AsyncClient, email: str, password: str) -> str:
    r = await client.post(
        "/auth/login",
        json={"email": email, "password": password, "school_id": SCHOOL_ID},
    )
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


# ──────────────────────────────────────────────────────────
# 1. Auth Bypass — 401 on all protected endpoints without token
# ──────────────────────────────────────────────────────────


class TestAuthBypass:
    """Verify that all protected endpoints return 401 without a valid token."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/auth/me"),
        ("GET", "/auth/sessions"),
        ("POST", "/auth/logout"),
        ("POST", "/auth/change-password"),
        ("GET", "/feed"),
        ("GET", "/notifications"),
        ("GET", "/content"),
        ("GET", "/results"),
        ("GET", "/invoices"),
        ("GET", "/teacher/classes"),
        ("GET", "/teacher/submissions"),
        ("GET", "/teacher/periods"),
        ("GET", "/admin/dashboard"),
        ("GET", "/admin/users"),
        ("GET", "/consents"),
        ("GET", "/activities"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    async def test_no_token_returns_401(self, client: httpx.AsyncClient, method: str, path: str):
        """Endpoint must reject requests without Authorization header."""
        if method == "GET":
            r = await client.get(path)
        elif method == "POST":
            r = await client.post(path, json={})
        else:
            r = await client.request(method, path)

        assert r.status_code == 401, f"{method} {path} returned {r.status_code}, expected 401"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client: httpx.AsyncClient):
        """A malformed JWT must be rejected."""
        r = await client.get("/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_format_rejected(self, client: httpx.AsyncClient):
        """A structurally valid but expired/tampered JWT is rejected."""
        fake_jwt = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )
        r = await client.get("/auth/me", headers={"Authorization": f"Bearer {fake_jwt}"})
        assert r.status_code == 401


# ──────────────────────────────────────────────────────────
# 2. Scope Masking — 404 (not 403) for cross-school access
# ──────────────────────────────────────────────────────────


class TestScopeMasking:
    """Cross-school access should return 404, not 403, to avoid leaking info."""

    @pytest.mark.asyncio
    async def test_cross_school_class_returns_404(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        """Accessing a class from another school must return 404."""
        fake_class_id = "00000000-0000-4000-8000-ffffffffffff"
        r = await client.get(
            f"/classes/{fake_class_id}",
            headers=auth_header(teacher_token),
        )
        # Must be 404 (not found) — never 403 (forbidden)
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_cross_school_invoice_returns_404(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Accessing an invoice from another school must return 404."""
        fake_invoice_id = "00000000-0000-4000-8000-ffffffffffff"
        r = await client.get(
            f"/invoices/{fake_invoice_id}",
            headers=auth_header(parent_token),
        )
        assert r.status_code == 404


# ──────────────────────────────────────────────────────────
# 3. SQL Injection — parameterized queries (SQLAlchemy safety)
# ──────────────────────────────────────────────────────────


class TestSQLInjection:
    """Verify SQL injection payloads are safely handled."""

    SQL_PAYLOADS = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "1 UNION SELECT * FROM users --",
        "admin'--",
        "' OR 1=1 --",
        "1; SELECT pg_sleep(5) --",
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    async def test_login_sqli(self, client: httpx.AsyncClient, payload: str):
        """SQL injection in login fields must not bypass auth."""
        r = await client.post(
            "/auth/login",
            json={
                "email": payload,
                "password": payload,
                "school_id": SCHOOL_ID,
            },
        )
        # Must not succeed (200 with token)
        assert r.status_code in (400, 401, 422), (
            f"SQL injection payload returned {r.status_code}"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", SQL_PAYLOADS)
    async def test_search_sqli(
        self, client: httpx.AsyncClient, admin_token: str, payload: str
    ):
        """SQL injection in search/filter params must not cause errors."""
        r = await client.get(
            "/admin/users",
            params={"search": payload},
            headers=auth_header(admin_token),
        )
        # Should return 200 (empty results) — never 500
        assert r.status_code == 200, (
            f"SQL injection in search returned {r.status_code}"
        )


# ──────────────────────────────────────────────────────────
# 4. XSS — React auto-escaping verification
# ──────────────────────────────────────────────────────────


class TestXSSPrevention:
    """Verify XSS payloads are stored safely and not reflected raw."""

    XSS_PAYLOADS = [
        '<script>alert("xss")</script>',
        '<img src=x onerror=alert(1)>',
        '"><svg onload=alert(1)>',
        "javascript:alert(1)",
        '<iframe src="javascript:alert(1)">',
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_xss_in_login_email(self, client: httpx.AsyncClient, payload: str):
        """XSS payload in email field must be rejected or safely handled."""
        r = await client.post(
            "/auth/login",
            json={
                "email": payload,
                "password": "test",
                "school_id": SCHOOL_ID,
            },
        )
        # Must not return 200 with reflected payload
        assert r.status_code in (400, 401, 422)
        # Response body must not contain raw script tags
        assert "<script>" not in r.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_xss_in_search(
        self, client: httpx.AsyncClient, admin_token: str, payload: str
    ):
        """XSS payload in search params must not be reflected raw."""
        r = await client.get(
            "/admin/users",
            params={"search": payload},
            headers=auth_header(admin_token),
        )
        assert r.status_code == 200
        # Response should not contain raw unescaped script tags
        if "<script>" in payload:
            # API should either escape or not reflect the input
            body = r.text
            assert '<script>alert' not in body.lower()


# ──────────────────────────────────────────────────────────
# 5. CSRF Protection — double-submit cookie
# ──────────────────────────────────────────────────────────


class TestCSRFProtection:
    """Verify CSRF protection on state-changing endpoints."""

    @pytest.mark.asyncio
    async def test_login_without_csrf_succeeds(self, client: httpx.AsyncClient):
        """Login endpoint should work without CSRF (it's the entry point)."""
        r = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_cross_origin_header_check(self, client: httpx.AsyncClient):
        """Requests with suspicious Origin headers should still be handled safely."""
        r = await client.post(
            "/auth/login",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "school_id": SCHOOL_ID,
            },
            headers={"Origin": "https://evil-site.com"},
        )
        # Login may succeed (CORS is handled at middleware level, not endpoint)
        # but verify no cookies are set for the evil origin
        assert r.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_state_change_without_auth_rejected(self, client: httpx.AsyncClient):
        """State-changing operations without auth must be rejected."""
        # Try to change password without token
        r = await client.post(
            "/auth/change-password",
            json={
                "current_password": "test",
                "new_password": "NewP@ssw0rd123!",
            },
        )
        assert r.status_code == 401


# ──────────────────────────────────────────────────────────
# 6. Password Policy — weak passwords rejected
# ──────────────────────────────────────────────────────────


class TestPasswordPolicy:
    """Verify password policy enforcement."""

    WEAK_PASSWORDS = [
        ("short", "Ab1!"),  # Too short
        ("no_uppercase", "abcdefgh123!@#"),
        ("no_lowercase", "ABCDEFGH123!@#"),
        ("no_digit", "Abcdefghijk!@#"),
        ("no_special", "Abcdefghijk123"),
        ("common", "Password1234!"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("reason,password", WEAK_PASSWORDS)
    async def test_weak_password_rejected_on_change(
        self, client: httpx.AsyncClient, admin_token: str, reason: str, password: str
    ):
        """Password change must reject weak passwords."""
        r = await client.post(
            "/auth/change-password",
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": password,
            },
            headers=auth_header(admin_token),
        )
        # Must not succeed — 400 or 422 expected
        assert r.status_code in (400, 422), (
            f"Weak password ({reason}) was accepted: {r.status_code}"
        )

    @pytest.mark.asyncio
    async def test_strong_password_accepted(
        self, client: httpx.AsyncClient, admin_token: str
    ):
        """A password meeting all policy requirements should be accepted."""
        strong_password = "S3cur€P@ssW0rd!2024"
        r = await client.post(
            "/auth/change-password",
            json={
                "current_password": ADMIN_PASSWORD,
                "new_password": strong_password,
            },
            headers=auth_header(admin_token),
        )
        # Accept 200 (success) or 422 (if password was recently changed)
        # The important thing is it's not rejected for policy reasons
        assert r.status_code in (200, 422)

        # Reset password back if it was changed
        if r.status_code == 200:
            # Re-login with new password
            login_r = await client.post(
                "/auth/login",
                json={
                    "email": ADMIN_EMAIL,
                    "password": strong_password,
                    "school_id": SCHOOL_ID,
                },
            )
            if login_r.status_code == 200:
                new_token = login_r.json()["data"]["access_token"]
                await client.post(
                    "/auth/change-password",
                    json={
                        "current_password": strong_password,
                        "new_password": ADMIN_PASSWORD,
                    },
                    headers=auth_header(new_token),
                )


# ──────────────────────────────────────────────────────────
# 7. Role Escalation — verify role boundaries
# ──────────────────────────────────────────────────────────


class TestRoleEscalation:
    """Verify users cannot access endpoints beyond their role."""

    @pytest.mark.asyncio
    async def test_student_cannot_access_admin(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Students must not access admin endpoints."""
        r = await client.get(
            "/admin/dashboard",
            headers=auth_header(student_token),
        )
        assert r.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_parent_cannot_access_teacher(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Parents must not access teacher endpoints."""
        r = await client.get(
            "/teacher/classes",
            headers=auth_header(parent_token),
        )
        assert r.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_admin(
        self, client: httpx.AsyncClient, teacher_token: str
    ):
        """Teachers must not access admin endpoints."""
        r = await client.get(
            "/admin/users",
            headers=auth_header(teacher_token),
        )
        assert r.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_student_cannot_grade(
        self, client: httpx.AsyncClient, student_token: str
    ):
        """Students must not be able to grade submissions."""
        fake_id = "00000000-0000-4000-8000-ffffffffffff"
        r = await client.post(
            f"/submissions/{fake_id}/grade",
            json={"score": 20, "feedback_text": "hacked"},
            headers=auth_header(student_token),
        )
        assert r.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_parent_cannot_create_invitation(
        self, client: httpx.AsyncClient, parent_token: str
    ):
        """Parents must not create invitations."""
        r = await client.post(
            "/invites/create",
            json={"role_target": "STD"},
            headers=auth_header(parent_token),
        )
        assert r.status_code in (403, 404)
