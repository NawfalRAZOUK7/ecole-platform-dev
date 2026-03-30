# Unit Tests

**412 total tests** covering business logic in isolation. All external dependencies are mocked. Tests are organized by layer (core infrastructure, domain models, ORM models, and services).

## Structure

```
unit/
├── core/          - Core infrastructure (permissions, ABAC, exceptions)
├── domain/        - Domain value objects (Grade, Money, RoleSet, TypedID)
├── models/        - ORM model representation & validation
└── services/      - Service layer business logic (11 services)
```

## Test Categories

### Core Infrastructure (3 tests)
**Path**: `unit/core/`

- **test_abac.py** - ABAC (Attribute-Based Access Control) policy engine
  - Policy evaluation with attributes
  - Effect resolution (Allow/Deny/Inherit)
  - Context-aware authorization logic

- **test_permissions.py** - Permission constants catalog
  - 166+ permission definitions
  - Permission categories (READ, CREATE, UPDATE, DELETE, EXECUTE)
  - Role-permission matrix validation

- **test_exceptions_additional.py** - Custom exception hierarchy
  - Business logic exceptions
  - Error message templates

### Domain Value Objects (5 tests)
**Path**: `unit/domain/`

Immutable, self-validating value objects. No mocks needed—pure logic testing.

- **test_grade.py** - Moroccan 0-20 grading system
  - Valid range: 0-20 with decimal precision
  - Grade interpretation (Excellent/Good/Pass/Fail)
  - Conversion to percentage (multiply by 5)

- **test_money.py** - MAD (Moroccan Dirham) currency
  - Arithmetic operations (add, subtract, multiply)
  - Currency validation
  - Decimal precision handling (2 places)

- **test_role_set.py** - Set of roles with operations
  - Role membership testing
  - Union/intersection of role sets
  - Immutability enforcement

- **test_typed_id.py** - Type-safe identifiers
  - ID format validation (UUID4)
  - Type safety across layers
  - Serialization/deserialization

- **test_value_object_additional.py** - Supplementary value object tests
  - Additional invariant checks
  - Edge case validation

### ORM Model Tests (4 tests)
**Path**: `unit/models/`

SQLAlchemy ORM model representation, validation, and helper properties.

- **test_repr.py** - Model __repr__ methods
  - String representation accuracy
  - Circular reference handling
  - Sensitive data masking

- **test_additional_repr.py** - Extended repr testing
  - Complex object graph representation
  - Performance considerations

- **test_validators.py** - ORM field validators
  - Moroccan phone format (+212 validation)
  - Email/URL validation
  - Enum constraint validation
  - Custom business rule validation

- **test_helper_properties.py** - Computed model properties
  - Grade interpretation properties
  - Age calculations
  - Status derivations
  - Relationship helpers

### Service Layer (11 services, ~220 tests)
**Path**: `unit/services/`

Business logic with mocked repositories and external services.

| Service | Tests | Key Coverage |
|---------|-------|--------------|
| **test_auth_service.py** | ~20 | Login, JWT token generation, password reset, MFA |
| **test_school_service.py** | ~6 | School CRUD, staff assignment, year management |
| **test_billing_service.py** | ~41 | Invoicing, subscriptions, payment processing, refunds |
| **test_gradebook_service.py** | ~11 | Grade entry, calculation, publication, archiving |
| **test_grading_service.py** | ~19 | Grade computation, curving, group operations |
| **test_quiz_service.py** | ~20 | Quiz creation, attempt tracking, auto-grading |
| **test_assignment_service.py** | ~25 | Assignment CRUD, submission tracking, rubric scoring |
| **test_attendance_service.py** | ~12 | Attendance marking, roll call, absence reporting |
| **test_communication_service.py** | ~9 | Notifications, messages, announcements |
| **test_report_service.py** | ~7 | Report generation, data aggregation, export |
| **test_timetable_service.py** | ~8 | Schedule creation, conflict detection, publishing |

## Running Unit Tests

```bash
# All unit tests
pytest backend/tests/unit/

# By layer
pytest backend/tests/unit/core/
pytest backend/tests/unit/domain/
pytest backend/tests/unit/models/
pytest backend/tests/unit/services/

# By service
pytest backend/tests/unit/services/test_auth_service.py

# With coverage
pytest backend/tests/unit/ --cov=backend.domain --cov-report=html

# Verbose
pytest backend/tests/unit/ -vv
```

## Mocking Strategy

- **Repositories**: Mocked via `unittest.mock.patch`
- **External APIs**: `responses` library for HTTP mocking
- **DateTime**: `freezegun` for time-dependent logic
- **Email**: In-memory backend for email tests

## Test Isolation

- No database access (all mocked)
- No external API calls
- No file system operations
- Each test is independent and can run in any order

## Fixtures

Shared fixtures from parent `conftest.py`:
- `app` - FastAPI test application
- `mock_db` - Mocked SQLAlchemy session
- `mock_redis` - Mocked Redis for caching
- Factory fixtures for common test objects

## Coverage Target

**Unit tests should maintain 96%+ coverage** for:
- Core domain models
- Service business logic
- Permission/authorization rules
- Validation logic

Run: `pytest backend/tests/unit/ --cov --cov-report=html`

## Related Documentation

- See **factories/** for test data generation
- See parent **README.md** for full test suite overview
- See **integration/** for database interaction tests
