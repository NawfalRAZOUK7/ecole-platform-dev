# Ecole Platform Infrastructure

Root infrastructure and DevOps configuration for the Ecole Platform—a K-12 EdTech SaaS serving Moroccan schools. This directory contains Docker-based deployment configurations, monitoring stacks, and operational scripts supporting zero-downtime blue-green deployments with full observability.

## Directory Structure

### Core Deployment Files

- **docker-compose.dev.yml** - Development environment with core services (backend, web, postgres, redis, worker, MinIO, mock OAuth)
- **docker-compose.staging.yml** - Staging environment for pre-production validation
- **docker-compose.prod.yml** - Production environment configuration
- **docker-compose.monitoring.yml** - Standalone monitoring stack (Prometheus, Grafana, Loki, Tempo, Promtail, Alertmanager)
- **docker-compose.blue.yml** - Blue deployment for zero-downtime rollout
- **docker-compose.green.yml** - Green deployment for zero-downtime rollout
- **docker-compose.override.yml.example** - Template for local environment overrides
- **DEPLOYMENT.md** - Detailed deployment procedures and runbooks

### Subdirectories

| Directory         | Purpose                                                              |
| ----------------- | -------------------------------------------------------------------- |
| **alertmanager/** | Prometheus AlertManager routing rules (email, Slack)                 |
| **backup/**       | Database backup and restore scripts with WORM compliance             |
| **certs/**        | TLS/SSL certificates (excluded from git)                             |
| **doppler/**      | Doppler environment bootstrap helpers for staging/production secrets |
| **grafana/**      | Monitoring dashboards and auto-provisioning config                   |
| **k8s/**          | Helm chart, values files, and local Kubernetes helpers               |
| **loki/**         | Log aggregation with Promtail collectors and alerting rules          |
| **minio/**        | Object storage notes for local/dev S3-compatible storage             |
| **nginx/**        | Reverse proxy configs with WAF, rate limiting, security headers      |
| **postgres/**     | PostgreSQL initialization scripts                                    |
| **prometheus/**   | Prometheus scrape targets and alerting rules                         |
| **redis/**        | Redis configuration with persistence and eviction                    |
| **scripts/**      | Deployment and operational automation                                |
| **secrets/**      | Sensitive configuration (excluded from git)                          |
| **tempo/**        | Distributed tracing configuration                                    |

## Quick Start

### Development

```bash
docker compose -f infra/docker-compose.dev.yml up
```

### Docker Compose matrix

| File                                                   | Purpose                                                                                                            |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `docker-compose.dev.yml`                               | Core services: backend, web, postgres, redis, worker, MinIO, mock OAuth (no monitoring).                           |
| `docker-compose.staging.yml`                           | Pre-production parity checks.                                                                                      |
| `docker-compose.prod.yml`                              | Production with PgBouncer, PostgreSQL + replica, Redis, backend, web, worker, nginx, certbot, Prometheus, Grafana. |
| `docker-compose.monitoring.yml`                        | Observability only: Prometheus, Grafana, Loki, Tempo, Promtail, Alertmanager.                                      |
| `docker-compose.tests.yml`                             | Disposable Docker test matrix for backend pytest, Postman/Newman, k6 smoke, and infra validation.                  |
| `docker-compose.blue.yml` / `docker-compose.green.yml` | Blue/green app instances for zero-downtime cutover.                                                                |
| `docker-compose.api-test.yml`                          | Lean stack for API / contract testing in CI or locally.                                                            |
| `docker-compose.override.yml.example`                  | Copy to `docker-compose.override.yml` (gitignored) for machine-specific ports and env.                             |

Secrets and environment-specific values are typically injected via **Doppler** or env files — see [`DEPLOYMENT.md`](DEPLOYMENT.md) and [`doppler/`](doppler/) scripts.

## Structure Conventions

- Compose files stay at the `infra/` root. Use `docker-compose.dev.yml` for local development, `docker-compose.tests.yml` for the Dockerized test matrix, `docker-compose.api-test.yml` for lean backend API/system-test support, `docker-compose.monitoring.yml` for observability-only work, and the staging/prod/blue/green files for deployment flows.
- Kubernetes assets stay under `infra/k8s/`. Shared defaults live in `values.yaml`; keep environment-specific settings in the matching values file. The Helm chart includes 12 resource templates plus 2 Helm helper files.
- Secrets are owned by Doppler or ignored local files under `infra/secrets/`. Do not commit rendered secret values.
- Database bootstrap is split deliberately: `infra/postgres/init.sql` owns roles, extensions, and privileges only; application tables, indexes, constraints, and enums are owned by Alembic migrations under `backend/alembic/`.
- Backend tooling lives in `backend/scripts/`; repo-wide automation remains under root `scripts/`; cross-service Postman/k6/chaos assets live under `system-tests/`.
- Observability names should use backend bounded contexts where possible: `auth`, `user`, `school`, `academic`, `lms`, `billing`, `content`, `communication`, `reports`, `admin`, `sync`, `ai`, and `operations`.

### Monitoring Stack

```bash
docker compose -f infra/docker-compose.monitoring.yml up
```

### Production Blue-Green Deployment

```bash
./infra/scripts/blue-green-deploy.sh <image-version>
```

## Key Features

- **Zero-Downtime Deployments** - Blue-green strategy via dedicated Docker Compose files
- **Full Observability** - Prometheus metrics, Loki logs, Tempo traces, Grafana dashboards
- **High Availability** - Redis caching, PostgreSQL with backup/restore, health checks
- **Security** - TLS termination, WAF rules, rate limiting, JWT key rotation
- **Compliance** - WORM audit exports, encrypted backups, audit logging
- **Disaster Recovery** - Automated restore drills, S3 backup upload, restore verification

## Common Operations

### Check Service Health

```bash
./infra/scripts/healthcheck.sh
```

### Database Backup

```bash
./infra/backup/pg_backup.sh
```

### Restore from Backup

```bash
./infra/backup/pg_restore.sh <dump-file>
```

### Rotate JWT Secrets

```bash
./infra/scripts/rotate-secrets.sh
```

### Run Disaster Recovery Drill

```bash
./infra/scripts/restore-drill.sh
```

### Upload Backups to S3

```bash
./infra/scripts/backup-s3.sh <backup-file>
```

### Renew TLS Certificates

```bash
./infra/scripts/ssl-renew.sh
```

## Environment Configuration

Copy and customize the override template:

```bash
cp infra/docker-compose.override.yml.example infra/docker-compose.override.yml
```

## Documentation

See **DEPLOYMENT.md** for:

- Step-by-step deployment procedures
- Rollback procedures
- Incident response runbooks
- Troubleshooting guides
- Monitoring and alerting setup
