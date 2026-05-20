# Validation Suite Review & Enhancement Report

Deep analysis of all tests, Actions Workflows, and tools created for the École Platform validation suite.

---

## Critical Issues Found

### 1. Postman Collection - 2FA Flow (scenario_2fa.postman_collection.json)

**Status:** ❌ CRITICAL - Multiple incorrect API endpoints and request formats

| Issue | Line | Problem | Fix Required |
|-------|------|---------|-------------|
| Login field name | 56 | Uses `"username"` but backend expects `"email"` | Change to `"email"` and add `school_id` |
| TOTP verify endpoint | 153 | Uses `/auth/2fa/verify` but should be `/auth/2fa/verify-setup` | Change endpoint path |
| Login with TOTP flow | 219 | Passes `totp_code` in login body - incorrect flow | Use temp_token flow: login → get temp_token → call /auth/2fa/verify |
| Disable TOTP method | 259 | Uses DELETE but endpoint is POST | Change to POST with body `{ "code": "..." }` |

**Correct 2FA Flow (based on backend/auth.py):**
1. POST /auth/login with `{ email, password, school_id }` → returns `{ access_token }` or `{ requires_2fa: true, temp_token }`
2. POST /auth/2fa/setup (protected) → returns `{ totp_secret, qr_code_url }`
3. POST /auth/2fa/verify-setup (protected) with `{ code }` → activates 2FA, returns backup codes
4. POST /auth/login with `{ email, password, school_id }` → returns `{ requires_2fa: true, temp_token }`
5. POST /auth/2fa/verify (public) with `{ temp_token, code }` → returns `{ access_token }`
6. POST /auth/2fa/disable (protected) with `{ code }` → disables 2FA

### 2. Postman Collection - Email Recovery (scenario_email_recovery.postman_collection.json)

**Status:** ❌ CRITICAL - Incorrect API endpoints and missing steps

| Issue | Line | Problem | Fix Required |
|-------|------|---------|-------------|
| Request endpoint | 59 | Uses `/auth/password/reset/request` but should be `/recovery/request` | Change to `/recovery/request` |
| Missing verify step | N/A | Missing `/recovery/verify` OTP verification step | Add request to `/recovery/verify` with `{ request_id, otp }` |
| Reset endpoint | 195 | Uses `/auth/password/reset/confirm` but should be `/recovery/reset` | Change to `/recovery/reset` |
| Login field name | 242 | Uses `"username"` but should use `"email"` | Change to `"email"` |
| Missing school_id | 59, 195 | Recovery requires `school_id` in request body | Add `school_id` field |

**Correct Recovery Flow (based on backend/recovery.py):**
1. POST /recovery/request with `{ email, school_id }` → returns `{ request_id }`
2. POST /recovery/verify with `{ request_id, otp }` → verifies OTP
3. POST /recovery/reset with `{ request_id, new_password }` → resets password

### 3. Postman Collection - Chaos Scenarios (scenario_chaos.postman_collection.json)

**Status:** ⚠️ MEDIUM - Syntax errors and async issues

| Issue | Line | Problem | Fix Required |
|-------|------|---------|-------------|
| Syntax error | 200 | Missing comma in header object after "Authorization" line | Add comma |
| Webhook dedup test | 106, 134 | Uses `{{$randomInt}}` for both requests - different IDs, won't test dedup | Use same provider_event_id for both requests |
| Rate limit async issue | 192-209 | pm.sendRequest is async, test phase runs before requests complete | Use sequential requests or add delay |
| Load test blocking issue | 327-332 | pm.wait() doesn't actually block in Postman/Newman | Use setTimeout with callback or skip this test in Postman |

---

## GitHub Actions Workflow Integration

**Status:** ⚠️ MEDIUM - New scenario collections not integrated

### Current State
- `postman-tests` job runs only `ecole_platform_full.postman_collection.json`
- New scenario collections (chaos, 2FA, email recovery, Sentry/TestMail) are not in CI

### Recommended Enhancement
Add a new job to run scenario collections:

```yaml
postman-scenario-tests:
  name: Postman Scenario Tests (Newman)
  runs-on: ubuntu-latest
  needs: [integration-tests]
  services:
    # Same as postman-tests job
  steps:
    # Same setup as postman-tests job
    - name: Run chaos scenarios
      run: |
        newman run system-tests/postman/scenario_chaos.postman_collection.json \
          -e system-tests/postman/env_local.json \
          --env-var "base_url=http://localhost:8000/api/v1" \
          --bail
    - name: Run 2FA flow
      run: |
        newman run system-tests/postman/scenario_2fa.postman_collection.json \
          -e system-tests/postman/env_local.json \
          --env-var "base_url=http://localhost:8000/api/v1" \
          --bail
    # Add other scenario collections
```

---

## Existing Test Infrastructure Review

### run_tests.sh Script
**Status:** ✅ GOOD

- Has `--include-scenarios` flag that picks up `scenario_*.postman_collection.json`
- Safety checks for localhost:8000 (dev DB)
- Supports custom environment files
- Well-structured with proper error handling

### Curl Chaos Scripts
**Status:** ✅ GOOD

- All scripts have proper argument parsing
- Error handling with set -euo pipefail
- Clear output with pass/fail indicators
- 02_webhook_duplicate.sh correctly uses same provider_event_id (unlike Postman version)

### Requestly Rules
**Status:** ✅ GOOD

- 4 rules covering main chaos scenarios
- Proper condition matching
- Clear descriptions
- Disabled by default (safe)

---

## Missing Test Scenarios

