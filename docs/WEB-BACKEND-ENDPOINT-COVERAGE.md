# Web Backend Endpoint Coverage Report

Snapshot date: April 10, 2026

This report compares backend HTTP endpoints defined in `backend/app/api/v1/*.py` against frontend API calls found in `web/src/**/*.service.ts`.

Coverage rules:

- `COVERED`: exact normalized path and HTTP method match
- `PARTIAL`: normalized path exists in frontend, but HTTP method differs
- `UNCOVERED`: no matching frontend call found

Notes:

- Only decorated backend HTTP routes were counted.
- `api.list(...)` in frontend services is treated as `GET`.
- Path variables are normalized, for example `/users/{id}` and `/users/{user_id}` are treated as the same path shape.
- Query-only conditional suffixes are ignored for path matching.
- Conditional endpoint branches in frontend services are expanded when both branches resolve to concrete API paths.
- Partial endpoints are not counted as covered in the coverage percentage.

## Summary

- Total backend endpoints: `350`
- Covered: `338`
- Partial: `1`
- Uncovered: `11`
- Coverage: `96.6%`

Comparison vs April 8, 2026 snapshot:

- Old coverage: `81.3%` (`283 / 348`)
- New coverage: `96.6%` (`338 / 350`)
- Delta: `+15.3` points

## Module Coverage

| Backend Module | Total | Covered | Uncovered | Coverage % |
|---|---:|---:|---:|---:|
| activities | 3 | 3 | 0 | 100.0% |
| admin | 15 | 15 | 0 | 100.0% |
| ai | 5 | 1 | 4 | 20.0% |
| analytics | 5 | 5 | 0 | 100.0% |
| announcements | 4 | 4 | 0 | 100.0% |
| assessments | 4 | 4 | 0 | 100.0% |
| assignments | 4 | 3 | 0 | 75.0% |
| attendance | 5 | 5 | 0 | 100.0% |
| attendance_analytics | 5 | 5 | 0 | 100.0% |
| auth | 14 | 14 | 0 | 100.0% |
| billing | 14 | 14 | 0 | 100.0% |
| budgets | 17 | 17 | 0 | 100.0% |
| class_assignments | 1 | 1 | 0 | 100.0% |
| classes | 1 | 1 | 0 | 100.0% |
| cms | 6 | 6 | 0 | 100.0% |
| compliance | 12 | 12 | 0 | 100.0% |
| consents | 2 | 2 | 0 | 100.0% |
| content | 9 | 7 | 2 | 77.8% |
| content_library | 6 | 6 | 0 | 100.0% |
| courses | 2 | 2 | 0 | 100.0% |
| devices | 3 | 3 | 0 | 100.0% |
| documents | 24 | 24 | 0 | 100.0% |
| enrollments | 2 | 2 | 0 | 100.0% |
| events | 15 | 15 | 0 | 100.0% |
| exports | 2 | 2 | 0 | 100.0% |
| features | 6 | 6 | 0 | 100.0% |
| feed | 1 | 1 | 0 | 100.0% |
| financial_health | 12 | 12 | 0 | 100.0% |
| gdpr | 3 | 3 | 0 | 100.0% |
| gradebook | 5 | 5 | 0 | 100.0% |
| invitations | 3 | 3 | 0 | 100.0% |
| invoices | 2 | 2 | 0 | 100.0% |
| messaging | 7 | 7 | 0 | 100.0% |
| micro_school | 15 | 15 | 0 | 100.0% |
| notifications | 13 | 11 | 2 | 84.6% |
| payments | 4 | 3 | 1 | 75.0% |
| profiles | 4 | 4 | 0 | 100.0% |
| progress | 4 | 4 | 0 | 100.0% |
| question_bank | 5 | 5 | 0 | 100.0% |
| quizzes | 10 | 10 | 0 | 100.0% |
| recovery | 3 | 3 | 0 | 100.0% |
| reports | 10 | 10 | 0 | 100.0% |
| results | 1 | 1 | 0 | 100.0% |
| router | 2 | 0 | 2 | 0.0% |
| rubrics | 7 | 7 | 0 | 100.0% |
| schools | 5 | 5 | 0 | 100.0% |
| skills | 12 | 12 | 0 | 100.0% |
| submissions | 7 | 7 | 0 | 100.0% |
| sync | 10 | 10 | 0 | 100.0% |
| teacher | 4 | 4 | 0 | 100.0% |
| timetable | 9 | 9 | 0 | 100.0% |
| timetable_generation | 6 | 6 | 0 | 100.0% |
| ws | 0 | 0 | 0 | 0.0% |
| TOTAL | 350 | 338 | 11 | 96.6% |

## Partial Endpoints

- `assignments`
  - `POST /api/v1/assignments/{assignment_id}/exercise-pdf` -> frontend uses `GET`

## Uncovered Endpoints

- `ai`
  - `POST /api/v1/writing-attempts`
  - `POST /api/v1/ai/preferences/opt-out`
  - `GET /api/v1/recommendations`
  - `GET /api/v1/events/schema`
- `content`
  - `GET /api/v1/student-work`
  - `GET /api/v1/student-work/class/{class_id}`
- `notifications`
  - `GET /api/v1/notifications/unsubscribe`
  - `GET /api/v1/notifications/email-open`
- `payments`
  - `POST /api/v1/payments/webhook/provider`
- `router`
  - `GET /api/v1/health`
  - `GET /api/v1/readiness`
