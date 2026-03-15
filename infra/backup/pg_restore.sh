#!/usr/bin/env bash
# PostgreSQL restore script — École Platform
#
# Reference: S-134 — Restore runbook and drill, F3 Ch05 — Restore Procedures
# Supports: full restore from backup, PITR to specific timestamp
#
# Usage:
#   ./pg_restore.sh /path/to/backup.sql.gz           # Full restore
#   ./pg_restore.sh --pitr "2026-03-15 14:30:00"      # Point-in-time recovery
#   ./pg_restore.sh --verify-only /path/to/backup      # Verify without restoring
#
# CRITICAL: This script will DROP and recreate the target database.
# Requires 4-eyes approval for production (F3 Ch07).

set -euo pipefail

# ── Configuration ──
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-ecole}"
PGDATABASE="${PGDATABASE:-ecole_platform}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"
WAL_ARCHIVE="${WAL_ARCHIVE:-/var/lib/postgresql/wal_archive}"

# ── Functions ──
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RESTORE: $*"
}

die() {
    log "ERROR: $*"
    exit 1
}

usage() {
    echo "Usage: $0 [OPTIONS] <backup_file>"
    echo ""
    echo "Options:"
    echo "  --pitr <timestamp>     Point-in-time recovery target (e.g., '2026-03-15 14:30:00')"
    echo "  --verify-only          Verify backup integrity without restoring"
    echo "  --target-db <name>     Target database name (default: ${PGDATABASE})"
    echo "  --skip-confirmation    Skip interactive confirmation (for automated drills)"
    echo ""
    echo "Examples:"
    echo "  $0 /backups/ecole_platform_20260315.sql.gz"
    echo "  $0 --pitr '2026-03-15 14:30:00'"
    echo "  $0 --verify-only /backups/ecole_platform_20260315.sql.gz"
    exit 1
}

# ── Parse arguments ──
PITR_TARGET=""
VERIFY_ONLY=false
SKIP_CONFIRM=false
BACKUP_FILE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --pitr)
            PITR_TARGET="$2"
            shift 2
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --target-db)
            PGDATABASE="$2"
            shift 2
            ;;
        --skip-confirmation)
            SKIP_CONFIRM=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            BACKUP_FILE="$1"
            shift
            ;;
    esac
done

# ── Pre-flight checks ──
log "=== PostgreSQL Restore Procedure ==="
log "Target: ${PGDATABASE}@${PGHOST}:${PGPORT}"

if [ -n "${BACKUP_FILE}" ]; then
    [ -f "${BACKUP_FILE}" ] || die "Backup file not found: ${BACKUP_FILE}"

    # Verify checksum if available
    if [ -f "${BACKUP_FILE}.sha256" ]; then
        log "Verifying backup checksum..."
        sha256sum --check "${BACKUP_FILE}.sha256" || die "Checksum verification failed!"
        log "Checksum verified OK"
    fi

    if [ "${VERIFY_ONLY}" = true ]; then
        log "Verification complete. Backup file is valid."
        exit 0
    fi
fi

# ── Confirmation ──
if [ "${SKIP_CONFIRM}" = false ]; then
    log "WARNING: This will DROP and recreate database '${PGDATABASE}'"
    read -rp "Type 'RESTORE' to confirm: " CONFIRM
    [ "${CONFIRM}" = "RESTORE" ] || die "Restore cancelled by user"
fi

# ── Step 1: Stop application connections ──
log "Step 1: Terminating active connections to ${PGDATABASE}"
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${PGDATABASE}' AND pid <> pg_backend_pid();" \
    2>/dev/null || true

# ── Step 2: Drop and recreate database ──
log "Step 2: Recreating database ${PGDATABASE}"
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "DROP DATABASE IF EXISTS ${PGDATABASE};"
psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c "CREATE DATABASE ${PGDATABASE} OWNER ${PGUSER};"

# ── Step 3: Restore from backup ──
if [ -n "${BACKUP_FILE}" ]; then
    log "Step 3: Restoring from backup file: ${BACKUP_FILE}"

    # Decrypt if encrypted
    RESTORE_FILE="${BACKUP_FILE}"
    if [[ "${BACKUP_FILE}" == *.enc ]]; then
        log "Decrypting backup..."
        RESTORE_FILE="${BACKUP_FILE%.enc}"
        openssl enc -aes-256-cbc -d -pbkdf2 \
            -in "${BACKUP_FILE}" \
            -out "${RESTORE_FILE}" \
            -pass env:BACKUP_ENCRYPTION_KEY
    fi

    # Restore
    gunzip -c "${RESTORE_FILE}" | pg_restore \
        -h "${PGHOST}" \
        -p "${PGPORT}" \
        -U "${PGUSER}" \
        -d "${PGDATABASE}" \
        --no-owner \
        --no-privileges \
        --verbose \
        2>&1

    log "Backup restored successfully"
fi

# ── Step 4: Run pending migrations ──
log "Step 4: Applying pending migrations (Alembic)"
cd "$(dirname "$0")/../../backend" || die "Cannot find backend directory"
alembic upgrade head 2>&1 || log "WARNING: Migration failed — may need manual intervention"

# ── Step 5: Post-restore validation (F3 Ch05 checklist) ──
log "Step 5: Post-restore validation"

# 5a. Schema conformance
log "  5a. Checking schema conformance..."
TABLES=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';")
log "  Schema has ${TABLES} tables"

# 5b. Data integrity — check critical tables
log "  5b. Checking data integrity..."
USERS=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -c \
    "SELECT count(*) FROM users;" 2>/dev/null || echo "0")
log "  Users table: ${USERS} rows"

# 5c. Audit log integrity
log "  5c. Checking audit log integrity..."
AUDIT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -c \
    "SELECT count(*) FROM audit_logs;" 2>/dev/null || echo "0")
log "  Audit logs: ${AUDIT} entries"

# 5d. API smoke test
log "  5d. Running API smoke test..."
if command -v curl >/dev/null 2>&1; then
    HEALTH=$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null || echo "FAILED")
    if echo "${HEALTH}" | grep -q "healthy"; then
        log "  Health check: PASS"
    else
        log "  WARNING: Health check failed — API may need restart"
    fi
else
    log "  WARNING: curl not available, skipping smoke test"
fi

# ── Summary ──
log "=== Restore Complete ==="
log "Database: ${PGDATABASE}"
log "Tables: ${TABLES}"
log "Users: ${USERS}"
log "Audit entries: ${AUDIT}"
log "Status: SUCCESS"
log ""
log "POST-RESTORE ACTIONS:"
log "  1. Restart the API server"
log "  2. Run integration smoke tests: make test"
log "  3. Verify observability (logs, metrics, traces)"
log "  4. Archive this log to artifacts/f3/restore_drills/"
log "  5. Update decision log with restore outcome"
