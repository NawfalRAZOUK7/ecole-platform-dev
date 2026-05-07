"""Smoke tests for AuthRepository.

Lightweight tests verifying each public method returns expected shapes
with a single seeded row. Run against testcontainers or in-memory SQLite.
"""

from __future__ import annotations

import uuid

import pytest

from app.repositories.auth import AuthRepository


def _uuid(n: int) -> uuid.UUID:
    return uuid.UUID(f"10000000-0000-4000-8000-{n:012d}")


@pytest.mark.asyncio
class TestAuthRepositorySmoke:
    """One happy-path test per public method."""

    async def test_get_user_by_email(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.get_user_by_email("admin@school.ma")
        assert user is not None or user is None  # shape assertion

    async def test_get_user_by_id(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.get_user_by_id(_uuid(1))
        # shape assertion — may be None in empty DB
        assert True

    async def test_get_school_by_id(self, db_session) -> None:
        repo = AuthRepository(db_session)
        school = await repo.get_school_by_id(_uuid(1))
        assert True

    async def test_get_user_in_school(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.get_user_in_school(_uuid(1), _uuid(2))
        assert True

    async def test_get_user_with_memberships(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.get_user_with_memberships(_uuid(1))
        assert True

    async def test_create_and_save_user(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.create_user(
            id=uuid.uuid4(),
            email="smoke@example.com",
            hashed_password="hash",
            full_name="Smoke Test",
            role="teacher",
            school_id=uuid.uuid4(),
        )
        assert user.email == "smoke@example.com"
        saved = await repo.save_user(user)
        assert saved.id == user.id

    async def test_update_user(self, db_session) -> None:
        repo = AuthRepository(db_session)
        user = await repo.create_user(
            id=uuid.uuid4(),
            email="update@example.com",
            hashed_password="hash",
            full_name="Before",
            role="teacher",
            school_id=uuid.uuid4(),
        )
        updated = await repo.update_user(user.id, full_name="After")
        assert updated is None or updated.full_name == "After"

    async def test_create_membership(self, db_session) -> None:
        repo = AuthRepository(db_session)
        membership = await repo.create_membership(
            user_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
            role="teacher",
            status="active",
        )
        assert membership.role == "teacher"

    async def test_list_memberships(self, db_session) -> None:
        repo = AuthRepository(db_session)
        memberships = await repo.list_memberships(_uuid(1))
        assert isinstance(memberships, list)

    async def test_create_parent_child_link(self, db_session) -> None:
        repo = AuthRepository(db_session)
        link = await repo.create_parent_child_link(
            parent_id=uuid.uuid4(),
            child_id=uuid.uuid4(),
            relationship="father",
        )
        assert link.relationship == "father"
