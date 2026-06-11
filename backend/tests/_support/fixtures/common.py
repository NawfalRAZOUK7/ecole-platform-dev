"""Reusable, broadly-applicable pytest fixtures.

Registered as a plugin from the root ``tests/conftest.py`` via
``pytest_plugins = ("tests._support.fixtures.common",)``, so these fixtures are
available everywhere without imports.

These are deliberately additive and do NOT shadow the existing
``admin_auth`` / ``sup_auth`` / ``*_auth`` fixtures already defined in
``tests/conftest.py``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from app.core.dependencies import AuthContext
from tests._support.builders import AuthContextBuilder, SchoolApplicationBuilder


@pytest.fixture
def auth_builder() -> AuthContextBuilder:
    """A fresh :class:`AuthContextBuilder` per test."""
    return AuthContextBuilder()


@pytest.fixture
def application_builder() -> SchoolApplicationBuilder:
    """A fresh :class:`SchoolApplicationBuilder` per test."""
    return SchoolApplicationBuilder()


@pytest.fixture
def build_auth() -> Callable[..., AuthContext]:
    """Factory fixture: ``build_auth(role="TCH", school_id=...)`` → AuthContext."""

    def _make(role: str = "STD", **overrides) -> AuthContext:
        builder = AuthContextBuilder().as_role(role)
        if "user_id" in overrides:
            builder.with_user(overrides["user_id"])
        if "school_id" in overrides:
            builder.for_school(overrides["school_id"])
        if "permissions" in overrides:
            builder.with_permissions(*overrides["permissions"])
        return builder.build()

    return _make
