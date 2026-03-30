# Database Repository Integration Tests

Data access layer testing with real PostgreSQL via testcontainers. Tests validate query correctness, transaction handling, and data persistence patterns.

## Test Files

### test_school_repo.py - School & Staff Repository
School organizational data access.

**Repository Operations:**
- Create/read/update/delete schools
- Find schools by director/supervisor
- Get all staff members for school
- Bulk staff assignments
- School archive/restore
- Academic year management

**Key Test Cases:**
- Single school creation and retrieval
- School with multiple classes and staff
- Director relationship verification
- Staff list filtering (active, role-based)
- Bulk import of staff (100+ records)
- Concurrent director assignments
- Soft delete (archive) and restoration
- Pagination (offset, limit)
- Sorting by name, creation date, status

**Example Test Patterns:**
```python
# Create school with director
school = await school_repo.create(
    name="Lycée Al-Khansaa",
    address="Rue Mohammed V",
    phone="+212612345678",
    director_id=director.id
)

# Query by director
schools = await school_repo.find_by_director(director_id)
assert len(schools) >= 1

# Bulk staff assignment
await school_repo.assign_staff_bulk(
    school_id=school.id,
    staff_ids=[emp1.id, emp2.id, emp3.id]
)
```

### test_lms_repo.py - Course, Assignment, Quiz Repository
Learning management system data access.

**Repository Operations:**
- Create/read/update courses
- Find courses by teacher, school, term
- Create/manage assignments
- Quiz creation and attempt tracking
- Grade storage and retrieval
- Bulk grade import
- Query with complex filters

**Key Test Cases:**
- Course with multiple assignments and quizzes
- Pagination of courses (50+ courses)
- Search courses by name/code
- Assignment with due date and rubric
- Quiz with multiple questions
- Grade entry validation (0-20 range)
- Grade import from CSV
- Querying grades with multiple filters (student, assignment, date range)
- Sorting by grade value, entry date

**Example Test Patterns:**
```python
# Create course with assignments
course = await course_repo.create(
    school_id=school.id,
    title="Mathématiques",
    term=Term.SPRING
)

assignments = await assignment_repo.find_by_course(course_id=course.id)
assert len(assignments) > 0

# Bulk grade import
grades_data = [
    GradeImportRow(student_id=s_id, value=Decimal("15.5"))
    for s_id in student_ids
]
await grades_repo.bulk_import(
    class_id=class_id,
    assignment_id=assignment_id,
    grades=grades_data
)

# Query with filters
grades = await grades_repo.find(
    class_id=class_id,
    assignment_id=assignment_id,
    min_value=Decimal("10"),
    sort_by="value DESC"
)
```

### test_billing_repo.py - Invoice & Payment Repository
Financial transaction data access.

**Repository Operations:**
- Create invoices from subscriptions
- Find invoices by school, date range, status
- Create payment records
- Track payment status and reconciliation
- Calculate school balance
- Subscription lifecycle management
- Refund processing
- Export billing data

**Key Test Cases:**
- Invoice generation with line items
- Line item pricing (course fees, storage, per-student)
- Invoice status transitions (draft → sent → paid)
- Payment creation and posting
- Partial payment handling
- Invoice search by date range
- Payment reconciliation (matched/unmatched)
- Subscription state (active, trial, expired, cancelled)
- Subscription renewal automation
- Refund request creation and approval
- School balance calculation (revenue - expenses)
- Export to CSV/PDF

**Example Test Patterns:**
```python
# Create invoice from subscription
subscription = await subscription_repo.get_active(school_id=school.id)
invoice = await invoice_repo.create_from_subscription(
    subscription_id=subscription.id,
    period_end=date.today()
)

# Find invoices by date range
invoices = await invoice_repo.find_by_date_range(
    school_id=school.id,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 3, 31),
    status="UNPAID"
)

# Process payment
payment = await payment_repo.create(
    invoice_id=invoice.id,
    amount=Money(amount=Decimal("1000.00"), currency="MAD"),
    method="BANK_TRANSFER"
)

# Calculate balance
balance = await billing_repo.calculate_school_balance(school_id)
assert balance.amount >= Decimal("0")
```

## Query Patterns

### Filtering
```python
# Find with multiple conditions
results = await repo.find(
    school_id=school_id,
    status="ACTIVE",
    limit=10,
    offset=0
)
```

### Sorting
```python
# Sort by field (ASC/DESC)
results = await repo.find_sorted(
    school_id=school_id,
    sort_by="name ASC"
)
```

### Date Range Queries
```python
# Time-bound queries
invoices = await invoice_repo.find_by_date_range(
    school_id=school_id,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 12, 31)
)
```

### Relationship Loading
```python
# Eager load relationships
school = await school_repo.get_with_relationships(
    school_id,
    include=["classes", "staff", "courses"]
)
assert len(school.classes) > 0
```

## Transaction Testing

### Isolation Levels
```python
async def test_concurrent_updates():
    # Each test gets isolated transaction
    # No phantom reads or dirty reads
    # Automatic rollback on test completion
```

### Rollback Verification
```python
async def test_failed_operation_rollback():
    # Failed operation doesn't persist
    with pytest.raises(IntegrityError):
        await repo.create_invalid()

    # Verify no partial data persisted
    count = await repo.count()
    assert count == original_count
```

## Performance Testing

- Single insert: <10ms
- Bulk insert (100 rows): <50ms
- Complex query (joins, filters): <100ms
- Pagination (1000 rows): <20ms

## Moroccan Context

All repositories handle:
- **Grades**: 0-20 scale
- **Currency**: MAD with 2 decimal precision
- **Phones**: +212 format validation
- **Timezone**: Africa/Casablanca for all timestamps
- **Language**: Fr/Ar name support

## Running Tests

```bash
# All database tests
pytest backend/tests/integration/db/

# Specific repository
pytest backend/tests/integration/db/test_school_repo.py
pytest backend/tests/integration/db/test_billing_repo.py -v

# By keyword
pytest backend/tests/integration/db/ -k "pagination" -v
pytest backend/tests/integration/db/ -k "moroccan" -v

# With coverage
pytest backend/tests/integration/db/ --cov=backend.repositories --cov-report=html
```

## Common Patterns

### Setup/Teardown
```python
@pytest.fixture
async def populated_database(async_session):
    """Create test data before test"""
    school = await create_test_school(async_session)
    classes = await create_test_classes(async_session, school, count=5)
    students = await create_test_students(async_session, classes)
    await async_session.commit()
    return {"school": school, "classes": classes, "students": students}
```

### Assertion Patterns
```python
# Verify count
count = await repo.count()
assert count == expected_count

# Verify data
item = await repo.get(id=item_id)
assert item.name == "Expected Name"

# Verify relationships
school = await school_repo.get_with_relationships(school_id)
assert len(school.classes) == 3
```

## Related Documentation

- Parent: `backend/tests/integration/README.md`
- API: `backend/tests/integration/api/README.md`
- Factories: `backend/tests/factories/README.md`
- Repositories: `backend/repositories/` for implementation
