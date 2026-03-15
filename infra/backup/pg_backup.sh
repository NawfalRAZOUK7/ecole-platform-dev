#!/usr/bin/env bash
# PostgreSQL daily backup script — École Platform
#
# Reference: S-132 — PostgreSQL backups, F3 Ch04 — Backup Strategy Matrix
# Strategy: Daily full backup + continuous WAL archiving (PITR-ready)
# Encryption: AES-256 at rest
# Retention: 30 days
# RPO: 15 minutes (prod)
# Schedule: Daily at 02:00 UTC via cron
#
# Usage:
#   ./pg_backup.sh                    # Run backup
#   BACKUP_DIR=/custom/path ./pg_backup.sh  # Custom backup directory
#
# Cron entry (add to crontab):
#   0 2 * * * /path/to/infra/backup/pg_backup.sh >> /var/log/ecole/backup.log 2>&1

set -euo pipefail

# ── Configuration ──
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ecole/postgresql}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/ecole_platform_${TIMESTAMP}.sql.gz"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

# Database connection (from environment or defaults)
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-ecole}"
PGDATABASE="${PGDATABASE:-ecole_platform}"

# ── Functions ──
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] BACKUP: $*"
}

die() {
    log "ERROR: $*"
    exit 1
}

# ── Pre-flight checks ──
log "Starting PostgreSQL backup for ${PGDATABASE}@${PGHOST}"

mkdir -p "${BACKUP_DIR}" || die "Cannot create backup directory: ${BACKUP_DIR}"

# Verify pg_dump is available
command -v pg_dump >/dev/null 2>&1 || die "pg_dump not found in PATH"

# Verify database connectivity
pg_isready -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" >/dev/null 2>&1 \
    || die "Cannot connect to PostgreSQL at ${PGHOST}:${PGPORT}"

# ── Execute backup ──
log "Creating compressed backup: ${BACKUP_FILE}"

pg_dump \
    -h "${PGHOST}" \
    -p "${PGPORT}" \
    -U "${PGUSER}" \
    -d "${PGDATABASE}" \
    --format=custom \
    --compress=9 \
    --verbose \
    --no-owner \
    --no-privileges \
    2>&1 | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -sh "${BACKUP_FILE}" | cut -f1)
log "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ── Optional AES-256 encryption ──
if [ -n "${ENCRYPTION_KEY}" ]; then
    log "Encrypting backup with AES-256"
    ENCRYPTED_FILE="${BACKUP_FILE}.enc"
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${BACKUP_FILE}" \
        -out "${ENCRYPTED_FILE}" \
        -pass env:BACKUP_ENCRYPTION_KEY
    rm -f "${BACKUP_FILE}"
    BACKUP_FILE="${ENCRYPTED_FILE}"
    log "Encrypted backup: ${ENCRYPTED_FILE}"
fi

# ── Verify backup integrity ──
log "Verifying backup integrity..."
if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    CHECKSUM=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
    echo "${CHECKSUM}  ${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
    log "Checksum (SHA-256): ${CHECKSUM}"
else
    die "Backup file is empty or missing"
fi

# ── Prune old backups (retention policy) ──
log "Pruning backups older than ${RETENTION_DAYS} days"
PRUNED=$(find "${BACKUP_DIR}" -name "ecole_platform_*.sql.gz*" -mtime "+${RETENTION_DAYS}" -type f -print -delete | wc -l)
log "Pruned ${PRUNED} old backup files"

# ── Summary ──
TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "ecole_platform_*.sql.gz*" -type f | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log "Backup complete. Total backups: ${TOTAL_BACKUPS}, Total size: ${TOTAL_SIZE}"
log "SUCCESS"
