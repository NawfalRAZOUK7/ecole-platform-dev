"""RBAC matrix tests for endpoint groups added after the legacy security suite."""

from __future__ import annotations

import pytest

from .conftest import CLASS_ID, PERIOD_ID, YEAR_ID, auth_header


ENDPOINT_CASES = [
    (
        "schools",
        "/schools",
        {},
        {
            "SYS": 404,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 403,
            "PAR": 403,
            "STD": 403,
            "CONTENT_MGR": 403,
        },
    ),
    (
        "gradebook",
        f"/gradebook/{CLASS_ID}/{PERIOD_ID}",
        {},
        {
            "SYS": 200,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 200,
            "PAR": 200,
            "STD": 200,
            "CONTENT_MGR": 403,
        },
    ),
    (
        "rubrics",
        "/rubrics",
        {},
        {
            "SYS": 200,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 200,
            "PAR": 403,
            "STD": 403,
            "CONTENT_MGR": 403,
        },
    ),
    (
        "question_bank",
        "/question-bank",
        {},
        {
            "SYS": 200,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 200,
            "PAR": 403,
            "STD": 403,
            "CONTENT_MGR": 200,
        },
    ),
    (
        "payment_plans",
        "/billing/payment-plans",
        {},
        {
            "SYS": 200,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 403,
            "PAR": 200,
            "STD": 403,
            "CONTENT_MGR": 403,
        },
    ),
    (
        "attendance_analytics",
        f"/analytics/attendance/class/{CLASS_ID}",
        {"period_id": PERIOD_ID},
        {
            "SYS": 200,
            "SUP": 200,
            "ADM": 200,
            "DIR": 200,
            "TCH": 200,
            "PAR": 403,
            "STD": 403,
            "CONTENT_MGR": 403,
        },
    ),
    (
        "timetable_generation",
        "/timetable/constraints",
        {"academic_year_id": YEAR_ID},
        {
            "SYS": 404,
            "SUP": 404,
            "ADM": 200,
            "DIR": 404,
            "TCH": 403,
            "PAR": 403,
            "STD": 403,
            "CONTENT_MGR": 403,
        },
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("group", "path", "params", "expected_by_role"),
    ENDPOINT_CASES,
    ids=[case[0] for case in ENDPOINT_CASES],
)
@pytest.mark.parametrize(
    "role",
    ["SYS", "SUP", "ADM", "DIR", "TCH", "PAR", "STD", "CONTENT_MGR"],
)
async def test_endpoint_group_rbac_matrix(
    client,
    admin_token,
    teacher_token,
    student_token,
    parent_token,
    superadmin_token,
    director_token,
    sys_token,
    content_mgr_token,
    group: str,
    path: str,
    params: dict[str, str],
    expected_by_role: dict[str, int],
    role: str,
):
    token_by_role = {
        "ADM": admin_token,
        "CONTENT_MGR": content_mgr_token,
        "DIR": director_token,
        "PAR": parent_token,
        "STD": student_token,
        "SUP": superadmin_token,
        "SYS": sys_token,
        "TCH": teacher_token,
    }

    response = await client.get(
        path,
        headers=auth_header(token_by_role[role]),
        params=params,
    )

    assert (
        response.status_code == expected_by_role[role]
    ), f"{group} {role} expected {expected_by_role[role]}, got {response.status_code}: {response.text}"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("group", "path", "params"),
    [(case[0], case[1], case[2]) for case in ENDPOINT_CASES],
    ids=[case[0] for case in ENDPOINT_CASES],
)
async def test_endpoint_group_requires_token(
    client,
    group: str,
    path: str,
    params: dict[str, str],
):
    response = await client.get(path, params=params)

    assert (
        response.status_code == 401
    ), f"{group} expected 401, got {response.status_code}"
