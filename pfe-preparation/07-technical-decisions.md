# Step 7 — Technical Decisions & Engineering Justifications

> Analysis extracted from implemented source code — no documentation files referenced.

---

## 1. Backend Framework: FastAPI

### Decision Evidence

The backend is built on **FastAPI 0.120.4** (`requirements.txt`), a modern Python ASGI framework. This choice is visible in every layer of the codebase.

### Engineering Justification from Code

**Native async/await throughout.** The entire backend is async-first: `create_async_engine` with asyncpg driver (`core/database.py`), `redis.asyncio` for cache (`core/redis.py`), `aiosmtplib` for email, and ARQ for async background tasks (`core/tasks.py`). FastAPI was the only Python framework at the time that natively supported async dependency injection with `Depends()`, which the project uses extensively for its security pipeline:

```
Security pipeline: AuthN → Context → RBAC → ABAC → INV → Audit → Events
```

This pipeline is implemented as a chain of `Depends()` calls in `core/dependencies.py`, where each step is an async function that can query the database or Redis without blocking the event loop.

**Automatic OpenAPI generation.** The `main.py` file defines 26 OpenAPI tag groups (auth, erp-classes, erp-enrollments, lms-courses, billing-invoices, etc.) and exposes both `/docs` (Swagger UI) and `/redoc` endpoints. FastAPI generates the complete OpenAPI schema from Pydantic models and type annotations — this was critical for a multi-client platform (web + mobile) where the API contract must be machine-readable.

**Pydantic-native validation.** The `Settings` class in `core/config.py` extends `pydantic_settings.BaseSettings` with 60+ typed configuration fields, Docker secret file loading via `model_post_init`, and multi-file `.env` resolution. Request/response schemas across all endpoints use Pydantic v2 for automatic validation, serialization, and OpenAPI schema generation.

**Middleware system.** FastAPI's ASGI middleware stack is used for five cross-cutting concerns registered in `main.py`:
- `CorrelationIdMiddleware` — UUID v4 correlation ID propagation via `contextvars` (`core/middleware.py`)
- `IdempotencyMiddleware` — Redis-backed POST/PUT/PATCH response caching with 24h TTL (`core/idempotency.py`)
- `RateLimitMiddleware` — Redis sliding window with 3 categories: auth (5/15min), write (30/min), read (100/min) (`core/rate_limit.py`)
- `PrometheusMiddleware` — Request metrics with UUID path normalization (`core/metrics.py`)
- `CORSMiddleware` — Configured for 7 custom headers including `Idempotency-Key` and `X-Client-Platform`

### Alternatives Considered (Why Not Django/Flask)

Django's ORM is synchronous (Django ORM async was experimental when the project started). The codebase's pervasive use of `async with async_session()`, `await db.execute()`, and async Redis pipelines would require Django Channels for WebSocket support, adding complexity. Flask lacks built-in dependency injection and type-based validation. FastAPI's performance characteristics (Uvicorn ASGI) and native async support made it the clear choice for a real-time platform with WebSocket notifications (`core/ws_manager.py` uses Redis Pub/Sub for horizontal scaling).

---

## 2. Frontend Framework: React 18 + TypeScript + Vite

### Decision Evidence

The web client uses **React 18.3.1** with **TypeScript 5.6**, built with **Vite 6.0** (`web/package.json`, `tsconfig.json`).

### Engineering Justification from Code

**Strict TypeScript configuration.** `tsconfig.json` enables `strict: true`, `noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`, and `noUncheckedSideEffectImports`. This catches an entire class of runtime errors at compile time — critical for a platform with 100+ routes and 10 user roles.

**Feature-first architecture.** The `web/src/` directory is organized as:
- `features/` — Domain-specific modules (auth, admin, teacher, student, billing, attendance, etc.)
- `shared/ui/` — 25+ reusable components (DataTable, FormField, Pagination, ErrorBoundary, etc.)
- `shared/hooks/` — Cross-cutting hooks (useAgeTheme, useNetworkStatus, useQueryDefaults, useFocusManagement)
- `shared/i18n/` — Trilingual system (fr, ar, en)
- `services/` — API client, auth context

**Lazy loading with code splitting.** All 140+ page components are imported via `React.lazy()` in `app/LazyPages.ts` and wrapped in `<Suspense fallback={<LoadingState />}>` in `App.tsx`. Vite's `manualChunks` configuration splits the bundle into 8 named chunks: `vendor` (React/ReactDOM/react-router), `query` (TanStack), `i18n`, `d3-libs`, `charts` (Recharts), `schemas` (Zod), `locale-ar`, and `locale-en`. Only the French locale is in the initial bundle; Arabic and English are loaded dynamically via `import()`.

