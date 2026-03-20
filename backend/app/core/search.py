"""PostgreSQL full-text search helpers using tsvector/tsquery.

Reference: Phase 3D — Advanced Query Filters & Full-text Search
Usage:
    from app.core.search import apply_search

    query = apply_search(query, ContentItem, "mathematiques")
    # Generates: WHERE to_tsvector('french', title) @@ plainto_tsquery('french', 'mathematiques')

Supports French, Arabic, and English via 'simple' configuration for multilingual.
Uses plainto_tsquery for safe user input (no special syntax parsing).
"""

from __future__ import annotations

from fastapi import Query
from sqlalchemy import func, or_
from sqlalchemy.sql import Select

from app.core.filtering import SEARCHABLE_FIELDS

# PostgreSQL text search configuration.
# 'simple' works for all languages (no stemming but handles accents).
# For French stemming use 'french', for Arabic use 'simple'.
# We use 'simple' as default for multilingual Morocco context.
TS_CONFIG = "simple"


async def parse_search(
    search: str | None = Query(
        None,
        description="Full-text search term. Searches across title, description, body fields.",
    ),
) -> str | None:
    """Parse the ?search= query param. Returns the raw search term or None."""
    if search and search.strip():
        return search.strip()
    return None


def apply_search(query: Select, model: type, search_term: str) -> Select:
    """Apply PostgreSQL full-text search to a SQLAlchemy query.

    Uses to_tsvector + plainto_tsquery with 'simple' config for multilingual support.
    Falls back to ILIKE if no searchable fields are defined for the model.
    """
    model_name = model.__name__
    fields = SEARCHABLE_FIELDS.get(model_name, [])

    if not fields:
        return query

    ts_query = func.plainto_tsquery(TS_CONFIG, search_term)

    conditions = []
    for field_name in fields:
        column = getattr(model, field_name, None)
        if column is None:
            continue
        # tsvector @@ tsquery (uses GIN index if available)
        ts_vector = func.to_tsvector(TS_CONFIG, func.coalesce(column, ""))
        conditions.append(ts_vector.bool_op("@@")(ts_query))
        # Also add ILIKE fallback for partial matching
        conditions.append(column.ilike(f"%{search_term}%"))

    if conditions:
        query = query.where(or_(*conditions))

    return query
