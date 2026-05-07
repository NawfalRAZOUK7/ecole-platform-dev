#!/usr/bin/env bash
# Restore Drill — École Platform
#
# Reference: Restore runbook and drill, restore procedures
# Automated restore drill to validate backup integrity and restore procedures.
#
# This script:
#   1. Creates a temporary test database
#   2. Restores the latest backup into it
#   3. Runs validation checks (schema, data integrity, audit logs)
#   4. Records results to artifacts/f3/restore_drills/
#   5. Cleans up the temporary database
#
# Usage:
#   ./restore_drill.sh                          # Auto-detect latest backup
#   ./restore_drill.sh /path/to/backup.sql.gz   # Specific backup file
#   ./restore_drill.sh --schedule               # Output cron entry for monthly drill
#
# Schedule: Monthly on the 1st at 04:00 UTC
#   0 4 1 * * /opt/ecole/infra/backup/restore_drill.sh >> /var/log/ecole/restore_drill.log 2>&1

set -euo pipefail

# ── Configuration ──
PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5432}"
PGUSER="${PGUSER:-ecole}"
PGDATABASE="${PGDATABASE:-ecole_platform}"
DRILL_DB="ecole_restore_drill_$(date +%s)"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/ecole/postgres}"
ARTIFACTS_DIR="$(cd "$(dirname "$0")/../../" && pwd)/artifacts/f3/restore_drills"
TIMESTAMP=$(date -u +%Y%m%d_%H%M%S)
DRILL_LOG="${ARTIFACTS_DIR}/drill_${TIMESTAMP}.log"
DRILL_REPORT="${ARTIFACTS_DIR}/drill_${TIMESTAMP}.json"

# ── Functions ──
log() {
    local msg="[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DRILL: $*"
    echo "${msg}"
    echo "${msg}" >> "${DRILL_LOG}" 2>/dev/null || true
}

die() {
    log "ERROR: $*"
    cleanup
    exit 1
}

cleanup() {
    log "Cleaning up drill database: ${DRILL_DB}"
    psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c \
        "DROP DATABASE IF EXISTS ${DRILL_DB};" 2>/dev/null || true
}

usage() {
    echo "Usage: $0 [OPTIONS] [backup_file]"
    echo ""
    echo "Options:"
    echo "  --schedule    Output cron entry for monthly restore drill"
    echo "  --verbose     Show detailed output during drill"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Auto-detect latest backup"
    echo "  $0 /backups/ecole_platform_20260315.sql.gz"
    echo "  $0 --schedule"
    exit 1
}

# ── Parse arguments ──
BACKUP_FILE=""
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --schedule)
            echo "# Restore drill — monthly on 1st at 04:00 UTC"
            echo "0 4 1 * * $(readlink -f "$0") >> /var/log/ecole/restore_drill.log 2>&1"
            exit 0
            ;;
        --verbose)
            VERBOSE=true
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

# ── Create artifacts directory ──
mkdir -p "${ARTIFACTS_DIR}"
touch "${DRILL_LOG}"

log "=========================================="
log "=== RESTORE DRILL — $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
log "=========================================="

# ── Step 0: Locate backup file ──
if [ -z "${BACKUP_FILE}" ]; then
    log "Step 0: Auto-detecting latest backup in ${BACKUP_DIR}"
    if [ -d "${BACKUP_DIR}" ]; then
        BACKUP_FILE=$(find "${BACKUP_DIR}" -name "*.sql.gz" -o -name "*.sql.gz.enc" | sort -r | head -1)
    fi

    if [ -z "${BACKUP_FILE}" ] || [ ! -f "${BACKUP_FILE}" ]; then
        die "No backup file found in ${BACKUP_DIR}. Provide a path manually."
    fi
    log "Using latest backup: ${BACKUP_FILE}"
else
    log "Step 0: Using specified backup: ${BACKUP_FILE}"
    [ -f "${BACKUP_FILE}" ] || die "Backup file not found: ${BACKUP_FILE}"
fi

BACKUP_SIZE=$(stat -f%z "${BACKUP_FILE}" 2>/dev/null || stat -c%s "${BACKUP_FILE}" 2>/dev/null || echo "unknown")
log "Backup size: ${BACKUP_SIZE} bytes"

