# Service Unit Tests

Unit tests for the business logic layer. Each test file corresponds to a service module. Dependencies (repositories, external services) are mocked to test logic in isolation.

## Files

- **test_auth_service.py** — Authentication, JWT tokens, password policies, 2FA
- **test_school_service.py** — School CRUD, academic year management
- **test_billing_service.py** — Invoice generation, payment processing, subscriptions
- **test_gradebook_service.py** — Grade entry, weighted averages, report cards
- **test_grading_service.py** — Moroccan 0-20 grade calculation and mention assignment
- **test_quiz_service.py** — Quiz attempts, auto-grading, question randomization
- **test_assignment_service.py** — Assignment lifecycle and submission handling
- **test_attendance_service.py** — Attendance recording and analytics
- **test_communication_service.py** — Messaging and notification dispatch
- **test_report_service.py** — Report generation and scheduling
- **test_timetable_service.py** — Timetable generation and conflict detection

## Running

```bash
pytest backend/tests/unit/services/ -v
```
