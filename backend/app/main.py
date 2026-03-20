"""École Platform — FastAPI Application Entry Point.

Modular monolith backend serving the École Platform API.
Architecture: Router → Service → Repository (Pack D2)
Security pipeline: AuthN → Context → RBAC → ABAC → INV → Audit → Events (Pack D6)
Phase 3A: OpenAPI tags, endpoint descriptions, spec export, Redoc page.
Phase 3C: WebSocket real-time notifications with Redis Pub/Sub.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.idempotency import IdempotencyMiddleware
from app.core.metrics import register_metrics
from app.core.middleware import register_middleware
from app.core.rate_limit import RateLimitMiddleware
from app.core.ws_manager import ws_manager

# ---------------------------------------------------------------------------
# OpenAPI tag metadata — groups endpoints by domain (Phase 3A)
# ---------------------------------------------------------------------------
OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": "Authentication — login, refresh, logout, profile, 2FA, email verification.",
    },
    {
        "name": "invitations",
        "description": "Invitation codes — create, consume, and revoke codes for user onboarding.",
    },
    {
        "name": "recovery",
        "description": "Account recovery — request OTP, verify, and reset password.",
    },
    {
        "name": "erp-classes",
        "description": "ERP — School classes: read class details, capacity, academic year.",
    },
    {
        "name": "erp-enrollments",
        "description": "ERP — Student enrollments: assign students to classes.",
    },
    {
        "name": "erp-class-assignments",
        "description": "ERP — Teacher assignments: assign teachers to classes.",
    },
    {
        "name": "erp-attendance",
        "description": "ERP — Attendance: mark sessions, absence justifications, reviews.",
    },
    {
        "name": "lms-courses",
        "description": "LMS — Courses: create and list courses (teacher/admin).",
    },
    {
        "name": "lms-assignments",
        "description": "LMS — Assignments: create and list homework assignments.",
    },
    {
        "name": "lms-submissions",
        "description": "LMS — Submissions: student work submissions and teacher grading.",
    },
    {
        "name": "lms-results",
        "description": "LMS — Results: student grades and academic results.",
    },
    {
        "name": "lms-content",
        "description": "LMS — Content: learning materials, assets, and progress tracking.",
    },
    {
        "name": "lms-activities",
        "description": "LMS — Activities: interactive learning sessions and completion.",
    },
    {
        "name": "lms-assessments",
        "description": "LMS — Assessments: exams, quizzes, publishing, and result submission.",
    },
    {
        "name": "billing-invoices",
        "description": "Billing — Invoices: list and view school fee invoices.",
    },
    {
        "name": "billing-payments",
        "description": "Billing — Payments: initiate payments, status, provider webhooks.",
    },
    {
        "name": "com-notifications",
        "description": "COM — Notifications: in-app notification feed.",
    },
    {
        "name": "com-consents",
        "description": "COM — Consents: manage communication and data-sharing preferences.",
    },
    {
        "name": "com-feed",
        "description": "COM — Parent feed: aggregated activity feed for parents.",
    },
    {
        "name": "ai",
        "description": "AI & Data — Writing assistance, recommendations, KPIs, event schema.",
    },
    {
        "name": "websocket",
        "description": "WebSocket — Real-time event delivery for connected clients.",
    },
    {
        "name": "system",
        "description": "System — Health check, version, and operational endpoints.",
    },
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # Startup: initialize WebSocket manager with Redis Pub/Sub
    await ws_manager.startup()
    yield
    # Shutdown: close all WebSocket connections and Redis Pub/Sub
    await ws_manager.shutdown()


app = FastAPI(
    title="École Platform API",
    lifespan=lifespan,
    description=(
        "EdTech SaaS platform API for K-12 schools in Morocco.\n\n"
        "## Domains\n"
        "- **IAM** — Authentication, authorization, invitations, recovery, 2FA\n"
        "- **ERP** — Classes, enrollments, teacher assignments, attendance\n"
        "- **LMS** — Courses, assignments, submissions, results, content, activities, assessments\n"
        "- **Billing** — Invoices and payments\n"
        "- **COM** — Notifications, consents, parent feed\n"
        "- **AI** — Writing assistance, recommendations, KPIs\n\n"
        "## Authentication\n"
        "All protected endpoints require a `Bearer` access token in the `Authorization` header.\n"
        "Tokens are obtained via `POST /auth/login`."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=OPENAPI_TAGS,
)

# Register Prometheus metrics middleware and /metrics endpoint (S-128, F2)
register_metrics(app)

# Register middleware and exception handlers (S-039, S-069, S-070)
# Must be registered BEFORE CORS middleware so CorrelationIdMiddleware wraps everything
register_middleware(app)

# Idempotency-Key middleware for POST/PUT/PATCH (S-070)
app.add_middleware(IdempotencyMiddleware)

# Rate limiting middleware — X-RateLimit headers + per-endpoint categories (Phase 2A)
app.add_middleware(RateLimitMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Correlation-Id",
        "X-Request-Id",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)

# Mount API v1 router
app.include_router(v1_router, prefix="/api/v1")
