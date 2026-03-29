# CI/CD & Infrastructure — Execution Prompts

> **How to use**: Execute each prompt sequentially with an AI coding agent.
> Each prompt is self-contained with full context, expected files, and verification steps.
> **Constraint**: No git commands — user handles git manually.

---

## CI-A1: Pre-commit Hooks Setup

**Goal**: Install pre-commit hooks for local code quality gates.

**Create** `.pre-commit-config.yaml` in the project root with these hooks:
1. `ruff` (lint + format) — rev `v0.8.0`, matching the CI pipeline Ruff version
2. `detect-secrets` — rev `v1.5.0`, with baseline file `.secrets.baseline`
3. `conventional-pre-commit` — rev `v3.6.0`, stage `commit-msg`, allowed prefixes: `feat, fix, chore, docs, style, refactor, perf, test, ci, build`
4. Local hook `alembic-heads` — runs `cd backend && alembic heads | wc -l` and fails if more than 1 head exists. Only triggers on files matching `alembic/versions/.*\.py$`
5. `pre-commit-hooks` — rev `v4.6.0`: `check-added-large-files` (5MB limit), `check-merge-conflict`, `check-yaml`, `end-of-file-fixer`, `trailing-whitespace`

**Add Makefile targets**:
- `hooks-install`: Installs pre-commit and both hooks (default + commit-msg)

**Generate** `.secrets.baseline` by running `detect-secrets scan > .secrets.baseline`.

**Verify**: Run `pre-commit run --all-files` — should pass with no errors on current codebase.

---

## CI-B1: CI Pipeline Hardening (Matrix + Security + Migration Safety)

**Goal**: Upgrade `.github/workflows/ci.yml` with parallel matrix testing, security scanning, and migration safety.

**Read** the existing `ci.yml` at `.github/workflows/ci.yml` and `CICD_INFRASTRUCTURE.md` Category 1 sections 1A, 1B, 1C.

**Changes to existing jobs**:
1. Add `strategy.matrix` to `unit-tests` and `integration-tests` jobs:
   - `python-version: ["3.12", "3.13"]`
   - `postgres-version: ["15", "16", "17"]`
   - `fail-fast: false`
2. Add `actions/cache@v4` for pip (keyed by `python-version + requirements hash`) to ALL Python jobs
3. Add `actions/cache@v4` for npm (keyed by `package-lock.json hash`) to web jobs

**New jobs** (all run in parallel after `lint`):
4. `security-trivy`: Build backend Docker image, scan with `aquasecurity/trivy-action@master`, fail on CRITICAL/HIGH, ignore unfixed
5. `security-pip-audit`: Install pip-audit, run `pip-audit -r backend/requirements.txt --strict`
6. `security-bandit`: Install bandit, run on `backend/app/`, config in pyproject.toml (exclude tests/alembic, skip B101). Upload JSON report as artifact
7. `migration-safety`: Only runs if PR touches `alembic/` files. Spins up PostgreSQL 16-alpine, runs `alembic upgrade head`, then `alembic downgrade base`, then `alembic upgrade head` again. Uses test DATABASE_URL env var

**Add to lint job**:
8. Migration branch conflict check: count `alembic heads`, fail if >1

**Add to `pyproject.toml`**:
```toml
[tool.bandit]
exclude_dirs = ["tests", "alembic"]
skips = ["B101"]
```

**Verify**: The YAML is valid (`python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`). All new jobs have correct `needs` dependencies.

---

## CI-C1: Docker Build Optimization

**Goal**: Optimize the backend Dockerfile with BuildKit features and multi-stage improvements.

**Read** `backend/Dockerfile` and `CICD_INFRASTRUCTURE.md` section 2A.

**Rewrite** `backend/Dockerfile`:
1. Add `# syntax=docker/dockerfile:1.7` as first line
2. Set `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PIP_NO_CACHE_DIR=1`
3. System deps layer: `libpq-dev gcc libffi-dev` + `rm -rf /var/lib/apt/lists/*`
4. Requirements layer with `--mount=type=cache,target=/root/.cache/pip` for pip cache
5. Add `test` stage (FROM base): installs dev deps, copies code, runs `ruff check` + `ruff format --check`
6. `development` stage: dev deps + reload CMD
7. `production` stage: copy code, create non-root `appuser`, healthcheck with httpx, 4 workers

**Verify**: `docker build --target test ./backend` passes. `docker build --target production ./backend` produces a working image. Compare image sizes before/after.

---

