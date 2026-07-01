# AI Agent Prompts for École Platform Validation Suite Implementation

This file contains pre-written prompts for each phase of the implementation plan. Each prompt is designed to be copied and pasted to an AI agent to execute that specific phase.

**Related Documents:**
- `IMPLEMENTATION-PLAN.md` - Master implementation plan with all phases
- `VALIDATION-SUITE-REVIEW.md` - Review findings and issue analysis
- `AUTH-FEATURES-AUDIT.md` - Auth feature audit with gaps
- `IMPLEMENTATION-CHECKLIST.md` - Original implementation checklist

---

## Initial Prompt - Setup and Context

```
You are implementing the École Platform validation suite enhancements and fixes. This is a multi-phase project to correct issues, add missing tests, and implement improvements.

**Context:**
- The validation suite includes Postman collections, curl chaos scripts, Requestly rules, and CI integration
- A review was conducted and documented in VALIDATION-SUITE-REVIEW.md
- Several critical issues were found in the Postman collections that need immediate fixing
- The implementation plan is documented in IMPLEMENTATION-PLAN.md with 12 phases

**Your Task:**
Start by reading the following files in order to understand the context:
1. IMPLEMENTATION-PLAN.md - Read the entire file to understand all phases
2. VALIDATION-SUITE-REVIEW.md - Read to understand the issues found
3. AUTH-FEATURES-AUDIT.md - Read to understand auth feature gaps
4. IMPLEMENTATION-CHECKLIST.md - Read to understand original implementation

After reading these files, confirm you understand:
- What are the 3 critical Postman collection issues that need immediate fixing?
- What is the correct 2FA flow according to the backend API?
- What is the correct password recovery flow according to the backend API?
- What are the missing auth endpoints that need test coverage?

Once you confirm understanding, we will proceed with Phase 1: Critical Fixes.
```

---

## Phase 1 Prompt - Critical Fixes

```
**Phase 1: Critical Fixes (IMMEDIATE - Before Commit)**

**Goal:** Fix the 3 broken Postman collections to make them functional

**Reference:** IMPLEMENTATION-PLAN.md - Phase 1 section, VALIDATION-SUITE-REVIEW.md - Critical Issues section

**Step 1.1: Fix scenario_2fa.postman_collection.json**

The current collection has these issues:
- Uses "username" instead of "email" in login request (backend expects email)
- Uses wrong endpoint: /auth/2fa/verify should be /auth/2fa/verify-setup
- Login with TOTP flow is incorrect (should use temp_token flow)
- Disable TOTP uses DELETE instead of POST

**Correct 2FA Flow (from backend/app/api/v1/auth.py):**
1. POST /auth/login with { email, password, school_id } → returns { access_token } or { requires_2fa: true, temp_token }
2. POST /auth/2fa/setup (protected) → returns { totp_secret, qr_code_url }
3. POST /auth/2fa/verify-setup (protected) with { code } → activates 2FA, returns backup codes
4. POST /auth/login with { email, password, school_id } → returns { requires_2fa: true, temp_token }
5. POST /auth/2fa/verify (public) with { temp_token, code } → returns { access_token }
6. POST /auth/2fa/disable (protected) with { code } → disables 2FA

**Fix the collection:**
1. Change login request to use "email" and "school_id" fields
2. Change TOTP verify endpoint to /auth/2fa/verify-setup
3. Implement correct temp_token flow for login with TOTP
4. Change disable TOTP to POST method with body { "code": "..." }
5. Update all test assertions accordingly

**Step 1.2: Fix scenario_email_recovery.postman_collection.json**

The current collection has these issues:
- Uses /auth/password/reset/request instead of /recovery/request
- Uses /auth/password/reset/confirm instead of /recovery/reset
- Missing /recovery/verify OTP verification step
- Uses "username" instead of "email"
- Missing school_id field

**Correct Recovery Flow (from backend/app/api/v1/recovery.py):**
1. POST /recovery/request with { email, school_id } → returns { request_id }
2. POST /recovery/verify with { request_id, otp } → verifies OTP
3. POST /recovery/reset with { request_id, new_password } → resets password

**Fix the collection:**
1. Change request endpoint to /recovery/request with { email, school_id }
2. Add new request for /recovery/verify with { request_id, otp }
3. Change reset endpoint to /recovery/reset with { request_id, new_password }
4. Change "username" to "email" in login request
5. Add school_id to all requests that need it

**Step 1.3: Fix scenario_chaos.postman_collection.json**

The current collection has these issues:
- Syntax error: missing comma in header object (line 200)
- Webhook dedup test uses different provider_event_id for both requests (won't test dedup)
- Rate limit and load tests have async limitations (document but don't fix)

**Fix the collection:**
1. Add missing comma in header object after "Authorization" line
2. Fix webhook dedup test to use same provider_event_id for both requests
3. Add comments documenting async limitations of rate limit and load tests

**Step 1.4: Test all fixed collections**

Run each collection with Newman to verify they work:
```bash
newman run system-tests/postman/scenario_2fa.postman_collection.json -e system-tests/postman/env_local.json
newman run system-tests/postman/scenario_email_recovery.postman_collection.json -e system-tests/postman/env_local.json
newman run system-tests/postman/scenario_chaos.postman_collection.json -e system-tests/postman/env_local.json
```

Also test with run_tests.sh:
```bash
system-tests/run_tests.sh --include-scenarios --allow-dev-db
```

**Deliverable:**
- Fixed scenario_2fa.postman_collection.json
- Fixed scenario_email_recovery.postman_collection.json
- Fixed scenario_chaos.postman_collection.json
- Confirmation that all 3 collections pass Newman tests

**Verification:**
Cross-reference your changes with backend/app/api/v1/auth.py and backend/app/api/v1/recovery.py to ensure endpoints and request formats match exactly.
```

