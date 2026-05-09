.PHONY: api-test-down api-test-status api-test-up audit-export backup backup-status build build-prod clean deploy-blue-green deploy-rollback deploy-status dev-init dev-reset docker-prune docs docs-schema down format health hooks-install lint lint-fix logs migrate migrate-down migrate-new migrate-status migrate-validate monitoring-down monitoring-up openapi openapi-check prod-down prod-logs prod-up redis-cli redis-cli-staging restart restore restore-drill rotate-all rotate-db rotate-jwt rotate-redis seed seed-core seed-friend-content shell shell-db shell-db-staging staging-down staging-logs staging-up status test test-cov test-full test-integration test-load test-perf test-postman test-postman-full test-postman-phases test-postman-scenarios test-security test-unit up version web-install web-lint worker worker-logs mobile-run mobile-build mobile-test web-build web-test web-test-e2e web-format pre-rollout

# ==================== Compose Files ====================
COMPOSE_FILE = infra/docker-compose.dev.yml
COMPOSE_STAGING = infra/docker-compose.staging.yml
COMPOSE_PROD = infra/docker-compose.prod.yml
COMPOSE_MONITORING = infra/docker-compose.monitoring.yml
COMPOSE_API_TEST = infra/docker-compose.api-test.yml
COMPOSE_ENV_FILE = .env

DC = docker compose --env-file $(COMPOSE_ENV_FILE) -f $(COMPOSE_FILE)
DC_API_TEST = docker compose --env-file $(COMPOSE_ENV_FILE) -p ecole-api-test -f $(COMPOSE_API_TEST)
DC_STAGING = docker compose -f $(COMPOSE_STAGING)
DC_PROD = docker compose -f $(COMPOSE_PROD)
DC_MONITORING = docker compose -f $(COMPOSE_MONITORING)

# App version (read from backend pyproject.toml, fallback to 1.0.0)
APP_VERSION := $(shell grep -m1 '^version = ' backend/pyproject.toml 2>/dev/null | cut -d'"' -f2 || echo "1.0.0")

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
	@echo "Starting staging environment..."
	@test -f infra/secrets/jwt_secret_key.txt || (echo "Missing infra/secrets/jwt_secret_key.txt" && exit 1)
	@test -f infra/secrets/db_password.txt || (echo "Missing infra/secrets/db_password.txt" && exit 1)
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
	@echo "══════════════════════════════════════════════════════"
	@echo "  Step 1/2 — Core seed (all tables)"
	@echo "══════════════════════════════════════════════════════"
	$(DC) exec backend python -m app.seed
	@echo ""
	@echo "══════════════════════════════════════════════════════"
	@echo "  Step 2/2 — Friend educational content (stories, PDFs, coloring)"
	@echo "══════════════════════════════════════════════════════"
	@if [ -d "../ecole-platform-reference/extraction/assets" ]; then \
		$(DC) exec backend mkdir -p /ecole-platform-reference/extraction/assets; \
		docker cp ../ecole-platform-reference/extraction/assets/. ecole-backend:/ecole-platform-reference/extraction/assets; \
		$(DC) exec backend python -m scripts.seed_friend_content; \
	else \
		echo "  Skipping friend content — ../ecole-platform-reference not found"; \
		echo "  Run 'make seed-friend-content' manually if you have the assets."; \
	fi
	@docker cp ecole-backend:/app/seed-report.md ./seed-report.md 2>/dev/null || true
	@docker cp ecole-backend:/app/seed-friend-report.md ./seed-friend-report.md 2>/dev/null || true
	@echo ""
	@echo "══════════════════════════════════════════════════════"
	@echo "  Seed complete!"
	@echo "  Reports: ./seed-report.md + ./seed-friend-report.md"
	@echo "══════════════════════════════════════════════════════"

