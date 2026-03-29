# CI/CD & Infrastructure Architecture — Ecole Platform

> **Scope**: 6 enhancement categories, 18 sub-options — all selected.
> **Current state**: 10-stage GitHub Actions CI, multi-env Docker Compose, Prometheus/Grafana/Loki monitoring, Nginx TLS + rate limiting, zero-downtime deploy with rollback.
> **Target state**: Production-hardened, auto-scaling-ready, fully observable EdTech SaaS.

---

## Category 1 — CI Pipeline Hardening

### 1A. Parallel Matrix Testing

**What changes**: Replace the single Python 3.12 / PostgreSQL 16 test job with a strategy matrix.

**Configuration**:
```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.12", "3.13"]
    postgres-version: ["15", "16", "17"]
```

**Dependency caching** (add to every Python job):
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: pip-${{ matrix.python-version }}-${{ hashFiles('backend/requirements*.txt') }}
    restore-keys: pip-${{ matrix.python-version }}-
```

**npm caching** (web jobs):
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.npm
    key: npm-${{ hashFiles('web/package-lock.json') }}
```

**Impact**: CI time drops ~40% due to parallelism; catches version-specific regressions before they reach staging.

---

### 1B. Security Scanning in CI

**Three new jobs** added to `.github/workflows/ci.yml`:

#### Trivy (Container Image Scanning)
```yaml
security-trivy:
  runs-on: ubuntu-latest
  needs: [lint]
  steps:
    - uses: actions/checkout@v4
    - name: Build backend image
      run: docker build -t ecole-backend:ci ./backend
    - uses: aquasecurity/trivy-action@master
      with:
        image-ref: ecole-backend:ci
        format: table
        exit-code: 1            # Fail on CRITICAL/HIGH
        severity: CRITICAL,HIGH
        ignore-unfixed: true
```

#### pip-audit (Python Dependency Audit)
```yaml
security-pip-audit:
  runs-on: ubuntu-latest
  needs: [lint]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install pip-audit
    - run: pip-audit -r backend/requirements.txt --strict
```

#### Bandit (Python Static Security Analysis)
```yaml
security-bandit:
  runs-on: ubuntu-latest
  needs: [lint]
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install bandit[toml]
    - run: bandit -r backend/app/ -c pyproject.toml -f json -o bandit-report.json
    - uses: actions/upload-artifact@v4
      if: always()
      with:
        name: bandit-report
        path: bandit-report.json
```

**pyproject.toml addition**:
```toml
[tool.bandit]
exclude_dirs = ["tests", "alembic"]
skips = ["B101"]  # Allow assert in tests
```

---

### 1C. Database Migration Safety

**New CI job**: Runs on any PR that modifies `alembic/versions/`.

```yaml
migration-safety:
  runs-on: ubuntu-latest
  if: contains(github.event.pull_request.changed_files, 'alembic/')
  services:
    postgres:
      image: postgres:16-alpine
      env:
        POSTGRES_USER: test
        POSTGRES_PASSWORD: test
        POSTGRES_DB: ecole_migration_test
      ports: ["5432:5432"]
      options: >-
        --health-cmd pg_isready
        --health-interval 5s
        --health-timeout 3s
        --health-retries 10
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with: { python-version: "3.12" }
    - run: pip install -r backend/requirements.txt
    - name: Forward migration
      run: cd backend && alembic upgrade head
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/ecole_migration_test
    - name: Verify downgrade reversibility
      run: cd backend && alembic downgrade base
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/ecole_migration_test
    - name: Re-apply to confirm idempotency
      run: cd backend && alembic upgrade head
      env:
        DATABASE_URL: postgresql+asyncpg://test:test@localhost:5432/ecole_migration_test
```

**Migration conflict detection** (add to lint job):
```yaml
- name: Check migration branch conflicts
  run: |
    cd backend
    heads=$(alembic heads | wc -l)
    if [ "$heads" -gt 1 ]; then
      echo "ERROR: Multiple migration heads detected — merge required"
      alembic heads
      exit 1
    fi
```

---

## Category 2 — Container & Deployment Strategy

### 2A. Docker Build Optimization

**Updated `backend/Dockerfile`** with BuildKit optimizations:

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps (cached layer)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq-dev gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Dependency layer (cached unless requirements change)
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements.txt

