# Backend Test Suite

Comprehensive test suite for the Ecole Platform, a K-12 EdTech SaaS for Moroccan schools. **1,203 total tests** with **96.71% line coverage** and **95.67% branch coverage**.

## Overview

- **Framework**: pytest with factory_boy + Faker for test data generation
- **Infrastructure**: testcontainers (PostgreSQL) for integration tests
- **Configuration**: See `pytest.ini` for test execution settings
- **Async Support**: SQLAlchemy async sessions via `conftest.py` fixtures

## Test Categories (6 types)

| Category | Tests | Purpose |
|----------|-------|---------|
| **Unit** | 412 | Business logic in isolation with mocked dependencies |
| **Integration** | 46 | Real database interactions with testcontainers |
| **Security** | 105 | RBAC matrix, ABAC policies, permission escalation |
| **Edge Cases** | 81 | Boundary values, error paths, timezone handling |
| **Performance** | 33 | Response time SLAs, concurrent request patterns |
| **Contract** | 18 | OpenAPI schema compliance, migration safety |

## Key Files

### Root Configuration
- **conftest.py** - Shared fixtures: async DB sessions, test client, base test setup
- **pytest.ini** - Test runner configuration
- **__init__.py** - Package marker

### Root-Level Tests (Legacy Phase Tests)
- **test_auth.py** - Authentication workflows (19,664 bytes)
- **test_contract.py** - Contract testing foundations (18,216 bytes)
- **test_phase1b_profiles.py** - User profile management
- **test_phase2c_register.py** - Registration flows
- **test_phase2d_family.py** - Family/guardian relationships
- **test_phase3.py** - Core LMS functionality (27,443 bytes)
- **test_phase3b_uploads.py** - File upload handling
- **test_phase3c_websocket.py** - WebSocket communication
- **test_phase3d_filters.py** - API filtering & pagination
- **test_phase3e_tasks.py** - Task management workflows
- **test_phase13_notifications.py** - Notification system
- **test_phase14_reports_analytics.py** - Reports & analytics
- **test_phase15_calendar_events.py** - Calendar event handling
- **test_phase16_document_management.py** - Document lifecycle
- **test_rbac_security.py** - RBAC enforcement (25,153 bytes)
- **test_security_audit.py** - Security audit trails (16,622 bytes)
- **test_unit_iam.py** - Identity & access management (7,687 bytes)
- **test_unit_response.py** - Response formatting (10,649 bytes)

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| **factories/** | Test data factories with Moroccan-specific defaults |
| **unit/** | Business logic tests (412 tests across core/domain/models/services) |
| **integration/** | Database & API endpoint tests (46 tests) |
| **security/** | RBAC/ABAC policy tests (105 tests) |
| **edge/** | Boundary values & error handling (81 tests) |
| **performance/** | Load & benchmark tests (33 tests) |
| **contract/** | Schema & migration contracts (18 tests) |

## Running Tests

```bash
# All tests
pytest

# Specific category
pytest backend/tests/unit/
pytest backend/tests/integration/
pytest backend/tests/security/

# With coverage
pytest --cov=backend --cov-report=html

# Specific test file
pytest backend/tests/test_auth.py

# Verbose output
pytest -vv backend/tests/
```

## Test Data

All factories generate **Moroccan-specific data**:
- Grades: 0-20 scale (Moroccan standard)
- Currency: MAD (Moroccan Dirham)
- Phone: +212 format
- Names: French/Arabic names common in Morocco
- Timezone: Africa/Casablanca

See **factories/** directory for complete factory definitions.

## Coverage Goals

- **Line Coverage**: 96.71%
- **Branch Coverage**: 95.67%

Check coverage with: `pytest --cov=backend --cov-report=term-missing`

## Async Testing Notes

- Use `@pytest.mark.asyncio` for async test functions
- `async_session` fixture provides SQLAlchemy AsyncSession
- `test_client` fixture provides FastAPI TestClient
- Fixtures automatically handle transaction rollback

## Key Testing Patterns

1. **Unit Tests**: Mock external dependencies, test business logic
2. **Integration Tests**: Use testcontainers PostgreSQL, real database queries
3. **Security Tests**: Verify RBAC matrices and ABAC policy enforcement
4. **Edge Cases**: Test boundary conditions and error paths
5. **Performance**: Monitor response times against SLA targets
6. **Contracts**: Validate API schemas and migration safety