---

## Phase 2 Prompt - CI Integration

```
**Phase 2: CI Integration (SHORT TERM - This Week)**

**Goal:** Integrate new scenario collections into GitHub Actions CI

**Reference:** IMPLEMENTATION-PLAN.md - Phase 2 section, .github/workflows/ci.yml (lines 834-933)

**Step 2.1: Review existing CI workflow**

Read the postman-tests job in .github/workflows/ci.yml (lines 834-933) to understand:
- Service dependencies (postgres, redis)
- Environment variables
- Newman installation and configuration
- How the full smoke collection is run

**Step 2.2: Create postman-scenario-tests job**

Add a new job to ci.yml called "postman-scenario-tests" that:
- Runs after integration-tests job (needs: [integration-tests])
- Uses the same service dependencies as postman-tests
- Runs the 4 scenario collections:
  - scenario_chaos.postman_collection.json
  - scenario_2fa.postman_collection.json
  - scenario_email_recovery.postman_collection.json
  - scenario_sentry_testmail.postman_collection.json

**Step 2.3: Configure environment variables for scenario tests**

Add these environment variables (use GitHub Secrets for sensitive values):
- TESTMAIL_API_KEY
- TESTMAIL_NAMESPACE
- TEST_EMAIL
- TEST_USER_EMAIL
- TEST_USER_PASSWORD
- TEST_SCHOOL_ID

**Step 2.4: Configure artifact uploads**

Upload Newman reports for each scenario collection as CI artifacts.

**Step 2.5: Test CI integration**

1. Push changes to a feature branch
2. Monitor the GitHub Actions run
3. Review artifacts and logs
4. Fix any CI-specific issues

**Deliverable:**
- Updated .github/workflows/ci.yml with postman-scenario-tests job
- GitHub Secrets configured for test environment variables
- Successful CI run with all scenario collections passing
```

---

## Phase 3 Prompt - Missing Auth Tests

