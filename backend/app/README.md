# app/ — Main Application Package

Core application code for the École Platform backend. Implements 3-tier architecture (Router → Service → Repository) with cross-cutting infrastructure and domain-driven design patterns.

## Directory Structure

```
app/
├── main.py              # FastAPI app factory, middleware, OpenAPI configuration
├── seed.py              # Demo data generation (Moroccan test data)
│
├── api/                 # REST API endpoints (Router layer)
│   └── v1/             # API v1 routes (48 endpoint files)
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
├── repositories/      # Data access layer (Repository pattern)
│   ├── base.py        # BaseRepository with CRUD operations
│   ├── auth.py        # User, Session queries
│   ├── school.py      # School, Class, Enrollment queries
│   ├── lms.py         # Course, Assignment, Quiz queries
│   ├── billing.py     # Invoice, Payment queries
│   ├── gradebook.py   # Grade & grading queries
│   ├── messaging.py   # Message queries
│   ├── notifications.py # Notification queries
│   ├── reports.py     # Report queries
│   ├── analytics.py   # Analytics & KPI queries
│   └── (24 more)      # Domain-specific repositories
│
├── schemas/           # Pydantic v2 request/response models
│   ├── auth.py        # LoginRequest, TokenResponse, UserProfile
│   ├── school.py      # SchoolInput, ClassInput, EnrollmentResponse
│   ├── lms.py         # CourseInput, AssignmentResponse, etc.
│   ├── billing.py     # InvoiceResponse, PaymentRequest, etc.
│   ├── gradebook.py   # GradeInput, GradeResponse, etc.
│   └── (20 more)      # Domain-specific schemas
│
├── services/          # Business logic layer (Service pattern)
│   ├── auth.py        # Authentication, JWT refresh, account mgmt
│   ├── school.py      # School operations, enrollment logic
│   ├── billing.py     # Invoicing, payment processing, subscriptions
│   ├── gradebook.py   # Grade calculation, reporting
│   ├── analytics.py   # KPI computation, dashboards
│   ├── communication.py # Message coordination
│   ├── email.py       # Email composition & sending
│   ├── sms.py         # SMS delivery
│   ├── calendar.py    # Event scheduling, RSVP logic
│   ├── reports.py     # Report generation & export
│   ├── gdpr.py        # Data export, deletion, compliance
│   ├── ai/            # AI provider strategy pattern
│   ├── delivery/      # Notification delivery channels
│   ├── lms/           # Learning management system services
│   └── (25 more)      # Domain-specific services
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
| **API** | OpenAPI + FastAPI | `api/v1/*.py` |
| **Service** | Domain-driven design | `services/*.py` |
| **Repository** | Data mapper + Unit of Work | `repositories/*.py` |
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
