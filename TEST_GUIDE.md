# Test Execution Guide

Complete guide for running all tests across the École Platform stack.

## Test Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         TEST PYRAMID                             │
├─────────────────────────────────────────────────────────────────┤
│  Backend (pytest)          Web (Vitest)         Mobile (Flutter)│
│  ├── unit/                 ├── unit/            ├── unit/       │
│  ├── integration/          ├── contract/        ├── widget/     │
│  ├── security/             └── e2e/            └── e2e/        │
│  ├── edge/                                                      │
│  ├── performance/                                               │
│  └── contract/                                                  │
├─────────────────────────────────────────────────────────────────┤
│  API Scenarios (Postman)     Load Tests (k6)                    │
│  ├── smoke/                  ├── smoke/                         │
│  ├── baseline/               ├── baseline/                      │
│  └── scenario/               ├── stress/                        │
│                              └── soak/                          │
└─────────────────────────────────────────────────────────────────┘
```

**Rule**: Unit tests run fast and isolated. Integration tests need Docker services. E2E tests need the full stack running.

---

## Prerequisites

```bash
# Backend
cd backend && source .venv/bin/activate

# Web
cd web && npm install

# Mobile
cd mobile && flutter pub get

# Postman (Newman)
npm install -g newman

# k6
brew install k6   # macOS
```

---

## 1. Backend Tests (pytest)

Location: `backend/tests/`

### 1.1 Unit Tests — Fast, No Database

```bash
cd backend
pytest tests/unit/ -v --tb=short
```

**By domain:**
```bash
pytest tests/unit/core/           -v   # JWT, permissions, rate limit
pytest tests/unit/domain/         -v   # Money, Grade, RoleSet
pytest tests/unit/models/         -v   # repr, validators
pytest tests/unit/schemas/        -v   # Pydantic validation
pytest tests/unit/services/       -v   # Business logic
pytest tests/unit/repositories/   -v   # Repository smoke tests
pytest tests/unit/api/            -v   # Router-level unit tests
pytest tests/unit/workers/        -v   # ARQ task tests
```

**With coverage:**
```bash
pytest tests/unit/ --cov=app --cov-report=term-missing
```

### 1.2 Integration Tests — Real Database (testcontainers)

> ⚠️ Requires Docker: postgres, redis, minio

```bash
cd backend
pytest tests/integration/ -v --tb=short
```

**By API domain:**
```bash
pytest tests/integration/api/iam/           -v   # Auth, profiles, family
pytest tests/integration/api/lms/           -v   # Content, uploads, story
pytest tests/integration/api/communication/ -v   # Notifications, announcements
pytest tests/integration/api/billing/       -v   # Invoices, payments
pytest tests/integration/api/academic/      -v   # Programs, attendance
pytest tests/integration/api/content/       -v   # Games, rewards
pytest tests/integration/api/storage/       -v   # Signed uploads
pytest tests/integration/api/operations/    -v   # Calendar, documents, reports
```

**Repository integration:**
```bash
pytest tests/integration/repositories/ -v
```

### 1.3 Security Tests — RBAC/ABAC Matrix

```bash
cd backend
pytest tests/security/ -v --tb=short
```

### 1.4 Contract Tests — OpenAPI Compliance

```bash
cd backend
pytest tests/contract/ -v --tb=short
```

### 1.5 Edge & Performance Tests

```bash
cd backend
pytest tests/edge/         -v   # Boundary values, error paths
pytest tests/performance/  -v   # Benchmarks
```

### 1.6 Full Backend Suite with Coverage

```bash
cd backend
pytest tests/ --cov=app --cov-branch --cov-report=html --cov-report=term-missing
```

**Check threshold:**
```bash
pytest tests/ --cov=app --cov-branch --cov-fail-under=90
```

---

## 2. Web Tests

Location: `web/`

### 2.1 Unit + Contract Tests

```bash
cd web
npm run test
```

**With coverage:**
```bash
npm run test:coverage
```

### 2.2 E2E Tests (Playwright)

> ⚠️ Requires backend running on http://localhost:8000

```bash
cd web
npx playwright test
```

**Specific specs:**
```bash
npx playwright test e2e/parent-feed-notify.spec.ts
npx playwright test e2e/teacher-assignment.spec.ts
npx playwright test e2e/student-submission.spec.ts
npx playwright test e2e/admin-invitation.spec.ts
npx playwright test e2e/two-factor-auth.spec.ts
```

---

## 3. Mobile Tests

Location: `mobile/`

### 3.1 Unit Tests

```bash
cd mobile
flutter test test/unit/
```

### 3.2 Widget Tests

```bash
cd mobile
flutter test test/widget/
```

### 3.3 E2E / Integration Tests

```bash
cd mobile
flutter test test/widget/app_flows_widget_test.dart
flutter test test/widget/offline_sync_widget_test.dart
flutter test integration_test/
```

---

## 4. API Scenarios (Postman + Newman)

Location: `tests/postman/`

### 4.1 Full Smoke Collection

```bash
newman run tests/postman/ecole_platform_full.postman_collection.json \
  -e tests/postman/env_local.json
