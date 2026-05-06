# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

École Platform is a K-12 EdTech SaaS for Moroccan schools. The monorepo has three independently deployable layers:

- `backend/` — FastAPI (Python 3.12, async SQLAlchemy 2.0, PostgreSQL 16, Redis 7, ARQ workers)
- `web/` — React 18 + TypeScript + Vite SPA (teacher/admin/director roles)
- `mobile/` — Flutter (student/parent roles)

The platform is multi-tenant per-school, bilingual (French/Arabic), and currency-aware (MAD).

---

## Commands

All daily commands run from the repo root via `make`. The dev stack is Docker Compose.

### Startup

```bash
make dev-init        # first-time setup: builds, migrates, seeds, starts all services
make up              # start dev stack (docker-compose.dev.yml)
make down            # stop dev stack
make seed-core       # seed database only (skips friend content assets)
```

### Backend

```bash
make test                         # all backend tests via Docker
make test-unit                    # fast unit tests only (no DB/Redis required)
make test-integration             # unit + integration tests
make test-cov                     # with HTML coverage report
make test-full                    # full suite + branch coverage report

# Run a single test file directly (requires venv active or Docker):
cd backend && .venv/bin/python -m pytest tests/unit/services/test_auth.py -v
cd backend && .venv/bin/python -m pytest tests/ -k "test_login" -v

make lint                         # ruff check
make lint-fix                     # ruff check --fix
make format                       # ruff format
```

### Migrations

```bash
make migrate                      # alembic upgrade head (in Docker)
make migrate-new msg="G51 description"   # autogenerate migration
make migrate-down                 # downgrade -1
make migrate-status               # current + history
```

Migration files live in `backend/alembic/versions/`. The naming convention is `{hash}_g{N}{letter}_{description}.py`. Migration groups (G) map to feature domains — don't mix concerns across groups.

### Web frontend

```bash
cd web && npm run dev             # dev server on :5173
cd web && npm test                # Vitest
cd web && npm run test:coverage   # with coverage
cd web && npm run lint            # ESLint
cd web && npm run build           # production build
```

### Flutter mobile

```bash
cd mobile && flutter pub get
cd mobile && flutter run           # requires connected device or emulator
cd mobile && flutter test          # all tests
cd mobile && flutter test test/widget/auth_screens_test.dart   # single file
cd mobile && flutter analyze
cd mobile && flutter build apk --release
```

### Kubernetes (local Kind cluster)

```bash
# Full setup from scratch:
kind create cluster --name ecole-dev
docker build -t ecole-platform-backend:local ./backend
docker build -t ecole-platform-web:local ./web
kind load docker-image ecole-platform-backend:local --name ecole-dev
kind load docker-image ecole-platform-web:local --name ecole-dev
helm install postgres bitnami/postgresql -n ecole-local --create-namespace \
  --set auth.username=ecole --set auth.password=ecole --set auth.database=ecole_platform
helm install redis bitnami/redis -n ecole-local --set auth.enabled=false --set replica.replicaCount=0
./infra/k8s/create-local-secrets.sh ecole-local
helm upgrade --install ecole-platform ./infra/k8s -n ecole-local -f ./infra/k8s/values-local.yaml \
  --set images.backend.repository=ecole-platform-backend --set images.backend.tag=local \
  --set images.web.repository=ecole-platform-web --set images.web.tag=local --wait

# Access:
kubectl port-forward -n ecole-local svc/ecole-platform-backend 8000:8000
kubectl port-forward -n ecole-local svc/ecole-platform-web 3000:80

# Teardown:
helm uninstall ecole-platform postgres redis -n ecole-local
kubectl delete namespace ecole-local
```

See `docs/KUBERNETES_SETUP.md` for the full guide including Docker Desktop alternative.

---

## Backend architecture

### Layer order (always top-to-bottom, no skipping)

```
API route (app/api/v1/*.py)
  → Service (app/services/*.py)      — business logic, orchestrates repos
  → Repository (app/repositories/*.py) — all DB queries, returns domain objects
  → Model (app/models/*.py)           — SQLAlchemy ORM, TimestampMixin (UUID PK + timestamps)
```

Services **never** import from `app/api/`. Repositories **never** import from `app/services/`. Direct DB access from routes is not allowed.

### Key cross-cutting modules

| Module | Purpose |
|---|---|
| `app/core/dependencies.py` | FastAPI `Depends()` — `AuthContext` (user_id, role, school_id, permissions) injected into every protected route |
| `app/core/permissions.py` | RBAC permission matrix for 5 roles: ADM, DIR, TCH, PAR, STD |
| `app/core/unit_of_work.py` | `UnitOfWork(db)` — wraps a single transaction; services `async with UnitOfWork(db) as uow` |
| `app/core/response.py` | Standardised JSON envelope: `{"data": ..., "meta": ...}` |
| `app/core/filtering.py` | Cursor-based pagination (all list endpoints use `cursor` + `limit`, not `offset`) |
| `app/core/storage.py` | `StorageBackend` protocol — `local` or `s3` chosen by `STORAGE_BACKEND` env var |
| `app/core/abac.py` | Attribute-based access control guards (school-scope enforcement) |

