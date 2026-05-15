# 🛠 Installation Guide

Complete setup guide for École Platform across all environments.

---

## Prerequisites

| Tool               | Version | Required for             |
| ------------------ | ------- | ------------------------ |
| **Docker**         | 24+     | All services             |
| **Docker Compose** | v2+     | Container orchestration  |
| **Node.js**        | 18+     | Web frontend             |
| **npm**            | 9+      | Web dependencies         |
| **Flutter**        | 3.x     | Mobile app               |
| **Dart**           | 3.x     | Mobile app               |
| **Python**         | 3.12+   | Backend (local dev only) |
| **Make**           | Any     | Command shortcuts        |

---

## Quick Setup (Docker — Recommended)

The fastest way to get the full platform running:

```bash
# 1. Clone the repository
git clone <repo-url>
cd ecole-platform-dev

# 2. Create environment file
cp .env.example .env

# 3. Start all services (API + PostgreSQL + Redis + Nginx)
make up

# 4. Apply database migrations
make migrate

# 5. Load test data
make seed

# 6. Verify everything is running
make health
# Expected: {"status": "healthy", "version": "0.1.0"}
```

The backend API is now available at `http://localhost:8000`.

---

## Web Frontend

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

The web app is available at `http://localhost:5173`.

### Build for production

```bash
npm run build    # Output in dist/
npm run preview  # Preview production build
```

---

## Mobile App

```bash
cd mobile

# Install dependencies
flutter pub get

# Run on connected device or emulator
flutter run

# Run on specific platform
flutter run -d chrome     # Web
flutter run -d android    # Android emulator
flutter run -d ios        # iOS simulator
```

### Build for release

```bash
flutter build apk         # Android APK
flutter build appbundle    # Android App Bundle
flutter build ios          # iOS (requires Xcode)
```

---

## Backend (Local Development — Without Docker)

If you prefer running the backend directly:

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-test.txt

# Run migrations
alembic upgrade head

# Seed demo data
python -m app.scripts.seed_demo

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: You still need PostgreSQL and Redis running. You can start just those:

```bash
docker compose -f infra/docker-compose.dev.yml up -d postgres redis
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required

| Variable         | Default                                                              | Description                                     |
| ---------------- | -------------------------------------------------------------------- | ----------------------------------------------- |
| `DATABASE_URL`   | `postgresql+asyncpg://ecole:change-me@localhost:5432/ecole_platform` | PostgreSQL connection string                    |
| `REDIS_URL`      | `redis://:change-me-dev-redis@localhost:6379/0`                      | Redis connection string                         |
| `JWT_SECRET_KEY` | `change-me-in-production`                                            | JWT signing key (**must change in production**) |

### Optional

| Variable                      | Default       | Description                                      |
| ----------------------------- | ------------- | ------------------------------------------------ |
| `APP_ENV`                     | `development` | Environment (development / staging / production) |
| `APP_PORT`                    | `8000`        | API server port                                  |
| `LOG_LEVEL`                   | `DEBUG`       | Logging level                                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`          | JWT access token lifetime                        |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `2`           | JWT refresh token lifetime                       |
| `MAX_SESSIONS_PER_USER`       | `5`           | Max concurrent sessions                          |
| `DATABASE_REPLICA_URL`        | —             | Read replica connection (optional)               |

### Object storage (MinIO / S3)

| Variable                     | Default                 | Description                                                                                                                                           |
| ---------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `STORAGE_BACKEND`            | `local`                 | `local` keeps files on disk; `s3` routes through MinIO. **Do not change to `s3` until the migration script has passed.** See `docs/MINIO_ROLLOUT.md`. |
| `DOCUMENT_STORAGE_BACKEND`   | `local`                 | Same switch for the student-documents service. Must be changed together with `STORAGE_BACKEND`.                                                       |
| `S3_ENDPOINT`                | `http://localhost:9000` | MinIO API address (internal: `http://minio:9000` in Docker)                                                                                           |
| `S3_BUCKET`                  | `ecole-dev-private`     | Bucket name — one per env (`ecole-{dev,staging,prod}-private`)                                                                                        |
| `S3_ACCESS_KEY`              | `minioadmin`            | Access key (dev only — use secrets manager in staging/prod)                                                                                           |
| `S3_SECRET_KEY`              | `minioadmin123`         | Secret key (dev only — **change in all non-dev environments**)                                                                                        |
| `S3_FORCE_PATH_STYLE`        | `true`                  | Required for MinIO; set `false` for AWS S3                                                                                                            |
| `S3_PRESIGN_GET_TTL_SECONDS` | `600`                   | Presigned download URL lifetime (10 min)                                                                                                              |

---

## Test Accounts

After running `make seed`, these accounts are available:

| Role     | Email                 | Password       | Description              |
| -------- | --------------------- | -------------- | ------------------------ |
| Admin    | `admin@ecole.test`    | `Admin123!`    | Full platform access     |
| Director | `director@ecole.test` | `Director123!` | Analytics and reports    |
| Teacher  | `teacher@ecole.test`  | `Teacher123!`  | Classes, grades, content |
| Parent   | `parent@ecole.test`   | `Parent123!`   | Child tracking, payments |
| Student  | `student@ecole.test`  | `Student123!`  | Learning, games, rewards |

---

## Monitoring Stack (Optional)

```bash
# Start Prometheus + Grafana + Loki + Tempo
make monitoring-up

# Access dashboards
open http://localhost:3000    # Grafana (admin/admin)
open http://localhost:9090    # Prometheus
open http://localhost:9093    # Alertmanager
```

---

## Running Tests

```bash
# Backend tests
make test                    # All tests
make test-cov                # With coverage report
pytest -m "security" tests/  # Security tests only
pytest -m "not slow" tests/  # Fast tests only

# Web tests
cd web
npm test                     # All tests
npm run test:watch           # Watch mode
npm run test:coverage        # With coverage

# Mobile tests
cd mobile
flutter test                 # All widget & unit tests
```

---

## Useful Make Commands

| Command              | Description                 |
| -------------------- | --------------------------- |
| `make up`            | Start dev environment       |
| `make down`          | Stop environment            |
| `make restart`       | Restart all services        |
| `make logs`          | Follow logs                 |
| `make migrate`       | Run DB migrations           |
| `make seed`          | Load test data              |
| `make test`          | Run backend tests           |
| `make lint`          | Check code style            |
| `make clean`         | Remove containers + volumes |
| `make health`        | Check API health            |
| `make shell`         | Open backend shell          |
| `make shell-db`      | Open PostgreSQL shell       |
| `make redis-cli`     | Open Redis CLI              |
| `make monitoring-up` | Start monitoring stack      |

---

## Troubleshooting

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000
# Kill it or change APP_PORT in .env
```

### Database connection refused

```bash
# Ensure PostgreSQL is running
docker compose -f infra/docker-compose.dev.yml ps postgres
# Check logs
docker compose -f infra/docker-compose.dev.yml logs postgres
```

### Migration errors

```bash
# Check current migration state
alembic current
# Reset and reapply
alembic downgrade base
alembic upgrade head
```

### npm install fails (web)

```bash
# Clear cache and retry
rm -rf node_modules package-lock.json
npm install
```

### Flutter pub get fails

```bash
# Clean and retry
flutter clean
flutter pub get
```
