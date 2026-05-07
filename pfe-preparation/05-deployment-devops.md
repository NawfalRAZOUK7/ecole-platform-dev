# Step 5 — Deployment & DevOps Analysis

> Extracted from implemented infrastructure code in `infra/`, `.github/workflows/`, `backend/Dockerfile`, `web/Dockerfile`, and `backend/app/core/` modules.

---

## 1. Infrastructure File Inventory

| Category | Files | Key Configs |
|---|---|---|
| Docker Compose | 7 compose files | dev, staging, prod, monitoring, blue, green, override example |
| Dockerfiles | 3 files | backend (multi-stage), web prod, web dev |
| CI/CD Workflows | 7 workflows | ci, deploy-staging, deploy-k8s, web-ci, web-e2e, docs, cleanup-images |
| Helm Chart | 10 templates + 3 values files | backend, web, worker deployments, HPA, PDB, ingress, configmap, secrets |
| Monitoring | 4 tool configs | Prometheus, Grafana (8 dashboards), Loki, Tempo |
| Alerting | 3 config files | Prometheus alert rules (12 rules), Loki log alerts (5 rules), Alertmanager routing |
| Nginx | 4 config files | dev, staging, prod (TLS), upstream (blue-green) |
| Scripts | 7 operational scripts | deploy, blue-green-deploy, healthcheck, backup, restore, rotate-secrets, ssl-renew |
| Backup | 4 scripts | pg_backup, pg_restore, restore_drill, audit_worm_export |
| Dependency Mgmt | 2 configs | Dependabot (4 ecosystems), dependabot-automerge workflow |

Total infrastructure files: **~55 files** dedicated to deployment, monitoring, and operations.

---

## 2. Container Strategy

### 2.1 Backend Dockerfile — Multi-Stage Build

The backend Dockerfile (`backend/Dockerfile`) uses Docker BuildKit syntax `docker/dockerfile:1.7` with 4 distinct stages:

**Stage 1 — `base`**: Python 3.12-slim foundation. Installs system dependencies (`libpq-dev`, `gcc`, `libffi-dev`) and pip requirements with BuildKit cache mount (`--mount=type=cache,target=/root/.cache/pip`) for layer-reusable dependency installs. Sets `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` for container-optimized Python execution.

**Stage 2 — `test`**: Extends base with dev/test dependencies. Runs `ruff check` and `ruff format --check` as part of the build — lint failures break the image build. This enforces code quality at the Docker layer, not just CI.

**Stage 3 — `development`**: Extends base with test deps. Runs Uvicorn with `--reload` for hot-reload development. Used by `docker-compose.dev.yml` with volume mounts for live code editing.

**Stage 4 — `production`**: Extends base with only production code. Creates a non-root `appuser`, transfers file ownership, and runs as `USER appuser`. Includes a Docker-native `HEALTHCHECK` hitting `/api/v1/health` every 30 seconds. Runs Uvicorn with 4 workers (no reload).

The production image does NOT include test dependencies, dev tools, or linting packages — the multi-stage approach ensures minimal attack surface and smaller image size.

### 2.2 Web Frontend Dockerfile

The web Dockerfile (`web/Dockerfile`) uses 3 stages:

**`development`**: Node 22-alpine with `npm ci` and Vite dev server.

**`build`**: Runs `npm run build` to produce static assets in `/workspace/web/dist`.

**`production`**: Uses `nginx:alpine` as the final image. Copies the built static files from the build stage. Runs Nginx as non-root user (`USER nginx`), with custom `nginx.conf` for SPA routing. The resulting image is lightweight — only Nginx and static HTML/JS/CSS.

### 2.4 Mobile CI/CD

The mobile application uses a Flutter build pipeline with the following stages:

- **Dart analysis** — static analysis via `dart analyze` and `flutter analyze`
- **Widget tests** — unit-level UI tests run with `flutter test`
- **Integration tests** — end-to-end tests on emulator/device via `integration_test`
- **Artifact generation** — APK (Android) and IPA (iOS) builds produced as CI artifacts
- **Distribution** — APK/IPA artifacts can be pushed to Firebase App Distribution or TestFlight for QA and beta testing

