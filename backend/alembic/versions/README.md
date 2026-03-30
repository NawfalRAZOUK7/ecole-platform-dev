# Alembic Migration Versions

Contains 34+ database migration files. Each migration defines `upgrade()` and `downgrade()` functions for forward and backward schema changes.

## Convention

- Migrations are auto-generated via `alembic revision --autogenerate -m "description"`
- Each file is prefixed with a revision hash and linked to its parent via `down_revision`
- All migrations are tested in CI via `alembic upgrade head` + `alembic downgrade base` round-trip

## Safety

The `validate_migrations.py` script checks for dangerous operations (DROP TABLE, DROP COLUMN without backup) before CI passes.
