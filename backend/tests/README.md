# Backend Test Suite

Comprehensive test suite for the École Platform backend. Organized by domain and test type for maintainability and fast feedback loops.

## Overview

- **Framework**: pytest with factory_boy + Faker for test data generation
- **Infrastructure**: testcontainers (PostgreSQL) for integration tests
- **Configuration**: See `pyproject.toml` for test execution settings
- **Async Support**: SQLAlchemy async sessions via `conftest.py` fixtures

## Test Categories

| Category | Purpose | Location |
|----------|---------|----------|
| **Unit** | Business logic in isolation with mocked dependencies | `unit/` |
| **Integration** | Real database interactions with testcontainers | `integration/` |
| **Security** | RBAC matrix, ABAC policies, permission escalation | `security/` |
| **Edge Cases** | Boundary values, error paths, timezone handling | `edge/` |
| **Performance** | Response time SLAs, concurrent request patterns | `performance/` |
| **Contract** | OpenAPI schema compliance, migration safety | `contract/` |

## Directory Structure

```
tests/
├── conftest.py                          # Shared fixtures
├── _support/                            # Test helpers (factories, fixtures, builders, matchers)
│
├── unit/                                # Fast, mocked, no DB
│   ├── core/                            # JWT, permissions, rate limit, middleware, etc.
│   ├── domain/                          # Value objects (Money, Grade, RoleSet, TypedId)
│   ├── models/                          # Model repr, validators, properties
│   ├── schemas/                         # Pydantic schema validation ★ NEW
│   ├── services/                        # Service layer unit tests
│   │   ├── iam/
│   │   ├── lms/
│   │   ├── billing/
│   │   ├── communication/
│   │   ├── academic/
│   │   └── ai/                          # ★ NEW
│   ├── repositories/                    # Repository smoke tests ★ NEW
│   ├── api/                             # Router-level unit tests with mocked services
│   └── workers/                         # ARQ task & worker tests
│
├── integration/                         # Real DB via testcontainers
│   ├── api/                             # API endpoint tests grouped by domain
│   │   ├── iam/                         # Auth, profiles, family, websocket, filters
│   │   ├── lms/                         # Content, uploads, story, levels, difficulty
│   │   ├── communication/               # Notifications, announcements, shared review
│   │   ├── billing/                     # Invoices, payments, budgets, financial health
│   │   ├── academic/                    # Programs, attendance, gradebook, skills
│   │   ├── content/                     # Games, rewards
│   │   ├── storage/                     # Signed uploads/downloads, ClamAV
│   │   ├── micro_school/                # Micro-school operations
│   │   ├── operations/                  # Calendar, documents, reports, readiness
│   │   └── sync/                        # Data sync endpoints
│   └── repositories/                    # Repository integration tests (was db/)
│
├── security/                            # RBAC/ABAC security matrix
│   ├── rbac/
│   ├── abac/
│   ├── audit/
│   └── tenancy/                         # Cross-tenant isolation ★ NEW
│
├── edge/                                # Boundary + error paths
├── performance/                         # Benchmarks + load patterns
└── contract/                            # OpenAPI + migration safety
```

## Running Tests

```bash
# All tests
pytest

# By category
pytest tests/unit/ -m unit
pytest tests/integration/api/iam/ -m integration
pytest tests/security/ -m security
pytest tests/edge/
pytest tests/performance/ -m performance
pytest tests/contract/

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/schemas/test_iam_schemas.py -v

# Verbose output
pytest -vv tests/
```

## Coverage

- **Threshold**: `fail_under = 90` in `pyproject.toml`
- **Operational scripts excluded**: `app/seed.py`, `app/scripts/*`, `app/templates/*`, `app/alembic/*`
- **Diff-cover gate**: New code in PRs must be ≥ 95% covered

Check coverage with:
```bash
pytest --cov=app --cov-branch --cov-report=term-missing
```

## Test Data

All factories generate **Moroccan-specific data**:
- Grades: 0-20 scale (Moroccan standard)
- Currency: MAD (Moroccan Dirham)
- Phone: +212 format
- Names: French/Arabic names common in Morocco
- Timezone: Africa/Casablanca

See **`_support/factories/`** directory for complete factory definitions.

## Async Testing Notes

- Use `@pytest.mark.asyncio` for async test functions
- `db_session` fixture provides SQLAlchemy AsyncSession
- `test_client` fixture provides FastAPI TestClient
- Fixtures automatically handle transaction rollback

## Key Testing Patterns

1. **Unit Tests**: Mock external dependencies, test business logic
2. **Integration Tests**: Use testcontainers PostgreSQL, real database queries
3. **Security Tests**: Verify RBAC matrices and ABAC policy enforcement
4. **Edge Cases**: Test boundary conditions and error paths
5. **Performance**: Monitor response times against SLA targets
6. **Contracts**: Validate API schemas and migration safety