## CI-C2: Container Registry + Versioned Tags

**Goal**: Push Docker images to GitHub Container Registry on merge to main.

**Read** `CICD_INFRASTRUCTURE.md` section 2B.

**Add new job** `publish-images` to `.github/workflows/ci.yml`:
1. Runs only on `push` to `main` (not PRs)
2. Needs: `unit-tests`, `integration-tests`, `security-trivy`
3. Permissions: `contents: read`, `packages: write`
4. Steps: checkout → docker/login-action (ghcr.io) → docker/setup-buildx-action → extract SHA tag → build+push backend (production target) → build+push web (production target)
5. Tags: `ghcr.io/<repo>/backend:<sha8>` + `:latest`
6. Cache: `type=gha` for both from and to

**Add SBOM generation** after each image push:
- Use `anchore/sbom-action@v0` with `spdx-json` format
- Upload as artifact

**Create** `.github/workflows/cleanup-images.yml`:
- Scheduled weekly (Sunday 3AM)
- Uses `actions/delete-package-versions@v5`
- Keeps minimum 10 versions, deletes untagged only

**Verify**: YAML validates. The `if` condition correctly gates on `main` push.

---

## CI-D1: PgBouncer Connection Pooling

**Goal**: Add PgBouncer between backend and PostgreSQL for connection pooling.

**Read** `infra/docker-compose.prod.yml` and `CICD_INFRASTRUCTURE.md` section 3C.

**Add** `pgbouncer` service to `infra/docker-compose.prod.yml`:
- Image: `edoburu/pgbouncer:1.22.0`
- Pool mode: `transaction`
- Default pool size: 50, max client connections: 200
- Reserve pool: 5 connections, 3s timeout
- Healthcheck: `pg_isready -h localhost -p 6432`
- Resources: 128MB memory, 0.5 CPU
- Depends on `postgres` (healthy)
- Port: 6432

**Update** backend service `DATABASE_URL` to point to `pgbouncer:6432` instead of `postgres:5432`.

**Also add** PgBouncer to `infra/docker-compose.staging.yml` with same config.

**Update** `backend/app/core/database.py` — add `statement_cache_size=0` to `connect_args` in engine creation (required for PgBouncer transaction pooling with asyncpg):
```python
connect_args={"statement_cache_size": 0}
```

**Verify**: `docker compose -f infra/docker-compose.prod.yml config` validates. The asyncpg connect_args are applied.

---

## CI-D2: Read Replica Setup

**Goal**: Add a PostgreSQL streaming replica and SQLAlchemy read routing.

**Read** `CICD_INFRASTRUCTURE.md` section 3B, `infra/docker-compose.prod.yml`, and `backend/app/core/database.py`.

**Step 1** — Update `infra/postgres/init.sql`:
- Add `CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD :'REPLICATOR_PASSWORD';`
- The password should come from env or secret file

**Step 2** — Add `postgres-replica` service to `infra/docker-compose.prod.yml`:
- Image: `postgres:16-alpine`
- Uses `pg_basebackup` from primary to initialize, then starts in hot standby mode
- Volume: `pgdata-replica`
- Resources: 1GB memory, 1.5 CPU
- Depends on `postgres` (healthy)

**Step 3** — Ensure primary PostgreSQL has `wal_level=replica`, `max_wal_senders=5`, `hot_standby=on` in its command args (some may already be present).

**Step 4** — Create `backend/app/core/db_routing.py`:
- `engine_primary` = async engine from `DATABASE_URL`
- `engine_replica` = async engine from `DATABASE_REPLICA_URL` (fallback to primary if not set)
- `AsyncSessionPrimary` and `AsyncSessionReplica` sessionmakers
- `get_read_db()` dependency for read-only queries
- `get_write_db()` dependency for mutations

**Step 5** — Add `DATABASE_REPLICA_URL` to `backend/app/core/config.py` settings (Optional[str], default None).

**Step 6** — Add `DATABASE_REPLICA_URL` to `.env.example` with comment.

**Verify**: The `get_read_db` and `get_write_db` are importable. The docker-compose config validates. Fallback to primary works when replica URL is not set.

---

## CI-D3: Automated Backups with S3 + Restore Drill

**Goal**: Automated daily backups to S3 with weekly restore verification.

**Read** `CICD_INFRASTRUCTURE.md` section 3A.

