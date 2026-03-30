# Integration Tests

**46 tests** with real database interactions using testcontainers PostgreSQL. Tests validate repository patterns, API endpoints, and cross-layer integration.

## Overview

- **Database**: testcontainers PostgreSQL (real schema, real data)
- **Approach**: Full stack testing with actual persistence
- **Categories**: API endpoints (6 test files) + Database repositories (3 test files)
- **Fixtures**: `async_session` fixture manages transactions and rollback

## Test Categories

### API Endpoint Tests (6 files)
**Path**: `integration/api/`

Test HTTP endpoint contracts and response formats with real database.

| File | Endpoints | Coverage |
|------|-----------|----------|
| **test_schools_api.py** | GET/POST/PUT /schools, /schools/{id} | School CRUD, pagination, search |
| **test_billing_api.py** | POST /invoices, GET /invoices, /payments | Invoice creation, payment processing |
| **test_gradebook_api.py** | GET/POST /gradebook | Grade entry, publication, filtering |
| **test_rubrics_api.py** | GET/POST /rubrics, /rubrics/{id}/grades | Rubric CRUD, grade mapping |
| **test_attendance_analytics_api.py** | GET /attendance/analytics | Attendance stats, time series |
| **test_timetable_api.py** | POST /timetable, GET /timetable/conflicts | Schedule creation, conflict detection |

**Key Files:**
- **helpers.py** - Shared test utilities: client fixture, auth helpers, data setup

### Database Repository Tests (3 files)
**Path**: `integration/db/`

Test data access layer with real database transactions.

| File | Entity | Coverage |
|------|--------|----------|
| **test_school_repo.py** | School, Director, Staff | CRUD, relationships, bulk operations |
| **test_lms_repo.py** | Course, Assignment, Quiz, Grade | Query filters, sorting, pagination |
| **test_billing_repo.py** | Invoice, Payment, Subscription | Transaction isolation, balance queries |

## Running Tests

```bash
# All integration tests
pytest backend/tests/integration/

# By category
pytest backend/tests/integration/api/
pytest backend/tests/integration/db/

# Specific test
pytest backend/tests/integration/api/test_schools_api.py::test_create_school_success

# With coverage
pytest backend/tests/integration/ --cov=backend --cov-report=html

# Live database (requires postgres running)
pytest backend/tests/integration/ -m "not testcontainer"
```

## Test Fixtures

### Database Fixtures
```python
@pytest.fixture
async def async_session(postgres_container):
    """Async SQLAlchemy session with testcontainers PostgreSQL"""
    # Creates fresh database for each test
    # Rolls back after test completes
    # Ensures transaction isolation
```

### API Fixtures
```python
@pytest.fixture
async def test_client(async_session):
    """FastAPI TestClient with authenticated context"""
    # Includes auth headers
    # Uses same database session as tests
```

### Data Setup
```python
@pytest.fixture
async def school_with_users(async_session):
    """Pre-populated school with director, teachers, students"""
    # Uses factories for consistent test data
    # Committed to database for queries
```

## testcontainers Strategy

**Benefits:**
- Real PostgreSQL (no SQLite mocks)
- Schema validation (migrations run)
- Complex queries tested
- Concurrent access patterns
- Realistic performance metrics

**Trade-offs:**
- Slower than unit tests (5-10s per test)
- Requires Docker running
- Network I/O overhead
- Database startup per test session

**Configuration:**
```python
# In conftest.py
@pytest.fixture(scope="session")
def postgres_container():
    container = PostgresContainer(image="postgres:15")
    container.start()
    yield container
    container.stop()
```

## API Integration Patterns

### Authentication
```python
async def test_authenticated_endpoint(test_client):
    # Auth headers automatically included
    response = await test_client.get("/api/schools")
    assert response.status_code == 200
```

### Error Handling
```python
async def test_invalid_grade_rejection(test_client):
    response = await test_client.post(
        "/api/grades",
        json={"value": 21}  # Invalid: > 20
    )
    assert response.status_code == 400
    assert "Grade must be 0-20" in response.json()["detail"]
```

### Data Validation
```python
async def test_moroccan_phone_validation(test_client):
    response = await test_client.post(
        "/api/users",
        json={"phone": "+1234567890"}  # Wrong country code
    )
    assert response.status_code == 422
    assert "must start with +212" in response.json()["detail"]
```

## Database Integration Patterns

### Transaction Isolation
```python
async def test_concurrent_grade_updates(async_session):
    # Each test gets fresh session
    # Automatic rollback after test
    # No cross-test data pollution
```

### Complex Queries
```python
async def test_gradebook_with_filters(async_session):
    # Real query with joins, filters, sorting
    gradebook = await gradebook_repo.find_by_class_and_period(
        class_id=class_id,
        period_id=period_id,
        include_absences=True
    )
    assert len(gradebook.students) == 30
```

### Bulk Operations
```python
async def test_bulk_grade_import(async_session):
    # Insert 100 grades in single transaction
    grades = [
        Grade(student_id=s_id, value=Decimal("15.5"))
        for s_id in student_ids
    ]
    await grades_repo.bulk_create(grades)

    # Verify all persisted
    count = await grades_repo.count()
    assert count == 100
```

## Performance Expectations

- Single CRUD test: 100-200ms
- API endpoint test: 50-150ms
- Complex query test: 200-500ms
- Bulk operation test: 500-1000ms

## Common Issues

**Issue**: testcontainer fails to start
**Solution**: Ensure Docker is running, check disk space

**Issue**: Tests pass locally but fail in CI
**Solution**: Check database connection pooling, transaction isolation level

**Issue**: Slow test execution
**Solution**: Use test markers to skip expensive tests during development

## Related Documentation

- Parent: `backend/tests/README.md`
- Unit Tests: `backend/tests/unit/README.md`
- Security: `backend/tests/security/README.md`
- Factories: `backend/tests/factories/README.md`
