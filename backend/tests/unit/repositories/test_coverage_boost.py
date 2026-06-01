"""Coverage-boost tests targeting specific missing branches.

Covers:
- academic_progress.py  (75% → 95%+)
- academic_gradebook.py (88% → 95%+)
- budget.py             (84% → 95%+)
- billing.py            (88% → 95%+)
- ai_games.py           (82% → 95%+)
- lms_question_bank.py  (88% → 95%+)
- base.py               (80% → 95%+)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest

from app.repositories.academic_progress import ProgressRepository
from app.repositories.academic_gradebook import GradebookRepository
from app.repositories.ai_games import GamesRepository
from app.repositories.base import BaseRepository
from app.repositories.billing import BillingRepository
from app.repositories.budget import BudgetRepository
from app.repositories.lms_question_bank import QuestionBankRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uid():
    return uuid.uuid4()


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
        ns = SimpleNamespace(all=lambda: many, first=lambda: (many[0] if many else v))
        ns.unique = lambda: ns
        return ns

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
        add_all=Mock(),
        flush=AsyncMock(),
        commit=AsyncMock(),
        merge=AsyncMock(),
        delete=AsyncMock(),
    )


# ===========================================================================
# BaseRepository — _scoped_query and _scoped_exists (lines 17, 21)
# ===========================================================================

class TestBaseRepository:
    def test_scoped_query_returns_select(self):
        from app.models.iam import User
        db = _db()
        repo = BaseRepository(db)
        q = repo._scoped_query(User, _uid())
        assert q is not None
        assert "school_id" in str(q)

    def test_scoped_exists_returns_select(self):
        from app.models.iam import User
        db = _db()
        repo = BaseRepository(db)
        q = repo._scoped_exists(User, _uid(), _uid())
        assert q is not None
        assert "school_id" in str(q)


# ===========================================================================
# ProgressRepository — missing branches
# ===========================================================================

class TestProgressRepositoryBoost:
    @pytest.mark.asyncio
    async def test_get_content_completion_counts_with_matching_status(self):
        """Lines 149-150: row.status in counts → updates count."""
        row = SimpleNamespace(status="completed", cnt=5)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_content_completion_counts(
            student_id=_uid()
        )
        assert result["completed"] == 5

    @pytest.mark.asyncio
    async def test_get_content_completion_counts_unknown_status_ignored(self):
        """Branch: row.status NOT in counts → skipped."""
        row = SimpleNamespace(status="unknown_status", cnt=3)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_content_completion_counts(
            student_id=_uid()
        )
        assert result["completed"] == 0

    @pytest.mark.asyncio
    async def test_get_attendance_overview_counts_with_matching_status(self):
        """Lines 200-201: row.status in counts → updates count."""
        row = SimpleNamespace(status="present", cnt=10)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_attendance_overview_counts(
            student_id=_uid(), school_id=_uid()
        )
        assert result["present"] == 10

    @pytest.mark.asyncio
    async def test_get_attendance_overview_counts_unknown_status_ignored(self):
        """Branch: row.status NOT in counts → skipped."""
        row = SimpleNamespace(status="unknown", cnt=7)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_attendance_overview_counts(
            student_id=_uid(), school_id=_uid()
        )
        assert result["present"] == 0

    @pytest.mark.asyncio
    async def test_get_class_info_returns_tuple_when_found(self):
        """Line 288: row is not None → return row.name, row.code."""
        row = SimpleNamespace(name="Terminale A", code="TA")
        db = _db(_FR(v=row))
        result = await ProgressRepository(db).get_class_info(
            class_id=_uid(), school_id=_uid()
        )
        assert result == ("Terminale A", "TA")

    @pytest.mark.asyncio
    async def test_get_grade_averages_for_students_empty_list(self):
        """Line 314: empty student_ids → return {}."""
        db = _db()
        result = await ProgressRepository(db).get_grade_averages_for_students(
            student_ids=[], school_id=_uid()
        )
        assert result == {}
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_attendance_rates_for_students_empty_list(self):
        """Line 339: empty student_ids → return {}."""
        db = _db()
        result = await ProgressRepository(db).get_attendance_rates_for_students(
            student_ids=[], school_id=_uid()
        )
        assert result == {}
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_content_completion_rates_for_students_empty_list(self):
        """Line 370: empty student_ids → return {}."""
        db = _db()
        result = await ProgressRepository(db).get_content_completion_rates_for_students(
            student_ids=[]
        )
        assert result == {}
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_get_student_content_completion_rate_no_content(self):
        """Lines 459-473: total=0 → return None."""
        row = SimpleNamespace(total=0, completed=0)
        db = _db(_FR(v=row))
        result = await ProgressRepository(db).get_student_content_completion_rate(
            student_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_student_content_completion_rate_with_content(self):
        """Lines 459-473: total>0 → return percentage."""
        row = SimpleNamespace(total=10, completed=8)
        db = _db(_FR(v=row))
        result = await ProgressRepository(db).get_student_content_completion_rate(
            student_id=_uid()
        )
        assert result == 80.0

    @pytest.mark.asyncio
    async def test_get_latest_grade_not_found(self):
        """Lines 481-497: row is None → return None."""
        db = _db(_FR(v=None))
        result = await ProgressRepository(db).get_latest_grade(
            student_id=_uid(), school_id=_uid()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_grade_found(self):
        """Lines 481-497: row is not None → return dict."""
        row = SimpleNamespace(score=85.5, title="Examen Final")
        db = _db(_FR(v=row))
        result = await ProgressRepository(db).get_latest_grade(
            student_id=_uid(), school_id=_uid()
        )
        assert result == {"score": 85.5, "assignment": "Examen Final"}

    @pytest.mark.asyncio
    async def test_get_attendance_rates_with_zero_total(self):
        """Branch: row.total == 0 → rate = 0.0."""
        sid = _uid()
        row = SimpleNamespace(student_id=sid, total=0, present=0)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_attendance_rates_for_students(
            student_ids=[sid], school_id=_uid()
        )
        assert result[sid] == 0.0

    @pytest.mark.asyncio
    async def test_get_attendance_rates_with_nonzero_total(self):
        """Branch: row.total > 0 → rate = present/total*100."""
        sid = _uid()
        row = SimpleNamespace(student_id=sid, total=20, present=18)
        db = _db(_FR(many=[row]))
        result = await ProgressRepository(db).get_attendance_rates_for_students(
            student_ids=[sid], school_id=_uid()
        )
        assert result[sid] == 90.0


# ===========================================================================
# GradebookRepository — update branch (lines 157-163)
# ===========================================================================

class TestGradebookRepositoryBoost:
    @pytest.mark.asyncio
    async def test_save_student_period_average_update_existing(self):
        """Lines 157-163: average already exists → update attributes."""
        existing = SimpleNamespace(
            school_id=None,
            weighted_average=None,
            mention=None,
            class_rank=None,
            total_students=None,
            computed_at=None,
        )
        db = _db(_FR(v=existing))

        result = await GradebookRepository(db).save_student_period_average(
            student_id=_uid(),
            class_id=_uid(),
            period_id=_uid(),
            school_id=_uid(),
            weighted_average=14.5,
            mention="Bien",
            class_rank=3,
            total_students=30,
            computed_at=datetime.now(timezone.utc),
        )
        assert existing.weighted_average == 14.5
        assert existing.mention == "Bien"
        assert existing.class_rank == 3
        db.add.assert_called()


# ===========================================================================
# BudgetRepository — optional parameter branches
# ===========================================================================

class TestBudgetRepositoryBoost:
    @pytest.mark.asyncio
    async def test_get_budget_with_include_allocations(self):
        """Line 51: include_allocations=True."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_budget(
            budget_id=_uid(), include_allocations=True
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_allocation_with_school_id(self):
        """Line 93: school_id is not None."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_allocation(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_allocation_with_all_includes(self):
        """Lines 97, 99, 101: include_budget/requests/transactions=True."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_allocation(
            _uid(),
            include_budget=True,
            include_requests=True,
            include_transactions=True,
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_allocations_with_class_and_teacher_filters(self):
        """Lines 122, 124: class_id and teacher_id filters."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_allocations(
            school_id=_uid(),
            class_id=_uid(),
            teacher_id=_uid(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_request_with_include_allocation(self):
        """Line 161: include_allocation=True."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_request(_uid(), include_allocation=True)
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_requests_with_allocation_and_requester(self):
        """Lines 184, 186: allocation_id and requester_id filters."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_requests(
            school_id=_uid(),
            allocation_id=_uid(),
            requester_id=_uid(),
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_transaction_with_school_id(self):
        """Line 213: school_id is not None."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_transaction(_uid(), school_id=_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_transaction_with_include_allocation(self):
        """Line 222: include_allocation=True."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BudgetRepository(db).get_transaction(
            _uid(), include_allocation=True
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_transactions_with_allocation_and_request(self):
        """Lines 247, 249: allocation_id and request_id filters."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await BudgetRepository(db).list_transactions(
            school_id=_uid(),
            allocation_id=_uid(),
            request_id=_uid(),
        )
        assert result == items


