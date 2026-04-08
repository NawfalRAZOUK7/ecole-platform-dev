# Web Backend Endpoint Coverage Report

Snapshot date: April 8, 2026

This report compares backend HTTP endpoints defined in `backend/app/api/v1/*.py` against frontend API calls found in `web/src/**/*.service.ts`.

Coverage rules:

- `COVERED`: exact normalized path and HTTP method match
- `PARTIAL`: normalized path exists in frontend, but HTTP method differs
- `UNCOVERED`: no matching frontend call found

Notes:

- Only decorated backend HTTP routes were counted.
- `api.list(...)` in frontend services is treated as `GET`.
- Path variables are normalized, for example `/users/{id}` and `/users/{user_id}` are treated as the same path shape.
- Partial endpoints are not counted as covered in the coverage percentage.

## Summary

- Total backend endpoints: `348`
- Covered: `283`
- Partial: `13`
- Uncovered: `52`
- Coverage: `81.3%`

## Module Coverage

| Backend Module | Total | Covered | Uncovered | Coverage % |
|---|---:|---:|---:|---:|
| activities | 3 | 3 | 0 | 100.0% |
| admin | 15 | 12 | 3 | 80.0% |
| ai | 5 | 1 | 4 | 20.0% |
| analytics | 5 | 5 | 0 | 100.0% |
| announcements | 4 | 4 | 0 | 100.0% |
| assessments | 4 | 3 | 1 | 75.0% |
| assignments | 4 | 3 | 0 | 75.0% |
| attendance | 5 | 5 | 0 | 100.0% |
| attendance_analytics | 5 | 4 | 1 | 80.0% |
| auth | 14 | 13 | 1 | 92.9% |
| billing | 14 | 14 | 0 | 100.0% |
| budgets | 17 | 12 | 3 | 70.6% |
| class_assignments | 1 | 0 | 1 | 0.0% |
| classes | 1 | 0 | 1 | 0.0% |
| cms | 6 | 6 | 0 | 100.0% |
| compliance | 12 | 11 | 1 | 91.7% |
| consents | 2 | 2 | 0 | 100.0% |
| content | 7 | 4 | 3 | 57.1% |
| content_library | 6 | 6 | 0 | 100.0% |
| courses | 2 | 2 | 0 | 100.0% |
| devices | 3 | 2 | 1 | 66.7% |
| documents | 24 | 18 | 1 | 75.0% |
| enrollments | 2 | 1 | 0 | 50.0% |
| events | 15 | 15 | 0 | 100.0% |
| exports | 2 | 0 | 2 | 0.0% |
| features | 6 | 6 | 0 | 100.0% |
| feed | 1 | 1 | 0 | 100.0% |
| financial_health | 12 | 10 | 2 | 83.3% |
| gdpr | 3 | 3 | 0 | 100.0% |
| gradebook | 5 | 5 | 0 | 100.0% |
| invitations | 3 | 3 | 0 | 100.0% |
| invoices | 2 | 2 | 0 | 100.0% |
| messaging | 7 | 6 | 1 | 85.7% |
| micro_school | 15 | 15 | 0 | 100.0% |
| notifications | 13 | 7 | 5 | 53.8% |
| payments | 4 | 3 | 1 | 75.0% |
| profiles | 4 | 4 | 0 | 100.0% |
| progress | 4 | 2 | 2 | 50.0% |
| question_bank | 5 | 5 | 0 | 100.0% |
| quizzes | 10 | 10 | 0 | 100.0% |
| recovery | 3 | 3 | 0 | 100.0% |
| reports | 10 | 3 | 7 | 30.0% |
| results | 1 | 1 | 0 | 100.0% |
| router | 2 | 0 | 2 | 0.0% |
| rubrics | 7 | 7 | 0 | 100.0% |
| schools | 5 | 2 | 2 | 40.0% |
| skills | 12 | 12 | 0 | 100.0% |
| submissions | 7 | 3 | 4 | 42.9% |
| sync | 10 | 10 | 0 | 100.0% |
| teacher | 4 | 4 | 0 | 100.0% |
| timetable | 9 | 4 | 3 | 44.4% |
| timetable_generation | 6 | 6 | 0 | 100.0% |
| ws | 0 | 0 | 0 | 0.0% |
| TOTAL | 348 | 283 | 52 | 81.3% |

## Partial Endpoints

- `assignments`
  - `POST /api/v1/assignments/{assignment_id}/exercise-pdf` -> frontend uses `GET`
