"""Contract tests — verify API responses match Pack C5 OpenAPI spec.

Reference: S-115 — Contract tests, S-068 — Standard response envelope
Tests that all responses conform to the expected structure:
- Success envelope: { data, meta: { timestamp, version } }
- List envelope: { data: [], meta: { next_cursor, has_more, timestamp, version } }
- Error envelope: { error: { code, message, category, correlation_id, retryable, timestamp } }
- Pagination: cursor-based, DEFAULT_PAGE_SIZE=20
"""

from __future__ import annotations

import uuid
from datetime import datetime

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
# Health Check Contract
# ======================================================================
class TestHealthContract:
    """GET /health — public, no auth."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_has_required_fields(self, client):
        body = (await client.get("/health")).json()
        assert body["status"] == "healthy"
        assert "version" in body
        assert "timestamp" in body

    @pytest.mark.asyncio
    async def test_health_timestamp_is_iso(self, client):
        body = (await client.get("/health")).json()
        datetime.fromisoformat(body["timestamp"])


# ======================================================================
# Success Envelope Contract (single item)
# ======================================================================
class TestSuccessEnvelopeContract:
    """All single-item responses: { data: {...}, meta: {timestamp, version} }."""

    @pytest.mark.asyncio
    async def test_class_detail_envelope(self, client, admin_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(admin_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert "timestamp" in body["meta"]
        assert "version" in body["meta"]

    @pytest.mark.asyncio
    async def test_invoice_detail_envelope(self, client, parent_token):
        resp = await client.get(f"/invoices/{INVOICE_ID}", headers=auth(parent_token))
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "meta" in body
        assert body["meta"]["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_content_item_detail_envelope(self, client, student_token):
        resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}",
            headers=auth(student_token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert isinstance(body["data"], dict)

    @pytest.mark.asyncio
    async def test_meta_timestamp_is_valid_iso(self, client, admin_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(admin_token))
        ts = resp.json()["meta"]["timestamp"]
        datetime.fromisoformat(ts)


# ======================================================================
# List Envelope Contract (paginated)
# ======================================================================
class TestListEnvelopeContract:
    """All list responses: { data: [...], meta: {next_cursor, has_more, timestamp, version} }."""

    LIST_ENDPOINTS = [
        ("/courses", "teacher_token"),
        ("/assignments", "teacher_token"),
        ("/results", "student_token"),
        ("/content-items", "student_token"),
        ("/activities", "student_token"),
        ("/assessments", "admin_token"),
        ("/invoices", "parent_token"),
        ("/notifications", "parent_token"),
        ("/consents", "parent_token"),
        ("/feed", "parent_token"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path,token_fixture", LIST_ENDPOINTS)
    async def test_list_envelope_structure(
        self,
        client,
        path,
        token_fixture,
        admin_token,
        teacher_token,
        student_token,
        parent_token,
    ):
        tokens = {
            "admin_token": admin_token,
            "teacher_token": teacher_token,
            "student_token": student_token,
            "parent_token": parent_token,
        }
        resp = await client.get(path, headers=auth(tokens[token_fixture]))
        assert resp.status_code == 200
        body = resp.json()

        # Structure checks
        assert "data" in body, f"{path} missing 'data' key"
        assert isinstance(body["data"], list), f"{path} data is not a list"
        assert "meta" in body, f"{path} missing 'meta' key"

        meta = body["meta"]
        assert "next_cursor" in meta, f"{path} meta missing next_cursor"
        assert "has_more" in meta, f"{path} meta missing has_more"
        assert "timestamp" in meta, f"{path} meta missing timestamp"
        assert "version" in meta, f"{path} meta missing version"

    @pytest.mark.asyncio
    async def test_list_data_is_array(self, client, parent_token):
        resp = await client.get("/invoices", headers=auth(parent_token))
        assert isinstance(resp.json()["data"], list)

    @pytest.mark.asyncio
    async def test_has_more_is_boolean(self, client, parent_token):
        resp = await client.get("/invoices", headers=auth(parent_token))
        assert isinstance(resp.json()["meta"]["has_more"], bool)


# ======================================================================
# Error Envelope Contract
# ======================================================================
class TestErrorEnvelopeContract:
    """Error responses: { error: { code, message, category, correlation_id, retryable, timestamp } }."""

    @pytest.mark.asyncio
    async def test_401_error_envelope(self, client):
        resp = await client.get("/invoices")
        assert resp.status_code == 401
        body = resp.json()
        assert "error" in body
        err = body["error"]
        assert "code" in err
        assert "message" in err
        assert "category" in err
        assert "correlation_id" in err
        assert "retryable" in err
        assert "timestamp" in err

    @pytest.mark.asyncio
    async def test_403_error_envelope(self, client, student_token):
        resp = await client.get("/invoices", headers=auth(student_token))
        assert resp.status_code == 403
        err = resp.json()["error"]
        assert err["category"] == "authz"
        assert err["retryable"] is False

    @pytest.mark.asyncio
    async def test_error_code_format(self, client):
        """Error codes follow ERR-{DOMAIN}-{NNN} format."""
        resp = await client.get("/invoices")
        code = resp.json()["error"]["code"]
        assert code.startswith("ERR-"), f"Error code '{code}' should start with ERR-"

    @pytest.mark.asyncio
    async def test_error_timestamp_is_iso(self, client):
        resp = await client.get("/invoices")
        ts = resp.json()["error"]["timestamp"]
        datetime.fromisoformat(ts)

    @pytest.mark.asyncio
    async def test_correlation_id_is_uuid(self, client):
        resp = await client.get("/invoices")
        cid = resp.json()["error"]["correlation_id"]
        if cid is not None:
            uuid.UUID(cid)  # Should not raise

    @pytest.mark.asyncio
    async def test_error_category_is_valid(self, client):
        valid = {
            "validation",
            "authn",
            "authz",
            "conflict",
            "external",
            "system",
            "rate_limit",
            "network",
            "not_found",
            "policy",
        }
        resp = await client.get("/invoices")
        cat = resp.json()["error"]["category"]
        assert cat in valid, f"Category '{cat}' not in valid set"


# ======================================================================
# Pagination Contract
# ======================================================================
class TestPaginationContract:
    """Cursor-based pagination behaviour."""

    @pytest.mark.asyncio
    async def test_default_page_size_applied(self, client, parent_token):
        """Without limit param, server defaults to 20 items max."""
        resp = await client.get("/notifications", headers=auth(parent_token))
        data = resp.json()["data"]
        assert len(data) <= 20

    @pytest.mark.asyncio
    async def test_limit_param_respected(self, client, parent_token):
        """Explicit limit=2 returns at most 2 items."""
        resp = await client.get(
            "/notifications",
            headers=auth(parent_token),
            params={"limit": 2},
        )
        data = resp.json()["data"]
        assert len(data) <= 2

    @pytest.mark.asyncio
    async def test_cursor_param_accepted(self, client, parent_token):
        """Passing cursor param doesn't cause 400/500."""
        resp1 = await client.get(
            "/notifications",
            headers=auth(parent_token),
            params={"limit": 1},
        )
        meta = resp1.json()["meta"]
        cursor = meta.get("next_cursor")
        if cursor:
            resp2 = await client.get(
                "/notifications",
                headers=auth(parent_token),
                params={"cursor": cursor},
            )
            assert resp2.status_code == 200

    @pytest.mark.asyncio
    async def test_has_more_false_on_last_page(self, client, parent_token):
        """When all items returned, has_more is False."""
        resp = await client.get(
            "/notifications",
            headers=auth(parent_token),
            params={"limit": 100},
        )
        meta = resp.json()["meta"]
        # If has_more is False, next_cursor should be null
        if not meta["has_more"]:
            assert meta["next_cursor"] is None


