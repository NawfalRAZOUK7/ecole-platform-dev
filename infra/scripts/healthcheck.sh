#!/usr/bin/env bash
# healthcheck.sh — Comprehensive health check for all production services
#
# Reference: Health monitoring
#
# Usage:
#   ./infra/scripts/healthcheck.sh           # Full check (exit 0 = healthy)
#   ./infra/scripts/healthcheck.sh --json    # Output as JSON
#   ./infra/scripts/healthcheck.sh --quiet   # Only exit code
#
# Checks:
#   1. API health endpoint
#   2. PostgreSQL connectivity
#   3. Redis connectivity
#   4. Disk space usage
#   5. TLS certificate expiry
#   6. Docker container status
#
# Cron (every 5 minutes):
#   */5 * * * * /path/to/infra/scripts/healthcheck.sh --quiet || /path/to/alert.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
CERTS_DIR="$INFRA_DIR/certs"

# Config
API_URL="${API_URL:-http://localhost/api/v1/health}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-ecole}"
DB_NAME="${DB_NAME:-ecole_platform}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
DISK_WARN_THRESHOLD=80
DISK_CRIT_THRESHOLD=90
CERT_WARN_DAYS=30
CERT_CRIT_DAYS=7

# Output mode
OUTPUT_JSON=false
QUIET=false
for arg in "$@"; do
    case "$arg" in
        --json)  OUTPUT_JSON=true ;;
        --quiet) QUIET=true ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Track overall status
OVERALL_STATUS=0
declare -A RESULTS

# ─────────────────────────── Check functions ───────────────────────────

check_api() {
    local name="api"
    local status="ok"
    local detail=""

    if response=$(curl -sf -o /dev/null -w "%{http_code}:%{time_total}" "$API_URL" 2>/dev/null); then
        local code="${response%%:*}"
        local time="${response##*:}"
        if [ "$code" = "200" ]; then
            detail="HTTP 200 (${time}s)"
        else
            status="warn"
            detail="HTTP $code (${time}s)"
            OVERALL_STATUS=1
        fi
    else
        status="critical"
        detail="Unreachable"
        OVERALL_STATUS=2
    fi

    RESULTS[$name]="$status|$detail"
}

check_postgres() {
    local name="postgres"
    local status="ok"
    local detail=""

    # Try via Docker first
    if docker exec ecole-prod-postgres pg_isready -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
        # Check connection count
        local conn_count
        conn_count=$(docker exec ecole-prod-postgres psql -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null || echo "?")
        detail="Healthy (active connections: $conn_count)"
    elif pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" &>/dev/null; then
        detail="Healthy (direct connection)"
    else
        status="critical"
        detail="Unreachable"
        OVERALL_STATUS=2
    fi

    RESULTS[$name]="$status|$detail"
}

check_redis() {
    local name="redis"
    local status="ok"
    local detail=""

    if docker exec ecole-prod-redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        # Check memory usage
        local mem_used
        mem_used=$(docker exec ecole-prod-redis redis-cli info memory 2>/dev/null | grep "used_memory_human" | cut -d: -f2 | tr -d '\r' || echo "?")
        detail="Healthy (memory: $mem_used)"
    elif redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q "PONG"; then
        detail="Healthy (direct connection)"
    else
        status="critical"
        detail="Unreachable"
        OVERALL_STATUS=2
    fi

    RESULTS[$name]="$status|$detail"
}

check_disk() {
    local name="disk"
    local status="ok"
    local detail=""

    # Check root partition usage
    local usage
    usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

    if [ "$usage" -ge "$DISK_CRIT_THRESHOLD" ]; then
        status="critical"
        detail="Root partition at ${usage}% (critical threshold: ${DISK_CRIT_THRESHOLD}%)"
        OVERALL_STATUS=2
    elif [ "$usage" -ge "$DISK_WARN_THRESHOLD" ]; then
        status="warn"
        detail="Root partition at ${usage}% (warning threshold: ${DISK_WARN_THRESHOLD}%)"
        [ $OVERALL_STATUS -lt 1 ] && OVERALL_STATUS=1
    else
        detail="Root partition at ${usage}%"
    fi

    # Check Docker data usage
    local docker_usage
    docker_usage=$(docker system df --format '{{.Size}}' 2>/dev/null | head -1 || echo "?")
    detail="$detail, Docker: $docker_usage"

    RESULTS[$name]="$status|$detail"
}