```
**Phase 3: Missing Auth Tests (SHORT TERM - This Week)**

**Goal:** Add Postman collections for missing auth endpoints

**Reference:** IMPLEMENTATION-PLAN.md - Phase 3 section, AUTH-FEATURES-AUDIT.md - "Missing Test Scenarios"

**Step 3.1: Create scenario_register.postman_collection.json**

Create a new Postman collection for invitation-based registration flow:

**Requests to add:**
1. POST /invitations/create - Generate invitation code
   - Body: { role_target, expires_in_hours, target_student_id (optional) }
   - Test: returns invite_id and code

2. POST /auth/register - Register with invitation code
   - Body: { code, email, full_name, phone, password, profile_data }
   - Test: returns access_token and user_id
   - Test: triggers email verification OTP send

3. POST /auth/verify-email - Verify email with OTP
   - Body: { user_id, school_id, otp }
   - Test: email verification successful

**Step 3.2: Create scenario_session_management.postman_collection.json**

Create a new Postman collection for session management:

**Requests to add:**
1. POST /auth/login - Login to get session
2. GET /auth/sessions - List active sessions
   - Test: returns array of sessions
   - Test: includes current session
3. DELETE /auth/sessions/{session_id} - Revoke specific session
   - Test: session revoked successfully
4. GET /auth/login-history - List login history
   - Test: returns paginated history
   - Test: includes recent login

**Step 3.3: Create scenario_password_change.postman_collection.json**

Create a new Postman collection for password change:

**Requests to add:**
1. POST /auth/login - Login to get token
2. POST /auth/change-password - Change password
   - Body: { current_password, new_password }
   - Test: password change successful
   - Test: enforces password policy (min 12 chars, etc.)
3. POST /auth/login - Login with new password
   - Test: login successful
4. POST /auth/login - Login with old password
   - Test: login fails with 401

**Step 3.4: Update documentation**

Update system-tests/postman/README.md to include the new collections.

**Deliverable:**
- scenario_register.postman_collection.json
- scenario_session_management.postman_collection.json
- scenario_password_change.postman_collection.json
- Updated system-tests/postman/README.md
- All collections tested with Newman
```

---

## Phase 4 Prompt - Environment Configuration

```
**Phase 4: Environment Configuration (SHORT TERM - This Week)**

**Goal:** Create environment file for scenario tests

**Reference:** IMPLEMENTATION-PLAN.md - Phase 4 section

**Step 4.1: Create env_scenarios.json**

Create system-tests/postman/env_scenarios.json with these variables:
- base_url: http://localhost:8000/api/v1
- test_user_email: (test user email)
- test_user_password: (test user password)
- test_school_id: (test school UUID)
- testmail_api_key: (TestMail API key)
- testmail_namespace: (TestMail namespace)
- test_email: (email for TestMail testing)
- invitation_code: (placeholder for invitation code)
- totp_code: (placeholder for TOTP code for manual testing)

**Step 4.2: Handle secrets properly**

If env_scenarios.json contains secrets:
- Add env_scenarios.json to .gitignore
- Create env_scenarios.example.json as a template with placeholder values

**Step 4.3: Document environment setup**

Add a section to system-tests/postman/README.md explaining:
- How to configure TestMail
- How to get test user credentials
- How to set up environment variables

**Deliverable:**
- system-tests/postman/env_scenarios.json (or .example.json)
- Updated .gitignore if needed
- Updated system-tests/postman/README.md with environment setup instructions
```

---

## Phase 5 Prompt - Additional Chaos Scenarios

```
**Phase 5: Additional Chaos Scenarios (MEDIUM TERM - Next Sprint)**

**Goal:** Add more chaos engineering scenarios

**Reference:** IMPLEMENTATION-PLAN.md - Phase 5 section, VALIDATION-SUITE-REVIEW.md - "Missing Test Scenarios"

**Step 5.1: Add database failure scenario**

Create system-tests/chaos/curl/06_db_connection_failure.sh:
- Test behavior when DB is unreachable
- Verify graceful error handling
- Verify offline-first behavior

Add to Postman chaos collection with folder "Database Connection Failure".

**Step 5.2: Add Redis failure scenario**

Create system-tests/chaos/curl/07_redis_connection_failure.sh:
- Test behavior when Redis is unreachable
- Verify session/cache fallback behavior

Add to Postman chaos collection with folder "Redis Connection Failure".

**Step 5.3: Add slow query scenario**

Create system-tests/chaos/curl/08_slow_query.sh:
- Test behavior with slow DB queries
- Verify timeout handling

**Step 5.4: Update Requestly rules**

Add to system-tests/chaos/requestly-rules.json:
- Rule for DB failure simulation
- Rule for Redis failure simulation

Update system-tests/chaos/requestly-import.md with new rules documentation.

**Deliverable:**
- 3 new curl scripts (06_db_connection_failure.sh, 07_redis_connection_failure.sh, 08_slow_query.sh)
- Updated scenario_chaos.postman_collection.json with new scenarios
- Updated requestly-rules.json with new rules
- Updated requestly-import.md
```

