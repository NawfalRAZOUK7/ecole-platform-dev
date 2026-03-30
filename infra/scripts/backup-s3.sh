#!/usr/bin/env bash
set -euo pipefail

DB_HOST="${DB_HOST:-${PGHOST:-localhost}}"
DB_PORT="${DB_PORT:-${PGPORT:-5432}}"
DB_NAME="${DB_NAME:-${PGDATABASE:-ecole_platform}}"
DB_USER="${DB_USER:-${PGUSER:-ecole}}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ecole/postgresql}"
S3_BUCKET="${S3_BUCKET:?S3_BUCKET required}"
S3_BACKUP_PREFIX="${S3_BACKUP_PREFIX:-backups}"
LOCAL_RETENTION_DAYS="${LOCAL_RETENTION_DAYS:-7}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
STORAGE_CLASS="${S3_STORAGE_CLASS:-STANDARD_IA}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] BACKUP-S3: $*"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || {
        log "ERROR: required command not found: $1"
        exit 1
    }
}

to_epoch() {
    if date -d "$1" +%s >/dev/null 2>&1; then
        date -d "$1" +%s
    else
        date -j -f "%Y-%m-%d" "$1" +%s
    fi
}

require_command pg_dump
require_command pg_isready
require_command gzip
require_command aws

mkdir -p "$BACKUP_DIR"

log "Starting backup for ${DB_NAME}@${DB_HOST}:${DB_PORT}"
pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1

pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-privileges | gzip > "$BACKUP_FILE"

log "Backup created: $(basename "$BACKUP_FILE") ($(du -h "$BACKUP_FILE" | cut -f1))"

aws s3 cp \
    "$BACKUP_FILE" \
    "s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/$(basename "$BACKUP_FILE")" \
    --storage-class "$STORAGE_CLASS"

log "Uploaded to s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/"

find "$BACKUP_DIR" -name "*.sql.gz" -mtime +"$LOCAL_RETENTION_DAYS" -delete

now_epoch="$(date +%s)"
aws s3 ls "s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/" | while read -r file_date file_time _size file_name; do
    [ -n "${file_name:-}" ] || continue
    file_epoch="$(to_epoch "$file_date")"
    age_days="$(( (now_epoch - file_epoch) / 86400 ))"
    if [ "$age_days" -gt "$RETENTION_DAYS" ]; then
        aws s3 rm "s3://${S3_BUCKET}/${S3_BACKUP_PREFIX}/${file_name}"
        log "Deleted expired S3 backup: ${file_name}"
    fi
done

log "Backup complete"
