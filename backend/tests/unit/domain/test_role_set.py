"""Unit tests for RoleSet."""

from __future__ import annotations

import pytest

from app.domain.value_objects.role_set import ROLE_COMPATIBILITY, RoleSet, VALID_ROLES


class TestRoleSet:
    def test_valid_single_role(self):
        role_set = RoleSet(frozenset({"ADM"}))

        assert role_set.roles == frozenset({"ADM"})

    def test_valid_multiple_roles(self):
        role_set = RoleSet(frozenset({"ADM", "TCH"}))

        assert role_set.roles == frozenset({"ADM", "TCH"})

    def test_invalid_role_code_raises(self):
        with pytest.raises(ValueError, match="Invalid roles"):
            RoleSet(frozenset({"INVALID"}))

    def test_has_true(self):
        assert RoleSet(frozenset({"ADM", "TCH"})).has("ADM") is True

    def test_has_false(self):
        assert RoleSet(frozenset({"ADM", "TCH"})).has("STD") is False

    def test_has_any_true(self):
        assert RoleSet(frozenset({"ADM", "TCH"})).has_any("STD", "TCH") is True

    def test_has_any_false(self):
        assert RoleSet(frozenset({"ADM"})).has_any("STD", "PAR") is False

    def test_empty_set_is_allowed(self):
        role_set = RoleSet(frozenset())

        assert role_set.roles == frozenset()
        assert role_set.primary_role == "STD"

    def test_all_valid_roles(self):
        role_set = RoleSet(frozenset(VALID_ROLES))

        assert role_set.roles == frozenset(VALID_ROLES)

    def test_is_staff_property(self):
        assert RoleSet(frozenset({"ADM"})).is_staff is True
        assert RoleSet(frozenset({"STD"})).is_staff is False

    def test_is_educator_property(self):
        assert RoleSet(frozenset({"TCH"})).is_educator is True
        assert RoleSet(frozenset({"CONTENT_MGR"})).is_educator is True
        assert RoleSet(frozenset({"PAR"})).is_educator is False

    def test_primary_role_uses_priority_order(self):
        role_set = RoleSet(frozenset({"STD", "ADM", "DIR"}))

        assert role_set.primary_role == "DIR"

    def test_roles_collection_is_iterable(self):
        role_set = RoleSet(frozenset({"PAR", "TCH"}))

        assert set(role_set.roles) == {"PAR", "TCH"}

    def test_role_compatibility_map_documents_known_pairings(self):
        assert ROLE_COMPATIBILITY["TCH"] == {"PAR", "CONTENT_MGR"}