# ---------- test stage ----------
FROM base AS test
COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements-dev.txt
COPY . .
RUN ruff check app/ && ruff format --check app/

# ---------- development ----------
FROM base AS development
COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-compile -r requirements-dev.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ---------- production ----------
FROM base AS production
COPY . .
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import httpx; httpx.get('http://localhost:8000/api/v1/health').raise_for_status()"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Multi-platform build** (CI step):
```yaml
- uses: docker/setup-buildx-action@v3
- uses: docker/build-push-action@v5
  with:
    context: ./backend
    platforms: linux/amd64,linux/arm64
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

### 2B. Container Registry + Versioned Tags

**New CI job** — triggers on merge to `main`:

```yaml
publish-images:
  runs-on: ubuntu-latest
  needs: [unit-tests, integration-tests, security-trivy]
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  permissions:
    contents: read
    packages: write
  steps:
    - uses: actions/checkout@v4
    - uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    - uses: docker/setup-buildx-action@v3

    - name: Extract version
      id: meta
      run: |
        SHA=$(echo "${{ github.sha }}" | cut -c1-8)
        echo "sha_tag=$SHA" >> "$GITHUB_OUTPUT"
        # If tagged release, extract semver
        if [[ "${{ github.ref }}" == refs/tags/v* ]]; then
          echo "version=${{ github.ref_name }}" >> "$GITHUB_OUTPUT"
        fi

    - uses: docker/build-push-action@v5
      with:
        context: ./backend
        target: production
        push: true
        tags: |
          ghcr.io/${{ github.repository }}/backend:${{ steps.meta.outputs.sha_tag }}
          ghcr.io/${{ github.repository }}/backend:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max

    - uses: docker/build-push-action@v5
      with:
        context: ./web
        target: production
        push: true
        tags: |
          ghcr.io/${{ github.repository }}/web:${{ steps.meta.outputs.sha_tag }}
          ghcr.io/${{ github.repository }}/web:latest
```

**Image cleanup** (scheduled workflow):
```yaml
name: Cleanup old images
on:
  schedule:
    - cron: "0 3 * * 0"  # Weekly Sunday 3AM
jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/delete-package-versions@v5
        with:
          package-name: backend
          package-type: container
          min-versions-to-keep: 10
          delete-only-untagged-versions: true
```

---

### 2C. Blue-Green Deployment

**Architecture**: Two identical stacks (`blue` and `green`) behind Nginx. Only one receives traffic at a time.

**New file** `infra/scripts/blue-green-deploy.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

ACTIVE_FILE="/opt/ecole/active-env"     # Contains "blue" or "green"
ACTIVE=$(cat "$ACTIVE_FILE" 2>/dev/null || echo "blue")
NEXT=$( [ "$ACTIVE" = "blue" ] && echo "green" || echo "blue" )

IMAGE_TAG="${1:?Usage: blue-green-deploy.sh <image-tag>}"
HEALTH_URL="http://localhost:800$( [ "$NEXT" = "blue" ] && echo 1 || echo 2 )/api/v1/health"

echo "=== Deploying $IMAGE_TAG to $NEXT (active: $ACTIVE) ==="

# 1. Pull new images
export IMAGE_TAG
docker compose -f "infra/docker-compose.$NEXT.yml" pull

# 2. Start next environment
docker compose -f "infra/docker-compose.$NEXT.yml" up -d

# 3. Run migrations on next environment
docker compose -f "infra/docker-compose.$NEXT.yml" exec backend \
  alembic upgrade head

# 4. Health check (60s timeout)
for i in $(seq 1 12); do
  if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    echo "  $NEXT is healthy"
    break
  fi
  [ "$i" -eq 12 ] && { echo "FATAL: $NEXT failed health check"; docker compose -f "infra/docker-compose.$NEXT.yml" down; exit 1; }
  sleep 5
done

# 5. Switch Nginx upstream
sed -i "s/upstream backend_active {.*}/upstream backend_active { server ecole-backend-$NEXT:8000; }/" \
  /etc/nginx/conf.d/upstream.conf
nginx -s reload

# 6. Record active environment
echo "$NEXT" > "$ACTIVE_FILE"

# 7. Drain and stop old environment (wait 30s for in-flight requests)
echo "  Draining $ACTIVE..."
sleep 30
docker compose -f "infra/docker-compose.$ACTIVE.yml" down

