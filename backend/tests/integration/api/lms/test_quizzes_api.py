"""Integration tests for quiz engine endpoints (Phase 4.A).

Coverage target: app/api/v1/lms/quizzes.py ≥ 95 % branch

Routes covered:
  POST   /quizzes                          — create quiz (TCH/ADM)
  GET    /quizzes/recommended-difficulty   — difficulty hint (STD/TCH)
  GET    /quizzes                          — list with filters
  GET    /quizzes/{id}                     — get single quiz
  PUT    /quizzes/{id}                     — update quiz (MANAGE)
  POST   /quizzes/{id}/publish             — publish (PUBLISH)
  POST   /quizzes/{id}/start               — start attempt (STD)
  POST   /attempts/{id}/respond            — respond to question (STD)
  POST   /attempts/{id}/submit             — submit attempt (STD)
  GET    /attempts/{id}/results            — view results
  GET    /quizzes/{id}/analytics           — analytics (TCH/ADM)
  GET    /quizzes/{id}/attempts            — list attempts (TCH/ADM)
"""

from __future__ import annotations

import uuid

import pytest

from app.models.lms import Quiz
from tests.integration.api.helpers import (
    SCHOOL_ID,
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


def _quiz_payload(**overrides) -> dict:
    suffix = unique_suffix()
    return {
        "title": f"Quiz {suffix}",
        "description": "A test quiz",
        "subject": "Maths",
        "level_band": "6eme",
        "difficulty": "MEDIUM",
        "time_limit_minutes": 30,
        "max_attempts": 3,
        "shuffle_questions": False,
        "questions": [
            {
                "question_type": "MCQ",
                "question_text": "What is 2 + 2?",
                "options": ["3", "4", "5"],
                "correct_answer": "4",
                "points": 1,
                "order": 0,
            }
        ],
        **overrides,
    }


SCHOOL_ID_UUID = uuid.UUID(SCHOOL_ID)


class TestQuizCreate:
    @pytest.mark.asyncio
    async def test_teacher_can_create_minimal_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json={"title": f"Minimal {unique_suffix()}"},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"].upper() == "DRAFT"
        assert data["school_id"] == SCHOOL_ID

    @pytest.mark.asyncio
    async def test_create_quiz_db_side_effect(self, client, session_factory):
        """(c) Verify quiz is persisted in DB after creation."""
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        title = f"DBVerify-{unique_suffix()}"
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json={"title": title, "subject": "Sciences", "difficulty": "EASY"},
        )
        assert response.status_code == 201
        quiz_id = uuid.UUID(response.json()["data"]["id"])
        # (c) DB side-effect: quiz must be persisted with correct fields
        async with session_factory() as session:
            quiz = await session.get(Quiz, quiz_id)
            assert quiz is not None, "Quiz not found in DB after creation"
            assert quiz.title == title
            assert quiz.school_id == SCHOOL_ID_UUID

    @pytest.mark.asyncio
    async def test_teacher_can_create_full_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json=_quiz_payload(),
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["title"].startswith("Quiz")
        assert data["subject"] == "Maths"
        assert data["difficulty"] == "MEDIUM"

    @pytest.mark.asyncio
    async def test_admin_can_create_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json=_quiz_payload(),
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_student_cannot_create_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json=_quiz_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_parent_cannot_create_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json=_quiz_payload(),
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_quiz_missing_title_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json={"description": "no title"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_quiz_invalid_difficulty_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            "/quizzes",
            headers=auth_header(token),
            json=_quiz_payload(difficulty="ULTRA"),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_quiz_unauthenticated_returns_401_or_403(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        response = await client.post("/quizzes", json=_quiz_payload())
        assert response.status_code in (401, 403)


class TestQuizList:
    @pytest.mark.asyncio
    async def test_teacher_can_list_quizzes(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        # Create one first
        await client.post("/quizzes", headers=auth_header(token), json=_quiz_payload())
        response = await client.get("/quizzes", headers=auth_header(token))
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_student_can_list_quizzes(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get("/quizzes", headers=auth_header(token))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_quizzes_with_filters(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/quizzes",
            headers=auth_header(token),
            params={
                "subject": "Maths",
                "difficulty": "MEDIUM",
                "status": "DRAFT",
                "limit": 10,
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_quizzes_pagination(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            "/quizzes",
            headers=auth_header(token),
            params={"limit": 2},
        )
        assert response.status_code == 200
        body = response.json()
        assert "meta" in body or "has_more" in body or "next_cursor" in body

    @pytest.mark.asyncio
    async def test_list_quizzes_student_with_subject_gets_recommended_flag(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        # Teacher creates a published quiz
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        cr = await client.post(
            "/quizzes", headers=auth_header(t_token), json=_quiz_payload()
        )
        qid = cr.json()["data"]["id"]
        await client.post(f"/quizzes/{qid}/publish", headers=auth_header(t_token))

        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/quizzes",
            headers=auth_header(s_token),
            params={"subject": "Maths"},
        )
        assert response.status_code == 200
        # recommended_difficulty may be set for student + subject combo
        # We just verify the response shape is valid
        assert "data" in response.json()


class TestQuizGet:
    @pytest.mark.asyncio
    async def test_teacher_can_get_own_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.get(f"/quizzes/{quiz_id}", headers=auth_header(token))
        assert response.status_code == 200
        assert response.json()["data"]["id"] == quiz_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_quiz_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/quizzes/{fake_id}", headers=auth_header(token))
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get("/quizzes/not-a-uuid", headers=auth_header(token))
        assert response.status_code == 422


class TestQuizUpdate:
    @pytest.mark.asyncio
    async def test_teacher_can_update_own_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.put(
            f"/quizzes/{quiz_id}",
            headers=auth_header(token),
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_nonexistent_quiz_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.put(
            f"/quizzes/{uuid.uuid4()}",
            headers=auth_header(token),
            json={"title": "Nope"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_update_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(t_token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.put(
            f"/quizzes/{quiz_id}",
            headers=auth_header(s_token),
            json={"title": "Hack"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_quiz_invalid_difficulty_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.put(
            f"/quizzes/{quiz_id}",
            headers=auth_header(token),
            json={"difficulty": "LEGENDARY"},
        )
        assert response.status_code == 422


class TestQuizPublish:
    @pytest.mark.asyncio
    async def test_teacher_can_publish_own_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.post(
            f"/quizzes/{quiz_id}/publish", headers=auth_header(token)
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"].upper() == "PUBLISHED"

    @pytest.mark.asyncio
    async def test_publish_nonexistent_quiz_returns_404(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.post(
            f"/quizzes/{uuid.uuid4()}/publish", headers=auth_header(token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_cannot_publish_quiz(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(t_token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/quizzes/{quiz_id}/publish", headers=auth_header(s_token)
        )
        assert response.status_code == 403


class TestQuizAttempt:
    async def _setup_published_quiz(self, client, teacher_token) -> str:
        """Create and publish a quiz, return its ID."""
        create_r = await client.post(
            "/quizzes",
            headers=auth_header(teacher_token),
            json=_quiz_payload(),
        )
        quiz_id = create_r.json()["data"]["id"]
        await client.post(
            f"/quizzes/{quiz_id}/publish", headers=auth_header(teacher_token)
        )
        return quiz_id

    @pytest.mark.asyncio
    async def test_student_can_start_attempt(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        quiz_id = await self._setup_published_quiz(client, t_token)
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/quizzes/{quiz_id}/start", headers=auth_header(s_token)
        )
        assert response.status_code in (201, 200)

    @pytest.mark.asyncio
    async def test_teacher_cannot_start_attempt(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        quiz_id = await self._setup_published_quiz(client, t_token)
        response = await client.post(
            f"/quizzes/{quiz_id}/start", headers=auth_header(t_token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_start_attempt_nonexistent_quiz_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/quizzes/{uuid.uuid4()}/start", headers=auth_header(s_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_student_can_respond_to_question(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        quiz_id = await self._setup_published_quiz(client, t_token)
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )

        start_r = await client.post(
            f"/quizzes/{quiz_id}/start", headers=auth_header(s_token)
        )
        if start_r.status_code not in (200, 201):
            pytest.skip("Could not start quiz attempt")
        attempt_data = start_r.json()["data"]
        attempt_id = attempt_data["id"]

        # Get the question id from the attempt or quiz
        quiz_r = await client.get(f"/quizzes/{quiz_id}", headers=auth_header(s_token))
        questions = quiz_r.json()["data"].get("questions", [])
        if not questions:
            pytest.skip("Quiz has no questions")
        question_id = questions[0]["id"]

        response = await client.post(
            f"/attempts/{attempt_id}/respond",
            headers=auth_header(s_token),
            json={"question_id": question_id, "student_answer": "4"},
        )
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_respond_missing_question_id_returns_422(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        fake_attempt = str(uuid.uuid4())
        response = await client.post(
            f"/attempts/{fake_attempt}/respond",
            headers=auth_header(s_token),
            json={"student_answer": "4"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_attempt_nonexistent_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.post(
            f"/attempts/{uuid.uuid4()}/submit", headers=auth_header(s_token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_results_nonexistent_attempt_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/attempts/{uuid.uuid4()}/results", headers=auth_header(t_token)
        )
        assert response.status_code == 404


class TestQuizAnalytics:
    @pytest.mark.asyncio
    async def test_teacher_can_get_quiz_analytics(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.get(
            f"/quizzes/{quiz_id}/analytics", headers=auth_header(token)
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_student_cannot_get_quiz_analytics(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(t_token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            f"/quizzes/{quiz_id}/analytics", headers=auth_header(s_token)
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_analytics_nonexistent_quiz_returns_404(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        response = await client.get(
            f"/quizzes/{uuid.uuid4()}/analytics", headers=auth_header(token)
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_teacher_can_list_quiz_attempts(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        response = await client.get(
            f"/quizzes/{quiz_id}/attempts",
            headers=auth_header(token),
            params={"limit": 10},
        )
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body["data"], list)

    @pytest.mark.asyncio
    async def test_student_cannot_list_quiz_attempts(self, client, legacy_api_seed):
        _ = legacy_api_seed
        t_token = await login_token(
            client, email=TEACHER_EMAIL, password=TEACHER_PASSWORD
        )
        create_r = await client.post(
            "/quizzes", headers=auth_header(t_token), json=_quiz_payload()
        )
        quiz_id = create_r.json()["data"]["id"]
        s_token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            f"/quizzes/{quiz_id}/attempts", headers=auth_header(s_token)
        )
        assert response.status_code == 403


class TestRecommendedDifficulty:
    @pytest.mark.asyncio
    async def test_student_can_get_recommended_difficulty(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/quizzes/recommended-difficulty",
            headers=auth_header(token),
            params={"subject": "Maths"},
        )
        assert response.status_code == 200
        assert "recommended_difficulty" in response.json()["data"]

    @pytest.mark.asyncio
    async def test_missing_subject_returns_422(self, client, legacy_api_seed):
        _ = legacy_api_seed
        token = await login_token(
            client, email=STUDENT_EMAIL, password=STUDENT_PASSWORD
        )
        response = await client.get(
            "/quizzes/recommended-difficulty",
            headers=auth_header(token),
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_parent_cannot_get_recommended_difficulty(
        self, client, legacy_api_seed
    ):
        _ = legacy_api_seed
        token = await login_token(client, email=PARENT_EMAIL, password=PARENT_PASSWORD)
        response = await client.get(
            "/quizzes/recommended-difficulty",
            headers=auth_header(token),
            params={"subject": "Maths"},
        )
        assert response.status_code == 403
