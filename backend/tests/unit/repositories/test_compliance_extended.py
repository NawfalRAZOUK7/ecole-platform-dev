"""Extended coverage tests for admin_men_compliance.py."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest

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
        many = self._many
        v = self._v
        return SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))

    def first(self):
        return self._many[0] if self._many else self._v

    def one(self):
        return self._v if self._v is not None else (0, 0)

    def one_or_none(self):
        return self._v

    def all(self):
        return self._many

    def mappings(self):
        return SimpleNamespace(all=lambda: self._many)

    def __iter__(self):
        return iter(self._many)


def _db(result=None, *, side_effects=None):
    r = result if result is not None else _FR()
    db = SimpleNamespace(
        execute=AsyncMock(return_value=r),
        add=Mock(),
        add_all=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        delete=AsyncMock(),
        refresh=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


class TestComplianceRepositoryExtended:
    """Cover missing lines in admin_men_compliance.py."""

    @pytest.mark.asyncio
    async def test_get_curriculum_without_objectives(self):
        """Cover get_curriculum without include_objectives (line 55)."""
        curriculum = MagicMock()
        db = _db(_FR(v=curriculum))
        result = await ComplianceRepository(db).get_curriculum(
            _uid(), include_objectives=False
        )
        assert result is curriculum

    @pytest.mark.asyncio
    async def test_get_curriculum_with_objectives(self):
        """Cover get_curriculum with include_objectives=True (line 55)."""
        curriculum = MagicMock()
        db = _db(_FR(v=curriculum))
        result = await ComplianceRepository(db).get_curriculum(
            _uid(), include_objectives=True
        )
        assert result is curriculum

    @pytest.mark.asyncio
    async def test_list_curricula_all_filters(self):
        """Cover list_curricula with all filters (lines 89-98)."""
        curriculum = MagicMock()
        db = _db(_FR(many=[curriculum]))
        result = await ComplianceRepository(db).list_curricula(
            level="primary",
            grade="CP",
            subject="Math",
            academic_year="2024-2025",
            is_active=True,
        )
        assert result == [curriculum]

    @pytest.mark.asyncio
    async def test_list_curricula_no_filters(self):
        """Cover list_curricula with no filters (lines 88+)."""
        db = _db(_FR(many=[]))
        result = await ComplianceRepository(db).list_curricula()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_curricula_is_active_false(self):
        """Cover is_active=False branch (line 98)."""
        curriculum = MagicMock()
        db = _db(_FR(many=[curriculum]))
        result = await ComplianceRepository(db).list_curricula(is_active=False)
        assert result == [curriculum]

    @pytest.mark.asyncio
    async def test_get_objective_without_curriculum(self):
        """Cover get_objective without include_curriculum (line 92)."""
        obj = MagicMock()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_objective(
            _uid(), include_curriculum=False
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_objective_with_curriculum(self):
        """Cover get_objective with include_curriculum=True (line 96)."""
        obj = MagicMock()
        db = _db(_FR(v=obj))
        result = await ComplianceRepository(db).get_objective(
            _uid(), include_curriculum=True
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_objectives_with_trimester_and_curriculum(self):
        """Cover list_objectives with trimester and include_curriculum (lines 153-160)."""
        obj = MagicMock()
        db = _db(_FR(many=[obj]))
        result = await ComplianceRepository(db).list_objectives(
            curriculum_id=_uid(),
            trimester=1,
            include_curriculum=True,
        )
        assert result == [obj]

    @pytest.mark.asyncio
    async def test_list_objectives_no_filters(self):
        """Cover list_objectives without optional filters."""
        db = _db(_FR(many=[]))
        result = await ComplianceRepository(db).list_objectives(curriculum_id=_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_get_mapping_with_school_id_and_objective(self):
        """Cover get_mapping with school_id and include_objective (lines 180-189)."""
        mapping = MagicMock()
        db = _db(_FR(v=mapping))
        result = await ComplianceRepository(db).get_mapping(
            _uid(), school_id=_uid(), include_objective=True
        )
        assert result is mapping

    @pytest.mark.asyncio
    async def test_get_mapping_no_extras(self):
        """Cover get_mapping without extras (line 204 else branches)."""
        db = _db(_FR(v=None))
        result = await ComplianceRepository(db).get_mapping(_uid())
        assert result is None

    @pytest.mark.asyncio
    async def test_find_mapping_with_both_ids(self):
        """Cover find_mapping with course_id and content_item_id (lines 203-210)."""
        mapping = MagicMock()
        db = _db(_FR(v=mapping))
        result = await ComplianceRepository(db).find_mapping(
            school_id=_uid(),
            objective_id=_uid(),
            course_id=_uid(),
            content_item_id=_uid(),
        )
        assert result is mapping

    @pytest.mark.asyncio
    async def test_find_mapping_no_ids(self):
        """Cover find_mapping with no course/content (else branches lines 204-210)."""
        db = _db(_FR(v=None))
        result = await ComplianceRepository(db).find_mapping(
            school_id=_uid(),
            objective_id=_uid(),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_list_mappings_all_filters(self):
        """Cover list_mappings with all optional filters (lines 222-249)."""
        mapping = MagicMock()
        db = _db(_FR(many=[mapping]))
        result = await ComplianceRepository(db).list_mappings(
            school_id=_uid(),
            curriculum_id=_uid(),
            objective_id=_uid(),
            course_id=_uid(),
            content_item_id=_uid(),
            include_objective=True,
        )
        assert result == [mapping]

    @pytest.mark.asyncio
    async def test_list_mappings_no_filters(self):
        """Cover list_mappings with no optional filters."""
        db = _db(_FR(many=[]))
        result = await ComplianceRepository(db).list_mappings(school_id=_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_delete_mapping(self):
        """Cover delete_mapping (lines 261-263)."""
        mapping = MagicMock()
        db = _db()
        await ComplianceRepository(db).delete_mapping(mapping)
        db.delete.assert_awaited_once_with(mapping)
        db.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_report_with_school_and_curriculum(self):
        """Cover get_report with school_id and include_curriculum (lines 272-278)."""
        report = MagicMock()
        db = _db(_FR(v=report))
        result = await ComplianceRepository(db).get_report(
            _uid(), school_id=_uid(), include_curriculum=True
        )
        assert result is report

    @pytest.mark.asyncio
    async def test_get_report_no_extras(self):
        """Cover get_report without extras."""
        db = _db(_FR(v=None))
        result = await ComplianceRepository(db).get_report(_uid())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_reports_with_filters(self):
        """Cover list_reports with curriculum_id and academic_year_id (lines 287-299)."""
        report = MagicMock()
        db = _db(_FR(many=[report]))
        result = await ComplianceRepository(db).list_reports(
            school_id=_uid(),
            curriculum_id=_uid(),
            academic_year_id=_uid(),
        )
        assert result == [report]

    @pytest.mark.asyncio
    async def test_list_reports_no_filters(self):
        """Cover list_reports without optional filters."""
        db = _db(_FR(many=[]))
        result = await ComplianceRepository(db).list_reports(school_id=_uid())
        assert result == []

    @pytest.mark.asyncio
    async def test_create_report(self):
        """Cover create_report (lines 302-304)."""
        report = MagicMock()
        db = _db()
        result = await ComplianceRepository(db).create_report(report)
        db.add.assert_called_with(report)
        assert result is report

    @pytest.mark.asyncio
    async def test_save_report(self):
        """Cover save_report (lines 307-309)."""
        report = MagicMock()
        db = _db()
        result = await ComplianceRepository(db).save_report(report)
        db.add.assert_called_with(report)
        assert result is report
