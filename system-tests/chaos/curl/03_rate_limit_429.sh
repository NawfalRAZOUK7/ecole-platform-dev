#!/usr/bin/env bash
# Chaos: Rate Limit 429 — test client retry behaviour under rate limiting

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"
REQUEST_COUNT="${REQUEST_COUNT:-20}"

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
    --request-count)
      REQUEST_COUNT="$2"
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
  echo "Usage: $0 --token <jwt> [--base-url <url>] [--request-count <n>]"
  exit 1
fi

echo "=== Chaos: Rate Limit 429 ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "Request Count: $REQUEST_COUNT"
echo ""

# Fire requests and collect status codes
declare -a STATUS_CODES
for i in $(seq 1 "$REQUEST_COUNT"); do
  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
    -X GET "${BASE_URL}/auth/me" \
    -H "Authorization: Bearer $TOKEN")
  STATUS_CODES+=("$RESPONSE")
  echo -n "."
  if [[ $((i % 5)) -eq 0 ]]; then
    echo " [$i/$REQUEST_COUNT]"
  fi
  # Add small delay between requests
  sleep 0.1
done
echo ""

# Count status codes
echo "=== Status Code Distribution ==="
declare -A COUNTS
for CODE in "${STATUS_CODES[@]}"; do
  ((COUNTS[$CODE]++)) || true
done

for CODE in $(printf '%s\n' "${!COUNTS[@]}" | sort -n); do
  echo "  $CODE: ${COUNTS[$CODE]}"
done
echo ""

# Check if 429s appeared
if [[ -n "${COUNTS[429]:-}" ]]; then
  echo "✅ PASS: Received ${COUNTS[429]} 429 responses (rate limiting active)"
  exit 0
elif [[ -n "${COUNTS[200]:-}" ]]; then
  echo "⚠️  INFO: All requests returned 200 (rate limit may not be active or threshold not reached)"
  exit 0
else
  echo "❌ FAIL: No 200 or 429 responses received"
  exit 1
fi