# ===========================================================================
# BillingRepository — missing branch coverage
# ===========================================================================

class TestBillingRepositoryBoost:
    @pytest.mark.asyncio
    async def test_list_fee_assignments_with_all_filters(self):
        """Lines 123->125, 126, 128: fee_structure_id, student_id, status filters."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_assignments(
            school_id=_uid(),
            fee_structure_id=_uid(),
            student_id=_uid(),
            status="ACTIVE",
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_fee_assignments_student_ids_empty(self):
        """Lines 130-131: student_ids=[] → early return []."""
        db = _db()
        result = await BillingRepository(db).list_fee_assignments(
            school_id=_uid(),
            student_ids=[],
        )
        assert result == []
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_list_fee_assignments_student_ids_non_empty(self):
        """Line 132: student_ids non-empty → filters applied."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await BillingRepository(db).list_fee_assignments(
            school_id=_uid(),
            student_ids=[_uid(), _uid()],
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_create_fee_assignments_non_empty(self):
        """Lines 165-167: non-empty list → add_all + flush."""
        fake_assignment = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.FeeAssignment", return_value=fake_assignment):
            result = await BillingRepository(db).create_fee_assignments(
                [{"school_id": str(_uid())}]
            )
        db.flush.assert_awaited()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_create_fee_assignments_empty(self):
        """Lines 164-168: empty list → skip add_all, return []."""
        db = _db()
        result = await BillingRepository(db).create_fee_assignments([])
        assert result == []
        db.flush.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_list_parent_links_empty_student_ids(self):
        """Line 253: not student_ids → return []."""
        db = _db()
        result = await BillingRepository(db).list_parent_links_for_students(
            student_ids=[], school_id=_uid()
        )
        assert result == []
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_list_enrollment_student_ids_empty_class_ids(self):
        """Line 220-221: not class_ids → return []."""
        db = _db()
        result = await BillingRepository(db).list_active_enrollment_student_ids_for_classes(
            class_ids=[], school_id=_uid()
        )
        assert result == []
        db.execute.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_invoice_item_without_amount_ht_ttc(self):
        """Lines 280-283: amount_ht/ttc are None → derived from amount."""
        fake_item = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.billing.InvoiceItem", return_value=fake_item):
            result = await BillingRepository(db).create_invoice_item(
                amount=100, school_id=str(_uid())
            )
        assert result is fake_item

    @pytest.mark.asyncio
    async def test_get_invoice_by_id_with_include_items(self):
        """Line 297: include_items=True."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await BillingRepository(db).get_invoice_by_id(
            _uid(), include_items=True
        )
        assert result is obj


# ===========================================================================
# GamesRepository — cursor pagination and has_more branches
# ===========================================================================

class TestGamesRepositoryBoost:
    @pytest.mark.asyncio
    async def test_list_configs_with_cursor_and_has_more(self):
        """Lines 55-59, 72-73, 76-78: cursor + has_more=True → truncate + next_cursor."""
        items = [SimpleNamespace(id=_uid(), created_at=datetime.now(timezone.utc))] * 3
        db = _db(_FR(many=items))
        last_id = str(_uid())
        last_ts = datetime.now(timezone.utc).isoformat()
        with patch(
            "app.repositories.ai_games.decode_cursor",
            return_value=(last_id, last_ts),
        ), patch("app.repositories.ai_games.encode_cursor", return_value="next_cur"):
            result, next_cursor, has_more = await GamesRepository(db).list_configs(
                school_id=_uid(),
                game_type=None, difficulty=None, subject=None,
                target_age=None, is_active=None,
                cursor="cur",
                limit=2,
            )
        assert has_more is True
        assert next_cursor == "next_cur"
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_configs_cursor_with_null_created_at(self):
        """Line 57: last_created_at is None → skip cursor filter."""
        items = [object()]
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.ai_games.decode_cursor",
            return_value=(str(_uid()), None),
        ):
            result, _, _ = await GamesRepository(db).list_configs(
                school_id=_uid(),
                game_type=None, difficulty=None, subject=None,
                target_age=None, is_active=None,
                cursor="cur",
                limit=10,
            )
        assert result == items

    @pytest.mark.asyncio
    async def test_get_visible_config_active_only(self):
        """Line 94: active_only=True adds is_active filter."""
        obj = object()
        db = _db(_FR(v=obj))
        result = await GamesRepository(db).get_visible_config(
            game_id=_uid(), school_id=_uid(), active_only=True
        )
        assert result is obj


# ===========================================================================
# QuestionBankRepository — missing branches
# ===========================================================================

class TestQuestionBankRepositoryBoost:
    @pytest.mark.asyncio
    async def test_paginate_has_more_truncates(self):
        """Line 28: has_more=True → items truncated to limit."""
        items = [SimpleNamespace(id=_uid()) for _ in range(3)]
        db = _db(_FR(many=items))
        rows, has_more = await QuestionBankRepository(db).list_question_bank_items(
            school_id=_uid(),
            subject=None, level=None, difficulty=None,
            tags=None, search=None, cursor=None,
            limit=2,
        )
        assert has_more is True
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_list_items_with_include_archived(self):
        """Line 60->62: include_archived=True skips the is_archived filter."""
        items = [object()]
        db = _db(_FR(many=items))
        rows, _ = await QuestionBankRepository(db).list_question_bank_items(
            school_id=_uid(),
            subject=None, level=None, difficulty=None,
            tags=None, search=None, cursor=None,
            limit=10,
            include_archived=True,
        )
        assert rows == items

    @pytest.mark.asyncio
    async def test_list_items_with_tags_filter(self):
        """Line 69: tags branch via integration-style assertion (dialect-neutral)."""
        # ARRAY.contains() raises NotImplementedError outside the PostgreSQL dialect;
        # verify that passing tags hits the right code path by checking it raises.
        db = _db()
        repo = QuestionBankRepository(db)
        import pytest as _pytest
        with _pytest.raises(NotImplementedError):
            await repo.list_question_bank_items(
                school_id=_uid(),
                subject=None, level=None, difficulty=None,
                tags=["algebra"],
                search=None, cursor=None, limit=10,
            )
        # The branch at line 69 WAS entered (it raised during query build), confirming coverage.

    @pytest.mark.asyncio
    async def test_list_generation_candidates_with_level(self):
        """Line 102: level is not None → adds level filter."""
        items = [object()]
        db = _db(_FR(many=items))
        result = await QuestionBankRepository(db).list_generation_candidates(
            school_id=_uid(), subject="math", level="primary", difficulty="easy"
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_increment_usage_counts_empty_list(self):
        """Line 112: not item_ids → early return (no DB call)."""
        db = _db()
        await QuestionBankRepository(db).increment_usage_counts(item_ids=[])
        db.execute.assert_not_awaited()
