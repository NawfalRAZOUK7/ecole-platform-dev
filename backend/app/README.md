# app/ — Main Application Package

Core application code for the École Platform backend. Implements 3-tier architecture (Router → Service → Repository) with cross-cutting infrastructure and domain-driven design patterns.

## Directory Structure

```
app/
├── main.py              # FastAPI app factory, middleware, OpenAPI configuration
├── seed.py              # Demo data generation (Moroccan test data)
│
├── api/                 # REST API endpoints (Router layer)
│   └── v1/             # API v1 routes grouped by bounded context (auth, user, school, lms, …)
│
├── core/               # Cross-cutting infrastructure
│   ├── config.py       # Pydantic settings, environment config
│   ├── database.py     # Async SQLAlchemy engine & session factory
│   ├── security.py     # JWT, password hashing, authentication
│   ├── permissions.py  # 166 permission constants (PERM-* codes)
│   ├── abac.py         # Attribute-based access control rules
│   ├── middleware.py   # Request logging, CORS, error handling
│   ├── rate_limit.py   # Per-user rate limiting via Redis
│   ├── redis.py        # Redis client & connection pool
│   ├── metrics.py      # Prometheus metrics, monitoring
│   ├── telemetry.py    # OpenTelemetry tracing
│   ├── exceptions.py   # Structured error definitions
│   ├── dependencies.py # FastAPI dependency injection
│   ├── response.py     # Standardized JSON responses
│   ├── storage.py      # File upload/download handling
│   ├── tasks.py        # Background task queue (arq)
│   ├── totp.py         # 2FA time-based one-time passwords
│   ├── password_policy.py  # Password validation rules
│   ├── idempotency.py  # Idempotent request handling
│   ├── feature_flags.py # Feature flag toggling
│   ├── unit_of_work.py # Transaction management pattern
│   ├── ws_manager.py   # WebSocket connection management
│   ├── db_routing.py   # Read replica routing strategy
│   ├── filtering.py    # Query filter builders
│   ├── search.py       # Full-text search implementation
│   └── business_metrics.py # KPI & analytics metrics
│
├── domain/            # Domain-driven design layer
│   ├── events/        # Domain events (event sourcing)
│   ├── protocols/     # Structural typing contracts
│   └── value_objects/ # Immutable value objects
│
├── data/              # Static reference data
│   └── common_passwords.txt  # Password policy blacklist
│
├── models/            # SQLAlchemy 2.0 ORM models
│   ├── iam.py         # User, Role, Permission, Session
│   ├── school.py      # School, Class, AcademicYear
│   ├── lms.py         # Course, Assignment, Quiz, Grade
│   ├── billing.py     # Invoice, Payment, Subscription
│   ├── calendar.py    # Event, RSVP
│   ├── com.py         # Message, Notification
│   ├── documents.py   # Document, StudentFile
│   ├── erp.py         # Timetable, Resource, Enrollment
│   ├── audit.py       # AuditLog
│   ├── ai.py          # AIInteraction
│   ├── reporting.py   # Report, ReportSchedule
│   └── feature.py     # FeatureFlag
│
├── repositories/      # Data access (flat modules; domain-prefixed names where helpful)
│   ├── base.py
│   ├── auth.py, school.py, lms.py, billing.py, erp.py, …
│   ├── lms_quiz.py, lms_question_bank.py, lms_rubric.py
│   ├── communication_calendar.py, communication_messaging.py, communication_notifications.py
│   ├── content_documents.py, content_cms.py
│   ├── academic_*.py  # gradebook, progress, attendance analytics, timetable, skill_passport
│   ├── reports_*.py, ai_games.py, ai_rewards.py, user_*.py, admin_*.py, …
│   └── README.md
│
├── schemas/           # Pydantic v2 models (packages mirror API domains)
│   ├── auth/          # IAM / login / tokens
│   ├── user/          # profile.py
│   ├── school/        # school + micro_school
│   ├── academic/      # erp, programs, gradebook, attendance analytics, timetable, skills
│   ├── lms/           # courses/assignments + quiz, question_bank, rubric, levels, student_work
│   ├── billing/       # invoices/fees + enhancements.py, budget.py
│   ├── content/       # cms, documents, uploads, storage, resources
│   ├── communication/  # com (init), notifications, calendar
│   ├── reports/       # reports (init), report_schedule, analytics, financial_health
│   ├── admin/         # men_compliance, feature
│   ├── ai/            # ai (init), games, rewards
│   ├── sync/          # sync_queue
│   └── README.md
│
├── services/          # Business logic (domain packages; avoid orphan modules at root)
│   ├── platform/      # audit, suspicious activity
│   ├── admin/         # admin dashboard, compliance, feature flags
│   ├── user/          # GDPR, profile_loader
│   ├── sync/          # offline sync queue
│   ├── auth/          # authentication, email, webauthn, oauth, 2FA, profile
│   ├── school/        # school + micro-school
│   ├── academic/      # ERP orchestration (erp), attendance, timetable, gradebook, skills, …
│   ├── lms/           # courses, assignments, quizzes, question bank, programs, …
│   ├── billing/       # invoices, payments, budgets, retries
│   ├── content/       # CMS, library, documents, uploads, snapshots, file storage
│   ├── communication/ # messaging, notifications, calendar, SMS, digests, realtime
│   ├── reports/       # analytics, dashboards, exports, financial health, transcripts
│   ├── ai/            # LLM providers, games, rewards
│   ├── delivery/      # channel strategies (email, push, in-app, SMS)
│   ├── __init__.py    # selective re-exports for legacy callers/tests
│   └── README.md
│
├── scripts/           # Application scripts
│   └── seed_demo.py   # Generate demo data (Moroccan schools)
│
└── templates/         # Jinja2 HTML templates
    ├── email/         # Email templates (HTML)
    │   ├── base.html              # Email layout
    │   ├── welcome.html           # User registration email
    │   ├── otp.html               # OTP code delivery
    │   ├── grade_published.html   # Grade notification
    │   ├── invoice_reminder.html  # Billing reminder
    │   └── notification_*.html    # Notification digests
    │
    └── reports/       # Report templates (PDF generation)
        ├── base.html              # Report layout
        ├── student_report_card.html
        ├── class_summary.html
        ├── attendance_report.html
        ├── school_analytics.html
        └── billing_statement.html
```