### Authentication pipeline

Every request passes: **JWT decode → AuthContext → RBAC check → ABAC school-scope guard**.  
Deny order: 401 (unauthenticated) → 404 (masked) → 403 (forbidden). Never return 403 before 404.

Access tokens: 30 min. Refresh tokens: 7 days. 2FA (TOTP) optional per user.

### Background workers

ARQ (async Redis Queue) workers live in `app/workers/`. Task definitions are in `app/core/tasks.py`. The worker process runs separately (`make worker`). Do not call heavy I/O directly from route handlers — enqueue via `await arq_pool.enqueue_job("task_name", ...)`.

### Model conventions

All models inherit `Base` and `TimestampMixin` (UUID PK, `created_at`, `updated_at`). School isolation: every tenant table has a `school_id` foreign key. Soft deletes are not used — records are deleted or archived via status enums.

---

## Web frontend architecture

Feature-based structure under `web/src/features/{feature-name}/`. Each feature contains its own pages, hooks, services, and types — no shared barrel imports between features.

- **API layer**: `web/src/services/` — typed `httpx`-style clients per domain
- **State**: React Query (server state) + React Context (auth/theme)
- **Role routing**: `web/src/features/auth/roleRedirects.ts` — login redirects by role; TCH/ADM/DIR only
- **Shared UI**: `web/src/shared/` — design system primitives (Button, Table, Modal, etc.)
- **i18n**: `react-i18next` with `fr`/`ar` namespaces; RTL layout toggled via `dir` attribute

Tests use Vitest + React Testing Library + MSW for API mocking. Factories in `web/tests/factories/`.

---

## Flutter mobile architecture

Feature-flat structure under `mobile/lib/features/{feature}/`. Each feature is self-contained (no Clean Architecture subdirs in practice — domain/data logic is colocated).

- **State**: Riverpod providers (all features use `StateNotifierProvider` or `AsyncNotifierProvider`)
- **HTTP**: Dio with interceptors for JWT refresh and Arabic locale header
- **Local storage**: `flutter_secure_storage` for tokens; SQLite (`sqflite`) for offline cache
- **Role routing**: STD and PAR roles only — teacher/admin routes redirect to web
- **Platform colours**: student screens `#7C3AED` (violet), parent screens `#2563EB` (blue)

Tests use `flutter_test` + `mocktail`. Widget tests in `mobile/test/widget/`; unit tests in `mobile/test/unit/`.

---

## Test infrastructure

### Backend test structure

```
backend/tests/
  conftest.py           # shared fixtures — real DB via testcontainers, real Redis
  unit/                 # fast, mocked — no DB/Redis; marker: @pytest.mark.unit
  integration/          # real DB + HTTP client against live stack; marker: @pytest.mark.integration
  security/             # RBAC matrix across all 5 roles; marker: @pytest.mark.security
  performance/          # k6-style benchmarks; marker: @pytest.mark.performance
  factories/            # SQLAlchemy model factories for test data
```

Integration tests hit a real database. Seed data must exist: run `make seed-core` before `make test-integration`. The `testcontainers` library spins up a fresh Postgres for unit tests automatically.

Coverage threshold is currently 80% (set in `pyproject.toml → [tool.coverage.report] fail_under`). Target is 90%.

### Seed credentials (dev/test)

| Role | Email | Password |
|---|---|---|
| Admin | admin@ecole-benani.ma | admin123 |
| Teacher | prof.math@ecole-benani.ma | teacher123 |
| Parent | parent.alaoui@gmail.com | parent123 |
| Student | yassine.alaoui@ecole-benani.ma | student123 |

School code: `EB-001` · School ID: `00000000-0000-4000-8000-000000000001`

---

## Infrastructure

- **Docker Compose files**: `infra/docker-compose.dev.yml` (default), `staging.yml`, `prod.yml`, `monitoring.yml`
- **Helm chart**: `infra/k8s/` — 15 templates; `values-local.yaml` for Kind, `values-staging.yaml`, `values-prod.yaml`
- **Secrets**: production secrets via `infra/secrets/*.txt` files (not committed); local dev uses `.env`
- **Object storage**: `STORAGE_BACKEND=local` (dev/local k8s) or `STORAGE_BACKEND=s3` (staging/prod). MinIO is the S3-compatible backend for self-hosted deployments.
- **CI**: `.github/workflows/` — `ci.yml` (lint + test + build), `deploy-k8s.yml` (Helm deploy), `security-trivy.yml` (image scan), `dependabot-automerge.yml`