**Type-safe API layer.** The API client in `services/api/client.ts` defines typed interfaces (`ApiResponse<T>`, `ApiListResponse<T>`, `ApiClientError`) that mirror the backend's response envelope. The access token is stored in memory only (never localStorage) for security, with automatic 401 refresh and CSRF double-submit cookie pattern.

**State management: TanStack React Query v5.** Rather than Redux or Zustand, the project chose server-state management via `@tanstack/react-query`. This is evidenced by the `useQueryDefaults` hook and the absence of any global state library in `package.json`. React Query's caching, deduplication, and background refetch align with the platform's data-heavy nature (grades, attendance, invoices, notifications).

**Form validation: React Hook Form + Zod.** The combination of `react-hook-form` with `@hookform/resolvers` and `zod` provides type-safe form validation that shares schema logic with the backend's Pydantic models.

### Why Not Next.js/Angular/Vue

The application is a pure SPA — there's no server-side rendering requirement because the platform serves authenticated users only (no SEO concern). Next.js would add server complexity for no benefit. The Vite dev server with proxy configuration (`/api` → backend) provides HMR in ~50ms. Angular's heavyweight DI system would be overkill for React Query's approach. Vue was likely excluded for the larger React ecosystem and TypeScript integration maturity.

---

## 3. Mobile Framework: Flutter (Dart)

### Decision Evidence

The `mobile/` directory contains a full Flutter application targeting iOS and Android (`pubspec.yaml`, SDK ^3.5.0).

### Engineering Justification from Code

**Clean architecture with 3 layers.** The `main.dart` docstring specifies: "3-layer architecture per Pack E2: presentation/ → domain/ → data/". The directory structure confirms this:
- `lib/data/` — `api/`, `dto/`, `local_store/`, `repositories_impl/`
- `lib/domain/` — `entities/`, `repositories/` (interfaces)
- `lib/features/` — 35+ feature modules (auth, attendance, billing, games, quizzes, etc.)
- `lib/shared/` — `services/`, `ui/`, `widgets/`

**State management: Riverpod.** `flutter_riverpod: ^2.6.1` is the single state management solution. The app uses `ProviderScope` at the root and `ConsumerStatefulWidget` for the main app. Riverpod was chosen over BLoC or Provider for its compile-time safety, testability, and ability to model async state (essential for a multi-role app with offline support).

**Offline-first with SQLite.** `sqflite: ^2.4.1` provides local persistence with TTL-based cache policies. The `CacheStore().pruneExpired()` call on startup and the `data/local_store/` directory confirm an offline-first strategy where API responses are cached locally and expired entries are pruned automatically. `connectivity_plus` monitors network status for sync decisions.

**Single codebase for iOS and Android.** Flutter's cross-platform compilation eliminates the need for separate Swift/Kotlin teams. The platform targets K-12 schools in Morocco where parents and students use both platforms — maintaining two native codebases would double the development effort.

**Native integrations.** The `pubspec.yaml` reveals 15+ native plugins:
- `firebase_messaging` + `firebase_core` — Push notifications
- `local_auth` — Biometric authentication (fingerprint/Face ID)
- `flutter_secure_storage` — Secure token storage (Keychain/Keystore)
- `web_socket_channel` — Real-time WebSocket connection to backend
- `file_picker` + `image_picker` — Document upload
- `table_calendar` + `device_calendar` — Calendar integration
- `flutter_tts` — Text-to-speech for student accessibility
- `fl_chart` — Data visualization (grades, attendance)

### Why Not React Native/Kotlin Multiplatform

React Native was likely excluded because the team was already using React for web — Flutter provides better performance for animation-heavy K-12 features (games, coloring, quizzes) via its Skia rendering engine. The `features/games/`, `features/coloring/`, and `features/quizzes/` directories confirm these interactive features exist. Kotlin Multiplatform was still maturing and has weaker iOS support.

---

## 4. Database: PostgreSQL 16

### Decision Evidence

PostgreSQL 16 Alpine is specified in `infra/docker-compose.dev.yml`, with `asyncpg` as the async driver and `SQLAlchemy 2.0` as the ORM (`requirements.txt`, `core/database.py`).

### Engineering Justification from Code

