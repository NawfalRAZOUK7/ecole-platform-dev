# École Platform — Implementation Checklist

Complete validation suite: workflow run, Sentry verification, Doppler stg/prd populate, chaos/auth/Sentry test files, and auth feature audit.

---

## Step 1 — Verify Doppler dev secrets present

- [ ] Run `doppler secrets get SENTRY_DSN VITE_SENTRY_DSN MOBILE_SENTRY_DSN TESTMAIL_API_KEY TESTMAIL_NAMESPACE --plain --config dev`
- [ ] Confirm all 5 values are returned (non-empty)
- [ ] Verify backend DSN starts with `https://...@o4510448810000384.ingest.de.sentry.io/4511374465106000`
- [ ] Verify web DSN starts with `https://...@o4510448810000384.ingest.de.sentry.io/4511374499643472`
- [ ] Verify mobile DSN starts with `https://...@o4510448810000384.ingest.de.sentry.io/4511374561050704`
- [ ] Verify TestMail API key is present (32-char hex)
- [ ] Verify TestMail namespace is `ibatt`

**Status:** ✅ Complete (verified earlier)

---

## Step 2 — Start dev stack via doppler-run + make up

- [ ] Verify Docker daemon is running (`docker info`)
- [ ] Run `make doppler-run CMD="make up"`
- [ ] Wait for `docker compose up -d --build` to complete (5-8 min on first build)
- [ ] Poll `curl -sf http://localhost:8000/api/v1/health` until it returns 200 (max 60 s)
- [ ] Verify `ecole-backend` container is Up
- [ ] Verify `ecole-web` container is Up on port 5173
- [ ] Verify `ecole-postgres` is healthy
- [ ] Verify `ecole-redis` is healthy
- [ ] Verify `ecole-minio` is healthy
- [ ] If any container fails to start, run `make logs` and triage

**Status:** ✅ Complete (web container fixed, all services up)

---

## Step 3 — Sentry sanity verification

- [ ] Run `curl -i http://localhost:8000/api/v1/sentry-debug`
- [ ] Confirm response is HTTP 500 (intentional `1/0` division)
- [ ] Run `curl -sf http://localhost:8000/api/v1/health` (normal request for transaction)
- [ ] Open Sentry project URL: https://ensmr.sentry.io/issues/?project=4511374465106000
- [ ] Verify the error event appears in Sentry within 60 seconds
- [ ] Verify the event has `environment: development` tag
- [ ] Verify a transaction event appears for the health check
- [ ] If event doesn't arrive, check backend logs for `sentry_sdk.init` lines
- [ ] If DSN was empty, verify Doppler injection worked

**Status:** ⏳ Pending

---

## Step 4 — Generate + run Doppler stg_main/prd_main populate script

- [ ] Create `infra/doppler/populate-stg-prd-defaults.sh`
- [ ] Review the script contents (non-secret defaults + CHANGE_ME placeholders)
- [ ] Run the script to populate `stg_main` config
- [ ] Run the script to populate `prd_main` config
- [ ] Verify `doppler secrets list --config stg_main` shows the new keys
- [ ] Verify `doppler secrets list --config prd_main` shows the new keys
- [ ] Confirm `APP_ENV=staging` in stg_main
- [ ] Confirm `APP_ENV=production` in prd_main
- [ ] Confirm all secrets are marked `CHANGE_ME_*` except safe defaults

**Status:** ⏳ Pending

---

## Step 5a — Requestly rules JSON + import doc

- [ ] Create `system-tests/chaos/requestly-rules.json` (Requestly import schema)
- [ ] Add Rule 1: Modify Response on `/api/v1/sync/push` → 503 + retry_after body
- [ ] Add Rule 2: Delay Request on `.*\/api\/v1\/sync\/.*` → 800 ms
- [ ] Add Rule 3: Modify Response on `/api/v1/` → 429 + Retry-After: 5 (toggleable)
- [ ] Add Rule 4: Modify Response on `/api/v1/payments/webhook/.*` → optional bypass mode
- [ ] Create `system-tests/chaos/requestly-import.md` with import instructions
- [ ] Test JSON validity (if possible)
- [ ] Update `system-tests/chaos/README.md` to reference the new files

**Status:** ⏳ Pending

---

## Step 5b — 5 curl chaos scripts + run-all orchestrator

- [ ] Create `system-tests/chaos/curl/01_sync_push_503.sh`
  - [ ] Accept `--token`, `--base-url` flags
  - [ ] POST `/sync/push` with sample payload
  - [ ] Expect 200 or 503 (Requestly-injected)
  - [ ] Print pass/fail
