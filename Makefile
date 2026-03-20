.PHONY: up down restart logs migrate seed test lint shell build clean status health \
       staging-up staging-down prod-up prod-down monitoring-up monitoring-down \
       shell-db redis-cli backup restore docker-prune version \
       migrate-new migrate-down migrate-status test-cov lint-fix format web-install web-lint \
       openapi openapi-check worker worker-logs

# ==================== Compose Files ====================
COMPOSE_FILE = infra/docker-compose.dev.yml
COMPOSE_STAGING = infra/docker-compose.staging.yml
COMPOSE_PROD = infra/docker-compose.prod.yml
COMPOSE_MONITORING = infra/docker-compose.monitoring.yml

DC = docker compose -f $(COMPOSE_FILE)
DC_STAGING = docker compose -f $(COMPOSE_STAGING)
DC_PROD = docker compose -f $(COMPOSE_PROD)
DC_MONITORING = docker compose -f $(COMPOSE_MONITORING)

# App version (from backend health endpoint or fallback)
APP_VERSION := 0.1.0

# ==================== Lifecycle (Dev) ====================

up:
	$(DC) up -d --build

down:
	$(DC) down

restart:
	$(DC) restart

logs:
	$(DC) logs -f

clean:
	$(DC) down -v --remove-orphans

# ==================== Build ====================

build:
	$(DC) build --no-cache

build-prod:
	$(DC_PROD) build --no-cache

# ==================== Staging ====================

staging-up:
	$(DC_STAGING) up -d --build

staging-down:
	$(DC_STAGING) down

staging-logs:
	$(DC_STAGING) logs -f

# ==================== Production ====================

prod-up:
	@echo "Starting production environment..."
	@test -f infra/secrets/jwt_secret_key.txt || (echo "Missing infra/secrets/jwt_secret_key.txt" && exit 1)
	@test -f infra/secrets/db_password.txt || (echo "Missing infra/secrets/db_password.txt" && exit 1)
	$(DC_PROD) up -d --build

prod-down:
	$(DC_PROD) down

prod-logs:
	$(DC_PROD) logs -f

# ==================== Monitoring ====================

monitoring-up:
	$(DC_MONITORING) up -d

monitoring-down:
	$(DC_MONITORING) down

# ==================== Backend ====================

migrate:
	$(DC) exec backend alembic upgrade head

migrate-new:
	$(DC) exec backend alembic revision --autogenerate -m "$(msg)"

migrate-down:
	$(DC) exec backend alembic downgrade -1

migrate-status:
	$(DC) exec backend alembic current
	@echo "---"
	$(DC) exec backend alembic history --verbose

migrate-validate:
	$(DC) exec backend python scripts/validate_migrations.py --verbose

seed:
	$(DC) exec backend python -m app.seed

test:
	$(DC) exec backend pytest -v --tb=short

test-cov:
	$(DC) exec backend pytest --cov=app --cov-report=term-missing --cov-report=html

lint:
	$(DC) exec backend ruff check app/

lint-fix:
	$(DC) exec backend ruff check --fix app/

format:
	$(DC) exec backend ruff format app/

openapi:
	$(DC) exec backend python scripts/export_openapi.py --redoc

openapi-check:
	$(DC) exec backend python scripts/export_openapi.py --check

shell:
	$(DC) exec backend bash

# ==================== Background Worker ====================

worker:
	$(DC) up -d --build worker

worker-logs:
	$(DC) logs -f worker

# ==================== Database ====================

shell-db:
	$(DC) exec postgres psql -U $${POSTGRES_USER:-ecole} -d $${POSTGRES_DB:-ecole_platform}

shell-db-staging:
	$(DC_STAGING) exec postgres psql -U $${POSTGRES_USER:-ecole} -d $${POSTGRES_DB:-ecole_platform_staging}

# ==================== Redis ====================

redis-cli:
	$(DC) exec redis redis-cli

redis-cli-staging:
	$(DC_STAGING) exec redis redis-cli

# ==================== Backup & Restore ====================

backup:
	@echo "Running PostgreSQL backup..."
	bash infra/backup/pg_backup.sh

restore:
	@echo "Running PostgreSQL restore..."
	@echo "Usage: make restore BACKUP_FILE=path/to/backup.sql.gz"
	bash infra/backup/pg_restore.sh $${BACKUP_FILE}

restore-drill:
	@echo "Running restore drill..."
	bash infra/backup/restore_drill.sh

audit-export:
	@echo "Running audit WORM export..."
	bash infra/backup/audit_worm_export.sh

# ==================== Web Frontend ====================

web-install:
	$(DC) exec web npm install

web-lint:
	$(DC) exec web npm run lint

# ==================== Maintenance ====================

docker-prune:
	@echo "Pruning unused Docker resources..."
	docker system prune -f --volumes
	docker image prune -f
	@echo "Docker prune complete."

# ==================== Status & Info ====================

status:
	$(DC) ps

health:
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool || echo 'Backend health check failed'

version:
	@echo "Ecole Platform v$(APP_VERSION)"
	@echo "---"
	@echo "Backend:"
	@curl -sf http://localhost:8000/api/v1/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  version: {d.get(\"version\",\"?\")}')" 2>/dev/null || echo "  (not running)"
	@echo "Docker images:"
	@docker images --format "  {{.Repository}}:{{.Tag}} ({{.Size}})" 2>/dev/null | grep ecole || echo "  (no images)"
	@echo "Compose services:"
	@$(DC) ps --format "  {{.Name}}: {{.Status}}" 2>/dev/null || echo "  (not running)"
