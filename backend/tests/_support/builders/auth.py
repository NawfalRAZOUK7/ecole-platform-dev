"""Fluent builder for AuthContext objects used across unit tests.

Replaces the per-file ``make_auth`` helpers with one consistent builder::

    from tests._support.builders import AuthContextBuilder

    auth = AuthContextBuilder().as_role("SUP").build()
    adm  = AuthContextBuilder().as_admin().for_school(school.id).build()
"""

from __future__ import annotations

import uuid

from app.core.dependencies import AuthContext


class AuthContextBuilder:
    """Build an :class:`AuthContext` with sensible random defaults."""

    def __init__(self) -> None:
        self._user_id: uuid.UUID = uuid.uuid4()
        self._role: str = "STD"
        self._school_id: uuid.UUID = uuid.uuid4()
        self._session_id: uuid.UUID = uuid.uuid4()
        self._permissions: set[str] = set()

    def as_role(self, role: str) -> "AuthContextBuilder":
        self._role = role
        return self

    def as_admin(self) -> "AuthContextBuilder":
        return self.as_role("ADM")

    def as_superadmin(self) -> "AuthContextBuilder":
        return self.as_role("SUP")

    def as_teacher(self) -> "AuthContextBuilder":
        return self.as_role("TCH")

    def with_user(self, user_id: uuid.UUID) -> "AuthContextBuilder":
        self._user_id = user_id
        return self

    def for_school(self, school_id: uuid.UUID) -> "AuthContextBuilder":
        self._school_id = school_id
        return self

    def with_session(self, session_id: uuid.UUID) -> "AuthContextBuilder":
        self._session_id = session_id
        return self

    def with_permissions(self, *permissions: str) -> "AuthContextBuilder":
        self._permissions = set(permissions)
        return self

    def build(self) -> AuthContext:
        return AuthContext(
            user_id=self._user_id,
            role=self._role,
            school_id=self._school_id,
            session_id=self._session_id,
            permissions=self._permissions,
        )
