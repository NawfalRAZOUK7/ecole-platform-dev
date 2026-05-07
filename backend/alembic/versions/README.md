# Alembic Migration Versions

Contains 65+ database migration files. Each migration defines `upgrade()` and `downgrade()` functions for forward and backward schema changes.

## Convention

- Migrations are auto-generated via `alembic revision --autogenerate -m "description"`
- Each file is prefixed with a 12-char revision hash and linked to its parent via `down_revision`
- All migrations are tested in CI via `alembic upgrade head` + `alembic downgrade base` round-trip
- Filename format: `{12-char-revision}_{action}_{description}.py`
  - `action` is one of: `create`, `add`, `alter`, `index`, `constraint`, `merge`

## Safety

The `validate_migrations.py` script checks:
- Naming convention compliance
- Presence of `upgrade()` and `downgrade()` functions
- Revision chain integrity (no orphans, no broken references)
- Raw SQL has explanatory comments

Run validation locally:
```bash
python scripts/validate_migrations.py
```

## Groups

| Prefix | Meaning |
|--------|---------|
| `g##` | Core feature groups (G1-G51a) |
| `h#` | Cross-cutting enhancements (H2 = difficulty adaptations) |
| `i#` | Infrastructure / compliance (I4 = absence justification) |
| `merge_` | Merge migration combining parallel branches |