**UUID primary keys everywhere.** The `TimestampMixin` in `core/database.py` provides `id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)` — inherited by every model. PostgreSQL's native UUID type with `uuid-ossp` and `pgcrypto` extensions (initialized in `infra/postgres/init.sql`) provides efficient storage and indexing. This choice enables distributed ID generation without coordination — critical for a multi-school SaaS where data is created across many tenants.

**School-scoped multi-tenancy.** The `SchoolScopedMixin` adds a required `school_id` FK with `index=True` to every tenant-scoped model. The `BaseRepository._scoped_query()` method enforces school isolation at the query level: `select(model_class).where(model_class.school_id == school_id)`. PostgreSQL's B-tree indexes on UUID foreign keys make this efficient even at scale.

**Soft delete pattern.** The `SoftDeleteMixin` provides `deleted_at` timestamp with `soft_delete()`, `restore()`, and `is_deleted` property — implementing GDPR-compliant data retention without losing audit trails. PostgreSQL's nullable timestamp columns with partial indexes support efficient queries that exclude soft-deleted rows.

**Advanced PostgreSQL features used:**
- **Materialized views** — `mv_kpi_daily` refreshed concurrently daily by the ARQ worker (`core/tasks.py`, line 302: `REFRESH MATERIALIZED VIEW CONCURRENTLY`)
- **ENUM types** — PostgreSQL native enums for role codes, payment status, etc. (bootstrapped in test `conftest.py`)
- **Streaming replication** — Production uses a read replica (`docker-compose.prod.yml`) with a `replicator` role defined in `init.sql`
- **3 database roles** — `app_user` (read/write for app), `app_readonly` (read-only for reporting), `replicator` (streaming replication)
- **PgBouncer connection pooling** — Transaction mode with pool_size=50 in staging and production

**Alembic migrations.** Version-controlled schema migrations with CI enforcement: the CI pipeline runs a 3-step migration safety check (upgrade → downgrade → re-upgrade) to ensure all migrations are reversible.

### Why Not MySQL/MongoDB

MongoDB's document model doesn't suit the platform's relational complexity — invoices reference students, enrollments reference classes, attendance references sessions, grades reference subjects. The codebase has 38+ repository files with complex JOINs. MySQL lacks PostgreSQL's native UUID type, materialized views, and the rich ENUM support used throughout. PostgreSQL's ACID guarantees are essential for financial operations (billing, payments).

---

## 5. Cache & Message Broker: Redis 7

### Decision Evidence

`redis[hiredis]==5.2.*` in `requirements.txt`, `redis:7-alpine` in Docker Compose, `redis.asyncio` usage in `core/redis.py`.

### Engineering Justification from Code

Redis serves **six distinct purposes** in the codebase, all through a single `redis.asyncio` connection pool:

1. **Rate limiting** — Sliding window counters in `core/rate_limit.py` with keys like `rl:{category}:{user_id}` and window-based expiry.

2. **Idempotency caching** — Response replay for POST/PUT/PATCH in `core/idempotency.py` with keys `idem:{user_id}:{key}` and 24h TTL.

3. **Session management** — Refresh token tracking and revocation. The `auth_service.py` uses Redis to store active session metadata and support the `max_sessions_per_user=5` limit.

4. **WebSocket Pub/Sub** — The `ws_manager.py` uses Redis Pub/Sub channels (`ws:user:{user_id}`) for cross-instance WebSocket message delivery. Each backend instance subscribes to relevant channels, enabling horizontal scaling without sticky sessions.

5. **Background task queue** — ARQ (`arq==0.26.*`) uses Redis as its job queue broker. The `WorkerSettings` class registers 14 task functions and 12+ cron jobs, all coordinated through Redis.

6. **Cache** — Recovery OTPs, email verification codes, and various temporary data with TTL-based expiry. The `task_cleanup_expired_cache` worker proactively scans and removes orphaned keys.

**Production configuration** in `infra/redis/redis.conf`: 256MB `maxmemory` with `allkeys-lru` eviction, AOF persistence with `everysec` fsync. The LRU policy ensures cache entries are evicted gracefully under memory pressure while AOF provides durability for the task queue.

### Why Not RabbitMQ/Memcached/Separate Systems

Using Redis for all six concerns eliminates operational complexity — one system to monitor, backup, and scale. RabbitMQ would add a separate broker for background tasks, but ARQ's Redis-based approach is sufficient for the platform's task volume (14 task types, ~12 cron schedules). Memcached lacks Pub/Sub (needed for WebSocket) and persistence (needed for task queue). The 256MB memory limit is appropriate for the platform's scale.

