# API Endpoint Integration Tests

HTTP endpoint contract testing with real database. Tests validate request/response formats, error handling, and business logic enforcement at API layer.

## Test Files

### test_schools_api.py - School Management Endpoints
CRUD operations for schools and organizational units.

**Endpoints Tested:**
- `GET /api/schools` - List schools with pagination, search, filters
- `POST /api/schools` - Create new school
- `GET /api/schools/{id}` - Retrieve school details with relationships
- `PUT /api/schools/{id}` - Update school information
- `DELETE /api/schools/{id}` - Delete school (with cascade handling)

**Key Test Cases:**
- Successful creation with all required fields
- Validation of Moroccan-specific fields (phone +212, MAD currency)
- Pagination (offset, limit)
- Search by name (case-insensitive)
- Authorization (director-only update)
- Soft delete handling (archive vs. permanent)
- Relationship loading (eager vs. lazy)

### test_billing_api.py - Billing Operations
Invoice and payment processing endpoints.

**Endpoints Tested:**
- `POST /api/invoices` - Create invoice from subscription/service
- `GET /api/invoices` - List invoices with date range filter
- `GET /api/invoices/{id}` - Retrieve invoice with line items
- `POST /api/payments` - Process payment
- `GET /api/payments/{id}/status` - Check payment status

**Key Test Cases:**
- Invoice generation from service fees
- Payment validation (amount, method, currency)
- Currency precision (MAD 2 decimal places)
- Subscription state transitions
- Refund processing
- Partial payment handling
- Invoice PDF generation

### test_gradebook_api.py - Grade Management
Grade entry, publication, and archival.

**Endpoints Tested:**
- `POST /api/gradebook/grades` - Enter grade
- `GET /api/gradebook/{class_id}` - Get class gradebook
- `PUT /api/gradebook/grades/{id}` - Update grade with audit
- `POST /api/gradebook/publish` - Publish grades to students
- `GET /api/gradebook/{class_id}/archive` - Retrieve archived grades

**Key Test Cases:**
- Grade validation (0-20 Moroccan scale)
- Decimal precision (e.g., 15.75)
- Grade interpretation (Excellent/Good/Pass/Fail)
- Duplicate prevention (one grade per student per assessment)
- Publication workflow (draft → published)
- Archival after school year ends
- Student notification on publication
- Teacher override with reason logging

### test_rubrics_api.py - Rubric-Based Grading
Rubric creation and rubric-based scoring.

**Endpoints Tested:**
- `POST /api/rubrics` - Create grading rubric
- `GET /api/rubrics/{id}` - Retrieve rubric with criteria
- `POST /api/rubrics/{id}/grades` - Apply rubric to assignment
- `PUT /api/rubrics/{id}` - Update rubric criteria/weights

**Key Test Cases:**
- Rubric with multiple criteria (4-6 typical)
- Weight validation (sum = 100%)
- Performance level definitions (4-5 levels)
- Score calculation (weighted average)
- Rubric versioning (effective dates)
- Rubric reuse across assignments
- Export to PDF

### test_attendance_analytics_api.py - Attendance Analytics
Attendance data aggregation and reporting.

**Endpoints Tested:**
- `GET /api/attendance/analytics/{class_id}` - Attendance summary
- `GET /api/attendance/analytics/{student_id}` - Individual attendance
- `GET /api/attendance/analytics/by-date/{date}` - Attendance by date
- `GET /api/attendance/export` - Export attendance CSV

**Key Test Cases:**
- Attendance percentage calculation
- Time series (daily, weekly, monthly)
- Absence patterns (chronic absentees)
- Lateness tracking
- Export format (CSV, PDF)
- Timezone handling (Africa/Casablanca dates)
- Date range filtering
- Student/class/school aggregation levels

### test_timetable_api.py - Schedule Management
Timetable/schedule creation and conflict detection.

**Endpoints Tested:**
- `POST /api/timetable` - Create weekly schedule
- `GET /api/timetable/{class_id}` - Get class schedule
- `GET /api/timetable/conflicts` - Detect scheduling conflicts
- `PUT /api/timetable/{id}` - Modify schedule entry
- `POST /api/timetable/publish` - Make schedule official

**Key Test Cases:**
- Schedule creation (all days/periods)
- Teacher availability constraints
- Room capacity validation
- Subject conflict detection (teacher in 2 places)
- Break time enforcement
- Timezone-aware timing (Africa/Casablanca)
- Change notification to stakeholders
- Schedule publication workflow

## Shared Utilities

### helpers.py - Test Helpers

**Key Functions:**
- `create_test_client(session)` - Authenticated FastAPI TestClient
- `login_user(client, email, password)` - Get auth token
- `set_auth_header(client, token)` - Add Bearer token
- `create_test_school(session)` - Pre-populated school with staff
- `create_test_users(session, count, role)` - Batch user creation

**Example Usage:**
```python
async def test_endpoint(test_client):
    # test_client fixture already authenticated
    response = await test_client.get("/api/schools")
    assert response.status_code == 200
```

## Common Patterns

### Error Response Testing
```python
async def test_invalid_grade():
    response = await test_client.post(
        "/api/grades",
        json={"value": 25}  # Invalid > 20
    )
    assert response.status_code == 400
    error = response.json()
    assert error["code"] == "INVALID_GRADE"
    assert error["message"] contains "0-20"
```

### Authorization Testing
```python
async def test_unauthorized_access():
    # Test with student role (should fail)
    response = await test_client.post(
        "/api/schools",
        json={"name": "New School"}
    )
    assert response.status_code == 403
```

### Moroccan Data Validation
```python
async def test_moroccan_phone_format():
    response = await test_client.post(
        "/api/users",
        json={
            "email": "user@school.ma",
            "phone": "+212612345678"  # Valid
        }
    )
    assert response.status_code == 201

    response = await test_client.post(
        "/api/users",
        json={
            "email": "user@school.ma",
            "phone": "+1612345678"  # Invalid
        }
    )
    assert response.status_code == 422
```

## Running Tests

```bash
# All API tests
pytest backend/tests/integration/api/

# By endpoint
pytest backend/tests/integration/api/test_schools_api.py
pytest backend/tests/integration/api/test_billing_api.py -v

# By keyword
pytest backend/tests/integration/api/ -k "authorization" -v
pytest backend/tests/integration/api/ -k "moroccan" -v

# With coverage
pytest backend/tests/integration/api/ --cov=backend.api --cov-report=html
```

## Test Isolation

- Each test gets fresh database via testcontainers
- Transactions automatically rolled back
- No cross-test data pollution
- Parallel test execution safe

## Performance Considerations

- Single endpoint test: 50-150ms
- Full file suite: 10-30s
- Run tests in parallel for CI: `pytest -n auto`

## Related Documentation

- Parent: `backend/tests/integration/README.md`
- Database: `backend/tests/integration/db/README.md`
- Factories: `backend/tests/factories/README.md`
- Security: `backend/tests/security/README.md` for authorization testing
