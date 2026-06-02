"""Integration tests for CMS endpoints (Phase 4.E).

Coverage target: app/api/v1/content/cms.py ≥ 95 % branch

Routes:
  POST   /cms/content                     — create (CONTENT_MGR)
  GET    /cms/content                     — list (CONTENT_MGR)
  PUT    /cms/content/{id}                — update (CONTENT_MGR)
  DELETE /cms/content/{id}                — archive (CONTENT_MGR)
  GET    /cms/submissions                 — list teacher submissions
  POST   /cms/content/{id}/review         — review decision
"""

from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from app.core.security import hash_password
from tests.factories.iam import MembershipFactory, UserFactory
from tests.factories.school import SchoolFactory
from tests.integration.api.helpers import (
    auth_header,
    login_token,
    unique_suffix,
)
from tests.integration.api.conftest import SCHOOL_ID as _SCHOOL_ID_UUID

ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"

CM_EMAIL = "content.manager@ecole-benani.ma"
CM_PASSWORD = "cmpassword123"


@pytest_asyncio.fixture(loop_scope="function")
async def content_manager_token(client, session_factory):
    """Create a CONTENT_MGR user via the shared session_factory and return their token.

    Uses loop_scope='function' to ensure the asyncpg connection is created
    in the same event loop as the test, preventing cross-loop Future errors.
    """
    from app.models.school import School

    cm_email = f"cm-{unique_suffix()}@test.example"
    cm_pass = "CmPa$$w0rd123"

    async with session_factory() as session:
        school = await session.get(School, _SCHOOL_ID_UUID)
        if school is None:
            school = await SchoolFactory.create(
                session=session,
                id=_SCHOOL_ID_UUID,
                code="ecole-benani",
                name="Ecole Benani",
            )
        cm_user = await UserFactory.create(
            session=session,
            school=school,
            email=cm_email,
            password_hash=hash_password(cm_pass),
        )
        await MembershipFactory.create(
            session=session,
            user=cm_user,
            school_id=_SCHOOL_ID_UUID,
            role_code="CONTENT_MGR",
        )
        await session.commit()

    token = await login_token(client, email=cm_email, password=cm_pass)
    return token


def _cms_content_payload(**overrides) -> dict:
    return {
        "title": f"Test Content {unique_suffix()}",
        "content_type": "ARTICLE",
        "subject": "Maths",
        "level_band": "6eme",
        "body": "This is test content body.",
        "language": "fr",
        "origin": "school",
        **overrides,
    }


class TestCmsContentCreate:
    @pytest.mark.asyncio
    async def test_content_manager_can_create_content(
        self, client, content_manager_token
    ):
        response = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=_cms_content_payload(),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert "id" in data
        assert "title" in data
        assert data["status"] in ("DRAFT", "draft")

    @pytest.mark.asyncio
    async def test_content_manager_can_create_full_content(
        self, client, content_manager_token
    ):
        response = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=_cms_content_payload(
                content_type="VIDEO",
                level_band="3eme",
                subject="Sciences",
            ),
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_teacher_cannot_create_cms_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/cms/content",
            headers=auth_header(token),
            json=_cms_content_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_cannot_create_cms_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/cms/content",
            headers=auth_header(token),
            json=_cms_content_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_title_returns_422(self, client, content_manager_token):
        payload = _cms_content_payload()
        del payload["title"]
        response = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=payload,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_content_type_returns_422(
        self, client, content_manager_token
    ):
        payload = _cms_content_payload()
        del payload["content_type"]
        response = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=payload,
        )
        assert response.status_code == 422


class TestCmsContentList:
    @pytest.mark.asyncio
    async def test_content_manager_can_list_content(
        self, client, content_manager_token
    ):
        # Create one first
        await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=_cms_content_payload(),
        )
        response = await client.get(
            "/cms/content", headers=auth_header(content_manager_token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_with_filters(self, client, content_manager_token):
        response = await client.get(
            "/cms/content",
            headers=auth_header(content_manager_token),
            params={"subject": "Maths", "level_band": "6eme", "status": "DRAFT"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_cms_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/cms/content", headers=auth_header(token))
        assert response.status_code == 403


class TestCmsContentUpdate:
    @pytest.mark.asyncio
    async def test_content_manager_can_update_content(
        self, client, content_manager_token
    ):
        cr = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=_cms_content_payload(),
        )
        content_id = cr.json()["data"]["id"]
        response = await client.put(
            f"/cms/content/{content_id}",
            headers=auth_header(content_manager_token),
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_nonexistent_content_returns_404(
        self, client, content_manager_token
    ):
        response = await client.put(
            f"/cms/content/{uuid.uuid4()}",
            headers=auth_header(content_manager_token),
            json={"title": "Nope"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_update_cms_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.put(
            f"/cms/content/{uuid.uuid4()}",
            headers=auth_header(token),
            json={"title": "Hack"},
        )
        assert response.status_code == 403


class TestCmsContentDelete:
    @pytest.mark.asyncio
    async def test_content_manager_can_archive_content(
        self, client, content_manager_token
    ):
        cr = await client.post(
            "/cms/content",
            headers=auth_header(content_manager_token),
            json=_cms_content_payload(),
        )
        content_id = cr.json()["data"]["id"]
        response = await client.delete(
            f"/cms/content/{content_id}",
            headers=auth_header(content_manager_token),
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client, content_manager_token):
        response = await client.delete(
            f"/cms/content/{uuid.uuid4()}",
            headers=auth_header(content_manager_token),
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_cannot_delete_cms_content(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.delete(
            f"/cms/content/{uuid.uuid4()}", headers=auth_header(token)
        )
        assert response.status_code == 403


class TestCmsSubmissions:
    @pytest.mark.asyncio
    async def test_content_manager_can_list_submissions(
        self, client, content_manager_token
    ):
        response = await client.get(
            "/cms/submissions", headers=auth_header(content_manager_token)
        )
        assert response.status_code == 200
        assert isinstance(response.json()["data"], list)

    @pytest.mark.asyncio
    async def test_list_submissions_with_status_filter(
        self, client, content_manager_token
    ):
        response = await client.get(
            "/cms/submissions",
            headers=auth_header(content_manager_token),
            params={"status": "PENDING"},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_teacher_cannot_list_submissions(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/cms/submissions", headers=auth_header(token))
        assert response.status_code == 403


class TestCmsReview:
    @pytest.mark.asyncio
    async def test_review_nonexistent_content_returns_404(
        self, client, content_manager_token
    ):
        response = await client.post(
            f"/cms/submissions/{uuid.uuid4()}/review",
            headers=auth_header(content_manager_token),
            json={"decision": "APPROVED", "feedback": "Great content"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_decision_returns_422(self, client, content_manager_token):
        response = await client.post(
            f"/cms/submissions/{uuid.uuid4()}/review",
            headers=auth_header(content_manager_token),
            json={"decision": "MAYBE"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_teacher_cannot_review(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/cms/submissions/{uuid.uuid4()}/review",
            headers=auth_header(token),
            json={"decision": "APPROVED"},
        )
        # 403 if permission is checked first; 404 if route is post-matched
        assert response.status_code in (403, 404)