seed-core:
	$(DC) exec backend python -m app.seed
	@docker cp ecole-backend:/app/seed-report.md ./seed-report.md 2>/dev/null || true
	@echo "  Report: ./seed-report.md"

seed-friend-content:
	@if [ -d "../ecole-platform-reference/extraction/assets" ]; then \
		$(DC) exec backend mkdir -p /ecole-platform-reference/extraction/assets; \
		docker cp ../ecole-platform-reference/extraction/assets/. ecole-backend:/ecole-platform-reference/extraction/assets; \
		$(DC) exec backend python -m scripts.seed_friend_content; \
		@docker cp ecole-backend:/app/seed-friend-report.md ./seed-friend-report.md 2>/dev/null || true; \
		@echo "  Report: ./seed-friend-report.md"; \
	else \
		echo "ERROR: ../ecole-platform-reference/extraction/assets not found"; \
		echo "Place friend content assets there or skip with 'make seed-core'"; \
		exit 1; \
	fi

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
	$(DC) exec redis redis-cli -a "$${REDIS_PASSWORD:-change-me-dev-redis}"

redis-cli-staging:
	$(DC_STAGING) exec redis redis-cli -a "$${REDIS_PASSWORD}"

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

# ==================== Pre-Deployment Checks ====================

pre-rollout:
	$(DC) exec backend python scripts/pre_rollout_check.py

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
	@$(DC) run --rm backend python -m app.seed
	@$(DC) up -d
	@echo ""
	@echo "  API:  http://localhost:8000/docs"
	@echo "  Web:  http://localhost:5173"
	@echo "  School: Ecole Benani (code: EB-001)"
	@echo "  Admin login: admin@ecole-benani.ma / admin123"
	@echo "  See: ai-workflow/SEED-REFERENCE.md for all credentials"
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

web-build:
	cd web && npm run build

web-test:
	cd web && npm run test

web-test-e2e:
	cd web && npm run test:e2e

web-format:
	cd web && npm run format

# ==================== Mobile ====================

mobile-run:
	cd mobile && flutter run

mobile-build:
	cd mobile && flutter build apk

mobile-test:
	cd mobile && flutter test

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
	cd backend && .venv/bin/python -m pytest tests/unit --timeout=10 -q

test-integration:
	cd backend && .venv/bin/python -m pytest tests/integration --timeout=30

test-security:
	cd backend && .venv/bin/python -m pytest tests/security --timeout=60

test-full:
	cd backend && .venv/bin/python -m pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing

test-perf:
	cd backend && .venv/bin/python -m pytest tests/performance --timeout=300 --benchmark-enable

# ==================== Disposable API Test Stack ====================

api-test-up:
	$(DC_API_TEST) up -d --build postgres redis backend
	$(DC_API_TEST) exec backend alembic upgrade head
	$(DC_API_TEST) exec backend python -m app.seed
	@echo "Disposable API test backend: http://localhost:8010/api/v1"

api-test-down:
	$(DC_API_TEST) down -v --remove-orphans

api-test-status:
	$(DC_API_TEST) ps

test-postman:
	POSTMAN_BASE_URL=$${POSTMAN_BASE_URL:-http://localhost:8010/api/v1} bash tests/run_tests.sh --all

test-postman-phases:
	POSTMAN_BASE_URL=$${POSTMAN_BASE_URL:-http://localhost:8010/api/v1} bash tests/run_tests.sh --all-phases

test-postman-scenarios:
	POSTMAN_BASE_URL=$${POSTMAN_BASE_URL:-http://localhost:8010/api/v1} bash tests/run_tests.sh --include-scenarios

test-postman-full:
	POSTMAN_BASE_URL=$${POSTMAN_BASE_URL:-http://localhost:8010/api/v1} bash tests/run_tests.sh --full-collection

test-load:
	cd tests/load && BASE_URL=$${BASE_URL:-http://localhost:8010/api/v1} k6 run $${SCENARIO:-baseline/01_logins.js}