**Create** `infra/scripts/backup-s3.sh`:
- Accepts `DB_HOST`, `DB_NAME`, `S3_BUCKET` from environment
- pg_dump + gzip → local file with timestamp
- Upload to S3 with `STANDARD_IA` storage class
- Local cleanup: delete files older than 7 days
- S3 cleanup: delete files older than 30 days
- Logging with timestamps

**Create** `infra/scripts/restore-drill.sh`:
- Downloads latest backup from S3
- Creates temporary database `ecole_restore_drill`
- Restores backup into it
- Validates: table count, total row count, critical tables exist (users, schools, roles, enrollments, courses)
- Cleans up temporary database
- Exits 0 on success, 1 on failure

**Both scripts**: Set executable permissions (`chmod +x`).

**Add Makefile targets**:
- `backup`: Runs backup-s3.sh with env from `.env`
- `restore-drill`: Runs restore-drill.sh
- `backup-status`: Lists latest 5 backups from S3

**Add cron documentation** to `DEPLOYMENT.md`:
```
0 2 * * * /opt/ecole/infra/scripts/backup-s3.sh >> /var/log/ecole-backup.log 2>&1
0 4 * * 0 /opt/ecole/infra/scripts/restore-drill.sh >> /var/log/ecole-restore-drill.log 2>&1
```

**Verify**: Both scripts pass `shellcheck`. The S3 bucket env var is documented in `.env.example`.

---

## CI-E1: OpenTelemetry APM Setup

**Goal**: Add distributed tracing with OpenTelemetry + Grafana Tempo.

**Read** `CICD_INFRASTRUCTURE.md` section 4A, `backend/requirements.txt`, and `infra/docker-compose.monitoring.yml`.

**Step 1** — Add to `backend/requirements.txt`:
```
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0
opentelemetry-instrumentation-fastapi==0.48b0
opentelemetry-instrumentation-sqlalchemy==0.48b0
opentelemetry-instrumentation-redis==0.48b0
opentelemetry-exporter-otlp==1.27.0
```

**Step 2** — Create `backend/app/core/telemetry.py`:
- `setup_telemetry(app, engine)` function
- Creates TracerProvider with resource (service.name=ecole-backend, deployment.environment from settings)
- BatchSpanProcessor → OTLPSpanExporter to `settings.OTEL_EXPORTER_ENDPOINT` (default: `http://tempo:4317`)
- Auto-instruments: FastAPI app, SQLAlchemy engine (`.sync_engine`), Redis
- Only activates when `settings.ENABLE_TRACING` is True

**Step 3** — Add settings to `backend/app/core/config.py`:
- `ENABLE_TRACING: bool = False`
- `OTEL_EXPORTER_ENDPOINT: Optional[str] = None`

**Step 4** — Call `setup_telemetry()` in `backend/app/main.py` startup (guarded by `settings.ENABLE_TRACING`).

**Step 5** — Create `infra/tempo/tempo.yml` with local storage backend, OTLP gRPC receiver on 4317, 30-day retention.

**Step 6** — Add `tempo` service to `infra/docker-compose.monitoring.yml`:
- Image: `grafana/tempo:2.4.0`
- Ports: 4317 (OTLP gRPC), 3200 (query)
- Volume: `tempo-data`

**Step 7** — Add Tempo as Grafana datasource in `infra/grafana/provisioning/datasources/datasources.yml`:
- Type: `tempo`, URL: `http://tempo:3200`
- Configure `tracesToLogs` (Loki linkage) and `serviceMap` (Prometheus linkage)

**Step 8** — Add `ENABLE_TRACING` and `OTEL_EXPORTER_ENDPOINT` to `.env.example`.

**Verify**: `pip install -r backend/requirements.txt` succeeds. The telemetry module imports without errors. Docker-compose monitoring config validates.

---

## CI-E2: Business Metrics + Log-Based Alerting

**Goal**: Add education-specific Prometheus metrics and Loki log alerting rules.

**Read** `CICD_INFRASTRUCTURE.md` sections 4B and 4C.

**Step 1** — Create `backend/app/core/business_metrics.py`:
- Prometheus metrics using `prometheus_client`:
  - `ecole_active_students_total` (Gauge, labels: school_id)
  - `ecole_assignment_submissions_total` (Counter, labels: school_id, status)
  - `ecole_grade_value` (Histogram, labels: school_id, subject, Moroccan 0-20 buckets)
  - `ecole_attendance_rate` (Gauge, labels: school_id)
  - `ecole_billing_payments_total` (Counter, labels: school_id, status)
  - `ecole_billing_revenue_mad` (Counter, labels: school_id, plan)
  - `ecole_timetable_generation_seconds` (Histogram, labels: school_id)

