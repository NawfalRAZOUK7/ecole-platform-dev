"""Multi-tenant isolation invariants (schema-level, DB-free).

The platform isolates establishments by a per-row ``school_id``. These tests
assert the structural foundation of that isolation directly from the SQLAlchemy
metadata, so a model that forgets to scope itself (or wires a wrong/ nullable
``school_id``) fails fast — independently of any running database.

Invariants checked:
  * Core tenant-owned tables expose a ``school_id`` column.
  * Every ``school_id`` column is a foreign key to ``schools.id``.
  * Core tenant-owned tables make ``school_id`` NOT NULL (no global rows).
  * Genuinely global tables (``schools`` itself) are NOT school-scoped.
"""

from __future__ import annotations

import app.models  # noqa: F401  (registers every model on Base.metadata)
from app.core.database import Base

# Tables that MUST be tenant-scoped with a mandatory school_id (SchoolScopedMixin).
# (Pre-tenant tables like school_applications, or course-scoped ones like
# assignments, are intentionally excluded — they isolate via a parent row.)
CORE_TENANT_TABLES = {
    "users",
    "memberships",
    "classes",
    "enrollments",
    "invoices",
    "courses",
    "audit_logs",
}

# Tables that are platform-global and must NOT carry a school_id.
GLOBAL_TABLES = {"schools"}


def _table(name: str):
    table = Base.metadata.tables.get(name)
    assert (
        table is not None
    ), f"expected table '{name}' to be registered on Base.metadata"
    return table


class TestSchoolIdForeignKeys:
    def test_every_school_id_column_points_to_schools_id(self) -> None:
        offenders = []
        for table in Base.metadata.tables.values():
            col = table.columns.get("school_id")
            if col is None:
                continue
            targets = {fk.column.table.name for fk in col.foreign_keys}
            if "schools" not in targets:
                offenders.append(f"{table.name}.school_id -> {targets or 'NO FK'}")
        assert offenders == [], f"school_id columns not FK to schools: {offenders}"


class TestCoreTenantTables:
    def test_core_tables_have_school_id(self) -> None:
        missing = [
            t for t in CORE_TENANT_TABLES if "school_id" not in _table(t).columns
        ]
        assert missing == [], f"core tenant tables missing school_id: {missing}"

    def test_core_tables_school_id_is_not_null(self) -> None:
        nullable = [
            t for t in CORE_TENANT_TABLES if _table(t).columns["school_id"].nullable
        ]
        assert nullable == [], f"core tenant tables with nullable school_id: {nullable}"

    def test_core_tables_school_id_is_indexed_or_fk(self) -> None:
        # Each tenant table should make cross-tenant filtering cheap: the
        # school_id must at least be a foreign key (FKs back the isolation).
        for t in CORE_TENANT_TABLES:
            col = _table(t).columns["school_id"]
            assert col.foreign_keys, f"{t}.school_id has no foreign key"


class TestGlobalTables:
    def test_schools_table_is_not_school_scoped(self) -> None:
        assert "school_id" not in _table("schools").columns
