"""Extended coverage tests for content_documents.py."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, MagicMock

import pytest

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


class TestDocumentsRepositoryExtended:
    """Cover missing lines in content_documents.py."""

    @pytest.mark.asyncio
    async def test_list_documents_no_filters_admin(self):
        """Cover list_documents for ADM role (lines 290-380)."""
        doc = MagicMock()
        doc.id = _uid()
        doc.created_at = _now()
        row = (doc, "Uploader Name", None)
        db = _db(_FR(many=[row]))
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
        assert len(result) == 1
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_documents_par_role_with_student_ids(self):
        """Cover PAR role with allowed_student_ids (lines 323-330)."""
        doc = MagicMock()
        doc.id = _uid()
        doc.created_at = _now()
        row = (doc, "Uploader", "Student")
        db = _db(_FR(many=[row]))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="PAR",
            user_id=_uid(),
            category="report",
            owner_id=None,
            mime_type=None,
            cursor=None,
            limit=10,
            allowed_student_ids={_uid(), _uid()},
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_documents_par_role_no_student_ids(self):
        """Cover PAR role with empty allowed_student_ids (line 329: else False)."""
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="PAR",
            user_id=_uid(),
            category=None,
            owner_id=None,
            mime_type=None,
            cursor=None,
            limit=10,
            allowed_student_ids=set(),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_documents_tch_role_with_student_ids(self):
        """Cover TCH role with visible student ids (lines 332-340)."""
        doc = MagicMock()
        doc.id = _uid()
        doc.created_at = _now()
        row = (doc, "T", None)
        db = _db(_FR(many=[row]))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="TCH",
            user_id=_uid(),
            category=None,
            owner_id=_uid(),
            mime_type="application/pdf",
            cursor=None,
            limit=10,
            allowed_student_ids={_uid()},
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_documents_std_role(self):
        """Cover STD role (lines 341-347)."""
        doc = MagicMock()
        doc.id = _uid()
        doc.created_at = _now()
        row = (doc, None, None)
        db = _db(_FR(many=[row]))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="STD",
            user_id=_uid(),
            category=None,
            owner_id=None,
            mime_type=None,
            cursor=None,
            limit=10,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_documents_has_more_and_cursor(self):
        """Cover has_more=True and next_cursor generation (lines 352-369)."""
        doc = MagicMock()
        doc.id = _uid()
        doc.created_at = _now()
        rows = [(doc, None, None)] * 3
        db = _db(_FR(many=rows))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            category=None,
            owner_id=None,
            mime_type=None,
            cursor=None,
            limit=2,
        )
        assert has_more is True
        assert cursor is not None
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_documents_with_cursor_filter(self):
        """Cover cursor-based filtering (lines 350-359)."""
        from app.core.response import encode_cursor

        uid = _uid()
        cursor_str = encode_cursor(uid, _now().isoformat())
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_documents(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            category=None,
            owner_id=None,
            mime_type=None,
            cursor=cursor_str,
            limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_documents_by_ids_empty(self):
        """Cover empty document_ids early return (line 390)."""
        db = _db()
        result = await DocumentsRepository(db).list_documents_by_ids(
            school_id=_uid(), document_ids=[]
        )
        assert result == []
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_documents_by_ids_nonempty(self):
        """Cover non-empty document_ids path."""
        doc = MagicMock()
        doc.id = _uid()
        db = _db(_FR(many=[doc]))
        result = await DocumentsRepository(db).list_documents_by_ids(
            school_id=_uid(), document_ids=[_uid()]
        )
        assert result == [doc]

    @pytest.mark.asyncio
    async def test_list_users_by_ids_empty(self):
        """Cover empty user_ids early return (line 243)."""
        db = _db()
        result = await DocumentsRepository(db).list_users_by_ids(
            school_id=_uid(), user_ids=[]
        )
        assert result == []
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_users_by_ids_nonempty(self):
        """Cover non-empty user_ids path."""
        user = MagicMock()
        user.id = _uid()
        db = _db(_FR(many=[user]))
        result = await DocumentsRepository(db).list_users_by_ids(
            school_id=_uid(), user_ids=[_uid()]
        )
        assert result == [user]

    @pytest.mark.asyncio
    async def test_list_students_for_classes_empty(self):
        """Cover empty class_ids early return (line 213-215)."""
        db = _db()
        result = await DocumentsRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[]
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_students_for_classes_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await DocumentsRepository(db).list_students_for_classes(
            school_id=_uid(), class_ids=[_uid()]
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_save_resource_and_create_resource(self):
        """Cover create_resource and save_resource (lines 499-507)."""
        resource = MagicMock()
        resource.id = _uid()
        db = _db()
        result = await DocumentsRepository(db).create_resource(resource)
        db.add.assert_called_with(resource)
        assert result is resource

        db2 = _db()
        result2 = await DocumentsRepository(db2).save_resource(resource)
        db2.add.assert_called_with(resource)
        assert result2 is resource

    @pytest.mark.asyncio
    async def test_get_resource(self):
        """Cover get_resource (lines 510-513)."""
        resource = MagicMock()
        db = _db(_FR(v=resource))
        result = await DocumentsRepository(db).get_resource(_uid())
        assert result is resource

    @pytest.mark.asyncio
    async def test_list_resources_minimal(self):
        """Cover list_resources with minimal parameters (lines 531-607)."""
        resource = MagicMock()
        resource.id = _uid()
        resource.created_at = _now()
        doc = MagicMock()
        row = (resource, doc, "Uploader")
        db = _db(_FR(many=[row]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=None,
            limit=10,
        )
        assert len(result) == 1
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_resources_tch_role_with_class_ids(self):
        """Cover TCH role with visible_class_ids (lines 564-573)."""
        resource = MagicMock()
        resource.id = _uid()
        resource.created_at = _now()
        db = _db(_FR(many=[(resource, MagicMock(), None)]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="TCH",
            user_id=_uid(),
            subject="Math",
            level="primary",
            resource_type="pdf",
            tags=["tag1"],
            search="test",
            min_rating=3.0,
            cursor=None,
            limit=10,
            visible_class_ids={_uid()},
        )
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_resources_tch_role_no_class_ids(self):
        """Cover TCH role with empty visible_class_ids (else False branch)."""
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="TCH",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=None,
            limit=10,
            visible_class_ids=set(),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_resources_par_role(self):
        """Cover PAR role (lines 574-582)."""
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="PAR",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=None,
            limit=10,
            visible_class_ids={_uid()},
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_resources_std_role(self):
        """Cover STD role."""
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="STD",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=None,
            limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_resources_with_cursor(self):
        """Cover cursor-based filtering in list_resources (lines 585-594)."""
        from app.core.response import encode_cursor

        cursor_str = encode_cursor(_uid(), _now().isoformat())
        db = _db(_FR(many=[]))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=cursor_str,
            limit=10,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_list_resources_has_more_cursor(self):
        """Cover has_more=True path and next_cursor in list_resources (lines 601-606)."""
        resource = MagicMock()
        resource.id = _uid()
        resource.created_at = _now()
        rows = [(resource, MagicMock(), None)] * 3
        db = _db(_FR(many=rows))
        result, cursor, has_more = await DocumentsRepository(db).list_resources(
            school_id=_uid(),
            role="ADM",
            user_id=_uid(),
            subject=None,
            level=None,
            resource_type=None,
            tags=[],
            search=None,
            min_rating=None,
            cursor=None,
            limit=2,
        )
        assert has_more is True
        assert cursor is not None

    @pytest.mark.asyncio
    async def test_get_resource_with_document(self):
        """Cover get_resource_with_document (lines 613-620)."""
        resource = MagicMock()
        document = MagicMock()
        db = _db(_FR(v=(resource, document, "Name")))
        result = await DocumentsRepository(db).get_resource_with_document(_uid())
        # Returns result.first() which is (resource, document, name)
        assert result == (resource, document, "Name")

    @pytest.mark.asyncio
    async def test_get_resource_rating(self):
        """Cover get_resource_rating (lines 628-634)."""
        rating = MagicMock()
        db = _db(_FR(v=rating))
        result = await DocumentsRepository(db).get_resource_rating(
            resource_id=_uid(), user_id=_uid()
        )
        assert result is rating

    @pytest.mark.asyncio
    async def test_save_resource_rating(self):
        """Cover save_resource_rating (lines 636-639)."""
        rating = MagicMock()
        db = _db()
        result = await DocumentsRepository(db).save_resource_rating(rating)
        db.add.assert_called_with(rating)
        assert result is rating

    @pytest.mark.asyncio
    async def test_calculate_resource_rating_stats(self):
        """Cover calculate_resource_rating_stats (lines 646-652)."""
        db = _db(_FR(v=(4.5, 10)))
        avg, count = await DocumentsRepository(db).calculate_resource_rating_stats(
            resource_id=_uid()
        )
        assert avg == 4.5
        assert count == 10

    @pytest.mark.asyncio
    async def test_calculate_resource_rating_stats_no_ratings(self):
        """Cover None average case."""
        db = _db(_FR(v=(None, 0)))
        avg, count = await DocumentsRepository(db).calculate_resource_rating_stats(
            resource_id=_uid()
        )
        assert avg == 0.0
        assert count == 0
