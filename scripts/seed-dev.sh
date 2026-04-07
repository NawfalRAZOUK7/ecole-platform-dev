#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  COMPOSE="docker compose"
fi

$COMPOSE -f docker-compose.dev.yml run --rm backend alembic upgrade head
$COMPOSE -f docker-compose.dev.yml run --rm backend python -m app.seed