## Key Patterns

| Layer | Pattern | Files |
|-------|---------|-------|
| **API** | OpenAPI + FastAPI | `api/v1/<domain>/*.py` |
| **Service** | Bounded-context packages | `services/<domain>/` |
| **Repository** | Data mapper + Unit of Work | `repositories/*.py` (domain-prefixed modules) |
| **Security** | RBAC/ABAC + AuthN | `core/security.py`, `core/permissions.py`, `core/abac.py` |
| **Async** | SQLAlchemy 2.0 + asyncio | `core/database.py` |
| **Events** | Domain events + decorators | `domain/events/` |
| **Value Objects** | Immutable domain values | `domain/value_objects/` |

## FastAPI Integration

- **Dependency Injection:** `FastAPI.Depends()` wires services, repos, security
- **Middleware Stack:** Auth, rate limiting, logging, error handling
- **OpenAPI Tags:** Organized by domain (auth, lms, billing, etc.)
- **WebSocket:** Real-time notifications via `api/v1/ws.py`
- **Request Tracing:** OpenTelemetry for observability

## Configuration

All settings from `core/config.py` (Pydantic):
- Database URL (PostgreSQL)
- Redis connection
- JWT secrets & expiry
- Email/SMS providers
- Feature flags
- CORS origins

## Testing

```bash
pytest tests/unit/     # Fast unit tests
pytest tests/integration/  # Real database tests
```

See `/tests/` for test structure and fixtures.

## Next Steps

- See `api/v1/` for REST endpoint definitions
- See `services/` for business logic implementation
- See `repositories/` for data access patterns
- See `core/` for infrastructure setup
