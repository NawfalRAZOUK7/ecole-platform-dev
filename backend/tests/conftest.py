"""Shared test fixtures for integration tests.

Uses the actual database and Redis instances running in Docker.
Seed data must be loaded before running tests (make seed).
"""

from __future__ import annotations

import uuid

import httpx
import pytest
import pytest_asyncio

# Fixed IDs from seed.py
SCHOOL_ID = "00000000-0000-4000-8000-000000000001"
ADMIN_EMAIL = "admin@ecole-benani.ma"
ADMIN_PASSWORD = "admin123"
TEACHER_EMAIL = "prof.math@ecole-benani.ma"
TEACHER_PASSWORD = "teacher123"
PARENT_EMAIL = "parent.alaoui@gmail.com"
PARENT_PASSWORD = "parent123"
STUDENT_EMAIL = "yassine.alaoui@ecole-benani.ma"
STUDENT_PASSWORD = "student123"

BASE_URL = "http://localhost:8000/api/v1"


@pytest.fixture
def base_url():
    return BASE_URL


@pytest.fixture
def school_id():
    return SCHOOL_ID


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for integration tests."""
    async with httpx.AsyncClient(base_url=BASE_URL) as c:
        yield c


@pytest_asyncio.fixture
async def admin_token(client: httpx.AsyncClient) -> str:
    """Get an admin access token."""
    response = await client.post(
        "/auth/login",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "school_id": SCHOOL_ID,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def teacher_token(client: httpx.AsyncClient) -> str:
    """Get a teacher access token."""
    response = await client.post(
        "/auth/login",
        json={
            "email": TEACHER_EMAIL,
            "password": TEACHER_PASSWORD,
            "school_id": SCHOOL_ID,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def student_token(client: httpx.AsyncClient) -> str:
    """Get a student access token."""
    response = await client.post(
        "/auth/login",
        json={
            "email": STUDENT_EMAIL,
            "password": STUDENT_PASSWORD,
            "school_id": SCHOOL_ID,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def parent_token(client: httpx.AsyncClient) -> str:
    """Get a parent access token."""
    response = await client.post(
        "/auth/login",
        json={
            "email": PARENT_EMAIL,
            "password": PARENT_PASSWORD,
            "school_id": SCHOOL_ID,
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]
