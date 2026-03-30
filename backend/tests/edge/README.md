# Edge Case Tests

**81 tests** validating boundary values, error handling chains, and time-dependent behavior. Tests confirm system robustness under extreme conditions.

## Overview

- **Coverage**: Moroccan grade boundaries, currency overflow, timezone edge cases
- **Approach**: Boundary value analysis, equivalence partitioning, state machine testing
- **Framework**: pytest with freezegun for time manipulation

## Test Files

### test_boundary_values.py - Moroccan Grade & Currency Limits
Tests grade scale boundaries and monetary precision edge cases.

**Grade Boundaries (0-20 Moroccan Scale):**
- Minimum valid: 0
- Just above minimum: 0.01
- Just below maximum: 19.99
- Maximum valid: 20
- Just above maximum: 20.01 (invalid)
- Invalid: -0.01, -1, 25, 1000

**Grade Decimal Precision:**
- Valid: 15.7, 15.75, 15.750 (trailing zeros)
- Invalid: 15.756 (3 decimals), 15.7599 (4 decimals)
- Edge: 0.00, 0.01, 19.99, 20.00

**Grade Interpretation Boundaries:**
```
0-9: Fail
10-13: Pass
14-17: Good
18-20: Excellent

Boundaries: 9.99→10.00, 13.99→14.00, 17.99→18.00
```

**Currency (MAD) Boundaries:**
- Minimum transaction: 0.01 MAD
- Maximum invoice: MAD ceiling (school budget)
- Overflow testing: 999999999.99 MAD
- Underflow: Negative amounts (refunds)
- Precision: 2 decimal places required
  - Valid: 100.00, 100.50, 100.01
  - Invalid: 100.001 (3 decimals), 100.005 (rounds)

**Test Example:**
```python
async def test_grade_boundary_zero():
    grade = Grade(value=Decimal("0"))
    assert grade.value == 0
    assert grade.interpretation == GradeLevel.FAIL

async def test_grade_boundary_maximum():
    grade = Grade(value=Decimal("20"))
    assert grade.value == 20
    assert grade.interpretation == GradeLevel.EXCELLENT

async def test_grade_above_maximum_rejected():
    with pytest.raises(GradeValidationError):
        Grade(value=Decimal("20.01"))

async def test_currency_precision_violation():
    # 3 decimal places not allowed
    with pytest.raises(MoneyPrecisionError):
        Money(amount=Decimal("100.001"), currency="MAD")
```

### test_error_paths.py - Exception Chains
Tests error handling and exception propagation through call stacks.

**Exception Categories:**

1. **Input Validation Errors**
   - Invalid grade (>20, <0)
   - Invalid phone (+1 instead of +212)
   - Invalid email format
   - Missing required fields

2. **Business Logic Errors**
   - Duplicate entry (student already in class)
   - State conflicts (publish already-published grades)
   - Relationship violations (parent not linked to student)
   - Capacity exceeded (class > 40 students)

3. **Database Errors**
   - Integrity constraints violated
   - Foreign key mismatch
   - Unique constraint violation
   - Deadlock in concurrent transaction

4. **Authorization Errors**
   - Permission denied (RBAC)
   - Relationship access denied (ABAC)
   - Role insufficient for operation
   - Session expired

5. **External Service Errors**
   - Payment gateway failure
   - Email service timeout
   - File upload rejection
   - Third-party API unavailable

**Error Propagation Testing:**

```python
async def test_error_chain_invalid_grade():
    # Grade validation → Service exception → API 400 response
    with pytest.raises(GradeValidationError) as exc_info:
        await grading_service.enter_grade(grade=25)

    error = exc_info.value
    assert error.code == "INVALID_GRADE"
    assert error.status_code == 400
    assert "0-20" in str(error)
    # Verify no data persisted
    assert await grades_repo.count() == 0

async def test_error_chain_duplicate_entry():
    # Create student → Verify relationship → Check enrollment → Duplicate detected
    student_id = uuid4()
    class_id = uuid4()

    # First enrollment succeeds
    await enrollment_service.enroll_student(student_id, class_id)

    # Second enrollment fails with specific error
    with pytest.raises(DuplicateEnrollmentError):
        await enrollment_service.enroll_student(student_id, class_id)

    # Verify only one enrollment exists
    enrollments = await enrollment_repo.find_by_student(student_id)
    assert len(enrollments) == 1

async def test_error_chain_concurrent_transaction_deadlock():
    # Simulate concurrent updates causing deadlock
    with pytest.raises(DatabaseDeadlockError):
        async with concurrent.TaskGroup() as tg:
            tg.create_task(update_grade_1())
            tg.create_task(update_grade_2())
    # Verify transaction rolled back completely
```

**Error Response Format:**
```json
{
  "code": "INVALID_GRADE",
  "message": "Grade must be between 0 and 20",
  "status_code": 400,
  "context": {
    "received_value": 25,
    "valid_range": "0-20"
  },
  "timestamp": "2026-03-30T10:30:00Z",
  "request_id": "req-uuid"
}
```

### test_time_dependent.py - Timezone & DST Edge Cases
Tests behavior around daylight saving time transitions and timezone handling.

**Timezone: Africa/Casablanca (WET/WEST)**
- WET (Western European Time): UTC+0 (Winter)
- WEST (Western European Summer Time): UTC+1 (Summer)
- Transition: Last Sunday of March (2:59 AM → 3:00 AM)
- Fall-back: Last Sunday of October (3:59 AM → 3:00 AM)