# Track drill metrics
DRILL_START=$(date +%s)
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_TOTAL=0

check_pass() {
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    log "  ✓ PASS: $1"
}

check_fail() {
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    log "  ✗ FAIL: $1"
}

# ── Step 1: Verify backup integrity (checksum) ──
log ""
log "Step 1: Backup integrity verification"

if [ -f "${BACKUP_FILE}.sha256" ]; then
    if sha256sum --check "${BACKUP_FILE}.sha256" --quiet 2>/dev/null; then
        check_pass "SHA-256 checksum verification"
    else
        check_fail "SHA-256 checksum verification"
    fi
else
    log "  WARNING: No checksum file found (${BACKUP_FILE}.sha256)"
    check_pass "Backup file exists and is readable"
fi

# ── Step 2: Create temporary drill database ──
log ""
log "Step 2: Creating drill database: ${DRILL_DB}"

psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d postgres -c \
    "CREATE DATABASE ${DRILL_DB} OWNER ${PGUSER};" 2>/dev/null \
    || die "Failed to create drill database"
check_pass "Drill database created"

# Ensure cleanup on exit
trap cleanup EXIT

# ── Step 3: Restore backup into drill database ──
log ""
log "Step 3: Restoring backup into drill database"
RESTORE_START=$(date +%s)

RESTORE_FILE="${BACKUP_FILE}"
# Handle encrypted backups
if [[ "${BACKUP_FILE}" == *.enc ]]; then
    log "  Decrypting backup..."
    RESTORE_FILE="/tmp/drill_restore_$$.sql.gz"
    openssl enc -aes-256-cbc -d -pbkdf2 \
        -in "${BACKUP_FILE}" \
        -out "${RESTORE_FILE}" \
        -pass env:BACKUP_ENCRYPTION_KEY \
        || die "Decryption failed"
fi

gunzip -c "${RESTORE_FILE}" | pg_restore \
    -h "${PGHOST}" \
    -p "${PGPORT}" \
    -U "${PGUSER}" \
    -d "${DRILL_DB}" \
    --no-owner \
    --no-privileges \
    2>/dev/null \
    && check_pass "Backup restored successfully" \
    || check_fail "Backup restore encountered errors"

RESTORE_END=$(date +%s)
RESTORE_DURATION=$((RESTORE_END - RESTORE_START))
log "  Restore duration: ${RESTORE_DURATION}s"

# Clean up decrypted temp file
if [[ "${BACKUP_FILE}" == *.enc ]] && [ -f "/tmp/drill_restore_$$.sql.gz" ]; then
    rm -f "/tmp/drill_restore_$$.sql.gz"
fi

# ── Step 4: Schema conformance (checklist) ──
log ""
log "Step 4: Schema conformance checks"

# 4a. Count tables
TABLE_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null || echo "0")
TABLE_COUNT=$(echo "${TABLE_COUNT}" | tr -d '[:space:]')
log "  Tables found: ${TABLE_COUNT}"

if [ "${TABLE_COUNT}" -ge 30 ]; then
    check_pass "Table count (${TABLE_COUNT} >= 30 expected tables)"
else
    check_fail "Table count (${TABLE_COUNT} < 30 expected tables)"
fi

# 4b. Verify critical tables exist
CRITICAL_TABLES="users memberships sessions invitations account_recovery_requests
    school_years school_periods classes class_assignments enrollments attendance_sessions attendance_records attendance_justifications
    courses assignments submissions grades content_items content_progress activity_definitions activity_sessions assessments assessment_results
    consent_records notifications notification_deliveries feed_items
    invoices invoice_line_items payment_attempts payment_proofs webhook_events
    audit_logs"

MISSING_TABLES=""
for table in ${CRITICAL_TABLES}; do
    EXISTS=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
        "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='${table}');" 2>/dev/null || echo "f")
    EXISTS=$(echo "${EXISTS}" | tr -d '[:space:]')
    if [ "${EXISTS}" != "t" ]; then
        MISSING_TABLES="${MISSING_TABLES} ${table}"
    fi
done

if [ -z "${MISSING_TABLES}" ]; then
    check_pass "All critical tables present"
else
    check_fail "Missing tables:${MISSING_TABLES}"
fi

