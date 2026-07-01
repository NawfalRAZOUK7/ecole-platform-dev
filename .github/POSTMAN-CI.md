# Postman CI Integration Guide

This guide explains how Postman scenario tests are integrated into the CI/CD pipeline and how to debug CI failures.

## Table of Contents

- [CI Pipeline Overview](#ci-pipeline-overview)
- [How Scenario Tests Run in CI](#how-scenario-tests-run-in-ci)
- [CI Environment Configuration](#ci-environment-configuration)
- [Debugging CI Failures](#debugging-ci-failures)
- [Skipping Specific Tests](#skipping-specific-tests)
- [Test Artifacts](#test-artifacts)
- [Local Reproduction](#local-reproduction)

## CI Pipeline Overview

The CI pipeline runs Postman scenario tests in the `postman-scenario-tests` job, which is part of the overall CI workflow.

### Pipeline Structure

```
lint → security-trivy → security-pip-audit → security-bandit → migration-safety → unit-tests → integration-tests → contract-tests → security-tests → e2e-tests → postman-tests → postman-scenario-tests → cleanup-test-data → k6-load-tests → security-audit → coverage-report
```

### Postman Scenario Tests Job

The `postman-scenario-tests` job:
- Runs after `integration-tests` (requires database and services)
- Uses PostgreSQL and Redis services
- Seeds test data before running tests
- Starts the API server on port 8000
- Runs Newman CLI with scenario collections
- Uploads test reports as artifacts
- Runs cleanup job after completion (always runs, even on failure)

## How Scenario Tests Run in CI

### Step-by-Step Process

1. **Checkout Code**: Clone the repository
2. **Set Up Python**: Install Python 3.12
3. **Install Dependencies**: Install backend dependencies
4. **Run Migrations**: Apply database migrations
5. **Seed Test Data**: Populate database with test users
6. **Start API Server**: Start Uvicorn server on port 8000
7. **Install Newman**: Install Newman CLI and reporter
8. **Run Scenario Collections**: Execute scenario tests with Newman
9. **Upload Reports**: Save test reports as artifacts

### Scenario Collections Run

The CI runs the following scenario collections:

```bash
# 2FA scenario
newman run system-tests/postman/scenario_2fa.postman_collection.json \
  -e system-tests/postman/env_local.json \
  --env-var "base_url=http://localhost:8000/api/v1" \
  --reporters cli,htmlextra,json \
  --bail || true

# Email recovery scenario
newman run system-tests/postman/scenario_email_recovery.postman_collection.json \
  -e system-tests/postman/env_local.json \
  --env-var "base_url=http://localhost:8000/api/v1" \
  --reporters cli,htmlextra,json \
  --bail || true

# Chaos scenario
newman run system-tests/postman/scenario_chaos.postman_collection.json \
  -e system-tests/postman/env_local.json \
  --env-var "base_url=http://localhost:8000/api/v1" \
  --reporters cli,htmlextra,json \
  --bail || true
```

**Note:** The `|| true` at the end ensures the CI continues even if a scenario test fails. This allows all scenarios to run and generate reports.

## CI Environment Configuration

### Environment Variables

The CI job sets the following environment variables:

```yaml
env:
  DATABASE_URL: postgresql+asyncpg://ecole:ecole@localhost:5432/ecole_platform
  REDIS_URL: redis://localhost:6379/0
  JWT_SECRET_KEY: test-secret-key-ci-only
  JWT_ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  REFRESH_TOKEN_DAYS: "7"
  APP_ENV: test
```

### Test Environment File

The CI uses `system-tests/postman/env_local.json` for environment configuration. This file should be committed to the repository and contains CI-specific test credentials.

**Important:** Do NOT commit secrets to `env_local.json`. Use environment-specific secrets for sensitive data.

### Services

The CI job uses the following services:

- **PostgreSQL 16-alpine**: Database for test data
- **Redis 7-alpine**: Cache and session storage

Services are started with health checks to ensure they're ready before tests run.

## Debugging CI Failures

### Step 1: Check Test Reports

Download the test artifacts from the failed CI run:

1. Go to the failed workflow run in GitHub Actions
2. Scroll to the "Upload scenario test reports" step
3. Download the HTML reports:
   - `scenario-2fa-report.html`
   - `scenario-email-recovery-report.html`
   - `scenario-chaos-report.html`
4. Open the HTML reports in your browser to see detailed test results

### Step 2: Check CI Logs

Review the CI logs for the failed scenario:

1. Go to the "Run scenario_2fa collection" step (or other failed scenario)
2. Look for error messages in the console output
3. Check for:
   - HTTP status codes (401, 404, 500, etc.)
   - Timeout errors
   - Connection refused errors
   - JSON parsing errors

### Step 3: Reproduce Locally

Reproduce the failure locally using the same environment:

```bash
# Start services
make up

# Run the specific scenario
npx newman run system-tests/postman/scenario_2fa.postman_collection.json \
  -e system-tests/postman/env_local.json \
  --env-var "base_url=http://localhost:8000/api/v1"
```

### Step 4: Check Backend Logs

If the test fails due to backend errors, check the backend logs:

```bash
docker logs ecole-backend
```

Look for:
- Exception stack traces
- Database connection errors
- Redis connection errors
- Validation errors

### Common CI Failures

#### Issue: "Connection refused" to API server

**Cause:** API server failed to start or crashed

**Solution:** Check the "Start API server" step in CI logs. Ensure the server starts within the 30-second timeout.

#### Issue: "401 Unauthorized" on login

**Cause:** Test credentials are incorrect or test data not seeded

**Solution:** Verify `env_local.json` has correct credentials. Check that database seeding succeeded.

#### Issue: "Invalid OTP" in email recovery test

**Cause:** OTP not returned in response (APP_ENV not set to test/development)

**Solution:** Ensure `APP_ENV=test` is set in the CI environment. The backend should return OTP in the response for testing.

#### Issue: "Rate limit exceeded"

**Cause:** Too many requests in quick succession

**Solution:** The CI runs tests sequentially, so this shouldn't happen. If it does, check for stuck rate limit keys in Redis.

#### Issue: Test timeout

**Cause:** Request took too long to complete

**Solution:** Check if the API server is responding slowly. Look for slow queries or network issues.

## Skipping Specific Tests

### Skipping a Scenario Collection

To skip a specific scenario collection temporarily, comment it out in the CI workflow:

```yaml
- name: Run scenario_2fa collection
  run: |
    # newman run system-tests/postman/scenario_2fa.postman_collection.json \
    #   -e system-tests/postman/env_local.json \
    #   --env-var "base_url=http://localhost:8000/api/v1" \
    #   --reporters cli,htmlextra,json \
    #   --reporter-htmlextra-export scenario-2fa-report.html \
    #   --reporter-json-export scenario-2fa-report.json \
    #   --bail || true
  echo "Skipping 2FA scenario test"
```

### Skipping a Specific Test in Postman

To skip a specific test within a collection, add a skip condition:

```javascript
pm.test("Test name", function () {
    if (pm.environment.get("SKIP_THIS_TEST") === "true") {
        console.log("Test skipped via environment variable");
        return;
    }
    // Your test logic here
});
```

Then set the environment variable in CI:

```yaml
- name: Run scenario_2fa collection
  env:
    SKIP_THIS_TEST: "true"
  run: |
    newman run system-tests/postman/scenario_2fa.postman_collection.json \
      -e system-tests/postman/env_local.json \
      --env-var "SKIP_THIS_TEST=true"
```

## Test Artifacts

### Available Artifacts

After each CI run, the following artifacts are uploaded:

- `scenario-2fa-report.html`: HTML report for 2FA scenario
- `scenario-2fa-report.json`: JSON report for 2FA scenario
- `scenario-email-recovery-report.html`: HTML report for email recovery scenario
- `scenario-email-recovery-report.json`: JSON report for 2FA scenario
- `scenario-chaos-report.html`: HTML report for chaos scenario
- `scenario-chaos-report.json`: JSON report for chaos scenario

### Accessing Artifacts

1. Go to the GitHub Actions workflow run
2. Scroll to the bottom of the page
3. Click on "Artifacts" section
4. Download the desired artifact

### Artifact Retention

Artifacts are retained for 30 days by default. You can change this in the workflow configuration:

```yaml
- name: Upload scenario test reports
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: scenario-reports
    retention-days: 90
    path: |
      scenario-2fa-report.html
      scenario-2fa-report.json
      scenario-email-recovery-report.html
      scenario-email-recovery-report.json
      scenario-chaos-report.html
      scenario-chaos-report.json
```

## Local Reproduction

### Reproducing CI Environment Locally

To reproduce the exact CI environment locally:

```bash
# Start services with CI-like configuration
docker compose -f infra/docker-compose.dev.yml up -d postgres redis

# Set CI environment variables
export DATABASE_URL=postgresql+asyncpg://ecole:ecole@localhost:5432/ecole_platform
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=test-secret-key-ci-only
export JWT_ALGORITHM=HS256
export ACCESS_TOKEN_EXPIRE_MINUTES=30
export REFRESH_TOKEN_DAYS=7
export APP_ENV=test

# Run migrations
cd backend
alembic upgrade head

# Seed test data
python -m app.seed

# Start API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Wait for server to start
for i in $(seq 1 30); do
    curl -sf http://localhost:8000/api/v1/health && break
    sleep 1
done

# Run scenario tests
cd ..
npx newman run system-tests/postman/scenario_2fa.postman_collection.json \
  -e system-tests/postman/env_local.json \
  --env-var "base_url=http://localhost:8000/api/v1"
```

### Using the Test Runner Script

The `system-tests/run_tests.sh` script provides a convenient way to run tests locally:

```bash
# Run all scenario tests
system-tests/run_tests.sh --include-scenarios

# Run a specific scenario
system-tests/run_tests.sh --include-scenarios --scenario email_recovery

# Run with development database
system-tests/run_tests.sh --include-scenarios --allow-dev-db
```

## Cleanup Job

The CI pipeline includes a `cleanup-test-data` job that runs after scenario tests:

- **Purpose**: Clean up test data to prevent pollution
- **Runs**: Always, even if scenario tests fail (`if: always()`)
- **What it does**:
  - Deletes test users with email prefix `test.`
  - Deletes test invitation codes
  - Revokes test sessions
- **When it runs**: After `postman-scenario-tests` completes

### Cleanup Script

The cleanup uses the `tests/cleanup_test_data.sh` script:

```bash
./tests/cleanup_test_data.sh \
  --token ADMIN_TOKEN \
  --base-url http://localhost:8000/api/v1 \
  --school-id 00000000-0000-4000-8000-000000000001
```

### Dry Run Mode

To test cleanup without actually deleting data:

```bash
./tests/cleanup_test_data.sh \
  --token ADMIN_TOKEN \
  --base-url http://localhost:8000/api/v1 \
  --school-id 00000000-0000-4000-8000-000000000001 \
  --dry-run
```

## Best Practices

### 1. Keep Tests Independent

Each scenario collection should be independent and not rely on state from other tests. This allows tests to run in any order and makes debugging easier.

### 2. Use Environment Variables

Use environment variables for configuration rather than hardcoding values in collections. This makes it easy to test against different environments.

### 3. Clean Up After Tests

Always include cleanup steps to remove test data. This prevents test pollution and ensures reproducible results.

### 4. Monitor Test Duration

If tests become too slow, consider:
- Adding timeouts to requests
- Parallelizing independent tests
- Optimizing database queries
- Using test databases with less data

### 5. Review Test Reports Regularly

Regularly review test reports to identify:
- Flaky tests (tests that intermittently fail)
- Performance regressions
- New failing tests
- Tests that are no longer relevant

## See Also

- `../../system-tests/postman/SCENARIO-SETUP.md` - Scenario test setup guide
- `../../system-tests/postman/README.md` - Postman collection documentation
- `../../tests/cleanup_test_data.sh` - Cleanup script
- `.github/workflows/ci.yml` - CI workflow configuration
