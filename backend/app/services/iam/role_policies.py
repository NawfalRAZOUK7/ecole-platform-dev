"""Role policy helpers for school-scoped IAM operations."""

from __future__ import annotations

from app.core.permissions import DIR, PAR, STD, TCH
from app.models.school import SchoolType

FORMAL_SCHOOL_INVITABLE_ROLES = frozenset({DIR, TCH, PAR, STD})
INFORMAL_SCHOOL_INVITABLE_ROLES = frozenset({PAR, STD})

FORMAL_SCHOOL_MANAGED_ROLES = FORMAL_SCHOOL_INVITABLE_ROLES
INFORMAL_SCHOOL_MANAGED_ROLES = INFORMAL_SCHOOL_INVITABLE_ROLES


def _normalized_school_type(school_type: str | None) -> str:
    return (school_type or SchoolType.FORMAL.value).lower().strip()


def allowed_invitation_roles(school_type: str | None) -> frozenset[str]:
    """Roles a tenant owner can invite after the tenant already exists.

    Formal school owners can invite directors, teachers, parents and students.
    Informal/micro-school owners can invite parents and students. The owner
    roles themselves (ADM and EDUCATOR) are provisioned through SuperAdmin
    onboarding approval, not regular school-admin invitations.
    """

    if _normalized_school_type(school_type) == SchoolType.INFORMAL.value:
        return INFORMAL_SCHOOL_INVITABLE_ROLES
    return FORMAL_SCHOOL_INVITABLE_ROLES


def allowed_managed_roles(school_type: str | None) -> frozenset[str]:
    """Roles a tenant admin can assign or batch-create inside an existing tenant."""

    if _normalized_school_type(school_type) == SchoolType.INFORMAL.value:
        return INFORMAL_SCHOOL_MANAGED_ROLES
    return FORMAL_SCHOOL_MANAGED_ROLES
