"""Unit tests for micro-school repository query helpers."""

from __future__ import annotations

import uuid
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from app.repositories.micro_school import MicroSchoolRepository


class _FakeExecuteResult:
    def __init__(
        self,
        *,
        one_or_none=None,
        one=None,
        many: list | None = None,
    ) -> None:
        self._one_or_none = one_or_none
        self._one = one
        self._many = many or []

    def scalar_one_or_none(self):
        return self._one_or_none

    def scalar_one(self):
        return self._one

    def scalars(self):
        return SimpleNamespace(all=lambda: self._many)


def make_repo(result: _FakeExecuteResult):
    db = SimpleNamespace(
        execute=AsyncMock(return_value=result),
        add=Mock(),
        delete=AsyncMock(),
        flush=AsyncMock(),
    )
    return MicroSchoolRepository(db), db


@pytest_asyncio.fixture(autouse=True)
async def clear_analytics_cache():
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_test_redis():
    yield


@pytest_asyncio.fixture(autouse=True)
async def dispose_app_engine_pool():
    yield


class TestMicroSchoolRepository:
    @pytest.mark.asyncio
    async def test_get_micro_school_applies_school_scope_and_loaders(self) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_school(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
            include_groups=True,
            include_payments=True,
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
        assert len(stmt._with_options) == 2

    @pytest.mark.asyncio
    async def test_list_micro_schools_applies_all_filters(self) -> None:
        expected = [object()]
        repo, db = make_repo(_FakeExecuteResult(many=expected))
        educator_id = uuid.uuid4()

        result = await repo.list_micro_schools(
            school_id=uuid.uuid4(),
            educator_id=educator_id,
            city="Casablanca",
            status="active",
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert result == expected
        assert "school_id" in sql
        assert "educator_id" in sql
        assert "city" in sql
        assert "status" in sql

    @pytest.mark.asyncio
    async def test_micro_school_crud_flushes_session(self) -> None:
        repo, db = make_repo(_FakeExecuteResult())
        entity = object()

        created = await repo.create_micro_school(entity)
        saved = await repo.save_micro_school(entity)
        await repo.delete_micro_school(entity)

        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_get_micro_group_applies_school_scope_and_loaders(self) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_group(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
            include_school=True,
            include_enrollments=True,
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
        assert len(stmt._with_options) == 2

    @pytest.mark.asyncio
    async def test_list_micro_groups_applies_school_scope_and_school_filter(
        self,
    ) -> None:
        expected = [object()]
        repo, db = make_repo(_FakeExecuteResult(many=expected))
        micro_school_id = uuid.uuid4()

        result = await repo.list_micro_groups(
            school_id=uuid.uuid4(),
            micro_school_id=micro_school_id,
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert result == expected
        assert "school_id" in sql
        assert "micro_school_id" in sql

    @pytest.mark.asyncio
    async def test_micro_group_crud_flushes_session(self) -> None:
        repo, db = make_repo(_FakeExecuteResult())
        entity = object()

        created = await repo.create_micro_group(entity)
        saved = await repo.save_micro_group(entity)
        await repo.delete_micro_group(entity)

        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_get_micro_enrollment_applies_school_scope_and_loaders(self) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_enrollment(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
            include_group=True,
            include_payments=True,
            include_progress_logs=True,
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
        assert len(stmt._with_options) == 3

    @pytest.mark.asyncio
    async def test_list_micro_enrollments_applies_all_filters(self) -> None:
        expected = [object()]
        repo, db = make_repo(_FakeExecuteResult(many=expected))

        result = await repo.list_micro_enrollments(
            school_id=uuid.uuid4(),
            micro_group_id=uuid.uuid4(),
            parent_id=uuid.uuid4(),
            status="active",
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert result == expected
        assert "school_id" in sql
        assert "micro_group_id" in sql
        assert "parent_id" in sql
        assert "status" in sql

    @pytest.mark.asyncio
    async def test_micro_enrollment_crud_flushes_session(self) -> None:
        repo, db = make_repo(_FakeExecuteResult())
        entity = object()

        created = await repo.create_micro_enrollment(entity)
        saved = await repo.save_micro_enrollment(entity)
        await repo.delete_micro_enrollment(entity)

        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_get_micro_payment_applies_school_scope_and_loaders(self) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_payment(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
            include_school=True,
            include_enrollment=True,
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
        assert len(stmt._with_options) == 2

    @pytest.mark.asyncio
    async def test_list_micro_payments_applies_all_filters(self) -> None:
        expected = [object()]
        repo, db = make_repo(_FakeExecuteResult(many=expected))

        result = await repo.list_micro_payments(
            school_id=uuid.uuid4(),
            micro_school_id=uuid.uuid4(),
            parent_id=uuid.uuid4(),
            child_enrollment_id=uuid.uuid4(),
            status="paid",
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert result == expected
        assert "school_id" in sql
        assert "micro_school_id" in sql
        assert "parent_id" in sql
        assert "child_enrollment_id" in sql
        assert "status" in sql

    @pytest.mark.asyncio
    async def test_micro_payment_crud_flushes_session(self) -> None:
        repo, db = make_repo(_FakeExecuteResult())
        entity = object()

        created = await repo.create_micro_payment(entity)
        saved = await repo.save_micro_payment(entity)
        await repo.delete_micro_payment(entity)

        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_micro_resource_queries_apply_filters_and_crud(self) -> None:
        expected = object()
        repo, db = make_repo(
            _FakeExecuteResult(one_or_none=expected, many=[expected]),
        )
        entity = object()

        resource = await repo.get_micro_resource(uuid.uuid4())
        items = await repo.list_micro_resources(
            resource_type="game",
            language="fr",
            age_group="3-5",
            is_premium=False,
        )
        created = await repo.create_micro_resource(entity)
        saved = await repo.save_micro_resource(entity)
        await repo.delete_micro_resource(entity)

        get_stmt = db.execute.await_args_list[0].args[0]
        list_stmt = db.execute.await_args_list[1].args[0]
        assert resource is expected
        assert items == [expected]
        assert "resource_type" in str(list_stmt)
        assert "language" in str(list_stmt)
        assert "age_group" in str(list_stmt)
        assert "is_premium" in str(list_stmt)
        assert "micro_resources.id" in str(get_stmt)
        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_get_micro_progress_log_applies_school_scope_and_loaders(
        self,
    ) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_progress_log(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
            include_enrollment=True,
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
        assert len(stmt._with_options) == 1

    @pytest.mark.asyncio
    async def test_list_micro_progress_logs_applies_all_filters(self) -> None:
        expected = [object()]
        repo, db = make_repo(_FakeExecuteResult(many=expected))

        result = await repo.list_micro_progress_logs(
            school_id=uuid.uuid4(),
            micro_enrollment_id=uuid.uuid4(),
            educator_id=uuid.uuid4(),
            date_from=date(2026, 4, 1),
            date_to=date(2026, 4, 30),
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert result == expected
        assert "school_id" in sql
        assert "micro_enrollment_id" in sql
        assert "educator_id" in sql
        assert "date" in sql

    @pytest.mark.asyncio
    async def test_micro_progress_log_crud_flushes_session(self) -> None:
        repo, db = make_repo(_FakeExecuteResult())
        entity = object()

        created = await repo.create_micro_progress_log(entity)
        saved = await repo.save_micro_progress_log(entity)
        await repo.delete_micro_progress_log(entity)

        assert created is entity
        assert saved is entity
        assert db.add.call_count == 2
        db.delete.assert_awaited_once_with(entity)
        assert db.flush.await_count == 3

    @pytest.mark.asyncio
    async def test_parent_has_school_access_applies_parent_and_school_scope(
        self,
    ) -> None:
        repo, db = make_repo(_FakeExecuteResult(one=2))

        has_access = await repo.parent_has_school_access(
            parent_id=uuid.uuid4(),
            micro_school_id=uuid.uuid4(),
            school_id=uuid.uuid4(),
        )

        stmt = db.execute.await_args.args[0]
        sql = str(stmt)
        assert has_access is True
        assert "parent_id" in sql
        assert "school_id" in sql

    @pytest.mark.asyncio
    async def test_get_micro_school_for_enrollment_applies_school_scope(self) -> None:
        expected = object()
        repo, db = make_repo(_FakeExecuteResult(one_or_none=expected))

        result = await repo.get_micro_school_for_enrollment(
            uuid.uuid4(),
            school_id=uuid.uuid4(),
        )

        stmt = db.execute.await_args.args[0]
        assert result is expected
        assert "school_id" in str(stmt)