---

## 6. Background Task Processing: ARQ

### Decision Evidence

`arq==0.26.*` in `requirements.txt`, extensive configuration in `core/tasks.py` (910 lines).

### Engineering Justification from Code

ARQ was chosen as the task queue over Celery for several reasons visible in the code:

**Native async.** Every task function is `async def` — `task_send_email`, `task_cleanup_expired_sessions`, `task_retry_failed_payments`, etc. ARQ runs tasks in the same async event loop, reusing the same asyncpg connection pools and Redis clients. Celery would require sync workers or complex async bridging.

**Redis reuse.** ARQ uses the same Redis instance as the application cache and Pub/Sub. The `get_redis_settings()` function parses the existing `REDIS_URL` environment variable into ARQ's `RedisSettings`. No additional broker infrastructure needed.

**Rich cron scheduling.** The `WorkerSettings.cron_jobs` list defines 12+ scheduled tasks with precise timing:
- Session cleanup daily at 03:00 UTC
- Cache cleanup at 03:15 UTC
- KPI materialized view refresh at 03:30 UTC
- Report file cleanup at 04:00 UTC
- Report schedule evaluation every 15 minutes
- Event reminders every 5 minutes
- Overdue payment reminders daily at 09:00 UTC (10:00 Morocco time)
- Parent alert checks every 6 hours

**Observability integration.** Every task function emits Prometheus metrics: `TASK_ENQUEUED_COUNT`, `TASK_COMPLETED_COUNT`, `TASK_FAILED_COUNT`, and `TASK_DURATION` with environment and task name labels. This is implemented consistently across all 14 task functions via explicit metric instrumentation.

**Fire-and-forget enqueue pattern.** The `enqueue_email()` and `enqueue_task()` helper functions wrap ARQ's `enqueue_job()` in try/except blocks that log warnings but never raise — ensuring API response times aren't affected by worker availability.

---

## 7. Architecture Pattern: Modular Monolith

### Decision Evidence

The `main.py` docstring declares: "Modular monolith backend serving the École Platform API. Architecture: Router → Service → Repository (Pack D2)."

### Engineering Justification from Code

**Three-layer separation.** The backend enforces strict layer boundaries:
- **Routers** (`app/api/v1/`) — HTTP concerns, request parsing, response formatting
- **Services** (`app/services/`) — Business logic, transaction orchestration, domain events
- **Repositories** (`app/repositories/`) — Data access, SQL queries, school-scoped filtering

There are 38 repository files, each extending `BaseRepository` with `_scoped_query()` for tenant isolation. Services use `UnitOfWork` (`core/unit_of_work.py`) for explicit transaction boundaries with automatic rollback on exception.

**Domain events for cross-module communication.** The `domain/events/` directory contains 13 event modules (auth, billing, erp, lms, calendar, documents, budget, etc.), all extending the base `DomainEvent` dataclass with `event_id`, `occurred_at`, `school_id`, and `actor_id`. Events like `InvoiceGenerated`, `PaymentReceived`, `UserRegistered`, `NewDeviceLogin` decouple modules — billing doesn't import from notifications, it emits an event that the notification system consumes.

**Domain value objects.** The `domain/value_objects/` directory contains domain-specific types:
- `Money` — Immutable MAD (Moroccan Dirham) value with `Decimal` precision, currency validation, and arithmetic operators. Prevents float rounding errors in financial calculations.
- `MoroccanGrade` — 0-20 scale with boundary validation, average computation, and Moroccan mention mapping (Très Bien ≥16, Bien ≥14, Assez Bien ≥12, Passable ≥10, Insuffisant <10).

These value objects encode domain invariants that can't be violated at runtime — a grade outside 0-20 or a negative money amount raises immediately.

**Structured exception hierarchy.** `core/exceptions.py` defines a `DomainException` base with 7 concrete subclasses: `AuthenticationError` (401), `AuthorizationError` (403), `NotFoundError` (404), `ConflictError` (409), `ValidationError` (422), `RateLimitError` (429). Each carries a machine-readable `error_code` (format `ERR-{DOMAIN}-{NNN}`), `ErrorCategory` enum, and `retryable` flag. Three exception handlers in `core/middleware.py` convert these into the unified `ErrorResponse` JSON envelope.

### Why Not Microservices