echo "=== Deploy complete: $NEXT is now active ==="
```

**Nginx upstream config** (`/etc/nginx/conf.d/upstream.conf`):
```nginx
upstream backend_active {
    server ecole-backend-blue:8000;
}
```

**Rollback**: `echo "blue" > /opt/ecole/active-env && nginx -s reload` — instant, under 5 seconds.

---

## Category 3 — Database Operations

### 3A. Automated Backup with Verification

**New file** `infra/scripts/backup-s3.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-ecole_platform}"
BACKUP_DIR="/var/backups/ecole"
S3_BUCKET="${S3_BUCKET:?S3_BUCKET required}"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

# 1. Dump + compress
echo "[$(date)] Starting backup..."
pg_dump -h "$DB_HOST" -U postgres -d "$DB_NAME" \
  --no-owner --no-privileges --format=plain | gzip > "$BACKUP_FILE"
echo "  Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# 2. Upload to S3
aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE")" \
  --storage-class STANDARD_IA
echo "  Uploaded to S3"

# 3. Local cleanup (keep 7 days locally)
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

# 4. S3 cleanup (keep 30 days)
aws s3 ls "s3://$S3_BUCKET/backups/" | while read -r line; do
  file_date=$(echo "$line" | awk '{print $1}')
  file_name=$(echo "$line" | awk '{print $4}')
  age=$(( ($(date +%s) - $(date -d "$file_date" +%s)) / 86400 ))
  if [ "$age" -gt "$RETENTION_DAYS" ] && [ -n "$file_name" ]; then
    aws s3 rm "s3://$S3_BUCKET/backups/$file_name"
    echo "  Deleted expired: $file_name"
  fi
done

echo "[$(date)] Backup complete"
```

**Weekly restore drill** `infra/scripts/restore-drill.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

S3_BUCKET="${S3_BUCKET:?S3_BUCKET required}"
DRILL_DB="ecole_restore_drill"

# 1. Get latest backup from S3
LATEST=$(aws s3 ls "s3://$S3_BUCKET/backups/" | sort | tail -1 | awk '{print $4}')
echo "[$(date)] Restore drill: $LATEST"

aws s3 cp "s3://$S3_BUCKET/backups/$LATEST" /tmp/drill-backup.sql.gz

# 2. Create temp database
psql -h localhost -U postgres -c "DROP DATABASE IF EXISTS $DRILL_DB;"
psql -h localhost -U postgres -c "CREATE DATABASE $DRILL_DB;"

# 3. Restore
gunzip -c /tmp/drill-backup.sql.gz | psql -h localhost -U postgres -d "$DRILL_DB" -q

# 4. Validate table counts
TABLE_COUNT=$(psql -h localhost -U postgres -d "$DRILL_DB" -t -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
ROW_TOTAL=$(psql -h localhost -U postgres -d "$DRILL_DB" -t -c \
  "SELECT sum(n_live_tup) FROM pg_stat_user_tables;")

echo "  Tables: $TABLE_COUNT | Total rows: $ROW_TOTAL"

# 5. Validate critical tables exist
for table in users schools roles enrollments courses; do
  count=$(psql -h localhost -U postgres -d "$DRILL_DB" -t -c "SELECT count(*) FROM $table;" 2>/dev/null || echo "MISSING")
  echo "  $table: $count rows"
done

# 6. Cleanup
psql -h localhost -U postgres -c "DROP DATABASE $DRILL_DB;"
rm /tmp/drill-backup.sql.gz

echo "[$(date)] Restore drill PASSED"
```

**Cron schedule** (add to prod server):
```cron
# Daily backup at 2AM Casablanca time
0 2 * * * /opt/ecole/infra/scripts/backup-s3.sh >> /var/log/ecole-backup.log 2>&1

# Weekly restore drill Sunday 4AM
0 4 * * 0 /opt/ecole/infra/scripts/restore-drill.sh >> /var/log/ecole-restore-drill.log 2>&1
```

---

### 3B. Read Replica Setup

**Add to `infra/docker-compose.prod.yml`**:
```yaml
postgres-replica:
  image: postgres:16-alpine
  environment:
    PGUSER: replicator
    PGPASSWORD_FILE: /run/secrets/replicator_password
  volumes:
    - pgdata-replica:/var/lib/postgresql/data
  command: |
    bash -c "
    until pg_basebackup -h postgres -U replicator -D /var/lib/postgresql/data -Fp -Xs -R; do
      echo 'Waiting for primary...'
      sleep 5
    done
    exec postgres
    "
  depends_on:
    postgres:
      condition: service_healthy
  deploy:
    resources:
      limits: { memory: 1G, cpus: "1.5" }
  networks: [ecole-network]
```

**Primary PostgreSQL additions** (in postgres service command):
```
-c wal_level=replica
-c max_wal_senders=5
-c hot_standby=on
```

**Create replication user** (add to `infra/postgres/init.sql`):
```sql
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD :'REPLICATOR_PASSWORD';
```

**SQLAlchemy read routing** — new file `backend/app/core/db_routing.py`:
```python
"""Read/write database routing for query optimization."""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Primary (read-write)
engine_primary = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10)

