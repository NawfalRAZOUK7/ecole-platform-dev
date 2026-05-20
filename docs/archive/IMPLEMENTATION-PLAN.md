# École Platform - Validation Suite Implementation Plan

Comprehensive implementation plan for correcting issues, adding missing tests, and implementing enhancements based on review findings.

**Source Documents:**
- `VALIDATION-SUITE-REVIEW.md` - Review findings and issue analysis
- `AUTH-FEATURES-AUDIT.md` - Auth feature audit with gaps
- `IMPLEMENTATION-CHECKLIST.md` - Original implementation checklist

**Last Updated:** 2026-05-12

---

## Phase 1: Critical Fixes (IMMEDIATE - Before Commit)

**Priority:** CRITICAL  
**Estimated Time:** 2-3 hours  
**Goal:** Fix broken Postman collections to make them functional

### Step 1.1: Fix scenario_2fa.postman_collection.json

**Reference:** VALIDATION-SUITE-REVIEW.md - Section "Postman Collection - 2FA Flow"

- [ ] 1.1.1 Fix login request body
  - [ ] Change `"username"` to `"email"` (line 56)
  - [ ] Add `"school_id"` field to login request (required by backend)
  - [ ] Update test assertions to expect correct response structure

- [ ] 1.1.2 Fix TOTP verify endpoint
  - [ ] Change endpoint from `/auth/2fa/verify` to `/auth/2fa/verify-setup` (line 153)
  - [ ] Update test to expect backup codes in response
  - [ ] Add assertion for `backup_codes` array

- [ ] 1.1.3 Fix Login with TOTP flow
  - [ ] Remove `totp_code` from login body (line 219)
  - [ ] Add test step: Login → expect `requires_2fa: true, temp_token`
  - [ ] Add test step: POST `/auth/2fa/verify` with `{ temp_token, code }`
  - [ ] Update assertions to check for access_token after 2FA verify

- [ ] 1.1.4 Fix Disable TOTP method
  - [ ] Change method from DELETE to POST (line 259)
  - [ ] Add request body: `{ "code": "{{totp_code}}" }`
  - [ ] Update test assertions for POST response

- [ ] 1.1.5 Verify against backend API
  - [ ] Cross-reference with `backend/app/api/v1/auth.py`
  - [ ] Cross-reference with `backend/app/schemas/auth.py`
  - [ ] Test collection manually with Newman

### Step 1.2: Fix scenario_email_recovery.postman_collection.json

**Reference:** VALIDATION-SUITE-REVIEW.md - Section "Postman Collection - Email Recovery"

- [ ] 1.2.1 Fix request endpoint
  - [ ] Change from `/auth/password/reset/request` to `/recovery/request` (line 59)
  - [ ] Add `"school_id"` field to request body
  - [ ] Update test to expect `request_id` in response

- [ ] 1.2.2 Add missing OTP verification step
  - [ ] Create new request: POST `/recovery/verify`
  - [ ] Request body: `{ "request_id": "{{reset_request_id}}", "otp": "{{otp}}" }`
  - [ ] Add test assertion for successful verification
  - [ ] Set environment variable `reset_request_id` from previous step

- [ ] 1.2.3 Fix reset endpoint
  - [ ] Change from `/auth/password/reset/confirm` to `/recovery/reset` (line 195)
  - [ ] Update request body to use `request_id` instead of `token`
  - [ ] Update test assertions for password reset success

- [ ] 1.2.4 Fix login field name
  - [ ] Change `"username"` to `"email"` in login request (line 242)
  - [ ] Update test assertions accordingly

- [ ] 1.2.5 Verify against backend API
  - [ ] Cross-reference with `backend/app/api/v1/recovery.py`
  - [ ] Cross-reference with `backend/app/schemas/auth.py` (RecoveryRequestCreate, RecoveryVerifyRequest, RecoveryResetRequest)
  - [ ] Test collection manually with Newman

### Step 1.3: Fix scenario_chaos.postman_collection.json

**Reference:** VALIDATION-SUITE-REVIEW.md - Section "Postman Collection - Chaos Scenarios"

- [ ] 1.3.1 Fix syntax error
  - [ ] Add missing comma in header object after "Authorization" line (line 200)
  - [ ] Validate JSON syntax with jq or Postman linter

