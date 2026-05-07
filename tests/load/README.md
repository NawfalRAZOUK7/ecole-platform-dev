# Load Testing Scripts

k6 load testing framework for realistic usage pattern simulation. Tests validate system performance under concurrent user load and stress conditions.

## Overview

- **Framework**: k6 (Go-based load testing tool)
- **Scenarios**: 4 usage patterns (login, read, upload, WebSocket)
- **Users**: 10-50 concurrent users per scenario
- **Duration**: 2-3 minutes per scenario
- **Metrics**: Response time, error rate, throughput

## Installation

```bash
# macOS
brew install k6

# Linux (Ubuntu/Debian)
apt-get install k6

# Windows
choco install k6

# Docker
docker run -i grafana/k6 run -o cloud - < script.js
```

## Safety

k6 scenarios create sessions/login history and some scenarios perform writes.
Run them against the disposable API-test stack unless you intentionally want to
dirty the normal dev DB:

```bash
make api-test-up
CI=1 make test-load SCENARIO=scenario1_logins.js
make api-test-down
```

`BASE_URL=http://localhost:8000/api/v1` is refused by default. Use
`K6_ALLOW_DEV_DB=1` only for an intentional destructive dev run.

## File Structure

```
tests/load/
├── config.js                 # Shared configuration
├── scenario1_logins.js       # Authentication load test
├── scenario2_get_requests.js # Read-heavy operations
├── scenario3_file_uploads.js # File upload stress test
└── scenario4_websocket.js    # WebSocket real-time test
```

## Shared Configuration

### config.js
Central configuration imported by all scenarios.

**Key Settings:**
```javascript
export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000/api/v1";
// scenario4_websocket.js also accepts WS_URL, e.g. ws://localhost:8010/api/v1/ws

export const RAMP_UP = 30;     // 30s to ramp up
export const RAMP_DOWN = 20;   // 20s to ramp down
export const HOLD_TIME = 90;   // 90s at peak load

export const THRESHOLDS = {
  "http_req_duration": ["p(95)<200"],  // 95th percentile < 200ms
  "http_req_failed": ["rate<0.1"],     // Error rate < 10%
  "group_duration": ["p(95)<500"],     // Group operations < 500ms
};
```

**Usage:**
```javascript
import { BASE_URL, RAMP_UP, THRESHOLDS } from "./config.js";

export const options = {
  stages: [
    { duration: `${RAMP_UP}s`, target: 20 },
    { duration: `${HOLD_TIME}s`, target: 20 },
    { duration: `${RAMP_DOWN}s`, target: 0 },
  ],
  thresholds: THRESHOLDS,
};
```

## Scenario 1: Logins (scenario1_logins.js)

Authentication throughput and JWT token generation under load.

**Profile:**
- **Duration**: 2 minutes total
  - 30s ramp-up (0 → 20 users)
  - 90s hold (20 concurrent users)
  - 20s ramp-down (20 → 0 users)
- **Target**: 20 concurrent login attempts
- **SLA**: <200ms per login, <1% error rate

**User Flow:**
1. Rotate through seeded users from `tests/load/config.js`
2. POST `/auth/login` with email, password, and school ID
3. Verify JWT token received
4. Store token for subsequent requests

**Key Metrics:**
```
Requests:
  - Total: 120-150 (depends on ramp profile)
  - Success: >99 (3-4 allowed to fail)
  - Avg: ~100ms
  - p95: ~180ms
  - p99: ~200ms
```

**Example Output:**
```
http_req_duration..............: avg=145.2ms, p(95)=185.6ms, p(99)=200.1ms
http_requests..................: 145 in 2m
http_req_failed................: 1 in 145 (0.7%)
```

## Scenario 2: GET Requests (scenario2_get_requests.js)

Typical user browsing pattern with read-heavy operations.

**Profile:**
- **Duration**: 2 minutes total
- **Target**: 50 concurrent read operations
- **SLA**: <100ms per GET, <1% error rate

**Request Sequence:**
```javascript
// 1. List schools
GET /schools?limit=10

// 2. Get school details
GET /schools/{school_id}

// 3. List teacher's classes
GET /classes?teacher_id={teacher_id}

// 4. Get grades for student
GET /grades?student_id={student_id}

// 5. Get announcements
GET /announcements?school_id={school_id}

// Repeat sequence every 5-10 seconds
```

**Key Metrics:**
```
Total requests: 300+ (50 users × 5 requests)
Average response: <100ms
Error rate: <1%
Throughput: 150 req/min
```

**Example Output:**
```
http_req_duration..............: avg=78.3ms, p(95)=98.5ms, p(99)=115.2ms
http_requests..................: 312 in 2m
http_req_failed................: 1 in 312 (0.3%)
group_duration.................: avg=405.7ms
```

## Scenario 3: File Uploads (scenario3_file_uploads.js)

Document upload handling and network I/O performance.

**Profile:**
- **Duration**: 3 minutes (1 min × 3 file types)
- **Target**: 10 concurrent upload sessions
- **File Types**:
  - PDF: 1 MB (typical assignment)
  - DOCX: 500 KB (typical submission)
  - Image: 2 MB (typical scan)

**Upload Sequence:**
```javascript
// For each file type:
// Upload a valid PDF payload against the current document endpoint.
POST /documents/upload with { category, linked_student_id, file }

// Repeat with concurrent admin users against the disposable API-test stack.
```