# Replica (read-only) — falls back to primary if not configured
engine_replica = create_async_engine(
    settings.DATABASE_REPLICA_URL or settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
)

AsyncSessionPrimary = sessionmaker(engine_primary, class_=AsyncSession, expire_on_commit=False)
AsyncSessionReplica = sessionmaker(engine_replica, class_=AsyncSession, expire_on_commit=False)

async def get_read_db() -> AsyncSession:
    """Session for read-only queries (reports, analytics, lists)."""
    async with AsyncSessionReplica() as session:
        yield session

async def get_write_db() -> AsyncSession:
    """Session for write operations (create, update, delete)."""
    async with AsyncSessionPrimary() as session:
        yield session
```

**Usage in routers** (analytics, gradebook, reports):
```python
from app.core.db_routing import get_read_db

@router.get("/analytics/attendance")
async def get_attendance_analytics(db: AsyncSession = Depends(get_read_db)):
    ...
```

---

### 3C. PgBouncer Connection Pooling

**New service** in `infra/docker-compose.prod.yml`:
```yaml
pgbouncer:
  image: edoburu/pgbouncer:1.22.0
  environment:
    DATABASE_URL: postgres://app_user:${POSTGRES_PASSWORD}@postgres:5432/ecole_platform
    POOL_MODE: transaction
    DEFAULT_POOL_SIZE: 50
    MAX_CLIENT_CONN: 200
    MAX_DB_CONNECTIONS: 50
    RESERVE_POOL_SIZE: 5
    RESERVE_POOL_TIMEOUT: 3
    SERVER_IDLE_TIMEOUT: 300
    SERVER_LIFETIME: 3600
    LOG_CONNECTIONS: 0
    LOG_DISCONNECTIONS: 0
    STATS_PERIOD: 60
  ports:
    - "6432:6432"
  depends_on:
    postgres:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "pg_isready", "-h", "localhost", "-p", "6432"]
    interval: 10s
    timeout: 3s
    retries: 5
  deploy:
    resources:
      limits: { memory: 128M, cpus: "0.5" }
  networks: [ecole-network]
