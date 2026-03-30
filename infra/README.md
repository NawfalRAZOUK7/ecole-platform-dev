# Ecole Platform Infrastructure

Root infrastructure and DevOps configuration for the Ecole Platform—a K-12 EdTech SaaS serving Moroccan schools. This directory contains Docker-based deployment configurations, monitoring stacks, and operational scripts supporting zero-downtime blue-green deployments with full observability.

## Directory Structure

### Core Deployment Files

- **docker-compose.dev.yml** - Development environment with all services (backend, frontend, database, caching, monitoring)
- **docker-compose.staging.yml** - Staging environment for pre-production validation
- **docker-compose.prod.yml** - Production environment configuration
- **docker-compose.monitoring.yml** - Standalone monitoring stack (Prometheus, Grafana, Loki, Tempo)
- **docker-compose.blue.yml** - Blue deployment for zero-downtime rollout
- **docker-compose.green.yml** - Green deployment for zero-downtime rollout
- **docker-compose.override.yml.example** - Template for local environment overrides
- **DEPLOYMENT.md** - Detailed deployment procedures and runbooks

### Subdirectories

| Directory | Purpose |
|-----------|---------|
| **alertmanager/** | Prometheus AlertManager routing rules (email, Slack) |
| **backup/** | Database backup and restore scripts with WORM compliance |
| **certs/** | TLS/SSL certificates (excluded from git) |
| **grafana/** | Monitoring dashboards and auto-provisioning config |
| **loki/** | Log aggregation with Promtail collectors and alerting rules |
| **nginx/** | Reverse proxy configs with WAF, rate limiting, security headers |
| **postgres/** | PostgreSQL initialization scripts |
| **prometheus/** | Prometheus scrape targets and alerting rules |
| **redis/** | Redis configuration with persistence and eviction |
| **scripts/** | Deployment and operational automation |
| **secrets/** | Sensitive configuration (excluded from git) |
| **tempo/** | Distributed tracing configuration |

## Quick Start

### Development
```bash
docker-compose -f docker-compose.dev.yml up
```

### Monitoring Stack
```bash
docker-compose -f docker-compose.monitoring.yml up
```

### Production Blue-Green Deployment
```bash
./scripts/blue-green-deploy.sh <image-version>
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
./scripts/healthcheck.sh
```

### Database Backup
```bash
./backup/pg_backup.sh
```

### Restore from Backup
```bash
./backup/pg_restore.sh <dump-file>
```

### Rotate JWT Secrets
```bash
./scripts/rotate-secrets.sh
```

### Run Disaster Recovery Drill
```bash
./scripts/restore-drill.sh
```

### Upload Backups to S3
```bash
./scripts/backup-s3.sh <backup-file>
```

### Renew TLS Certificates
```bash
./scripts/ssl-renew.sh
```

## Environment Configuration

Copy and customize the override template:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
```

## Documentation

See **DEPLOYMENT.md** for:
- Step-by-step deployment procedures
- Rollback procedures
- Incident response runbooks
- Troubleshooting guides
- Monitoring and alerting setup
