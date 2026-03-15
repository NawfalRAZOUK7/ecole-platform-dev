"""École Platform — FastAPI Application Entry Point.

Modular monolith backend serving the École Platform API.
Architecture: Router → Service → Repository (Pack D2)
Security pipeline: AuthN → Context → RBAC → ABAC → INV → Audit → Events (Pack D6)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings
from app.core.middleware import register_middleware

app = FastAPI(
    title="École Platform API",
    description="EdTech platform API for K-12 schools — IAM, ERP, LMS, COM, Billing, IA",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register middleware and exception handlers (S-039, S-069)
# Must be registered BEFORE CORS middleware so CorrelationIdMiddleware wraps everything
register_middleware(app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-Id", "X-Request-Id"],
)

# Mount API v1 router
app.include_router(v1_router, prefix="/api/v1")