A modular monolith was the right choice for a PFE project and early-stage SaaS:
- **Single deployment unit** — One Docker image, one Helm chart, one CI pipeline. The codebase deploys in under 5 minutes.
- **Shared database transactions** — Operations like "create invoice + send notification + update student record" run in a single database transaction via `UnitOfWork`, avoiding distributed transaction complexity.
- **Module boundaries are enforced by convention** — Domain events, separate repository files, and the router/service/repository layering create logical isolation. If a module needs to become a microservice later, the event-driven boundary is already defined.
- **14 background tasks run in the same worker** — All 14 ARQ task functions share the same database connection pool and Redis client, minimizing resource consumption.

---

## 8. Authentication & Security Stack

### Decision Evidence

`python-jose[cryptography]==3.5.0`, `passlib[bcrypt]==1.7.*`, `bcrypt==4.2.*`, `pyotp==2.9.*` in `requirements.txt`.

### Engineering Justification from Code

**JWT with dual-key rotation.** `core/security.py` creates access tokens (30min TTL) with claims: `sub`, `role`, `school_id`, `session_id`, `exp`, `iat`, `jti`, `type`. The `config.py` supports `jwt_previous_key` for zero-downtime key rotation — the `infra/scripts/rotate-secrets.sh` script implements a 30-minute dual-key window where both old and new keys are valid.

**bcrypt password hashing.** Direct `bcrypt` library usage (not through passlib) for password hashing and verification. The password policy in `core/password_policy.py` enforces: minimum 12 characters, uppercase, lowercase, digit, special character, not in common passwords list, and not containing the user's name or email.

**TOTP 2FA.** `pyotp` provides time-based one-time password generation and verification. The auth service handles the complete 2FA flow: setup (QR code via `qrcode[pil]`), verify-setup, disable, and verify-login.

**RBAC permission catalog.** `core/permissions.py` defines 10 roles (ADM, DIR, TCH, EDUCATOR, PAR, STD, SUP, SYS, CONTENT_MGR, PUBLIC) and 80+ permissions in the format `PERM-{DOMAIN}:{resource}:{action}`. The permission catalog is the single source of truth — no database queries needed for permission checks.

**Security dependency chain.** `core/dependencies.py` implements the security pipeline as composable FastAPI dependencies: `get_current_user()` → `AuthContext` → RBAC check → ABAC check → invariant check. The deny ordering follows the principle: 401 (not authenticated) → 404 (resource not found, masking existence) → 403 (not authorized).

---

## 9. Observability Stack: Prometheus + Grafana + Loki + Tempo

### Decision Evidence

`prometheus-client==0.21.*` and 4 OpenTelemetry packages in `requirements.txt`. Full monitoring stack in `docker-compose.monitoring.yml`.

### Engineering Justification from Code

**30+ Prometheus collectors in `core/metrics.py`.** The metrics module (409 lines) implements the four golden signals pattern:
- **Latency** — `REQUEST_DURATION` histogram with 10 custom buckets (5ms → 30s)
- **Traffic** — `REQUEST_COUNT` counter by method, endpoint, status
- **Errors** — `ERROR_COUNT` counter by type, plus `AUTH_LOGIN_COUNT` by status
- **Saturation** — `DB_POOL_SIZE`, `DB_POOL_IN_USE`, `DB_POOL_OVERFLOW` gauges

Domain-specific metrics include: `WEBHOOK_COUNT`, `WEBHOOK_SIGNATURE_FAILURES`, `PAYMENT_INITIATED/COMPLETED`, `BACKUP_JOB_SUCCESS/FAILURE`, `TASK_ENQUEUED/COMPLETED/FAILED/DURATION`, `REPORT_GENERATION`, `DOCUMENT_UPLOAD`, `REDIS_COMMANDS/HIT/MISS`.

**OpenTelemetry distributed tracing.** `core/telemetry.py` (46 lines) initializes auto-instrumentation for FastAPI, SQLAlchemy, and Redis via OTLP gRPC exporter to Tempo. The Grafana datasource configuration (`grafana/provisioning/datasources/datasources.yml`) links Tempo traces to Loki logs, enabling click-through from a slow trace to its log entries.

**12 Prometheus alert rules + 5 Loki alert rules.** Three severity levels with inhibition (SEV-1 suppresses SEV-2/3):
- SEV-1: availability <99.5%, DB pool ≥90%, webhook signature failure
- SEV-2: p95 latency >500ms, error rate >2%, login success <90%
- SEV-3: request rate >500/s, payment failure >10%

