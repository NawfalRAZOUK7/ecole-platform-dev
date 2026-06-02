"""Unit tests for app/core/filtering.py — full branch coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import String
from sqlalchemy import column as sa_column
from starlette.requests import Request

from app.core.filtering import (
    FILTERABLE_FIELDS,
    SORTABLE_FIELDS,
    FilterItem,
    FilterSpec,
    SortSpec,
    _apply_operator,
    apply_filters,
    apply_sort,
    parse_filters,
    parse_sort,
)


# ---------------------------------------------------------------------------
# FilterSpec / SortSpec data classes
# ---------------------------------------------------------------------------


def test_filter_spec_as_dict():
    spec = FilterSpec(items=[FilterItem("status", "eq", "active")])
    result = spec.as_dict()
    assert result == [{"field": "status", "op": "eq", "value": "active"}]


def test_filter_spec_empty():
    spec = FilterSpec()
    assert spec.as_dict() == []


def test_sort_spec_as_list_asc():
    spec = SortSpec(fields=[("title", "asc")])
    assert spec.as_list() == ["title"]


def test_sort_spec_as_list_desc():
    spec = SortSpec(fields=[("created_at", "desc")])
    assert spec.as_list() == ["-created_at"]


def test_sort_spec_as_list_mixed():
    spec = SortSpec(fields=[("created_at", "desc"), ("title", "asc")])
    assert spec.as_list() == ["-created_at", "title"]


def test_sort_spec_empty():
    spec = SortSpec()
    assert spec.as_list() == []


# ---------------------------------------------------------------------------
# _apply_operator — all branches
# ---------------------------------------------------------------------------


def _col(name: str = "status"):
    return sa_column(name, String)


def test_apply_operator_eq():
    expr = _apply_operator(_col(), "eq", "active")
    assert str(expr.compile(compile_kwargs={"literal_binds": True})) == "status = 'active'"


def test_apply_operator_gt():
    from sqlalchemy import Integer
    col = sa_column("score", Integer)
    expr = _apply_operator(col, "gt", "10")
    assert "score" in str(expr)


def test_apply_operator_gte():
    expr = _apply_operator(_col("score"), "gte", "5")
    assert "score" in str(expr)


def test_apply_operator_lt():
    expr = _apply_operator(_col("score"), "lt", "100")
    assert "score" in str(expr)


def test_apply_operator_lte():
    expr = _apply_operator(_col("score"), "lte", "99")
    assert "score" in str(expr)


def test_apply_operator_in():
    expr = _apply_operator(_col("status"), "in", "active,inactive")
    sql = str(expr.compile(compile_kwargs={"literal_binds": True}))
    assert "IN" in sql.upper() or "in" in sql.lower()


def test_apply_operator_like():
    expr = _apply_operator(_col("title"), "like", "math")
    sql = str(expr.compile(compile_kwargs={"literal_binds": True}))
    assert "math" in sql.lower()


def test_apply_operator_unknown_defaults_to_eq():
    expr = _apply_operator(_col("status"), "unknown_op", "active")
    assert str(expr.compile(compile_kwargs={"literal_binds": True})) == "status = 'active'"


# ---------------------------------------------------------------------------
# parse_filters (async FastAPI dependency)
# ---------------------------------------------------------------------------


def _make_request_with_params(query_string: str) -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/test",
        "query_string": query_string.encode(),
        "headers": [],
        "server": ("localhost", 8000),
    }
    return Request(scope)


@pytest.mark.asyncio
async def test_parse_filters_eq_implicit():
    request = _make_request_with_params("filter[status]=active")
    spec = await parse_filters(request)
    assert len(spec.items) == 1
    assert spec.items[0].field == "status"
    assert spec.items[0].operator == "eq"
    assert spec.items[0].value == "active"


@pytest.mark.asyncio
async def test_parse_filters_explicit_operator():
    request = _make_request_with_params("filter[created_at__gte]=2024-01-01")
    spec = await parse_filters(request)
    assert spec.items[0].operator == "gte"


@pytest.mark.asyncio
async def test_parse_filters_in_operator():
    request = _make_request_with_params("filter[status__in]=active,inactive")
    spec = await parse_filters(request)
    assert spec.items[0].operator == "in"


@pytest.mark.asyncio
async def test_parse_filters_unknown_operator_ignored():
    request = _make_request_with_params("filter[status__badop]=value")
    spec = await parse_filters(request)
    assert len(spec.items) == 0


@pytest.mark.asyncio
async def test_parse_filters_non_filter_params_ignored():
    request = _make_request_with_params("page=1&limit=20")
    spec = await parse_filters(request)
    assert len(spec.items) == 0


@pytest.mark.asyncio
async def test_parse_filters_multiple():
    request = _make_request_with_params("filter[status]=active&filter[title__like]=math")
    spec = await parse_filters(request)
    assert len(spec.items) == 2


# ---------------------------------------------------------------------------
# parse_sort (async FastAPI dependency)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_sort_asc():
    spec = await parse_sort("title")
    assert spec.fields == [("title", "asc")]


@pytest.mark.asyncio
async def test_parse_sort_desc():
    spec = await parse_sort("-created_at")
    assert spec.fields == [("created_at", "desc")]


@pytest.mark.asyncio
async def test_parse_sort_multiple():
    spec = await parse_sort("-created_at,title")
    assert spec.fields == [("created_at", "desc"), ("title", "asc")]


@pytest.mark.asyncio
async def test_parse_sort_none():
    spec = await parse_sort(None)
    assert spec.fields == []


@pytest.mark.asyncio
async def test_parse_sort_empty_parts_skipped():
    spec = await parse_sort(",title,,")
    assert spec.fields == [("title", "asc")]


# ---------------------------------------------------------------------------
# apply_filters
# ---------------------------------------------------------------------------


class CourseModel:
    status = sa_column("status", String)
    title = sa_column("title", String)


def test_apply_filters_allowed_field():
    FILTERABLE_FIELDS["CourseModel"] = {"status", "title"}
    spec = FilterSpec(items=[FilterItem("status", "eq", "published")])
    mock_query = MagicMock()
    mock_query.where.return_value = mock_query

    apply_filters(mock_query, CourseModel, spec)

    mock_query.where.assert_called_once()
    FILTERABLE_FIELDS.pop("CourseModel", None)


def test_apply_filters_disallowed_field_skipped():
    FILTERABLE_FIELDS["CourseModel"] = {"status"}
    spec = FilterSpec(items=[FilterItem("secret_field", "eq", "value")])
    mock_query = MagicMock()

    apply_filters(mock_query, CourseModel, spec)

    mock_query.where.assert_not_called()
    FILTERABLE_FIELDS.pop("CourseModel", None)


def test_apply_filters_field_not_on_model():
    FILTERABLE_FIELDS["CourseModel"] = {"nonexistent"}
    spec = FilterSpec(items=[FilterItem("nonexistent", "eq", "value")])
    mock_query = MagicMock()

    apply_filters(mock_query, CourseModel, spec)

    mock_query.where.assert_not_called()
    FILTERABLE_FIELDS.pop("CourseModel", None)


def test_apply_filters_empty_spec():
    spec = FilterSpec()
    mock_query = MagicMock()
    apply_filters(mock_query, CourseModel, spec)
    mock_query.where.assert_not_called()


def test_apply_filters_unknown_model_no_allowed():
    class UnknownModel:
        field = sa_column("field", String)

    spec = FilterSpec(items=[FilterItem("field", "eq", "value")])
    mock_query = MagicMock()
    apply_filters(mock_query, UnknownModel, spec)
    mock_query.where.assert_not_called()


# ---------------------------------------------------------------------------
# apply_sort
# ---------------------------------------------------------------------------


class SortableModel:
    title = sa_column("title", String)
    created_at = sa_column("created_at", String)


def test_apply_sort_asc():
    SORTABLE_FIELDS["SortableModel"] = {"title", "created_at"}
    spec = SortSpec(fields=[("title", "asc")])
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query

    apply_sort(mock_query, SortableModel, spec)

    mock_query.order_by.assert_called_once()
    SORTABLE_FIELDS.pop("SortableModel", None)


def test_apply_sort_desc():
    SORTABLE_FIELDS["SortableModel"] = {"title", "created_at"}
    spec = SortSpec(fields=[("created_at", "desc")])
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query

    apply_sort(mock_query, SortableModel, spec)

    mock_query.order_by.assert_called_once()
    SORTABLE_FIELDS.pop("SortableModel", None)


def test_apply_sort_disallowed_field_skipped():
    SORTABLE_FIELDS["SortableModel"] = {"created_at"}
    spec = SortSpec(fields=[("hidden_field", "asc")])
    mock_query = MagicMock()

    apply_sort(mock_query, SortableModel, spec)

    mock_query.order_by.assert_not_called()
    SORTABLE_FIELDS.pop("SortableModel", None)


def test_apply_sort_field_not_on_model():
    SORTABLE_FIELDS["SortableModel"] = {"nonexistent"}
    spec = SortSpec(fields=[("nonexistent", "asc")])
    mock_query = MagicMock()

    apply_sort(mock_query, SortableModel, spec)

    mock_query.order_by.assert_not_called()
    SORTABLE_FIELDS.pop("SortableModel", None)


def test_apply_sort_default_column_used_when_empty():
    spec = SortSpec(fields=[])
    mock_query = MagicMock()
    mock_query.order_by.return_value = mock_query
    default_col = sa_column("id", String)

    apply_sort(mock_query, SortableModel, spec, default_column=default_col)

    mock_query.order_by.assert_called_once()


def test_apply_sort_no_default_no_fields_not_called():
    spec = SortSpec(fields=[])
    mock_query = MagicMock()

    apply_sort(mock_query, SortableModel, spec)

    mock_query.order_by.assert_not_called()
