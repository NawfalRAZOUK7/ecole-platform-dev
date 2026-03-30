"""Teacher-class ABAC tests for grading scope."""

from __future__ import annotations

import pytest

from .conftest import auth_header


GRADE_BODY = {
    "score": 18,
    "feedback_text": "Evaluation securite",
    "publish": False,
}


@pytest.mark.asyncio
async def test_teacher_can_grade_own_course_submission(
    client,
    teacher_token,
    teacher_owned_submission,
):
    response = await client.post(
        f"/submissions/{teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(teacher_token),
        json=GRADE_BODY,
    )

    assert response.status_code == 201, response.text
    assert response.json()["data"]["submission_id"] == str(
        teacher_owned_submission["submission_id"]
    )


@pytest.mark.asyncio
async def test_teacher_can_update_grade_for_own_course(
    client,
    teacher_token,
    teacher_owned_submission,
):
    first_response = await client.post(
        f"/submissions/{teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(teacher_token),
        json=GRADE_BODY,
    )
    assert first_response.status_code == 201, first_response.text

    response = await client.post(
        f"/submissions/{teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(teacher_token),
        json={
            "score": 19,
            "feedback_text": "Mise a jour par le bon enseignant",
            "publish": True,
        },
    )

    assert response.status_code == 201, response.text
    assert float(response.json()["data"]["score"]) <= 19.0


@pytest.mark.asyncio
async def test_other_teacher_cannot_grade_submission_outside_scope(
    client,
    other_teacher_token,
    teacher_owned_submission,
):
    response = await client.post(
        f"/submissions/{teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(other_teacher_token),
        json=GRADE_BODY,
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_other_teacher_can_grade_own_course_submission(
    client,
    other_teacher_token,
    other_teacher_owned_submission,
):
    response = await client.post(
        f"/submissions/{other_teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(other_teacher_token),
        json=GRADE_BODY,
    )

    assert response.status_code == 201, response.text


@pytest.mark.asyncio
async def test_seed_teacher_cannot_grade_other_teacher_course(
    client,
    teacher_token,
    other_teacher_owned_submission,
):
    response = await client.post(
        f"/submissions/{other_teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(teacher_token),
        json=GRADE_BODY,
    )

    assert response.status_code == 403, response.text


@pytest.mark.asyncio
async def test_teacher_can_preview_own_submission_scope(
    client,
    teacher_token,
    teacher_owned_submission,
):
    response = await client.get(
        f"/submissions/{teacher_owned_submission['submission_id']}/preview",
        headers=auth_header(teacher_token),
    )

    assert response.status_code == 200, response.text
    assert response.json()["data"]["submission_id"] == str(
        teacher_owned_submission["submission_id"]
    )


@pytest.mark.asyncio
async def test_other_teacher_cannot_preview_submission_outside_scope(
    client,
    other_teacher_token,
    teacher_owned_submission,
):
    response = await client.get(
        f"/submissions/{teacher_owned_submission['submission_id']}/preview",
        headers=auth_header(other_teacher_token),
    )

    assert response.status_code == 404, response.text


@pytest.mark.asyncio
async def test_seed_teacher_cannot_override_penalty_for_other_teacher_course(
    client,
    teacher_token,
    other_teacher_token,
    other_teacher_owned_submission,
):
    grade_response = await client.post(
        f"/submissions/{other_teacher_owned_submission['submission_id']}/grade",
        headers=auth_header(other_teacher_token),
        json=GRADE_BODY,
    )
    assert grade_response.status_code == 201, grade_response.text

    response = await client.post(
        f"/submissions/{other_teacher_owned_submission['submission_id']}/override-penalty",
        headers=auth_header(teacher_token),
    )

    assert response.status_code == 403, response.text
