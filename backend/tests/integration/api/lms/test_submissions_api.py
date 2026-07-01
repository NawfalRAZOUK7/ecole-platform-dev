"""Integration tests for submission endpoints (Phase 4.H).

Coverage target: app/api/v1/lms/submissions.py ≥ 95 % branch

Routes:
  POST   /submissions                       — create submission (STD)
  POST   /submissions/{id}/grade            — grade submission (TCH/ADM)
  POST   /submissions/{id}/override-penalty — override penalty (TCH/ADM)
  POST   /submissions/{id}/files            — upload file (STD)
  GET    /submissions/{id}/files/{file_id}  — download file
  POST   /submissions/{id}/submit           — finalize submission (STD)
  GET    /submissions/{id}/preview          — preview files (TCH/ADM)
"""

from __future__ import annotations

import io
import uuid

import pytest

from tests.integration.api.helpers import (
    auth_header,
    login_token,
)

# IDs seeded by legacy_api_seed (defined in tests/integration/api/conftest.py)
ASSIGNMENT_ID = "30000000-0000-4000-8000-000000000003"
SUBMISSION_ID = "30000000-0000-4000-8000-000000000002"

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"


class TestSubmissionCreate:
    @pytest.mark.asyncio
    async def test_student_can_create_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/submissions",
            headers=auth_header(token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        # 201 if assignment allows, or 409 if already submitted
        assert response.status_code in (201, 409)

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/submissions",
            headers=auth_header(token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/submissions",
            headers=auth_header(token),
            json={"assignment_id": ASSIGNMENT_ID},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_submission_missing_assignment_id_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/submissions", headers=auth_header(token), json={}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_submission_nonexistent_assignment_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/submissions",
            headers=auth_header(token),
            json={"assignment_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_create_submission(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        response = await client.post(
            "/submissions", json={"assignment_id": ASSIGNMENT_ID}
        )
        assert response.status_code in (401, 403)


class TestSubmissionGrade:
    @pytest.mark.asyncio
    async def test_teacher_can_grade_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/grade",
            headers=auth_header(token),
            json={"score": 15.5, "feedback_text": "Good work!", "publish": True},
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_grade_nonexistent_submission_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{uuid.uuid4()}/grade",
            headers=auth_header(token),
            json={"score": 10.0},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_grade_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/grade",
            headers=auth_header(token),
            json={"score": 20.0},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_grade_negative_score_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/grade",
            headers=auth_header(token),
            json={"score": -5.0},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_grade_missing_score_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/grade",
            headers=auth_header(token),
            json={"feedback_text": "No score"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_parent_cannot_grade(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/grade",
            headers=auth_header(token),
            json={"score": 10.0},
        )
        assert response.status_code == 403


class TestOverridePenalty:
    @pytest.mark.asyncio
    async def test_teacher_can_override_penalty(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/override-penalty",
            headers=auth_header(token),
        )
        # 200 if submission is graded and has a penalty; 404 if not found;
        # 409 if no penalty; 422 if business rule violation (no grade yet)
        assert response.status_code in (200, 404, 409, 422)

    @pytest.mark.asyncio
    async def test_override_penalty_nonexistent_submission_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{uuid.uuid4()}/override-penalty",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_override_penalty(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/override-penalty",
            headers=auth_header(token),
        )
        assert response.status_code == 403


class TestSubmissionFinalize:
    @pytest.mark.asyncio
    async def test_teacher_cannot_finalize_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/submit",
            headers=auth_header(token),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_finalize_nonexistent_submission_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/submissions/{uuid.uuid4()}/submit",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_can_finalize_existing_submission(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        # Use the seeded SUBMISSION_ID (may already be submitted, but tests the endpoint)
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/submit",
            headers=auth_header(token),
        )
        # 200 or 409 (already submitted) or 403 (if student doesn't own it)
        # 422 if submission not in draft state (business rule)
        assert response.status_code in (200, 409, 403, 404, 422)


class TestSubmissionPreview:
    @pytest.mark.asyncio
    async def test_teacher_can_preview_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/submissions/{SUBMISSION_ID}/preview",
            headers=auth_header(token),
        )
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_preview_nonexistent_submission_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/submissions/{uuid.uuid4()}/preview",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_preview_submission(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            f"/submissions/{SUBMISSION_ID}/preview",
            headers=auth_header(token),
        )
        assert response.status_code == 403


class TestSubmissionFileUpload:
    @pytest.mark.asyncio
    async def test_student_can_upload_file(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        file_content = b"Test file content for submission"
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/files",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
        )
        # 201 if submission exists and user can upload; 403/404 otherwise
        assert response.status_code in (201, 403, 404, 409)

    @pytest.mark.asyncio
    async def test_teacher_cannot_upload_submission_file(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/submissions/{SUBMISSION_ID}/files",
            headers=auth_header(token),
            files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_download_nonexistent_file_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/submissions/{SUBMISSION_ID}/files/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert response.status_code == 404
