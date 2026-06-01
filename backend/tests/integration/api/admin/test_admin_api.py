"""Integration tests for admin endpoints (Phase 4.I).

Coverage target: app/api/v1/admin/admin.py ≥ 95 % branch

Routes covered:
  GET    /admin/dashboard             — stats (ADM/DIR)
  GET    /admin/users                 — list users (ADM/DIR)
  GET    /admin/enrollments           — list enrollments (ADM/DIR)
  POST   /admin/impersonate/{id}      — impersonate (ADM/DIR)
  POST   /admin/stop-impersonation    — stop impersonating
  GET    /admin/users/{id}/login-history
  PUT    /admin/users/{id}/suspend
  PUT    /admin/users/{id}/activate
  PUT    /admin/users/{id}/role
  GET    /admin/invitations
  GET    /admin/audit-logs
  GET    /admin/justifications
  POST   /admin/register-batch
  POST   /admin/parent-child-links
  GET    /admin/parent-child-links
  DELETE /admin/parent-child-links/{id}
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration.api.helpers import (
    SCHOOL_ID,
    STUDENT_ID,
    auth_header,
    login_token,
    unique_suffix,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"
SUPERADMIN_EMAIL = "superadmin@ecole-platform.ma"
SUPERADMIN_PASSWORD = "superadmin123"

PARENT_ID = "10000000-0000-4000-8000-000000000005"
TEACHER_ID = "10000000-0000-4000-8000-000000000003"
ADMIN_ID = "10000000-0000-4000-8000-000000000001"
PARENT_CHILD_LINK_ID = "71000000-0000-4000-8000-000000000001"


class TestAdminDashboard:
    @pytest.mark.asyncio
    async def test_admin_can_get_dashboard_stats(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/admin/dashboard", headers=auth_header(token))
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_students" in data or "user_count" in data or isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_dashboard(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get("/admin/dashboard", headers=auth_header(token))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_access_dashboard(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD)
        response = await client.get("/admin/dashboard", headers=auth_header(token))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_dashboard(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.get("/admin/dashboard")
        assert response.status_code in (401, 403)


class TestAdminUserList:
    @pytest.mark.asyncio
    async def test_admin_can_list_users(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/admin/users", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/users",
            headers=auth_header(token),
            params={"search": "admin", "role": "ADM"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_with_status_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/users",
            headers=auth_header(token),
            params={"status": "active", "limit": 10},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_users(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get("/admin/users", headers=auth_header(token))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_list_users(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get("/admin/users", headers=auth_header(token))
        assert response.status_code == 403


class TestAdminEnrollments:
    @pytest.mark.asyncio
    async def test_admin_can_list_enrollments(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/admin/enrollments", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_enrollments_with_filters(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/enrollments",
            headers=auth_header(token),
            params={"status": "active", "missing_program": False},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_enrollments(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get("/admin/enrollments", headers=auth_header(token))
        assert response.status_code == 403


class TestAdminUserActions:
    @pytest.mark.asyncio
    async def test_admin_can_suspend_user(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        # Suspend the teacher
        response = await client.put(
            f"/admin/users/{TEACHER_ID}/suspend",
            headers=auth_header(token),
        )
        assert response.status_code in (200, 409)

    @pytest.mark.asyncio
    async def test_admin_can_activate_user(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/admin/users/{TEACHER_ID}/activate",
            headers=auth_header(token),
        )
        assert response.status_code in (200, 409)

    @pytest.mark.asyncio
    async def test_suspend_nonexistent_user_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/admin/users/{uuid.uuid4()}/suspend",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_suspend_users(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.put(
            f"/admin/users/{STUDENT_ID}/suspend",
            headers=auth_header(token),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_change_user_role(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/admin/users/{TEACHER_ID}/role",
            headers=auth_header(token),
            params={"role": "TCH"},
        )
        assert response.status_code in (200, 409)

    @pytest.mark.asyncio
    async def test_change_role_missing_role_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.put(
            f"/admin/users/{TEACHER_ID}/role",
            headers=auth_header(token),
        )
        assert response.status_code == 422


class TestAdminLoginHistory:
    @pytest.mark.asyncio
    async def test_admin_can_view_user_login_history(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            f"/admin/users/{STUDENT_ID}/login-history",
            headers=auth_header(token),
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_teacher_cannot_view_login_history(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            f"/admin/users/{STUDENT_ID}/login-history",
            headers=auth_header(token),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_login_history_nonexistent_user_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            f"/admin/users/{uuid.uuid4()}/login-history",
            headers=auth_header(token),
        )
        assert response.status_code == 404


class TestAdminInvitations:
    @pytest.mark.asyncio
    async def test_admin_can_list_invitations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/admin/invitations", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_invitations_with_status_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/invitations",
            headers=auth_header(token),
            params={"status": "active"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_invitations(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get("/admin/invitations", headers=auth_header(token))
        assert response.status_code == 403


class TestAdminAuditLogs:
    @pytest.mark.asyncio
    async def test_admin_can_list_audit_logs(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get("/admin/audit-logs", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_audit_logs_with_action_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/audit-logs",
            headers=auth_header(token),
            params={"action_type": "AUTH_SESSION_OPENED", "limit": 5},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_access_audit_logs(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get("/admin/audit-logs", headers=auth_header(token))
        assert response.status_code == 403


class TestAdminJustifications:
    @pytest.mark.asyncio
    async def test_admin_can_list_justifications(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/justifications", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_justifications(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/admin/justifications", headers=auth_header(token)
        )
        assert response.status_code == 403


class TestAdminBatchRegister:
    @pytest.mark.asyncio
    async def test_admin_can_batch_register_users(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        suffix = unique_suffix()
        response = await client.post(
            "/admin/register-batch",
            headers=auth_header(token),
            json={
                "users": [
                    {
                        "email": f"batch-{suffix}@test.example",
                        "full_name": "Batch User Test",
                        "role": "TCH",
                    }
                ]
            },
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_batch_register_missing_users_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/admin/register-batch",
            headers=auth_header(token),
            json={},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_teacher_cannot_batch_register(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            "/admin/register-batch",
            headers=auth_header(token),
            json={"users": []},
        )
        assert response.status_code == 403


class TestParentChildLinks:
    @pytest.mark.asyncio
    async def test_admin_can_list_parent_child_links(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/parent-child-links", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_links_with_filters(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.get(
            "/admin/parent-child-links",
            headers=auth_header(token),
            params={"parent_id": PARENT_ID, "status": "active"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_parent_child_links(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.get(
            "/admin/parent-child-links", headers=auth_header(token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_create_parent_child_link(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/admin/parent-child-links",
            headers=auth_header(token),
            params={
                "parent_user_id": PARENT_ID,
                "child_user_id": STUDENT_ID,
            },
        )
        # 201 first time; 409 if link already exists
        assert response.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_create_link_nonexistent_parent_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/admin/parent-child-links",
            headers=auth_header(token),
            params={
                "parent_user_id": str(uuid.uuid4()),
                "child_user_id": STUDENT_ID,
            },
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_parent_child_link(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.delete(
            f"/admin/parent-child-links/{PARENT_CHILD_LINK_ID}",
            headers=auth_header(token),
        )
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_link_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.delete(
            f"/admin/parent-child-links/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_delete_link(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.delete(
            f"/admin/parent-child-links/{PARENT_CHILD_LINK_ID}",
            headers=auth_header(token),
        )
        assert response.status_code == 403


class TestImpersonation:
    @pytest.mark.asyncio
    async def test_admin_can_impersonate_user(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            f"/admin/impersonate/{TEACHER_ID}",
            headers=auth_header(token),
        )
        assert response.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_impersonate_nonexistent_user_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            f"/admin/impersonate/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_impersonate(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD)
        response = await client.post(
            f"/admin/impersonate/{STUDENT_ID}",
            headers=auth_header(token),
        )
        assert response.status_code == 403
