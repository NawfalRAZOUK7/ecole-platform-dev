#!/usr/bin/env bash
# Audit log WORM export — École Platform
#
# Reference: Configure audit log WORM export, backup strategy matrix
# Daily append-only export of audit_logs to immutable storage.
# Retention: 180 days. AES-256 encryption + SHA-256 integrity.
#
# Usage:
#   ./audit_worm_export.sh                      # Export today's audit logs
#   ./audit_worm_export.sh --date 2026-03-14    # Export specific date
#   ./audit_worm_export.sh --verify             # Verify all exports integrity
#   ./audit_worm_export.sh --prune              # Remove exports older than 180 days
#
# WORM Semantics:
#   - Each daily export is append-only (new file per day, never overwritten)
#   - Existing export files are never modified (immutable once written)
#   - Exports include SHA-256 checksum manifest for tamper detection
#   - Optional AES-256-CBC encryption for compliance
#
# Cron: 03:30 UTC daily (after pg_backup at 02:00)
#   30 3 * * * /opt/ecole/infra/backup/audit_worm_export.sh >> /var/log/ecole/audit_export.log 2>&1

set -euo pipefail

# ── Configuration ──
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-ecole}"
PGDATABASE="${PGDATABASE:-ecole_platform}"
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-}"

EXPORT_DIR="${AUDIT_EXPORT_DIR:-/var/backups/ecole/audit}"
RETENTION_DAYS=180  # F3: 180-day retention for audit logs
EXPORT_FORMAT="jsonl"  # JSON Lines — one JSON object per audit entry

# ── Functions ──
log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] AUDIT-EXPORT: $*"
}

die() {
    log "ERROR: $*"
    exit 1
}

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --date <YYYY-MM-DD>   Export audit logs for a specific date (default: yesterday)"
    echo "  --verify              Verify integrity of all existing exports"
    echo "  --prune               Remove exports older than ${RETENTION_DAYS} days"
    echo "  --dry-run             Show what would be exported without writing"
    echo ""
    echo "Environment variables:"
    echo "  PGHOST, PGPORT, PGUSER, PGDATABASE — PostgreSQL connection"
    echo "  BACKUP_ENCRYPTION_KEY — Optional AES-256 encryption key"
    echo "  AUDIT_EXPORT_DIR — Export directory (default: /var/backups/ecole/audit)"
    exit 1
}

# ── Parse arguments ──
EXPORT_DATE=""
VERIFY_ONLY=false
PRUNE_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --date)
            EXPORT_DATE="$2"
            shift 2
            ;;
        --verify)
            VERIFY_ONLY=true
            shift
            ;;
        --prune)
            PRUNE_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

# Default to yesterday (complete day of logs)
if [ -z "${EXPORT_DATE}" ]; then
    EXPORT_DATE=$(date -u -d "yesterday" +%Y-%m-%d 2>/dev/null || date -u -v-1d +%Y-%m-%d)
fi

