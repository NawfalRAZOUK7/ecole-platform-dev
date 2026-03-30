.PHONY: up down restart logs migrate seed test lint shell build clean status health \
       staging-up staging-down prod-up prod-down monitoring-up monitoring-down \
       shell-db redis-cli backup restore backup-status docker-prune version \
       migrate-new migrate-down migrate-status test-cov lint-fix format web-install web-lint \
       openapi openapi-check worker worker-logs test-unit test-integration test-security \
       test-full test-perf

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

hooks-install: ## Install pre-commit hooks
	python3 -m pip install pre-commit
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "Pre-commit hooks installed"

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
	@echo "Running PostgreSQL backup to S3..."
	bash infra/scripts/backup-s3.sh

restore:
	@echo "Running PostgreSQL restore..."
	@echo "Usage: make restore BACKUP_FILE=path/to/backup.sql.gz"
	bash infra/backup/pg_restore.sh $${BACKUP_FILE}

restore-drill:
	@echo "Running S3 restore drill..."
	bash infra/scripts/restore-drill.sh

backup-status:
	@echo "Latest local backups:"
	@find $${BACKUP_DIR:-/var/backups/ecole/postgresql} -maxdepth 1 -name '*.sql.gz' -print 2>/dev/null | sort | tail -5 || true
	@echo "---"
	@echo "Latest S3 backups:"
	@bash -lc 'aws s3 ls "s3://$${S3_BUCKET:?S3_BUCKET required}/$${S3_BACKUP_PREFIX:-backups}/" | tail -5'

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

# ==================== Test Matrix ====================

test-unit:
	cd backend && .venv/bin/python -m pytest tests/unit -m unit --timeout=10 -q

test-integration:
	cd backend && .venv/bin/python -m pytest tests/unit tests/integration -m "unit or integration" --timeout=30

test-security:
	cd backend && .venv/bin/python -m pytest tests/security -m security --timeout=60

test-full:
	cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing

test-perf:
	cd backend && .venv/bin/python -m pytest tests/performance -m performance --timeout=300 --benchmark-enable
