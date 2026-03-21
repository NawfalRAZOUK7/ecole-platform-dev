# Deployment Guide — École Platform

> Reference: Phase 7A — Production Environment & TLS

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [TLS Certificates](#tls-certificates)
4. [Deployment](#deployment)
5. [Health Monitoring](#health-monitoring)
6. [Rollback](#rollback)
7. [Scaling](#scaling)
8. [Maintenance](#maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker** ≥ 24.0 with Compose V2
- **Domain names** pointed to the server:
  - `ecole-platform.example` (web frontend)
  - `api.ecole-platform.example` (API backend)
- **Ports 80 and 443** open for HTTP/HTTPS traffic
- **Linux server** (Ubuntu 22.04+ recommended), minimum 4GB RAM / 2 vCPU

## Initial Setup

### 1. Clone and configure

```bash
git clone <repo-url> ecole-platform
cd ecole-platform
```

### 2. Create environment file

```bash
cp .env.example .env.prod
```

Edit `.env.prod` with production values:

```env
# Database (use managed DB URL if available)
DATABASE_URL=postgresql+asyncpg://ecole:<password>@postgres:5432/ecole_platform
POSTGRES_USER=ecole
POSTGRES_DB=ecole_platform

# Redis (use managed Redis URL if available)
REDIS_URL=redis://redis:6379/0

# Auth
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
LOG_LEVEL=WARNING
CORS_ORIGINS=https://ecole-platform.example

# SMTP
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@ecole-platform.example

# S3 / Object storage (optional)
S3_ENDPOINT=https://s3.example.com
S3_BUCKET=ecole-uploads
S3_REGION=auto

# Timezone
TZ=Africa/Casablanca
```

### 3. Create Docker secrets

```bash
cd infra/secrets

# Generate a strong JWT secret (64 hex chars)
openssl rand -hex 32 > jwt_secret_key.txt

# Set database password (use the same as in managed DB or compose)
echo "your-strong-db-password-here" > db_password.txt

# Set SMTP password
echo "your-smtp-password" > smtp_password.txt

# Verify files exist
ls -la *.txt
```

> **Never commit these files to git.** They are in `.gitignore`.

### 4. Run initial deployment

```bash
# Build and start all services
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod up -d --build

# Run database migrations
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod \
  run --rm backend alembic upgrade head

# Seed initial data (first deploy only)
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod \
  run --rm backend python -m app.seed
```

## TLS Certificates

### Option A: Let's Encrypt (recommended)

```bash
# Set your domains
export CERT_EMAIL="admin@ecole-platform.example"
export WEB_DOMAIN="ecole-platform.example"
export API_DOMAIN="api.ecole-platform.example"

# Obtain certificates
./infra/scripts/ssl-renew.sh obtain "$WEB_DOMAIN"
./infra/scripts/ssl-renew.sh obtain "$API_DOMAIN"

# Verify
./infra/scripts/ssl-renew.sh status
```

Update `nginx-prod.conf` certificate paths to point to Let's Encrypt:

```nginx
ssl_certificate     /etc/nginx/ssl/live/ecole-platform.example/fullchain.pem;
ssl_certificate_key /etc/nginx/ssl/live/ecole-platform.example/privkey.pem;
```

**Auto-renewal cron** (add to server crontab):

```cron
# Renew certificates twice daily
0 3,15 * * * /path/to/infra/scripts/ssl-renew.sh renew >> /var/log/ssl-renew.log 2>&1
```

### Option B: Custom certificate

Place your certificate files in `infra/certs/`:

```
infra/certs/fullchain.pem   # Full certificate chain
infra/certs/privkey.pem      # Private key
```

Reload nginx after placing certs:

```bash
docker compose -f infra/docker-compose.prod.yml exec nginx nginx -s reload
```

## Deployment

### Standard deployment (zero-downtime)

```bash
./infra/scripts/deploy.sh
```

The script performs:
1. **Pre-flight checks** — verifies secrets, env file, Docker
2. **Image backup** — tags current images as `previous` for rollback
3. **Build** — pulls latest base images and rebuilds services
4. **Migrations** — runs `alembic upgrade head`
5. **Rolling restart** — restarts services one at a time
6. **Health check** — validates each service after restart
7. **Auto-rollback** — if backend health check fails, restores previous image

### Skip migrations

```bash
./infra/scripts/deploy.sh --skip-migrations
```

### Deployment log

All deployment output is logged to `infra/deploy.log`.

## Health Monitoring

### Manual check

```bash
# Full interactive report
./infra/scripts/healthcheck.sh

# JSON output (for monitoring systems)
./infra/scripts/healthcheck.sh --json

# Exit code only (0=healthy, 1=degraded, 2=critical)
./infra/scripts/healthcheck.sh --quiet
```

### What is checked

| Check | OK | Warning | Critical |
|-------|-----|---------|----------|
| API | HTTP 200 | Non-200 response | Unreachable |
| PostgreSQL | pg_isready + connection count | — | Unreachable |
| Redis | PING=PONG + memory usage | — | Unreachable |
| Disk | < 80% usage | 80-90% usage | > 90% usage |
| Certificates | > 30 days validity | 7-30 days | < 7 days or expired |
| Containers | All running | — | Any container down |

### Cron monitoring

```cron
# Health check every 5 minutes
*/5 * * * * /path/to/infra/scripts/healthcheck.sh --quiet || /path/to/alert.sh
```

## Rollback

### Automatic rollback

The deploy script automatically rolls back if the backend health check fails after restart. Previous images are tagged as `ecole-backend:previous` before each deployment.

### Manual rollback

```bash
./infra/scripts/deploy.sh --rollback
```

### Emergency rollback

If the deploy script itself fails:

```bash
# Restore previous backend image
docker tag ecole-backend:previous ecole-backend:latest

# Restart services
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod up -d backend worker

# Verify
curl -sf http://localhost/api/v1/health
```

### Database rollback

If a migration caused issues:

```bash
# Check current revision
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod \
  run --rm backend alembic current

# Downgrade to a specific revision
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod \
  run --rm backend alembic downgrade <revision>
```

## Scaling

### Backend scaling

The backend service has no `container_name`, allowing horizontal scaling:

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod \
  up -d --scale backend=3
```

Nginx's `upstream api_backend` will load-balance across instances via Docker's internal DNS.

### Resource limits

Current production limits (adjustable in `docker-compose.prod.yml`):

| Service | Memory Limit | CPU Limit |
|---------|-------------|-----------|
| Backend | 1GB | 2.0 |
| PostgreSQL | 2GB | 2.0 |
| Redis | 512MB | 0.5 |
| Worker | 512MB | 1.0 |
| Web | 256MB | 0.5 |
| Nginx | 128MB | 0.5 |

## Maintenance

### Database backup

Daily backups run automatically via `infra/backup/pg_backup.sh`. See the backup scripts documentation for details.

```bash
# Manual backup
./infra/backup/pg_backup.sh

# Restore drill (monthly validation)
./infra/backup/restore_drill.sh
```

### Log access

```bash
# View backend logs
docker compose -f infra/docker-compose.prod.yml logs -f backend

# View nginx access logs
docker compose -f infra/docker-compose.prod.yml logs -f nginx

# View worker logs
docker compose -f infra/docker-compose.prod.yml logs -f worker

# View all logs
docker compose -f infra/docker-compose.prod.yml logs -f
```

For centralized logging, deploy the monitoring stack:

```bash
docker compose -f infra/docker-compose.monitoring.yml up -d
```

Access Grafana at `http://localhost:3000` (default: admin/admin).

### Certificate renewal

Certificates auto-renew via cron. To manually check or renew:

```bash
./infra/scripts/ssl-renew.sh status
./infra/scripts/ssl-renew.sh renew
```

### Updating services

```bash
# Pull latest base images and rebuild
docker compose -f infra/docker-compose.prod.yml --env-file .env.prod build --pull

# Or use the deploy script for zero-downtime updates
./infra/scripts/deploy.sh
```

## Troubleshooting

### Service won't start

```bash
# Check container status
docker compose -f infra/docker-compose.prod.yml ps

# Check logs for the failing service
docker compose -f infra/docker-compose.prod.yml logs <service-name>

# Check resource usage
docker stats --no-stream
```

### Database connection issues

```bash
# Test connectivity
docker exec ecole-prod-postgres pg_isready -U ecole -d ecole_platform

# Check connection count
docker exec ecole-prod-postgres psql -U ecole -d ecole_platform \
  -c "SELECT count(*) FROM pg_stat_activity;"

# Check for long-running queries
docker exec ecole-prod-postgres psql -U ecole -d ecole_platform \
  -c "SELECT pid, now()-query_start AS duration, query FROM pg_stat_activity WHERE state='active' ORDER BY duration DESC LIMIT 5;"
```

### Redis issues

```bash
# Check memory usage
docker exec ecole-prod-redis redis-cli info memory

# Check connected clients
docker exec ecole-prod-redis redis-cli info clients

# Flush cache (careful!)
docker exec ecole-prod-redis redis-cli FLUSHDB
```

### Nginx 502 Bad Gateway

This usually means the backend is down or unreachable:

```bash
# Check if backend is running
docker compose -f infra/docker-compose.prod.yml ps backend

# Check backend health
curl -sf http://localhost:8000/api/v1/health

# Restart backend
docker compose -f infra/docker-compose.prod.yml restart backend
```

### Disk space issues

```bash
# Check Docker disk usage
docker system df

# Prune unused images/containers/volumes
docker system prune -f

# Prune unused volumes (careful — deletes unused data volumes!)
docker volume prune -f
```

### Certificate issues

```bash
# Check current cert status
./infra/scripts/ssl-renew.sh status

# Test TLS configuration
openssl s_client -connect ecole-platform.example:443 -servername ecole-platform.example

# Force renew
docker run --rm -v ./infra/certs:/etc/letsencrypt certbot/certbot renew --force-renewal
```

---

## Architecture Overview

```
Internet
    │
    ├── :80  ──→ Nginx (HTTP→HTTPS redirect + ACME challenge)
    └── :443 ──→ Nginx (TLS termination)
                    │
                    ├── /api/*  ──→ Backend (FastAPI, Uvicorn ×4 workers)
                    ├── /api/v1/ws ──→ Backend (WebSocket)
                    └── /*      ──→ Web (Static React SPA)
                                        │
                    Backend ──→ PostgreSQL 16 (WAL archiving)
                           ──→ Redis 7 (cache + sessions + queues)
                           ──→ S3 (file uploads)
                    Worker  ──→ ARQ (background tasks via Redis)
                    Certbot ──→ Let's Encrypt (auto-renewal)
```

## Security Checklist

- [ ] All secrets created in `infra/secrets/` (never in git)
- [ ] `.env.prod` has production values (not defaults)
- [ ] TLS certificates installed and valid
- [ ] CORS_ORIGINS set to actual domain
- [ ] SMTP configured for email delivery
- [ ] Firewall allows only ports 80, 443, 22
- [ ] Backups configured (`pg_backup.sh` in cron)
- [ ] Health monitoring configured (`healthcheck.sh` in cron)
- [ ] SSL auto-renewal configured (`ssl-renew.sh` in cron)
- [ ] Log rotation configured (Docker JSON driver, max 10MB × 5 files)
