"""Unit tests for typed UUID wrappers."""

from __future__ import annotations

import uuid

import pytest

from app.domain.value_objects.typed_id import SchoolId, UserId


class TestTypedIds:
    def test_user_id_from_valid_uuid(self):
        value = uuid.uuid4()

        typed_id = UserId(value)

        assert typed_id.value == value

    def test_school_id_from_valid_uuid(self):
        value = uuid.uuid4()

        typed_id = SchoolId(value)

        assert typed_id.value == value

    def test_user_id_from_string_via_factory(self):
        value = str(uuid.uuid4())

        typed_id = UserId.from_str(value)

        assert typed_id.value == uuid.UUID(value)

    def test_school_id_from_string_via_factory(self):
        value = str(uuid.uuid4())

        typed_id = SchoolId.from_str(value)

        assert typed_id.value == uuid.UUID(value)

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError):
            UserId.from_str("not-a-uuid")

    def test_equality_same_id(self):
        value = uuid.uuid4()

        assert UserId(value) == UserId(value)

    def test_equality_different_ids(self):
        assert UserId(uuid.uuid4()) != UserId(uuid.uuid4())

    def test_repr_contains_class_name_and_uuid(self):
        value = uuid.uuid4()

        rendered = repr(UserId(value))

        assert "UserId" in rendered
        assert str(value) in rendered

    def test_hash_consistent_for_same_value(self):
        value = uuid.uuid4()

        assert hash(UserId(value)) == hash(UserId(value))

    def test_str_returns_uuid_string(self):
        value = uuid.uuid4()

        assert str(SchoolId(value)) == str(value)
