# api/ — REST API Layer

HTTP request handlers for the École Platform. Implements the router layer of the 3-tier architecture, converting HTTP requests into service calls with full OpenAPI documentation.

## Structure

```
api/
└── v1/              # API version 1 (current production API)
    ├── router.py    # Main router aggregator (combines all endpoints)
    ├── auth.py      # Authentication & user account endpoints
    ├── schools.py   # School management endpoints
    ├── classes.py   # Class management endpoints
    ├── courses.py   # Course endpoints
    ├── assignments.py    # Assignment endpoints
    ├── quizzes.py   # Quiz endpoints
    ├── gradebook.py # Grade viewing & grading endpoints
    ├── billing.py   # Invoice & payment endpoints
    ├── attendance.py # Attendance tracking endpoints
    ├── messaging.py  # Message endpoints
    ├── notifications.py  # Notification endpoints
    ├── reports.py   # Report generation endpoints
    ├── analytics.py  # Analytics & KPI endpoints
    ├── ai.py        # AI assistant endpoints
    ├── gdpr.py      # Data export & deletion endpoints
    ├── cms.py       # Content management endpoints
    ├── exports.py   # Data export endpoints
    ├── timetable.py # Timetable management endpoints
    ├── ws.py        # WebSocket real-time endpoints
    │
    ├── (48+ route files total)
    │
    ├── admin.py, activities.py, announcements.py
    ├── assessments.py, attendance_analytics.py
    ├── calendar.py, class_assignments.py, cms.py
    ├── consents.py, content.py, content_library.py
    ├── devices.py, documents.py, enrollments.py
    ├── events.py, features.py, feed.py, invitations.py
    ├── invoices.py, payments.py, profiles.py, progress.py
    ├── question_bank.py, recovery.py, results.py, rubrics.py
    ├── submissions.py, teacher.py, timetable_generation.py
    └── (and more domain-specific endpoints)
```

## API Versioning

- **Version 1 (v1/):** Current production API
- Future versions: Add `api/v2/`, `api/v3/` as needed
- Each version is independently deployable

## Route Organization

Routes are organized by **business domain**:

| Domain | Files | Purpose |
|--------|-------|---------|
| **Authentication** | `auth.py`, `recovery.py` | Login, JWT refresh, password reset, 2FA |
| **School Management** | `schools.py`, `classes.py`, `enrollments.py` | School setup, class management, student enrollment |
| **Learning Management** | `courses.py`, `assignments.py`, `quizzes.py`, `progress.py` | Course delivery, assignments, quizzes, student progress |
| **Grading** | `gradebook.py`, `rubrics.py`, `assessments.py` | Grade entry, rubric management, assessment tools |
| **Billing** | `billing.py`, `invoices.py`, `payments.py` | Invoice generation, payment processing |
| **Attendance** | `attendance.py`, `attendance_analytics.py` | Attendance tracking, reports |
| **Communication** | `messaging.py`, `notifications.py` | Messages, notifications, alerts |
| **Reporting** | `reports.py`, `analytics.py` | Report generation, KPI dashboards |
| **Content** | `cms.py`, `content.py`, `content_library.py` | CMS, resource library, documents |
| **Real-time** | `ws.py` | WebSocket connections, live updates |
| **GDPR** | `gdpr.py`, `exports.py` | Data export, deletion, compliance |
| **Admin** | `admin.py`, `features.py` | Admin operations, feature management |

## Request/Response Pattern

Each endpoint:
1. **Validates input** — Pydantic schemas in `schemas/`
2. **Authenticates** — JWT token verification
3. **Authorizes** — RBAC/ABAC permission checks
4. **Calls service** — Business logic from `services/`
5. **Returns response** — Standardized JSON from `core/response.py`

Example:
```python
@router.post("/courses", tags=["lms"], status_code=201)
async def create_course(
    req: CourseInput,
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(),
):
    permission_check(current_user, "PERM-LMS:course:create")
    course = await service.create_course(req, school_id=current_user.school_id)
    return course
```

## OpenAPI Documentation

Routes are tagged with OpenAPI categories for Swagger/Redoc:
- `/docs` — Swagger UI
- `/redoc` — ReDoc UI
- `/openapi.json` — OpenAPI 3.0 specification

Tags defined in `app/main.py`:

```python
OPENAPI_TAGS = [
    {"name": "auth", "description": "Authentication & user account"},
    {"name": "erp-classes", "description": "School class management"},
    {"name": "lms-courses", "description": "Course delivery & content"},
    # ... (50+ tags)
]
```

## Security & Validation

All routes implement:
- **Input Validation** — Pydantic v2 schemas with constraints
- **Authentication** — JWT token verification via `get_current_user()`
- **Authorization** — Permission decorators from `core/permissions.py`
- **Rate Limiting** — Per-user quotas via Redis
- **Audit Logging** — Request/response tracking for compliance
- **CORS** — Cross-origin access control in middleware

## WebSocket Endpoints

Real-time communication:
- **File:** `ws.py`
- **Path:** `/ws/{user_id}`
- **Features:** Live notifications, message delivery, presence
- **Manager:** `core/ws_manager.py` handles connections

## Dependency Injection

Routes use FastAPI `Depends()` for:
- Current authenticated user
- Service layer instances
- Database session
- Rate limit quota
- Permission context

Example:
```python
async def create_assignment(
    req: AssignmentInput,
    current_user: User = Depends(get_current_user),
    service: AssignmentService = Depends(),
):
    # service, current_user injected automatically
```

## Response Format

All responses use standardized format from `core/response.py`:

**Success (2xx):**
```json
{
  "success": true,
  "data": { "id": 1, "name": "..." },
  "message": "Resource created"
}
```

**Error (4xx/5xx):**
```json
{
  "success": false,
  "error": "PERMISSION_DENIED",
  "message": "User lacks permission to perform action",
  "details": { "required_permission": "PERM-LMS:course:edit" }
}
```

## Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| `AUTHENTICATION_REQUIRED` | 401 | Missing or invalid JWT |
| `PERMISSION_DENIED` | 403 | Missing required permission |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource doesn't exist |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `CONFLICT` | 409 | Business rule violation |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

See `core/exceptions.py` for complete error catalog.

## Testing

Routes are tested in `/tests/api/v1/`:
```bash
pytest tests/api/v1/test_courses.py -v
pytest -m "security" tests/api/  # RBAC/ABAC matrix tests
```

## Next Steps

- See `router.py` for how routes are aggregated
- See `auth.py` for authentication endpoint patterns
- See `core/exceptions.py` for error handling
- See `schemas/` for request/response models
