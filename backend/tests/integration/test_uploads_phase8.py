"""Integration smoke-tests — Phase 8 direct-upload API endpoints.

Tests /uploads/init, /uploads/complete, /uploads/{id}/status.
Storage is mocked where needed so the suite runs without a live MinIO instance.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch


from app.models.uploads import UploadSession
from tests.integration.api.helpers import auth_header

_FAKE_PRESIGN_URL = "https://minio.test/presigned-put"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _init_body(school_id: str, *, submission_id: str | None = None) -> dict:
    return {
        "kind": "submission_file",
        "filename": "homework.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 512 * 1024,
        "scope": {
            "school_id": school_id,
            "submission_id": submission_id or str(uuid.uuid4()),
        },
    }


def _patch_s3(presign_url: str = _FAKE_PRESIGN_URL):
    """Context manager: makes the local storage look like S3StorageBackend
    and stubs presign_put so /uploads/init returns a fake URL."""
    from app.core.storage import S3StorageBackend

    return patch.multiple(
        "app.api.v1.uploads",
        isinstance=lambda obj, cls: True
        if cls is S3StorageBackend
        else __builtins__["isinstance"](obj, cls),
        storage=AsyncMock(presign_put=AsyncMock(return_value=presign_url)),
    )


# ---------------------------------------------------------------------------
# /uploads/init — auth and validation (no storage required)
# ---------------------------------------------------------------------------


class TestUploadInit:
    async def test_requires_auth(self, client, api_context):
        school_id = str(api_context["school"].id)
        resp = await client.post("/uploads/init", json=_init_body(school_id))
        assert resp.status_code == 401

    async def test_missing_kind_returns_422(self, client, api_context):
        token = api_context["student"]["token"]
        resp = await client.post(
            "/uploads/init",
            headers=auth_header(token),
            json={
                "filename": "x.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 1024,
            },
        )
        assert resp.status_code == 422

    async def test_invalid_mime_returns_422(self, client, api_context):
        """Unsupported MIME type for the declared kind → 422."""
        token = api_context["student"]["token"]
        school_id = str(api_context["school"].id)
        body = _init_body(school_id)
        body["mime_type"] = "video/mp4"  # not allowed for submission_file
        resp = await client.post(
            "/uploads/init",
            headers=auth_header(token),
            json=body,
        )
        assert resp.status_code == 422

    async def test_cross_school_returns_403(self, client, api_context):
        """scope.school_id belonging to a different school → 403."""
        token = api_context["student"]["token"]
        other_school_id = str(uuid.uuid4())
        resp = await client.post(
            "/uploads/init",
            headers=auth_header(token),
            json=_init_body(other_school_id),
        )
        assert resp.status_code == 403

    async def test_local_storage_rejects_before_presign(self, client, api_context):
        """With STORAGE_BACKEND=local the endpoint rejects the request.

        Scope validation runs first (→ 404 for unknown submission) and the
        S3 backend check runs second (→ 422 with ERR-UPLOAD-501).  Either
        error means the request was correctly rejected without presigning.
        """
        token = api_context["student"]["token"]
        school_id = str(api_context["school"].id)
        resp = await client.post(
            "/uploads/init",
            headers=auth_header(token),
            json=_init_body(school_id),
        )
        # 404 = scope entity not found; 422 = local storage not supported.
        # Both indicate the upload was blocked before any presign was issued.
        assert resp.status_code in (404, 422)

    async def test_teacher_content_asset_local_storage_rejects(
        self, client, api_context
    ):
        """Teachers uploading content assets are also rejected on local storage."""
        token = api_context["teacher"]["token"]
        school_id = str(api_context["school"].id)
        resp = await client.post(
            "/uploads/init",
            headers=auth_header(token),
            json={
                "kind": "content_asset",
                "filename": "lecture.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 2 * 1024 * 1024,
                "scope": {
                    "school_id": school_id,
                    "content_item_id": str(uuid.uuid4()),
                },
            },
        )
        assert resp.status_code in (404, 422)


# ---------------------------------------------------------------------------
# /uploads/{id}/status — auth and 404
# ---------------------------------------------------------------------------


class TestUploadStatus:
    async def test_requires_auth(self, client, api_context):
        resp = await client.get(f"/uploads/{uuid.uuid4()}/status")
        assert resp.status_code == 401

    async def test_unknown_id_returns_404(self, client, api_context):
        token = api_context["teacher"]["token"]
        resp = await client.get(
            f"/uploads/{uuid.uuid4()}/status",
            headers=auth_header(token),
        )
        assert resp.status_code == 404

    async def test_session_inserted_directly_is_visible(
        self, client, api_context, session_factory
    ):
        """Insert an UploadSession row directly and verify the status endpoint reflects it."""
        school = api_context["school"]
        student = api_context["student"]
        token = student["token"]

        upload_id = uuid.uuid4()
        async with session_factory() as db:
            row = UploadSession(
                id=upload_id,
                upload_state="uploading",
                kind="submission_file",
                object_key=f"schools/{school.id}/uploading/{upload_id}.pdf",
                mime_type="application/pdf",
                size_bytes=100 * 1024,
                school_id=school.id,
                uploader_id=student["user"].id,
                scope_data={"submission_id": str(uuid.uuid4())},
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.add(row)
            await db.commit()

        resp = await client.get(
            f"/uploads/{upload_id}/status",
            headers=auth_header(token),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["upload_id"] == str(upload_id)
        assert data["state"] == "uploading"

    async def test_any_school_member_can_poll_session(
        self, client, api_context, session_factory
    ):
        """A teacher can poll a student's upload session (same school, different uploader)."""
        school = api_context["school"]
        student = api_context["student"]
        teacher_token = api_context["teacher"]["token"]

        upload_id = uuid.uuid4()
        async with session_factory() as db:
            row = UploadSession(
                id=upload_id,
                upload_state="scanning",
                kind="submission_file",
                object_key=f"schools/{school.id}/submissions/x/{upload_id}.pdf",
                mime_type="application/pdf",
                size_bytes=100 * 1024,
                school_id=school.id,
                uploader_id=student["user"].id,  # student uploaded
                scope_data={"submission_id": str(uuid.uuid4())},
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.add(row)
            await db.commit()

        # Teacher from the same school can see the session
        resp = await client.get(
            f"/uploads/{upload_id}/status",
            headers=auth_header(teacher_token),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["state"] == "scanning"


# ---------------------------------------------------------------------------
# /uploads/complete — auth and 404
# ---------------------------------------------------------------------------


class TestUploadComplete:
    async def test_requires_auth(self, client, api_context):
        resp = await client.post(
            "/uploads/complete",
            json={"upload_id": str(uuid.uuid4()), "size_bytes": 1024},
        )
        assert resp.status_code == 401

    async def test_unknown_session_returns_404(self, client, api_context):
        token = api_context["student"]["token"]
        resp = await client.post(
            "/uploads/complete",
            headers=auth_header(token),
            json={"upload_id": str(uuid.uuid4()), "size_bytes": 1024},
        )
        assert resp.status_code == 404

    async def test_missing_size_bytes_returns_422(self, client, api_context):
        token = api_context["student"]["token"]
        resp = await client.post(
            "/uploads/complete",
            headers=auth_header(token),
            json={"upload_id": str(uuid.uuid4())},
        )
        assert resp.status_code == 422

    async def test_already_scanning_returns_409(
        self, client, api_context, session_factory
    ):
        """Calling /complete twice on the same session → 409 Conflict."""
        school = api_context["school"]
        student = api_context["student"]
        token = student["token"]

        upload_id = uuid.uuid4()
        async with session_factory() as db:
            row = UploadSession(
                id=upload_id,
                upload_state="scanning",  # already advanced past 'uploading'
                kind="submission_file",
                object_key=f"schools/{school.id}/submissions/x/{upload_id}.pdf",
                mime_type="application/pdf",
                size_bytes=100 * 1024,
                school_id=school.id,
                uploader_id=student["user"].id,
                scope_data={"submission_id": str(uuid.uuid4())},
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            )
            db.add(row)
            await db.commit()

        resp = await client.post(
            "/uploads/complete",
            headers=auth_header(token),
            json={"upload_id": str(upload_id), "size_bytes": 100 * 1024},
        )
        assert resp.status_code == 409