### Auth Endpoints Not Covered

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| POST /auth/register | Invitation-based registration | HIGH |
| POST /auth/verify-email | Email verification OTP | HIGH |
| POST /auth/change-password | Password change (requires current password) | MEDIUM |
| GET /auth/sessions | List active sessions | MEDIUM |
| DELETE /auth/sessions/{id} | Revoke specific session | MEDIUM |
| GET /auth/login-history | Paginated login history | LOW |

### Additional Chaos Scenarios

| Scenario | Purpose | Priority |
|----------|---------|----------|
| Database connection failure | Test DB outage resilience | HIGH |
| Redis connection failure | Test cache/session outage | HIGH |
| Slow database queries | Test query timeout handling | MEDIUM |
| Malformed request bodies | Test validation error handling | LOW |
| Missing required headers | Test auth header validation | LOW |

---

## Enhancements Recommended

### High Priority

1. **Fix Postman 2FA collection**
   - Correct all endpoint paths and request formats
   - Implement proper temp_token flow for 2FA login
   - Add school_id to login requests

2. **Fix Postman email recovery collection**
   - Correct endpoint paths to use /recovery/*
   - Add missing OTP verification step
   - Add school_id to requests

3. **Fix Postman chaos collection**
   - Fix syntax error (missing comma)
   - Fix webhook dedup test to use same provider_event_id
   - Document async limitations of rate limit/load tests

4. **Add scenario collections to CI**
   - Create new GitHub Actions job for scenario tests
   - Run after integration-tests job
   - Fail fast on scenario test failures

### Medium Priority

5. **Add missing auth endpoint tests**
   - Registration flow with invitation code
   - Email verification flow
   - Password change flow
   - Session management (list/revoke)

6. **Add environment file for scenario tests**
   - Create `system-tests/postman/env_scenarios.json` with required variables
   - Include test credentials, school_id, TestMail API keys

7. **Add Postman collection for invitation flow**
   - Test invitation code generation
   - Test invitation code consumption
   - Test invitation revocation

8. **Add Postman collection for session management**
   - Test session listing
   - Test session revocation
   - Test login history pagination

### Low Priority

9. **Add k6 load tests for auth endpoints**
   - Baseline login load test
   - Baseline 2FA load test
   - Baseline recovery flow load test

10. **Add Postman data-driven tests**
    - Test with multiple user roles (STD, TCH, PAR, ADM)
    - Test with multiple school contexts
    - Test edge cases (expired tokens, invalid OTPs, etc.)

11. **Add test data fixtures**
    - Create test user fixtures for Postman
    - Create test invitation codes
    - Create test school contexts

---

## Security Considerations

### Secrets Management

**Status:** ⚠️ MEDIUM - TestMail API keys in environment files

- TestMail API keys should not be committed to repo
- Use Doppler or environment variables for secrets
- Document which secrets are required for each test

### Rate Limiting in Tests

**Status:** ⚠️ MEDIUM - Rate limit test could trigger production-like limits

- Rate limit test fires 100 rapid requests
- Could trigger backend rate limiting in CI
- Consider reducing request count or adding delay

### Test Data Cleanup

**Status:** ❌ MISSING - No cleanup after tests

- Tests create users, sessions, recovery requests
- No cleanup mechanism to reset test state
- Could cause test pollution in CI

---

## Performance Considerations

### Postman Async Limitations

**Status:** ⚠️ MEDIUM - Rate limit and load tests won't work correctly in Postman

- Postman's pm.sendRequest is async
- Test phase runs before all requests complete
- Use curl scripts or k6 for actual load testing

### CI Job Duration

**Status:** ✅ GOOD

- Current CI jobs are reasonably fast
- Adding scenario tests will add ~5-10 minutes
- Consider running scenario tests in parallel

---

## Documentation Gaps

### Missing Documentation

1. **Scenario test setup instructions**
   - How to configure TestMail API keys
   - How to set up test users
   - How to generate invitation codes

2. **Chaos testing guide**
   - When to use Requestly vs curl vs Postman
   - How to interpret chaos test results
   - How to tune chaos parameters

3. **CI integration guide**
   - How scenario tests run in CI
   - How to debug CI failures
   - How to skip specific tests if needed

---

## Summary

### Overall Assessment

| Component | Status | Issues | Enhancements |
|-----------|--------|--------|--------------|
| Postman Collections | ⚠️ MEDIUM | 10 critical/medium issues | 8 high/medium enhancements |
| Curl Scripts | ✅ GOOD | 0 issues | 2 low enhancements |
| Requestly Rules | ✅ GOOD | 0 issues | 1 low enhancement |
| GitHub Actions | ⚠️ MEDIUM | 1 missing integration | 1 high enhancement |
| run_tests.sh | ✅ GOOD | 0 issues | 0 enhancements |

### Action Items

**Immediate (Before Commit):**
1. Fix scenario_2fa.postman_collection.json - correct all API endpoints
2. Fix scenario_email_recovery.postman_collection.json - correct all API endpoints
3. Fix scenario_chaos.postman_collection.json - syntax error and webhook dedup

**Short Term (This Week):**
4. Add scenario collections to GitHub Actions CI
5. Create env_scenarios.json for test environment variables
6. Add missing auth endpoint tests (register, verify-email, change-password, sessions)

**Medium Term (Next Sprint):**
7. Add Postman collection for invitation flow
8. Add Postman collection for session management
9. Add test data cleanup mechanism
10. Document scenario test setup

**Long Term (Future):**
11. Add k6 load tests for auth endpoints
12. Add data-driven tests with multiple roles
13. Add additional chaos scenarios (DB/Redis failure)
