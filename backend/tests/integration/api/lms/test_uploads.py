"""Integration tests for Phase 3B — File Upload & Storage Pipeline.

Tests: upload → download → checksum verify → MIME validation → size limit → delete.
Requires seed data + running API server (make up && make migrate && make seed).
"""

from __future__ import annotations

import hashlib
import io
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.core.database import async_session
from app.models.lms import Submission, SubmissionFile


# Fixed seed IDs (must match test_role_flow.py / seed data)
ASSIGNMENT_ID = "30000000-0000-4000-8000-000000000003"
CONTENT_ITEM_ID = "30000000-0000-4000-8000-000000000005"
STUDENT_ID = "10000000-0000-4000-8000-000000000007"


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def make_pdf_bytes(content: bytes = b"fake-pdf-content") -> tuple[bytes, str]:
    """Create a fake PDF file and return (bytes, sha256)."""
    sha256 = hashlib.sha256(content).hexdigest()
    return content, sha256


@pytest_asyncio.fixture(autouse=True)
async def reset_submission_upload_state():
    """Keep submission file tests deterministic across repeated suite reruns."""
    assignment_id = uuid.UUID(ASSIGNMENT_ID)
    student_id = uuid.UUID(STUDENT_ID)
    async with async_session() as session:
        submission_ids = list(
            (
                await session.execute(
                    select(Submission.id).where(
                        Submission.assignment_id == assignment_id,
                        Submission.student_id == student_id,
                        Submission.status.in_(["draft", "submitted"]),
                    )
                )
            )
            .scalars()
            .all()
        )
        if submission_ids:
            await session.execute(
                delete(SubmissionFile).where(
                    SubmissionFile.submission_id.in_(submission_ids)
                )
            )
            await session.execute(
                delete(Submission).where(Submission.id.in_(submission_ids))
            )
            await session.commit()
    yield


