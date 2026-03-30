"""Load-pattern tests for concurrent permissions, batch grading, and large pagination."""

from __future__ import annotations

import asyncio
import math
import time

import pytest

from app.core.permissions import (
    ADM,
    DIR,
    PAR,
    PERM_ADM_USER_READ,
    PERM_BIL_PAYMENT_PLAN_READ,
    PERM_LMS_SUBMISSION_GRADE,
    PERM_PROF_CHILD_READ,
    TCH,
    role_has_permission,
)
from app.core.response import list_response
from app.domain.value_objects.grade import MoroccanGrade


def paginate_records(records: list[dict[str, int]], cursor: str | None, limit: int) -> dict:
    start = int(cursor) if cursor is not None else 0
    page = records[start : start + limit]
    next_cursor = start + limit if (start + limit) < len(records) else None
    return list_response(
        page,
        next_cursor=str(next_cursor) if next_cursor is not None else None,
        has_more=next_cursor is not None,
    )


@pytest.mark.slow
class TestLoadPatterns:
    @pytest.mark.parametrize(
        ("role_code", "permission"),
        [
            (ADM, PERM_ADM_USER_READ),
            (DIR, PERM_ADM_USER_READ),
            (TCH, PERM_LMS_SUBMISSION_GRADE),
            (PAR, PERM_PROF_CHILD_READ),
        ],
    )
    @pytest.mark.asyncio
    async def test_100_concurrent_permission_checks(
        self,
        role_code: str,
        permission: str,
    ) -> None:
        started_at = time.perf_counter()
        results = await asyncio.gather(
            *[
                asyncio.to_thread(role_has_permission, role_code, permission)
                for _ in range(100)
            ]
        )
        elapsed = time.perf_counter() - started_at

        assert len(results) == 100
        assert all(result is True for result in results)
        assert elapsed < 0.5

    @pytest.mark.parametrize("batch_size", [10, 20, 40])
    @pytest.mark.asyncio
    async def test_batch_grade_creation_patterns(self, batch_size: int) -> None:
        started_at = time.perf_counter()
        grades = await asyncio.gather(
            *[
                asyncio.to_thread(MoroccanGrade.from_float, float(index % 21))
                for index in range(batch_size)
            ]
        )
        elapsed = time.perf_counter() - started_at

        assert len(grades) == batch_size
        assert max(float(grade.value) for grade in grades) <= 20.0
        assert elapsed < 0.5

    @pytest.mark.parametrize("page_size", [20, 50, 100])
    @pytest.mark.asyncio
    async def test_paginate_1000_records(self, page_size: int) -> None:
        records = [{"id": index} for index in range(1000)]
        cursor = None
        seen = 0
        pages = 0
        started_at = time.perf_counter()

        while True:
            payload = paginate_records(records, cursor, page_size)
            seen += len(payload["data"])
            pages += 1
            cursor = payload["meta"]["next_cursor"]
            if not payload["meta"]["has_more"]:
                break

        elapsed = time.perf_counter() - started_at

        assert seen == 1000
        assert pages == math.ceil(1000 / page_size)
        assert elapsed < 0.1