**PII redaction in Promtail.** The log pipeline in `promtail-config.yml` applies inline regex replacement to redact `password`, `token`, and `refresh_token` fields before logs reach Loki. This is a GDPR-aligned design decision for a platform handling student and parent data.

### Why This Stack (Not ELK/Datadog/New Relic)

The entire stack runs self-hosted in Docker containers — no SaaS vendor dependency or per-seat pricing. For a Moroccan school platform, this eliminates USD-denominated cloud monitoring costs. The stack is also fully open-source (Apache 2.0 / AGPL), aligning with the academic context of a PFE project.

---

## 10. Containerization: Docker Multi-Stage Builds

### Decision Evidence

`backend/Dockerfile` (4 stages), `web/Dockerfile` (3 stages), 6 Docker Compose files.

### Engineering Justification from Code

**Backend Dockerfile — 4 build stages:**
1. `base` — Python 3.12-slim with system dependencies, non-root `appuser`, requirements installed
2. `test` — Adds test dependencies for CI
3. `development` — Hot reload with Uvicorn, runs as root for volume mounts
4. `production` — Copies only app code, runs as `appuser` (UID 1000), includes `HEALTHCHECK` instruction

**Web Dockerfile — 3 build stages:**
1. Development — Node 22-alpine with Vite dev server
2. Build — `npm run build` produces static assets
3. Production — nginx:alpine serves static files, runs as non-root user

**Three-environment topology:**
- **Development** (`docker-compose.dev.yml`) — 5 services, host volume mounts, hot reload
- **Staging** (`docker-compose.staging.yml`) — Mirrors production with PgBouncer, WAL archiving, seed data on startup
- **Production** (`docker-compose.prod.yml`) — 10 services including read replica, PgBouncer, certbot, Nginx reverse proxy

**Docker secrets.** Production uses 9 Docker secrets (`/run/secrets/*`) instead of environment variables. The `Settings.model_post_init()` method reads `DATABASE_URL_FILE`, `REDIS_URL_FILE`, `JWT_SECRET_KEY_FILE`, etc. from the filesystem, preventing secrets from appearing in `docker inspect` output or process environment listings.

---

## 11. CI/CD: GitHub Actions with Matrix Testing

### Decision Evidence

`.github/workflows/ci.yml` (~1065 lines), 4 workflow files, `.github/dependabot.yml`.

### Engineering Justification from Code

**13-job CI pipeline** with dependency graph:
- `lint` → Static analysis (Ruff, ESLint, Prettier)
- `security-trivy`, `security-pip-audit`, `security-bandit` → Security scanning (parallel)
- `migration-safety` → 3-step Alembic verification (upgrade → downgrade → re-upgrade)
- `unit-tests` → **6-matrix** (Python 3.12/3.13 × PostgreSQL 15/16/17)
- `integration-tests` → **6-matrix** (same)
- `contract-tests`, `security-tests`, `e2e-tests` → Specialized test suites
- `load-tests` → k6 with 4 scenarios
- `coverage-report` → Cross-phase aggregation with 95% threshold on core modules
- `publish-images` → GHCR push with SBOM generation (SPDX format)

**Matrix testing across 6 environment combinations** catches compatibility issues early. Testing against PostgreSQL 15, 16, and 17 ensures the platform works on any version a school might deploy. Python 3.12 and 3.13 testing future-proofs the codebase.

**Kubernetes deployment** (`.github/workflows/deploy-k8s.yml`) uses Helm with environment-specific values, automatic rollback on failure, and post-deploy health verification.

**Dependency management** via Dependabot across 4 ecosystems (pip, npm, Docker, GitHub Actions) with grouped security updates.

---

## 12. Orchestration: Kubernetes with Helm

### Decision Evidence

`infra/k8s/` directory with Helm chart, HPA, PDB, and Ingress templates.

### Engineering Justification from Code

**Horizontal Pod Autoscaler.** Backend scales from 2 to 8 replicas at 70% CPU utilization (`values.yaml`). The HPA uses `autoscaling/v2` with CPU target utilization percentage.

**Pod Disruption Budgets.** `pdb.yaml` ensures `minAvailable: 1` for both backend and web during node drains or upgrades — maintaining availability during cluster maintenance.

**Ingress routing.** Path-based routing: `/api` and `/ws` route to the backend service, everything else routes to the web SPA. TLS termination via cert-manager with the school's domain.

**Liveness and readiness probes.** Backend deployment defines:
- Readiness: `/api/v1/health` every 10s with 5s timeout
- Liveness: `/api/v1/health` every 30s with 10s timeout