- `budgets`
  - `GET /api/v1/budgets/allocations/{allocation_id}` -> frontend uses `PUT`
  - `GET /api/v1/budgets/allocations/{allocation_id}/requests` -> frontend uses `POST`
- `documents`
  - `GET /api/v1/documents/{document_id}` -> frontend uses `DELETE`
  - `POST /api/v1/students/{student_id}/documents` -> frontend uses `GET`
  - `POST /api/v1/resources` -> frontend uses `GET`
  - `PUT /api/v1/resources/{resource_id}` -> frontend uses `GET`
  - `DELETE /api/v1/resources/{resource_id}` -> frontend uses `GET`
- `enrollments`
  - `POST /api/v1/enrollments` -> frontend uses `GET`
- `notifications`
  - `PUT /api/v1/notifications/preferences` -> frontend uses `GET` and `POST`
- `schools`
  - `DELETE /api/v1/schools/{school_id}` -> frontend uses `GET` and `PATCH`
- `timetable`
  - `GET /api/v1/timetable/slots` -> frontend uses `POST`
  - `GET /api/v1/timetable/exceptions` -> frontend uses `POST`

## Uncovered Endpoints

- `admin`
  - `POST /api/v1/admin/impersonate/{user_id}`
  - `POST /api/v1/admin/stop-impersonation`
  - `GET /api/v1/admin/users/{user_id}/login-history`
- `ai`
  - `POST /api/v1/writing-attempts`
  - `POST /api/v1/ai/preferences/opt-out`
  - `GET /api/v1/recommendations`
  - `GET /api/v1/events/schema`
- `assessments`
  - `POST /api/v1/assessments/{assessment_id}/results`
- `attendance_analytics`
  - `POST /api/v1/analytics/attendance/check-thresholds`
- `auth`
  - `POST /api/v1/auth/2fa/verify`
- `budgets`
  - `GET /api/v1/budgets/requests/{request_id}`
  - `POST /api/v1/budgets/allocations/{allocation_id}/transactions`
  - `GET /api/v1/budgets/allocations/{allocation_id}/transactions`
- `class_assignments`
  - `POST /api/v1/class-assignments`
- `classes`
  - `GET /api/v1/classes/{class_id}`
- `compliance`
  - `GET /api/v1/compliance/reports/{report_id}/download`
- `content`
  - `GET /api/v1/content-items/{content_item_id}/stream`
  - `GET /api/v1/content-items/{content_item_id}/assets/{asset_id}`
  - `DELETE /api/v1/content-items/{content_item_id}/assets/{asset_id}`
- `devices`
  - `POST /api/v1/devices/register`
- `documents`
  - `POST /api/v1/documents/upload`
- `exports`
  - `GET /api/v1/export/csv`
  - `GET /api/v1/export/xlsx`
- `financial_health`
  - `GET /api/v1/financial-health/export/csv`
  - `GET /api/v1/financial-health/export/pdf`
- `messaging`
  - `GET /api/v1/messages/search`
- `notifications`
  - `GET /api/v1/notifications/unread-count`
  - `POST /api/v1/notifications/batch`
  - `DELETE /api/v1/notifications/{notification_id}`
  - `GET /api/v1/notifications/unsubscribe`
  - `GET /api/v1/notifications/email-open`
- `payments`
  - `POST /api/v1/payments/webhook/provider`
- `progress`
  - `GET /api/v1/progress/student/{student_id}`
  - `GET /api/v1/progress/me`
- `reports`
  - `POST /api/v1/reports/schedules`
  - `GET /api/v1/reports/schedules`
  - `PUT /api/v1/reports/schedules/{schedule_id}`
  - `DELETE /api/v1/reports/schedules/{schedule_id}`
  - `POST /api/v1/reports/schedules/{schedule_id}/run`
  - `GET /api/v1/reports/{job_id}/status`
  - `GET /api/v1/reports/{job_id}/download`
- `router`
  - `GET /api/v1/health`
  - `GET /api/v1/readiness`
- `schools`
  - `POST /api/v1/schools`
  - `GET /api/v1/schools`
- `submissions`
  - `POST /api/v1/submissions/{submission_id}/override-penalty`
  - `POST /api/v1/submissions/{submission_id}/files`
  - `GET /api/v1/submissions/{submission_id}/files/{file_id}`
  - `GET /api/v1/submissions/{submission_id}/preview`
- `timetable`
  - `GET /api/v1/timetable/class/{class_id}/weekly`
  - `GET /api/v1/timetable/teacher/{teacher_id}/weekly`
  - `GET /api/v1/timetable/me/weekly`