> **Note:** Mobile deployment is currently manual and performed via CI-generated artifacts. There is no automated app store release pipeline at this time.

### 2.3 Service Topology per Compose File

The `docker-compose.dev.yml` defines **6 services**: `postgres` (16-alpine), `redis` (7-alpine), `backend` (development target), `worker` (ARQ background processor), `web` (Node 22 Vite dev server), and `minio` (S3-compatible object storage for documents, uploads, and invoice PDFs). All services have resource limits, health checks, and JSON file logging with rotation.

The `docker-compose.prod.yml` extends this to **11+ services**: `backend` (production target), `postgres` (tuned with WAL archiving, pg_stat_statements, custom shared_buffers), `pgbouncer` (connection pooling), `postgres-replica` (streaming replication), `redis` (maxmemory 512MB, LRU eviction), `web` (Nginx-served static), `nginx` (TLS reverse proxy), `worker` (ARQ), `certbot` (Let's Encrypt auto-renewal), `prometheus`, `grafana`, and `minio` (S3-compatible object storage for documents, uploads, and invoice PDFs).

---

## 3. Environment Topology

The platform implements a three-environment strategy — development, staging, and production — each with distinct Docker Compose configurations.

### 3.1 Development Environment

Uses `docker-compose.dev.yml`. Backend runs in development mode with `--reload`, volume-mounted source code for live editing. Ports exposed directly to host (5432, 6379, 8000, 5173). Default credentials with `change-me` placeholders. No TLS, no PgBouncer, no reverse proxy.

### 3.2 Staging Environment

Uses `docker-compose.staging.yml`. Mirrors production topology but with relaxed settings: PgBouncer present (transaction pooling, 50 pool size), WAL archiving enabled for PITR, backend runs production Docker target, `SEED_ON_STARTUP=true` for demo data (the seed system achieves ~93% table coverage), `AI_PROVIDER=mock` to avoid real API costs, TLS via Nginx, no ports exposed except 80/443 via Nginx. Named `ecole-staging-*` containers. Separate `ecole-staging-network`.

### 3.3 Production Environment

Uses `docker-compose.prod.yml`. All secrets delivered via Docker secrets (`/run/secrets/*`) — no environment variable secrets. PgBouncer in transaction pool mode (50 pool, 200 max clients). PostgreSQL tuned: `shared_buffers=256MB`, `effective_cache_size=768MB`, `work_mem=4MB`, `max_connections=200`, `log_min_duration_statement=200ms`, `shared_preload_libraries=pg_stat_statements`. Read replica with streaming replication (`hot_standby=on`). Certbot auto-renewal loop (every 12 hours). Backend scaled without fixed container name (`--scale backend=N` ready). `ENABLE_STRICT_RATE_LIMIT=true`. `ACCESS_TOKEN_EXPIRE_MINUTES=15` (shorter than staging's 30).

### 3.4 Docker Secrets Management

Production uses 9 Docker secrets, each as a file in `infra/secrets/`:

- `jwt_secret_key.txt` — generated via `openssl rand -hex 32`
- `db_password.txt`, `app_db_password.txt`, `app_readonly_password.txt` — generated via `openssl rand -base64 24`
- `database_url.txt` — full connection string pointing at PgBouncer port 6432
- `redis_password.txt`, `redis_url.txt` — Redis credentials
- `smtp_password.txt` — email service credentials
- `grafana_admin_password.txt` — Grafana admin password

Services read secrets via `*_FILE` environment variables (e.g., `DATABASE_URL_FILE=/run/secrets/database_url`), keeping secrets out of environment variable inspection.

---

## 4. CI/CD Pipeline

### 4.1 Main CI Pipeline (`ci.yml`)

Triggered on push to `main`/`develop` and pull requests. The pipeline has **13 jobs** organized in a dependency DAG:

**Layer 1 — Quality Gate** (parallel):
- `lint`: Ruff check + format check, Alembic migration branch conflict detection (no multiple heads), OpenAPI spec drift check (`scripts/export_openapi.py --check`)
- `web-lint`: TypeScript compile check (`tsc --noEmit`), Vite build verification

**Layer 2 — Security Scans** (after lint):
- `security-trivy`: Container image vulnerability scan using Aqua Trivy, fails on CRITICAL/HIGH severity
- `security-pip-audit`: Python dependency vulnerability audit via `pip-audit --strict`
- `security-bandit`: Static application security testing with Bandit, outputs JSON report

**Layer 3 — Testing** (after lint):
- `unit-tests`: Matrix build across Python 3.12/3.13 × PostgreSQL 15/16/17 (6 combinations). Coverage enforced at 95% minimum for core modules (`exceptions.py`, `permissions.py`, `response.py`, `security.py`)
- `migration-safety`: Detects Alembic file changes, runs `upgrade head` → `downgrade base` → `upgrade head` to verify reversibility and idempotency

**Layer 4 — Integration** (after unit):
- `integration-tests`: Same 6-matrix combinations. Starts real PostgreSQL + Redis services, runs Alembic migrations, seeds data, starts live Uvicorn server, runs integration test suite
- `e2e-tests` (after web-lint + integration): Playwright E2E with Chromium, full stack (backend + Vite dev server)

**Layer 5 — Specialized Testing** (after integration):
- `contract-tests`: API contract verification against live server
- `security-tests`: RBAC enforcement tests (every role × every endpoint)
- `security-audit`: Dedicated security audit test suite
- `load-tests`: k6 performance testing with 4 scenarios — login flows, GET requests, file uploads, WebSocket connections

**Layer 6 — Artifacts** (after all tests):
- `coverage-report`: Combines coverage data from all test jobs (unit + integration + contract + security + e2e + load), generates HTML report and XML output
- `publish-images`: Builds and pushes to GHCR (`ghcr.io`) with SHA-based tags + `latest`. Generates SPDX SBOMs for both backend and web images. Only runs on `main` branch pushes

All jobs use `actions/cache@v4` for pip and npm dependencies. The pipeline validates across **6 Python/PostgreSQL combinations**, 3 security scan tools, 4 load test scenarios, and produces SBOMs.

### 4.2 Deploy to Staging (`deploy-staging.yml`)

Triggered on push to `develop`. Builds and starts the full staging stack with `docker compose up -d --build --wait`. Verifies backend health, then validates seed data by attempting a login with the admin test account and checking for a valid access token in the response.

### 4.3 Deploy to Kubernetes (`deploy-k8s.yml`)

Triggered on push to `main` (production) or `develop` (staging). Two-job pipeline:

**Job 1 — Build & Push**: Builds backend and web images, pushes to GHCR with SHA-based tags. Uses BuildKit layer caching via `cache-from: type=gha,scope=backend`.

**Job 2 — Deploy**: Determines environment from branch name. Sets up Helm v3.14 and kubectl. Configures kubeconfig from a base64-encoded GitHub secret (`KUBE_CONFIG`). Runs `helm upgrade --install` with environment-specific values files. Verifies rollout status for both backend and web deployments with timeout. Performs post-deploy health check by exec'ing into the backend pod. On failure, automatically runs `helm rollback` to the previous release.

### 4.4 Dependency Management

Dependabot configured for 4 ecosystems:
- **pip** (weekly, Monday 08:00 Africa/Casablanca): Groups `security` packages (cryptography, python-jose, passlib, pyotp) and `database` packages (sqlalchemy, alembic, asyncpg)
- **npm** (weekly): Web frontend dependencies
- **Docker** (monthly): Base image updates
- **GitHub Actions** (monthly): CI action version bumps

Auto-merge workflow (`dependabot-automerge.yml`) enables automatic merging of patch-level Dependabot PRs.

### 4.5 Image Lifecycle

`cleanup-images.yml` runs weekly (Sunday 03:00) to delete old untagged container images from GHCR, keeping the 10 most recent versions for both backend and web packages.

---

## 5. Zero-Downtime Deployment Strategy

### 5.1 Blue-Green Deployment

The platform implements blue-green deployment via `docker-compose.blue.yml` and `docker-compose.green.yml`. Each file defines a `backend-{color}` and `worker-{color}` service pair, mapped to different host ports (blue: 8001, green: 8002). Both use pre-built images from GHCR (`ghcr.io/ecole-platform/backend`) tagged via `IMAGE_TAG` environment variable.

The `blue-green-deploy.sh` script orchestrates the switch:

1. Reads current active environment from `infra/active-env` file (defaults to `blue`)
2. Pulls and starts the inactive environment's containers
3. Runs `alembic upgrade head` inside the new backend container
4. Health-checks the new environment (12 attempts, 5-second intervals = 60-second timeout)
5. If health check fails, tears down the new environment and exits with error
6. If healthy, rewrites `nginx/upstream.conf` to point `backend_active` at the new container
7. Sends `nginx -s reload` to the production Nginx for seamless traffic switch
8. Writes the new active environment to the `active-env` file
9. Waits 30 seconds for connection draining, then stops the old environment

The Nginx `upstream.conf` file is the single point of traffic routing: `upstream backend_active { server ecole-backend-blue:8000; }` or `ecole-backend-green:8000`.

### 5.2 Rolling Deploy Script

The `deploy.sh` script provides a traditional rolling deployment with automatic rollback:

1. **Pre-flight**: Verifies Docker Compose V2, `.env.prod`, compose file, and secret files exist
2. **Image backup**: Tags current running images as `:previous` for rollback
3. **Build/Pull**: Builds updated images with `--pull`
4. **Migrations**: Runs `alembic upgrade head` (skippable via `--skip-migrations`)
5. **Rolling restart**: Restarts services sequentially — infrastructure (postgres, redis) → backend (with health check) → worker → web → nginx reload
6. **Automatic rollback**: If backend health check fails, restores `:previous` image tag and restarts
7. **Final health check**: Verifies the full stack is operational

The script supports `--rollback` flag for manual rollback to the `:previous` tagged images.

---

## 6. Monitoring & Observability Stack

### 6.1 Four Pillars Architecture

The monitoring stack (`docker-compose.monitoring.yml`) implements the four pillars of observability:

| Pillar | Tool | Version | Data Source |
|---|---|---|---|
| Metrics | Prometheus | v2.51.0 | `/metrics` endpoint on backend:8000 |
| Logs | Loki + Promtail | v2.9.4 | Docker container stdout/stderr via socket |
| Traces | Tempo | v2.4.0 | OpenTelemetry OTLP gRPC on port 4317 |
| Dashboards | Grafana | v10.4.0 | Auto-provisioned datasources + dashboards |

### 6.2 Metrics — Prometheus + Application Instrumentation

The backend exposes a `/metrics` endpoint via `prometheus_client`. The `metrics.py` module (409 lines) defines a custom `CollectorRegistry` with **30+ metric collectors** across 10 categories:

**Golden Signals**: `api_request_count` (Counter, 5 labels), `api_request_duration_seconds` (Histogram, 10 custom buckets from 10ms to 10s), `api_error_count` (Counter with client/server category).

**Auth Metrics**: `auth_login_count`, `auth_token_refresh_count` (success/failure).

**Database Pool**: `db_pool_size`, `db_pool_in_use`, `db_pool_overflow` (Gauges, refreshed on each `/metrics` scrape via `collect_db_pool_metrics()`).

**Redis**: `redis_commands_count`, `redis_hit_count`, `redis_miss_count`.

**Webhook**: `webhook_received_count`, `webhook_signature_failures`.

**Billing**: `payment_initiated_count`, `payment_completed_count` (by outcome: paid/failed/canceled).

**Backup**: `backup_job_success_count`, `backup_job_failure_count`, `last_successful_backup_timestamp`.

**Background Tasks**: `task_enqueued_total`, `task_completed_total`, `task_failed_total`, `task_duration_seconds`.

**Reports**: `report_generation_count`, `report_generation_duration_seconds`.

**Document Storage**: `upload_count`, `upload_size_bytes`, `storage_total_bytes`.

The `PrometheusMiddleware` automatically instruments all API requests, normalizing UUID path segments to `{id}` to prevent label cardinality explosion. Prometheus scrapes every 10 seconds with 30-day retention.

### 6.3 Distributed Tracing — OpenTelemetry + Tempo

The `telemetry.py` module configures OpenTelemetry with auto-instrumentation for three layers:

- **FastAPI**: `FastAPIInstrumentor.instrument_app(app)` — traces every HTTP request with span attributes (method, path, status, duration)
- **SQLAlchemy**: `SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)` — traces database queries with SQL statement and execution time
- **Redis**: `RedisInstrumentor().instrument()` — traces Redis commands

Traces are exported via OTLP gRPC to Tempo (port 4317) using `BatchSpanProcessor` for efficient batching. Each span carries service metadata: `service.name=ecole-backend`, `service.version=0.1.0`, `deployment.environment`.

Tempo stores traces locally with 30-day block retention (720 hours). The Grafana Tempo datasource is pre-configured with `tracesToLogs` linking (traces → Loki logs by `service.name`) and `serviceMap` visualization via Prometheus.

### 6.4 Log Aggregation — Loki + Promtail

**Promtail** ships Docker container logs to Loki by mounting the Docker socket. It auto-discovers containers matching `ecole-*` naming pattern. The pipeline extracts structured fields from JSON logs: `level`, `correlation_id`, `user_id`, `method`, `path`, `status_code`, `latency_ms`, `error_code`, `module`. Only `level` is promoted to a Loki label (to avoid high cardinality); other fields are queryable via LogQL line filters.

Promtail includes inline PII redaction — regex-based replacement of `password`, `token`, and `refresh_token` values with `[REDACTED]` before shipping to Loki.

**Loki** uses TSDB storage schema v13 with filesystem backend. Configured with ingestion rate limits (10 MB/s, 20 MB burst), 7-day rejection window for old samples, and 30-day retention with automated compaction every 10 minutes. Loki's ruler connects to Alertmanager for log-based alerting.

### 6.5 Grafana Dashboards

8 pre-provisioned dashboards stored as JSON in `infra/grafana/dashboards/`:

1. **api-overview.json** — Request rate, latency percentiles, error rate, top endpoints
2. **auth-sessions.json** — Login success/failure rates, session counts, token refreshes
3. **billing-providers.json** — Payment initiation, completion by outcome, webhook status
4. **business-education.json** — Educational activity metrics (LMS, attendance)
5. **business-metrics.json** — Cross-domain business KPIs
6. **db-redis-health.json** — Connection pool utilization, Redis memory/hit rate
7. **infrastructure.json** — Container health, resource usage, network metrics
8. **logs-explorer.json** — Loki log search with correlation ID filtering

Grafana auto-provisions 4 datasources (Prometheus, Loki, Tempo, Alertmanager) via YAML provisioning in `grafana/provisioning/datasources/datasources.yml`.

---

## 7. Alerting Strategy

### 7.1 Three-Severity Model

Alert rules implement a SEV-1/SEV-2/SEV-3 severity model with 12 Prometheus metric-based rules and 5 Loki log-based rules.

**SEV-1 — Critical (immediate response)**:
- `ApiAvailabilityCritical`: Server error rate > 0.5% over 1 hour (SLO: 99.5%)
- `DbPoolSaturationCritical`: Pool utilization ≥ 90% for 10 minutes
- `WebhookSignatureFailure`: Any signature verification failure (possible compromise)
- `AuthBruteForce` (Loki): > 5 failed logins/min from single IP
- `DatabasePoolExhaustion` (Loki): SQLAlchemy QueuePool overflow detected
- `MigrationErrors` (Loki): Alembic errors in backend logs

**SEV-2 — Major (urgent)**:
- `ApiLatencyHigh`: p95 > 500ms for 10 minutes (SLO target: 350ms)
- `ApiErrorRateHigh`: Error rate > 2% for 5 minutes
- `AuthLoginSuccessLow`: Login success rate < 90% for 10 minutes
- `DbPoolSaturationWarning`: Pool utilization ≥ 85% for 10 minutes
- `ProviderTimeoutHigh`: > 30 external provider timeouts in 5 minutes
- `BackupJobFailed`: Backup job failure in last hour
- `HighErrorRate` (Loki): > 0.5 errors/sec for 2 minutes
- `PaymentWebhookFailures` (Loki): Elevated webhook failure rate

**SEV-3 — Warning (monitor)**:
- `ApiRequestRateHigh`: Request rate > 500 req/s for 5 minutes
- `PaymentFailureElevated`: Payment failure rate > 10% for 10 minutes
- `BackupMissed`: No backup in 25 hours

### 7.2 Alertmanager Routing

Alerts route to 3 Slack channels by severity:
- SEV-1 → `#ecole-critical` (10s group wait, 1m interval, 15m repeat)
- SEV-2 → `#ecole-warnings` (30s group wait, 5m interval, 1h repeat)
- SEV-3 → `#ecole-info` (1m group wait, 10m interval, 4h repeat)

Inhibition rules suppress lower-severity alerts when higher-severity fires for the same service — SEV-1 suppresses SEV-2 and SEV-3, SEV-2 suppresses SEV-3.

---

## 8. Reverse Proxy & TLS

### 8.1 Nginx Production Configuration

The Nginx production config (`nginx-prod.conf`, 313 lines) implements:

**TLS Hardening**: TLSv1.2 + TLSv1.3 only. Strong cipher suite (ECDHE + AES-GCM + CHACHA20-POLY1305). HSTS with 1-year max-age, includeSubDomains, preload. OCSP stapling. Session cache (10MB shared, 1-day timeout), session tickets disabled.

**Rate Limiting**: 4 distinct rate zones:
- `api_per_user`: 30 req/s per JWT token (burst 50)
- `api_per_ip`: 10 req/s per IP (burst 20, delayed after 10)
- `web_per_ip`: 5 req/s per IP (burst 30)
- `auth_per_ip`: 1 req/s per IP (burst 5) — strictest for login endpoints

The JWT-based rate key (`$jwt_rate_key`) extracts the Bearer token from the Authorization header using Nginx map, enabling per-user rate limiting rather than per-IP (which would penalize users behind NAT/shared networks).

**Security Headers**: X-Frame-Options DENY, X-Content-Type-Options nosniff, XSS Protection, strict Referrer-Policy, Content-Security-Policy (default-src 'self', frame-ancestors 'none'), Permissions-Policy (geolocation/microphone/camera disabled), server_tokens off.

**Lightweight WAF**: Regex-based blocking of SQL injection patterns (`union select`, `or 1=1`, `--`, `/*`), XSS patterns (`<script`, `javascript:`, `onerror=`), path traversal (`../`), and suspicious file extensions (`.php`, `.asp`, `.aspx`, `.jsp`).

**WebSocket Support**: `/api/v1/ws` proxied with `Upgrade` and `Connection "upgrade"` headers, 1-hour read/send timeouts for long-lived connections.

**Metrics Protection**: `/metrics` endpoint restricted to private IP ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).

**File Upload Routes**: Specific location block for submission/document upload paths with 50MB limit (vs 1MB default for API routes), extended read timeout (120s).

**Static Asset Caching**: 1-year expiry with `Cache-Control: public, immutable` for JS/CSS/images/fonts.

### 8.2 Let's Encrypt Integration

The production Certbot container runs a renewal loop every 12 hours using `--webroot` mode. Nginx serves ACME challenges from `/var/www/certbot`. The `ssl-renew.sh` script handles initial certificate obtainment and integrates with cron for automated renewal.

---

## 9. Database Operations

### 9.1 PostgreSQL Initialization

The `init.sql` script creates 3 database roles:
- `app_user`: Full read/write access for the backend application
- `app_readonly`: SELECT-only access for reporting/analytics queries
- `replicator`: REPLICATION role for streaming replication

Passwords are read from Docker secret files when available, falling back to environment variables. Default privileges ensure all future tables automatically grant appropriate access. Extensions `uuid-ossp` and `pgcrypto` are pre-installed.

### 9.2 Backup Strategy

The `pg_backup.sh` script implements:
- **Schedule**: Daily at 02:00 UTC via cron
- **Format**: `pg_dump --format=custom --compress=9` (maximum compression)
- **Encryption**: Optional AES-256-CBC with PBKDF2 key derivation
- **Integrity**: SHA-256 checksum file generated for each backup
- **Retention**: 30-day automatic pruning of old backups
- **RPO**: 15 minutes in production (continuous WAL archiving supplements daily dumps)

PostgreSQL is configured with `wal_level=replica`, `archive_mode=on`, and `archive_command` copying WAL segments to a dedicated volume — enabling Point-In-Time Recovery between daily full backups.

### 9.3 Secret Rotation

The `rotate-secrets.sh` script supports rotating JWT, database, and Redis secrets with zero downtime:

**JWT rotation**: Implements a dual-key window — the old and new secrets are both valid for a configurable period (default 1800 seconds / 30 minutes), allowing existing tokens to remain valid while new tokens use the new secret. After the window, only the new secret is active.

**Database rotation**: Changes the PostgreSQL password via `ALTER USER`, updates the secret files, and restarts dependent services.

**Redis rotation**: Uses `CONFIG SET requirepass` for live password change without restart, then updates secret files and restarts clients.

---

## 10. Kubernetes Deployment

### 10.1 Helm Chart Architecture

The `infra/k8s/` directory contains a Helm chart with templates for:

- `backend-deployment.yaml`: FastAPI pods with configMapRef for environment variables, secretKeyRef for sensitive values, readiness probe (HTTP GET `/api/v1/health`, 10s period, 5s timeout) and liveness probe (30s period, 10s timeout)
- `backend-hpa.yaml`: HorizontalPodAutoscaler (autoscaling/v2) targeting 70% CPU utilization, scaling from 2 to 8 replicas
- `backend-service.yaml`, `web-service.yaml`: ClusterIP services
- `worker-deployment.yaml`: ARQ worker pods running `arq app.worker.WorkerSettings`
- `web-deployment.yaml`: Nginx SPA pods
- `ingress.yaml`: Nginx Ingress with TLS via cert-manager (`letsencrypt-prod` ClusterIssuer), path-based routing: `/api` → backend, `/ws` → backend, `/` → web
- `pdb.yaml`: PodDisruptionBudgets for backend and web (minAvailable: 1)
- `configmap.yaml`, `secrets.yaml`: Configuration injection

### 10.2 Values per Environment

Default values (`values.yaml`):
- Backend: 2 replicas, 250m/256Mi request, 2 CPU/1Gi limit, HPA enabled (2-8 replicas at 70% CPU)
- Worker: 1 replica, 100m/256Mi request, 1 CPU/512Mi limit
- Web: 2 replicas, 50m/64Mi request, 500m/128Mi limit
- PDB: minAvailable 1 for backend and web
- Ingress: Nginx class with cert-manager, 25MB body size, 100 req/min rate limit

Environment-specific overrides are in `values-staging.yaml` and `values-prod.yaml`.

---

## 11. Health Checking

### 11.1 Application-Level Health

The backend exposes `/api/v1/health` used by:
- Docker HEALTHCHECK in Dockerfile (30s interval, 5s timeout, 3 retries)
- Docker Compose `depends_on: condition: service_healthy`
- Kubernetes readiness/liveness probes
- Nginx health check location (no rate limit)
- CI/CD deploy verification scripts

### 11.2 Infrastructure Health Script

The `healthcheck.sh` script (330 lines) performs 6 comprehensive checks:

1. **API**: HTTP status code + response time from `/api/v1/health`
2. **PostgreSQL**: `pg_isready` + active connection count via `pg_stat_activity`
3. **Redis**: `redis-cli ping` + memory usage from `info memory`
4. **Disk**: Root partition usage (80% warn, 90% critical) + Docker disk usage
5. **Certificates**: TLS cert expiry (30-day warn, 7-day critical) for both Let's Encrypt and direct cert files
6. **Containers**: Verifies all expected containers are running (postgres, redis, nginx, web, worker, backend)

Outputs in 3 formats: human-readable terminal with color-coded status icons, JSON for programmatic consumption, or quiet mode (exit code only, for cron). Overall status: HEALTHY (0), DEGRADED (1), or CRITICAL (2).

---

## 12. Operational Scripts Summary

| Script | Purpose | Key Feature |
|---|---|---|
| `deploy.sh` | Zero-downtime rolling deploy | Auto-rollback on health check failure |
| `blue-green-deploy.sh` | Blue-green swap via Nginx upstream | 30s connection draining, active-env file tracking |
| `healthcheck.sh` | Full infrastructure health audit | 6 checks, JSON/terminal/quiet output |
| `pg_backup.sh` | Daily PostgreSQL backup | AES-256 encryption, SHA-256 integrity, 30-day retention |
| `pg_restore.sh` | Restore from backup | Decryption + pg_restore |
| `restore_drill.sh` | Restore drill testing | Validates backup recoverability |
| `rotate-secrets.sh` | JWT/DB/Redis secret rotation | Dual-key JWT window for zero-downtime |
| `ssl-renew.sh` | TLS certificate renewal | Let's Encrypt webroot mode |
| `backup-s3.sh` | Offsite backup to S3 | Cross-region backup replication |
| `audit_worm_export.sh` | Audit log WORM export | Write-once compliance archival |

---

## 13. Key DevOps Architecture Decisions

**Decision 1 — Docker Compose over Kubernetes for initial deployment**: The primary deployment uses Docker Compose with blue-green scripts. Kubernetes manifests exist as Helm charts for future scaling. This pragmatic approach avoids Kubernetes complexity for a school platform's initial user base while providing a clear migration path.

**Decision 2 — PgBouncer in transaction mode**: Connection pooling via PgBouncer (50 pool, 200 max clients) is present in both staging and production. Transaction mode enables efficient connection sharing across 4+ Uvicorn workers, critical for async SQLAlchemy with connection pool overhead.

**Decision 3 — Blue-green over rolling for zero-downtime**: Blue-green deployment with Nginx upstream switching provides atomic traffic cutover. The 30-second drain period allows in-flight requests to complete. Rollback is instant — rewrite upstream.conf and reload Nginx.

**Decision 4 — Full observability from day one**: Prometheus metrics (30+ collectors), Loki log aggregation, Tempo distributed tracing, and 8 Grafana dashboards are implemented from the start — not as afterthoughts. The three-severity alert model with inhibition rules and per-channel routing demonstrates production-grade operational awareness.

**Decision 5 — Docker secrets over environment variables**: Production secrets use Docker secret files (`/run/secrets/*`) read via `*_FILE` env vars, keeping credentials out of `docker inspect`, process listings, and CI logs. This is a significant security improvement over plain environment variables.

**Decision 6 — Multi-matrix CI testing**: The 6-combination matrix (Python 3.12/3.13 × PostgreSQL 15/16/17) ensures forward compatibility. Combined with Trivy container scanning, pip-audit, Bandit SAST, and k6 load testing, the CI pipeline validates security, correctness, and performance before any merge.

**Decision 7 — WAL archiving + daily dumps for RPO**: Continuous WAL archiving provides 15-minute RPO between daily full backups. The `restore_drill.sh` script validates that backups are actually recoverable — a critical operational practice often overlooked.

---

## 14. Infrastructure Metrics Summary

| Metric | Value |
|---|---|
| Docker Compose services (prod) | 10 |
| CI pipeline jobs | 13 |
| CI test matrix combinations | 6 (2 Python × 3 PostgreSQL) |
| Security scan tools | 3 (Trivy, pip-audit, Bandit) |
| Prometheus alert rules | 12 |
| Loki log alert rules | 5 |
| Grafana dashboards | 8 |
| Application metrics collectors | 30+ |
| Helm chart templates | 10 |
| Operational scripts | 10 |
| Docker secrets (prod) | 9 |
| Nginx rate limit zones | 4 |
| Backup retention | 30 days |
| Trace retention | 30 days |
| Log retention | 30 days |
