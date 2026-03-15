.PHONY: up down restart logs migrate seed test lint shell build clean status health

COMPOSE_FILE = infra/docker-compose.dev.yml
DC = docker compose -f $(COMPOSE_FILE)

# ==================== Lifecycle ====================

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

# ==================== Backend ====================

migrate:
	$(DC) exec backend alembic upgrade head

migrate-new:
	$(DC) exec backend alembic revision --autogenerate -m "$(msg)"

migrate-down:
	$(DC) exec backend alembic downgrade -1

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

shell:
	$(DC) exec backend bash

# ==================== Web Frontend ====================

web-install:
	$(DC) exec web npm install

web-lint:
	$(DC) exec web npm run lint

# ==================== Status ====================

status:
	$(DC) ps

health:
	@curl -sf http://localhost:8000/api/v1/health | python3 -m json.tool || echo '❌ Backend health check failed'
