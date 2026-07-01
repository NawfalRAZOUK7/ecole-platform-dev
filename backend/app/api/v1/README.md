# api/v1/ — REST API v1 Implementation

Production REST API endpoints for the École Platform. Version 1 (v1) serves all client applications. Routes are organized by business domain with complete OpenAPI documentation.

## Overview

- **60+ endpoint files** organized by bounded context
- **Public + Authenticated routes** for different user roles
- **OpenAPI 3.0 specification** with Swagger & ReDoc UIs
- **Real-time WebSocket support** for live notifications
- **Full RBAC/ABAC authorization** on all protected routes

## Directory Structure

### Core Router Files

| File        | Purpose                | Routes                                                                          |
| ----------- | ---------------------- | ------------------------------------------------------------------------------- |
| `router.py` | Main router aggregator | Imports & combines all sub-routers, health check, readiness probe, Sentry debug |

### auth/ — Authentication (4 files)

| File          | Purpose                  | Routes                                                                        |
| ------------- | ------------------------ | ----------------------------------------------------------------------------- |
| `auth.py`     | Login, JWT, 2FA, profile | `POST /auth/login`, `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` |
| `webauthn.py` | WebAuthn/Passkey         | `POST /auth/webauthn/register`, `POST /auth/webauthn/authenticate`            |
| `oauth.py`    | Social login             | `POST /auth/oauth/{provider}`, `POST /auth/oauth/callback`                    |
| `sms_2fa.py`  | SMS 2FA                  | `POST /auth/2fa/sms/send`, `POST /auth/2fa/sms/verify`                        |

### user/ — User Management (5 files)

| File          | Purpose             | Routes                                                                    |
| ------------- | ------------------- | ------------------------------------------------------------------------- |
| `recovery.py` | Password reset, OTP | `POST /recovery/request`, `POST /recovery/verify`, `POST /recovery/reset` |
| `profiles.py` | User profile access | `GET /profiles/{id}`, `PATCH /profiles/{id}`                              |
| `consents.py` | GDPR consent prefs  | `GET /consents`, `PATCH /consents`                                        |
| `devices.py`  | Device token mgmt   | `POST /devices`, `GET /devices`, `DELETE /devices/{id}`                   |
| `gdpr.py`     | Data privacy        | `POST /gdpr/export`, `POST /gdpr/delete`                                  |

### school/ — School Management (3 files)

| File              | Purpose          | Routes                                                              |
| ----------------- | ---------------- | ------------------------------------------------------------------- |
| `schools.py`      | School CRUD      | `GET /schools`, `POST /schools`, `GET /schools/{id}`                |
| `classes.py`      | Class info (ERP) | `GET /classes`, `GET /classes/{id}`                                 |
| `micro_school.py` | Micro-schools    | `GET /micro-school`, `POST /micro-school`, `GET /micro-school/{id}` |

### lms/ — Learning Management (14 files)

| File                   | Purpose                | Routes                                                                 |
| ---------------------- | ---------------------- | ---------------------------------------------------------------------- |
| `courses.py`           | Course management      | `GET /courses`, `POST /courses`, `GET /courses/{id}`                   |
| `assignments.py`       | Assignment creation    | `GET /assignments`, `POST /assignments`                                |
| `submissions.py`       | Student submissions    | `POST /submissions`, `GET /submissions/{id}`                           |
| `quizzes.py`           | Quiz management        | `GET /quizzes`, `POST /quizzes`, `POST /quizzes/{id}/start`            |
| `content.py`           | Course content & items | `GET /content-items`, `POST /content-items`, `GET /content-items/{id}` |
| `assessments.py`       | Assessments            | `GET /assessments`, `POST /assessments`                                |
| `question_bank.py`     | Question library       | `GET /question-bank`, `POST /question-bank`                            |
| `rubrics.py`           | Grading rubrics        | `GET /rubrics`, `POST /rubrics`                                        |
| `class_assignments.py` | Teacher assignments    | `POST /class-assignments`, `DELETE /class-assignments/{id}`            |
| `enrollments.py`       | Student enrollment     | `POST /enrollments`, `GET /enrollments`                                |
| `levels.py`            | Level-age mappings     | `GET /levels`, `POST /levels`                                          |
| `programs.py`          | Academic programs      | `GET /programs`, `POST /programs`                                      |
| `eligibility.py`       | Eligibility rules      | `GET /eligibility-rules`, `POST /eligibility/check`                    |
| `shared_review.py`     | Parent shared review   | `GET /shared-review`, `POST /shared-review/comments`                   |

