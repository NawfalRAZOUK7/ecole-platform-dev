"""Unit tests for app/services/iam/role_policies.py.

Covers the school-type → invitable/managed role mapping, normalization of the
school-type string (None, case, whitespace, unknown), and the invariant that
owner/platform roles (ADM, EDUCATOR, SUP, SYS, CONTENT_MGR) are never invitable
or managed through regular school-admin flows — they go through SuperAdmin
onboarding instead.
"""

from __future__ import annotations

from app.core.permissions import DIR, PAR, STD, TCH
from app.models.school import SchoolType
from app.services.iam.role_policies import (
    FORMAL_SCHOOL_INVITABLE_ROLES,
    INFORMAL_SCHOOL_INVITABLE_ROLES,
    allowed_invitation_roles,
    allowed_managed_roles,
)

_OWNER_OR_PLATFORM_ROLES = {"ADM", "EDUCATOR", "SUP", "SYS", "CONTENT_MGR"}


class TestFormalSchool:
    def test_invitable_roles(self) -> None:
        assert allowed_invitation_roles("formal") == frozenset({DIR, TCH, PAR, STD})

    def test_managed_equals_invitable(self) -> None:
        assert allowed_managed_roles("formal") == allowed_invitation_roles("formal")

    def test_excludes_owner_and_platform_roles(self) -> None:
        assert _OWNER_OR_PLATFORM_ROLES.isdisjoint(allowed_invitation_roles("formal"))


class TestInformalSchool:
    def test_invitable_roles_are_parents_and_students_only(self) -> None:
        assert allowed_invitation_roles("informal") == frozenset({PAR, STD})

    def test_managed_equals_invitable(self) -> None:
        assert allowed_managed_roles("informal") == allowed_invitation_roles("informal")

    def test_excludes_teachers_and_directors(self) -> None:
        roles = allowed_invitation_roles("informal")
        assert DIR not in roles
        assert TCH not in roles

    def test_excludes_owner_and_platform_roles(self) -> None:
        assert _OWNER_OR_PLATFORM_ROLES.isdisjoint(allowed_invitation_roles("informal"))


class TestNormalization:
    def test_none_defaults_to_formal(self) -> None:
        assert allowed_invitation_roles(None) == FORMAL_SCHOOL_INVITABLE_ROLES
        assert allowed_managed_roles(None) == FORMAL_SCHOOL_INVITABLE_ROLES

    def test_empty_string_defaults_to_formal(self) -> None:
        assert allowed_invitation_roles("") == FORMAL_SCHOOL_INVITABLE_ROLES

    def test_unknown_type_defaults_to_formal(self) -> None:
        assert allowed_invitation_roles("garderie") == FORMAL_SCHOOL_INVITABLE_ROLES

    def test_is_case_insensitive(self) -> None:
        assert allowed_invitation_roles("INFORMAL") == INFORMAL_SCHOOL_INVITABLE_ROLES
        assert allowed_invitation_roles("Informal") == INFORMAL_SCHOOL_INVITABLE_ROLES

    def test_strips_whitespace(self) -> None:
        assert (
            allowed_invitation_roles("  informal  ") == INFORMAL_SCHOOL_INVITABLE_ROLES
        )

    def test_enum_values_are_consistent(self) -> None:
        assert (
            allowed_invitation_roles(SchoolType.FORMAL.value)
            == FORMAL_SCHOOL_INVITABLE_ROLES
        )
        assert (
            allowed_invitation_roles(SchoolType.INFORMAL.value)
            == INFORMAL_SCHOOL_INVITABLE_ROLES
        )


class TestInvariants:
    def test_returned_sets_are_frozen(self) -> None:
        assert isinstance(allowed_invitation_roles("formal"), frozenset)
        assert isinstance(allowed_managed_roles("informal"), frozenset)

    def test_informal_is_subset_of_formal(self) -> None:
        assert allowed_invitation_roles("informal") <= allowed_invitation_roles(
            "formal"
        )