# ======================================================================
# Data Field Contract — ERP
# ======================================================================
class TestERPFieldContract:
    """Verify ERP response data fields match spec."""

    @pytest.mark.asyncio
    async def test_class_detail_fields(self, client, admin_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(admin_token))
        data = resp.json()["data"]
        assert "id" in data
        assert "school_id" in data
        assert "code" in data

    @pytest.mark.asyncio
    async def test_enrollment_create_fields(self, client, admin_token):
        resp = await client.post(
            "/enrollments",
            headers=auth(admin_token),
            json={
                "student_id": STUDENT_ID,
                "class_id": CLASS_ID,
                "period_id": PERIOD_ID,
            },
        )
        data = resp.json()["data"]
        assert "id" in data
        assert "student_id" in data
        assert "class_id" in data
        assert "period_id" in data

    @pytest.mark.asyncio
    async def test_attendance_session_fields(self, client, teacher_token):
        slot = f"contract-{uuid.uuid4().hex[:8]}"
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
        data = resp.json()["data"]
        assert "id" in data
        assert "class_id" in data
        assert "slot" in data
        assert "records" in data
        assert isinstance(data["records"], list)


# ======================================================================
# Data Field Contract — LMS
# ======================================================================
class TestLMSFieldContract:
    """Verify LMS response data fields match spec."""

    @pytest.mark.asyncio
    async def test_course_create_fields(self, client, teacher_token):
        resp = await client.post(
            "/courses",
            headers=auth(teacher_token),
            json={
                "class_id": CLASS_ID,
                "title": f"Contract Course {uuid.uuid4().hex[:8]}",
                "status": "draft",
            },
        )
        data = resp.json()["data"]
        assert "id" in data
        assert "class_id" in data
        assert "teacher_id" in data
        assert "title" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_content_item_fields(self, client, student_token):
        resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}",
            headers=auth(student_token),
        )
        data = resp.json()["data"]
        assert "id" in data
        assert "title" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_activity_session_fields(self, client, student_token):
        resp = await client.post(
            "/activities/sessions",
            headers=auth(student_token),
            json={"activity_id": ACTIVITY_ID},
        )
        data = resp.json()["data"]
        assert "id" in data
        assert "activity_id" in data
        assert "student_id" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_results_item_fields(self, client, student_token):
        resp = await client.get("/results", headers=auth(student_token))
        data = resp.json()["data"]
        if len(data) > 0:
            item = data[0]
            assert "assignment_title" in item
            assert "course_title" in item
            assert "score" in item