**Key Metrics:**
```
PDF uploads: 10
  - Total time: 1 minute
  - Avg upload: 900ms
  - SLA: <2s

DOCX uploads: 10
  - Total time: 1 minute
  - Avg upload: 600ms
  - SLA: <1.5s

Image uploads: 10
  - Total time: 1 minute
  - Avg upload: 1500ms
  - SLA: <3s
```

**Network Expectations:**
- Upload speed depends on network bandwidth
- At 10 Mbps: 1 MB = ~1s
- Adjust user count based on network capacity

**Example Output:**
```
http_req_duration..............: avg=950.4ms, p(95)=1800.2ms
http_requests..................: 30 in 3m (PDF, DOCX, Image)
http_req_failed................: 0 in 30 (0%)
upload_success_rate............: 100%
```

## Scenario 4: WebSocket (scenario4_websocket.js)

Real-time communication with sustained connections.

**Profile:**
- **Duration**: 3 minutes
- **Target**: 20 concurrent WebSocket connections
- **Operations**: Connect, receive messages, handle reconnection
- **SLA**: <500ms connection, <100ms message round-trip

**Connection Flow:**
```javascript
// 1. Connect WebSocket
ws://localhost:8010/api/v1/ws/notifications?token={jwt}

// 2. Receive notification messages
  - School announcements
  - Grade publication
  - Assignment due reminders
  - Real-time updates

// 3. Handle disconnection
  - Graceful close
  - Automatic reconnection
  - Backoff retry

// 4. Sustained connection
  - Keep-alive pings every 30s
  - Receive ~5-10 messages per user
  - Hold connection 3 minutes
```

**Key Metrics:**
```
Connections: 20
  - Successful: 20 (100%)
  - Avg connection time: 350ms
  - p95 connection: 450ms

Messages received: ~150 (20 users × 7-8 messages)
  - Avg latency: 80ms
  - p95 latency: 95ms

Connection stability: 99.5% uptime
  - Reconnections: <1
  - Message loss: 0
```

**Example Output:**
```
ws_connecting..................: avg=345.2ms
ws_session_duration............: avg=179.8s
ws_messages_received............: 157
ws_messages_sent..............: 0
ws_ping_duration...............: avg=45.3ms
```

## Running Tests

### Individual Scenario
```bash
# Scenario 1: Logins
k6 run scenario1_logins.js

# Scenario 2: GET requests
k6 run scenario2_get_requests.js

# Scenario 3: File uploads
k6 run scenario3_file_uploads.js

# Scenario 4: WebSocket
k6 run scenario4_websocket.js
```

### Custom Parameters
```bash
# Set base URL
k6 run -e BASE_URL=http://staging.example.com/api scenario1_logins.js

# Set WebSocket URL
k6 run -e WS_URL=ws://staging.example.com/ws scenario4_websocket.js

# Set concurrent users (override ramp settings)
k6 run -o csv=results.csv scenario1_logins.js
```

### All Scenarios (Sequential)
```bash
#!/bin/bash
for scenario in scenario1_logins.js scenario2_get_requests.js scenario3_file_uploads.js scenario4_websocket.js; do
  echo "Running $scenario..."
  k6 run "$scenario"
  echo "---"
done
```

### Cloud Integration (Grafana Cloud)
```bash
# Authenticate (one-time)
k6 login cloud

# Run with cloud output
k6 run -o cloud scenario1_logins.js

# View results at https://app.k6.io/
```

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Login response | <200ms (p95) | ✓ PASS |
| GET request | <100ms (p95) | ✓ PASS |
| File upload | <2s (p95) | ✓ PASS |
| WebSocket connect | <500ms | ✓ PASS |
| Error rate | <1% | ✓ PASS |

## Test Data Setup

**Pre-requisites:**
1. Backend server running on configured BASE_URL
2. Test database with fixtures populated:
   - Seed users from `backend/app/seed.py`
   - 3+ test schools
   - 10+ test classes
   - Sample documents for upload tests

**Setup Script:**
```bash
# Populate test database
python -m backend.fixtures.populate_test_data

# Start backend
poetry run python -m backend.main
```

## Troubleshooting

**Issue**: "Connection refused" error
**Cause**: Backend not running on configured port
**Solution**: Start backend server first, verify BASE_URL

**Issue**: WebSocket "connection rejected" (scenario4)
**Cause**: Invalid JWT token or missing query parameter
**Solution**: Verify token format, check WebSocket URL syntax

**Issue**: File upload hangs (scenario3)
**Cause**: Network bandwidth saturation
**Solution**: Reduce concurrent users or increase timeout threshold

**Issue**: Threshold failures (high response times)
**Cause**: Slow database, under-provisioned infrastructure
**Solution**: Profile slow queries, increase server resources

## Continuous Monitoring

- **Before deployment**: Run all scenarios ✓
- **Regression**: Run against baseline metrics
- **Nightly**: Run extended scenarios (5+ minutes)
- **Post-deployment**: Verify no performance degradation

## Related Documentation

- Parent: `tests/README.md`
- Backend Tests: `backend/tests/README.md`
- Performance Tests: `backend/tests/performance/README.md`
- k6 Documentation: https://k6.io/docs/
- Sample Output: `results.csv` (generated by test runs)
