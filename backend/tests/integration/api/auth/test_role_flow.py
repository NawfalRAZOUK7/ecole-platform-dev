"""Integration tests for Phase 3 — Core API Endpoints.

Tests all Phase 3 endpoints across ERP, LMS, Billing, and COM domains.
Requires seed data to be loaded (make seed).
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


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ======================================================================
# ERP — Teacher Assignment (S-047)
# ======================================================================
class TestTeacherAssignment:
    @pytest.mark.asyncio
    async def test_create_teacher_assignment(self, client, admin_token):
        """ADM can assign a teacher to a class."""
        resp = await client.post(
            "/class-assignments",
            headers=auth_header(admin_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["teacher_id"] == TEACHER_ID
        assert data["class_id"] == CLASS_ID

    @pytest.mark.asyncio
    async def test_create_teacher_assignment_idempotent(self, client, admin_token):
        """Re-assigning same teacher returns existing assignment."""
        resp = await client.post(
            "/class-assignments",
            headers=auth_header(admin_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code in (200, 201)
        assert resp.json()["data"]["teacher_id"] == TEACHER_ID

    @pytest.mark.asyncio
    async def test_create_teacher_assignment_rbac(self, client, student_token):
        """STD cannot assign teachers (403)."""
        resp = await client.post(
            "/class-assignments",
            headers=auth_header(student_token),
            json={
                "teacher_id": TEACHER_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        assert resp.status_code == 403


# ======================================================================
# ERP — Attendance (S-048)
# ======================================================================
class TestAttendance:
    @pytest.mark.asyncio
    async def test_create_attendance_session(self, client, teacher_token):
        """TCH can create an attendance session."""
        slot = f"slot-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/attendance/sessions",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-15",
                "slot": slot,
                "records": [
                    {"student_id": STUDENT_ID, "status": "present"},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["class_id"] == CLASS_ID
        assert data["slot"] == slot
        assert len(data["records"]) == 1
        assert data["records"][0]["status"] == "present"

    @pytest.mark.asyncio
    async def test_attendance_duplicate_slot(self, client, teacher_token):
        """Duplicate class/date/slot returns 409."""
        slot = f"dup-{uuid.uuid4().hex[:8]}"
        # First call
        resp1 = await client.post(
            "/attendance/sessions",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-14",
                "slot": slot,
                "records": [{"student_id": STUDENT_ID, "status": "absent"}],
            },
        )
        assert resp1.status_code == 201

        # Second call with same slot
        resp2 = await client.post(
            "/attendance/sessions",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-14",
                "slot": slot,
                "records": [{"student_id": STUDENT_ID, "status": "present"}],
            },
        )
        assert resp2.status_code == 409

    @pytest.mark.asyncio
    async def test_attendance_rbac_student(self, client, student_token):
        """STD cannot mark attendance (403)."""
        resp = await client.post(
            "/attendance/sessions",
            headers=auth_header(student_token),
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
# ERP — Justification (S-049, S-050)
# ======================================================================
class TestJustification:
    @pytest.mark.asyncio
    async def test_justification_flow(
        self, client, teacher_token, parent_token, admin_token
    ):
        """Full flow: TCH marks absent → PAR justifies → ADM reviews."""
        # 1. Teacher marks student absent
        slot = f"just-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/attendance/sessions",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
                "session_date": "2026-03-13",
                "slot": slot,
                "records": [{"student_id": STUDENT_ID, "status": "absent"}],
            },
        )
        assert resp.status_code == 201
        record_id = resp.json()["data"]["records"][0]["id"]

        # 2. Parent submits justification
        resp = await client.post(
            "/attendance/justifications",
            headers=auth_header(parent_token),
            data={
                "attendance_record_id": record_id,
                "reason": "Rendez-vous medical",
            },
        )
        assert resp.status_code == 201, resp.text
        just_id = resp.json()["data"]["id"]
        assert resp.json()["data"]["status"] == "pending"

        # 3. Admin reviews (approves)
        resp = await client.post(
            f"/attendance/justifications/{just_id}/review",
            headers=auth_header(admin_token),
            json={"decision": "justified"},
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["decision"] == "justified"


# ======================================================================
# LMS — Courses (S-051)
# ======================================================================
class TestCourses:
    @pytest.mark.asyncio
    async def test_create_course(self, client, teacher_token):
        """TCH can create a course."""
        resp = await client.post(
            "/courses",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"Test Course {uuid.uuid4().hex[:8]}",
                "description": "Test description",
                "status": "draft",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["class_id"] == CLASS_ID
        assert data["teacher_id"] == TEACHER_ID
        assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_list_courses(self, client, teacher_token):
        """TCH can list courses."""
        resp = await client.get(
            "/courses",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        assert "data" in resp.json()
        assert "meta" in resp.json()

    @pytest.mark.asyncio
    async def test_create_course_rbac(self, client, student_token):
        """STD cannot create courses (403)."""
        resp = await client.post(
            "/courses",
            headers=auth_header(student_token),
            json={
                "class_id": CLASS_ID,
                "title": "Should fail",
                "status": "draft",
            },
        )
        assert resp.status_code == 403


# ======================================================================
# LMS — Assignments (S-052)
# ======================================================================
class TestAssignments:
    @pytest.mark.asyncio
    async def test_create_assignment(self, client, teacher_token):
        """TCH can create an assignment for their course."""
        # First create a course
        course_resp = await client.post(
            "/courses",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"Course for assignment {uuid.uuid4().hex[:8]}",
                "status": "draft",
            },
        )
        course_id = course_resp.json()["data"]["id"]

        # Create assignment
        resp = await client.post(
            "/assignments",
            headers=auth_header(teacher_token),
            json={
                "course_id": course_id,
                "title": "Test Assignment",
                "total_points": 20,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["total_points"] == 20

    @pytest.mark.asyncio
    async def test_list_assignments(self, client, teacher_token):
        """TCH can list assignments."""
        resp = await client.get(
            "/assignments",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200


# ======================================================================
# LMS — Submissions (S-053)
# ======================================================================
class TestSubmissions:
    @pytest.mark.asyncio
    async def test_create_submission(self, client, student_token):
        """STD can submit work. Uses seed assignment."""
        resp = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        # Either 201 (new) or 200 (idempotent replay)
        assert resp.status_code in (200, 201)
        data = resp.json()["data"]
        assert data["student_id"] == STUDENT_ID

    @pytest.mark.asyncio
    async def test_submission_idempotent(self, client, student_token):
        """Submitting twice returns same submission."""
        resp1 = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        resp2 = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert resp1.json()["data"]["id"] == resp2.json()["data"]["id"]


# ======================================================================
# LMS — Results (S-055)
# ======================================================================
class TestResults:
    @pytest.mark.asyncio
    async def test_student_results(self, client, student_token):
        """STD can view own results."""
        resp = await client.get(
            "/results",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert "score" in data[0]
        assert "assignment_title" in data[0]

    @pytest.mark.asyncio
    async def test_parent_results(self, client, parent_token):
        """PAR can view child results."""
        resp = await client.get(
            "/results",
            headers=auth_header(parent_token),
            params={"student_id": STUDENT_ID},
        )
        assert resp.status_code == 200


# ======================================================================
# LMS — Content Items (S-056, S-057)
# ======================================================================
class TestContentItems:
    @pytest.mark.asyncio
    async def test_list_content_items(self, client, student_token):
        """STD can list published content items."""
        resp = await client.get(
            "/content-items",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert all(item["status"] == "published" for item in data)

    @pytest.mark.asyncio
    async def test_get_content_item(self, client, student_token):
        """STD can get a content item by ID."""
        resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == CONTENT_ITEM_ID

    @pytest.mark.asyncio
    async def test_update_content_progress(self, client, student_token):
        """STD can track progress on content items."""
        resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/progress",
            headers=auth_header(student_token),
            json={"status": "completed"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "completed"


# ======================================================================
# LMS — Activities (S-058, S-059)
# ======================================================================
class TestActivities:
    @pytest.mark.asyncio
    async def test_list_activities(self, client, student_token):
        """STD can list activities."""
        resp = await client.get(
            "/activities",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_activity_session_lifecycle(self, client, student_token):
        """STD can start and complete an activity session."""
        # Start session
        resp = await client.post(
            "/activities/sessions",
            headers=auth_header(student_token),
            json={"activity_id": ACTIVITY_ID},
        )
        assert resp.status_code == 201
        session_id = resp.json()["data"]["id"]
        assert resp.json()["data"]["status"] == "started"

        # Complete session
        resp = await client.post(
            f"/activities/sessions/{session_id}/complete",
            headers=auth_header(student_token),
            json={"score": 90.0},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "completed"
        assert resp.json()["data"]["score"] == 90.0

    @pytest.mark.asyncio
    async def test_complete_already_completed(self, client, student_token):
        """Completing an already completed session returns 409."""
        # Start session
        resp = await client.post(
            "/activities/sessions",
            headers=auth_header(student_token),
            json={"activity_id": ACTIVITY_ID},
        )
        session_id = resp.json()["data"]["id"]

        # Complete
        await client.post(
            f"/activities/sessions/{session_id}/complete",
            headers=auth_header(student_token),
            json={"score": 50.0},
        )

        # Try completing again
        resp = await client.post(
            f"/activities/sessions/{session_id}/complete",
            headers=auth_header(student_token),
            json={"score": 60.0},
        )
        assert resp.status_code == 409


# ======================================================================
# LMS — Assessments (S-060)
# ======================================================================
class TestAssessments:
    @pytest.mark.asyncio
    async def test_list_assessments(self, client, admin_token):
        """ADM can list assessments."""
        resp = await client.get(
            "/assessments",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    @pytest.mark.asyncio
    async def test_create_assessment(self, client, teacher_token):
        """TCH can create an assessment."""
        resp = await client.post(
            "/assessments",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"Test Assessment {uuid.uuid4().hex[:8]}",
                "total_points": 100,
                "status": "draft",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["data"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_publish_assessment(self, client, teacher_token):
        """TCH can publish a draft assessment."""
        # Create draft
        resp = await client.post(
            "/assessments",
            headers=auth_header(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"Publish test {uuid.uuid4().hex[:8]}",
                "total_points": 50,
                "status": "draft",
            },
        )
        assess_id = resp.json()["data"]["id"]

        # Publish
        resp = await client.post(
            f"/assessments/{assess_id}/publish",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "published"

    @pytest.mark.asyncio
    async def test_submit_assessment_result(self, client, student_token):
        """STD can submit an assessment result."""
        resp = await client.post(
            f"/assessments/{ASSESSMENT_ID}/results",
            headers=auth_header(student_token),
            json={
                "assessment_id": ASSESSMENT_ID,
                "score": 35.0,
            },
        )
        # Either 201 (new) or 200 (idempotent)
        assert resp.status_code in (200, 201)
        assert resp.json()["data"]["student_id"] == STUDENT_ID


# ======================================================================
# Billing — Invoices (S-061)
# ======================================================================
class TestInvoices:
    @pytest.mark.asyncio
    async def test_list_invoices_parent(self, client, parent_token):
        """PAR can list own invoices."""
        resp = await client.get(
            "/invoices",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert all(item["parent_id"] == PARENT_ID for item in data)

    @pytest.mark.asyncio
    async def test_list_invoices_admin(self, client, admin_token):
        """ADM can list all school invoices."""
        resp = await client.get(
            "/invoices",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_invoice(self, client, parent_token):
        """PAR can get own invoice details."""
        resp = await client.get(
            f"/invoices/{INVOICE_ID}",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == INVOICE_ID
        assert len(data["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_invoices_rbac(self, client, student_token):
        """STD cannot view invoices (403)."""
        resp = await client.get(
            "/invoices",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403


# ======================================================================
# Billing — Payments (S-062, S-063)
# ======================================================================
class TestPayments:
    @pytest.mark.asyncio
    async def test_initiate_payment(self, client, parent_token):
        """PAR can initiate a payment."""
        key = f"test-pay-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/payments/initiate",
            headers=auth_header(parent_token),
            json={
                "invoice_id": INVOICE_ID,
                "idempotency_key": key,
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["status"] == "pending"
        assert data["idempotency_key"] == key

    @pytest.mark.asyncio
    async def test_payment_idempotent(self, client, parent_token):
        """Same idempotency_key returns same payment attempt."""
        key = f"idem-{uuid.uuid4().hex[:8]}"
        resp1 = await client.post(
            "/payments/initiate",
            headers=auth_header(parent_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": key},
        )
        resp2 = await client.post(
            "/payments/initiate",
            headers=auth_header(parent_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": key},
        )
        assert resp1.json()["data"]["id"] == resp2.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_get_payment_status(self, client, parent_token):
        """PAR can get payment status."""
        key = f"get-{uuid.uuid4().hex[:8]}"
        create_resp = await client.post(
            "/payments/initiate",
            headers=auth_header(parent_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": key},
        )
        attempt_id = create_resp.json()["data"]["id"]

        resp = await client.get(
            f"/payments/{attempt_id}",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == attempt_id

    @pytest.mark.asyncio
    async def test_payment_rbac(self, client, student_token):
        """STD cannot initiate payments (403)."""
        resp = await client.post(
            "/payments/initiate",
            headers=auth_header(student_token),
            json={
                "invoice_id": INVOICE_ID,
                "idempotency_key": "should-fail",
            },
        )
        assert resp.status_code == 403


# ======================================================================
# COM — Notifications (S-065)
# ======================================================================
class TestNotifications:
    @pytest.mark.asyncio
    async def test_list_notifications_parent(self, client, parent_token):
        """PAR can list own notifications."""
        resp = await client.get(
            "/notifications",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert all(item["parent_id"] == PARENT_ID for item in data)

    @pytest.mark.asyncio
    async def test_list_notifications_admin(self, client, admin_token):
        """ADM can list all school notifications."""
        resp = await client.get(
            "/notifications",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_notifications_rbac(self, client, student_token):
        """STD can also read notifications (has PERM-COM:notification:read)."""
        resp = await client.get(
            "/notifications",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 200


# ======================================================================
# COM — Consents (S-066)
# ======================================================================
class TestConsents:
    @pytest.mark.asyncio
    async def test_list_consents(self, client, parent_token):
        """PAR can list consent preferences."""
        resp = await client.get(
            "/consents",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_consents_rbac(self, client, student_token):
        """STD cannot manage consents (403)."""
        resp = await client.get(
            "/consents",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 403


# ======================================================================
# COM — Feed (S-067)
# ======================================================================
class TestFeed:
    @pytest.mark.asyncio
    async def test_list_feed(self, client, parent_token):
        """PAR can view feed."""
        resp = await client.get(
            "/feed",
            headers=auth_header(parent_token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert all(item["parent_id"] == PARENT_ID for item in data)

    @pytest.mark.asyncio
    async def test_feed_with_student_filter(self, client, parent_token):
        """PAR can filter feed by student_id."""
        resp = await client.get(
            "/feed",
            headers=auth_header(parent_token),
            params={"student_id": STUDENT_ID},
        )
        assert resp.status_code == 200


# ======================================================================
# Response Envelope & Pagination
# ======================================================================
class TestResponseEnvelope:
    @pytest.mark.asyncio
    async def test_success_envelope(self, client, parent_token):
        """Success response has data + meta with timestamp and version."""
        resp = await client.get(
            "/invoices",
            headers=auth_header(parent_token),
        )
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert body["meta"]["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_list_pagination_meta(self, client, admin_token):
        """List responses include next_cursor and has_more."""
        resp = await client.get(
            "/notifications",
            headers=auth_header(admin_token),
        )
        meta = resp.json()["meta"]
        assert "next_cursor" in meta
        assert "has_more" in meta

    @pytest.mark.asyncio
    async def test_error_envelope(self, client):
        """Error responses have error.code, error.category, error.correlation_id."""
        resp = await client.get("/invoices")  # No auth
        body = resp.json()
        assert "error" in body
        assert "code" in body["error"]
        assert "category" in body["error"]
        assert "correlation_id" in body["error"]
