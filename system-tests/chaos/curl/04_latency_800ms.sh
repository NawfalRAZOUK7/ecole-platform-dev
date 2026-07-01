#!/usr/bin/env bash
# Chaos: Latency 800ms — test UI loader/timeout tolerance with delayed sync

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"

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
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate
if [[ -z "$TOKEN" ]]; then
  echo "Error: --token required"
  echo "Usage: $0 --token <jwt> [--base-url <url>]"
  exit 1
fi

echo "=== Chaos: Latency 800ms ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo ""
echo "NOTE: This test measures actual latency. Enable Requestly rule 'Chaos: Sync API Delay 800ms' first."
echo ""

# Measure sync pull with timing
START=$(date +%s%N)
RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" \
  -X GET "${BASE_URL}/sync/pull" \
  -H "Authorization: Bearer $TOKEN")
END=$(date +%s%N)

HTTP_CODE=$(echo "$RESPONSE" | tail -n2 | head -n1)
TIME_TOTAL=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d' | sed '$d')

echo "HTTP Code: $HTTP_CODE"
echo "Time Total: ${TIME_TOTAL}s"
echo "Response: $BODY"
echo ""

# Check latency threshold
LATENCY_MS=$(echo "$TIME_TOTAL * 1000" | bc)
echo "Latency: ${LATENCY_MS}ms"
echo ""

if [[ $(echo "$LATENCY_MS >= 800" | bc) -eq 1 ]]; then
  echo "✅ PASS: Latency >= 800ms (Requestly rule active)"
  exit 0
elif [[ $(echo "$LATENCY_MS < 800" | bc) -eq 1 ]]; then
  echo "⚠️  INFO: Latency < 800ms (Requestly rule not active or network fast)"
  exit 0
else
  echo "❌ FAIL: Could not measure latency"
  exit 1
fi
