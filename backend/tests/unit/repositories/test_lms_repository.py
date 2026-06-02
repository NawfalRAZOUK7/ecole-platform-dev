"""Mock-based unit tests for app/repositories/lms.py.

Covers: LMSRepository (all public methods), AssignmentRepository,
AssessmentRepository, and helper _dt_to_iso.  All DB calls are mocked.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.repositories.lms import (
    AssessmentRepository,
    AssignmentRepository,
    LMSRepository,
    _dt_to_iso,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

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
        return self._v

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
        flush=AsyncMock(),
        commit=AsyncMock(),
        delete=AsyncMock(),
    )
    if side_effects:
        db.execute.side_effect = side_effects
    return db


def _fake_filter():
    return SimpleNamespace(filters=[], sort=[], search=None)


def _fake_fs():
    """Fake FilterSpec/SortSpec objects (the repo calls apply_filters/apply_sort)."""
    fs = MagicMock()
    return fs


# ---------------------------------------------------------------------------
# _dt_to_iso helper
# ---------------------------------------------------------------------------

def test_dt_to_iso_with_value():
    dt = _now()
    assert _dt_to_iso(dt) == dt.isoformat()


def test_dt_to_iso_none():
    assert _dt_to_iso(None) is None


# ---------------------------------------------------------------------------
# _paginate_scalars / _paginate_rows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_paginate_scalars_no_more():
    items = [object(), object()]
    db = _db(_FR(many=items))
    repo = LMSRepository(db)
    result, has_more = await repo._paginate_scalars(MagicMock(), limit=5)
    assert result == items
    assert has_more is False


@pytest.mark.asyncio
async def test_paginate_scalars_has_more():
    items = [object() for _ in range(6)]
    db = _db(_FR(many=items))
    repo = LMSRepository(db)
    result, has_more = await repo._paginate_scalars(MagicMock(), limit=5)
    assert len(result) == 5
    assert has_more is True


@pytest.mark.asyncio
async def test_paginate_rows_no_more():
    db = _db(_FR(many=["a", "b"]))
    repo = LMSRepository(db)
    result, has_more = await repo._paginate_rows(MagicMock(), limit=5)
    assert result == ["a", "b"]
    assert has_more is False


@pytest.mark.asyncio
async def test_paginate_rows_has_more():
    rows = list(range(6))
    db = _db(_FR(many=rows))
    repo = LMSRepository(db)
    result, has_more = await repo._paginate_rows(MagicMock(), limit=5)
    assert len(result) == 5
    assert has_more is True


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_user():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_user(_uid()) is obj


# ---------------------------------------------------------------------------
# list_activities
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_activities_minimal():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_activities(
            school_id=_uid(),
            activity_type=None,
            difficulty=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_activities_with_all_filters():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_search", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)),
    ):
        result, _ = await LMSRepository(db).list_activities(
            school_id=_uid(),
            activity_type="quiz",
            difficulty="easy",
            filters=MagicMock(),
            sort=MagicMock(),
            search="math",
            cursor="cur",
            limit=5,
        )
    assert result == items


# ---------------------------------------------------------------------------
# get_activity / get_next_activity_attempt_no / create_activity_session
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_activity():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_activity(_uid()) is obj


@pytest.mark.asyncio
async def test_get_next_activity_attempt_no():
    db = _db(_FR(scalar=2))
    result = await LMSRepository(db).get_next_activity_attempt_no(
        student_id=_uid(), activity_id=_uid()
    )
    assert result == 3


@pytest.mark.asyncio
async def test_get_next_activity_attempt_no_none():
    db = _db(_FR(scalar=None))
    result = await LMSRepository(db).get_next_activity_attempt_no(
        student_id=_uid(), activity_id=_uid()
    )
    assert result == 1


@pytest.mark.asyncio
async def test_create_activity_session():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.ActivitySession", return_value=fake):
        result = await LMSRepository(db).create_activity_session(
            student_id=_uid(), activity_id=_uid(), attempt_no=1
        )
    assert result is fake


@pytest.mark.asyncio
async def test_get_activity_session():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_activity_session(_uid()) is obj


@pytest.mark.asyncio
async def test_save_activity_session():
    sess = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_activity_session(sess)
    assert result is sess
    db.add.assert_called_once_with(sess)


# ---------------------------------------------------------------------------
# Class / Teacher / Parent / Student helpers
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_class():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_class(_uid()) is obj


@pytest.mark.asyncio
async def test_list_teacher_class_ids():
    cid = _uid()
    db = _db(_FR(many=[cid]))
    result = await LMSRepository(db).list_teacher_class_ids(
        teacher_id=_uid(), school_id=_uid()
    )
    assert cid in result


@pytest.mark.asyncio
async def test_list_parent_child_ids():
    cid = _uid()
    db = _db(_FR(many=[cid]))
    result = await LMSRepository(db).list_parent_child_ids(
        parent_id=_uid(), school_id=_uid()
    )
    assert cid in result


@pytest.mark.asyncio
async def test_list_student_class_ids():
    cid = _uid()
    db = _db(_FR(many=[cid]))
    result = await LMSRepository(db).list_student_class_ids(
        student_id=_uid(), school_id=_uid()
    )
    assert cid in result


@pytest.mark.asyncio
async def test_student_is_enrolled_in_class_true():
    db = _db(_FR(scalar=True))
    result = await LMSRepository(db).student_is_enrolled_in_class(
        student_id=_uid(), class_id=_uid()
    )
    assert result is True


@pytest.mark.asyncio
async def test_student_is_enrolled_in_class_false():
    db = _db(_FR(scalar=False))
    result = await LMSRepository(db).student_is_enrolled_in_class(
        student_id=_uid(), class_id=_uid()
    )
    assert result is False


# ---------------------------------------------------------------------------
# Course CRUD + list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_course():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_course(_uid()) is obj


@pytest.mark.asyncio
async def test_create_course():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.Course", return_value=fake):
        result = await LMSRepository(db).create_course(school_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_list_courses_no_class_no_teacher():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_courses(
            school_id=_uid(),
            class_id=None,
            teacher_class_ids=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_courses_with_class_and_search():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_search", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)),
    ):
        result, _ = await LMSRepository(db).list_courses(
            school_id=_uid(),
            class_id=_uid(),
            teacher_class_ids=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search="bio",
            cursor="cursor",
            limit=5,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_courses_empty_teacher_class_ids():
    db = _db(_FR(many=[]))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, has_more = await LMSRepository(db).list_courses(
            school_id=_uid(),
            class_id=None,
            teacher_class_ids=set(),  # empty set → early return
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == []
    assert has_more is False


# ---------------------------------------------------------------------------
# Assignment CRUD + list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_assignment():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_assignment(_uid()) is obj


@pytest.mark.asyncio
async def test_get_assignment_with_course_found():
    assignment = SimpleNamespace(id=_uid())
    course = SimpleNamespace(id=_uid())
    row = (assignment, course)
    db = _db(_FR(v=row))
    result = await LMSRepository(db).get_assignment_with_course(_uid())
    assert result == (assignment, course)


@pytest.mark.asyncio
async def test_get_assignment_with_course_not_found():
    db = _db(_FR(v=None))
    result = await LMSRepository(db).get_assignment_with_course(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_create_assignment():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.Assignment", return_value=fake):
        result = await LMSRepository(db).create_assignment(course_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_save_assignment():
    asgn = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_assignment(asgn)
    assert result is asgn


@pytest.mark.asyncio
async def test_list_assignments_with_course():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_assignments(
            school_id=_uid(),
            course_id=_uid(),
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_assignments_no_course():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_search", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)),
    ):
        result, _ = await LMSRepository(db).list_assignments(
            school_id=_uid(),
            course_id=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search="txt",
            cursor="cur",
            limit=5,
        )
    assert result == items


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_submission():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_submission(_uid()) is obj


@pytest.mark.asyncio
async def test_get_submission_with_context_found():
    sub = SimpleNamespace(id=_uid())
    asgn = SimpleNamespace(id=_uid())
    course = SimpleNamespace(id=_uid())
    row = (sub, asgn, course)
    db = _db(_FR(v=row))
    result = await LMSRepository(db).get_submission_with_context(_uid())
    assert result == (sub, asgn, course)


@pytest.mark.asyncio
async def test_get_submission_with_context_not_found():
    db = _db(_FR(v=None))
    result = await LMSRepository(db).get_submission_with_context(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_find_active_submission():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).find_active_submission(
        assignment_id=_uid(), student_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_create_submission():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.Submission", return_value=fake):
        result = await LMSRepository(db).create_submission(assignment_id=_uid(), student_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_save_submission():
    sub = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_submission(sub)
    assert result is sub


# ---------------------------------------------------------------------------
# Grade
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_grade_for_submission():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_grade_for_submission(_uid()) is obj


@pytest.mark.asyncio
async def test_create_grade():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.Grade", return_value=fake):
        result = await LMSRepository(db).create_grade(submission_id=_uid(), score=9.5)
    assert result is fake


@pytest.mark.asyncio
async def test_save_grade():
    grade = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_grade(grade)
    assert result is grade


# ---------------------------------------------------------------------------
# SubmissionFile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_count_submission_files():
    db = _db(_FR(scalar=3))
    result = await LMSRepository(db).count_submission_files(_uid())
    assert result == 3


@pytest.mark.asyncio
async def test_create_submission_file():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.SubmissionFile", return_value=fake):
        result = await LMSRepository(db).create_submission_file(submission_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_submission_file_found():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_submission_file(
        submission_id=_uid(), file_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_get_submission_file_no_submission():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_submission_file(
        submission_id=_uid(), file_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_list_submission_files():
    items = [object()]
    db = _db(_FR(many=items))
    result = await LMSRepository(db).list_submission_files(_uid())
    assert result == items


# ---------------------------------------------------------------------------
# ContentItem
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_content_item():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_content_item(_uid()) is obj


@pytest.mark.asyncio
async def test_list_content_items_minimal():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_content_items(
            school_id=_uid(),
            content_type=None,
            level_band=None,
            language=None,
            letter=None,
            target_age=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_content_items_empty_teacher_class_ids():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, has_more = await LMSRepository(db).list_content_items(
            school_id=_uid(),
            content_type=None,
            level_band=None,
            language=None,
            letter=None,
            target_age=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_content_items_with_all_params():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_search", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)),
    ):
        result, _ = await LMSRepository(db).list_content_items(
            school_id=_uid(),
            content_type="video",
            level_band="primary",
            language="fr",
            letter=None,
            target_age=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search="math",
            cursor="cur",
            limit=5,
        )
    assert result == items


# ---------------------------------------------------------------------------
# ContentProgress
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_content_progress_no_student():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_content_progress(
        content_item_id=_uid(), student_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_get_content_progress_with_student():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_content_progress(
        content_item_id=_uid(), student_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_create_content_progress():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.ContentProgress", return_value=fake):
        result = await LMSRepository(db).create_content_progress(
            content_item_id=_uid(), student_id=_uid()
        )
    assert result is fake


@pytest.mark.asyncio
async def test_save_content_progress():
    cp = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_content_progress(cp)
    assert result is cp


@pytest.mark.asyncio
async def test_save_content_item():
    ci = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_content_item(ci)
    assert result is ci


# ---------------------------------------------------------------------------
# ContentItemAsset
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_content_asset_no_type():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_content_asset(
        content_item_id=_uid(), asset_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_get_content_asset_with_type():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_content_asset(
        content_item_id=_uid(), asset_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_list_content_assets_no_type():
    items = [object()]
    db = _db(_FR(many=items))
    result = await LMSRepository(db).list_content_assets(
        content_item_id=_uid()
    )
    assert result == items


@pytest.mark.asyncio
async def test_list_content_assets_with_type():
    items = [object()]
    db = _db(_FR(many=items))
    result = await LMSRepository(db).list_content_assets(
        content_item_id=_uid(), page_only=True
    )
    assert result == items


@pytest.mark.asyncio
async def test_create_content_asset():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.ContentItemAsset", return_value=fake):
        result = await LMSRepository(db).create_content_asset(content_item_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_save_content_asset():
    asset = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_content_asset(asset)
    assert result is asset


@pytest.mark.asyncio
async def test_delete_content_asset():
    asset = SimpleNamespace(id=_uid())
    db = _db()
    await LMSRepository(db).delete_content_asset(asset)
    db.delete.assert_awaited_once_with(asset)


# ---------------------------------------------------------------------------
# browse_content_library
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_browse_content_library_minimal():
    items = [object()]
    db = _db(_FR(many=items))
    result, _ = await LMSRepository(db).browse_content_library(
        school_id=_uid(),
        content_type=None,
        level_band=None,
        subject=None,
        language=None,
        origin=None,
        letter=None,
        target_age=None,
        cursor=None,
        limit=10,
    )
    assert result == items


@pytest.mark.asyncio
async def test_browse_content_library_all_params():
    items = [object()]
    db = _db(_FR(many=items))
    with patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)):
        result, _ = await LMSRepository(db).browse_content_library(
            school_id=_uid(),
            content_type="video",
            level_band=None,
            subject="science",
            language=None,
            origin=None,
            letter=None,
            target_age=None,
            cursor="cur",
            limit=5,
        )
    assert result == items


@pytest.mark.asyncio
async def test_browse_content_library_empty_teacher_ids():
    items = [object()]
    db = _db(_FR(many=items))
    result, has_more = await LMSRepository(db).browse_content_library(
        school_id=_uid(),
        content_type=None,
        level_band=None,
        subject=None,
        language=None,
        origin=None,
        letter=None,
        target_age=None,
        cursor=None,
        limit=10,
    )
    assert result == items


# ---------------------------------------------------------------------------
# ClassContentAssignment
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_class_content_assignment():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).find_class_content_assignment(
        content_item_id=_uid(), class_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_create_class_content_assignment():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.ClassContentAssignment", return_value=fake):
        result = await LMSRepository(db).create_class_content_assignment(
            content_item_id=_uid(), class_id=_uid()
        )
    assert result is fake


@pytest.mark.asyncio
async def test_get_class_content_assignment():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_class_content_assignment(_uid()) is obj


@pytest.mark.asyncio
async def test_delete_class_content_assignment():
    assignment = SimpleNamespace(id=_uid())
    db = _db()
    await LMSRepository(db).delete_class_content_assignment(assignment)
    db.delete.assert_awaited_once_with(assignment)
    db.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# ContentSubmission
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_active_content_submission():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).find_active_content_submission(
        content_item_id=_uid(), submitted_by=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_create_content_submission():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.ContentSubmission", return_value=fake):
        result = await LMSRepository(db).create_content_submission(
            content_item_id=_uid(), submitted_by=_uid()
        )
    assert result is fake


@pytest.mark.asyncio
async def test_list_my_content_submissions_no_filters():
    rows = [object()]
    db = _db(_FR(many=rows))
    result, _ = await LMSRepository(db).list_my_content_submissions(
        submitted_by=_uid(), status=None, cursor=None, limit=10
    )
    assert result == rows


@pytest.mark.asyncio
async def test_list_my_content_submissions_with_status_and_cursor():
    rows = [object()]
    db = _db(_FR(many=rows))
    with patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)):
        result, _ = await LMSRepository(db).list_my_content_submissions(
            submitted_by=_uid(), status="PENDING", cursor="cur", limit=5
        )
    assert result == rows


# ---------------------------------------------------------------------------
# Assessment CRUD + list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_assessment():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.Assessment", return_value=fake):
        result = await LMSRepository(db).create_assessment(class_id=_uid())
    assert result is fake


@pytest.mark.asyncio
async def test_get_assessment():
    obj = object()
    db = _db(_FR(v=obj))
    assert await LMSRepository(db).get_assessment(_uid()) is obj


@pytest.mark.asyncio
async def test_get_assessment_with_class_found():
    assessment = SimpleNamespace(id=_uid())
    class_room = SimpleNamespace(id=_uid())
    row = (assessment, class_room)
    db = _db(_FR(v=row))
    result = await LMSRepository(db).get_assessment_with_class(_uid())
    assert result == (assessment, class_room)


@pytest.mark.asyncio
async def test_get_assessment_with_class_not_found():
    db = _db(_FR(v=None))
    result = await LMSRepository(db).get_assessment_with_class(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_list_assessments_minimal():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_assessments(
            school_id=_uid(),
            class_id=None,
            status=None,
            teacher_class_ids=None,
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == items


@pytest.mark.asyncio
async def test_list_assessments_empty_teacher_ids():
    db = _db(_FR(many=[]))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
    ):
        result, _ = await LMSRepository(db).list_assessments(
            school_id=_uid(),
            class_id=None,
            status=None,
            teacher_class_ids=set(),
            filters=MagicMock(),
            sort=MagicMock(),
            search=None,
            cursor=None,
            limit=10,
        )
    assert result == []


@pytest.mark.asyncio
async def test_list_assessments_with_all_params():
    items = [object()]
    db = _db(_FR(many=items))
    with (
        patch("app.repositories.lms.apply_filters", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_sort", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.apply_search", side_effect=lambda q, *a, **kw: q),
        patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)),
    ):
        result, _ = await LMSRepository(db).list_assessments(
            school_id=_uid(),
            class_id=_uid(),
            status="published",
            teacher_class_ids={_uid()},
            filters=MagicMock(),
            sort=MagicMock(),
            search="history",
            cursor="cur",
            limit=5,
        )
    assert result == items


@pytest.mark.asyncio
async def test_save_assessment():
    assessment = SimpleNamespace(id=_uid())
    db = _db()
    result = await LMSRepository(db).save_assessment(assessment)
    assert result is assessment


# ---------------------------------------------------------------------------
# AssessmentResult
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_assessment_result_no_student():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_assessment_result(
        assessment_id=_uid(), student_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_get_assessment_result_with_student():
    obj = object()
    db = _db(_FR(v=obj))
    result = await LMSRepository(db).get_assessment_result(
        assessment_id=_uid(), student_id=_uid()
    )
    assert result is obj


@pytest.mark.asyncio
async def test_create_assessment_result():
    fake = SimpleNamespace(id=_uid())
    db = _db()
    with patch("app.repositories.lms.AssessmentResult", return_value=fake):
        result = await LMSRepository(db).create_assessment_result(assessment_id=_uid())
    assert result is fake


# ---------------------------------------------------------------------------
# list_results (the combined assignment+assessment list_results)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_lms_list_results_no_student_ids():
    rows = [("a", "b")]
    db = _db(_FR(many=rows))
    with patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)):
        result, _ = await LMSRepository(db).list_results(
            school_id=_uid(), student_ids=None, cursor="c", limit=10
        )
    assert result == rows


@pytest.mark.asyncio
async def test_lms_list_results_empty_student_ids():
    result, has_more = await LMSRepository(_db()).list_results(
        school_id=_uid(), student_ids=set(), cursor=None, limit=10
    )
    assert result == []
    assert has_more is False


@pytest.mark.asyncio
async def test_lms_list_results_with_student_ids():
    rows = [("a", "b")]
    db = _db(_FR(many=rows))
    result, _ = await LMSRepository(db).list_results(
        school_id=_uid(), student_ids={_uid()}, cursor=None, limit=10
    )
    assert result == rows


# ---------------------------------------------------------------------------
# list_class_content
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_class_content_minimal():
    rows = [object()]
    db = _db(_FR(many=rows))
    result, _ = await LMSRepository(db).list_class_content(
        school_id=_uid(), class_id=_uid(), cursor=None, limit=10
    )
    assert result == rows


@pytest.mark.asyncio
async def test_list_class_content_with_cursor():
    rows = [object()]
    db = _db(_FR(many=rows))
    with patch("app.repositories.lms.decode_cursor", return_value=(_uid(), None)):
        result, _ = await LMSRepository(db).list_class_content(
            school_id=_uid(), class_id=_uid(), cursor="cur", limit=5
        )
    assert result == rows


# ---------------------------------------------------------------------------
# AssignmentRepository (subclass)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assignment_repo_list_for_class_non_assigned_status():
    db = _db()
    repo = AssignmentRepository(db)
    result = await repo.list_for_class(_uid(), _uid(), status="graded")
    assert result == []


@pytest.mark.asyncio
async def test_assignment_repo_list_for_class_none_status():
    fake_asgn = SimpleNamespace(
        id=_uid(), title="T", due_at=None, total_points=10
    )
    db = _db(_FR(many=[fake_asgn]))
    repo = AssignmentRepository(db)
    result = await repo.list_for_class(_uid(), _uid(), status=None)
    assert len(result) == 1
    assert result[0]["title"] == "T"


@pytest.mark.asyncio
async def test_assignment_repo_list_for_class_assigned_status():
    fake_asgn = SimpleNamespace(
        id=_uid(), title="T2", due_at=None, total_points=5
    )
    db = _db(_FR(many=[fake_asgn]))
    repo = AssignmentRepository(db)
    result = await repo.list_for_class(_uid(), _uid(), status="assigned")
    assert len(result) == 1


@pytest.mark.asyncio
async def test_assignment_repo_list_for_student_no_classes():
    db = _db(_FR(many=[]))  # list_student_class_ids returns empty
    repo = AssignmentRepository(db)
    result = await repo.list_for_student(_uid(), _uid())
    assert result == []


@pytest.mark.asyncio
async def test_assignment_repo_get_detail_not_found():
    db = _db(_FR(v=None))
    repo = AssignmentRepository(db)
    result = await repo.get_detail(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_assignment_repo_get_detail_found():
    assignment = SimpleNamespace(
        id=_uid(), title="A", due_at=None, total_points=10,
        teacher_id=_uid(), description="desc",
        exercise_type="pdf", exercise_pdf_path=None
    )
    course = SimpleNamespace(id=_uid(), class_id=_uid())
    db = _db(_FR(v=(assignment, course)))
    repo = AssignmentRepository(db)
    result = await repo.get_detail(assignment.id)
    assert result is not None
    assert result["title"] == "A"


@pytest.mark.asyncio
async def test_assignment_repo_get_results_empty():
    db = _db(_FR(many=[]))
    repo = AssignmentRepository(db)
    result = await repo.get_results(_uid())
    assert result == []


@pytest.mark.asyncio
async def test_assignment_repo_get_results_with_grade():
    sub = SimpleNamespace(
        id=_uid(), student_id=_uid(), status="submitted",
        submitted_at=_now()
    )
    grade = SimpleNamespace(score=8.5, feedback_text="Good", published_at=_now())
    db = _db(_FR(many=[(sub, grade)]))
    repo = AssignmentRepository(db)
    result = await repo.get_results(_uid())
    assert len(result) == 1
    assert result[0]["score"] == 8.5


@pytest.mark.asyncio
async def test_assignment_repo_get_results_no_grade():
    sub = SimpleNamespace(
        id=_uid(), student_id=_uid(), status="submitted", submitted_at=None
    )
    db = _db(_FR(many=[(sub, None)]))
    repo = AssignmentRepository(db)
    result = await repo.get_results(_uid())
    assert result[0]["score"] is None


# ---------------------------------------------------------------------------
# AssessmentRepository (subclass)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_assessment_repo_list_for_class_no_status():
    fake = SimpleNamespace(id=_uid(), title="Math", due_at=None, total_points=20, status="open")
    db = _db(_FR(many=[fake]))
    repo = AssessmentRepository(db)
    result = await repo.list_for_class(_uid(), _uid(), status=None)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_assessment_repo_list_for_class_with_status_filter():
    fake = SimpleNamespace(id=_uid(), title="Math", due_at=None, total_points=20, status="open")
    db = _db(_FR(many=[fake]))
    repo = AssessmentRepository(db)
    result = await repo.list_for_class(_uid(), _uid(), status="closed")
    assert result == []  # status mismatch filtered out


@pytest.mark.asyncio
async def test_assessment_repo_list_for_student_no_classes():
    db = _db(_FR(many=[]))
    repo = AssessmentRepository(db)
    result = await repo.list_for_student(_uid(), _uid())
    assert result == []


@pytest.mark.asyncio
async def test_assessment_repo_get_detail_not_found():
    db = _db(_FR(v=None))
    repo = AssessmentRepository(db)
    result = await repo.get_detail(_uid())
    assert result is None


@pytest.mark.asyncio
async def test_assessment_repo_get_detail_found():
    assessment = SimpleNamespace(
        id=_uid(), title="Bio", due_at=None, total_points=15,
        status="open", teacher_id=_uid(), window_end=None
    )
    class_room = SimpleNamespace(id=_uid())
    db = _db(_FR(v=(assessment, class_room)))
    repo = AssessmentRepository(db)
    result = await repo.get_detail(assessment.id)
    assert result is not None
    assert result["title"] == "Bio"


@pytest.mark.asyncio
async def test_assessment_repo_get_results_empty():
    db = _db(_FR(many=[]))
    result = await AssessmentRepository(db).get_results(_uid())
    assert result == []


@pytest.mark.asyncio
async def test_assessment_repo_get_results_with_scores():
    row = SimpleNamespace(
        student_id=_uid(), status="graded", score=14.0, created_at=_now()
    )
    db = _db(_FR(many=[row]))
    result = await AssessmentRepository(db).get_results(_uid())
    assert result[0]["score"] == 14.0


@pytest.mark.asyncio
async def test_assessment_repo_get_results_no_score():
    row = SimpleNamespace(
        student_id=_uid(), status="submitted", score=None, created_at=_now()
    )
    db = _db(_FR(many=[row]))
    result = await AssessmentRepository(db).get_results(_uid())
    assert result[0]["score"] is None