**DST Transition Test Cases:**

1. **Spring Forward (2:59 AM → 3:00 AM)**
   ```python
   async def test_spring_forward_time_gap():
       # Test event scheduled for 2:30 AM (doesn't exist)
       with pytest.raises(InvalidTimeError):
           await calendar_service.create_event(
               datetime=datetime(2026, 3, 29, 2, 30, tzinfo=casablanca_tz)
           )
   ```

2. **Fall Back (3:59 AM → 3:00 AM - 1 hour repeats)**
   ```python
   async def test_fall_back_duplicate_time():
       # Event at 3:30 AM on transition day is ambiguous
       time1 = datetime(2026, 10, 25, 3, 30, tzinfo=casablanca_tz, fold=0)  # First 3:30
       time2 = datetime(2026, 10, 25, 3, 30, tzinfo=casablanca_tz, fold=1)  # Second 3:30
       # System should distinguish and not create duplicate events
       event1 = await calendar_service.create_event(datetime=time1)
       event2 = await calendar_service.create_event(datetime=time2)
       assert event1.id != event2.id
   ```

3. **Academic Calendar Boundaries**
   ```python
   async def test_academic_year_boundary_at_midnight():
       # School year ends at 2026-06-30 23:59:59 Casablanca time
       # Next day starts new year
       assert await calendar_service.get_current_year() == 2025_2026

       # Move to 2026-07-01 00:00:00
       assert await calendar_service.get_current_year() == 2026_2027
   ```

4. **Grade Entry Timestamp**
   ```python
   async def test_grade_entry_preserves_casablanca_timezone():
       # Grade entered at 10:30 AM Casablanca time
       grade = await grading_service.enter_grade(
           grade_value=15.5,
           timestamp=datetime(2026, 3, 30, 10, 30, tzinfo=casablanca_tz)
       )
       # Timestamp stored with Casablanca timezone
       assert grade.created_at.tzinfo == casablanca_tz
   ```

5. **Attendance Roll Call Timing**
   ```python
   async def test_attendance_morning_rollcall_at_dst_boundary():
       # Morning roll call normally at 8:00 AM
       # During transition, verify system handles correctly
       rollcall_time = datetime(2026, 3, 29, 8, 0, tzinfo=casablanca_tz)
       # System should treat as valid time
       attendance = await attendance_service.record_rollcall(
           class_id=class_id,
           timestamp=rollcall_time
       )
       assert attendance.created_at.tzinfo == casablanca_tz
   ```

6. **Scheduled Task Execution**
   ```python
   async def test_scheduled_task_skips_invalid_dst_time():
       # Task scheduled for 2:30 AM on spring-forward day
       # Should be skipped or executed at next valid time
       with pytest.raises(NoValidTimeError):
           await scheduler.schedule_task(
               task_id="daily_report",
               time=time(2, 30),  # Invalid on DST transition
               date=date(2026, 3, 29)
           )
   ```

**Freezegun Usage for Time Control:**
```python
@pytest.mark.freezegun
async def test_with_frozen_time():
    # Freeze time at specific moment
    freeze_time("2026-03-29 02:30:00+01:00")  # Spring-forward transition
    # Test code here operates with frozen clock
```

## Running Tests

```bash
# All edge case tests
pytest backend/tests/edge/

# By category
pytest backend/tests/edge/test_boundary_values.py
pytest backend/tests/edge/test_error_paths.py -v
pytest backend/tests/edge/test_time_dependent.py

# By keyword
pytest backend/tests/edge/ -k "boundary" -v
pytest backend/tests/edge/ -k "grade" -v
pytest backend/tests/edge/ -k "timezone" -v
pytest backend/tests/edge/ -k "dst" -v

# With coverage
pytest backend/tests/edge/ --cov=backend --cov-report=html

# Slow tests (timezone transitions)
pytest backend/tests/edge/ -v --durations=0
```

## Key Testing Principles

1. **Boundary Analysis**: Test min, max, just below max, just above min
2. **Equivalence Classes**: Group test cases by behavior
3. **State Transitions**: Test invalid state changes
4. **Error Messages**: Verify clear, actionable error messages
5. **Cleanup**: Ensure failed operations don't leave partial data
6. **Reproducibility**: Time-dependent tests use freezegun for isolation

## Moroccan-Specific Edge Cases

- Grade 0 (lowest score, student must retake)
- Grade 20 (perfect score, rare but important)
- MAD 0.01 (smallest monetary unit)
- +212 phone format (not +1, +44, etc.)
- DST transitions (Africa/Casablanca specific dates)
- Arabic diacritics in names (ع، غ، خ، ح، ق، ك)

## Performance Under Load

- Grade entry bulk import: 1000 grades < 5s
- Concurrent grade updates: 10 simultaneous < 2s
- Payment processing (concurrent): 100 payments < 10s

## Coverage Goals

- **Boundary**: 100% of min/max/off-by-one values
- **Error**: All error paths tested
- **Time**: All DST transitions and edge cases
- **Moroccan**: All locale-specific edge cases

## Related Documentation

- Parent: `backend/tests/README.md`
- Unit: `backend/tests/unit/domain/` for value object edge cases
- Integration: `backend/tests/integration/` for persistence tests
- Security: `backend/tests/security/` for authorization edge cases
