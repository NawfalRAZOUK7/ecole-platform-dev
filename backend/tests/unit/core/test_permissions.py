"""Unit tests for permission hierarchy helpers."""

from __future__ import annotations

import pytest

from app.core import permissions as perms


class TestPermissionHierarchy:
    def test_platform_roles_constant(self):
        assert perms.PLATFORM_ROLES == {perms.SUP, perms.SYS, perms.CONTENT_MGR}

    def test_role_hierarchy_exact_structure(self):
        assert perms.ROLE_HIERARCHY == {
            perms.SYS: [perms.SUP],
            perms.SUP: [perms.ADM],
            perms.ADM: [perms.DIR],
            perms.DIR: [perms.TCH],
        }

    @pytest.mark.parametrize(
        ("role", "direct_count", "inherited_count", "effective_count"),
        [
            (perms.SYS, 6, 170, 176),
            (perms.SUP, 9, 164, 173),
            (perms.ADM, 25, 139, 164),
            (perms.DIR, 66, 75, 141),
            (perms.TCH, 81, 0, 81),
            (perms.PAR, 50, 0, 50),
            (perms.STD, 42, 0, 42),
            (perms.CONTENT_MGR, 32, 0, 32),
        ],
    )
    def test_effective_permission_counts_by_role(
        self,
        role: str,
        direct_count: int,
        inherited_count: int,
        effective_count: int,
    ):
        direct_permissions = perms.ROLE_PERMISSIONS[role]
        effective_permissions = perms.get_effective_permissions(role)

        assert len(direct_permissions) == direct_count
        assert len(effective_permissions - direct_permissions) == inherited_count
        assert len(effective_permissions) == effective_count

    def test_unknown_role_returns_empty_permissions(self):
        assert perms.get_effective_permissions("UNKNOWN") == set()
        assert perms.get_permissions_for_role("UNKNOWN") == set()

    def test_circular_role_hierarchy_detected(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setitem(perms.ROLE_HIERARCHY, perms.TCH, [perms.SYS])

        with pytest.raises(ValueError, match="Circular role hierarchy detected"):
            perms.get_effective_permissions(perms.SYS)

    @pytest.mark.parametrize(
        ("role", "permission"),
        [
            (perms.DIR, perms.PERM_LMS_ASSIGNMENT_CREATE),
            (perms.ADM, perms.PERM_BIL_INVOICE_READ),
            (perms.SUP, perms.PERM_ERP_ENROLLMENT_ASSIGN),
            (perms.SYS, perms.PERM_SUP_AUDIT_READ),
        ],
    )
    def test_roles_inherit_expected_permissions(self, role: str, permission: str):
        assert permission not in perms.ROLE_PERMISSIONS[role]
        assert perms.role_has_permission(role, permission)

    def test_parent_and_student_stay_outside_admin_branch(self):
        assert not perms.role_has_permission(perms.PAR, perms.PERM_ERP_CLASS_READ)
        assert not perms.role_has_permission(
            perms.PAR, perms.PERM_LMS_ASSIGNMENT_CREATE
        )
        assert not perms.role_has_permission(perms.STD, perms.PERM_ERP_CLASS_READ)
        assert not perms.role_has_permission(perms.STD, perms.PERM_ADM_SCHOOL_MANAGE)

    @pytest.mark.parametrize(
        ("role", "permission", "expected"),
        [
            (perms.SYS, perms.PERM_IAM_SESSION_CREATE, True),
            (perms.SYS, perms.PERM_BIL_PAYMENT_RECONCILE, True),
            (perms.SUP, perms.PERM_SYS_FEATURE_MANAGE, False),
            (perms.SUP, perms.PERM_ADM_PLATFORM_STATS, True),
            (perms.ADM, perms.PERM_ADM_SCHOOL_MANAGE, True),
            (perms.ADM, perms.PERM_IAM_PARENT_LINK_READ, True),
            (perms.DIR, perms.PERM_ERP_TIMETABLE_GENERATE, True),
            (perms.DIR, perms.PERM_ERP_ENROLLMENT_ASSIGN, False),
            (perms.TCH, perms.PERM_LMS_SUBMISSION_GRADE, True),
            (perms.TCH, perms.PERM_LMS_SUBMISSION_CREATE, False),
            (perms.PAR, perms.PERM_BIL_INVOICE_READ, True),
            (perms.PAR, perms.PERM_COM_CONVERSATION_CREATE, True),
            (perms.STD, perms.PERM_LMS_SUBMISSION_CREATE, True),
            (perms.STD, perms.PERM_QUIZ_ATTEMPT, True),
            (perms.STD, perms.PERM_BIL_INVOICE_READ, False),
            (perms.CONTENT_MGR, perms.PERM_CMS_CONTENT_MANAGE, True),
            (perms.CONTENT_MGR, perms.PERM_SYS_FEATURE_MANAGE, True),
            (perms.CONTENT_MGR, perms.PERM_QUIZ_ATTEMPT, False),
            (perms.CONTENT_MGR, perms.PERM_DOC_RESOURCE_READ, True),
            (perms.CONTENT_MGR, perms.PERM_IAM_PARENT_LINK_CREATE, False),
        ],
    )
    def test_role_has_permission_matrix(
        self,
        role: str,
        permission: str,
        expected: bool,
    ):
        assert perms.role_has_permission(role, permission) is expected