check_certs() {
    local name="certificates"
    local status="ok"
    local detail=""

    local has_certs=false

    for domain_dir in "$CERTS_DIR/live"/*/; do
        if [ ! -d "$domain_dir" ]; then continue; fi
        local domain
        domain=$(basename "$domain_dir")
        local cert_file="$domain_dir/fullchain.pem"
        if [ ! -f "$cert_file" ]; then continue; fi

        has_certs=true
        local expiry
        expiry=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
        local expiry_epoch
        expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" +%s 2>/dev/null || echo "0")
        local now_epoch
        now_epoch=$(date +%s)
        local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

        if [ "$days_left" -lt "$CERT_CRIT_DAYS" ]; then
            status="critical"
            detail="$domain: ${days_left} days until expiry"
            OVERALL_STATUS=2
        elif [ "$days_left" -lt "$CERT_WARN_DAYS" ]; then
            status="warn"
            detail="$domain: ${days_left} days until expiry"
            [ $OVERALL_STATUS -lt 1 ] && OVERALL_STATUS=1
        else
            detail="$domain: valid for ${days_left} days"
        fi
    done

    # Also check direct cert files (non-Let's Encrypt)
    if [ "$has_certs" = false ]; then
        for cert_file in "$CERTS_DIR/fullchain.pem" "$CERTS_DIR/cert.pem"; do
            if [ -f "$cert_file" ]; then
                has_certs=true
                local expiry
                expiry=$(openssl x509 -enddate -noout -in "$cert_file" 2>/dev/null | cut -d= -f2)
                local expiry_epoch
                expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || date -j -f "%b %d %H:%M:%S %Y %Z" "$expiry" +%s 2>/dev/null || echo "0")
                local now_epoch
                now_epoch=$(date +%s)
                local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

                if [ "$days_left" -lt "$CERT_CRIT_DAYS" ]; then
                    status="critical"
                    OVERALL_STATUS=2
                elif [ "$days_left" -lt "$CERT_WARN_DAYS" ]; then
                    status="warn"
                    [ $OVERALL_STATUS -lt 1 ] && OVERALL_STATUS=1
                fi
                detail="valid for ${days_left} days"
            fi
        done
    fi

    if [ "$has_certs" = false ]; then
        status="warn"
        detail="No certificates found"
        [ $OVERALL_STATUS -lt 1 ] && OVERALL_STATUS=1
    fi

    RESULTS[$name]="$status|$detail"
}

check_containers() {
    local name="containers"
    local status="ok"
    local detail=""
    local unhealthy=0
    local total=0

    local expected_containers=("ecole-prod-postgres" "ecole-prod-redis" "ecole-prod-nginx" "ecole-prod-web" "ecole-prod-worker")

    for container in "${expected_containers[@]}"; do
        total=$((total + 1))
        local state
        state=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "missing")

        if [ "$state" != "running" ]; then
            unhealthy=$((unhealthy + 1))
            detail="${detail}${container}=${state} "
        fi
    done

    # Also check backend (may be scaled, no fixed name)
    local backend_count
    backend_count=$(docker ps --filter "name=backend" --filter "status=running" --format '{{.ID}}' 2>/dev/null | wc -l | tr -d ' ')
    total=$((total + 1))
    if [ "$backend_count" -eq 0 ]; then
        unhealthy=$((unhealthy + 1))
        detail="${detail}backend=missing "
    fi

    if [ "$unhealthy" -gt 0 ]; then
        status="critical"
        detail="$unhealthy/$total containers unhealthy: $detail"
        OVERALL_STATUS=2
    else
        detail="All $total containers running (backend instances: $backend_count)"
    fi

    RESULTS[$name]="$status|$detail"
}

# ─────────────────────────── Run all checks ───────────────────────────

check_api
check_postgres
check_redis
check_disk
check_certs
check_containers

# ─────────────────────────── Output ───────────────────────────

if [ "$OUTPUT_JSON" = true ]; then
    echo "{"
    echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
    echo "  \"status\": $([ $OVERALL_STATUS -eq 0 ] && echo '"healthy"' || ([ $OVERALL_STATUS -eq 1 ] && echo '"degraded"' || echo '"critical"')),"
    echo "  \"checks\": {"
    local first=true
    for key in "${!RESULTS[@]}"; do
        local val="${RESULTS[$key]}"
        local s="${val%%|*}"
        local d="${val##*|}"
        if [ "$first" = true ]; then first=false; else echo ","; fi
        printf '    "%s": {"status": "%s", "detail": "%s"}' "$key" "$s" "$d"
    done
    echo ""
    echo "  }"
    echo "}"
elif [ "$QUIET" = false ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  École Platform — Health Check Report"
    echo "  $(date)"
    echo "═══════════════════════════════════════════════════════"
    echo ""

    for key in api postgres redis disk certificates containers; do
        if [ -z "${RESULTS[$key]+x}" ]; then continue; fi
        local val="${RESULTS[$key]}"
        local s="${val%%|*}"
        local d="${val##*|}"

        local icon
        case "$s" in
            ok)       icon="${GREEN}✓${NC}" ;;
            warn)     icon="${YELLOW}⚠${NC}" ;;
            critical) icon="${RED}✗${NC}" ;;
        esac

        printf "  ${icon}  %-15s %s\n" "$key" "$d"
    done

    echo ""
    case $OVERALL_STATUS in
        0) echo -e "  Overall: ${GREEN}HEALTHY${NC}" ;;
        1) echo -e "  Overall: ${YELLOW}DEGRADED${NC}" ;;
        2) echo -e "  Overall: ${RED}CRITICAL${NC}" ;;
    esac
    echo ""
fi

exit $OVERALL_STATUS
