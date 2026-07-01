# Deployment & Operations Scripts

Bash scripts for deploying, maintaining, and recovering the École Platform. Automates critical operational tasks with safety checks and logging.

## Boundaries

- `infra/scripts/` is for deployment, backup, restore, secret rotation, certificates, and health checks.
- Backend developer/CI utilities such as OpenAPI export and migration validation live in `backend/scripts/`.
- Cross-service Postman, k6, and chaos workflows live in `system-tests/`.
- Operational notes should use the backend bounded context names when a check is domain-specific: `auth`, `user`, `school`, `academic`, `lms`, `billing`, `content`, `communication`, `reports`, `admin`, `sync`, `ai`, and `operations`.

## Scripts Overview

### Deployment

#### deploy.sh
- **Purpose** - Standard production deployment
- **Usage** - `./deploy.sh [--skip-migrations] [--rollback]`
- **Actions**
  - Build/pull production images through `docker-compose.prod.yml`
  - Run Alembic migrations unless skipped
  - Restart backend, worker, web, and nginx with health checks
  - Verify deployment success
- **Safety** - Automatic rollback on health check failure
- **Output** - Deployment log with timestamps

Example:
```bash
./deploy.sh
./deploy.sh --skip-migrations
```

#### blue-green-deploy.sh
- **Purpose** - Zero-downtime production deployment
- **Usage** - `./blue-green-deploy.sh <version>`
- **Actions**
  - Deploy new version to "green" environment
  - Health-check the green environment before traffic switch
  - Keep `system-tests/` available for manual smoke checks when needed
  - Switch traffic from "blue" to "green"
  - Keep blue environment as rollback target
  - Monitor for issues during and after switch
- **Safety** - Traffic switchback available for 30 minutes post-deployment
- **RTO** - <2 minutes with instant rollback capability
- **Output** - Deployment report with health metrics

Example:
```bash
./blue-green-deploy.sh v1.2.3
```

### Backup & Disaster Recovery

#### backup-s3.sh
- **Purpose** - Upload database backups to AWS S3
- **Usage** - `./backup-s3.sh <backup-file>`
- **Actions**
  - Validate backup file exists and is readable
  - Calculate file checksum (MD5/SHA256)
  - Upload to S3 with encryption
  - Verify upload integrity
  - Store checksum with backup
  - Manage retention (keep last 30 backups)
- **Safety** - Server-side encryption (SSE-S3), versioning enabled
- **Output** - Upload confirmation with S3 location

Example:
```bash
./backup-s3.sh ecole_backup_2026-03-30_143022.sql.gz
```

#### restore-drill.sh
- **Purpose** - Automated disaster recovery testing
- **Usage** - `./restore-drill.sh <environment>`
- **Actions**
  - Select oldest backup for worst-case recovery test
  - Spin up staging environment if needed
  - Restore database from selected backup
  - Run data validation queries
  - Verify table counts and checksums
  - Test critical application functionality
  - Document recovery time and success metrics
  - Tear down staging environment
- **Safety** - Uses staging, never touches production data
- **RTO Verification** - Confirms recovery meets SLA
- **Output** - Drill report with recovery metrics

Example:
```bash
./restore-drill.sh staging
```

### Secrets & Security

#### rotate-secrets.sh
- **Purpose** - JWT signing key rotation for security
- **Usage** - `./rotate-secrets.sh [--dry-run]`
- **Actions**
  - Generate new JWT signing key
  - Update application secrets
  - Restart authentication services
  - Validate new tokens are issued correctly
  - Keep old key for grace period (invalidates existing tokens after TTL)
  - Log rotation event for audit
- **Safety** - Dry-run mode available for validation
- **Grace Period** - 24 hours for token refresh
- **Output** - Rotation confirmation and timeline

Example:
```bash
./rotate-secrets.sh --dry-run  # Preview changes
./rotate-secrets.sh            # Execute rotation
```

### Monitoring & Health

#### healthcheck.sh
- **Purpose** - Verify all services are healthy
- **Usage** - `./healthcheck.sh [--verbose]`
- **Actions**
  - Check HTTP endpoints respond with 200
  - Verify database connectivity
  - Test cache (Redis) responsiveness
  - Validate metrics endpoints
  - Check certificate expiration
  - Monitor container resource usage
- **Checks**
  - API `/health` endpoint
  - Database connection pool
  - Redis connectivity
  - NGINX reverse proxy
  - Prometheus scrape targets
  - TLS certificate validity
- **Exit Code** - 0 if healthy, 1 if any check fails
- **Output** - Status summary per service

Example:
```bash
./healthcheck.sh
./healthcheck.sh --verbose  # Detailed output
```

### Certificate Management

#### ssl-renew.sh
- **Purpose** - Renew TLS/SSL certificates
- **Usage** - `./ssl-renew.sh [--force]`
- **Actions**
  - Check certificate expiration date
  - Request renewal if within 30 days of expiry
  - Validate new certificate
  - Update NGINX configuration
  - Reload NGINX with zero downtime
  - Verify new certificate is active
- **Methods**
  - Let's Encrypt ACME (automated)
  - Manual certificate import
- **Safety** - Validates certificate before using
- **Frequency** - Runs daily via cron (auto-renews 30 days before expiry)
- **Output** - Renewal status and certificate details

Example:
```bash
./ssl-renew.sh
./ssl-renew.sh --force  # Force renewal regardless of expiry date
```

## Common Operations Workflows

### Deploy New Version with Zero Downtime
```bash
./blue-green-deploy.sh v1.2.3
# Or with manual verification:
docker-compose -f docker-compose.blue.yml up -d
# Test blue environment...
# Then switch traffic:
docker-compose -f docker-compose.green.yml down
mv docker-compose.blue.yml docker-compose.yml
docker-compose up -d
```

### Create and Backup Database
```bash
../backup/pg_backup.sh
# Creates: ecole_backup_2026-03-30_143022.sql.gz
./backup-s3.sh ecole_backup_2026-03-30_143022.sql.gz
```

### Test Disaster Recovery
```bash
./restore-drill.sh staging
# Verify recovery meets RTO/RPO targets
```

### Routine Health Check
```bash
./healthcheck.sh --verbose
# All services should report OK
```

### Rotate Secrets Before Change
```bash
./rotate-secrets.sh --dry-run  # Preview
./rotate-secrets.sh            # Execute
```

## Logging & Debugging

All scripts log to `infra/` directory:
```
infra/
├── deploy.log
├── backup.log
├── restore-drill.log
└── healthcheck.log
```

Enable debug mode:
```bash
DEBUG=1 ./deploy.sh
```

## Prerequisites

Scripts require:
- Docker and Docker Compose
- AWS CLI (for S3 operations)
- PostgreSQL client tools
- NGINX reload capability
- SSH access to all hosts (if multi-server setup)

Ensure dependencies are installed:
```bash
# Docker and Docker Compose
# AWS CLI (for S3 operations)
# PostgreSQL client tools
# NGINX reload capability
```

## Emergency Procedures

See `../DEPLOYMENT.md` for:
- Service recovery procedures
- Database corruption recovery
- Incident response runbooks
- Escalation procedures
- Communication templates
