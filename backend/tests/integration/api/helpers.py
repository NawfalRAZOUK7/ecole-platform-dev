"""Shared helpers for API integration tests."""

from __future__ import annotations

import uuid

import httpx

SCHOOL_ID = "00000000-0000-4000-8000-000000000001"
YEAR_ID = "20000000-0000-4000-8000-000000000001"
PERIOD_ID = "20000000-0000-4000-8000-000000000003"
CLASS_ID = "20000000-0000-4000-8000-000000000004"
STUDENT_ID = "10000000-0000-4000-8000-000000000007"
INVOICE_ID = "40000000-0000-4000-8000-000000000001"

SUPERADMIN_EMAIL = "superadmin@ecole-platform.ma"
SUPERADMIN_PASSWORD = "superadmin123"


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login_token(
    client: httpx.AsyncClient,
    *,
    email: str,
    password: str,
    school_id: str = SCHOOL_ID,
) -> str:
    response = await client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
            "school_id": school_id,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]["access_token"]


def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]