# ── Verify mode ──
if [ "${VERIFY_ONLY}" = true ]; then
    log "=== Audit Export Integrity Verification ==="
    FAILURES=0
    CHECKED=0

    if [ ! -d "${EXPORT_DIR}" ]; then
        die "Export directory does not exist: ${EXPORT_DIR}"
    fi

    for checksum_file in "${EXPORT_DIR}"/*.sha256; do
        [ -f "${checksum_file}" ] || continue
        CHECKED=$((CHECKED + 1))
        if sha256sum --check "${checksum_file}" --quiet 2>/dev/null; then
            log "  OK: $(basename "${checksum_file%.sha256}")"
        else
            log "  FAIL: $(basename "${checksum_file%.sha256}")"
            FAILURES=$((FAILURES + 1))
        fi
    done

    log "Checked: ${CHECKED}, Failures: ${FAILURES}"
    [ "${FAILURES}" -eq 0 ] || die "Integrity verification failed for ${FAILURES} export(s)"
    log "All exports verified OK"
    exit 0
fi

# ── Prune mode ──
if [ "${PRUNE_ONLY}" = true ]; then
    log "=== Pruning exports older than ${RETENTION_DAYS} days ==="

    if [ ! -d "${EXPORT_DIR}" ]; then
        log "Export directory does not exist: ${EXPORT_DIR}. Nothing to prune."
        exit 0
    fi

    PRUNED=0
    find "${EXPORT_DIR}" -name "audit_*.${EXPORT_FORMAT}*" -mtime +${RETENTION_DAYS} -type f | while read -r file; do
        if [ "${DRY_RUN}" = true ]; then
            log "  Would remove: $(basename "${file}")"
        else
            rm -f "${file}"
            log "  Removed: $(basename "${file}")"
        fi
        PRUNED=$((PRUNED + 1))
    done

    # Also prune orphan checksum and manifest files
    find "${EXPORT_DIR}" -name "audit_*.sha256" -mtime +${RETENTION_DAYS} -type f -exec rm -f {} \; 2>/dev/null || true
    find "${EXPORT_DIR}" -name "audit_*.manifest" -mtime +${RETENTION_DAYS} -type f -exec rm -f {} \; 2>/dev/null || true

    log "Pruning complete"
    exit 0
fi

# ── Export mode ──
log "=== Audit Log WORM Export ==="
log "Date: ${EXPORT_DATE}"
log "Target: ${EXPORT_DIR}"

# Create export directory (append-only: new files only, never overwrite)
mkdir -p "${EXPORT_DIR}"

# Define output filenames
BASE_NAME="audit_${EXPORT_DATE}"
EXPORT_FILE="${EXPORT_DIR}/${BASE_NAME}.${EXPORT_FORMAT}.gz"
MANIFEST_FILE="${EXPORT_DIR}/${BASE_NAME}.manifest"
CHECKSUM_FILE="${EXPORT_DIR}/${BASE_NAME}.${EXPORT_FORMAT}.gz.sha256"

# WORM check: refuse to overwrite existing export (immutability guarantee)
if [ -f "${EXPORT_FILE}" ]; then
    log "Export already exists for ${EXPORT_DATE}: ${EXPORT_FILE}"
    log "WORM policy: existing exports are immutable and cannot be overwritten."
    log "To re-export, first remove the existing file manually (requires ops approval)."
    exit 0
fi

# ── Step 1: Count records for the target date ──
RECORD_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -A -c \
    "SELECT count(*) FROM audit_logs WHERE created_at >= '${EXPORT_DATE}'::date AND created_at < ('${EXPORT_DATE}'::date + interval '1 day');" \
    2>/dev/null || echo "0")

RECORD_COUNT=$(echo "${RECORD_COUNT}" | tr -d '[:space:]')
log "Records to export: ${RECORD_COUNT}"

if [ "${RECORD_COUNT}" = "0" ]; then
    log "No audit records found for ${EXPORT_DATE}. Skipping export."
    exit 0
fi

if [ "${DRY_RUN}" = true ]; then
    log "DRY RUN: Would export ${RECORD_COUNT} records to ${EXPORT_FILE}"
    exit 0
fi

# ── Step 2: Export audit logs as JSON Lines (one JSON object per line) ──
log "Step 2: Exporting audit logs as JSONL..."

TEMP_FILE=$(mktemp "/tmp/audit_export_XXXXXX.${EXPORT_FORMAT}")
trap 'rm -f "${TEMP_FILE}"' EXIT

psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -A -c \
    "SELECT row_to_json(t) FROM (
        SELECT
            id,
            action,
            actor_id,
            actor_role,
            resource_type,
            resource_id,
            school_id,
            ip_address,
            correlation_id,
            details,
            created_at
        FROM audit_logs
        WHERE created_at >= '${EXPORT_DATE}'::date
          AND created_at < ('${EXPORT_DATE}'::date + interval '1 day')
        ORDER BY created_at ASC
    ) t;" > "${TEMP_FILE}" 2>/dev/null

EXPORTED=$(wc -l < "${TEMP_FILE}" | tr -d '[:space:]')
log "Exported ${EXPORTED} records to temp file"

# Verify record count matches
if [ "${EXPORTED}" != "${RECORD_COUNT}" ]; then
    log "WARNING: Expected ${RECORD_COUNT} records but exported ${EXPORTED}"
fi

# ── Step 3: Compress ──
log "Step 3: Compressing export..."
gzip -c "${TEMP_FILE}" > "${EXPORT_FILE}"
FILESIZE=$(stat -f%z "${EXPORT_FILE}" 2>/dev/null || stat -c%s "${EXPORT_FILE}" 2>/dev/null || echo "unknown")
log "Compressed size: ${FILESIZE} bytes"

# ── Step 4: Optional encryption ──
if [ -n "${ENCRYPTION_KEY}" ]; then
    log "Step 4: Encrypting export (AES-256-CBC)..."
    ENCRYPTED_FILE="${EXPORT_FILE}.enc"
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in "${EXPORT_FILE}" \
        -out "${ENCRYPTED_FILE}" \
        -pass env:BACKUP_ENCRYPTION_KEY

    # Replace unencrypted file with encrypted version
    mv "${ENCRYPTED_FILE}" "${EXPORT_FILE}"
    EXPORT_FILE="${EXPORT_FILE}"  # Keep same name for checksum
    log "Encryption complete"
else
    log "Step 4: Skipping encryption (BACKUP_ENCRYPTION_KEY not set)"
fi

# ── Step 5: Generate SHA-256 checksum ──
log "Step 5: Generating checksum..."
(cd "${EXPORT_DIR}" && sha256sum "$(basename "${EXPORT_FILE}")" > "${CHECKSUM_FILE}")
log "Checksum: $(cat "${CHECKSUM_FILE}")"

# ── Step 6: Write manifest (metadata for audit trail) ──
log "Step 6: Writing manifest..."
cat > "${MANIFEST_FILE}" <<MANIFEST
{
  "export_date": "${EXPORT_DATE}",
  "export_timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "database": "${PGDATABASE}",
  "host": "${PGHOST}",
  "record_count": ${EXPORTED},
  "format": "jsonl",
  "compressed": true,
  "encrypted": $([ -n "${ENCRYPTION_KEY}" ] && echo "true" || echo "false"),
  "retention_days": ${RETENTION_DAYS},
  "checksum_algorithm": "SHA-256",
  "checksum_file": "$(basename "${CHECKSUM_FILE}")",
  "export_file": "$(basename "${EXPORT_FILE}")",
  "worm_policy": "append-only, immutable once written",
  "compliance_ref": "Backup Strategy Matrix"
}
MANIFEST

# ── Step 7: Set immutable attribute (if supported by filesystem) ──
log "Step 7: Setting immutable file attributes..."
if command -v chattr >/dev/null 2>&1; then
    chattr +i "${EXPORT_FILE}" 2>/dev/null && log "  Set immutable: ${EXPORT_FILE}" || log "  WARNING: Cannot set immutable attribute (may need root)"
    chattr +i "${CHECKSUM_FILE}" 2>/dev/null && log "  Set immutable: ${CHECKSUM_FILE}" || true
    chattr +i "${MANIFEST_FILE}" 2>/dev/null && log "  Set immutable: ${MANIFEST_FILE}" || true
else
    log "  WARNING: chattr not available — immutable attributes not set"
    log "  For production, use filesystem-level WORM (e.g., AWS S3 Object Lock)"
fi

# ── Summary ──
log "=== Audit WORM Export Complete ==="
log "Date:       ${EXPORT_DATE}"
log "Records:    ${EXPORTED}"
log "File:       ${EXPORT_FILE}"
log "Checksum:   ${CHECKSUM_FILE}"
log "Manifest:   ${MANIFEST_FILE}"
log "Retention:  ${RETENTION_DAYS} days"
log "Status:     SUCCESS"