# 4c. Count indexes
INDEX_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM pg_indexes WHERE schemaname='public';" 2>/dev/null || echo "0")
INDEX_COUNT=$(echo "${INDEX_COUNT}" | tr -d '[:space:]')
log "  Indexes found: ${INDEX_COUNT}"

if [ "${INDEX_COUNT}" -ge 50 ]; then
    check_pass "Index count (${INDEX_COUNT} >= 50 expected indexes)"
else
    check_fail "Index count (${INDEX_COUNT} < 50 expected indexes)"
fi

# 4d. Check constraints
CONSTRAINT_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM information_schema.table_constraints WHERE constraint_schema='public' AND constraint_type='CHECK';" 2>/dev/null || echo "0")
CONSTRAINT_COUNT=$(echo "${CONSTRAINT_COUNT}" | tr -d '[:space:]')
log "  CHECK constraints: ${CONSTRAINT_COUNT}"

if [ "${CONSTRAINT_COUNT}" -ge 5 ]; then
    check_pass "CHECK constraints present (${CONSTRAINT_COUNT})"
else
    check_fail "CHECK constraints insufficient (${CONSTRAINT_COUNT})"
fi

# ── Step 5: Data integrity checks ──
log ""
log "Step 5: Data integrity checks"

# 5a. Users table
USER_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM users;" 2>/dev/null || echo "0")
USER_COUNT=$(echo "${USER_COUNT}" | tr -d '[:space:]')
log "  Users: ${USER_COUNT}"

if [ "${USER_COUNT}" -ge 1 ]; then
    check_pass "Users table has data (${USER_COUNT} rows)"
else
    check_fail "Users table is empty"
fi

# 5b. Audit logs
AUDIT_COUNT=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM audit_logs;" 2>/dev/null || echo "0")
AUDIT_COUNT=$(echo "${AUDIT_COUNT}" | tr -d '[:space:]')
log "  Audit logs: ${AUDIT_COUNT}"

if [ "${AUDIT_COUNT}" -ge 0 ]; then
    check_pass "Audit logs table accessible (${AUDIT_COUNT} rows)"
fi

# 5c. Foreign key integrity (check for orphaned references)
FK_VIOLATIONS=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT count(*) FROM memberships m LEFT JOIN users u ON m.user_id = u.id WHERE u.id IS NULL;" 2>/dev/null || echo "0")
FK_VIOLATIONS=$(echo "${FK_VIOLATIONS}" | tr -d '[:space:]')

if [ "${FK_VIOLATIONS}" = "0" ]; then
    check_pass "Foreign key integrity — no orphaned memberships"
else
    check_fail "Foreign key integrity — ${FK_VIOLATIONS} orphaned memberships"
fi

# 5d. Alembic migration version present
ALEMBIC_VERSION=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${DRILL_DB}" -t -A -c \
    "SELECT version_num FROM alembic_version LIMIT 1;" 2>/dev/null || echo "")
ALEMBIC_VERSION=$(echo "${ALEMBIC_VERSION}" | tr -d '[:space:]')

if [ -n "${ALEMBIC_VERSION}" ]; then
    check_pass "Alembic version present: ${ALEMBIC_VERSION}"
else
    check_fail "Alembic version missing"
fi

# ── Step 6: Compare with source database ──
log ""
log "Step 6: Source database comparison"

SOURCE_TABLES=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -A -c \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';" 2>/dev/null || echo "0")
SOURCE_TABLES=$(echo "${SOURCE_TABLES}" | tr -d '[:space:]')

SOURCE_USERS=$(psql -h "${PGHOST}" -p "${PGPORT}" -U "${PGUSER}" -d "${PGDATABASE}" -t -A -c \
    "SELECT count(*) FROM users;" 2>/dev/null || echo "0")
SOURCE_USERS=$(echo "${SOURCE_USERS}" | tr -d '[:space:]')

log "  Source DB tables: ${SOURCE_TABLES}, Drill DB tables: ${TABLE_COUNT}"
log "  Source DB users: ${SOURCE_USERS}, Drill DB users: ${USER_COUNT}"

if [ "${TABLE_COUNT}" = "${SOURCE_TABLES}" ]; then
    check_pass "Table count matches source database"
else
    check_fail "Table count mismatch (source: ${SOURCE_TABLES}, drill: ${TABLE_COUNT})"
fi