- [ ] 1.3.2 Fix webhook dedup test
  - [ ] Change first request to use fixed `provider_event_id` (line 106)
  - [ ] Change second request to use same `provider_event_id` (line 134)
  - [ ] Add environment variable `provider_event_id` set in first request
  - [ ] Update test assertions to check for `already_processed` response

- [ ] 1.3.3 Document async limitations
  - [ ] Add comment in rate limit test explaining async pm.sendRequest limitation
  - [ ] Add comment in load test explaining pm.wait() doesn't block
  - [ ] Add note that these tests work better with curl scripts or k6

- [ ] 1.3.4 Verify webhook endpoint exists
  - [ ] Check if `/payments/webhook/test_psp` exists in backend
  - [ ] If not, update to use actual webhook endpoint or document as placeholder

### Step 1.4: Test all fixed collections

- [ ] 1.4.1 Run scenario_2fa collection
  ```bash
  newman run system-tests/postman/scenario_2fa.postman_collection.json -e system-tests/postman/env_local.json
  ```

- [ ] 1.4.2 Run scenario_email_recovery collection
  ```bash
  newman run system-tests/postman/scenario_email_recovery.postman_collection.json -e system-tests/postman/env_local.json
  ```

- [ ] 1.4.3 Run scenario_chaos collection
  ```bash
  newman run system-tests/postman/scenario_chaos.postman_collection.json -e system-tests/postman/env_local.json
  ```

- [ ] 1.4.4 Run with run_tests.sh script
  ```bash
  system-tests/run_tests.sh --include-scenarios --allow-dev-db
  ```

---

## Phase 2: CI Integration (SHORT TERM - This Week)

**Priority:** HIGH  
**Estimated Time:** 1-2 hours  
**Goal:** Integrate new scenario collections into GitHub Actions CI

### Step 2.1: Review existing CI workflow

**Reference:** `.github/workflows/ci.yml` - postman-tests job (lines 834-933)

- [ ] 2.1.1 Analyze current postman-tests job structure
  - [ ] Review service dependencies (postgres, redis)
  - [ ] Review environment variables
  - [ ] Review Newman installation and configuration

- [ ] 2.1.2 Identify integration point
  - [ ] Determine if new job should be separate or added to existing
  - [ ] Check if scenario tests need different dependencies
  - [ ] Verify scenario tests can run in CI environment

### Step 2.2: Create postman-scenario-tests job

- [ ] 2.2.1 Add new job to ci.yml
  - [ ] Copy postman-tests job structure as template
  - [ ] Rename to postman-scenario-tests
  - [ ] Set dependency on integration-tests job

- [ ] 2.2.2 Add scenario collection runs
  - [ ] Add step to run scenario_chaos collection
  - [ ] Add step to run scenario_2fa collection
  - [ ] Add step to run scenario_email_recovery collection
  - [ ] Add step to run scenario_sentry_testmail collection

- [ ] 2.2.3 Configure environment variables for scenario tests
  - [ ] Add TestMail API key as secret (if not already)
  - [ ] Add test email address
  - [ ] Add TestMail namespace
  - [ ] Add test user credentials (email, password, school_id)

- [ ] 2.2.4 Configure artifact uploads
  - [ ] Upload Newman reports for each scenario
  - [ ] Upload combined HTML report

### Step 2.3: Test CI integration

- [ ] 2.3.1 Push changes to feature branch
- [ ] 2.3.2 Monitor GitHub Actions run
- [ ] 2.3.3 Review artifacts and logs
- [ ] 2.3.4 Fix any CI-specific issues

---

## Phase 3: Missing Auth Tests (SHORT TERM - This Week)

**Priority:** HIGH  
**Estimated Time:** 3-4 hours  
**Goal:** Add Postman collections for missing auth endpoints

### Step 3.1: Create scenario_register.postman_collection.json

**Reference:** AUTH-FEATURES-AUDIT.md - "Implemented Features" section

- [ ] 3.1.1 Create collection structure
  - [ ] Add info block with description
  - [ ] Add environment variables (base_url, invitation_code, email, password, etc.)
  - [ ] Add folder structure

