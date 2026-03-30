# Top-Level Integration & E2E Tests

Manual API testing collections and load test scripts. Complements automated pytest suite with human-driven testing and realistic usage pattern validation.

## Overview

- **Approach**: Postman collections for API exploration, k6 scripts for load simulation
- **Audience**: QA testers, developers, performance engineers
- **Execution**: Manual via Postman UI or automated via CLI/CI
- **Data**: Uses live backend with test database fixtures

## Test Files

### Postman Collections
Organized by feature phase, each collection contains request sequences with assertions.

| Collection | Endpoints | Coverage | Last Updated |
|------------|-----------|----------|--------------|
| **postman_collection_phase12.json** | 28 requests | School, Classes, Staff (28,232 bytes) | Mar 27 |
| **postman_collection_phase13.json** | 12 requests | Notifications, Messages (12,551 bytes) | Mar 27 |
| **postman_collection_phase14.json** | 10 requests | Reports, Analytics (10,953 bytes) | Mar 27 |
| **postman_collection_phase15.json** | 9 requests | Calendar, Events (9,677 bytes) | Mar 27 |
| **postman_collection_phase16.json** | 6 requests | Documents, File Upload (6,030 bytes) | Mar 27 |

**Total**: 65 manual test requests across 5 phases

**How to Use:**

1. **Import into Postman**
   - Open Postman
   - File → Import → Select .json collection
   - Click "Import"

2. **Set Environment Variables**
   - Base URL: `http://localhost:8000/api`
   - Auth Token: Obtain via POST `/auth/login`
   - School ID: Copy from collection variable
   - Class ID: Copy from collection variable

3. **Run Collection**
   - Click collection name
   - Runner → Start Test
   - Monitor responses and assertions

4. **View Results**
   - Test Summary: Pass/Fail count
   - Failures: Detailed assertion messages
   - Response Times: Compare to SLA targets

**Example Test Request:**
```json
{
  "name": "Create School",
  "request": {
    "method": "POST",
    "url": "{{base_url}}/schools",
    "body": {
      "name": "Lycée Test {{$timestamp}}",
      "phone": "+212612345678"
    }
  },
  "tests": {
    "Status is 201": "pm.response.code === 201",
    "Response has school_id": "pm.response.json().id",
    "Name matches request": "pm.response.json().name === pm.request.body.raw.name"
  }
}
```

### run_tests.sh - Test Execution Script
Bash script to run Postman collections via CLI.

**Usage:**
```bash
./run_tests.sh                    # Run all phases
./run_tests.sh phase12            # Run specific phase
./run_tests.sh phase13 --verbose  # Verbose output
```

**Script Features:**
- Sequential test execution
- Automatic environment setup
- JSON test report generation
- Failure summaries
- Performance metrics

**Output:**
```
Running tests/postman_collection_phase12.json...
✓ Create School (201ms)
✓ Get School (45ms)
✓ Update School (78ms)
✓ Create Class (120ms)
...
PASSED: 24/28
FAILED: 4/28
```

## Load Test Scripts

**Path**: `tests/load/`

k6-based load testing for performance validation and stress testing.

### Shared Configuration
- **config.js** - Common settings, environment, timing constants
  - Base URL configuration
  - Ramp-up/down profiles
  - Timeout settings
  - Data generators

**Example config.js:**
```javascript
export const options = {
  stages: [
    { duration: "30s", target: 20 },  // Ramp up to 20 users
    { duration: "1m30s", target: 20 }, // Stay at 20 for 1.5min
    { duration: "20s", target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<200"],  // 95th percentile < 200ms
    http_req_failed: ["rate<0.1"],     // Error rate < 10%
  },
};
```

### Scenario 1: Logins
- **File**: `scenario1_logins.js` (2,124 bytes)
- **Pattern**: Concurrent user authentication
- **Users**: 20 concurrent students logging in
- **Duration**: 2 minutes
- **Target SLA**: <200ms per login
- **Metrics**: Auth success rate, token generation time

**Test Sequence:**
1. POST `/auth/login` (email, password)
2. Verify JWT token in response
3. Store token for next scenario