---

## Phase 6 Prompt - Test Data Cleanup

```
**Phase 6: Test Data Cleanup (MEDIUM TERM - Next Sprint)**

**Goal:** Add cleanup mechanism to prevent test pollution

**Reference:** IMPLEMENTATION-PLAN.md - Phase 6 section

**Step 6.1: Create cleanup script**

Create tests/cleanup_test_data.sh that:
- Deletes test users created during tests
- Deletes test invitation codes
- Deletes test recovery requests
- Revokes test sessions

The script should:
- Accept parameters for what to clean (users, invitations, sessions, etc.)
- Use the backend API to perform cleanup
- Be idempotent (safe to run multiple times)

**Step 6.2: Integrate into CI workflow**

Add a cleanup step after the postman-scenario-tests job in .github/workflows/ci.yml:
- Run cleanup even if tests fail (always: true)
- Use the test environment variables

**Step 6.3: Add cleanup to Postman collections**

Add a "Cleanup" folder to each scenario collection with:
- Request to delete test user
- Request to revoke test sessions
- Mark as optional (allow failure)

**Deliverable:**
- tests/cleanup_test_data.sh
- Updated .github/workflows/ci.yml with cleanup step
- Updated Postman collections with cleanup folders
```

---

## Phase 7 Prompt - k6 Load Tests

```
**Phase 7: k6 Load Tests (LONG TERM - Future)**

**Goal:** Add k6 load tests for auth endpoints

**Reference:** IMPLEMENTATION-PLAN.md - Phase 7 section

**Step 7.1: Create k6 auth load tests**

Create system-tests/load/auth/ directory with these files:

1. system-tests/load/auth/01_login_baseline.js
   - Baseline login load test
   - Target: 100 RPS for 5 minutes
   - Measure p50, p90, p95, p99 latency

2. system-tests/load/auth/02_2fa_baseline.js
   - Baseline 2FA load test
   - Target: 50 RPS for 5 minutes
   - Measure TOTP verification latency

3. system-tests/load/auth/03_recovery_baseline.js
   - Baseline recovery flow load test
   - Target: 20 RPS for 5 minutes
   - Measure OTP verification latency

Each k6 script should:
- Use environment variables for base_url
- Have proper setup and teardown
- Export metrics in JSON format
- Include assertions for response times

**Step 7.2: Integrate k6 tests into CI**

Add a k6-auth-tests job to .github/workflows/ci.yml:
- Run after integration-tests
- Configure to run the 3 k6 scripts
- Add artifact upload for k6 results

**Deliverable:**
- 3 k6 load test scripts
- Updated .github/workflows/ci.yml with k6-auth-tests job
- Successful CI run with k6 tests
```

---

## Phase 8 Prompt - Data-Driven Tests

```
**Phase 8: Data-Driven Tests (LONG TERM - Future)**

**Goal:** Add tests with multiple roles and contexts

**Reference:** IMPLEMENTATION-PLAN.md - Phase 8 section

**Step 8.1: Create test data fixtures**

Create tests/fixtures/ directory with these files:

1. tests/fixtures/users.json
   - Test users for each role (STD, TCH, PAR, ADM)
   - Multiple users per role
   - Include credentials and school_id

2. tests/fixtures/schools.json
   - Multiple test school contexts
   - Different school configurations

3. tests/fixtures/invitation_codes.json
   - Pre-generated invitation codes
   - For each role type

**Step 8.2: Create data-driven Postman collections**

Use Newman's data file feature:
- Create CSV/JSON data files for iterations
- Test with multiple user roles
- Test with multiple school contexts

**Step 8.3: Add edge case tests**

Add tests for:
- Expired tokens
- Invalid OTPs
- Malformed requests
- Missing required headers

**Deliverable:**
- Test fixture files (users.json, schools.json, invitation_codes.json)
- Data-driven Postman collections
- Edge case test requests
```