- [ ] 3.1.2 Add request: Generate invitation code
  - [ ] POST /invitations/create
  - [ ] Request body: `{ role_target, expires_in_hours, target_student_id (optional) }`
  - [ ] Test assertion: returns invite_id and code

- [ ] 3.1.3 Add request: Register with invitation code
  - [ ] POST /auth/register
  - [ ] Request body: `{ code, email, full_name, phone, password, profile_data }`
  - [ ] Test assertion: returns access_token and user_id
  - [ ] Test assertion: triggers email verification OTP send

- [ ] 3.1.4 Add request: Verify email (OTP)
  - [ ] POST /auth/verify-email
  - [ ] Request body: `{ user_id, school_id, otp }`
  - [ ] Test assertion: email verification successful

### Step 3.2: Create scenario_session_management.postman_collection.json

- [ ] 3.2.1 Create collection structure
  - [ ] Add environment variables (base_url, token, session_id)
  - [ ] Add folder structure

- [ ] 3.2.2 Add request: Login (to get session)
  - [ ] POST /auth/login
  - [ ] Save session_id from response

- [ ] 3.2.3 Add request: List active sessions
  - [ ] GET /auth/sessions
  - [ ] Test assertion: returns array of sessions
  - [ ] Test assertion: includes current session

- [ ] 3.2.4 Add request: Revoke specific session
  - [ ] DELETE /auth/sessions/{session_id}
  - [ ] Test assertion: session revoked successfully

- [ ] 3.2.5 Add request: List login history
  - [ ] GET /auth/login-history
  - [ ] Test assertion: returns paginated history
  - [ ] Test assertion: includes recent login

### Step 3.3: Create scenario_password_change.postman_collection.json

- [ ] 3.3.1 Create collection structure
  - [ ] Add environment variables (base_url, token, current_password, new_password)

- [ ] 3.3.2 Add request: Login (to get token)
  - [ ] POST /auth/login
  - [ ] Save access_token

- [ ] 3.3.3 Add request: Change password
  - [ ] POST /auth/change-password
  - [ ] Request body: `{ current_password, new_password }`
  - [ ] Test assertion: password change successful
  - [ ] Test assertion: enforces password policy (min 12 chars, etc.)

- [ ] 3.3.4 Add request: Login with new password
  - [ ] POST /auth/login with new password
  - [ ] Test assertion: login successful

- [ ] 3.3.5 Add request: Verify old password doesn't work
  - [ ] POST /auth/login with old password
  - [ ] Test assertion: login fails with 401

### Step 3.4: Update run_tests.sh and README

- [ ] 3.4.1 Update system-tests/postman/README.md
  - [ ] Add new collections to documentation
  - [ ] Add usage instructions

- [ ] 3.4.2 Verify run_tests.sh --include-scenarios picks up new collections
  - [ ] Run: system-tests/run_tests.sh --list --include-scenarios
  - [ ] Verify new collections are listed

---

## Phase 4: Environment Configuration (SHORT TERM - This Week)

**Priority:** HIGH  
**Estimated Time:** 1 hour  
**Goal:** Create environment file for scenario tests

### Step 4.1: Create env_scenarios.json

- [ ] 4.1.1 Create system-tests/postman/env_scenarios.json
  - [ ] Add base_url variable
  - [ ] Add test user credentials (email, password, school_id)
  - [ ] Add TestMail API configuration (api_key, namespace, test_email)
  - [ ] Add invitation code placeholder
  - [ ] Add TOTP code placeholder (for manual testing)

- [ ] 4.1.2 Add env_scenarios.json to .gitignore
  - [ ] Add to .gitignore if it contains secrets
  - [ ] Or create env_scenarios.example.json as template

- [ ] 4.1.3 Document environment setup
  - [ ] Add section to system-tests/postman/README.md
  - [ ] Explain how to configure TestMail
  - [ ] Explain how to get test user credentials

---

## Phase 5: Additional Chaos Scenarios (MEDIUM TERM - Next Sprint)

**Priority:** MEDIUM  
**Estimated Time:** 2-3 hours  
**Goal:** Add more chaos engineering scenarios

### Step 5.1: Add database failure scenario

**Reference:** VALIDATION-SUITE-REVIEW.md - "Missing Test Scenarios" section