# ======================================================================
# Data Field Contract — Billing
# ======================================================================
class TestBillingFieldContract:
    """Verify Billing response data fields match spec."""

    @pytest.mark.asyncio
    async def test_invoice_list_fields(self, client, parent_token):
        resp = await client.get("/invoices", headers=auth(parent_token))
        data = resp.json()["data"]
        assert len(data) >= 1
        inv = data[0]
        assert "id" in inv
        assert "school_id" in inv
        assert "parent_id" in inv
        assert "status" in inv
        assert "total_amount" in inv

    @pytest.mark.asyncio
    async def test_invoice_detail_has_items(self, client, parent_token):
        resp = await client.get(f"/invoices/{INVOICE_ID}", headers=auth(parent_token))
        data = resp.json()["data"]
        assert "items" in data
        assert isinstance(data["items"], list)
        if len(data["items"]) > 0:
            item = data["items"][0]
            assert "description" in item
            assert "amount" in item

    @pytest.mark.asyncio
    async def test_payment_initiate_fields(self, client, parent_token):
        key = f"contract-{uuid.uuid4().hex[:8]}"
        resp = await client.post(
            "/payments/initiate",
            headers=auth(parent_token),
            json={"invoice_id": INVOICE_ID, "idempotency_key": key},
        )
        data = resp.json()["data"]
        assert "id" in data
        assert "invoice_id" in data
        assert "status" in data
        assert "idempotency_key" in data
        assert data["status"] == "pending"


# ======================================================================
# Data Field Contract — COM
# ======================================================================
class TestCOMFieldContract:
    """Verify COM response data fields match spec."""

    @pytest.mark.asyncio
    async def test_notification_fields(self, client, parent_token):
        resp = await client.get("/notifications", headers=auth(parent_token))
        data = resp.json()["data"]
        if len(data) > 0:
            n = data[0]
            assert "id" in n
            assert "school_id" in n
            assert "title" in n

    @pytest.mark.asyncio
    async def test_feed_item_fields(self, client, parent_token):
        resp = await client.get("/feed", headers=auth(parent_token))
        data = resp.json()["data"]
        if len(data) > 0:
            f = data[0]
            assert "id" in f
            assert "parent_id" in f
            assert "title" in f

    @pytest.mark.asyncio
    async def test_consent_fields(self, client, parent_token):
        resp = await client.get("/consents", headers=auth(parent_token))
        data = resp.json()["data"]
        if len(data) > 0:
            c = data[0]
            assert "id" in c
            assert "user_id" in c
            assert "status" in c


# ======================================================================
# Version Contract
# ======================================================================
class TestVersionContract:
    """All meta.version must match APP_VERSION constant."""

    @pytest.mark.asyncio
    async def test_version_in_success(self, client, admin_token):
        resp = await client.get(f"/classes/{CLASS_ID}", headers=auth(admin_token))
        assert resp.json()["meta"]["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_version_in_list(self, client, parent_token):
        resp = await client.get("/invoices", headers=auth(parent_token))
        assert resp.json()["meta"]["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_version_in_health(self, client):
        resp = await client.get("/health")
        assert resp.json()["version"] == "0.1.0"