**Step 2** — Instrument service methods to emit metrics:
- `grading_service.grade_submission()` → observe `ecole_grade_value`
- `assignment_service.create_submission()` → increment `ecole_assignment_submissions_total`
- Billing payment handler → increment payment/revenue counters
- These are lightweight `.observe()` / `.inc()` calls — add as single lines at the end of the relevant methods

**Step 3** — Create Grafana dashboard JSON at `infra/grafana/dashboards/business-education.json`:
- 7 panels: active students (time series), submission rate (stacked bar), grade distribution (histogram), attendance trends (line + 90% target), billing collection (pie), revenue per school (bar in MAD), timetable generation p95 (gauge)
- Datasource: Prometheus
- Auto-refresh: 30s
- Time range: last 24h default

**Step 4** — Update Loki config at `infra/loki/loki-config.yml`:
- Add `ruler` section with local storage and alertmanager URL

**Step 5** — Create `infra/loki/rules/ecole-alerts.yml`:
- `HighErrorRate`: >0.5 errors/sec for 2min → SEV-2
- `AuthBruteForce`: >5 failed logins/min from same IP → SEV-1
- `DatabasePoolExhaustion`: QueuePool overflow log → SEV-1
- `PaymentWebhookFailures`: elevated webhook failures for 5min → SEV-2
- `MigrationErrors`: any alembic ERROR log → SEV-1

**Verify**: The metrics module imports correctly. The Grafana dashboard JSON is valid. The Loki rules YAML is valid. Metric names follow Prometheus naming conventions (`ecole_` prefix, `_total` for counters).

---

## CI-F1: Security Hardening (Secrets + WAF + Vulnerability Management)

**Goal**: Implement secret rotation, WAF rules, Dependabot, and SBOM generation.

**Read** `CICD_INFRASTRUCTURE.md` sections 5A, 5B, 5C.

**Step 1** — Create `infra/scripts/rotate-secrets.sh`:
- Accepts argument: `jwt`, `db`, `redis`, or `all`
- JWT rotation: generates new secret with `openssl rand -hex 32`, dual-key acceptance window (30min), then switch to new only
- DB rotation: `ALTER USER` → update secret file → restart backend/worker
- Redis rotation: `CONFIG SET requirepass` → update secret → restart consumers
- Logging to `/var/log/ecole-secret-rotation.log`
- `chmod +x`

**Step 2** — Update `infra/nginx/nginx-prod.conf`:
- Add per-user rate limiting using JWT subject extraction (`map $http_authorization`)
- Add `limit_req_zone` for `$jwt_sub` at 30r/s with burst 50
- Add WAF rules: SQL injection pattern blocking, XSS pattern blocking, path traversal blocking
- Per-endpoint body size limits: 50MB for upload endpoints, 1MB for JSON endpoints
- Add geographic blocking config (commented out, requires GeoIP module)

**Step 3** — Create `.github/dependabot.yml`:
- 4 ecosystems: pip (weekly Monday), npm (weekly Monday), docker (monthly), github-actions (monthly)
- Timezone: `Africa/Casablanca`
- PR limit: 10 per ecosystem
- Grouped updates for security and database packages
- Reviewer: nawfalrazouk

**Step 4** — Create `.github/workflows/dependabot-automerge.yml`:
- Triggers on `pull_request` from dependabot[bot]
- Auto-merges patch version updates that pass CI
- Uses `gh pr merge --auto --squash`

**Step 5** — Add Makefile targets:
- `rotate-jwt`, `rotate-db`, `rotate-redis`, `rotate-all`: Call rotate-secrets.sh with appropriate args

**Verify**: `shellcheck infra/scripts/rotate-secrets.sh` passes. Nginx config validates (`nginx -t` syntax). Dependabot YAML is valid. Auto-merge workflow has correct permissions (`contents: write`, `pull-requests: write`).

---

## CI-F2: Blue-Green Deployment

**Goal**: Implement blue-green deployment with instant rollback.

**Read** `CICD_INFRASTRUCTURE.md` section 2C.

**Step 1** — Create two environment compose files:
- `infra/docker-compose.blue.yml`: Backend + worker with container names `ecole-backend-blue`, `ecole-worker-blue`, using shared postgres/redis/pgbouncer
- `infra/docker-compose.green.yml`: Same structure with `ecole-backend-green`, `ecole-worker-green`
- Both reference `IMAGE_TAG` env var for the image version
- Both share the same `ecole-network` external network

