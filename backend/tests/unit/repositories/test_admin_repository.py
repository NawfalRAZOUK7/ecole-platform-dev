"""Mock-based unit tests for admin repositories:
- AdminRepository (admin.py)
- FeatureRepository (admin_feature.py)
- ComplianceRepository (admin_men_compliance.py)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.admin import AdminRepository
from app.repositories.admin_feature import FeatureRepository
from app.repositories.admin_men_compliance import ComplianceRepository


def _uid():
    return uuid.uuid4()


def _now():
    return datetime.now(timezone.utc)


class _FR:
    def __init__(self, v=None, many=None, scalar=None, rowcount=1):
        self._v = v
        self._many = many or []
        self._scalar = scalar
        self.rowcount = rowcount

    def scalar_one_or_none(self):
        return self._v

    def scalar_one(self):
        return self._v

    def scalar(self):
        return self._scalar

    def scalars(self):
        many = self._many; v = self._v
        return SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None):
    r = result if result is not None else _FR()
    return SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
    )


# ===========================================================================
# AdminRepository
# ===========================================================================

class TestAdminRepository:
    @pytest.mark.asyncio
    async def test_count_school_users(self):
        db = _db(_FR(scalar=10))
        result = await AdminRepository(db).count_school_users(_uid())
        assert result == 10

    @pytest.mark.asyncio
    async def test_count_active_sessions(self):
        db = _db(_FR(scalar=3))
        result = await AdminRepository(db).count_active_sessions(_uid())
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_active_invitations(self):
        db = _db(_FR(scalar=2))
        result = await AdminRepository(db).count_active_invitations(
            school_id=_uid(), now=_now()
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_count_recent_audit_events(self):
        db = _db(_FR(scalar=5))
        result = await AdminRepository(db).count_recent_audit_events(
            school_id=_uid(), audit_cutoff=_now()
        )
        assert result == 5

    @pytest.mark.asyncio
    async def test_count_pending_justifications(self):
        db = _db(_FR(scalar=1))
        result = await AdminRepository(db).count_pending_justifications(_uid())
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_role_counts(self):
        db = _db(_FR(many=[("TCH", 5), ("STD", 30)]))
        result = await AdminRepository(db).get_role_counts(_uid())
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_list_users_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_users(
            school_id=_uid(), search=None, role=None, status=None,
            cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_users_with_all_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_users(
            school_id=_uid(),
            cursor_dt=_now(),
            limit=5,
            role="TCH",
            status="active",
            search="Ahmed",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_active_memberships_for_users(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_active_memberships_for_users(
            school_id=_uid(), user_ids=[_uid()]
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        assert await AdminRepository(_db(_FR(v=obj))).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_get_user_by_email_in_school(self):
        obj = object()
        assert await AdminRepository(_db(_FR(v=obj))).get_user_by_email_in_school(
            email="x@test.ma", school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_get_user_with_role_no_role(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AdminRepository(db).get_user_with_role(
            user_id=_uid(), school_id=_uid(), role_code="TCH"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_user_with_role_with_role(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AdminRepository(db).get_user_with_role(
            user_id=_uid(), school_id=_uid(), role_code="TCH"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_set_user_status(self):
        user = SimpleNamespace(id=_uid(), status="active")
        db = _db()
        result = await AdminRepository(db).set_user_status(user, "suspended")
        assert result.status == "suspended"

    @pytest.mark.asyncio
    async def test_update_active_membership_role(self):
        db = _db()
        await AdminRepository(db).update_active_membership_role(
            user_id=_uid(), school_id=_uid(), role_code="ADM"
        )
        db.execute.assert_awaited()

    @pytest.mark.asyncio
    async def test_list_invitations_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_invitations(
            school_id=_uid(), status=None, now=_now(), cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_invitations_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_invitations(
            school_id=_uid(),
            cursor_dt=_now(),
            limit=5,
            status="active",
            now=_now(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_audit_logs_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_audit_logs(
            school_id=_uid(), action_type=None, correlation_id=None,
            date_from=None, date_to=None, cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_audit_logs_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_audit_logs(
            school_id=_uid(),
            cursor_dt=_now(),
            limit=5,
            action_type="login",
            correlation_id=None,
            date_from=None,
            date_to=None,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_justifications_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_justifications(
            school_id=_uid(), status=None, cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_justifications_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_justifications(
            school_id=_uid(),
            cursor_dt=_now(),
            limit=5,
            status="pending",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_user(self):
        user = SimpleNamespace(id=_uid())
        db = _db()
        result = await AdminRepository(db).create_user(user)
        db.add.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_create_membership(self):
        membership = SimpleNamespace(id=_uid())
        db = _db()
        result = await AdminRepository(db).create_membership(membership)
        db.add.assert_called_once_with(membership)

    @pytest.mark.asyncio
    async def test_create_invitation(self):
        invite = SimpleNamespace(id=_uid())
        db = _db()
        result = await AdminRepository(db).create_invitation(invite)
        db.add.assert_called_once_with(invite)

    @pytest.mark.asyncio
    async def test_create_parent_child_link(self):
        link = SimpleNamespace(id=_uid())
        db = _db()
        result = await AdminRepository(db).create_parent_child_link(link)
        db.add.assert_called_once_with(link)

    @pytest.mark.asyncio
    async def test_get_active_parent_child_link(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await AdminRepository(db).get_active_parent_child_link(
            parent_user_id=_uid(), child_user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_parent_child_links_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_parent_child_links(
            school_id=_uid(), parent_id=None, student_id=None,
            status=None, cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_parent_child_links_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await AdminRepository(db).list_parent_child_links(
            school_id=_uid(), parent_id=_uid(), student_id=_uid(),
            status="active", cursor_dt=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_parent_child_link(self):
        obj = object()
        assert await AdminRepository(_db(_FR(v=obj))).get_parent_child_link(
            link_id=_uid(), school_id=_uid()
        ) is obj

    @pytest.mark.asyncio
    async def test_revoke_parent_child_link(self):
        link = SimpleNamespace(id=_uid(), status="active")
        db = _db()
        result = await AdminRepository(db).revoke_parent_child_link(link)
        assert result is link


# ===========================================================================
# FeatureRepository
# ===========================================================================

class TestFeatureRepository:
    @pytest.mark.asyncio
    async def test_get_toggle_by_feature_key(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FeatureRepository(db).get_toggle_by_feature_key(
            feature_key="ai_enabled"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_toggle_by_id(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await FeatureRepository(db).get_toggle_by_id(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_toggles(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await FeatureRepository(db).list_toggles()
        assert result == items

    @pytest.mark.asyncio
    async def test_create_toggle(self):
        toggle = SimpleNamespace(id=_uid())
        db = _db()
        result = await FeatureRepository(db).create_toggle(toggle)
        db.add.assert_called_once_with(toggle)

    @pytest.mark.asyncio
    async def test_save_toggle(self):
        toggle = SimpleNamespace(id=_uid())
        db = _db()
        result = await FeatureRepository(db).save_toggle(toggle)
        assert result is toggle

    @pytest.mark.asyncio
    async def test_delete_toggle(self):
        toggle = SimpleNamespace(id=_uid())
        db = _db()
        await FeatureRepository(db).delete_toggle(toggle)
        db.delete.assert_awaited_once_with(toggle)


# ===========================================================================
# ComplianceRepository
# ===========================================================================

class TestComplianceRepository:
    @pytest.mark.asyncio
    async def test_get_user(self):
        obj = object()
        assert await ComplianceRepository(_db(_FR(v=obj))).get_user(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_academic_year(self):
        obj = object()
        assert await ComplianceRepository(_db(_FR(v=obj))).get_academic_year(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_course(self):
        obj = object()
        assert await ComplianceRepository(_db(_FR(v=obj))).get_course(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_content_item(self):
        obj = object()
        assert await ComplianceRepository(_db(_FR(v=obj))).get_content_item(_uid()) is obj

    @pytest.mark.asyncio
    async def test_get_curriculum_no_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_curriculum(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_curriculum_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_curriculum(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_curriculum_by_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_curriculum_by_scope(
            level="primary", grade="1", subject="math",
            academic_year="2024-2025", version="1"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_curricula_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_curricula()
        assert result == items

    @pytest.mark.asyncio
    async def test_list_curricula_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_curricula(
            level="primary",
            subject="math",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_curriculum(self):
        curriculum = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).create_curriculum(curriculum)
        db.add.assert_called_once_with(curriculum)

    @pytest.mark.asyncio
    async def test_save_curriculum(self):
        curriculum = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).save_curriculum(curriculum)
        assert result is curriculum

    @pytest.mark.asyncio
    async def test_get_objective_no_scope(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_objective(
            _uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_objective_with_curriculum(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_objective(
            _uid(), include_curriculum=True
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_objective_by_code(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_objective_by_code(
            curriculum_id=_uid(), code="OBJ-001"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_objectives_no_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_objectives(
            curriculum_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_objectives_with_status(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_objectives(
            curriculum_id=_uid(), trimester=1
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_objective(self):
        obj = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).create_objective(obj)
        db.add.assert_called_once_with(obj)

    @pytest.mark.asyncio
    async def test_save_objective(self):
        obj = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).save_objective(obj)
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_mapping_no_status(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_mapping(
            mapping_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_mapping_with_status(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_mapping(
            _uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_find_mapping(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).find_mapping(
            school_id=_uid(), objective_id=_uid(), content_item_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_mappings_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_mappings(
            school_id=_uid(), curriculum_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_mappings_with_filters(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await ComplianceRepository(db).list_mappings(
            school_id=_uid(),
            curriculum_id=_uid(),
            objective_id=_uid(),
            content_item_id=_uid(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_mapping(self):
        mapping = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).create_mapping(mapping)
        db.add.assert_called_once_with(mapping)

    @pytest.mark.asyncio
    async def test_save_mapping(self):
        mapping = SimpleNamespace(id=_uid())
        db = _db()
        result = await ComplianceRepository(db).save_mapping(mapping)
        assert result is mapping

    @pytest.mark.asyncio
    async def test_delete_mapping(self):
        mapping = SimpleNamespace(id=_uid())
        db = _db()
        await ComplianceRepository(db).delete_mapping(mapping)
        db.delete.assert_awaited_once_with(mapping)
