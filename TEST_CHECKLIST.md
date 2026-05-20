# Ecole Platform — Test Execution Checklist

## Legend
- ⬜ Not run
- 🔄 Running
- ✅ Passed
- ❌ Failed
- ⏭️ Skipped (tooling missing)

---

## 1. Backend Tests (pytest)

### 1.1 Unit Tests
- [x] `pytest tests/unit --tb=short -q`
  - Status: ✅ Passed
  - Time: ~60s
  - Failures: 0
  - Skipped: 1

### 1.2 Integration Tests
- [ ] `pytest tests/integration --tb=short -q`
  - Status: ❌ Multiple failures (require running dev DB + worker)
  - Time: Long
  - Key failures:
    - `asyncpg.exceptions.InvalidPasswordError` on upload tests (test DB credentials mismatch)
    - `httpx.ReadError` on WebSocket/shared-review tests
    - Invoice PDF / receipt API assertion failures (async worker not running)

### 1.3 Security Tests
- [ ] `pytest tests/security --tb=short -q`
  - Status: ⏭️ Slow (requires Docker testcontainers)
  - Key notes:
    - `fixture 'isolated_legacy_api_db'` — FIXED: direct import in `tests/security/conftest.py`
    - Tests timeout due to PostgresContainer startup; run with `-m 'not slow'` or ensure Docker is available

### 1.4 Contract Tests
- [x] `pytest tests/contract --tb=short -q`
  - Status: ✅ Passed

### 1.5 Edge Tests
- [x] `pytest tests/edge --tb=short -q`
  - Status: ✅ Passed
  - Fixes applied:
    - Fixed stale `SchoolServiceBase` import → `SchoolService`
    - Fixed missing `LMSServiceBase` import

### 1.6 Performance Tests
- [x] `pytest tests/performance --tb=short -q`
  - Status: ✅ Passed

### 1.7 Slow Tests
- [ ] `pytest -m slow --tb=short -q`
  - Status: ⬜ Not run

### 1.8 Full Suite
- [ ] `pytest --tb=short -q`
  - Status: ⬜ Not run

---

## 2. Mobile Tests (Flutter)

### 2.1 Static Analysis
- [x] `flutter analyze`
  - Status: ✅ Passed
  - Issues: 0

### 2.2 Unit + Widget Tests
- [x] `flutter test --coverage --reporter=expanded`
  - Status: ✅ Passed
  - Passed: 242
  - Failed: 0

### 2.3 Integration Tests
- [ ] `flutter test integration_test/`
  - Status: ❌ Failed (wireless iOS device issue)
  - Fix: Run with `--publish-port` flag or use simulator
  - Command:
  ```bash
  cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
  flutter test integration_test/ --publish-port
  # OR use a simulator
  flutter test integration_test/ -d <simulator-id>
  ```

### 2.4 Build Gate
- [x] `flutter build apk --debug`
  - Status: ✅ Passed
  - APK path: mobile/build/app/outputs/flutter-apk/app-debug.apk

---

## 3. Web Tests (Vitest + Playwright)

### 3.1 Static Analysis
- [x] `npm run lint`
  - Status: ✅ Passed

### 3.2 Type Check
- [x] `npm run typecheck`
  - Status: ✅ Passed

### 3.3 Unit Tests
- [x] `npm run test`
  - Status: ✅ Passing (37 test files, ~250+ tests)
  - Fixes applied:
    - Rewrote `tests/unit/services/directUpload.test.ts` — updated MSW handlers to match actual `/api/v1/content/upload-url` and `/api/v1/content/upload-confirm` endpoints; fixed XHR mock to support `addEventListener`
    - Fixed `tests/contract/api-contract.test.ts` — added `// @vitest-environment node` and updated file pattern from `.service.ts` → `.api.ts`
    - Fixed stale imports in test utilities (`@/services/auth/AuthContext` → `@/app/providers/AuthContext`, `@/services/api/client` → `@/core/api/client`)
    - Added `server.deps.inline: ['msw']` to vitest.config.ts
    - Replaced `node:stream/web` polyfill with `web-streams-polyfill` in tests/setup.ts

### 3.4 Coverage
- [ ] `npm run test:coverage`
  - Status: ⬜ Not run

### 3.5 Contract Tests
- [x] `npm run test:contract`
  - Status: ✅ Passed (62s — validates all frontend `.api.ts` files against backend OpenAPI spec)

### 3.6 E2E Tests
- [ ] `npm run test:e2e`
  - Status: ⬜ Not run / requires dev server

### 3.7 Build Gate
- [x] `npm run build`
  - Status: ✅ Passed

---