- [ ] 5.1.1 Create curl script: 06_db_connection_failure.sh
  - [ ] Test behavior when DB is unreachable
  - [ ] Verify graceful error handling
  - [ ] Verify offline-first behavior

- [ ] 5.1.2 Add to Postman chaos collection
  - [ ] Add folder: "Database Connection Failure"
  - [ ] Add test assertions for error responses

### Step 5.2: Add Redis failure scenario

- [ ] 5.2.1 Create curl script: 07_redis_connection_failure.sh
  - [ ] Test behavior when Redis is unreachable
  - [ ] Verify session/cache fallback behavior

- [ ] 5.2.2 Add to Postman chaos collection
  - [ ] Add folder: "Redis Connection Failure"
  - [ ] Add test assertions

### Step 5.3: Add slow query scenario

- [ ] 5.3.1 Create curl script: 08_slow_query.sh
  - [ ] Test behavior with slow DB queries
  - [ ] Verify timeout handling

### Step 5.4: Update Requestly rules

- [ ] 5.4.1 Add rule for DB failure simulation
- [ ] 5.4.2 Add rule for Redis failure simulation
- [ ] 5.4.3 Update requestly-import.md with new rules

---

## Phase 6: Test Data Cleanup (MEDIUM TERM - Next Sprint)

**Priority:** MEDIUM  
**Estimated Time:** 2 hours  
**Goal:** Add cleanup mechanism to prevent test pollution

### Step 6.1: Create cleanup script

- [ ] 6.1.1 Create tests/cleanup_test_data.sh
  - [ ] Delete test users created during tests
  - [ ] Delete test invitation codes
  - [ ] Delete test recovery requests
  - [ ] Revoke test sessions

- [ ] 6.1.2 Integrate into CI workflow
  - [ ] Add cleanup step after postman-scenario-tests job
  - [ ] Run cleanup even if tests fail (always: true)

### Step 6.2: Add cleanup to Postman collections

- [ ] 6.2.1 Add cleanup folder to each collection
  - [ ] Request to delete test user
  - [ ] Request to revoke test sessions
  - [ ] Mark as optional (allow failure)

---

## Phase 7: k6 Load Tests (LONG TERM - Future)

**Priority:** LOW  
**Estimated Time:** 4-6 hours  
**Goal:** Add k6 load tests for auth endpoints

### Step 7.1: Create k6 auth load tests

**Reference:** VALIDATION-SUITE-REVIEW.md - "Enhancements Recommended" section

- [ ] 7.1.1 Create system-tests/load/auth/01_login_baseline.js
  - [ ] Baseline login load test
  - [ ] Target: 100 RPS for 5 minutes
  - [ ] Measure p50, p90, p95, p99 latency

- [ ] 7.1.2 Create system-tests/load/auth/02_2fa_baseline.js
  - [ ] Baseline 2FA load test
  - [ ] Target: 50 RPS for 5 minutes
  - [ ] Measure TOTP verification latency

- [ ] 7.1.3 Create system-tests/load/auth/03_recovery_baseline.js
  - [ ] Baseline recovery flow load test
  - [ ] Target: 20 RPS for 5 minutes
  - [ **] Measure OTP verification latency

### Step 7.2: Integrate k6 tests into CI

- [ ] 7.2.1 Add k6-auth-tests job to ci.yml
- [ ] 7.2.2 Configure to run after integration-tests
- [ ] 7.2.3 Add artifact upload for k6 results

---

## Phase 8: Data-Driven Tests (LONG TERM - Future)

**Priority:** LOW  
**Estimated Time:** 3-4 hours  
**Goal:** Add tests with multiple roles and contexts

### Step 8.1: Create test data fixtures

- [ ] 8.1.1 Create tests/fixtures/users.json
  - [ ] Test users for each role (STD, TCH, PAR, ADM)
  - [ ] Multiple users per role
  - [ ] Include credentials and school_id

- [ ] 8.1.2 Create tests/fixtures/schools.json
  - [ ] Multiple test school contexts
  - [ ] Different school configurations

- [ ] 8.1.3 Create tests/fixtures/invitation_codes.json
  - [ ] Pre-generated invitation codes
  - [ ] For each role type

### Step 8.2: Create data-driven Postman collections

