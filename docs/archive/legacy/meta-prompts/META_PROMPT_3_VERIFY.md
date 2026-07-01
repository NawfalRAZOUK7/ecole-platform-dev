# META-PROMPT 3: Full Verification

> Copy-paste this ENTIRE prompt into a NEW session (fresh context).
> Open folder: `ecole-platform-dev/`
> This prompt runs a complete verification pass across all layers.

---

```md
I've just completed a full-stack architecture refactoring of "École Platform" — an EdTech SaaS for K-12 schools in Morocco. This is a monorepo with FastAPI backend, React web, and Flutter mobile.

BEFORE ANYTHING, read these files to understand what was done:
1. Read ARCHITECTURE_STANDARD.md — the patterns everything must follow
2. Read REFACTOR_CHECKLIST.md — see what was completed

YOUR TASK: Run a comprehensive verification across all layers. For each check, report PASS or FAIL with details.

---

## BACKEND VERIFICATION (3-Tier Architecture)

### Check 1: No SQL in Routers
Search ALL files in backend/app/api/v1/ for these patterns:
- `from sqlalchemy import` → should be ZERO (except type annotations)
- `from sqlalchemy.orm import` → should be ZERO
- `db.execute(` → should be ZERO
- `select(` → should be ZERO
- `.add(` on db session → should be ZERO

For each violation found, list the file, line number, and the offending code.

### Check 2: No SQL in Services
Search ALL files in backend/app/services/ for:
- `from sqlalchemy import select` → should be ZERO
- `from sqlalchemy import update` → should be ZERO
- `from sqlalchemy import delete` → should be ZERO
- `self.db.execute(` → should be ZERO (except via repository)

Services SHOULD still have `from sqlalchemy.ext.asyncio import AsyncSession` (for commit/rollback).

### Check 3: Repository Completeness
- List ALL files in backend/app/repositories/
- Verify each one imports and extends BaseRepository
- Count total repository classes
- Verify each service file creates at least one repository in its `__init__`

### Check 4: RBAC Consistency
Search ALL files in backend/app/api/v1/ for:
- `if.*role.*==` or `if.*auth\.role` → should be ZERO (no hardcoded role checks for access control)
- `requires_role(` → should be ZERO (replaced by requires_permission)
- Count endpoints with `@requires_permission` → should cover all non-public endpoints

### Check 5: Shared Helpers
Search ALL files in backend/app/api/v1/ for:
- `def _get_client_ip` → should be ZERO (moved to core/request_utils.py)
- `def _request_locale` → should be ZERO
- `def _optional_current` → should be ZERO

### Check 6: OpenAPI Metadata
Count endpoints that have `summary=` in their decorator vs those that don't.
Report the percentage of documented endpoints.

---

## WEB VERIFICATION (React Query + Hooks)

### Check 7: No Direct API Calls in Pages
Search ALL `*Page.tsx` files in web/src/features/ for:
- `api.get(` → should be ZERO
- `api.post(` → should be ZERO
- `api.patch(` → should be ZERO
- `api.delete(` → should be ZERO
- `api.list(` → should be ZERO

These should ONLY appear in `*.service.ts` files.

### Check 8: Service + Hook Files Exist
For each feature directory in web/src/features/:
- Check if it has at least one `*.service.ts` file
- Check if it has at least one `use*.ts` hook file
- Report missing services/hooks

### Check 9: React Query Setup
- Read web/src/main.tsx → verify QueryClientProvider wraps the app
- Read web/src/shared/hooks/useQueryDefaults.ts → verify stale time constants exist

### Check 10: Build Passes
Run: `cd web && npm run build`
Report result.

---

## MOBILE VERIFICATION

### Check 11: Flutter Analyze
Run: `cd mobile && flutter analyze`
Report any issues.

### Check 12: No Deprecated Patterns
Search mobile/lib/ for:
- `DropdownButtonFormField` with `value:` on the next line (should be `initialValue:`)
- `resp['data']` or `resp['meta']` (should be resp.data, resp.nextCursor)

---

## INFRA VERIFICATION

### Check 13: Secrets Security
- Verify `.env` is in `.gitignore`
- Verify `.env.example` has NO real secrets (no real JWT keys, passwords)
- Verify `infra/redis/redis.conf` has `requirepass` and `protected-mode yes`
- Verify `infra/postgres/init.sql` has no hardcoded passwords
- Verify `infra/docker-compose.monitoring.yml` doesn't have `ecole-grafana` as password

---

## MISSING FEATURE VERIFICATION

### Check 14: Phase 14 Gaps Fixed
- Verify PDF templates exist in backend/app/templates/reports/ or similar
- Verify Arabic RTL support in templates
- Verify weekly aggregation in analytics endpoints

### Check 15: Phase 16 Gaps Fixed
- Read web/src/features/documents/ResourcesPage.tsx → verify it's a real implementation (>100 lines)
- Search for document expiry notification logic in backend
- Search for bulk document ZIP download endpoint

---

## SUMMARY REPORT

After all checks, produce a summary table:

| Check | Area | Status | Issues |
|-------|------|--------|--------|
| 1 | Backend Routers | PASS/FAIL | ... |
| 2 | Backend Services | PASS/FAIL | ... |
| ... | ... | ... | ... |
| 15 | Phase 16 Gaps | PASS/FAIL | ... |

If ANY check fails, list the specific files and lines that need fixing.
If all checks pass, confirm the refactoring is complete.

Update REFACTOR_CHECKLIST.md with the final validation results.

CRITICAL: Do NOT run any git command. No git add, commit, push, or any other git operation. I handle all git myself.
```