### academic/ — Academic Operations (9 files)

| File                      | Purpose                  | Routes                                                |
| ------------------------- | ------------------------ | ----------------------------------------------------- |
| `attendance.py`           | Attendance tracking      | `POST /attendance`, `GET /attendance/{student_id}`    |
| `attendance_analytics.py` | Attendance reports       | `GET /attendance/analytics`, `GET /attendance/alerts` |
| `gradebook.py`            | Grade entry & viewing    | `GET /gradebook`, `POST /gradebook/{id}`              |
| `results.py`              | Quiz results             | `GET /results`                                        |
| `progress.py`             | Student progress         | `GET /progress`, `GET /progress/{student_id}`         |
| `skills.py`               | Skill passport           | `GET /skills`, `POST /skills`                         |
| `timetable.py`            | Timetable mgmt           | `GET /timetable`, `POST /timetable/slots`             |
| `timetable_generation.py` | Timetable generation     | `POST /timetable/generate`                            |
| `teacher.py`              | Teacher functions        | `GET /teacher/classes`, `GET /teacher/students`       |
| `student_academic.py`     | Student academic history | `GET /students/{id}/academic-history`                 |

### billing/ — Billing & Finance (4 files)

| File          | Purpose                   | Routes                                     |
| ------------- | ------------------------- | ------------------------------------------ |
| `billing.py`  | Fee structures & policies | `GET /billing/fees`, `POST /billing/fees`  |
| `invoices.py` | Invoice listing           | `GET /invoices`, `GET /invoices/{id}`      |
| `payments.py` | Payment processing        | `POST /payments`, `POST /payments/webhook` |
| `budgets.py`  | Micro-budgets             | `GET /budgets`, `POST /budgets`            |

### communication/ — Communication (2 files)

| File               | Purpose                  | Routes                                           |
| ------------------ | ------------------------ | ------------------------------------------------ |
| `messaging.py`     | Messages & conversations | `GET /messages`, `POST /messages`                |
| `notifications.py` | Notification mgmt        | `GET /notifications`, `POST /notifications/read` |

### content/ — Content & Documents (7 files)

| File                 | Purpose              | Routes                                          |
| -------------------- | -------------------- | ----------------------------------------------- |
| `cms.py`             | Content management   | `GET /cms/pages`, `POST /cms/pages`             |
| `content_library.py` | Reusable content     | `GET /content-library`, `POST /content-library` |
| `documents.py`       | Document mgmt        | `GET /documents`, `POST /documents`             |
| `exports.py`         | Data export          | `POST /exports`, `GET /exports/{id}`            |
| `feed.py`            | Parent activity feed | `GET /feed`                                     |
| `snapshots.py`       | Academic snapshots   | `GET /snapshots`, `POST /snapshots`             |
| `uploads.py`         | Direct uploads       | `POST /uploads/init`, `POST /uploads/complete`  |

### admin/ — Administration (6 files)

| File               | Purpose              | Routes                                        |
| ------------------ | -------------------- | --------------------------------------------- |
| `admin.py`         | Admin operations     | `GET /admin/users`, `POST /admin/roles`       |
| `invitations.py`   | Invite code mgmt     | `POST /invites`, `DELETE /invites/{id}`       |
| `announcements.py` | School announcements | `GET /announcements`, `POST /announcements`   |
| `features.py`      | Feature flags        | `GET /features`, `POST /features/{id}/toggle` |
| `compliance.py`    | MEN compliance       | `GET /compliance`, `POST /compliance`         |
| `events.py`        | Calendar events      | `GET /events`, `POST /events`                 |

### ai/ — AI & Gamification (4 files)

| File            | Purpose           | Routes                                      |
| --------------- | ----------------- | ------------------------------------------- |
| `ai.py`         | AI assistant      | `POST /ai/ask`, `POST /ai/generate`         |
| `activities.py` | Activity tracking | `GET /activities`, `POST /activities`       |
| `games.py`      | Mobile games      | `GET /games/configs`, `POST /games/configs` |
| `rewards.py`    | Student rewards   | `GET /rewards/me`, `POST /rewards/award`    |

### reports/ — Reporting & Analytics (4 files)

| File                      | Purpose              | Routes                                           |
| ------------------------- | -------------------- | ------------------------------------------------ |
| `reports.py`              | Report generation    | `POST /reports`, `GET /reports/{id}`             |
| `analytics.py`            | KPI dashboards       | `GET /analytics/dashboard`, `GET /analytics/kpi` |
| `attendance_analytics.py` | Attendance analytics | `GET /analytics/attendance`                      |
| `financial_health.py`     | Financial health     | `GET /financial-health`                          |