### Scenario 2: GET Requests
- **File**: `scenario2_get_requests.js` (1,934 bytes)
- **Pattern**: Typical user browsing (read-heavy)
- **Requests**:
  - GET /schools (list)
  - GET /schools/{id} (details)
  - GET /classes (teacher's classes)
  - GET /grades (student's grades)
  - GET /announcements (school-wide)
- **Users**: 50 concurrent
- **Duration**: 2 minutes
- **Target SLA**: <100ms per GET

### Scenario 3: File Uploads
- **File**: `scenario3_file_uploads.js` (2,170 bytes)
- **Pattern**: Document upload workflow
- **Files**:
  - PDF (1MB typical)
  - DOCX (500KB typical)
  - Image (2MB typical)
- **Users**: 10 concurrent upload sessions
- **Duration**: 1 minute per file type
- **Target SLA**: <1000ms per upload (network bound)

**Upload Test:**
```javascript
import http from "k6/http";
import { check } from "k6";

export default function () {
  const file = open("sample.pdf", "b");
  const response = http.post(
    `${BASE_URL}/documents/upload`,
    { file: http.file(file, "document.pdf") },
    { headers: { Authorization: `Bearer ${TOKEN}` } }
  );

  check(response, {
    "Upload successful": (r) => r.status === 201,
    "Upload time < 2s": (r) => r.timings.duration < 2000,
  });
}
```

### Scenario 4: WebSocket
- **File**: `scenario4_websocket.js` (2,006 bytes)
- **Pattern**: Real-time communication (notifications, live updates)
- **Operations**:
  - Connect WebSocket
  - Send/receive messages
  - Handle disconnection/reconnection
- **Users**: 20 concurrent WebSocket connections
- **Duration**: 3 minutes (sustained connection)
- **Target Metrics**:
  - Connection time < 500ms
  - Message round-trip < 100ms
  - 99.5% uptime (max 1 disconnection)

**WebSocket Test:**
```javascript
import ws from "k6/ws";
import { check } from "k6";

export default function () {
  const url = "ws://localhost:8000/ws/notifications";
  const res = ws.connect(url, null, function (socket) {
    socket.on("open", function () {
      console.log("Connected");
    });

    socket.on("message", function (data) {
      check(data, {
        "Message received": (m) => m.length > 0,
      });
    });

    socket.on("close", function () {
      console.log("Disconnected");
    });
  });

  check(res, {
    "Connection successful": (r) => r.status === 101,
  });
}
```

## Running Load Tests

### Prerequisites
```bash
# Install k6
npm install -g k6
# or
brew install k6  # macOS
```

### Run Individual Scenario
```bash
# Run scenario 1 (logins)
k6 run tests/load/scenario1_logins.js

# Run with environment variables
k6 run -e BASE_URL=http://localhost:8000/api tests/load/scenario1_logins.js

# Run with output to cloud
k6 run -o cloud tests/load/scenario1_logins.js
```

### Run All Scenarios
```bash
# Sequential scenarios
k6 run tests/load/scenario1_logins.js
k6 run tests/load/scenario2_get_requests.js
k6 run tests/load/scenario3_file_uploads.js
k6 run tests/load/scenario4_websocket.js
```

### Generate Report
```bash
# HTML report
k6 run --out csv=results.csv tests/load/scenario1_logins.js

# View metrics
k6 stats results.csv
```

## Expected Test Results

### Phase Coverage
- **Phase 12**: School & organizational setup (28 requests)
- **Phase 13**: Communication system (12 requests)
- **Phase 14**: Reporting & analytics (10 requests)
- **Phase 15**: Calendar & scheduling (9 requests)
- **Phase 16**: Document management (6 requests)

### Load Test Targets
- **Scenario 1** (logins): 20 users, all succeed, <200ms
- **Scenario 2** (reads): 50 users, error rate <1%, <100ms p95
- **Scenario 3** (uploads): 10 concurrent, <2s per file
- **Scenario 4** (WebSocket): 20 connections, 99.5% uptime

## Integration with CI/CD

```yaml
# .github/workflows/test.yml
- name: Run Postman Tests
  run: ./tests/run_tests.sh

- name: Run Load Tests
  run: k6 run tests/load/scenario1_logins.js --out cloud
```

## Test Data Management

- **Fixtures**: Pre-populated schools and users in test database
- **Cleanup**: Automatic between test runs via conftest teardown
- **Isolation**: Each test run uses fresh database state

## Performance Baselines

| Scenario | Metric | Baseline | Status |
|----------|--------|----------|--------|
| Login | p95 | 185ms | PASS |
| GET List | p95 | 78ms | PASS |
| GET Detail | p95 | 45ms | PASS |
| File Upload | p95 | 1200ms | PASS |
| WebSocket | Connection | 350ms | PASS |

## Common Issues & Troubleshooting

**Issue**: Postman tests fail with 401 Unauthorized
**Solution**: Verify auth token is valid and not expired. Re-login to get fresh token.

**Issue**: k6 load test shows connection refused
**Solution**: Ensure backend server is running on configured port. Check BASE_URL environment variable.

**Issue**: File upload tests timeout
**Solution**: Network I/O is slow. Increase timeout threshold or reduce file size for initial testing.

## Related Documentation

- Backend Unit Tests: `backend/tests/README.md`
- Integration Tests: `backend/tests/integration/README.md`
- Performance Tests: `backend/tests/performance/README.md`
- OpenAPI Spec: `backend/docs/openapi.yaml`
- k6 Documentation: https://k6.io/docs/
- Postman Documentation: https://www.postman.com/resources/postman-guide/