- [ ] 8.2.1 Use Newman's data file feature
  - [ ] Create CSV/JSON data files for iterations
  - [ ] Test with multiple user roles
  - [ ] Test with multiple school contexts

### Step 8.3: Add edge case tests

- [ ] 8.3.1 Test expired tokens
- [ ] 8.3.2 Test invalid OTPs
- [ ] 8.3.3 Test malformed requests
- [ ] 8.3.4 Test missing required headers

---

## Phase 9: Documentation (ONGOING)

**Priority:** MEDIUM  
**Estimated Time:** 2-3 hours  
**Goal:** Complete documentation gaps

### Step 9.1: Create scenario test setup guide

**Reference:** VALIDATION-SUITE-REVIEW.md - "Documentation Gaps" section

- [ ] 9.1.1 Create system-tests/postman/SCENARIO-SETUP.md
  - [ ] How to configure TestMail API keys
  - [ ] How to set up test users
  - [ ] How to generate invitation codes
  - [ ] How to configure environment variables

### Step 9.2: Create chaos testing guide

- [ ] 9.2.1 Create system-tests/chaos/CHAOS-TESTING-GUIDE.md
  - [ ] When to use Requestly vs curl vs Postman
  - [ ] How to interpret chaos test results
  - [ ] How to tune chaos parameters
  - [ ] Common failure modes and what they test

### Step 9.3: Create CI integration guide

- [ ] 9.3.1 Create .github/POSTMAN-CI.md
  - [ ] How scenario tests run in CI
  - [ ] How to debug CI failures
  - [ ] How to skip specific tests if needed
  - [ ] CI environment configuration

---

## Phase 10: Optional Enhancements (NICE-TO-HAVE)

**Priority:** LOW  
**Estimated Time:** 5-8 hours  
**Goal:** Implement optional enhancements from review

### Step 10.1: Add WebAuthn/Passkeys support tests

**Reference:** AUTH-FEATURES-AUDIT.md - "Gaps / Missing Features" section

- [ ] 10.1.1 Create scenario_webauthn.postman_collection.json
  - [ ] Test WebAuthn registration
  - [ ] Test WebAuthn login
  - [ ] Test WebAuthn disable

### Step 10.2: Add social login tests

- [ ] 10.2.1 Create scenario_social_login.postman_collection.json
  - [ ] Test Google OAuth flow
  - [ ] Test Microsoft OAuth flow
  - [ ] Test Apple OAuth flow

### Step 10.3: Add SMS 2FA tests

- [ ] 10.3.1 Create scenario_sms_2fa.postman_collection.json
  - [ ] Test SMS OTP send
  - [ ] Test SMS OTP verify
  - [ ] Test SMS 2FA disable

### Step 10.4: Add account deletion tests

- [ ] 10.4.1 Create scenario_account_deletion.postman_collection.json
  - [ ] Test account deletion request
  - [ ] Test data export (GDPR)
  - [ ] Test right to be forgotten

### Step 10.5: Add suspicious activity detection tests

- [ ] 10.5.1 Create scenario_suspicious_activity.postman_collection.json
  - [ ] Test login from new location
  - [ ] Test login from new device
  - [ ] Test multiple failed logins

---

## Phase 11: Auth Feature Implementation (FUTURE)

**Priority:** LOW  
**Estimated Time:** 20-30 hours  
**Goal:** Implement missing auth features identified in audit

**Reference:** AUTH-FEATURES-AUDIT.md - "Recommendations" section

### Step 11.1: Implement password reuse policy

- [ ] 11.1.1 Add password history tracking to user model
- [ ] 11.1.2 Store last 5-10 password hashes
- [ ] 11.1.3 Add validation to prevent reuse
- [ ] 11.1.4 Add tests for password reuse prevention

### Step 11.2: Implement account lockout on failed login

- [ ] 11.2.1 Track failed login attempts per user/IP
- [ ] 11.2.2 Implement progressive lockout (5 attempts = 15 min, 10 attempts = 1 hour)
- [ ] 11.2.3 Send email notification on lockout
- [ ] 11.2.4 Add tests for account lockout

### Step 11.3: Implement suspicious activity detection

