"""Generic filtering and sorting dependencies for list endpoints.

Reference: Phase 3D — Advanced Query Filters & Full-text Search
Usage:
    @router.get("")
    async def list_items(
        filters: FilterSpec = Depends(parse_filters),
        sort: SortSpec = Depends(parse_sort),
        ...
    ):
        query = apply_filters(query, Model, filters)
        query = apply_sort(query, Model, sort, default_column=Model.id)

Supported filter operators: eq, gt, gte, lt, lte, in, like
Query syntax: ?filter[status]=published  (eq implied)
              ?filter[created_at__gte]=2025-01-01
              ?filter[status__in]=draft,published
              ?sort=-created_at,title  (- prefix = descending)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from fastapi import Query, Request
from sqlalchemy import asc, desc
from sqlalchemy.sql import Select


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class FilterItem:
    """A single filter: field__operator = value."""

    field: str
    operator: str  # eq, gt, gte, lt, lte, in, like
    value: Any


@dataclass
class FilterSpec:
    """Collection of filters parsed from query params."""

    items: list[FilterItem] = field(default_factory=list)

    def as_dict(self) -> list[dict[str, str]]:
        """Serialize for meta.filters_applied."""
        return [
            {"field": f.field, "op": f.operator, "value": str(f.value)}
            for f in self.items
        ]


@dataclass
class SortSpec:
    """Sort specification parsed from ?sort= query param."""

    fields: list[tuple[str, str]] = field(default_factory=list)  # (field, "asc"|"desc")

    def as_list(self) -> list[str]:
        """Serialize for meta.sort_by (e.g. ['-created_at', 'title'])."""
        return [f"-{f}" if d == "desc" else f for f, d in self.fields]


# ---------------------------------------------------------------------------
# Filter operators — safe mapping to SQLAlchemy
# ---------------------------------------------------------------------------
VALID_OPERATORS = {"eq", "gt", "gte", "lt", "lte", "in", "like"}

# Regex for filter param: filter[field] or filter[field__op]
FILTER_PATTERN = re.compile(r"^filter\[(\w+?)(?:__(\w+))?\]$")


def _apply_operator(column: Any, operator: str, value: str) -> Any:
    """Apply a filter operator to a SQLAlchemy column."""
    if operator == "eq":
        return column == value
    elif operator == "gt":
        return column > value
    elif operator == "gte":
        return column >= value
    elif operator == "lt":
        return column < value
    elif operator == "lte":
        return column <= value
    elif operator == "in":
        return column.in_(value.split(","))
    elif operator == "like":
        return column.ilike(f"%{value}%")
    return column == value


# ---------------------------------------------------------------------------
# FastAPI dependency — parse filters from query params
# ---------------------------------------------------------------------------
async def parse_filters(request: Request) -> FilterSpec:
    """Parse filter[field__op]=value query params into FilterSpec.

    Examples:
        ?filter[status]=published           → eq
        ?filter[created_at__gte]=2025-01-01 → gte
        ?filter[status__in]=draft,published → in
        ?filter[title__like]=math           → ilike
    """
    spec = FilterSpec()
    for key, value in request.query_params.items():
        match = FILTER_PATTERN.match(key)
        if match:
            field_name = match.group(1)
            operator = match.group(2) or "eq"
            if operator in VALID_OPERATORS:
                spec.items.append(
                    FilterItem(field=field_name, operator=operator, value=value)
                )
    return spec


async def parse_sort(
    sort: str | None = Query(
        None,
        description="Sort fields, comma-separated. Prefix with - for desc. E.g. -created_at,title",
    ),
) -> SortSpec:
    """Parse ?sort=-created_at,title into SortSpec."""
    spec = SortSpec()
    if sort:
        for part in sort.split(","):
            part = part.strip()
            if not part:
                continue
            if part.startswith("-"):
                spec.fields.append((part[1:], "desc"))
            else:
                spec.fields.append((part, "asc"))
    return spec


# ---------------------------------------------------------------------------
# Apply filters and sort to a SQLAlchemy query
# ---------------------------------------------------------------------------
# Allowlists per model — prevents injection of arbitrary column names
FILTERABLE_FIELDS: dict[str, set[str]] = {
    "Course": {"status", "title", "class_id", "teacher_id", "created_at"},
    "Assignment": {"title", "course_id", "due_at", "created_at"},
    "ContentItem": {
        "status",
        "content_type",
        "level_band",
        "language",
        "title",
        "created_at",
    },
    "Notification": {"title", "event_ref", "created_at"},
    "Activity": {"type", "difficulty", "title", "created_at"},
    "Assessment": {"status", "class_id", "title", "due_at", "created_at"},
    "Invoice": {"status", "created_at"},
    "ParentFeedItem": {"source_type", "title", "created_at"},
}

SORTABLE_FIELDS: dict[str, set[str]] = {
    "Course": {"id", "title", "status", "created_at"},
    "Assignment": {"id", "title", "due_at", "created_at"},
    "ContentItem": {"id", "title", "content_type", "created_at"},
    "Notification": {"id", "title", "created_at"},
    "Activity": {"id", "title", "type", "created_at"},
    "Assessment": {"id", "title", "status", "due_at", "created_at"},
    "Invoice": {"id", "status", "created_at"},
    "ParentFeedItem": {"id", "title", "created_at"},
}

# Full-text searchable fields per model
SEARCHABLE_FIELDS: dict[str, list[str]] = {
    "Course": ["title", "description"],
    "Assignment": ["title", "description"],
    "ContentItem": ["title"],
    "Notification": ["title", "body"],
    "Activity": ["title", "pedagogical_objective"],
    "Assessment": ["title"],
    "Invoice": [],
    "ParentFeedItem": ["title", "body"],
}


def apply_filters(query: Select, model: type, filters: FilterSpec) -> Select:
    """Apply FilterSpec to a SQLAlchemy Select, respecting allowlists."""
    model_name = model.__name__
    allowed = FILTERABLE_FIELDS.get(model_name, set())

    for item in filters.items:
        if item.field not in allowed:
            continue
        column = getattr(model, item.field, None)
        if column is None:
            continue
        query = query.where(_apply_operator(column, item.operator, item.value))

    return query


def apply_sort(
    query: Select,
    model: type,
    sort: SortSpec,
    *,
    default_column: Any = None,
) -> Select:
    """Apply SortSpec to a SQLAlchemy Select, respecting allowlists.

    If no sort is specified and a default_column is given, uses that.
    """
    model_name = model.__name__
    allowed = SORTABLE_FIELDS.get(model_name, set())

    applied = False
    for field_name, direction in sort.fields:
        if field_name not in allowed:
            continue
        column = getattr(model, field_name, None)
        if column is None:
            continue
        query = query.order_by(desc(column) if direction == "desc" else asc(column))
        applied = True

    if not applied and default_column is not None:
        query = query.order_by(default_column)

    return query