```

### 4.2 Domain Scenarios

```bash
# Academic lifecycle
newman run tests/postman/scenario_academic_year_lifecycle.postman_collection.json -e tests/postman/env_local.json

# Student journey
newman run tests/postman/scenario_student_lifecycle.postman_collection.json -e tests/postman/env_local.json

# Teacher workflow
newman run tests/postman/scenario_teacher_workflow.postman_collection.json -e tests/postman/env_local.json

# Parent journey
newman run tests/postman/scenario_parent_journey.postman_collection.json -e tests/postman/env_local.json

# Admin operations
newman run tests/postman/scenario_admin_operations.postman_collection.json -e tests/postman/env_local.json

# Billing cycle
newman run tests/postman/scenario_billing_cycle.postman_collection.json -e tests/postman/env_local.json

# Quiz assessment
newman run tests/postman/scenario_quiz_assessment_flow.postman_collection.json -e tests/postman/env_local.json

# Content management
newman run tests/postman/scenario_content_management.postman_collection.json -e tests/postman/env_local.json

# RBAC / ABAC / Security
newman run tests/postman/scenario_rbac_matrix.postman_collection.json -e tests/postman/env_local.json
newman run tests/postman/scenario_abac_policies.postman_collection.json -e tests/postman/env_local.json
newman run tests/postman/scenario_security_hardening.postman_collection.json -e tests/postman/env_local.json

# Upload / Download
newman run tests/postman/scenario_direct_upload_flow.postman_collection.json -e tests/postman/env_local.json

# Invoice PDF
newman run tests/postman/scenario_invoice_pdf_flow.postman_collection.json -e tests/postman/env_local.json

# Program enrollment
newman run tests/postman/scenario_program_enrollment_flow.postman_collection.json -e tests/postman/env_local.json
```

---

## 5. Load Tests (k6)

Location: `tests/load/`

### 5.1 Smoke — Verify API is Alive

```bash
k6 run tests/load/smoke/healthcheck.js
```

### 5.2 Baseline — Standard Load Patterns

```bash
k6 run tests/load/baseline/01_logins.js
k6 run tests/load/baseline/02_get_requests.js
k6 run tests/load/baseline/03_file_uploads.js
k6 run tests/load/baseline/04_websocket.js
```

### 5.3 Stress — Peak Load

```bash
k6 run tests/load/stress/peak_school_morning.js
k6 run tests/load/stress/upload_burst.js
```

### 5.4 Soak — Long-Running Stability

```bash
k6 run tests/load/soak/24h_steady_traffic.js
```

---

## 6. Quick Validation Scripts

### Run Everything (Local Dev)

```bash
# Terminal 1: Start infrastructure
cd infra && docker-compose -f docker-compose.dev.yml up -d

# Terminal 2: Backend tests
cd backend
pytest tests/unit/ -q
pytest tests/integration/api/iam/ -q
pytest tests/security/ -q
pytest tests/contract/ -q

# Terminal 3: Web tests
cd web
npm run test

# Terminal 4: Mobile tests
cd mobile
flutter test
```

### CI-Style Full Check

```bash
cd backend
pytest tests/ --cov=app --cov-branch --cov-fail-under=90
```

---

## Test Relationship Map

| What you change | Run these |
|-----------------|-----------|
| `app/core/*.py` | `tests/unit/core/`, `tests/security/`, `tests/edge/` |
| `app/schemas/*.py` | `tests/unit/schemas/` |
| `app/services/*.py` | `tests/unit/services/`, `tests/integration/api/<domain>/` |
| `app/repositories/*.py` | `tests/unit/repositories/`, `tests/integration/repositories/` |
| `app/api/v1/*.py` | `tests/integration/api/<domain>/`, `tests/contract/` |
| `app/models/*.py` | `tests/unit/models/`, `tests/integration/` |
| Frontend component | `web/tests/unit/...`, `web/e2e/...` |
| Mobile screen | `mobile/test/widget/...` |
| Infrastructure config | `tests/load/smoke/`, Postman smoke |

---

## Environment Variables for Testing

```bash
# Backend
export DATABASE_URL="postgresql+asyncpg://ecole:ecole@localhost:5432/ecole_platform"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="test-secret-key"
export APP_ENV="test"

# k6
export BASE_URL="http://localhost:8000"
export API_TOKEN="your-test-token"
```
