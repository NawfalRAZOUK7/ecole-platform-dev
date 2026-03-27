"""Prometheus metrics exporter — golden signals per F2 catalog.

Reference: S-128 — Prometheus metrics exporter, Pack F2 — Observability & SLO
Exports: api_request_count, api_request_duration, api_error_rate,
         db_pool_in_use, redis_hit_rate, auth login metrics, webhook metrics.

Metrics endpoint: GET /metrics (public, no auth)
"""

from __future__ import annotations

import time

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# ---------------------------------------------------------------------------
# Custom registry (avoids default process/platform collectors for cleaner output)
# ---------------------------------------------------------------------------
REGISTRY = CollectorRegistry()

# ---------------------------------------------------------------------------
# Application Info
# ---------------------------------------------------------------------------
APP_INFO = Info(
    "ecole_platform",
    "École Platform application metadata",
    registry=REGISTRY,
)
APP_INFO.info(
    {
        "version": "0.1.0",
        "service": "api-backend",
    }
)

# ---------------------------------------------------------------------------
# Golden Signal 1: Request Count (throughput)
# ---------------------------------------------------------------------------
REQUEST_COUNT = Counter(
    "api_request_count",
    "Total number of API requests",
    ["env", "service", "method", "path", "status"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Golden Signal 2: Request Duration / Latency
# ---------------------------------------------------------------------------
REQUEST_DURATION = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["env", "service", "method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Golden Signal 3: Error Count
# ---------------------------------------------------------------------------
ERROR_COUNT = Counter(
    "api_error_count",
    "Total number of API errors (4xx and 5xx)",
    ["env", "service", "method", "path", "status", "error_category"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Auth Metrics
# ---------------------------------------------------------------------------
AUTH_LOGIN_COUNT = Counter(
    "auth_login_count",
    "Login attempts",
    ["env", "status"],  # status: success, failure
    registry=REGISTRY,
)

AUTH_TOKEN_REFRESH_COUNT = Counter(
    "auth_token_refresh_count",
    "Token refresh attempts",
    ["env", "status"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Database Pool Metrics (updated via periodic probe)
# ---------------------------------------------------------------------------
DB_POOL_SIZE = Gauge(
    "db_pool_size",
    "Total database connection pool size",
    ["env", "service"],
    registry=REGISTRY,
)

DB_POOL_IN_USE = Gauge(
    "db_pool_in_use",
    "Number of database connections currently in use",
    ["env", "service"],
    registry=REGISTRY,
)

DB_POOL_OVERFLOW = Gauge(
    "db_pool_overflow",
    "Number of overflow database connections currently in use",
    ["env", "service"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Redis Metrics
# ---------------------------------------------------------------------------
REDIS_COMMANDS_COUNT = Counter(
    "redis_commands_count",
    "Redis command count",
    ["env", "service", "command"],
    registry=REGISTRY,
)

REDIS_HIT_COUNT = Counter(
    "redis_hit_count",
    "Redis cache hit count",
    ["env", "service"],
    registry=REGISTRY,
)

REDIS_MISS_COUNT = Counter(
    "redis_miss_count",
    "Redis cache miss count",
    ["env", "service"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Webhook Metrics
# ---------------------------------------------------------------------------
WEBHOOK_COUNT = Counter(
    "webhook_received_count",
    "Webhook events received",
    ["env", "provider", "status"],
    registry=REGISTRY,
)

WEBHOOK_SIGNATURE_FAILURES = Counter(
    "webhook_signature_failures",
    "Webhook signature verification failures",
    ["env", "provider"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Billing Metrics
# ---------------------------------------------------------------------------
PAYMENT_INITIATED_COUNT = Counter(
    "payment_initiated_count",
    "Payment initiation attempts",
    ["env", "status"],
    registry=REGISTRY,
)

PAYMENT_COMPLETED_COUNT = Counter(
    "payment_completed_count",
    "Payments completed (paid/failed/canceled)",
    ["env", "outcome"],  # outcome: paid, failed, canceled
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Backup / Operational Metrics
# ---------------------------------------------------------------------------
BACKUP_JOB_SUCCESS = Counter(
    "backup_job_success_count",
    "Successful backup jobs",
    ["env", "asset"],
    registry=REGISTRY,
)

BACKUP_JOB_FAILURE = Counter(
    "backup_job_failure_count",
    "Failed backup jobs",
    ["env", "asset"],
    registry=REGISTRY,
)

LAST_BACKUP_TIMESTAMP = Gauge(
    "last_successful_backup_timestamp",
    "Unix timestamp of last successful backup",
    ["env", "asset"],
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Background Task Metrics (Phase 3E)
# ---------------------------------------------------------------------------
TASK_ENQUEUED_COUNT = Counter(
    "task_enqueued_total",
    "Total tasks enqueued",
    ["env", "task"],
    registry=REGISTRY,
)

TASK_COMPLETED_COUNT = Counter(
    "task_completed_total",
    "Total tasks completed successfully",
    ["env", "task"],
    registry=REGISTRY,
)

TASK_FAILED_COUNT = Counter(
    "task_failed_total",
    "Total tasks that failed",
    ["env", "task"],
    registry=REGISTRY,
)

TASK_DURATION = Histogram(
    "task_duration_seconds",
    "Background task execution duration in seconds",
    ["env", "task"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Report Generation Metrics (Phase 14)
# ---------------------------------------------------------------------------
REPORT_GENERATION_COUNT = Counter(
    "report_generation_count",
    "Total report generation attempts",
    ["env", "report_type", "status"],
    registry=REGISTRY,
)

REPORT_GENERATION_DURATION = Histogram(
    "report_generation_duration_seconds",
    "Report generation duration in seconds",
    ["env", "report_type"],
    buckets=(0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
    registry=REGISTRY,
)

# ---------------------------------------------------------------------------
# Document storage metrics (Phase 16)
# ---------------------------------------------------------------------------
DOCUMENT_UPLOAD_COUNT = Counter(
    "upload_count",
    "Total document uploads accepted by the backend",
    ["env", "mime_type", "deduplicated"],
    registry=REGISTRY,
)

DOCUMENT_UPLOAD_SIZE_BYTES = Counter(
    "upload_size_bytes",
    "Total uploaded document size in bytes",
    ["env", "mime_type"],
    registry=REGISTRY,
)

DOCUMENT_STORAGE_TOTAL_BYTES = Gauge(
    "storage_total_bytes",
    "Current total stored document bytes tracked by the API",
    ["env"],
    registry=REGISTRY,
)


class _CollectorNameProxy:
    """Expose a stable public metric name without mutating the registered collector."""

    def __init__(self, collector, public_name: str) -> None:
        self._collector = collector
        self._name = public_name

    def labels(self, *args, **kwargs):
        return self._collector.labels(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(self._collector, name)


TASK_ENQUEUED_COUNT = _CollectorNameProxy(TASK_ENQUEUED_COUNT, "task_enqueued_total")


# ---------------------------------------------------------------------------
# Helper: normalize path to avoid cardinality explosion
# ---------------------------------------------------------------------------
def _normalize_path(path: str) -> str:
    """Collapse UUID path segments to {id} to limit label cardinality."""
    import re

    # Replace UUID-like segments
    path = re.sub(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        "{id}",
        path,
    )
    # Replace numeric-only segments
    path = re.sub(r"/\d+", "/{id}", path)
    return path


# ---------------------------------------------------------------------------
# Middleware: auto-instrument all API requests
# ---------------------------------------------------------------------------
class PrometheusMiddleware(BaseHTTPMiddleware):
    """Auto-instruments all API requests with golden signal metrics."""

    def __init__(self, app: FastAPI, env: str = "development") -> None:
        super().__init__(app)
        self.env = env
        self.service = "api-backend"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip /metrics and /docs endpoints
        if request.url.path in ("/metrics", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        method = request.method
        path = _normalize_path(request.url.path)
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start
        status = str(response.status_code)

        # Record request count
        REQUEST_COUNT.labels(
            env=self.env,
            service=self.service,
            method=method,
            path=path,
            status=status,
        ).inc()

        # Record latency
        REQUEST_DURATION.labels(
            env=self.env,
            service=self.service,
            method=method,
            path=path,
        ).observe(duration)

        # Record errors (4xx, 5xx)
        if response.status_code >= 400:
            category = "client" if response.status_code < 500 else "server"
            ERROR_COUNT.labels(
                env=self.env,
                service=self.service,
                method=method,
                path=path,
                status=status,
                error_category=category,
            ).inc()

        return response


# ---------------------------------------------------------------------------
# DB pool metrics collector
# ---------------------------------------------------------------------------
def collect_db_pool_metrics(engine, env: str = "development") -> None:
    """Collect database connection pool metrics from the SQLAlchemy engine."""
    service = "api-backend"
    pool = engine.pool
    DB_POOL_SIZE.labels(env=env, service=service).set(pool.size())
    DB_POOL_IN_USE.labels(env=env, service=service).set(pool.checkedout())
    DB_POOL_OVERFLOW.labels(env=env, service=service).set(pool.overflow())


# ---------------------------------------------------------------------------
# /metrics endpoint handler
# ---------------------------------------------------------------------------
async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    # Collect DB pool metrics on each scrape
    from app.core.database import engine as db_engine
    from app.core.config import settings

    try:
        collect_db_pool_metrics(db_engine.sync_engine, env=settings.app_env)
    except Exception:
        pass  # Don't fail metrics if pool inspection fails

    body = generate_latest(REGISTRY)
    return Response(content=body, media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------
def register_metrics(app: FastAPI) -> None:
    """Register Prometheus middleware and /metrics endpoint on the FastAPI app."""
    from app.core.config import settings

    app.add_middleware(PrometheusMiddleware, env=settings.app_env)
    app.add_route("/metrics", metrics_endpoint, methods=["GET"])