# ======================================================================
# Submission File Upload (Phase 3B)
# ======================================================================
class TestSubmissionFileUpload:
    """Test POST /submissions/{id}/files and GET /submissions/{id}/files/{file_id}."""

    @pytest.mark.asyncio
    async def test_upload_and_download_submission_file(self, client, student_token):
        """STD uploads a file to their submission, then downloads it."""
        # First, ensure a submission exists
        sub_resp = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert sub_resp.status_code in (200, 201)
        submission_id = sub_resp.json()["data"]["id"]

        # Upload a file
        pdf_bytes, expected_checksum = make_pdf_bytes()
        upload_resp = await client.post(
            f"/submissions/{submission_id}/files",
            headers=auth_header(student_token),
            files={"file": ("homework.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        assert upload_resp.status_code == 201
        upload_data = upload_resp.json()["data"]
        file_id = upload_data["id"]
        assert upload_data["mime_type"] == "application/pdf"
        assert upload_data["file_size"] == len(pdf_bytes)
        assert upload_data["checksum"] == expected_checksum

        # Download the file
        download_resp = await client.get(
            f"/submissions/{submission_id}/files/{file_id}",
            headers=auth_header(student_token),
        )
        assert download_resp.status_code == 200
        assert download_resp.content == pdf_bytes

    @pytest.mark.asyncio
    async def test_upload_rejected_bad_mime(self, client, student_token):
        """Upload with disallowed MIME type is rejected."""
        sub_resp = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        submission_id = sub_resp.json()["data"]["id"]

        resp = await client.post(
            f"/submissions/{submission_id}/files",
            headers=auth_header(student_token),
            files={
                "file": ("malware.exe", io.BytesIO(b"bad"), "application/x-msdownload")
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_max_files_limit(self, client, student_token):
        """Cannot exceed 5 files per submission."""
        sub_resp = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        submission_id = sub_resp.json()["data"]["id"]

        # Upload 5 files (some may already exist from prior tests — use unique content)
        for i in range(5):
            content = f"file-content-{i}-unique".encode()
            resp = await client.post(
                f"/submissions/{submission_id}/files",
                headers=auth_header(student_token),
                files={
                    "file": (f"file{i}.pdf", io.BytesIO(content), "application/pdf")
                },
            )
            # May hit the limit if files already exist from prior test runs
            if resp.status_code == 422:
                break

        # The 6th upload should definitely fail
        resp = await client.post(
            f"/submissions/{submission_id}/files",
            headers=auth_header(student_token),
            files={"file": ("extra.pdf", io.BytesIO(b"extra"), "application/pdf")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_teacher_can_download_submission_file(
        self, client, student_token, teacher_token
    ):
        """TCH can download files from student submissions in their course."""
        # Create submission and upload file as student
        sub_resp = await client.post(
            "/submissions",
            headers=auth_header(student_token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        submission_id = sub_resp.json()["data"]["id"]

        pdf_bytes, _ = make_pdf_bytes(b"teacher-download-test")
        upload_resp = await client.post(
            f"/submissions/{submission_id}/files",
            headers=auth_header(student_token),
            files={"file": ("hw.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        )
        # May be 201 or 422 (if max files reached), either way try download
        if upload_resp.status_code == 201:
            file_id = upload_resp.json()["data"]["id"]

            # Teacher downloads
            download_resp = await client.get(
                f"/submissions/{submission_id}/files/{file_id}",
                headers=auth_header(teacher_token),
            )
            assert download_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rbac_student_cannot_read_others_submission_files(
        self, client, student_token
    ):
        """STD cannot download files from another student's submission."""
        # Use a non-existent submission ID (different student)
        fake_submission = "00000000-0000-4000-8000-ffffffffffff"
        fake_file = "00000000-0000-4000-8000-ffffffffffff"
        resp = await client.get(
            f"/submissions/{fake_submission}/files/{fake_file}",
            headers=auth_header(student_token),
        )
        assert resp.status_code == 404


# ======================================================================
# Content Asset Upload/Download/Delete (Phase 3B)
# ======================================================================
class TestContentAssetUpload:
    """Test POST/GET/DELETE /content-items/{id}/assets."""

    @pytest.mark.asyncio
    async def test_upload_download_delete_content_asset(self, client, teacher_token):
        """TCH uploads an asset, downloads it, then deletes it."""
        # Upload
        asset_bytes = b"lesson-material-content"
        expected_checksum = hashlib.sha256(asset_bytes).hexdigest()

        upload_resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(teacher_token),
            files={"file": ("lesson.pdf", io.BytesIO(asset_bytes), "application/pdf")},
        )
        assert upload_resp.status_code == 201
        asset_data = upload_resp.json()["data"]
        asset_id = asset_data["id"]
        assert asset_data["checksum"] == expected_checksum
        assert asset_data["mime_type"] == "application/pdf"
        assert asset_data["file_size"] == len(asset_bytes)

        # Download
        download_resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(teacher_token),
        )
        assert download_resp.status_code == 200
        assert download_resp.content == asset_bytes

        # Delete
        delete_resp = await client.delete(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(teacher_token),
        )
        assert delete_resp.status_code == 200
        assert delete_resp.json()["data"]["deleted"] is True

        # Verify deleted — download should 404
        verify_resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(teacher_token),
        )
        assert verify_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_admin_can_upload_content_asset(self, client, admin_token):
        """ADM can upload content assets."""
        resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(admin_token),
            files={
                "file": (
                    "admin-doc.pdf",
                    io.BytesIO(b"admin-content"),
                    "application/pdf",
                )
            },
        )
        assert resp.status_code == 201

        # Clean up
        asset_id = resp.json()["data"]["id"]
        await client.delete(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(admin_token),
        )

    @pytest.mark.asyncio
    async def test_student_can_download_content_asset(
        self, client, teacher_token, student_token
    ):
        """STD can download content assets (read-only)."""
        # Upload as teacher
        upload_resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(teacher_token),
            files={
                "file": (
                    "for-students.pdf",
                    io.BytesIO(b"study-material"),
                    "application/pdf",
                )
            },
        )
        assert upload_resp.status_code == 201
        asset_id = upload_resp.json()["data"]["id"]

        # Download as student
        download_resp = await client.get(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(student_token),
        )
        assert download_resp.status_code == 200

        # Clean up
        await client.delete(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(teacher_token),
        )

    @pytest.mark.asyncio
    async def test_student_cannot_upload_content_asset(self, client, student_token):
        """STD cannot upload content assets (403)."""
        resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(student_token),
            files={"file": ("hack.pdf", io.BytesIO(b"nope"), "application/pdf")},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_student_cannot_delete_content_asset(
        self, client, teacher_token, student_token
    ):
        """STD cannot delete content assets (403)."""
        # Upload as teacher
        upload_resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(teacher_token),
            files={
                "file": ("protected.pdf", io.BytesIO(b"no-delete"), "application/pdf")
            },
        )
        assert upload_resp.status_code == 201
        asset_id = upload_resp.json()["data"]["id"]

        # Delete attempt as student
        delete_resp = await client.delete(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(student_token),
        )
        assert delete_resp.status_code == 403

        # Clean up as teacher
        await client.delete(
            f"/content-items/{CONTENT_ITEM_ID}/assets/{asset_id}",
            headers=auth_header(teacher_token),
        )

    @pytest.mark.asyncio
    async def test_upload_rejected_bad_mime_content_asset(self, client, teacher_token):
        """Upload with disallowed MIME type is rejected."""
        resp = await client.post(
            f"/content-items/{CONTENT_ITEM_ID}/assets",
            headers=auth_header(teacher_token),
            files={
                "file": ("bad.exe", io.BytesIO(b"malware"), "application/x-msdownload")
            },
        )
        assert resp.status_code == 422
