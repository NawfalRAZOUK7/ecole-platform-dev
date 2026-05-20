# Chaos Testing Guide

This guide explains how to use chaos engineering tests for the École Platform to validate system resilience under failure conditions.

## Table of Contents

- [What is Chaos Testing?](#what-is-chaos-testing)
- [Choosing Your Testing Tool](#choosing-your-testing-tool)
- [Available Chaos Scenarios](#available-chaos-scenarios)
- [Using Requestly](#using-requestly)
- [Using Curl Scripts](#using-curl-scripts)
- [Using Postman Collections](#using-postman-collections)
- [Interpreting Results](#interpreting-results)
- [Tuning Chaos Parameters](#tuning-chaos-parameters)
- [Common Failure Modes](#common-failure-modes)

## What is Chaos Testing?

Chaos testing (or chaos engineering) is the practice of intentionally introducing failures into a system to test its resilience. By simulating real-world failure scenarios, you can:

- Validate graceful error handling
- Test offline-first behavior
- Verify fallback mechanisms
- Identify single points of failure
- Ensure the system degrades gracefully under stress

## Choosing Your Testing Tool

We provide three ways to run chaos tests, each suited for different scenarios:

### Requestly (Recommended for Manual Testing)

**When to use:**
- Interactive testing in the browser
- Testing frontend behavior under failures
- Quick ad-hoc testing
- Visual debugging

**Pros:**
- Easy to enable/disable rules
- Works with real browser traffic
- No code changes needed
- Good for UI testing

**Cons:**
- Requires Requestly Desktop app
- Not suitable for automated CI/CD
- Manual setup required

### Curl Scripts (Recommended for Automation)

**When to use:**
- Automated testing in CI/CD
- Backend-only testing
- Scripted test scenarios
- Integration with shell scripts

**Pros:**
- Fully automated
- Easy to integrate into CI/CD
- No external dependencies
- Scriptable and repeatable

**Cons:**
- Requires backend to be running
- Less visual feedback
- Need to manage authentication tokens

### Postman Collections (Recommended for API Testing)

**When to use:**
- API contract testing
- Integration with other API tests
- Detailed assertions
- Test reporting

**Pros:**
- Rich assertion capabilities
- Integrated with other API tests
- Detailed test reports
- Easy to share with team

**Cons:**
- Requires Newman CLI
- More complex setup
- Limited to HTTP-level failures

## Available Chaos Scenarios

### 1. Sync Push 503 (Offline-First Validation)

**Purpose:** Test offline-first behavior when sync push returns 503

**What it tests:**
- App handles server unavailability
- Data is queued locally for retry
- User sees appropriate offline indicators
- Sync resumes when server is available

**Tools:** Requestly, curl, Postman

### 2. Webhook Duplicate (Idempotency)

**Purpose:** Test webhook deduplication under load

**What it tests:**
- Duplicate webhook requests are handled correctly
- Idempotency keys prevent double processing
- System returns consistent responses

**Tools:** Requestly, curl, Postman

### 3. Rate Limit 429 (Client Retry Behavior)

**Purpose:** Test client handling of rate limiting

**What it tests:**
- Client respects retry-after headers
- User sees appropriate rate limit messages
- Backoff strategy is implemented

**Tools:** Requestly, curl, Postman

### 4. Latency 800ms (UI Loader Tolerance)

**Purpose:** Test UI behavior under slow API responses

**What it tests:**
- UI shows loading indicators
- No timeout errors occur
- User experience remains acceptable

**Tools:** Requestly, curl, Postman

### 5. Database Failure 503 (Graceful Degradation)

**Purpose:** Test behavior when database is unreachable

**What it tests:**
- App shows error messages
- No crashes or infinite loading
- Fallback UI is displayed
- Error logging is working

**Tools:** Requestly, curl, Postman

### 6. Redis Failure 503 (Cache Fallback)

**Purpose:** Test behavior when Redis/cache is unavailable

**What it tests:**
- App falls back to database queries
- Session management still works
- Performance degrades gracefully
- Cache misses are handled

**Tools:** Requestly, curl, Postman

### 7. Slow Query 5s (Timeout Handling)

**Purpose:** Test behavior with slow database queries

**What it tests:**
- UI shows loading for extended period
- Timeout handling is graceful
- No zombie requests
- User can cancel operations

**Tools:** Requestly, curl, Postman

### 8. Load Smoke (System Stability)

**Purpose:** Test system stability under load

**What it tests:**
- System handles concurrent requests
- Success rate remains acceptable
- No memory leaks
- Performance degrades gracefully

**Tools:** curl, Postman

## Using Requestly

### Installation

1. Download Requestly Desktop from https://requestly.com/desktop
2. Install and launch the application
3. Navigate to the HTTP Rules tab

### Importing Rules

1. Click "Import" or drag-and-drop `system-tests/chaos/requestly-rules.json`
2. Review the imported rules
3. Enable the rules you want to test

### Testing with Requestly

#### Sync Push 503 (Offline-First Validation)

1. Enable "Chaos: Sync Push 503"
2. In the web app, trigger a sync push (e.g., submit a form)
3. Verify the app shows an offline indicator / retries locally
4. Disable the rule, sync should resume

#### Latency 800ms (UI Loader Tolerance)

1. Enable "Chaos: Sync API Delay 800ms"
2. Trigger a sync pull in the app
3. Verify the UI shows a loader for at least 800ms
4. Verify no timeout error occurs

#### Rate Limit 429 (Client Retry Behavior)

1. Enable "Chaos: Rate Limit 429"
2. Fire multiple rapid requests (e.g., refresh the page 10 times)
3. Verify the client shows a "rate limited" message
4. Verify retry-after logic is respected

#### Database Failure 503 (Graceful Degradation)

1. Enable "Chaos: Database Failure 503"
2. Navigate to a page that loads students/teachers/classes
3. Verify the app shows an error message or fallback UI
4. Verify no crash or infinite loading state

#### Redis Failure 503 (Cache Fallback)

1. Enable "Chaos: Redis Failure 503"
2. Navigate to sessions page or perform session-dependent action
3. Verify the app falls back to DB or shows appropriate error
4. Verify session management still works (if fallback implemented)

#### Slow Query Delay 5s (Timeout Handling)

1. Enable "Chaos: Slow Query Delay 5s"
2. Navigate to a page that loads students/teachers/classes
3. Verify the UI shows a loader for at least 5s
4. Verify no timeout error occurs (or timeout is handled gracefully)

## Using Curl Scripts

### Prerequisites

- Backend services running
- Valid JWT authentication token

### Running Scripts

```bash
# Sync Push 503
cd system-tests/chaos/curl
./01_sync_push_503.sh --token YOUR_JWT_TOKEN

# Webhook Duplicate
./02_webhook_duplicate.sh --token YOUR_JWT_TOKEN

# Rate Limit 429
./03_rate_limit_429.sh --token YOUR_JWT_TOKEN

# Latency 800ms
./04_latency_800ms.sh --token YOUR_JWT_TOKEN

# Load Smoke
./05_load_smoke.sh

# Database Failure
./06_db_connection_failure.sh --token YOUR_JWT_TOKEN

# Redis Failure
./07_redis_connection_failure.sh --token YOUR_JWT_TOKEN

# Slow Query
./08_slow_query.sh --token YOUR_JWT_TOKEN
```

### Running All Scripts

```bash
./run-all.sh --token YOUR_JWT_TOKEN
```

## Using Postman Collections

### Running Chaos Tests

```bash
npx newman run system-tests/postman/scenario_chaos.postman_collection.json \
  -e system-tests/postman/env_scenarios.json
```

### Available Tests in Collection

- **Sync Push 503**: Tests offline-first behavior
- **Webhook Duplicate**: Tests idempotency
- **Rate Limit 429**: Tests client retry behavior
- **Latency 800ms**: Tests UI loader tolerance
- **Load Smoke**: Tests system stability
- **Database Failure 503**: Tests graceful degradation
- **Redis Failure 503**: Tests cache fallback
- **Slow Query 5s**: Tests timeout handling

## Interpreting Results

### Success Criteria

A chaos test is considered successful if:

1. **Expected Error Received**: The system returns the expected error code (e.g., 503, 429, 408)
2. **Graceful Degradation**: The system degrades gracefully rather than crashing
3. **User-Friendly Error**: Error messages are clear and actionable
4. **No Data Loss**: No data is lost during the failure
5. **Recovery**: The system recovers when the failure is resolved

### Failure Indicators

A chaos test fails if:

1. **Unexpected Status Code**: System returns 200 when it should return an error
2. **Application Crash**: The application crashes or becomes unresponsive
3. **Infinite Loading**: UI shows indefinite loading without timeout
4. **Data Corruption**: Data is corrupted or lost
5. **Cascading Failures**: One failure causes multiple downstream failures

### Example Results

**Passing Test:**
```
✅ PASS: Received 503 as expected (Requestly rule active)
✅ PASS: Error message is user-friendly
✅ PASS: Application remains responsive
```

**Failing Test:**
```
❌ FAIL: Received 200 when 503 expected (Requestly rule not active)
❌ FAIL: Application crashed with unhandled exception
❌ FAIL: Infinite loading without timeout
```

## Tuning Chaos Parameters

### Adjusting Latency

In Requestly, modify the delay value:
- **UI Testing**: 500ms - 2000ms (typical network latency)
- **Database Testing**: 2000ms - 10000ms (slow queries)
- **Stress Testing**: >10000ms (extreme conditions)

### Adjusting Rate Limits

In `requestly-rules.json`, modify the rate limit threshold:
- **Normal Load**: 10-50 requests per second
- **Peak Load**: 50-100 requests per second
- **Stress Load**: 100-500 requests per second

### Adjusting Failure Duration

For curl scripts, you can add sleep commands to simulate extended failures:

```bash
# Simulate 30-second database outage
docker stop ecole-postgres
sleep 30
docker start ecole-postgres
```

## Common Failure Modes

### 1. Network Timeout

**Symptoms:** Requests hang indefinitely, no response

**What to test:**
- Client timeout configuration
- Retry logic with exponential backoff
- Circuit breaker pattern

**Chaos Scenario:** Latency 800ms, Slow Query 5s

### 2. Service Unavailable

**Symptoms:** 503 Service Unavailable errors

**What to test:**
- Graceful error messages
- Offline queueing
- Service discovery fallback

**Chaos Scenario:** Sync Push 503, Database Failure 503, Redis Failure 503

### 3. Rate Limiting

**Symptoms:** 429 Too Many Requests errors

**What to test:**
- Client respects retry-after header
- User feedback for rate limits
- Backoff strategy

**Chaos Scenario:** Rate Limit 429

### 4. Data Consistency

**Symptoms:** Duplicate records, inconsistent state

**What to test:**
- Idempotency keys
- Transaction rollback
- Duplicate detection

**Chaos Scenario:** Webhook Duplicate

### 5. Performance Degradation

**Symptoms:** Slow responses, high latency

**What to test:**
- Caching effectiveness
- Database query optimization
- CDN usage

**Chaos Scenario:** Latency 800ms, Slow Query 5s, Load Smoke

## Best Practices

1. **Start Small:** Begin with simple latency tests before moving to service failures
2. **Monitor Logs:** Always check backend logs during chaos tests
3. **Test Recovery:** Verify the system recovers when the chaos is removed
4. **Document Findings:** Record what breaks and how it's fixed
5. **Run Regularly:** Incorporate chaos tests into your regular testing schedule
6. **Gradual Increase:** Slowly increase chaos severity as system resilience improves
7. **Test in Production:** Consider using feature flags to test in production with canary releases

## See Also

- `requestly-import.md` - How to import Requestly rules
- `requestly-rules.json` - Pre-configured Requestly rules
- `curl/` - Standalone curl scripts for chaos scenarios
- `../postman/scenario_chaos.postman_collection.json` - Postman chaos collection
