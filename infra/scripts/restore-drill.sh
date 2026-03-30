#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-${PGHOST:-localhost}}"
DB_PORT="${DB_PORT:-${PGPORT:-5432}}"
DB_USER="${DB_USER:-${PGUSER:-ecole}}"
ADMIN_DB="${ADMIN_DB:-postgres}"
S3_BUCKET="${S3_BUCKET:?S3_BUCKET required}"
S3_BACKUP_PREFIX="${S3_BACKUP_PREFIX:-backups}"
DRILL_DB="ecole_restore_drill_$(date +%Y%m%d_%H%M%S)"
TMP_FILE="/tmp/${DRILL_DB}.sql.gz"
CRITICAL_TABLES="${CRITICAL_TABLES:-users schools memberships courses invoices}"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] RESTORE-DRILL: $*"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        log "ERROR: required command not found: $1"
        exit 1
    }
}

cleanup() {
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$ADMIN_DB" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DRILL_DB}' AND pid <> pg_backend_pid();" \
        >/dev/null 2>&1 || true
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$ADMIN_DB" -c \
        "DROP DATABASE IF EXISTS ${DRILL_DB};" >/dev/null 2>&1 || true
    rm -f "$TMP_FILE"
}

trap cleanup EXIT

require_command aws
require_command psql
require_command gunzip

LATEST="$(aws s3 ls "s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/" | awk '{print $4}' | sort | tail -1)"
[ -n "$LATEST" ] || {
    log "ERROR: no backup objects found in s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/"
    exit 1
}

log "Downloading latest backup: ${LATEST}"
aws s3 cp "s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/${LATEST}" "$TMP_FILE" >/dev/null

log "Creating drill database: ${DRILL_DB}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$ADMIN_DB" -c "DROP DATABASE IF EXISTS ${DRILL_DB};" >/dev/null
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$ADMIN_DB" -c "CREATE DATABASE ${DRILL_DB};" >/dev/null

log "Restoring backup into ${DRILL_DB}"
gunzip -c "$TMP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DRILL_DB" -q >/dev/null

table_count="$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DRILL_DB" -t -A -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';")"
row_total="$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DRILL_DB" -t -A -c \
    "SELECT COALESCE(sum(n_live_tup), 0)::bigint FROM pg_stat_user_tables;")"

log "Validation summary: tables=${table_count} rows=${row_total}"

for table_name in $CRITICAL_TABLES; do
    exists="$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DRILL_DB" -t -A -c \
        "SELECT to_regclass('public.${table_name}') IS NOT NULL;")"
    if [ "$exists" != "t" ]; then
        log "ERROR: critical table missing: ${table_name}"
        exit 1
    fi
done

log "Restore drill PASSED"