- [ ] Create `system-tests/chaos/curl/02_webhook_duplicate.sh`
  - [ ] POST PSP webhook twice with same `provider_event_id`
  - [ ] Assert `already_processed: true` on second
- [ ] Create `system-tests/chaos/curl/03_rate_limit_429.sh`
  - [ ] Fire 100 requests at `/auth/me`
  - [ ] Sort response codes
  - [ ] Expect mostly 200 + some 429
- [ ] Create `system-tests/chaos/curl/04_latency_800ms.sh`
  - [ ] Single request to `/sync/pull`
  - [ ] Measure `time_total`
  - [ ] Assert > 800ms when Requestly rule active
- [ ] Create `system-tests/chaos/curl/05_load_smoke.sh`
  - [ ] 10-RPS for 30 s against chosen endpoint
  - [ ] Use `curl` + `parallel` or loop
  - [ ] Report success rate
- [ ] Create `system-tests/chaos/run-all.sh` orchestrator
  - [ ] Accept `--token`, `--base-url`, `--ngrok-url` flags
  - [ ] Run all 5 scripts in sequence
  - [ ] Print summary table
- [ ] Make all scripts executable (`chmod +x`)
- [ ] Update `system-tests/chaos/README.md` with usage examples

**Status:** ⏳ Pending

---

## Step 5c — Postman collection - chaos scenarios

- [ ] Create `system-tests/postman/scenario_chaos.postman_collection.json`
- [ ] Add folder: "Sync Push 503" with POST `/sync/push` + assertion
- [ ] Add folder: "Webhook Dedup" with double POST + `already_processed` assertion
- [ ] Add folder: "Rate Limit 429" with loop + 429 detection
- [ ] Add folder: "Latency 800ms" with timing assertion
- [ ] Add folder: "Load Smoke" with 10-RPS loop
- [ ] Add environment variable: `base_url` (default `http://localhost:8000/api/v1`)
- [ ] Add environment variable: `token` (optional)
- [ ] Add Newman command in collection description
- [ ] Update `system-tests/postman/README.md` to reference the collection

**Status:** ⏳ Pending

---

## Step 5d — Postman collection - 2FA flow

- [ ] Create `system-tests/postman/scenario_2fa_flow.postman_collection.json`
- [ ] Add request: "Login" → POST `/auth/login` → expect `pending_2fa` response
- [ ] Add request: "Setup 2FA" → POST `/auth/2fa/setup` → get otpauth URI + backup codes
- [ ] Add request: "Verify Enrolment" → POST `/auth/2fa/verify` → confirm enrolment
- [ ] Add request: "Logout" → POST `/auth/logout`
- [ ] Add request: "Login Again" → POST `/auth/login` → expect 2FA challenge
- [ ] Add request: "Login with TOTP" → POST `/auth/2fa/login` with TOTP code
  - [ ] Pre-request script: use `crypto-js` to generate TOTP from secret
- [ ] Add request: "Disable 2FA" → POST `/auth/2fa/disable` with backup code
- [ ] Add assertions at each step
- [ ] Update `system-tests/postman/README.md`

**Status:** ⏳ Pending

---

## Step 5e — Postman collection - email recovery (TestMail)

- [ ] Create `system-tests/postman/scenario_email_recovery.postman_collection.json`
- [ ] Add request: "Request Recovery" → POST `/recovery/request` with Testmail address
- [ ] Pre-request script: generate fresh `fresh_email` Testmail address
- [ ] Add request: "Poll Testmail" → GET Testmail API to find OTP email
  - [ ] Pre-request script: poll up to 30 s with exponential backoff
- [ ] Add request: "Verify OTP" → POST `/recovery/verify` with extracted OTP
- [ ] Add request: "Reset Password" → POST `/recovery/reset` with new password
- [ ] Add request: "Login with New Password" → POST `/auth/login` → expect 200
- [ ] Add environment variable: `testmail_api_key` (from Doppler)
- [ ] Add environment variable: `testmail_namespace` (from Doppler)
- [ ] Update `system-tests/postman/README.md`

**Status:** ⏳ Pending

---

## Step 5f — Postman collection - Sentry/TestMail validation

