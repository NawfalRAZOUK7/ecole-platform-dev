#!/usr/bin/env bash
set -euo pipefail

SECRET_TYPE="${1:?Usage: rotate-secrets.sh <jwt|db|redis|all>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${COMPOSE_FILE:-$INFRA_DIR/docker-compose.prod.yml}"
SECRETS_DIR="${SECRETS_DIR:-$INFRA_DIR/secrets}"
LOG_FILE="${SECRET_ROTATION_LOG:-$INFRA_DIR/secret-rotation.log}"
JWT_DUAL_WINDOW_SECONDS="${JWT_DUAL_WINDOW_SECONDS:-1800}"
DATABASE_USER="${DATABASE_USER:-ecole}"
DATABASE_NAME="${DATABASE_NAME:-ecole_platform}"
DATABASE_HOST="${DATABASE_HOST:-pgbouncer}"
REDIS_HOST="${REDIS_HOST:-redis}"

log() {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ROTATE: $*" | tee -a "$LOG_FILE"
}

compose() {
    docker compose -f "$COMPOSE_FILE" "$@"
}

ensure_secret_dir() {
    mkdir -p "$SECRETS_DIR"
}

rotate_jwt() {
    ensure_secret_dir
    log "Rotating JWT secret"
    local new_secret
    new_secret="$(openssl rand -hex 32)"
    local secret_file="$SECRETS_DIR/jwt_secret_key.txt"
    local next_secret_file="$SECRETS_DIR/jwt_secret_key.next.txt"
    local old_secret=""

    if [ -f "$secret_file" ]; then
        old_secret="$(cat "$secret_file")"
    fi

    printf '%s\n' "$new_secret" > "$next_secret_file"

    if [ -n "$old_secret" ]; then
        log "Starting dual-key window"
        JWT_DUAL_KEY="${old_secret},${new_secret}" compose exec -T backend sh -lc 'kill -HUP 1 || true'
        sleep "$JWT_DUAL_WINDOW_SECONDS"
    fi

    mv "$next_secret_file" "$secret_file"
    compose restart backend >/dev/null
    log "JWT rotation complete"
}

rotate_db() {
    ensure_secret_dir
    log "Rotating database password"
    local new_password
    new_password="$(openssl rand -hex 24)"

    compose exec -T postgres psql -U postgres -c "ALTER USER ${DATABASE_USER} PASSWORD '${new_password}';"
    printf '%s\n' "$new_password" > "$SECRETS_DIR/db_password.txt"
    printf 'postgresql+asyncpg://%s:%s@%s:6432/%s\n' \
        "$DATABASE_USER" "$new_password" "$DATABASE_HOST" "$DATABASE_NAME" \
        > "$SECRETS_DIR/database_url.txt"

    compose restart backend worker >/dev/null
    log "Database password rotation complete"
}

rotate_redis() {
    ensure_secret_dir
    log "Rotating Redis password"
    local new_password
    new_password="$(openssl rand -hex 24)"

    compose exec -T redis redis-cli CONFIG SET requirepass "$new_password" >/dev/null
    printf 'redis://:%s@%s:6379/0\n' "$new_password" "$REDIS_HOST" > "$SECRETS_DIR/redis_url.txt"

    compose restart backend worker >/dev/null
    log "Redis password rotation complete"
}

case "$SECRET_TYPE" in
    jwt)
        rotate_jwt
        ;;
    db)
        rotate_db
        ;;
    redis)
        rotate_redis
        ;;
    all)
        rotate_jwt
        rotate_db
        rotate_redis
        ;;
    *)
        echo "Usage: rotate-secrets.sh <jwt|db|redis|all>" >&2
        exit 1
        ;;
esac