This ensures unhealthy pods are removed from service before they affect users, and stuck pods are restarted automatically.

---

## 13. Internationalization: Trilingual Support (fr/ar/en)

### Decision Evidence

`web/src/shared/i18n/index.ts`, locale files (fr.json, ar.json, en.json), `mobile/lib/l10n/`.

### Engineering Justification from Code

**French as default, Arabic with RTL.** The i18n system (`shared/i18n/index.ts`) sets `fallbackLng: 'fr'` and only bundles French in the initial load. Arabic and English are lazy-loaded via dynamic `import()` — reducing initial bundle size. When Arabic is selected, `applyDirection()` sets `document.documentElement.dir = 'rtl'` for full RTL layout.

**Morocco-specific formatting.** `formatDate()` uses `timeZone: 'Africa/Casablanca'` for all date display. `formatCurrency()` defaults to MAD (Moroccan Dirham). The backend's ARQ cron jobs use `ZoneInfo("Africa/Casablanca")` for scheduling notification digests and document expiry checks at local business hours.

**Mobile i18n.** The Flutter app uses `flutter_localizations` with `intl: ^0.20.2` for date/number formatting and ARB-based string localization in `lib/l10n/`.

This trilingual design reflects Morocco's linguistic reality: French is the primary language of instruction in many private schools, Arabic is the national language, and English is increasingly important for international curricula.

---

## 14. Real-Time Communication: WebSocket + Redis Pub/Sub

### Decision Evidence

`core/ws_manager.py`, `web/src/services/api/client.ts`, `mobile/pubspec.yaml` (`web_socket_channel`).

### Engineering Justification from Code

The `ConnectionManager` class manages WebSocket connections with three key design decisions:

1. **Redis Pub/Sub for horizontal scaling.** Each backend instance maintains local connections but subscribes to Redis channels (`ws:user:{user_id}`). When a notification is published, all instances receive it and forward to locally connected clients. This enables scaling to multiple backend pods without sticky sessions.

2. **Connection limits.** `MAX_CONNECTIONS_PER_USER = 3` prevents resource exhaustion. When a user opens a 4th tab, the oldest connection is evicted.

3. **Heartbeat keepalive.** `HEARTBEAT_INTERVAL = 30` seconds maintains connection liveness through proxies and load balancers that may close idle connections.

4. **Graceful degradation.** If Redis is unavailable, the manager falls back to local-only delivery — notifications still reach users connected to the same instance.

---

## 15. Document Generation: WeasyPrint + ReportLab

### Decision Evidence

`weasyprint==68.0` and `reportlab==4.2.*` in `requirements.txt`, `task_generate_report` in `core/tasks.py`.

### Engineering Justification from Code

The platform generates PDF reports asynchronously via ARQ background tasks. `ReportsService.generate_report_job()` is called by the worker, with results cached and tracked via `ReportJobStatus`. WeasyPrint renders HTML templates to PDF (leveraging Jinja2 templates), while ReportLab handles programmatic PDF generation for structured data reports (gradebooks, attendance records, invoices).

The choice of dual PDF engines allows: WeasyPrint for rich, styled reports that designers can modify via HTML/CSS, and ReportLab for data-heavy tabular reports that need precise layout control.

---

## 16. Technology Decision Summary