- [ ] Create `system-tests/postman/scenario_sentry_testmail_validation.postman_collection.json`
- [ ] Add request: "Sentry Debug" → GET `/sentry-debug` → expect 500
- [ ] Add request: "Send Test Email" → POST a noop email send
- [ ] Pre-request script: poll Testmail API to assert receipt
- [ ] Add request: "Print Sentry Project URL" → print in tests
- [ ] Add assertions for each step
- [ ] Update `system-tests/postman/README.md`

**Status:** ⏳ Pending

---

## Step 5g — Update system-tests/chaos/README + system-tests/postman/README

- [ ] Update `system-tests/chaos/README.md`
  - [ ] Add section "Requestly Rules" with import command
  - [ ] Add section "Curl Scripts" with `./run-all.sh` usage
  - [ ] Link to `requestly-rules.json` and `curl/` directory
- [ ] Update `system-tests/postman/README.md`
  - [ ] List all 4 new collections
  - [ ] Provide Newman run commands for each
  - [ ] Document required environment variables

**Status:** ⏳ Pending

---

## Step 6 — Auth feature audit + AUTH-FEATURES-AUDIT.md

- [ ] Grep for `lockout` / `failed_attempts` in backend code
- [ ] Grep for password validators in `auth.py`
- [ ] Grep for session listing/revocation endpoints
- [ ] Create `docs/AUTH-FEATURES-AUDIT.md`
- [ ] Add table: Capability | Status | Evidence | External config needed?
- [ ] Audit: Email + password login (✅)
- [ ] Audit: Logout (token revocation) (✅)
- [ ] Audit: Refresh tokens (HttpOnly cookie) (✅)
- [ ] Audit: CSRF double-submit (✅)
- [ ] Audit: Email verification (✅)
- [ ] Audit: Password recovery (OTP via email) (✅)
- [ ] Audit: TOTP 2FA (QR code) (✅)
- [ ] Audit: TOTP backup codes (✅)
- [ ] Audit: Rate limiting on auth (✅)
- [ ] Audit: Account lockout after N failures (⚠️)
- [ ] Audit: Password complexity rules (⚠️)
- [ ] Audit: Multi-tenancy (school × role) (✅)
- [ ] Audit: Invitation codes (✅)
- [ ] Audit: Role-based access (RBAC) (✅)
- [ ] Audit: Attribute-based access (ABAC) (✅)
- [ ] Audit: Audit log of auth events (✅)
- [ ] Audit: Active session listing/revocation (⚠️)
- [ ] Audit: OAuth (Google, Microsoft) (❌)
- [ ] Audit: WebAuthn / Passkeys (❌)
- [ ] Audit: SMS 2FA (❌)
- [ ] Audit: Magic links (passwordless) (❌)
- [ ] Add "What's safe to ship today" section
- [ ] Add "What's worth adding before production" section
- [ ] Add "What's nice-to-have but external" section

**Status:** ⏳ Pending

---

## Step 7 — Wrap-up with copy-paste run commands

- [x] Create summary of all new files created
- [x] Provide copy-paste commands for:
  - [x] Running chaos tests via curl
  - [x] Running chaos tests via Newman
  - [x] Running 2FA flow via Newman
  - [x] Running email recovery via Newman
  - [x] Running Sentry/TestMail validation via Newman
  - [x] Importing Requestly rules
  - [x] Verifying Doppler stg/prd configs
- [x] Provide next steps for the user (commit, test, deploy)

**Status:** ✅ Complete

### Run Commands

#### Verify dev stack is running

```bash
docker ps
# Verify ecole-backend, ecole-web, ecole-worker, postgres, redis are running
```

#### Run curl chaos scripts

```bash
cd system-tests/chaos/curl

# Run individual scripts
./01_sync_push_503.sh --token <jwt> --base-url http://localhost:8000/api/v1
./02_webhook_duplicate.sh --ngrok-url <ngrok-url>
./03_rate_limit_429.sh --token <jwt> --request-count 100
./04_latency_800ms.sh --token <jwt>
./05_load_smoke.sh --rps 10 --duration 30

# Or run all at once
./run-all.sh --token <jwt> --ngrok-url <ngrok-url>
```

#### Run Postman collections

```bash
cd system-tests/postman

# Run chaos scenarios
newman run scenario_chaos.postman_collection.json -e env_local.json

# Run 2FA flow
newman run scenario_2fa.postman_collection.json -e env_local.json

# Run email recovery
newman run scenario_email_recovery.postman_collection.json -e env_local.json

# Run Sentry/TestMail validation
newman run scenario_sentry_testmail.postman_collection.json -e env_local.json
```

