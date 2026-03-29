"""FastAPI dependencies for authentication, RBAC, and ABAC guards.

Reference: S-029 (JWT validation), S-034 (RBAC middleware), S-035/S-036/S-037 (ABAC guards)
Security pipeline order: AuthN -> Context/Scope -> RBAC -> ABAC -> INV
Deny ordering (S-042): 401 -> 404 (masking) -> 403
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.permissions import get_permissions_for_role, role_has_permission
from app.core.security import decode_access_token
from app.models.iam import Session, User

# HTTPBearer scheme — auto_error=False so we return 401 ourselves (not 403)
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Authenticated user context
# ---------------------------------------------------------------------------
@dataclass
class AuthContext:
    """Resolved authentication context available to all protected endpoints."""

    user_id: uuid.UUID
    role: str
    school_id: uuid.UUID
    session_id: uuid.UUID
    permissions: set[str]

    # Loaded lazily if needed
    user: User | None = None


# ---------------------------------------------------------------------------
# AuthN dependency — extracts + validates access token (S-029)
# ---------------------------------------------------------------------------
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthContext:
    """Extract and validate the access token, returning an AuthContext.

    Pipeline position: step 1 (AuthN).
    Deny ordering: returns 401 for any auth failure.
    """
    if credentials is None:
        raise AuthenticationError(
            "Missing Authorization header",
            error_code="ERR-IAM-401",
        )

    # Decode and validate the JWT
    payload = decode_access_token(credentials.credentials)

    user_id = uuid.UUID(payload["sub"])
    session_id = uuid.UUID(payload["session_id"])
    role = payload["role"]
    school_id = uuid.UUID(payload["school_id"])

    # Verify session is still active (not revoked) — S-032
    session_result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.revoke_at.is_(None),
        )
    )
    session = session_result.scalar_one_or_none()
    if session is None:
        raise AuthenticationError(
            "Session has been revoked",
            error_code="ERR-IAM-401",
        )

    permissions = get_permissions_for_role(role)

    return AuthContext(
        user_id=user_id,
        role=role,
        school_id=school_id,
        session_id=session_id,
        permissions=permissions,
    )


# ---------------------------------------------------------------------------
# RBAC dependency — checks permission(s) (S-034)
# ---------------------------------------------------------------------------
class RequiresPermission:
    """FastAPI dependency that checks the user's role has the required permission(s).

    Usage:
        @router.get("/classes/{class_id}", dependencies=[Depends(RequiresPermission("PERM-ERP:class:read"))])
        async def get_class(...): ...

    Or in endpoint signature:
        async def get_class(auth: AuthContext = Depends(RequiresPermission("PERM-ERP:class:read"))): ...

    Pipeline position: step 3 (RBAC), after AuthN and scope check.
    """

    def __init__(self, *permissions: str) -> None:
        self.required_permissions = permissions

    async def __call__(
        self,
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        for perm in self.required_permissions:
            if not role_has_permission(auth.role, perm):
                raise AuthorizationError(
                    "Insufficient permissions",
                    error_code="ERR-AUTHZ-001",
                    details={
                        "required": list(self.required_permissions),
                        "role": auth.role,
                    },
                )
        return auth


# Convenience alias for common use
def requires_permission(*permissions: str) -> RequiresPermission:
    """Create a RequiresPermission dependency for the given permission codes."""
    return RequiresPermission(*permissions)


class RequiresAnyPermission:
    """FastAPI dependency that accepts any one of the given permissions."""

    def __init__(self, *permissions: str) -> None:
        self.allowed_permissions = permissions

    async def __call__(
        self,
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if not any(role_has_permission(auth.role, perm) for perm in self.allowed_permissions):
            raise AuthorizationError(
                "Insufficient permissions",
                error_code="ERR-AUTHZ-001",
                details={
                    "required_any": list(self.allowed_permissions),
                    "role": auth.role,
                },
            )
        return auth


def requires_any_permission(*permissions: str) -> RequiresAnyPermission:
    """Create a RequiresAnyPermission dependency for the given permission codes."""
    return RequiresAnyPermission(*permissions)


class RequiresRole:
    """FastAPI dependency that restricts access to one or more role codes."""

    def __init__(self, *roles: str) -> None:
        self.allowed_roles = roles

    async def __call__(
        self,
        auth: AuthContext = Depends(get_current_user),
    ) -> AuthContext:
        if auth.role not in self.allowed_roles:
            raise AuthorizationError(
                "Insufficient permissions",
                error_code="ERR-AUTHZ-001",
                details={
                    "allowed_roles": list(self.allowed_roles),
                    "role": auth.role,
                },
            )
        return auth


def requires_role(*roles: str) -> RequiresRole:
    """Create a RequiresRole dependency for the given role codes."""
    return RequiresRole(*roles)


# ---------------------------------------------------------------------------
# ABAC guard: school boundary (S-035)
# ---------------------------------------------------------------------------
def verify_school_boundary(resource_school_id: uuid.UUID, auth: AuthContext) -> None:
    """Verify that the resource belongs to the user's school.

    Returns 404 (NOT 403) to prevent information leakage (scope masking per D6).
    Pipeline position: step 2 (Context/Scope), between AuthN and RBAC.
    """
    from app.core.exceptions import NotFoundError

    if resource_school_id != auth.school_id:
        raise NotFoundError(
            "Resource not found",
            error_code="ERR-RES-404",
        )


# ---------------------------------------------------------------------------
# ABAC guard: parent-child ownership (S-036)
# ---------------------------------------------------------------------------
async def get_parent_child_ids(
    parent_user_id: uuid.UUID,
    school_id: uuid.UUID,
    db: AsyncSession,
) -> set[uuid.UUID]:
    """Get the set of student IDs linked to a parent in a school.

    Phase 1A: uses parent_child_links table for explicit parent-child relationships.
    Parents can only access data for their linked children (ABAC ownership guard).
    """
    from app.models.iam import ParentChildLink

    result = await db.execute(
        select(ParentChildLink.child_user_id).where(
            ParentChildLink.parent_user_id == parent_user_id,
            ParentChildLink.school_id == school_id,
            ParentChildLink.status == "active",
        )
    )
    return set(result.scalars().all())


def verify_parent_child_ownership(
    child_id: uuid.UUID,
    allowed_child_ids: set[uuid.UUID],
) -> None:
    """Verify that the parent has access to this child's data.

    Returns 404 (masking) if the child is not linked to the parent.
    """
    from app.core.exceptions import NotFoundError

    if child_id not in allowed_child_ids:
        raise NotFoundError(
            "Resource not found",
            error_code="ERR-RES-404",
        )


# ---------------------------------------------------------------------------
# ABAC guard: teacher assignment (S-037)
# ---------------------------------------------------------------------------
async def get_teacher_class_ids(
    teacher_user_id: uuid.UUID,
    school_id: uuid.UUID,
    db: AsyncSession,
) -> set[uuid.UUID]:
    """Get the set of class IDs assigned to a teacher."""
    from app.models.erp import TeacherAssignment

    result = await db.execute(
        select(TeacherAssignment.class_id).where(
            TeacherAssignment.teacher_id == teacher_user_id,
            TeacherAssignment.school_id == school_id,
        )
    )
    return set(result.scalars().all())


def verify_teacher_assignment(
    class_id: uuid.UUID,
    allowed_class_ids: set[uuid.UUID],
) -> None:
    """Verify that the teacher is assigned to this class.

    Returns 404 (masking) if the class is not assigned to the teacher.
    """
    from app.core.exceptions import NotFoundError

    if class_id not in allowed_class_ids:
        raise NotFoundError(
            "Resource not found",
            error_code="ERR-RES-404",
        )
