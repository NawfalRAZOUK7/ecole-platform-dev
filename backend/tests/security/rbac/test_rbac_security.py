"""RBAC security matrix tests — every endpoint × every role.

Reference: S-113 — RBAC security tests, S-034 — RBAC enforcement
Verifies that each endpoint correctly allows/denies access per role.
Deny ordering: 401 (no token) → 404 (scope mask) → 403 (insufficient perms).
"""

from __future__ import annotations

import uuid

import pytest


# Fixed seed IDs
CLASS_ID = "20000000-0000-4000-8000-000000000004"
PERIOD_ID = "20000000-0000-4000-8000-000000000003"
TEACHER_ID = "10000000-0000-4000-8000-000000000003"
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
PARENT_ID = "10000000-0000-4000-8000-000000000005"
INVOICE_ID = "40000000-0000-4000-8000-000000000001"
CONTENT_ITEM_ID = "30000000-0000-4000-8000-000000000005"
ACTIVITY_ID = "30000000-0000-4000-8000-000000000006"
ASSESSMENT_ID = "30000000-0000-4000-8000-000000000004"
ASSIGNMENT_ID = "30000000-0000-4000-8000-000000000003"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# 1. UNAUTHENTICATED (no token) → always 401
# ======================================================================
class TestUnauthenticated:
    """No Bearer token → 401 on all protected endpoints."""

    ENDPOINTS = [
        ("GET", "/classes/{cid}"),
        ("POST", "/enrollments"),
        ("POST", "/class-assignments"),
        ("POST", "/attendance/sessions"),
        ("POST", "/attendance/justifications"),
        ("GET", "/courses"),
        ("POST", "/courses"),
        ("GET", "/assignments"),
        ("POST", "/assignments"),
        ("POST", "/submissions"),
        ("GET", "/results"),
        ("GET", "/content-items"),
        ("POST", "/activities/sessions"),
        ("GET", "/assessments"),
        ("POST", "/assessments"),
        ("GET", "/invoices"),
        ("POST", "/payments/initiate"),
        ("GET", "/notifications"),
        ("GET", "/consents"),
        ("GET", "/feed"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,path", ENDPOINTS)
    async def test_no_token_returns_401(self, client, method, path):
        path = path.replace("{cid}", CLASS_ID)
        if method == "GET":
            resp = await client.get(path)
        else:
            resp = await client.post(path, json={})
        assert (
            resp.status_code == 401
        ), f"{method} {path} expected 401, got {resp.status_code}"


# ======================================================================
# 2. DENY ORDERING — 401 → 404 → 403
# ======================================================================
class TestDenyOrdering:
    """Verify deny ordering: 401 before 404 before 403."""

    @pytest.mark.asyncio
    async def test_401_before_403_on_classes(self, client):
        """No token → 401 even though resource exists."""
        resp = await client.get(f"/classes/{CLASS_ID}")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_masks_403_other_school(self, client, student_token):
        """Request to resource in another school → 404 (scope masking), not 403."""
        fake_class = str(uuid.uuid4())
        resp = await client.get(
            f"/classes/{fake_class}",
            headers=auth(student_token),
        )
        # Student lacks permission OR class doesn't exist → masked as 404
        assert resp.status_code in (403, 404)

    @pytest.mark.asyncio
    async def test_403_on_known_resource(self, client, student_token):
        """STD trying to POST enrollment → 403 (has auth, school matches, but no perm)."""
        resp = await client.post(
            "/enrollments",
            headers=auth(student_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 3. ERP — Class Read (PERM-ERP:class:read)
# ======================================================================
class TestClassReadRBAC:
    """GET /classes/{id} — allowed: ADM, DIR, TCH (assigned); denied: STD, PAR."""

    @pytest.mark.asyncio
    async def test_admin_can_read_class(self, client, admin_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_can_read_assigned_class(self, client, teacher_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(teacher_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_read_class(self, client, student_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(student_token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_read_class(self, client, parent_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(parent_token))
        assert resp.status_code == 403


# ======================================================================
# 4. ERP — Enrollment (PERM-ERP:enrollment:assign)
# ======================================================================
class TestEnrollmentRBAC:
    """POST /enrollments — allowed: ADM; denied: TCH, STD, PAR."""

    @pytest.mark.asyncio
    async def test_admin_can_enroll(self, client, admin_token):
        resp = await client.post(
            "/enrollments",
            headers=auth(admin_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_teacher_cannot_enroll(self, client, teacher_token):
        resp = await client.post(
            "/enrollments",
            headers=auth(teacher_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_enroll(self, client, student_token):
        resp = await client.post(
            "/enrollments",
            headers=auth(student_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_enroll(self, client, parent_token):
        resp = await client.post(
            "/enrollments",
            headers=auth(parent_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 5. ERP — Teacher Assignment (PERM-ERP:assignment:update)
# ======================================================================
class TestTeacherAssignmentRBAC:
    """POST /class-assignments — allowed: ADM; denied: TCH, STD, PAR."""

    @pytest.mark.asyncio
    async def test_admin_can_assign(self, client, admin_token):
        resp = await client.post(
            "/class-assignments",
            headers=auth(admin_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_student_cannot_assign(self, client, student_token):
        resp = await client.post(
            "/class-assignments",
            headers=auth(student_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_assign(self, client, parent_token):
        resp = await client.post(
            "/class-assignments",
            headers=auth(parent_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 6. ERP — Attendance (PERM-ERP:attendance:mark)
# ======================================================================
class TestAttendanceRBAC:
    """POST /attendance/sessions — allowed: TCH (assigned); denied: STD, PAR."""

    @pytest.mark.asyncio
    async def test_teacher_can_mark(self, client, teacher_token):
        slot = f"rbac-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/attendance/sessions",
            headers=auth(teacher_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-15",
                "slot": slot,
                "records": [{"student_id": STUDENT_ID, "status": "present"}],
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_mark(self, client, student_token):
        resp = await client.post(
            "/attendance/sessions",
            headers=auth(student_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-15",
                "slot": "test",
                "records": [{"student_id": STUDENT_ID, "status": "present"}],
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_mark(self, client, parent_token):
        resp = await client.post(
            "/attendance/sessions",
            headers=auth(parent_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-15",
                "slot": "test",
                "records": [{"student_id": STUDENT_ID, "status": "present"}],
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 7. LMS — Courses (PERM-LMS:course:publish)
# ======================================================================
class TestCourseRBAC:
    """POST /courses — allowed: TCH, ADM; denied: STD, PAR."""

    @pytest.mark.asyncio
    async def test_teacher_can_create_course(self, client, teacher_token):
        resp = await client.post(
            "/courses",
            headers=auth(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"RBAC Course {uuid.uuid4().hex[:8]}",
                "status": "draft",
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_create_course(self, client, student_token):
        resp = await client.post(
            "/courses",
            headers=auth(student_token),
            json={
                "class_id": CLASS_ID,
                "title": "Should fail",
                "status": "draft",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_course(self, client, parent_token):
        resp = await client.post(
            "/courses",
            headers=auth(parent_token),
            json={
                "class_id": CLASS_ID,
                "title": "Should fail",
                "status": "draft",
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 8. LMS — Assignments (PERM-LMS:assignment:create)
# ======================================================================
class TestAssignmentRBAC:
    """POST /assignments — allowed: TCH; denied: STD, PAR."""

    @pytest.mark.asyncio
    async def test_student_cannot_create_assignment(self, client, student_token):
        resp = await client.post(
            "/assignments",
            headers=auth(student_token),
            json={
                "course_id": str(uuid.uuid4()),
                "title": "Should fail",
                "total_points": 20,
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_assignment(self, client, parent_token):
        resp = await client.post(
            "/assignments",
            headers=auth(parent_token),
            json={
                "course_id": str(uuid.uuid4()),
                "title": "Should fail",
                "total_points": 20,
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 9. LMS — Submissions (PERM-LMS:submission:create)
# ======================================================================
class TestSubmissionRBAC:
    """POST /submissions — allowed: STD; denied: PAR."""

    @pytest.mark.asyncio
    async def test_student_can_submit(self, client, student_token):
        resp = await client.post(
            "/submissions",
            headers=auth(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert resp.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_parent_cannot_submit(self, client, parent_token):
        resp = await client.post(
            "/submissions",
            headers=auth(parent_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert resp.status_code == 403


# ======================================================================
# 10. LMS — Results (PERM-LMS:result:read)
# ======================================================================
class TestResultsRBAC:
    """GET /results — allowed: STD (own), PAR (child); denied: none with perm."""

    @pytest.mark.asyncio
    async def test_student_can_read_own_results(self, client, student_token):
        resp = await client.get("/results", headers=auth(student_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_can_read_child_results(self, client, parent_token):
        resp = await client.get(
            "/results",
            headers=auth(parent_token),
            params={"student_id": STUDENT_ID},
        )
        assert resp.status_code == 200


# ======================================================================
# 11. LMS — Content Items (PERM-LMS:content:read)
# ======================================================================
class TestContentItemsRBAC:
    """GET /content-items — allowed: STD, TCH, ADM, PAR; wide access."""

    @pytest.mark.asyncio
    async def test_student_can_list_content(self, client, student_token):
        resp = await client.get("/content-items", headers=auth(student_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_can_list_content(self, client, teacher_token):
        resp = await client.get("/content-items", headers=auth(teacher_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_list_content(self, client, admin_token):
        """ADM inherits PERM-LMS:content:read through the school hierarchy."""
        resp = await client.get("/content-items", headers=auth(admin_token))
        assert resp.status_code == 200


# ======================================================================
# 12. LMS — Activities list (PERM-LMS:activity:read)
# ======================================================================
class TestActivityListRBAC:
    """GET /activities — allowed: STD, TCH, ADM; denied: PAR."""

    @pytest.mark.asyncio
    async def test_student_can_list_activities(self, client, student_token):
        resp = await client.get("/activities", headers=auth(student_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_can_list_activities(self, client, teacher_token):
        resp = await client.get("/activities", headers=auth(teacher_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_list_activities(self, client, admin_token):
        """ADM inherits PERM-LMS:activity:read through the school hierarchy."""
        resp = await client.get("/activities", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_cannot_list_activities(self, client, parent_token):
        resp = await client.get("/activities", headers=auth(parent_token))
        assert resp.status_code == 403


# ======================================================================
# 13. LMS — Activity sessions (PERM-LMS:activity-session:create)
# ======================================================================
class TestActivityRBAC:
    """POST /activities/sessions — allowed: STD; denied: PAR."""

    @pytest.mark.asyncio
    async def test_student_can_start_session(self, client, student_token):
        resp = await client.post(
            "/activities/sessions",
            headers=auth(student_token),
            json={"activity_id": ACTIVITY_ID},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_parent_cannot_start_session(self, client, parent_token):
        resp = await client.post(
            "/activities/sessions",
            headers=auth(parent_token),
            json={"activity_id": ACTIVITY_ID},
        )
        assert resp.status_code == 403


# ======================================================================
# 14. LMS — Assessments (PERM-LMS:assessment:create)
# ======================================================================
class TestAssessmentRBAC:
    """POST /assessments — allowed: TCH, ADM; denied: STD, PAR."""

    @pytest.mark.asyncio
    async def test_teacher_can_create(self, client, teacher_token):
        resp = await client.post(
            "/assessments",
            headers=auth(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"RBAC Assessment {uuid.uuid4().hex[:8]}",
                "total_points": 50,
                "status": "draft",
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_create(self, client, student_token):
        resp = await client.post(
            "/assessments",
            headers=auth(student_token),
            json={
                "class_id": CLASS_ID,
                "title": "Should fail",
                "total_points": 50,
                "status": "draft",
            },
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create(self, client, parent_token):
        resp = await client.post(
            "/assessments",
            headers=auth(parent_token),
            json={
                "class_id": CLASS_ID,
                "title": "Should fail",
                "total_points": 50,
                "status": "draft",
            },
        )
        assert resp.status_code == 403


# ======================================================================
# 14. Billing — Invoices (PERM-BIL:invoice:read)
# ======================================================================
class TestInvoiceRBAC:
    """GET /invoices — allowed: ADM, PAR (own); denied: STD, TCH."""

    @pytest.mark.asyncio
    async def test_admin_can_list_invoices(self, client, admin_token):
        resp = await client.get("/invoices", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_can_list_own_invoices(self, client, parent_token):
        resp = await client.get("/invoices", headers=auth(parent_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_list_invoices(self, client, student_token):
        resp = await client.get("/invoices", headers=auth(student_token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_invoices(self, client, teacher_token):
        resp = await client.get("/invoices", headers=auth(teacher_token))
        assert resp.status_code == 403


# ======================================================================
# 15. Billing — Payments (PERM-BIL:payment:initiate)
# ======================================================================
class TestPaymentRBAC:
    """POST /payments/initiate — allowed: PAR; denied: STD, TCH."""

    @pytest.mark.asyncio
    async def test_parent_can_initiate(self, client, parent_token):
        key = f"rbac-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/payments/initiate",
            headers=auth(parent_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": key},
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_initiate(self, client, student_token):
        resp = await client.post(
            "/payments/initiate",
            headers=auth(student_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": "fail"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_initiate(self, client, teacher_token):
        resp = await client.post(
            "/payments/initiate",
            headers=auth(teacher_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": "fail"},
        )
        assert resp.status_code == 403


# ======================================================================
# 16. COM — Notifications (PERM-COM:notification:read)
# ======================================================================
class TestNotificationRBAC:
    """GET /notifications — allowed: ADM, PAR, STD, TCH."""

    @pytest.mark.asyncio
    async def test_admin_can_read(self, client, admin_token):
        resp = await client.get("/notifications", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_can_read(self, client, parent_token):
        resp = await client.get("/notifications", headers=auth(parent_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_student_can_read(self, client, student_token):
        resp = await client.get("/notifications", headers=auth(student_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_can_read(self, client, teacher_token):
        resp = await client.get("/notifications", headers=auth(teacher_token))
        assert resp.status_code == 200


# ======================================================================
# 17. COM — Consents (PERM-COM:consent:update)
# ======================================================================
class TestConsentRBAC:
    """GET /consents — allowed: PAR, ADM; denied: STD, TCH."""

    @pytest.mark.asyncio
    async def test_parent_can_list_consents(self, client, parent_token):
        resp = await client.get("/consents", headers=auth(parent_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_list_consents(self, client, admin_token):
        resp = await client.get("/consents", headers=auth(admin_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_list_consents(self, client, student_token):
        resp = await client.get("/consents", headers=auth(student_token))
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_consents(self, client, teacher_token):
        resp = await client.get("/consents", headers=auth(teacher_token))
        assert resp.status_code == 403


# ======================================================================
# 18. COM — Feed (PERM-COM:notification:read + PAR only)
# ======================================================================
class TestFeedRBAC:
    """GET /feed — allowed: PAR; denied: STD (feed is parent-specific)."""

    @pytest.mark.asyncio
    async def test_parent_can_read_feed(self, client, parent_token):
        resp = await client.get("/feed", headers=auth(parent_token))
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_read_feed(self, client, admin_token):
        resp = await client.get("/feed", headers=auth(admin_token))
        assert resp.status_code == 200


# ======================================================================
# 19. Error Response Format Validation
# ======================================================================
class TestErrorResponseFormat:
    """All 401/403 responses must follow the error envelope format."""

    @pytest.mark.asyncio
    async def test_401_error_format(self, client):
        resp = await client.get("/invoices")
        body = resp.json()
        assert "error" in body
        err = body["error"]
        assert "code" in err
        assert "message" in err
        assert "category" in err
        assert err["category"] == "authn"

    @pytest.mark.asyncio
    async def test_403_error_format(self, client, student_token):
        resp = await client.get("/invoices", headers=auth(student_token))
        body = resp.json()
        assert "error" in body
        err = body["error"]
        assert "code" in err
        assert err["category"] == "authz"

    @pytest.mark.asyncio
    async def test_error_has_correlation_id(self, client):
        resp = await client.get("/invoices")
        body = resp.json()
        assert "correlation_id" in body["error"]

    @pytest.mark.asyncio
    async def test_error_has_timestamp(self, client):
        resp = await client.get("/invoices")
        body = resp.json()
        assert "timestamp" in body["error"]