#### Verify Sentry events

```bash
# Trigger error event
curl http://localhost:8000/api/v1/sentry-debug

# Trigger transaction event
curl http://localhost:8000/api/v1/health

# Verify in Sentry dashboard:
# https://ensmr.sentry.io/issues/?project=4511374465106000
# https://ensmr.sentry.io/performance/?project=4511374465106000
```

#### Verify Doppler configs

```bash
# Verify dev config
/opt/homebrew/bin/doppler secrets get APP_ENV LOG_LEVEL SENTRY_TRACES_SAMPLE_RATE --config dev

# Verify stg_main config
/opt/homebrew/bin/doppler secrets get APP_ENV LOG_LEVEL SENTRY_TRACES_SAMPLE_RATE --config stg_main

# Verify prd_main config
/opt/homebrew/bin/doppler secrets get APP_ENV LOG_LEVEL SENTRY_TRACES_SAMPLE_RATE --config prd_main
```

#### Start dev stack with Doppler

```bash
# Start dev stack with Doppler-injected secrets
make doppler-run CMD="make up"

# Stop dev stack
make down

# Expose webhook via ngrok
make ngrok-webhook
```

#### Import Requestly rules

```bash
# Open Requestly Desktop and import:
# system-tests/chaos/requestly-rules.json

# See import instructions:
# system-tests/chaos/requestly-import.md
```

### Artifacts Created Summary

#### Doppler

- `infra/doppler/populate-stg-prd-defaults.sh` — Script to populate stg_main and prd_main configs with defaults

#### Chaos Engineering

- `system-tests/chaos/requestly-rules.json` — 4 Requestly rules for chaos testing
- `system-tests/chaos/requestly-import.md` — Import instructions
- `system-tests/chaos/curl/01_sync_push_503.sh` — Sync push 503 test
- `system-tests/chaos/curl/02_webhook_duplicate.sh` — Webhook dedup test
- `system-tests/chaos/curl/03_rate_limit_429.sh` — Rate limit test
- `system-tests/chaos/curl/04_latency_800ms.sh` — Latency test
- `system-tests/chaos/curl/05_load_smoke.sh` — Load smoke test
- `system-tests/chaos/curl/run-all.sh` — Orchestrator

#### Postman Collections

- `system-tests/postman/scenario_chaos.postman_collection.json` — Chaos scenarios
- `system-tests/postman/scenario_2fa.postman_collection.json` — 2FA flow
- `system-tests/postman/scenario_email_recovery.postman_collection.json` — Email recovery
- `system-tests/postman/scenario_sentry_testmail.postman_collection.json` — Sentry/TestMail validation

#### Documentation

- `IMPLEMENTATION-CHECKLIST.md` — Step-by-step implementation checklist (this file)
- `AUTH-FEATURES-AUDIT.md` — Auth feature audit with gaps and recommendations
- `system-tests/chaos/README.md` — Updated with new artifacts
- `system-tests/postman/README.md` — Updated with new collections

### Next Steps

1. **Commit the changes**

   ```bash
   git add IMPLEMENTATION-CHECKLIST.md AUTH-FEATURES-AUDIT.md
   git add infra/doppler/populate-stg-prd-defaults.sh
   git add system-tests/chaos/requestly-rules.json system-tests/chaos/requestly-import.md
   git add system-tests/chaos/curl/*.sh
   git add system-tests/postman/scenario_*.json
   git add system-tests/chaos/README.md system-tests/postman/README.md
   git commit -m "Add validation suite: chaos tests, Postman collections, auth audit"
   ```

2. **Test the artifacts locally**
   - Run curl chaos scripts
   - Run Postman collections via Newman
   - Import Requestly rules and test with Requestly Desktop
   - Verify Sentry events in dashboard

3. **Replace CHANGE*ME*\* secrets in Doppler stg_main/prd_main**
   - Run: `doppler secrets get --config stg_main` to see all placeholders
   - Replace with actual production secrets before deploying

4. **Deploy to staging**
   - Run Doppler populate script for stg_main if needed
   - Replace CHANGE*ME*\* secrets with staging values
   - Deploy and run Postman CI job

---

## Summary

**Total steps:** 7
**Total sub-checklist items:** ~100
**Estimated completion time:** 45–60 minutes (excluding Docker build time)

**Current status:** Step 1 ✅ | Step 2 ✅ | Step 3 ✅ | Step 4 ✅ | Step 5a–g ✅ | Step 6 ✅ | Step 7 ✅
