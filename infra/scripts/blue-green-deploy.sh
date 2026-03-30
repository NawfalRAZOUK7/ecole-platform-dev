#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:?Usage: blue-green-deploy.sh <image-tag>}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$INFRA_DIR")"
ENV_FILE="${ENV_FILE:-$PROJECT_DIR/.env.prod}"
ACTIVE_FILE="${ACTIVE_FILE:-$INFRA_DIR/active-env}"
UPSTREAM_FILE="${UPSTREAM_FILE:-$INFRA_DIR/nginx/upstream.conf}"
PROD_COMPOSE="$INFRA_DIR/docker-compose.prod.yml"

active_env="$(cat "$ACTIVE_FILE" 2>/dev/null || echo blue)"
if [ "$active_env" = "blue" ]; then
    next_env="green"
    next_port="8002"
else
    next_env="blue"
    next_port="8001"
fi

next_compose="$INFRA_DIR/docker-compose.${next_env}.yml"
active_compose="$INFRA_DIR/docker-compose.${active_env}.yml"
backend_service="backend-${next_env}"
health_url="http://localhost:${next_port}/api/v1/health"

compose_next() {
    docker compose -f "$next_compose" --env-file "$ENV_FILE" "$@"
}

compose_prod() {
    docker compose -f "$PROD_COMPOSE" --env-file "$ENV_FILE" "$@"
}

printf '=== Deploying %s to %s (active: %s) ===\n' "$IMAGE_TAG" "$next_env" "$active_env"

export IMAGE_TAG
compose_next pull
compose_next up -d
compose_next exec -T "$backend_service" alembic upgrade head

for _ in $(seq 1 12); do
    if curl -sf "$health_url" >/dev/null 2>&1; then
        echo "  ${next_env} is healthy"
        break
    fi
    sleep 5
done

if ! curl -sf "$health_url" >/dev/null 2>&1; then
    echo "FATAL: ${next_env} failed health check"
    compose_next down
    exit 1
fi

cat > "$UPSTREAM_FILE" <<EOF
upstream backend_active {
    server ecole-backend-${next_env}:8000;
}
EOF

compose_prod exec -T nginx nginx -s reload
printf '%s\n' "$next_env" > "$ACTIVE_FILE"

echo "  Draining ${active_env}..."
sleep 30
docker compose -f "$active_compose" --env-file "$ENV_FILE" down >/dev/null 2>&1 || true

echo "=== Deploy complete: ${next_env} is now active ==="
