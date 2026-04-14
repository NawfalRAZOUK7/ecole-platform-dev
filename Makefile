.PHONY: up down restart logs migrate seed seed-friend-content test lint shell build clean status health \
       staging-up staging-down prod-up prod-down monitoring-up monitoring-down \
       shell-db redis-cli backup restore backup-status docker-prune version \
       migrate-new migrate-down migrate-status test-cov lint-fix format web-install web-lint \
       openapi openapi-check worker worker-logs test-unit test-integration test-security \
       test-full test-perf rotate-jwt rotate-db rotate-redis rotate-all \
       deploy-blue-green deploy-rollback deploy-status dev-init dev-reset seed-demo \
       docs docs-schema

# ==================== Compose Files ====================
COMPOSE_FILE = infra/docker-compose.dev.yml
COMPOSE_STAGING = infra/docker-compose.staging.yml
COMPOSE_PROD = infra/docker-compose.prod.yml
COMPOSE_MONITORING = infra/docker-compose.monitoring.yml
COMPOSE_ENV_FILE = .env

DC = docker compose --env-file $(COMPOSE_ENV_FILE) -f $(COMPOSE_FILE)
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

seed-friend-content:
	$(DC) exec backend mkdir -p /ecole-platform-reference/extraction/assets
	docker cp ../ecole-platform-reference/extraction/assets/. ecole-backend:/ecole-platform-reference/extraction/assets
	$(DC) exec backend python -m scripts.seed_friend_content

seed-demo:
	$(DC) run --rm backend python -m app.scripts.seed_demo

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

docs:
	cd backend && .venv/bin/python scripts/export_openapi.py --redoc

docs-schema:
	cd backend && .venv/bin/pip install eralchemy2 && .venv/bin/python -c "from eralchemy2 import render_er; from app.core.database import Base; import app.models.audit, app.models.billing, app.models.calendar, app.models.com, app.models.documents, app.models.erp, app.models.iam, app.models.lms, app.models.reporting, app.models.school; render_er(Base.metadata, 'docs/schema.png')"

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

# ==================== Secret Rotation ====================

rotate-jwt:
	@echo "Rotating JWT secret..."
	bash infra/scripts/rotate-secrets.sh jwt

rotate-db:
	@echo "Rotating database password..."
	bash infra/scripts/rotate-secrets.sh db

rotate-redis:
	@echo "Rotating Redis password..."
	bash infra/scripts/rotate-secrets.sh redis

rotate-all:
	@echo "Rotating all application secrets..."
	bash infra/scripts/rotate-secrets.sh all

# ==================== Blue-Green Deployment ====================

deploy-blue-green:
	@test -n "$${IMAGE_TAG}" || (echo "Usage: make deploy-blue-green IMAGE_TAG=<sha-or-tag>" && exit 1)
	bash infra/scripts/blue-green-deploy.sh "$${IMAGE_TAG}"

deploy-rollback:
	@echo "Rolling back via blue-green deploy using IMAGE_TAG=$${IMAGE_TAG:-previous}"
	bash infra/scripts/blue-green-deploy.sh "$${IMAGE_TAG:-previous}"

deploy-status:
	@echo "Active environment:"
	@cat infra/active-env 2>/dev/null || echo "blue"
	@echo "---"
	@echo "Current upstream:"
	@cat infra/nginx/upstream.conf

# ==================== Developer Onboarding ====================

dev-init:
	@echo "=== Ecole Platform — Dev Setup ==="
	@test -f .env || (cp .env.example .env && echo "  .env created")
	@$(DC) build
	@$(DC) up -d postgres redis
	@echo "  Waiting for PostgreSQL..."
	@sleep 5
	@$(DC) run --rm backend alembic upgrade head
	@$(DC) run --rm backend python -m app.scripts.seed_demo
	@$(DC) up -d
	@echo ""
	@echo "  API:  http://localhost:8000/docs"
	@echo "  Web:  http://localhost:5173"
	@echo "  Demo school: Lycée Mohammed V (code: LMV-001)"
	@echo "  Admin login: admin@ecole-demo.ma / Demo1234!"
	@echo "=== Setup complete ==="

dev-reset:
	@$(DC) down -v --remove-orphans
	@rm -f .env
	@echo "Environment cleared. Run 'make dev-init' to start fresh."

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
