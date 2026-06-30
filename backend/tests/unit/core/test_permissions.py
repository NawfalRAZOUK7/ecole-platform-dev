"""Unit tests for the permission catalog.

The catalog uses **explicit composition** (no role inheritance): ROLE_PERMISSIONS
holds the complete permission set per role, composed from named bundles. DIR
(oversight) and ADM (operations) are independent siblings — neither a superset of
the other — and SYS is a narrow automation account (no god-mode).
"""

from __future__ import annotations

import pytest

from app.core import permissions as perms


class TestPermissionCatalog:
    def test_platform_roles_constant(self):
        assert perms.PLATFORM_ROLES == {perms.SUP, perms.SYS, perms.CONTENT_MGR}

    def test_role_inheritance_removed(self):
        # Inheritance was replaced by explicit composition bundles.
        assert perms.ROLE_HIERARCHY == {}

    @pytest.mark.parametrize(
        ("role", "effective_count"),
        [
            (perms.SYS, 13),
            (perms.SUP, 179),
            (perms.ADM, 162),
            (perms.DIR, 118),
            (perms.TCH, 86),
            (perms.PAR, 54),
            (perms.STD, 47),
            (perms.CONTENT_MGR, 33),
        ],
    )
    def test_effective_equals_direct_no_inheritance(self, role, effective_count):
        direct = perms.ROLE_PERMISSIONS[role]
        effective = perms.get_effective_permissions(role)
        assert effective == set(direct)  # no inheritance: effective == direct
        assert len(effective) == effective_count

    def test_dir_and_adm_are_independent_siblings(self):
        adm = perms.get_effective_permissions(perms.ADM)
        dir_ = perms.get_effective_permissions(perms.DIR)
        assert not dir_ <= adm  # neither is a superset of the other
        assert not adm <= dir_
        # DIR oversight is absent from ADM:
        assert perms.PERM_ADM_AUDIT_READ in dir_ and perms.PERM_ADM_AUDIT_READ not in adm
        assert (
            perms.PERM_ADM_ANNOUNCEMENT_MANAGE in dir_
            and perms.PERM_ADM_ANNOUNCEMENT_MANAGE not in adm
        )
        # ADM operations are absent from DIR:
        assert perms.PERM_ADM_USER_MANAGE in adm and perms.PERM_ADM_USER_MANAGE not in dir_
        assert perms.PERM_BIL_FEE_CREATE in adm and perms.PERM_BIL_FEE_CREATE not in dir_

    def test_impersonation_is_sup_only(self):
        imp = perms.PERM_ADM_IMPERSONATE
        assert perms.role_has_permission(perms.SUP, imp)
        for role in (perms.DIR, perms.ADM, perms.SYS, perms.TCH):
            assert not perms.role_has_permission(role, imp)

    def test_sup_is_superadmin_distinct_from_sys(self):
        sup = perms.get_effective_permissions(perms.SUP)
        sys = perms.get_effective_permissions(perms.SYS)
        assert perms.get_effective_permissions(perms.ADM) <= sup
        assert perms.get_effective_permissions(perms.DIR) <= sup
        assert sup != sys
        assert len(sys) < len(sup)  # SYS is the narrow automation account

    def test_unknown_role_returns_empty_permissions(self):
        assert perms.get_effective_permissions("UNKNOWN") == set()
        assert perms.get_permissions_for_role("UNKNOWN") == set()

    def test_circular_role_hierarchy_detected(self, monkeypatch: pytest.MonkeyPatch):
        # Defensive: if a hierarchy is ever re-introduced with a cycle, detect it.
        monkeypatch.setitem(perms.ROLE_HIERARCHY, perms.SYS, [perms.SYS])
        with pytest.raises(ValueError, match="Circular role hierarchy detected"):
            perms.get_effective_permissions(perms.SYS)

    def test_parent_and_student_stay_outside_admin_branch(self):
        assert not perms.role_has_permission(perms.PAR, perms.PERM_ERP_CLASS_READ)
        assert not perms.role_has_permission(perms.PAR, perms.PERM_LMS_ASSIGNMENT_CREATE)
        assert not perms.role_has_permission(perms.STD, perms.PERM_ERP_CLASS_READ)
        assert not perms.role_has_permission(perms.STD, perms.PERM_ADM_SCHOOL_MANAGE)

    def test_activity_read_permission_matches_expected_roles(self):
        for role in (perms.STD, perms.TCH, perms.DIR, perms.ADM):
            assert perms.role_has_permission(role, perms.PERM_LMS_ACTIVITY_READ)
        assert not perms.role_has_permission(perms.PAR, perms.PERM_LMS_ACTIVITY_READ)

    @pytest.mark.parametrize(
        ("role", "permission", "expected"),
        [
            # SYS — narrow automation: can authenticate + run jobs, no school mgmt
            (perms.SYS, perms.PERM_IAM_SESSION_CREATE, True),
            (perms.SYS, perms.PERM_BIL_PAYMENT_RECONCILE, True),
            (perms.SYS, perms.PERM_SUP_AUDIT_READ, False),
            (perms.SYS, perms.PERM_ADM_SCHOOL_MANAGE, False),
            # SUP — platform super-admin
            (perms.SUP, perms.PERM_ADM_IMPERSONATE, True),
            (perms.SUP, perms.PERM_ADM_PLATFORM_STATS, True),
            (perms.SUP, perms.PERM_SYS_FEATURE_MANAGE, False),
            # ADM — operations (not oversight)
            (perms.ADM, perms.PERM_ADM_SCHOOL_MANAGE, True),
            (perms.ADM, perms.PERM_IAM_PARENT_LINK_READ, True),
            (perms.ADM, perms.PERM_ADM_AUDIT_READ, False),
            (perms.ADM, perms.PERM_ERP_TIMETABLE_GENERATE, True),
            # DIR — oversight (not operations)
            (perms.DIR, perms.PERM_ADM_AUDIT_READ, True),
            (perms.DIR, perms.PERM_ERP_TIMETABLE_GENERATE, False),
            (perms.DIR, perms.PERM_ERP_ENROLLMENT_ASSIGN, False),
            (perms.DIR, perms.PERM_LMS_ASSIGNMENT_CREATE, True),
            # TCH / PAR / STD / CONTENT_MGR — unchanged
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
    def test_role_has_permission_matrix(self, role, permission, expected):
        assert perms.role_has_permission(role, permission) is expected