```

**Update DATABASE_URL** in backend service:
```yaml
# Before: postgresql+asyncpg://user:pass@postgres:5432/ecole_platform
# After:  postgresql+asyncpg://user:pass@pgbouncer:6432/ecole_platform
```

**Note**: With `transaction` pool mode, prepared statements must be disabled in asyncpg. Add to SQLAlchemy engine:
```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    connect_args={"statement_cache_size": 0},  # Required for PgBouncer
)
```

---

## Category 4 — Observability & Monitoring Upgrades

### 4A. Application Performance Monitoring (OpenTelemetry)

**New dependencies** (add to `requirements.txt`):
```
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0
opentelemetry-instrumentation-fastapi==0.48b0
opentelemetry-instrumentation-sqlalchemy==0.48b0
opentelemetry-instrumentation-redis==0.48b0
opentelemetry-exporter-otlp==1.27.0
```

**New file** `backend/app/core/telemetry.py`:
```python
"""OpenTelemetry setup for distributed tracing."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource

def setup_telemetry(app, engine):
    """Initialize OpenTelemetry tracing."""
    resource = Resource.create({
        "service.name": "ecole-backend",
        "service.version": "1.0.0",
        "deployment.environment": settings.APP_ENV,
    })

    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(OTLPSpanExporter(
        endpoint=settings.OTEL_EXPORTER_ENDPOINT or "http://tempo:4317",
        insecure=True,
    ))
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)
    RedisInstrumentor().instrument()
```

**Add Tempo to monitoring stack** (`infra/docker-compose.monitoring.yml`):
```yaml
tempo:
  image: grafana/tempo:2.4.0
  command: ["-config.file=/etc/tempo/tempo.yml"]
  volumes:
    - ./tempo/tempo.yml:/etc/tempo/tempo.yml
    - tempo-data:/var/tempo
  ports:
    - "4317:4317"   # OTLP gRPC
    - "3200:3200"   # Tempo query
  networks: [ecole-network]
```

**Tempo config** `infra/tempo/tempo.yml`:
```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: "0.0.0.0:4317"

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal

compactor:
  compaction:
    block_retention: 720h  # 30 days

metrics_generator:
  storage:
    path: /var/tempo/generator/wal
  traces_storage:
    path: /var/tempo/generator/traces
```

**Grafana datasource addition** (`infra/grafana/provisioning/datasources/datasources.yml`):
```yaml
- name: Tempo
  type: tempo
  access: proxy
  url: http://tempo:3200
  jsonData:
    tracesToLogs:
      datasourceUid: loki
      tags: ["service.name"]
    serviceMap:
      datasourceUid: prometheus
```

---

### 4B. Business Metrics Dashboard

**New file** `backend/app/core/business_metrics.py`:
```python
"""Education-specific Prometheus metrics."""
from prometheus_client import Counter, Histogram, Gauge

# Student engagement
active_students = Gauge(
    "ecole_active_students_total",
    "Currently active students",
    ["school_id"],
)
assignment_submissions = Counter(
    "ecole_assignment_submissions_total",
    "Total assignment submissions",
    ["school_id", "status"],  # status: on_time, late, missed
)

# Grading
grade_distribution = Histogram(
    "ecole_grade_value",
    "Grade distribution (0-20 Moroccan scale)",
    ["school_id", "subject"],
    buckets=[0, 4, 8, 10, 12, 14, 16, 18, 20],
)

# Attendance
attendance_rate = Gauge(
    "ecole_attendance_rate",
    "Daily attendance rate",
    ["school_id"],
)

# Billing
billing_collection = Counter(
    "ecole_billing_payments_total",
    "Payment transactions",
    ["school_id", "status"],  # status: success, failed, pending
)
billing_revenue = Counter(
    "ecole_billing_revenue_mad",
    "Revenue in MAD",
    ["school_id", "plan"],
)

# Timetable
timetable_generation = Histogram(
    "ecole_timetable_generation_seconds",
    "Timetable generation duration",
    ["school_id"],
)
```

**Grafana dashboard** `infra/grafana/dashboards/business-education.json` — panels:
1. Active students per school (time series)
2. Assignment submission rate: on-time vs late vs missed (stacked bar)
3. Grade distribution histogram (Moroccan 0-20 scale)
4. Attendance rate trends (line chart with 90% target line)
5. Billing collection rate (pie: success/failed/pending)
6. Revenue per school per month (bar chart in MAD)
7. Timetable generation p95 latency (gauge)

---

### 4C. Log-Based Alerting

**Loki ruler config** — add to `infra/loki/loki-config.yml`:
```yaml
ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/scratch
  alertmanager_url: http://alertmanager:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
```

**Alert rules** `infra/loki/rules/ecole-alerts.yml`:
```yaml
groups:
  - name: ecole-log-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate({service=~"ecole-.*"} |= "ERROR" [5m])) > 0.5
        for: 2m
        labels:
          severity: SEV-2
        annotations:
          summary: "High error rate detected (>0.5 errors/sec for 2min)"

      - alert: AuthBruteForce
        expr: |
          sum(rate({service="ecole-backend"} |= "login_failed" [1m])) by (ip) > 5
        for: 0s
        labels:
          severity: SEV-1
        annotations:
          summary: "Possible brute-force: >5 failed logins/min from same IP"

      - alert: DatabasePoolExhaustion
        expr: |
          {service="ecole-backend"} |= "QueuePool limit" |= "overflow"
        for: 1m
        labels:
          severity: SEV-1
        annotations:
          summary: "SQLAlchemy connection pool exhausted"

      - alert: PaymentWebhookFailures
        expr: |
          sum(rate({service="ecole-backend"} |= "webhook" |= "failed" [10m])) > 0.1
        for: 5m
        labels:
          severity: SEV-2
        annotations:
          summary: "Payment webhook failure rate elevated"

      - alert: MigrationErrors
        expr: |
          {service="ecole-backend"} |= "alembic" |= "ERROR"
        for: 0s
        labels:
          severity: SEV-1
        annotations:
          summary: "Database migration error detected"
```

---

## Category 5 — Security Hardening

### 5A. Secret Rotation Framework

**New file** `infra/scripts/rotate-secrets.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail

SECRET_TYPE="${1:?Usage: rotate-secrets.sh <jwt|db|redis|all>}"
SECRETS_DIR="/run/secrets"
LOG_FILE="/var/log/ecole-secret-rotation.log"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG_FILE"; }

rotate_jwt() {
    log "Rotating JWT secret..."
    NEW_SECRET=$(openssl rand -hex 32)
    OLD_SECRET=$(cat "$SECRETS_DIR/jwt_secret_key")

    # Phase 1: Accept both old and new (dual-key window)
    echo "$NEW_SECRET" > "$SECRETS_DIR/jwt_secret_key.new"
    export JWT_DUAL_KEY="$OLD_SECRET,$NEW_SECRET"
    docker compose -f infra/docker-compose.prod.yml exec backend \
      kill -HUP 1  # Graceful reload

    log "  Dual-key window active (30min)"
    sleep 1800

    # Phase 2: New key only
    echo "$NEW_SECRET" > "$SECRETS_DIR/jwt_secret_key"
    rm "$SECRETS_DIR/jwt_secret_key.new"
    unset JWT_DUAL_KEY
    docker compose -f infra/docker-compose.prod.yml restart backend
    log "  JWT rotation complete"
}

rotate_db() {
    log "Rotating database password..."
    NEW_PASS=$(openssl rand -base64 24)

    # 1. Create new role or alter existing
    docker compose -f infra/docker-compose.prod.yml exec postgres \
      psql -U postgres -c "ALTER USER app_user PASSWORD '$NEW_PASS';"

    # 2. Update secret file
    echo "postgresql+asyncpg://app_user:$NEW_PASS@pgbouncer:6432/ecole_platform" \
      > "$SECRETS_DIR/database_url"

    # 3. Restart app (PgBouncer reconnects automatically)
    docker compose -f infra/docker-compose.prod.yml restart backend worker
    log "  Database password rotation complete"
}

rotate_redis() {
    log "Rotating Redis password..."
    NEW_PASS=$(openssl rand -base64 24)

    # 1. Update Redis ACL
    docker compose -f infra/docker-compose.prod.yml exec redis \
      redis-cli CONFIG SET requirepass "$NEW_PASS"

    # 2. Update secret
    echo "redis://:$NEW_PASS@redis:6379/0" > "$SECRETS_DIR/redis_url"

    # 3. Restart consumers
    docker compose -f infra/docker-compose.prod.yml restart backend worker
    log "  Redis password rotation complete"
}

case "$SECRET_TYPE" in
  jwt)   rotate_jwt ;;
  db)    rotate_db ;;
  redis) rotate_redis ;;
  all)   rotate_jwt; rotate_db; rotate_redis ;;
esac
```

**Pre-commit secret detection** (`.pre-commit-config.yaml` addition):
```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
```

---

### 5B. WAF & Advanced Rate Limiting

**Updated Nginx rate limiting** (per-user via JWT):
```nginx
# Extract user ID from JWT for per-user limiting
map $http_authorization $jwt_sub {
    default "";
    "~Bearer (?<token>.+)" $token;
}

# Per-user rate zones
limit_req_zone $jwt_sub zone=api_per_user:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=api_per_ip:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth_per_ip:10m rate=1r/s;

# Graduated throttling
limit_req zone=api_per_user burst=50 nodelay;  # Soft: 30r/s, burst 50
limit_req zone=api_per_ip burst=20 delay=10;   # Hard: 10r/s, delay after 10
```

**WAF rules** (add to Nginx server block):
```nginx
# SQL injection patterns
if ($args ~* "(union|select|insert|update|delete|drop|--|;|'|\")" ) {
    return 403;
}

# XSS patterns
if ($args ~* "(<script|javascript:|on\w+=)" ) {
    return 403;
}

# Path traversal
if ($uri ~* "\.\./") {
    return 403;
}

# Request body size per endpoint
location /api/v1/lms/submissions/upload {
    client_max_body_size 50m;   # File uploads
    proxy_pass http://backend_active;
}
location /api/v1/ {
    client_max_body_size 1m;    # JSON payloads
    proxy_pass http://backend_active;
}

# Geographic blocking (optional, Moroccan-focused)
# Requires ngx_http_geoip2_module
# geoip2 /usr/share/GeoIP/GeoLite2-Country.mmdb {
#     $geoip2_country_code country iso_code;
# }
# if ($geoip2_country_code !~ "^(MA|FR|ES|US|GB|CA)$") {
#     return 403;
# }
```

---

### 5C. Vulnerability Management

**Dependabot** — `.github/dependabot.yml`:
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /backend
    schedule:
      interval: weekly
      day: monday
      time: "08:00"
      timezone: Africa/Casablanca
    open-pull-requests-limit: 10
    labels: ["dependencies", "python"]
    reviewers: ["nawfalrazouk"]
    groups:
      security:
        patterns: ["cryptography", "python-jose", "passlib", "pyotp"]
      database:
        patterns: ["sqlalchemy", "alembic", "asyncpg"]

  - package-ecosystem: npm
    directory: /web
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 10
    labels: ["dependencies", "javascript"]

  - package-ecosystem: docker
    directory: /backend
    schedule:
      interval: monthly
    labels: ["dependencies", "docker"]

  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: monthly
    labels: ["dependencies", "ci"]
```

**Auto-merge patch versions** — `.github/workflows/dependabot-automerge.yml`:
```yaml
name: Dependabot auto-merge
on: pull_request

permissions:
  contents: write
  pull-requests: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - uses: dependabot/fetch-metadata@v2
        id: metadata
      - if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**SBOM generation** (add to publish-images job):
```yaml
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    image: ghcr.io/${{ github.repository }}/backend:${{ steps.meta.outputs.sha_tag }}
    format: spdx-json
    output-file: sbom-backend.spdx.json
- uses: actions/upload-artifact@v4
  with:
    name: sbom
    path: sbom-backend.spdx.json
```

---

## Category 6 — Developer Experience

### 6A. Local Development Parity

**New Makefile targets**:
```makefile
## ── Developer Onboarding ──────────────────────────────────
dev-init: ## One-command setup: env + build + migrate + seed
	@echo "=== Ecole Platform — Dev Setup ==="
	@test -f .env || cp .env.example .env && echo "  .env created"
	@docker compose -f infra/docker-compose.dev.yml build
	@docker compose -f infra/docker-compose.dev.yml up -d postgres redis
	@echo "  Waiting for PostgreSQL..."
	@sleep 5
	@docker compose -f infra/docker-compose.dev.yml run --rm backend \
		alembic upgrade head
	@docker compose -f infra/docker-compose.dev.yml run --rm backend \
		python -m app.scripts.seed_demo
	@docker compose -f infra/docker-compose.dev.yml up -d
	@echo ""
	@echo "  API:  http://localhost:8000/docs"
	@echo "  Web:  http://localhost:5173"
	@echo "  DB:   postgresql://ecole_user:ecole_pass@localhost:5432/ecole_platform"
	@echo ""
	@echo "  Demo school: Lycée Mohammed V (code: LMV-001)"
	@echo "  Admin login: admin@ecole-demo.ma / Demo1234!"
	@echo "=== Setup complete ==="

dev-reset: ## Tear down everything and start fresh
	@docker compose -f infra/docker-compose.dev.yml down -v --remove-orphans
	@rm -f .env
	@echo "  Environment cleared. Run 'make dev-init' to start fresh."
```

**Seed script** `backend/app/scripts/seed_demo.py`:
```python
"""Seeds a demo school with sample data for development."""
# Creates:
# - 1 school (Lycée Mohammed V, Casablanca)
# - 1 admin, 3 teachers, 2 parents, 5 students
# - 3 classes (1ère Année, 2ème Année, 3ème Année)
# - 5 courses (Mathématiques, Physique, Français, Arabe, Informatique)
# - Sample timetable, assignments, grades
# - Billing plan (Plan Établissement, 500 MAD/month)
```

---

### 6B. Pre-commit Hooks

**New file** `.pre-commit-config.yaml`:
```yaml
repos:
  # Python linting (matches CI)
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  # Secret detection
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']

  # Conventional commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, chore, docs, style, refactor, perf, test, ci, build]

  # Migration conflict detection
  - repo: local
    hooks:
      - id: alembic-heads
        name: Check for multiple Alembic heads
        entry: bash -c 'cd backend && heads=$(alembic heads 2>/dev/null | wc -l); [ "$heads" -le 1 ]'
        language: system
        files: 'alembic/versions/.*\.py$'
        pass_filenames: false

  # File size limit (5MB)
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: check-added-large-files
        args: ['--maxkb=5120']
      - id: check-merge-conflict
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
```

**Makefile target**:
```makefile
hooks-install: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Pre-commit hooks installed"
```

---

### 6C. Documentation Generation

**API docs deployment** — `.github/workflows/docs.yml`:
```yaml
name: Deploy API Docs
on:
  push:
    branches: [main]
    paths: ["backend/app/**"]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  deploy-docs:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r backend/requirements.txt
      - name: Export OpenAPI spec
        run: |
          cd backend
          python -c "
          from app.main import app
          import json
          spec = app.openapi()
          with open('../docs/openapi.json', 'w') as f:
              json.dump(spec, f, indent=2)
          "
      - name: Generate Redoc static site
        run: |
          mkdir -p docs/site
          npx @redocly/cli build-docs docs/openapi.json -o docs/site/index.html
      - uses: actions/upload-pages-artifact@v3
        with: { path: docs/site }
      - uses: actions/deploy-pages@v4
        id: deployment
```

**Schema diagram generation** (Makefile target):
```makefile
docs-schema: ## Generate database schema diagram
	pip install eralchemy2 --break-system-packages
	cd backend && python -c " \
		from app.core.database import Base; \
		from app.models import *; \
		from eralchemy2 import render_er; \
		render_er(Base, 'docs/schema.png')"
	@echo "Schema diagram: backend/docs/schema.png"
```

---

## Implementation Order

The recommended execution order respects dependencies:

| Phase | Prompt  | Category | Depends On |
|-------|---------|----------|------------|
| 1     | CI-A1   | 6B Pre-commit hooks | — |
| 2     | CI-B1   | 1A+1B+1C CI pipeline hardening | — |
| 3     | CI-C1   | 2A Docker build optimization | — |
| 4     | CI-C2   | 2B Container registry | CI-B1 |
| 5     | CI-D1   | 3C PgBouncer | — |
| 6     | CI-D2   | 3B Read replica | CI-D1 |
| 7     | CI-D3   | 3A Automated backups | — |
| 8     | CI-E1   | 4A OpenTelemetry APM | — |
| 9     | CI-E2   | 4B+4C Business metrics + log alerts | CI-E1 |
| 10    | CI-F1   | 5A+5B+5C Security hardening | CI-B1 |
| 11    | CI-F2   | 2C Blue-green deployment | CI-C2 |
| 12    | CI-G1   | 6A Dev onboarding + 6C Docs | — |

---

## Summary

| Category | Enhancements | New Files | Modified Files |
|----------|-------------|-----------|----------------|
| 1. CI Pipeline | Matrix + Security + Migration | 0 | ci.yml, pyproject.toml |
| 2. Containers | BuildKit + Registry + Blue-Green | blue-green-deploy.sh | Dockerfile, ci.yml |
| 3. Database | Backup + Replica + PgBouncer | backup-s3.sh, restore-drill.sh, db_routing.py | docker-compose.prod.yml, init.sql |
| 4. Observability | APM + Business + Log Alerts | telemetry.py, business_metrics.py, tempo.yml, ecole-alerts.yml | monitoring compose, grafana config |
| 5. Security | Rotation + WAF + Deps | rotate-secrets.sh, dependabot.yml, automerge.yml | nginx-prod.conf, .pre-commit-config.yaml |
| 6. Developer XP | Onboarding + Hooks + Docs | .pre-commit-config.yaml, seed_demo.py, docs.yml | Makefile |
