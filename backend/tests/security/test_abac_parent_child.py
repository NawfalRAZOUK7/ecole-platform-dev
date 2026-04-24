"""Parent-child ABAC coverage for grades, attendance, billing, and documents."""

from __future__ import annotations

import pytest
import pytest_asyncio

from .conftest import SCHOOL_ID, STUDENT_ID, YEAR_ID, auth_header


PARENT_TOKEN_CASES = [
    ("active", 200),
    ("unlinked", 404),
    ("revoked", 404),
]


@pytest_asyncio.fixture(loop_scope="function")
async def parent_tokens(
    parent_token,
    unlinked_parent_token,
    revoked_parent_token,
) -> dict[str, str]:
    return {
        "active": parent_token,
        "unlinked": unlinked_parent_token,
        "revoked": revoked_parent_token,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("token_key,expected_status", PARENT_TOKEN_CASES)
async def test_parent_transcript_access(
    client,
    parent_tokens,
    grade_category_id,
    token_key: str,
    expected_status: int,
):
    token = parent_tokens[token_key]
    response = await client.get(
        f"/gradebook/transcript/{STUDENT_ID}",
        headers=auth_header(token),
        params={"academic_year_id": YEAR_ID},
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("token_key,expected_status", PARENT_TOKEN_CASES)
async def test_parent_fee_assignment_access(
    client,
    parent_tokens,
    token_key: str,
    expected_status: int,
):
    token = parent_tokens[token_key]
    response = await client.get(
        "/billing/fee-assignments",
        headers=auth_header(token),
        params={"student_id": STUDENT_ID},
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("token_key,expected_status", PARENT_TOKEN_CASES)
async def test_parent_student_documents_access(
    client,
    parent_tokens,
    token_key: str,
    expected_status: int,
):
    token = parent_tokens[token_key]
    response = await client.get(
        f"/students/{STUDENT_ID}/documents",
        headers=auth_header(token),
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("token_key,expected_status", PARENT_TOKEN_CASES)
async def test_parent_document_checklist_access(
    client,
    parent_tokens,
    token_key: str,
    expected_status: int,
):
    token = parent_tokens[token_key]
    response = await client.get(
        f"/students/{STUDENT_ID}/documents/checklist",
        headers=auth_header(token),
    )

    assert response.status_code == expected_status, response.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "token_key,expected_status",
    [
        ("active", 201),
        ("unlinked", 404),
        ("revoked", 404),
    ],
)
async def test_parent_attendance_justification_access(
    client,
    parent_tokens,
    token_key: str,
    expected_status: int,
    absence_record_id,
):
    token = parent_tokens[token_key]
    response = await client.post(
        "/attendance/justifications",
        headers=auth_header(token),
        data={
            "attendance_record_id": str(absence_record_id),
            "reason": "Absence justifiee par un parent de test",
        },
    )

    assert response.status_code == expected_status, response.text
    if expected_status == 201:
        payload = response.json()["data"]
        assert payload["attendance_record_id"] == str(absence_record_id)
        assert payload["school_id"] == SCHOOL_ID