**Step 2** — Create `infra/scripts/blue-green-deploy.sh`:
- Reads active environment from `/opt/ecole/active-env` (default: blue)
- Determines next environment (opposite of active)
- Pulls new images → starts next env → runs migrations → health check (60s timeout) → switches Nginx upstream → drains old env (30s) → stops old env
- On health check failure: stops next env and exits 1 (active env untouched)
- `--rollback` flag: immediately switches Nginx back to the other env

**Step 3** — Create `infra/nginx/upstream.conf`:
- Contains `upstream backend_active { server ecole-backend-blue:8000; }`
- Included by nginx-prod.conf via `include /etc/nginx/conf.d/upstream.conf;`

**Step 4** — Update `infra/nginx/nginx-prod.conf` to use `backend_active` upstream and include the upstream.conf.

**Step 5** — Add Makefile targets:
- `deploy-blue-green`: Runs blue-green-deploy.sh with IMAGE_TAG
- `deploy-rollback`: Runs blue-green-deploy.sh --rollback
- `deploy-status`: Shows which environment is active

**Verify**: Both compose files validate. The deploy script passes `shellcheck`. Nginx config with the include validates.

---

## CI-G1: Developer Onboarding + Documentation

**Goal**: One-command dev setup and auto-generated API documentation.

**Read** `CICD_INFRASTRUCTURE.md` sections 6A and 6C.

**Step 1** — Create `backend/app/scripts/seed_demo.py`:
- Async script that connects to the database
- Creates 1 demo school: "Lycée Mohammed V", code "LMV-001", city "Casablanca", region "Casablanca-Settat", timezone "Africa/Casablanca", grading_scale "0-20"
- Creates users: 1 admin (admin@ecole-demo.ma / Demo1234!), 3 teachers, 2 parents, 5 students — all with appropriate roles
- Creates 3 classes: "1ère Année Bac Sciences", "2ème Année Bac Sciences", "Tronc Commun Sciences"
- Creates 5 courses: Mathématiques, Physique-Chimie, Français, Arabe, Informatique
- Creates sample enrollments linking students to classes
- Creates sample teacher assignments linking teachers to classes/courses
- Creates a billing plan: "Plan Établissement", 500 MAD/month
- Uses existing SQLAlchemy models and follows the 3-tier architecture (can use repositories directly since this is a script)
- Idempotent: checks if demo school exists before creating

**Step 2** — Add Makefile targets:
- `dev-init`: Copy .env.example → .env if missing, docker-compose build, up postgres+redis, wait 5s, alembic upgrade head, run seed_demo.py, up all services, print URLs
- `dev-reset`: docker-compose down -v --remove-orphans, rm .env, print instructions
- `seed-demo`: Just runs the seed script (for re-seeding)

**Step 3** — Create `.github/workflows/docs.yml`:
- Triggers on push to main when `backend/app/**` changes
- Exports OpenAPI spec from FastAPI app
- Generates static Redoc site with `@redocly/cli`
- Deploys to GitHub Pages

**Step 4** — Add Makefile target:
- `docs`: Generates OpenAPI spec + Redoc HTML locally
- `docs-schema`: Generates ER diagram with eralchemy2

**Step 5** — Update `DEPLOYMENT.md` with new Makefile targets and developer onboarding section.

**Verify**: `python -c "from app.scripts.seed_demo import ..."` imports without error. The docs workflow YAML validates. All new Makefile targets have help comments (`## description`).

---

## Execution Summary

| Prompt | Focus | Est. Time | Priority |
|--------|-------|-----------|----------|
| CI-A1 | Pre-commit hooks | 15 min | High |
| CI-B1 | CI pipeline hardening | 30 min | High |
| CI-C1 | Docker build optimization | 20 min | Medium |
| CI-C2 | Container registry | 20 min | Medium |
| CI-D1 | PgBouncer | 15 min | High |
| CI-D2 | Read replica | 25 min | Medium |
| CI-D3 | Automated backups | 20 min | High |
| CI-E1 | OpenTelemetry APM | 25 min | Medium |
| CI-E2 | Business metrics + log alerts | 30 min | Medium |
| CI-F1 | Security hardening | 30 min | High |
| CI-F2 | Blue-green deployment | 25 min | Medium |
| CI-G1 | Dev onboarding + docs | 25 min | Medium |

**Total**: ~12 prompts, ~4.5 hours estimated execution time.
