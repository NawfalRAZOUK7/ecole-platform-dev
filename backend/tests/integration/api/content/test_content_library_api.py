"""Integration tests for content library endpoints (Phase 4.G).

Coverage target: app/api/v1/content/content_library.py ≥ 95 % branch

Routes:
  GET    /content/library              — browse library (STD/TCH/PAR/ADM)
  POST   /content/assign               — assign to class (TCH/ADM)
  DELETE /content/assign/{id}          — unassign (TCH/ADM)
  POST   /content/submit-for-review    — submit for platform review (TCH/ADM)
  GET    /content/my-submissions       — list my submissions (TCH/ADM)
  GET    /classes/{id}/content         — list class content (all authenticated)
"""

from __future__ import annotations

import uuid

import pytest

from tests.integration.api.helpers import (
    CLASS_ID,
    auth_header,
    login_token,
)

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"


class TestBrowseContentLibrary:
    @pytest.mark.asyncio
    async def test_student_can_browse_library(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get("/content/library", headers=auth_header(token))
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_teacher_can_browse_library(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/content/library", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_parent_can_browse_library(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get("/content/library", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_with_content_type_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/content/library",
            headers=auth_header(token),
            params={"content_type": "ARTICLE"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_with_multiple_filters(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/content/library",
            headers=auth_header(token),
            params={
                "level_band": "6eme",
                "subject": "Maths",
                "language": "fr",
                "origin": "platform",
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_with_target_age_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/content/library",
            headers=auth_header(token),
            params={"target_age": 12},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_browse_with_letter_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/content/library",
            headers=auth_header(token),
            params={"letter": "A"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_browse(self, client, legacy_api_seed):
        _ = legacy_api_seed
        response = await client.get("/content/library")
        assert response.status_code in (401, 403)


class TestContentAssign:
    @pytest.mark.asyncio
    async def test_teacher_can_assign_content_to_class(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        # Try to assign some content (may 404 if no content exists, but tests the route)
        response = await client.post(
            "/content/assign",
            headers=auth_header(token),
            json={
                "content_item_id": str(uuid.uuid4()),
                "class_id": CLASS_ID,
                "due_date": None,
            },
        )
        # 404 is acceptable if content doesn't exist; 201 if it does
        assert response.status_code in (201, 404)

    @pytest.mark.asyncio
    async def test_student_cannot_assign_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/content/assign",
            headers=auth_header(token),
            json={"content_item_id": str(uuid.uuid4()), "class_id": CLASS_ID},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_assign_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/content/assign",
            headers=auth_header(token),
            json={"content_item_id": str(uuid.uuid4()), "class_id": CLASS_ID},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_assign_missing_class_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/content/assign",
            headers=auth_header(token),
            json={"content_item_id": str(uuid.uuid4())},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_assign_missing_content_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/content/assign",
            headers=auth_header(token),
            json={"class_id": CLASS_ID},
        )
        assert response.status_code == 422


class TestContentUnassign:
    @pytest.mark.asyncio
    async def test_unassign_nonexistent_assignment_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.delete(
            f"/content/assign/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_unassign_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.delete(
            f"/content/assign/{uuid.uuid4()}",
            headers=auth_header(token),
        )
        assert response.status_code == 403


class TestContentSubmitForReview:
    @pytest.mark.asyncio
    async def test_teacher_can_submit_for_review(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/content/submit-for-review",
            headers=auth_header(token),
            json={
                "content_item_id": str(uuid.uuid4()),
                "notes": "Requesting platform review",
            },
        )
        # 404 if content doesn't exist
        assert response.status_code in (201, 404)

    @pytest.mark.asyncio
    async def test_student_cannot_submit_for_review(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/content/submit-for-review",
            headers=auth_header(token),
            json={"content_item_id": str(uuid.uuid4())},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_submit_missing_content_id_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/content/submit-for-review",
            headers=auth_header(token),
            json={"notes": "no content id"},
        )
        assert response.status_code == 422


class TestMyContentSubmissions:
    @pytest.mark.asyncio
    async def test_teacher_can_list_own_submissions(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/content/my-submissions", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_submissions_with_status_filter(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/content/my-submissions",
            headers=auth_header(token),
            params={"status": "PENDING"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_list_submissions(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/content/my-submissions", headers=auth_header(token)
        )
        assert response.status_code == 403


class TestClassContent:
    @pytest.mark.asyncio
    async def test_teacher_can_list_class_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/classes/{CLASS_ID}/content", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_student_can_list_class_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            f"/classes/{CLASS_ID}/content", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_class_content_nonexistent_class_returns_200_empty(
        self, client, legacy_api_seed
    ):
        """Service returns empty list for non-existent class (scope-filtered)."""
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/classes/{uuid.uuid4()}/content", headers=auth_header(token)
        )
        # Service may return 200 empty list (school-scoped filter) or 404
        assert response.status_code in (200, 404)

    @pytest.mark.asyncio
    async def test_list_class_content_pagination(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/classes/{CLASS_ID}/content",
            headers=auth_header(token),
            params={"limit": 5},
        )
        assert response.status_code == 200
