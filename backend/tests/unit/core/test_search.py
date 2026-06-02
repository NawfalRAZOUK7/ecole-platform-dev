"""Unit tests for app/core/search.py — full branch coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy import String
from sqlalchemy import column as sa_column

from app.core.search import apply_search, parse_search


# ---------------------------------------------------------------------------
# parse_search (FastAPI dependency)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_parse_search_with_term():
    result = await parse_search("mathematics")
    assert result == "mathematics"


@pytest.mark.asyncio
async def test_parse_search_strips_whitespace():
    result = await parse_search("  algebra  ")
    assert result == "algebra"


@pytest.mark.asyncio
async def test_parse_search_none_returns_none():
    result = await parse_search(None)
    assert result is None


@pytest.mark.asyncio
async def test_parse_search_empty_string_returns_none():
    result = await parse_search("")
    assert result is None


@pytest.mark.asyncio
async def test_parse_search_whitespace_only_returns_none():
    result = await parse_search("   ")
    assert result is None


# ---------------------------------------------------------------------------
# apply_search — no searchable fields for model
# ---------------------------------------------------------------------------


def test_apply_search_no_fields_returns_original_query():
    from app.core.filtering import SEARCHABLE_FIELDS

    class FakeModel:
        __name__ = "UnknownModel"

    original_fields = SEARCHABLE_FIELDS.copy()
    SEARCHABLE_FIELDS.pop("UnknownModel", None)

    mock_query = MagicMock()
    result = apply_search(mock_query, FakeModel, "term")

    SEARCHABLE_FIELDS.update(original_fields)

    assert result is mock_query  # returned unchanged


# ---------------------------------------------------------------------------
# apply_search — model with searchable fields
# ---------------------------------------------------------------------------


def test_apply_search_with_fields_modifies_query():
    """Class name must match SEARCHABLE_FIELDS key (Python __name__ descriptor)."""
    from app.core.filtering import SEARCHABLE_FIELDS

    # Class name IS the dict key — cannot be overridden via class var in Python 3.14
    class SearchTestModel:
        title = sa_column("title", String)
        description = sa_column("description", String)

    SEARCHABLE_FIELDS["SearchTestModel"] = ["title", "description"]

    mock_query = MagicMock()
    mock_query.where.return_value = mock_query

    try:
        apply_search(mock_query, SearchTestModel, "maths")
        mock_query.where.assert_called_once()
    finally:
        del SEARCHABLE_FIELDS["SearchTestModel"]


def test_apply_search_skips_missing_attribute():
    """Fields listed in SEARCHABLE_FIELDS but absent on model are skipped."""
    from app.core.filtering import SEARCHABLE_FIELDS

    class SparseSearchModel:
        title = sa_column("title", String)
        # 'body' intentionally missing

    SEARCHABLE_FIELDS["SparseSearchModel"] = ["title", "body"]

    mock_query = MagicMock()
    mock_query.where.return_value = mock_query

    try:
        apply_search(mock_query, SparseSearchModel, "test")
        mock_query.where.assert_called_once()
    finally:
        del SEARCHABLE_FIELDS["SparseSearchModel"]


def test_apply_search_no_conditions_when_all_attrs_missing():
    """If all listed fields are missing on model, query is unchanged."""
    from app.core.filtering import SEARCHABLE_FIELDS

    class EmptySearchModel:
        pass

    SEARCHABLE_FIELDS["EmptySearchModel"] = ["title", "body"]

    mock_query = MagicMock()

    try:
        returned = apply_search(mock_query, EmptySearchModel, "test")
        mock_query.where.assert_not_called()
        assert returned is mock_query
    finally:
        del SEARCHABLE_FIELDS["EmptySearchModel"]
