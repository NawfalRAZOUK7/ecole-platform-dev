# Load Tests (k6)

Performance and stress testing scripts using k6.

## Structure

```
tests/load/
├── config.js              # Shared configuration
├── smoke/                 # Quick health checks
│   └── healthcheck.js
├── baseline/              # Standard load patterns
│   ├── 01_logins.js
│   ├── 02_get_requests.js
│   ├── 03_file_uploads.js
│   └── 04_websocket.js
├── stress/                # Peak load scenarios
│   ├── peak_school_morning.js
│   └── upload_burst.js
└── soak/                  # Long-running stability
    └── 24h_steady_traffic.js
```

## Quick Start

```bash
# Verify API is alive
k6 run smoke/healthcheck.js

# Run baseline login test
k6 run baseline/01_logins.js

# Run all baselines
for f in baseline/*.js; do k6 run "$f"; done
```

## Configuration

Set environment variables to override defaults:

```bash
export BASE_URL="http://localhost:8000"
export API_TOKEN="your-jwt-token"
```

## Scenarios

| File | VUs | Duration | Purpose |
|------|-----|----------|---------|
| `smoke/healthcheck.js` | 1 | 10s | Verify API alive |
| `baseline/01_logins.js` | 20 | 2m | Auth performance |
| `baseline/02_get_requests.js` | 50 | 2m | Read-heavy browsing |
| `baseline/03_file_uploads.js` | 10 | 1m | Concurrent uploads |
| `baseline/04_websocket.js` | 20 | 3m | WS connection stability |
| `stress/peak_school_morning.js` | 500 | 11m | Peak morning load |
| `stress/upload_burst.js` | 50 | 7m | Upload stress test |
| `soak/24h_steady_traffic.js` | 10 | 24h+ | Memory leak detection |

## CI Integration

```yaml
- name: k6 smoke test
  run: k6 run tests/load/smoke/healthcheck.js
```
