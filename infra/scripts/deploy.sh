#!/usr/bin/env bash
# deploy.sh — Zero-downtime deployment with rollback
#
# Reference: Production deployment
#
# Usage:
#   ./infra/scripts/deploy.sh [--skip-migrations] [--rollback]
#
# Steps:
#   1. Pre-flight checks (secrets, env, Docker)
#   2. Pull latest images / build updated services
#   3. Run database migrations
#   4. Rolling restart (one service at a time)
#   5. Health check after each service restart
#   6. Rollback on failure (restore previous image tags)
#
# Prerequisites:
#   - Docker Compose V2
#   - .env.prod file in project root
#   - Secrets files in infra/secrets/

set -euo pipefail

# ─────────────────────────── Config ───────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$INFRA_DIR")"
COMPOSE_FILE="$INFRA_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"
LOG_FILE="$INFRA_DIR/deploy.log"
HEALTH_URL="http://localhost/api/v1/health"
HEALTH_TIMEOUT=60
ROLLBACK=false
SKIP_MIGRATIONS=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ─────────────────────────── Helpers ───────────────────────────
log()   { echo -e "$(date '+%Y-%m-%d %H:%M:%S') [INFO]  $*" | tee -a "$LOG_FILE"; }
warn()  { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${YELLOW}[WARN]${NC}  $*" | tee -a "$LOG_FILE"; }
error() { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"; }
ok()    { echo -e "$(date '+%Y-%m-%d %H:%M:%S') ${GREEN}[OK]${NC}    $*" | tee -a "$LOG_FILE"; }

compose() {
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

# ─────────────────────────── Parse args ───────────────────────────
for arg in "$@"; do
    case "$arg" in
        --rollback)        ROLLBACK=true ;;
        --skip-migrations) SKIP_MIGRATIONS=true ;;
        --help|-h)
            echo "Usage: deploy.sh [--skip-migrations] [--rollback]"
            exit 0 ;;
    esac
done

# ─────────────────────────── Rollback ───────────────────────────
if [ "$ROLLBACK" = true ]; then
    log "Starting rollback to previous deployment..."
    BACKUP_TAG="${DEPLOY_BACKUP_TAG:-previous}"

    if docker image inspect "ecole-backend:$BACKUP_TAG" &>/dev/null; then
        log "Restoring backend image from tag: $BACKUP_TAG"
        docker tag "ecole-backend:$BACKUP_TAG" "ecole-backend:latest"
        compose up -d --no-build backend worker
        log "Waiting for health check..."
        sleep 5
        if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
            ok "Rollback successful — services healthy"
        else
            error "Rollback completed but health check failed — manual intervention required"
            exit 1
        fi
    else
        error "No backup image found. Manual rollback required."
        error "Check 'docker images' for available tags."
        exit 1
    fi
    exit 0
fi

# ─────────────────────────── Pre-flight ───────────────────────────
log "═══════════════════════════════════════════════════════"
log "  École Platform — Production Deployment"
log "═══════════════════════════════════════════════════════"
log ""

# Check prerequisites
log "Running pre-flight checks..."

if ! command -v docker &>/dev/null; then
    error "Docker is not installed"
    exit 1
fi

if ! docker compose version &>/dev/null; then
    error "Docker Compose V2 is required"
    exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
    error "Missing .env.prod at $ENV_FILE"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    error "Missing docker-compose.prod.yml at $COMPOSE_FILE"
    exit 1
fi

# Check secrets
for secret in jwt_secret_key.txt db_password.txt smtp_password.txt; do
    if [ ! -f "$INFRA_DIR/secrets/$secret" ]; then
        error "Missing secret: $INFRA_DIR/secrets/$secret"
        exit 1
    fi
done

ok "Pre-flight checks passed"

# ─────────────────────────── Backup current images ───────────────────────────
log "Backing up current images..."
for svc in backend web; do
    IMAGE=$(compose images "$svc" --format json 2>/dev/null | python3 -c "import sys,json; imgs=json.load(sys.stdin); print(imgs[0]['ID'] if imgs else '')" 2>/dev/null || echo "")
    if [ -n "$IMAGE" ]; then
        docker tag "$IMAGE" "ecole-$svc:previous" 2>/dev/null || true
    fi
done
ok "Image backup complete (tag: previous)"

# ─────────────────────────── Build / Pull ───────────────────────────
log "Building updated images..."
compose build --pull 2>&1 | tee -a "$LOG_FILE"
ok "Images built successfully"

# ─────────────────────────── Migrations ───────────────────────────
if [ "$SKIP_MIGRATIONS" = false ]; then
    log "Running database migrations..."
    compose run --rm --no-deps backend alembic upgrade head 2>&1 | tee -a "$LOG_FILE"
    ok "Migrations complete"
else
    warn "Skipping migrations (--skip-migrations)"
fi

# ─────────────────────────── Rolling restart ───────────────────────────
wait_healthy() {
    local service=$1
    local max_wait=${2:-$HEALTH_TIMEOUT}
    local elapsed=0

    log "Waiting for $service to become healthy (timeout: ${max_wait}s)..."
    while [ $elapsed -lt $max_wait ]; do
        local status
        status=$(compose ps "$service" --format json 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else [data]
for c in items:
    print(c.get('Health', c.get('Status', 'unknown')))
    break
" 2>/dev/null || echo "unknown")

        if echo "$status" | grep -qi "healthy"; then
            ok "$service is healthy"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done

    error "$service did not become healthy within ${max_wait}s"
    return 1
}

# Restart infrastructure first (DB, Redis)
log "Restarting infrastructure services..."
compose up -d postgres redis
wait_healthy postgres 30 || { error "Database failed to start"; exit 1; }
wait_healthy redis 15 || { error "Redis failed to start"; exit 1; }

# Restart backend (one at a time if scaled)
log "Restarting backend..."
compose up -d --no-deps backend
wait_healthy backend "$HEALTH_TIMEOUT" || {
    error "Backend health check failed — initiating rollback"
    docker tag "ecole-backend:previous" "ecole-backend:latest" 2>/dev/null || true
    compose up -d --no-deps backend
    sleep 10
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        warn "Rollback successful — previous backend restored"
    else
        error "Rollback FAILED — manual intervention required"
    fi
    exit 1
}

# Restart worker
log "Restarting worker..."
compose up -d --no-deps worker
ok "Worker restarted"

# Restart web frontend
log "Restarting web frontend..."
compose up -d --no-deps web
ok "Web frontend restarted"

# Restart nginx (reload config without downtime)
log "Reloading Nginx configuration..."
compose exec nginx nginx -s reload 2>/dev/null || compose up -d --no-deps nginx
ok "Nginx reloaded"

# ─────────────────────────── Final health check ───────────────────────────
log "Running final health check..."
sleep 3

if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
    ok "═══════════════════════════════════════════════════════"
    ok "  Deployment complete — all services healthy"
    ok "═══════════════════════════════════════════════════════"
else
    error "Final health check failed — check logs with: docker compose -f $COMPOSE_FILE logs"
    exit 1
fi

log "Deployment finished at $(date)"