### sync/ — Offline Sync (1 file)

| File      | Purpose      | Routes                                                      |
| --------- | ------------ | ----------------------------------------------------------- |
| `sync.py` | Offline sync | `POST /sync/register`, `POST /sync/push`, `POST /sync/pull` |

### Real-time (1 file)

| File    | Purpose                | Routes   |
| ------- | ---------------------- | -------- |
| `ws.py` | WebSocket live updates | `WS /ws` |

## Request/Response Format

### Authentication Header

```
Authorization: Bearer <JWT_TOKEN>
```

### Success Response (2xx)

```json
{
  "success": true,
  "data": { "id": 1, "name": "John Doe" },
  "message": "Operation successful"
}
```

### Error Response (4xx/5xx)

```json
{
  "success": false,
  "error": "PERMISSION_DENIED",
  "message": "User lacks permission to access this resource",
  "details": { "required_permission": "PERM-LMS:course:edit" }
}
```

## Common Query Parameters

| Param    | Type | Example                 | Notes                                 |
| -------- | ---- | ----------------------- | ------------------------------------- |
| `limit`  | int  | `?limit=10`             | Records per page (default: 20)        |
| `offset` | int  | `?offset=20`            | Pagination offset                     |
| `sort`   | str  | `?sort=created_at`      | Sort field (prefix with `-` for desc) |
| `filter` | str  | `?filter=status:active` | Filter criteria                       |
| `search` | str  | `?search=john`          | Full-text search                      |

## OpenAPI Tags

Routes are tagged with OpenAPI categories for discovery:

- `auth` — Authentication & user account
- `erp-classes` — School class management
- `erp-enrollments` — Student enrollment
- `erp-attendance` — Attendance tracking
- `lms-courses` — Course delivery
- `lms-assignments` — Assignment management
- `lms-grading` — Grading & rubrics
- `lms-progress` — Student progress
- `billing-invoices` — Invoice management
- `billing-payments` — Payment processing
- `communication-messages` — Messaging
- `communication-notifications` — Notifications
- `reporting-analytics` — Analytics & KPIs
- `admin` — Administrative operations
- `real-time` — WebSocket connections

## Dependency Injection

All routes use FastAPI `Depends()` for:

- **Current User** — JWT authentication
- **Services** — Business logic instances
- **Permissions** — RBAC/ABAC checks
- **Database** — Async session management

Example:

```python
@router.get("/courses/{course_id}")
async def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(),
):
    # current_user & service injected automatically
    return await service.get_course(course_id, current_user.school_id)
```

## Status Codes

| Code | Meaning        | Example                 |
| ---- | -------------- | ----------------------- |
| 200  | OK             | Request successful      |
| 201  | Created        | Resource created        |
| 204  | No Content     | Success, no body        |
| 400  | Bad Request    | Invalid input           |
| 401  | Unauthorized   | Missing/invalid token   |
| 403  | Forbidden      | Permission denied       |
| 404  | Not Found      | Resource not found      |
| 409  | Conflict       | Business rule violation |
| 422  | Unprocessable  | Validation error        |
| 500  | Internal Error | Server error            |

## WebSocket (ws.py)

Real-time notifications via WebSocket:

- **Endpoint:** `WS /ws/{user_id}`
- **Authentication:** JWT in query param or header
- **Messages:** JSON-encoded notification payloads
- **Reconnection:** Automatic with exponential backoff

Example client:

```javascript
const ws = new WebSocket(`wss://api.ecole.ma/ws/user123?token=${JWT}`);
ws.onmessage = (e) => {
  const notification = JSON.parse(e.data);
  console.log(notification); // { type: "grade_published", ... }
};
```

## Testing Routes

```bash
# Test specific endpoint
pytest tests/api/v1/test_courses.py -v

# Test all auth endpoints
pytest tests/api/v1/test_auth.py -v

# Test RBAC/ABAC matrix
pytest -m "security" tests/api/v1/

# Integration test with real DB
pytest -m "integration" tests/api/v1/
```

## Rate Limiting

All authenticated endpoints have per-user rate limits:

- **Default:** 1000 requests/hour
- **Override:** Via Redis configuration
- **Response header:** `X-RateLimit-Remaining`

See `core/rate_limit.py` for configuration.

## Next Steps

- See `router.py` to understand router aggregation
- See `auth.py` for authentication endpoint patterns
- See `schemas/` for request/response models
- See `services/` for business logic implementation
- See `core/permissions.py` for RBAC/ABAC rules
