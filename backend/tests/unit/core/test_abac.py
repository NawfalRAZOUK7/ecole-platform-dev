"""Unit tests for ABAC helpers."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Column, MetaData, String, Table, select

from app.core.abac import (
    apply_owner_scope,
    validate_parent_child_access,
    validate_student_teacher_access,
    validate_teacher_class_access,
)
from app.core.dependencies import AuthContext


TEST_TABLE = Table(
    "owner_scoped_records",
    MetaData(),
    Column("user_id", String),
    Column("teacher_id", String),
    Column("parent_id", String),
    Column("student_id", String),
)


def make_auth(role: str) -> AuthContext:
    return AuthContext(
        user_id=uuid.uuid4(),
        role=role,
        school_id=uuid.uuid4(),
        session_id=uuid.uuid4(),
        permissions=set(),
    )


def compiled_sql(query) -> str:
    return str(query.compile())


def where_sql(query) -> str:
    return str(query.whereclause)


class TestApplyOwnerScope:
    @pytest.mark.parametrize("role", ["ADM", "DIR", "SUP"])
    def test_admin_roles_leave_query_unfiltered(self, role: str):
        scoped = apply_owner_scope(select(TEST_TABLE), auth=make_auth(role))

        assert scoped._where_criteria == ()

    def test_teacher_scope_filters_on_teacher_field(self):
        auth = make_auth("TCH")
        scoped = apply_owner_scope(select(TEST_TABLE), auth=auth)

        assert "teacher_id" in compiled_sql(scoped)
        assert list(scoped.compile().params.values()) == [auth.user_id]

    def test_parent_scope_filters_on_parent_field(self):
        auth = make_auth("PAR")
        scoped = apply_owner_scope(select(TEST_TABLE), auth=auth)

        assert "parent_id" in compiled_sql(scoped)
        assert list(scoped.compile().params.values()) == [auth.user_id]

    def test_student_scope_filters_on_student_field(self):
        auth = make_auth("STD")
        scoped = apply_owner_scope(select(TEST_TABLE), auth=auth)

        assert "student_id" in compiled_sql(scoped)
        assert list(scoped.compile().params.values()) == [auth.user_id]

    def test_other_roles_fall_back_to_owner_field(self):
        auth = make_auth("CONTENT_MGR")
        scoped = apply_owner_scope(select(TEST_TABLE), auth=auth)

        assert "user_id" in compiled_sql(scoped)
        assert list(scoped.compile().params.values()) == [auth.user_id]

    def test_missing_teacher_field_falls_back_to_owner_field(self):
        auth = make_auth("TCH")
        scoped = apply_owner_scope(
            select(TEST_TABLE),
            auth=auth,
            teacher_field=None,
        )

        assert "user_id" in where_sql(scoped)
        assert "teacher_id" not in where_sql(scoped)
        assert list(scoped.compile().params.values()) == [auth.user_id]


class TestValidateParentChildAccess:
    @pytest.mark.asyncio
    async def test_returns_true_for_active_link(self):
        result = Mock()
        result.scalar_one_or_none.return_value = uuid.uuid4()
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_parent_child_access(
                db,
                parent_id=uuid.uuid4(),
                student_id=uuid.uuid4(),
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_returns_false_for_inactive_link(self):
        result = Mock()
        result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_parent_child_access(
                db,
                parent_id=uuid.uuid4(),
                student_id=uuid.uuid4(),
            )
            is False
        )

        query = db.execute.await_args.args[0]
        assert "parent_child_links" in compiled_sql(query)
        assert "status" in compiled_sql(query)
        assert "active" in query.compile().params.values()

    @pytest.mark.asyncio
    async def test_returns_false_when_link_is_missing(self):
        result = Mock()
        result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_parent_child_access(
                db,
                parent_id=uuid.uuid4(),
                student_id=uuid.uuid4(),
            )
            is False
        )


class TestValidateTeacherClassAccess:
    @pytest.mark.asyncio
    async def test_returns_true_for_assigned_teacher(self):
        result = Mock()
        result.scalar_one_or_none.return_value = uuid.uuid4()
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_teacher_class_access(
                db,
                teacher_id=uuid.uuid4(),
                class_id=uuid.uuid4(),
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_returns_false_for_unassigned_teacher(self):
        result = Mock()
        result.scalar_one_or_none.return_value = None
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_teacher_class_access(
                db,
                teacher_id=uuid.uuid4(),
                class_id=uuid.uuid4(),
            )
            is False
        )

        query = db.execute.await_args.args[0]
        assert "teacher_assignments" in compiled_sql(query)


class TestValidateStudentTeacherAccess:
    @pytest.mark.asyncio
    async def test_returns_true_when_student_and_teacher_share_class(self):
        result = Mock()
        result.scalar.return_value = True
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_student_teacher_access(
                db,
                student_id=uuid.uuid4(),
                teacher_id=uuid.uuid4(),
            )
            is True
        )

    @pytest.mark.asyncio
    async def test_returns_false_when_student_and_teacher_do_not_share_class(self):
        result = Mock()
        result.scalar.return_value = False
        db = AsyncMock()
        db.execute.return_value = result

        assert (
            await validate_student_teacher_access(
                db,
                student_id=uuid.uuid4(),
                teacher_id=uuid.uuid4(),
            )
            is False
        )

    @pytest.mark.asyncio
    async def test_query_requires_active_enrollment_and_intersection(self):
        result = Mock()
        result.scalar.return_value = False
        db = AsyncMock()
        db.execute.return_value = result

        await validate_student_teacher_access(
            db,
            student_id=uuid.uuid4(),
            teacher_id=uuid.uuid4(),
        )

        query = db.execute.await_args.args[0]
        compiled = compiled_sql(query)

        assert "INTERSECT" in compiled
        assert "enrollments.status" in compiled
        assert "active" in query.compile().params.values()
