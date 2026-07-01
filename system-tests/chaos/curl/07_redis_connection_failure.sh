#!/usr/bin/env bash
# Chaos: Redis Connection Failure — test behavior when Redis is unreachable

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

echo "=== Chaos: Redis Connection Failure ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Test 1: List sessions (requires Redis for session cache)
echo "Test 1: GET ${BASE_URL}/auth/sessions"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X GET "${BASE_URL}/auth/sessions" \
  -H "Authorization: Bearer $TOKEN")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Code: $HTTP_CODE"
echo "Response: $BODY"
echo ""

# Check for error response indicating Redis failure
if [[ "$HTTP_CODE" == "500" ]] || [[ "$HTTP_CODE" == "503" ]]; then
  echo "✅ PASS: Received error response as expected (Redis unreachable)"
  exit 0
elif [[ "$HTTP_CODE" == "200" ]]; then
  echo "⚠️  INFO: Received 200 (Redis is reachable, Requestly rule not active)"
  exit 0
else
  echo "❌ FAIL: Unexpected HTTP code $HTTP_CODE"
  exit 1
fi
