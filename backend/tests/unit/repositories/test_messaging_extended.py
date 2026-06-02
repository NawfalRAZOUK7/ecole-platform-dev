"""Extended coverage tests for communication_messaging.py."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.repositories.communication_messaging import MessagingRepository


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


class TestMessagingRepositoryExtended:
    """Cover missing lines in communication_messaging.py."""

    @pytest.mark.asyncio
    async def test_list_class_ids_for_students_empty(self):
        """Empty student_ids returns empty set (line 87)."""
        db = _db()
        result = await MessagingRepository(db).list_class_ids_for_students(
            student_ids=set(), school_id=_uid()
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_class_ids_for_students_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await MessagingRepository(db).list_class_ids_for_students(
            student_ids={_uid()}, school_id=_uid()
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_student_ids_for_classes_empty(self):
        """Empty class_ids returns empty set (line 104)."""
        db = _db()
        result = await MessagingRepository(db).list_student_ids_for_classes(
            class_ids=set(), school_id=_uid()
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_student_ids_for_classes_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await MessagingRepository(db).list_student_ids_for_classes(
            class_ids={_uid()}, school_id=_uid()
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_teacher_ids_for_classes_empty(self):
        """Empty class_ids returns empty set (line 121)."""
        db = _db()
        result = await MessagingRepository(db).list_teacher_ids_for_classes(
            class_ids=set(), school_id=_uid()
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_teacher_ids_for_classes_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await MessagingRepository(db).list_teacher_ids_for_classes(
            class_ids={_uid()}, school_id=_uid()
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_list_parent_ids_for_students_empty(self):
        """Empty student_ids returns empty set (line 155)."""
        db = _db()
        result = await MessagingRepository(db).list_parent_ids_for_students(
            student_ids=set(), school_id=_uid()
        )
        assert result == set()
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_list_parent_ids_for_students_nonempty(self):
        uid = _uid()
        db = _db(_FR(many=[uid]))
        result = await MessagingRepository(db).list_parent_ids_for_students(
            student_ids={_uid()}, school_id=_uid()
        )
        assert uid in result

    @pytest.mark.asyncio
    async def test_create_conversation_participants_empty(self):
        """Empty participants list (lines 179-182)."""
        db = _db()
        result = await MessagingRepository(db).create_conversation_participants([])
        assert result == []
        db.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_conversation_participants_nonempty(self):
        """Non-empty participants list."""
        school_id = _uid()
        participants_data = [
            {"user_id": _uid(), "conversation_id": _uid(), "school_id": school_id}
        ]
        db = _db()
        # ConversationParticipant(**data) — bypass model by patching
        from unittest.mock import patch, MagicMock

        mock_cp = MagicMock()
        with patch(
            "app.repositories.communication_messaging.ConversationParticipant",
            side_effect=lambda **kw: mock_cp,
        ):
            await MessagingRepository(db).create_conversation_participants(
                participants_data
            )
        db.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_message_sent_at(self):
        """Cover get_message_sent_at (line 278)."""
        ts = _now()
        db = _db(_FR(v=ts))
        result = await MessagingRepository(db).get_message_sent_at(_uid())
        assert result is ts

    @pytest.mark.asyncio
    async def test_get_message_sent_at_not_found(self):
        db = _db(_FR(v=None))
        result = await MessagingRepository(db).get_message_sent_at(_uid())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_conversation_messages_no_before(self):
        """Cover list_conversation_messages without before_sent_at (line 308)."""
        msg = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[msg]))
        items, has_more = await MessagingRepository(db).list_conversation_messages(
            conversation_id=_uid(), before_sent_at=None, limit=10
        )
        assert items == [msg]
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_conversation_messages_with_before(self):
        """Cover before_sent_at filter branch."""
        msg = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[msg]))
        items, has_more = await MessagingRepository(db).list_conversation_messages(
            conversation_id=_uid(), before_sent_at=_now(), limit=10
        )
        assert items == [msg]

    @pytest.mark.asyncio
    async def test_list_conversation_messages_has_more(self):
        msgs = [SimpleNamespace(id=_uid()) for _ in range(3)]
        db = _db(_FR(many=msgs))
        items, has_more = await MessagingRepository(db).list_conversation_messages(
            conversation_id=_uid(), before_sent_at=None, limit=2
        )
        assert has_more is True
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_create_read_receipts_empty(self):
        """Empty receipts list (lines 351-354)."""
        db = _db()
        result = await MessagingRepository(db).create_read_receipts([])
        assert result == []
        db.add_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_read_receipts_nonempty(self):
        """Non-empty receipts list."""
        from unittest.mock import patch, MagicMock

        _uid()
        receipts_data = [{"message_id": _uid(), "user_id": _uid()}]
        db = _db()
        mock_rr = MagicMock()
        with patch(
            "app.repositories.communication_messaging.MessageReadReceipt",
            side_effect=lambda **kw: mock_rr,
        ):
            await MessagingRepository(db).create_read_receipts(receipts_data)
        db.add_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_read_receipts_without_message_id(self):
        """Cover list_read_receipts without message_id filter (lines 362-371)."""
        receipt = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[receipt]))
        result = await MessagingRepository(db).list_read_receipts(
            conversation_id=_uid(), message_id=None
        )
        assert result == [receipt]

    @pytest.mark.asyncio
    async def test_list_read_receipts_with_message_id(self):
        """Cover message_id filter branch (line 368)."""
        receipt = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[receipt]))
        result = await MessagingRepository(db).list_read_receipts(
            conversation_id=_uid(), message_id=_uid()
        )
        assert result == [receipt]

    @pytest.mark.asyncio
    async def test_list_parent_feed_items_no_student(self):
        """Cover list_parent_feed_items without student_id (lines 385-411)."""
        item = SimpleNamespace(id=_uid())
        db = _db(_FR(many=[item]))
        from app.core.filtering import FilterSpec, SortSpec

        items, has_more = await MessagingRepository(db).list_parent_feed_items(
            school_id=_uid(),
            parent_id=_uid(),
            student_id=None,
            filters=FilterSpec(),
            sort=SortSpec(),
            search=None,
            cursor=None,
            limit=10,
        )
        assert items == [item]

    @pytest.mark.asyncio
    async def test_list_parent_feed_items_with_student_and_search(self):
        """Cover student_id filter and search branches."""
        db = _db(_FR(many=[]))
        from app.core.filtering import FilterSpec, SortSpec

        items, has_more = await MessagingRepository(db).list_parent_feed_items(
            school_id=_uid(),
            parent_id=_uid(),
            student_id=_uid(),
            filters=FilterSpec(),
            sort=SortSpec(),
            search="homework",
            cursor=None,
            limit=10,
        )
        assert items == []

    @pytest.mark.asyncio
    async def test_list_parent_feed_items_with_cursor(self):
        """Cover cursor branch in list_parent_feed_items."""
        from app.core.filtering import FilterSpec, SortSpec
        from app.core.response import encode_cursor

        cursor = encode_cursor(_uid())
        db = _db(_FR(many=[]))
        items, has_more = await MessagingRepository(db).list_parent_feed_items(
            school_id=_uid(),
            parent_id=_uid(),
            student_id=None,
            filters=FilterSpec(),
            sort=SortSpec(),
            search=None,
            cursor=cursor,
            limit=10,
        )
        assert items == []

    @pytest.mark.asyncio
    async def test_list_conversations_for_user_with_cursor(self):
        """Cover cursor branch in list_conversations_for_user."""
        from app.core.response import encode_cursor

        cursor = encode_cursor(_uid())
        db = _db(_FR(many=[]))
        items, has_more = await MessagingRepository(db).list_conversations_for_user(
            school_id=_uid(),
            user_id=_uid(),
            cursor=cursor,
            limit=10,
        )
        assert items == []
        assert has_more is False

    @pytest.mark.asyncio
    async def test_list_conversations_for_user_has_more(self):
        """When rows > limit, has_more = True."""
        conv = SimpleNamespace(id=_uid())
        rows = [(conv, _now()), (conv, _now()), (conv, _now())]
        db = _db(_FR(many=rows))
        items, has_more = await MessagingRepository(db).list_conversations_for_user(
            school_id=_uid(),
            user_id=_uid(),
            cursor=None,
            limit=2,
        )
        assert has_more is True
        assert len(items) == 2