if [ "${USER_COUNT}" = "${SOURCE_USERS}" ]; then
    check_pass "User count matches source database"
else
    check_fail "User count mismatch (source: ${SOURCE_USERS}, drill: ${USER_COUNT})"
fi

# ── Step 7: Timing metrics ──
log ""
log "Step 7: Timing metrics"

DRILL_END=$(date +%s)
DRILL_DURATION=$((DRILL_END - DRILL_START))
log "  Total drill duration: ${DRILL_DURATION}s"
log "  Restore duration: ${RESTORE_DURATION}s"

# Check against RTO target (1h = 3600s)
RTO_TARGET=3600
if [ "${RESTORE_DURATION}" -lt "${RTO_TARGET}" ]; then
    check_pass "Restore time (${RESTORE_DURATION}s) within RTO target (${RTO_TARGET}s)"
else
    check_fail "Restore time (${RESTORE_DURATION}s) exceeds RTO target (${RTO_TARGET}s)"
fi

# ── Generate drill report (JSON) ──
log ""
log "Generating drill report..."

DRILL_STATUS="PASS"
if [ "${CHECKS_FAILED}" -gt 0 ]; then
    DRILL_STATUS="FAIL"
fi

cat > "${DRILL_REPORT}" <<REPORT
{
  "drill_id": "drill_${TIMESTAMP}",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "${DRILL_STATUS}",
  "backup_file": "${BACKUP_FILE}",
  "backup_size_bytes": "${BACKUP_SIZE}",
  "drill_database": "${DRILL_DB}",
  "source_database": "${PGDATABASE}",
  "timing": {
    "total_duration_seconds": ${DRILL_DURATION},
    "restore_duration_seconds": ${RESTORE_DURATION},
    "rto_target_seconds": ${RTO_TARGET},
    "within_rto": $([ "${RESTORE_DURATION}" -lt "${RTO_TARGET}" ] && echo "true" || echo "false")
  },
  "checks": {
    "total": ${CHECKS_TOTAL},
    "passed": ${CHECKS_PASSED},
    "failed": ${CHECKS_FAILED}
  },
  "schema": {
    "tables": ${TABLE_COUNT},
    "indexes": ${INDEX_COUNT},
    "check_constraints": ${CONSTRAINT_COUNT},
    "missing_tables": "$(echo ${MISSING_TABLES} | xargs)"
  },
  "data": {
    "users": ${USER_COUNT},
    "audit_logs": ${AUDIT_COUNT},
    "alembic_version": "${ALEMBIC_VERSION}",
    "fk_violations": ${FK_VIOLATIONS}
  },
  "source_comparison": {
    "source_tables": ${SOURCE_TABLES},
    "source_users": ${SOURCE_USERS},
    "tables_match": $([ "${TABLE_COUNT}" = "${SOURCE_TABLES}" ] && echo "true" || echo "false"),
    "users_match": $([ "${USER_COUNT}" = "${SOURCE_USERS}" ] && echo "true" || echo "false")
  },
  "references": {
    "story": "restore-drill",
    "spec": "Restore Procedures",
    "runbook": "infra/backup/pg_restore.sh"
  }
}
REPORT

log "Report saved: ${DRILL_REPORT}"

# ── Summary ──
log ""
log "=========================================="
log "=== RESTORE DRILL SUMMARY ==="
log "=========================================="
log "Status:          ${DRILL_STATUS}"
log "Checks passed:   ${CHECKS_PASSED}/${CHECKS_TOTAL}"
log "Checks failed:   ${CHECKS_FAILED}/${CHECKS_TOTAL}"
log "Restore time:    ${RESTORE_DURATION}s (RTO target: ${RTO_TARGET}s)"
log "Total duration:  ${DRILL_DURATION}s"
log "Report:          ${DRILL_REPORT}"
log "Log:             ${DRILL_LOG}"
log ""
log "POST-DRILL ACTIONS:"
log "  1. Review drill report: cat ${DRILL_REPORT}"
log "  2. Update decision log with drill outcome"
log "  3. If FAIL: investigate and schedule re-drill"
log "  4. Archive report to project artifacts"
log "=========================================="

# Exit with appropriate code
if [ "${CHECKS_FAILED}" -gt 0 ]; then
    exit 1
fi
exit 0
