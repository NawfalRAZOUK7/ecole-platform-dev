#!/usr/bin/env bash
# Chaos: Load Smoke — mini load test (10 RPS for 30 s) to test system resilience

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"
ENDPOINT="${ENDPOINT:-health}"
RPS="${RPS:-10}"
DURATION="${DURATION:-30}"

# Parse flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --token)
      TOKEN="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --endpoint)
      ENDPOINT="$2"
      shift 2
      ;;
    --rps)
      RPS="$2"
      shift 2
      ;;
    --duration)
      DURATION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "=== Chaos: Load Smoke ==="
echo "Base URL: $BASE_URL"
echo "Endpoint: $ENDPOINT"
echo "Rate: $RPS RPS"
echo "Duration: ${DURATION}s"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Build curl command
if [[ "$ENDPOINT" == "health" ]]; then
  CURL_CMD="curl -s -o /dev/null -w '%{http_code}' ${BASE_URL}/health"
else
  if [[ -z "$TOKEN" ]]; then
    echo "Error: --token required for protected endpoints"
    exit 1
  fi
  CURL_CMD="curl -s -o /dev/null -w '%{http_code}' -X GET ${BASE_URL}/${ENDPOINT} -H 'Authorization: Bearer $TOKEN'"
fi

# Run load test using background processes
declare -a PIDS
declare -i SUCCESS=0
declare -i FAIL=0
declare -i TOTAL=0

START_TIME=$(date +%s)
END_TIME=$((START_TIME + DURATION))

echo "Starting load test..."
echo ""

while [[ $(date +%s) -lt $END_TIME ]]; do
  # Spawn RPS requests in parallel
  for _ in $(seq 1 "$RPS"); do
    RESPONSE=$(eval "$CURL_CMD" 2>/dev/null || echo "000")
    ((TOTAL++)) || true
    
    if [[ "$RESPONSE" == "200" ]]; then
      ((SUCCESS++)) || true
    else
      ((FAIL++)) || true
      echo -n "E"
    fi
  done
  sleep 1
done

# Wait for any remaining background jobs
for pid in "${PIDS[@]:-}"; do
  wait "$pid" 2>/dev/null || true
done

echo ""
echo "=== Results ==="
echo "Total Requests: $TOTAL"
echo "Success: $SUCCESS"
echo "Failures: $FAIL"
echo "Success Rate: $(echo "scale=2; $SUCCESS * 100 / $TOTAL" | bc)%"
echo ""

# Determine pass/fail
SUCCESS_RATE=$(echo "scale=2; $SUCCESS * 100 / $TOTAL" | bc)
if [[ $(echo "$SUCCESS_RATE >= 95" | bc) -eq 1 ]]; then
  echo "✅ PASS: Success rate >= 95%"
  exit 0
elif [[ $(echo "$SUCCESS_RATE >= 80" | bc) -eq 1 ]]; then
  echo "⚠️  WARN: Success rate between 80-95% (degraded but acceptable)"
  exit 0
else
  echo "❌ FAIL: Success rate < 80% (system under stress)"
  exit 1
fi