| Layer | Technology | Version | Key Justification |
|-------|-----------|---------|-------------------|
| Backend framework | FastAPI | 0.120.4 | Native async, auto OpenAPI, Pydantic validation, dependency injection |
| Backend language | Python | 3.12/3.13 | Async ecosystem maturity, data science libs, rapid development |
| Web framework | React | 18.3.1 | Component model, massive ecosystem, TypeScript support |
| Web build tool | Vite | 6.0 | Sub-second HMR, ES module native, optimized chunking |
| Web language | TypeScript | 5.6 | Strict typing catches bugs at compile time across 100+ routes |
| Mobile framework | Flutter | SDK ^3.5.0 | Single codebase iOS/Android, Skia rendering for games/interactive |
| Mobile state | Riverpod | 2.6.1 | Compile-time safety, async-native, testable |
| Database | PostgreSQL | 16 | UUID PK, materialized views, streaming replication, ENUM types |
| ORM | SQLAlchemy | 2.0 | Async support, type-mapped columns, Alembic migrations |
| Cache/Broker | Redis | 7 | Rate limiting + sessions + Pub/Sub + task queue + cache in one system |
| Task queue | ARQ | 0.26 | Async-native, Redis-backed, built-in cron, lightweight |
| API validation | Pydantic | v2 | Settings, request schemas, OpenAPI generation |
| Server state | TanStack Query | 5.95 | Caching, deduplication, background refetch for data-heavy UI |
| Form validation | Zod + RHF | 4.3/7.72 | Type-safe schemas shared with backend contract |
| Auth | JWT + bcrypt + TOTP | — | Stateless access, secure passwords, optional 2FA |
| Metrics | Prometheus | 0.21 | 30+ custom collectors, golden signals, alerting |
| Tracing | OpenTelemetry | 1.40 | FastAPI/SQLAlchemy/Redis auto-instrumentation |
| Logs | Loki + Promtail | 2.9.4 | Docker-native, PII redaction, correlation ID extraction |
| Visualization | Grafana | 10.4 | 4 datasources linked (Prometheus, Loki, Tempo, Alertmanager) |
| Container | Docker | Multi-stage | 4-stage backend, 3-stage web, non-root production |
| Orchestration | Kubernetes + Helm | — | HPA, PDB, Ingress, auto-rollback |
| CI/CD | GitHub Actions | — | 13-job pipeline, 6-matrix testing, SBOM generation |
| PDF generation | WeasyPrint + ReportLab | 68.0/4.2 | HTML-to-PDF for styled reports, programmatic for data tables |
| i18n | i18next / flutter_intl | — | Trilingual (fr/ar/en), RTL support, lazy loading |

---

## 21. Cross-Cutting Engineering Patterns

Several patterns appear consistently across all technology choices:

**Async-first design.** FastAPI, asyncpg, redis.asyncio, ARQ, aiosmtplib — every I/O-bound operation is non-blocking. This is not incidental; the security pipeline alone involves 3+ async dependency resolutions per request.

**Convention over configuration.** The `BaseRepository._scoped_query()` pattern, `TimestampMixin` for audit columns, `DomainEvent` base class for event inheritance, and `ErrorCategory` enum for exception classification create a consistent development experience across all 6 business domains.

**Observability as a first-class concern.** Every ARQ task function instruments duration, success, and failure metrics. The PrometheusMiddleware normalizes UUID paths. Log entries include correlation IDs. Traces span from HTTP request through SQLAlchemy to Redis. This is not an afterthought — it's designed into every layer.

**Security by default.** Docker secrets instead of env vars, non-root containers, 401→404→403 deny ordering, RBAC permission catalog, ABAC school-scoping, PII redaction in logs, CSRF double-submit cookies, bcrypt hashing, rate limiting at both Nginx and application layers.

**Morocco-specific engineering.** MAD currency type, 0-20 grading scale with French mentions, Africa/Casablanca timezone throughout, trilingual i18n with Arabic RTL, Moroccan phone format in test factories, France locale in Faker data generation.

## 17. MinIO/S3 Object Storage

### Context

Need for scalable file storage (documents, uploads, invoice PDFs).

### Decision

Use MinIO for dev/staging, AWS S3 for production, behind a unified `StorageBackend` protocol.

### Rationale

S3-compatible API, presigned URLs offload API from file transfer, interchangeable backends.

### Trade-off

Added infrastructure complexity vs. infinite local disk scaling issues.

---

## 18. Seed Architecture for Demo Data

### Context

Need realistic demo data for sales, CI, and developer onboarding.

### Decision

Three-tier seed system (`seed.py` + `seed_extensions.py` + `seed_enhanced.py`) achieving ~93% table coverage.

### Rationale

Idempotent, fast reset, covers all personas (admin/teacher/parent/student), 2 schools for multi-tenant demos.

### Trade-off

Maintenance cost when schema changes vs. manual data entry overhead.

---

## 19. Mobile Offline-First Sync

### Context

Unreliable Moroccan network connectivity.

### Decision

SQLite local storage + sync queue with server reconciliation.

### Rationale

8 local stores, offline queue replays mutations when connectivity returns, conflict resolution.

### Trade-off

Data consistency complexity vs. user experience in low-connectivity areas.

---

## 20. Pydantic v2 Migration

### Context

Pydantic v1 deprecation, performance improvements in v2.

### Decision

Migrated entire codebase to Pydantic v2 with `model_validator`, `field_validator`, `computed_field`.

### Rationale

2-5x faster validation, better type inference, future-proof.

### Trade-off

Breaking changes requiring widespread code updates.
