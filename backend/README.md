# École Platform Backend

FastAPI-based K-12 EdTech SaaS backend for Moroccan schools. Production-grade REST API with real-time WebSocket support, supporting 8-role RBAC+ABAC security model.

## Architecture

**3-tier modular monolith pattern:**
- **Router Layer** (`api/v1/*.py`) — HTTP request handlers, input validation, OpenAPI documentation
- **Service Layer** (`services/*.py`) — Business logic, domain rules, orchestration, integrations
- **Repository Layer** (`repositories/*.py`) — Async SQLAlchemy data access, query optimization

**Cross-cutting Infrastructure:**
- Security pipeline: AuthN → Context → RBAC → ABAC → Audit → Events
- SOLID principles with dependency injection via FastAPI `Depends()`
- Event-driven patterns for async tasks, notifications, and audit logging
- Domain-driven design with value objects and structural protocols

## Directory Structure

```
backend/
├── Dockerfile              # Container image
├── pyproject.toml          # Project metadata, test config, coverage rules
├── pytest.ini              # Test runner configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Dev tooling (linters, formatters)
├── requirements-test.txt   # Testing libraries
├── alembic.ini            # Database migration config
│
├── alembic/               # Database migrations
│   └── versions/          # 35+ Alembic migration files
│
├── app/                   # Main application package
│   ├── main.py           # FastAPI app factory, middleware stack, OpenAPI tags
│   ├── seed.py           # Demo data seeding script
│   ├── api/              # API layer (REST endpoints)
│   ├── core/             # Cross-cutting infrastructure
│   ├── domain/           # Domain-driven design patterns
│   ├── data/             # Static data files
│   ├── models/           # SQLAlchemy 2.0 ORM models
│   ├── repositories/     # Data access layer (queries)
│   ├── schemas/          # Pydantic v2 request/response schemas
│   ├── services/         # Business logic layer
│   ├── scripts/          # Application scripts
│   └── templates/        # Jinja2 HTML templates
│
├── docs/                 # Backend documentation
├── scripts/              # Utility scripts (OpenAPI export, validation)
├── tests/                # Test suite (unit, integration)
└── uploads/              # File storage for courses & submissions
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project config, pytest markers, coverage thresholds (90%) |
| `Dockerfile` | Production container image |
| `alembic.ini` | Database migration runner config |
| `requirements*.txt` | Dependency specifications |

## Running the Backend

```bash
# Development server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.scripts.seed_demo

# Run tests
pytest tests/ -v

# Export OpenAPI spec
python scripts/export_openapi.py
```

## Security Features

- **Authentication:** JWT + optional 2FA (TOTP)
- **Authorization:** RBAC (8 roles) + ABAC (attribute-based controls)
- **Data Protection:** Password hashing, password policies, GDPR compliance
- **API Protection:** Rate limiting, idempotency keys, CORS, CSRF
- **Audit Trail:** Immutable audit logs, domain events
- **Rate Limiting:** Per-user request quotas via Redis

## Testing

- **Unit tests:** Mocked services, fast feedback
- **Integration tests:** Real database, API contracts
- **Security tests:** RBAC/ABAC matrix validation
- **Performance tests:** Load testing and benchmarks
- Coverage requirement: 90%

```bash
pytest -m "not slow" tests/  # Quick runs
pytest -m "security" tests/   # Security matrix tests
```

## Database

- **Engine:** PostgreSQL with async SQLAlchemy 2.0
- **Migrations:** Alembic version control
- **Read Replicas:** Automatic routing for read-heavy queries
- **ORM Features:** Mapped[] columns, async sessions, lazy loading
- **Connection Pool:** Smart pooling with recycling

## Next Steps

- See `app/` for application code structure
- See `alembic/versions/` for migration history
- See `tests/` for testing patterns