---

## Phase 9 Prompt - Documentation

```
**Phase 9: Documentation (ONGOING)**

**Goal:** Complete documentation gaps

**Reference:** IMPLEMENTATION-PLAN.md - Phase 9 section, VALIDATION-SUITE-REVIEW.md - "Documentation Gaps"

**Step 9.1: Create scenario test setup guide**

Create system-tests/postman/SCENARIO-SETUP.md with:
- How to configure TestMail API keys
- How to set up test users
- How to generate invitation codes
- How to configure environment variables
- Troubleshooting common setup issues

**Step 9.2: Create chaos testing guide**

Create system-tests/chaos/CHAOS-TESTING-GUIDE.md with:
- When to use Requestly vs curl vs Postman
- How to interpret chaos test results
- How to tune chaos parameters
- Common failure modes and what they test
- Safety precautions for chaos testing

**Step 9.3: Create CI integration guide**

Create .github/POSTMAN-CI.md with:
- How scenario tests run in CI
- How to debug CI failures
- How to skip specific tests if needed
- CI environment configuration
- CI artifact locations and interpretation

**Deliverable:**
- system-tests/postman/SCENARIO-SETUP.md
- system-tests/chaos/CHAOS-TESTING-GUIDE.md
- .github/POSTMAN-CI.md
```

---

## Phase 10 Prompt - Optional Enhancements

```
**Phase 10: Optional Enhancements (NICE-TO-HAVE)**

**Goal:** Implement optional enhancements from review

**Reference:** IMPLEMENTATION-PLAN.md - Phase 10 section, AUTH-FEATURES-AUDIT.md - "Gaps / Missing Features"

**Step 10.1: Add WebAuthn/Passkeys support tests**

Create scenario_webauthn.postman_collection.json:
- Test WebAuthn registration
- Test WebAuthn login
- Test WebAuthn disable

**Step 10.2: Add social login tests**

Create scenario_social_login.postman_collection.json:
- Test Google OAuth flow
- Test Microsoft OAuth flow
- Test Apple OAuth flow

**Step 10.3: Add SMS 2FA tests**

Create scenario_sms_2fa.postman_collection.json:
- Test SMS OTP send
- Test SMS OTP verify
- Test SMS 2FA disable

**Step 10.4: Add account deletion tests**

Create scenario_account_deletion.postman_collection.json:
- Test account deletion request
- Test data export (GDPR)
- Test right to be forgotten

**Step 10.5: Add suspicious activity detection tests**

Create scenario_suspicious_activity.postman_collection.json:
- Test login from new location
- Test login from new device
- Test multiple failed logins

**Note:** These are optional and should only be implemented if the corresponding features exist in the backend.

**Deliverable:**
- Postman collections for implemented features only
- Skip collections for features not yet implemented
```

---

## Phase 11 Prompt - Auth Feature Implementation

```
**Phase 11: Auth Feature Implementation (FUTURE)**

**Goal:** Implement missing auth features identified in audit

**Reference:** IMPLEMENTATION-PLAN.md - Phase 11 section, AUTH-FEATURES-AUDIT.md - "Recommendations"

**WARNING:** This phase requires backend code changes, not just test changes. Coordinate with backend team.

**Step 11.1: Implement password reuse policy**

Backend changes:
- Add password history tracking to user model
- Store last 5-10 password hashes
- Add validation to prevent reuse
- Add tests for password reuse prevention

**Step 11.2: Implement account lockout on failed login**

Backend changes:
- Track failed login attempts per user/IP
- Implement progressive lockout (5 attempts = 15 min, 10 attempts = 1 hour)
- Send email notification on lockout
- Add tests for account lockout

**Step 11.3: Implement suspicious activity detection**

Backend changes:
- Track login locations (IP geolocation)
- Track device fingerprints
- Alert on login from new country/region
- Alert on login from new device type
- Add tests for suspicious activity alerts

**Step 11.4: Implement WebAuthn/Passkeys**

Backend changes:
- Add WebAuthn registration endpoint
- Add WebAuthn login endpoint
- Add WebAuthn disable endpoint
- Add tests for WebAuthn flow

**Step 11.5: Implement social login (OAuth)**

Backend changes:
- Add Google OAuth integration
- Add Microsoft OAuth integration
- Add Apple OAuth integration
- Add tests for social login flows

**Deliverable:**
- Backend code changes for each feature
- Database migrations if needed
- Tests for each feature
- Documentation updates
```

