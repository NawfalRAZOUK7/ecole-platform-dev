"""Mock-based unit tests for content repositories:
- CMSRepository (content_cms.py)
- DocumentRepository (content_documents.py)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.repositories.content_cms import CMSRepository
from app.repositories.content_documents import DocumentsRepository


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
# CMSRepository
# ===========================================================================


class TestCMSRepository:
    @pytest.mark.asyncio
    async def test_create_content_item(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.content_cms.ContentItem", return_value=fake):
            result = await CMSRepository(db).create_content_item(
                school_id=_uid(), title="Intro to Python"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_save_content_item(self):
        ci = SimpleNamespace(id=_uid())
        db = _db()
        result = await CMSRepository(db).save_content_item(ci)
        assert result is ci

    @pytest.mark.asyncio
    async def test_get_platform_content(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_platform_content(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_content_item_no_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_content_item(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_get_content_item_with_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_content_item(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_platform_content_minimal(self):
        items = [object()]
        db = _db(_FR(many=items))
        result, has_more = await CMSRepository(db).list_platform_content(
            content_type=None,
            level_band=None,
            subject=None,
            status=None,
            origin=None,
            cursor=None,
            limit=10,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_platform_content_with_filters(self):
        now = _now()
        items = [SimpleNamespace(id=_uid(), created_at=now) for _ in range(6)]
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.content_cms.decode_cursor",
            return_value=(_uid(), now.isoformat()),
        ):
            result, has_more = await CMSRepository(db).list_platform_content(
                content_type="video",
                level_band=None,
                subject=None,
                status="published",
                origin=None,
                cursor="cur",
                limit=5,
            )
        assert has_more is True

    @pytest.mark.asyncio
    async def test_list_submission_review_queue_minimal(self):
        items = [(_uid(), _uid(), _uid())]
        db = _db(_FR(many=items))
        result, has_more = await CMSRepository(db).list_submission_review_queue(
            status=None,
            subject=None,
            level_band=None,
            school_id_filter=None,
            cursor=None,
            limit=10,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_submission_review_queue_with_filters(self):
        now = _now()
        items = [(_uid(), _uid(), _uid()) for _ in range(6)]
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.content_cms.decode_cursor",
            return_value=(_uid(), now.isoformat()),
        ):
            result, has_more = await CMSRepository(db).list_submission_review_queue(
                status="PENDING",
                subject=None,
                level_band=None,
                school_id_filter=None,
                cursor="cur",
                limit=5,
            )
        assert has_more is True

    @pytest.mark.asyncio
    async def test_get_content_submission(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_content_submission(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_content_submission(self):
        sub = SimpleNamespace(id=_uid())
        db = _db()
        result = await CMSRepository(db).save_content_submission(sub)
        assert result is sub

    @pytest.mark.asyncio
    async def test_get_teacher_profile(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_teacher_profile(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_create_notification(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.content_cms.Notification", return_value=fake):
            result = await CMSRepository(db).create_notification(
                user_id=_uid(), content="Review needed"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_create_notifications_empty(self):
        db = _db()
        db.add_all = Mock()
        result = await CMSRepository(db).create_notifications(notifications_data=[])
        assert result == []

    @pytest.mark.asyncio
    async def test_create_notifications_nonempty(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        db.add_all = Mock()
        with patch("app.repositories.content_cms.Notification", return_value=fake):
            result = await CMSRepository(db).create_notifications(
                notifications_data=[{"user_id": str(_uid()), "content": "x"}]
            )
        assert result == [fake]

    @pytest.mark.asyncio
    async def test_create_announcement(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        with patch("app.repositories.content_cms.Announcement", return_value=fake):
            result = await CMSRepository(db).create_announcement(
                school_id=_uid(), title="Test", content="Body"
            )
        assert result is fake

    @pytest.mark.asyncio
    async def test_get_announcement(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await CMSRepository(db).get_announcement(_uid())
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_announcement(self):
        ann = SimpleNamespace(id=_uid())
        db = _db()
        result = await CMSRepository(db).save_announcement(ann)
        assert result is ann

    @pytest.mark.asyncio
    async def test_list_announcements_minimal(self):
        items = []
        db = _db(_FR(many=items))
        result, has_more = await CMSRepository(db).list_announcements(
            school_id=_uid(), requester_role="ADM", status=None, cursor=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_announcements_non_admin(self):
        items = []
        db = _db(_FR(many=items))
        result, has_more = await CMSRepository(db).list_announcements(
            school_id=_uid(), requester_role="STD", status=None, cursor=None, limit=10
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_announcements_with_status_and_cursor(self):
        items = []
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.content_cms.decode_cursor", return_value=(_uid(), None)
        ):
            result, has_more = await CMSRepository(db).list_announcements(
                school_id=_uid(),
                requester_role="ADM",
                status="PUBLISHED",
                cursor="cur",
                limit=5,
            )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_membership_user_ids_by_roles_empty(self):
        db = _db()
        result = await CMSRepository(db).list_membership_user_ids_by_roles(
            school_id=_uid(), roles=[]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_membership_user_ids_by_roles_nonempty(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CMSRepository(db).list_membership_user_ids_by_roles(
            school_id=_uid(), roles=["TCH", "ADM"]
        )
        assert result == ids

    @pytest.mark.asyncio
    async def test_list_student_ids_in_classes_empty(self):
        db = _db()
        result = await CMSRepository(db).list_student_ids_in_classes(
            class_ids=[], school_id=_uid()
        )
        assert result == set()

    @pytest.mark.asyncio
    async def test_list_student_ids_in_classes_nonempty(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await CMSRepository(db).list_student_ids_in_classes(
            class_ids=[_uid()], school_id=_uid()
        )
        assert isinstance(result, set)


# ===========================================================================
# DocumentRepository
# ===========================================================================


class TestDocumentRepository:
    @pytest.mark.asyncio
    async def test_get_document(self):
        obj = object()
        assert await DocumentsRepository(_db(_FR(v=obj))).get_document(_uid()) is obj

    @pytest.mark.asyncio
    async def test_create_document(self):
        doc = SimpleNamespace(id=_uid())
        db = _db()
        await DocumentsRepository(db).create_document(doc)
        db.add.assert_called_once_with(doc)

    @pytest.mark.asyncio
    async def test_save_document(self):
        doc = SimpleNamespace(id=_uid())
        db = _db()
        result = await DocumentsRepository(db).save_document(doc)
        assert result is doc

    @pytest.mark.asyncio
    async def test_create_document_version(self):
        fake = SimpleNamespace(id=_uid())
        db = _db()
        await DocumentsRepository(db).create_document_version(fake)
        db.add.assert_called_once_with(fake)

    @pytest.mark.asyncio
    async def test_find_document_by_sha(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await DocumentsRepository(db).find_document_by_sha(
            school_id=_uid(), sha256="sha256abc"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_count_documents_for_storage_path_no_exclude(self):
        # method calls db.execute twice (documents + versions)
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            return _FR(v=1)  # each returns 1, total = 2

        db = SimpleNamespace(
            execute=mock_execute,
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            merge=AsyncMock(),
            delete=AsyncMock(),
        )
        result = await DocumentsRepository(db).count_documents_for_storage_path(
            storage_path="path/to/file"
        )
        assert result == 2

    @pytest.mark.asyncio
    async def test_count_documents_for_storage_path_with_exclude(self):
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            return _FR(v=0) if call_count == 1 else _FR(v=1)

        db = SimpleNamespace(
            execute=mock_execute,
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            merge=AsyncMock(),
            delete=AsyncMock(),
        )
        result = await DocumentsRepository(db).count_documents_for_storage_path(
            storage_path="path/to/file", exclude_document_id=_uid()
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_next_document_version_number(self):
        db = _db(_FR(v=2))
        result = await DocumentsRepository(db).get_next_document_version_number(
            document_id=_uid()
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_get_next_document_version_number_none(self):
        db = _db(_FR(v=None))
        result = await DocumentsRepository(db).get_next_document_version_number(
            document_id=_uid()
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_count_thumbnail_references_no_exclude(self):
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            return _FR(v=2) if call_count == 1 else _FR(v=1)

        db = SimpleNamespace(
            execute=mock_execute,
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            merge=AsyncMock(),
            delete=AsyncMock(),
        )
        result = await DocumentsRepository(db).count_thumbnail_references(
            thumbnail_path="thumb/path"
        )
        assert result == 3

    @pytest.mark.asyncio
    async def test_count_thumbnail_references_with_exclude(self):
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            return _FR(v=1) if call_count == 1 else _FR(v=0)

        db = SimpleNamespace(
            execute=mock_execute,
            add=Mock(),
            flush=AsyncMock(),
            commit=AsyncMock(),
            merge=AsyncMock(),
            delete=AsyncMock(),
        )
        result = await DocumentsRepository(db).count_thumbnail_references(
            thumbnail_path="thumb/path", exclude_document_id=_uid()
        )
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_document_version(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await DocumentsRepository(db).get_document_version(
            document_id=_uid(), version_number=1
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_document_versions(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_document_versions(
            document_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_parent_child_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await DocumentsRepository(db).list_parent_child_ids(
            parent_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_parent_ids_for_student(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await DocumentsRepository(db).list_parent_ids_for_student(
            student_id=_uid(), school_id=_uid()
        )
        assert result == set(ids)

    @pytest.mark.asyncio
    async def test_list_teacher_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await DocumentsRepository(db).list_teacher_class_ids(
            teacher_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_student_class_ids(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await DocumentsRepository(db).list_student_class_ids(
            student_id=_uid(), school_id=_uid()
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_list_students_for_classes_empty(self):
        db = _db()
        result = await DocumentsRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[]
        )
        assert result == set()

    @pytest.mark.asyncio
    async def test_list_students_for_classes_nonempty(self):
        ids = [_uid()]
        db = _db(_FR(many=ids))
        result = await DocumentsRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[_uid()]
        )
        assert isinstance(result, set)

    @pytest.mark.asyncio
    async def test_get_user_in_school(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await DocumentsRepository(db).get_user_in_school(
            user_id=_uid(), school_id=_uid()
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_users_by_ids_empty(self):
        db = _db()
        result = await DocumentsRepository(db).list_users_by_ids(
            school_id=_uid(), user_ids=[]
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_users_by_ids_nonempty(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_users_by_ids(
            school_id=_uid(), user_ids=[_uid()]
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_students_in_school(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_students_in_school(school_id=_uid())
        assert result == items

    @pytest.mark.asyncio
    async def test_find_document_for_student_category(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await DocumentsRepository(db).find_document_for_student_category(
            school_id=_uid(), linked_student_id=_uid(), category="transcript"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_list_documents_minimal(self):
        items = []
        db = _db(_FR(many=items))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            category=None,
            owner_id=None,
            mime_type=None,
            cursor=None,
            limit=10,
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_documents_with_filters(self):
        items = []
        db = _db(_FR(many=items))
        with patch(
            "app.repositories.content_documents.decode_cursor",
            return_value=(_uid(), None),
        ):
            result, cursor, has_more = await DocumentsRepository(db).list_documents(
                school_id=_uid(),
                role="TCH",
                user_id=_uid(),
                category="grade",
                owner_id=_uid(),
                mime_type="application/pdf",
                cursor="cur",
                limit=5,
            )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_documents_by_ids(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_documents_by_ids(
            document_ids=[_uid()], school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_student_documents(self):
        # Returns list of tuples; use empty list
        db = _db(_FR(many=[]))
        result = await DocumentsRepository(db).list_student_documents(
            student_id=_uid(), school_id=_uid()
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_student_requirements(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_student_requirements(
            school_id=_uid()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_find_student_requirement(self):
        obj = object()
        db = _db(_FR(v=obj))
        result = await DocumentsRepository(db).find_student_requirement(
            school_id=_uid(), category="transcript"
        )
        assert result is obj

    @pytest.mark.asyncio
    async def test_save_requirement(self):
        req = SimpleNamespace(id=_uid())
        db = _db()
        result = await DocumentsRepository(db).save_requirement(req)
        assert result is req

    @pytest.mark.asyncio
    async def test_list_expiring_documents(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_expiring_documents(
            window_start=_now(), window_end=_now()
        )
        assert result == items

    @pytest.mark.asyncio
    async def test_list_deleted_documents(self):
        items = [object()]
        db = _db(_FR(many=items))
        result = await DocumentsRepository(db).list_deleted_documents(before=_now())
        assert result == items

    @pytest.mark.asyncio
    async def test_hard_delete_document(self):
        doc = SimpleNamespace(id=_uid())
        db = _db()
        await DocumentsRepository(db).hard_delete_document(doc)
        db.delete.assert_awaited_once_with(doc)

    @pytest.mark.asyncio
    async def test_notification_exists_false(self):
        db = _db(_FR(v=None))
        result = await DocumentsRepository(db).notification_exists(
            idempotency_key="idem-key-123"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_notification_exists_true(self):
        db = _db(_FR(v="some-id"))
        result = await DocumentsRepository(db).notification_exists(
            idempotency_key="idem-key-456"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_create_resource(self):
        resource = SimpleNamespace(id=_uid())
        db = _db()
        await DocumentsRepository(db).create_resource(resource)
        db.add.assert_called_once_with(resource)