- [ ] 11.3.1 Track login locations (IP geolocation)
- [ ] 11.3.2 Track device fingerprints
- [ ] 11.3.3 Alert on login from new country/region
- [ ] 11.3.4 Alert on login from new device type
- [ ] 11.3.5 Add tests for suspicious activity alerts

### Step 11.4: Implement WebAuthn/Passkeys

- [ ] 11.4.1 Add WebAuthn registration endpoint
- [ ] 11.4.2 Add WebAuthn login endpoint
- [ ] 11.4.3 Add WebAuthn disable endpoint
- [ ] 11.4.4 Add tests for WebAuthn flow

### Step 11.5: Implement social login (OAuth)

- [ ] 11.5.1 Add Google OAuth integration
- [ ] 11.5.2 Add Microsoft OAuth integration
- [ ] 11.5.3 Add Apple OAuth integration
- [ ] 11.5.4 Add tests for social login flows

---

## Phase 12: Security Enhancements (FUTURE)

**Priority:** MEDIUM  
**Estimated Time:** 5-10 hours  
**Goal:** Implement security improvements

### Step 12.1: Secrets management for tests

**Reference:** VALIDATION-SUITE-REVIEW.md - "Security Considerations" section

- [ ] 12.1.1 Remove TestMail API keys from environment files
- [ ] 12.1.2 Use Doppler for test secrets
- [ ] 12.1.3 Document which secrets are required
- [ ] 12.1.4 Update CI to use Doppler for secrets

### Step 12.2: Rate limiting in tests

- [ ] 12.2.1 Reduce rate limit test request count (100 → 20)
- [ ] 12.2.2 Add delay between requests
- [ ] 12.2.3 Document rate limit considerations

### Step 12.3: Add security headers validation

- [ ] 12.3.1 Add test for security headers (CSP, HSTS, etc.)
- [ ] 12.3.2 Add test for CORS configuration
- [ ] 12.3.3 Add test for content security policy

---

## Implementation Checklist Summary

### Quick Reference

| Phase | Priority | Est. Time | Status |
|-------|----------|-----------|--------|
| Phase 1: Critical Fixes | CRITICAL | 2-3 hrs | ⏳ Pending |
| Phase 2: CI Integration | HIGH | 1-2 hrs | ⏳ Pending |
| Phase 3: Missing Auth Tests | HIGH | 3-4 hrs | ⏳ Pending |
| Phase 4: Environment Config | HIGH | 1 hr | ⏳ Pending |
| Phase 5: Additional Chaos | MEDIUM | 2-3 hrs | ⏳ Pending |
| Phase 6: Test Data Cleanup | MEDIUM | 2 hrs | ⏳ Pending |
| Phase 7: k6 Load Tests | LOW | 4-6 hrs | ⏳ Pending |
| Phase 8: Data-Driven Tests | LOW | 3-4 hrs | ⏳ Pending |
| Phase 9: Documentation | MEDIUM | 2-3 hrs | ⏳ Pending |
| Phase 10: Optional Enhancements | LOW | 5-8 hrs | ⏳ Pending |
| Phase 11: Auth Feature Implementation | LOW | 20-30 hrs | ⏳ Pending |
| Phase 12: Security Enhancements | MEDIUM | 5-10 hrs | ⏳ Pending |

**Total Estimated Time:** 50-76 hours (excluding Phase 11)

---

## Getting Started

### For AI Agent Implementation

1. Start with Phase 1 (Critical Fixes) - these must be done before committing
2. Proceed through Phases 2-4 in order (Short Term priorities)
3. Implement Phases 5-6 as time permits (Medium Term)
4. Phases 7-12 are optional and can be done incrementally

### For Manual Implementation

1. Review Phase 1 items and fix Postman collections manually
2. Test each fixed collection with Newman before proceeding
3. Use the checklist items to track progress
4. Reference the source documents for detailed context

### Progress Tracking

Use this file as a master checklist. Mark items as complete with `[x]` as you work through them.

---

## Notes

- This plan is based on findings from `VALIDATION-SUITE-REVIEW.md`
- Auth feature gaps are from `AUTH-FEATURES-AUDIT.md`
- Original implementation context is from `IMPLEMENTATION-CHECKLIST.md`
- Adjust timelines based on actual implementation experience
- Some phases may require coordination with backend team
- Always test changes in a branch before merging to main