---

## Phase 12 Prompt - Security Enhancements

```
**Phase 12: Security Enhancements (FUTURE)**

**Goal:** Implement security improvements

**Reference:** IMPLEMENTATION-PLAN.md - Phase 12 section, VALIDATION-SUITE-REVIEW.md - "Security Considerations"

**Step 12.1: Secrets management for tests**

- Remove TestMail API keys from environment files
- Use Doppler for test secrets
- Document which secrets are required
- Update CI to use Doppler for secrets

**Step 12.2: Rate limiting in tests**

- Reduce rate limit test request count (100 → 20)
- Add delay between requests
- Document rate limit considerations

**Step 12.3: Add security headers validation**

Add tests for:
- Security headers (CSP, HSTS, X-Frame-Options, etc.)
- CORS configuration
- Content security policy

**Deliverable:**
- Updated environment configuration for secrets
- Updated rate limit test
- Security header validation tests
```

---

## Final Verification Prompt

```
**Final Verification - Implementation Complete**

**Goal:** Verify all implemented phases and ensure quality

**Step 1: Review all implemented changes**

Review the following files to ensure all changes are correct:
- IMPLEMENTATION-PLAN.md - Mark completed phases with [x]
- VALIDATION-SUITE-REVIEW.md - Verify all critical issues are addressed
- All modified Postman collections
- All new Postman collections
- All new curl scripts
- .github/workflows/ci.yml
- Documentation files

**Step 2: Run all tests**

Run all Postman collections:
```bash
system-tests/run_tests.sh --all --allow-dev-db
```

Run all curl chaos scripts:
```bash
cd system-tests/chaos/curl
./run-all.sh --token <jwt> --ngrok-url <ngrok-url>
```

**Step 3: Verify CI integration**

- Push all changes to a feature branch
- Monitor GitHub Actions run
- Verify all jobs pass
- Review artifacts

**Step 4: Create summary report**

Create a summary report (IMPLEMENTATION-SUMMARY.md) with:
- List of all completed phases
- List of all files created/modified
- Test results summary
- Any remaining issues or limitations
- Recommendations for future work

**Step 5: Update documentation**

Update IMPLEMENTATION-CHECKLIST.md with:
- Mark all completed items
- Add any new items discovered during implementation
- Update status sections

**Deliverable:**
- All tests passing
- CI integration working
- IMPLEMENTATION-SUMMARY.md
- Updated IMPLEMENTATION-CHECKLIST.md
- Ready for code review and merge
```

---

## Usage Instructions

### For AI Agent Implementation

1. Start with the **Initial Prompt** to provide context
2. Execute phases in order (1 → 12)
3. For each phase, copy the corresponding **Phase Prompt**
4. After completing a phase, use the **Final Verification Prompt** if appropriate
5. Track progress in IMPLEMENTATION-PLAN.md by marking items with [x]

### For Manual Implementation

1. Read all source documents first
2. Work through phases sequentially
3. Use the prompts as checklists
4. Test each phase before proceeding to the next
5. Mark completed items in IMPLEMENTATION-PLAN.md

### Progress Tracking

Use IMPLEMENTATION-PLAN.md as the master checklist. Mark items as complete with [x] as you work through them.

### Notes

- Phases 1-4 are critical and should be done first
- Phases 5-6 are medium priority
- Phases 7-12 are optional and can be done incrementally
- Phase 11 requires backend coordination
- Always test changes in a branch before merging to main