## 4. System Tests

### 4.1 Postman Collections
- [x] `system-tests/run_tests.sh --all --list`
  - Status: ✅ Passed

### 4.2 k6 Load Tests
- [ ] k6 syntax checks
  - Status: ⏭️ Skipped (k6 not installed)

### 4.3 Shell Scripts
- [x] `bash -n` on all scripts
  - Status: ✅ Passed

---

## 5. Infrastructure Tests

### 5.1 Helm
- [x] `helm lint infra/k8s`
  - Status: ✅ Passed

### 5.2 Docker Compose
- [x] All 7 compose files config valid
  - Status: ✅ Passed

### 5.3 Dockerfiles
- [ ] `docker build`
  - Status: ⬜ Not run

---

## 6. Workflow Validation

### 6.1 YAML Syntax
- [x] All 11 workflow files parse
  - Status: ✅ Passed

### 6.2 Actionlint
- [ ] `actionlint`
  - Status: ⏭️ Skipped (not installed)

---

## 7. Fixes Applied During Review

### Backend
1. **Installed missing packages:** `webauthn==2.6.0`, `authlib`, `twilio`
2. **Fixed `app/api/v1/auth/auth.py`** — `EmailVerificationService` was imported from `app.services.auth.email` but lives in `app.services.auth.auth`
3. **Fixed `app/services/auth/email.py`** — Jinja loader pointed to `app/services/templates` but templates are in `app/templates`
4. **Fixed `app/api/v1/auth/webauthn.py`** — `response_model=list_response(...)` → `ApiListResponse[...]`
5. **Fixed `app/api/v1/auth/sms_2fa.py`** — `response_model=success_response(dict)` → `ApiResponse[dict]`
6. **Fixed `app/api/v1/auth/oauth.py`** — same response_model fix
7. **Fixed `tests/edge/test_error_paths.py`** — stale `SchoolServiceBase` import, missing `LMSServiceBase` import
8. **Fixed `tests/unit/scripts/test_ci_coverage_policy.py`** — updated to match current CI workflow
9. **Fixed `tests/security/conftest.py`** — added `isolated_legacy_api_db` import for pytest 8+ compatibility
10. **Fixed `tests/conftest.py`** — moved `pytest_plugins` to root level

### Web
11. **Fixed `vitest.config.ts`** — added `server.deps.inline: ['msw']` for MSW bundling
12. **Fixed `tests/setup.ts`** — replaced `node:stream/web` with `web-streams-polyfill` for jsdom compatibility

---

## 8. Known Issues Remaining

### Backend Integration Tests — DB Credentials
Upload tests fail with `asyncpg.exceptions.InvalidPasswordError`. The test database credentials in `tests/integration/api/conftest.py` may need updating to match the disposable testcontainer credentials.

### Backend Integration Tests — Invoice PDF / Receipt
`test_admin_can_request_invoice_pdf_fr` and `test_admin_can_request_receipt_fr` fail with `AssertionError: assert 'failed' in ('pending', 'processing', 'ready')`. The async PDF generation may need a longer timeout or a running worker.

### Backend Integration Tests — WebSocket
`httpx.ReadError` on WebSocket tests. WebSocket endpoints may need a different test client setup.

### Mobile Integration Tests
Requires `--publish-port` flag for wireless iOS device, or use a simulator.

---

## 9. Commands to Run Next

```bash
# Backend integration (after starting dev DB)
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
source .venv/bin/activate
pytest tests/integration --tb=short -q

# Backend security
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/backend
source .venv/bin/activate
pytest tests/security --tb=short -q

# Mobile integration
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/mobile
flutter test integration_test/ --publish-port

# Web build verification
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev/web
npm run build

# Docker builds
cd /Users/nawfalrazouk/Ecole-Platform/ecole-platform-dev
docker build -f backend/Dockerfile --target test backend/
docker build -f web/Dockerfile web/
```

---

## 10. Final Scorecard

| Suite | Status | Count |
|---|---|---|
| ✅ Passed | Mobile analyze, Mobile unit, Mobile build, Web lint, Web typecheck, Web build, Backend unit, Backend edge, Backend performance, Backend contract, Helm, Compose, Workflows, Shell scripts | 14 |
| ⚠️ Partial | Backend integration (template + import fixes applied, DB/WS issues remain), Backend security (fixture fix applied, slow) | 2 |
| ⚠️ Partial | Backend integration (DB/WS/worker issues), Backend security (slow / Docker) | 2 |
| ❌ Blocked | Mobile integration (device config) | 1 |
| ⏭️ Skipped | k6, Newman, Actionlint, Docker builds, E2E | 6 |
