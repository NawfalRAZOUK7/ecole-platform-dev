#!/usr/bin/env bash
# Chaos: Slow Query — test behavior with slow DB queries

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"
SCHOOL_ID="${SCHOOL_ID:-00000000-0000-4000-8000-000000000001}"

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
    --school-id)
      SCHOOL_ID="$2"
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
  echo "Usage: $0 --token <jwt> [--base-url <url>] [--school-id <uuid>]"
  exit 1
fi

echo "=== Chaos: Slow Query ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "School ID: $SCHOOL_ID"
echo ""

# Test 1: List students with potential slow query
echo "Test 1: GET ${BASE_URL}/schools/${SCHOOL_ID}/students"
START_TIME=$(date +%s)
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X GET "${BASE_URL}/schools/${SCHOOL_ID}/students" \
  -H "Authorization: Bearer $TOKEN")
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Code: $HTTP_CODE"
echo "Duration: ${DURATION}s"
echo "Response: $BODY"
echo ""

# Check for timeout or slow response
if [[ "$DURATION" -gt 10 ]]; then
  echo "✅ PASS: Query took ${DURATION}s (slow query simulation active)"
  exit 0
elif [[ "$HTTP_CODE" == "200" ]]; then
  echo "⚠️  INFO: Query completed in ${DURATION}s (slow query rule not active)"
  exit 0
elif [[ "$HTTP_CODE" == "504" ]]; then
  echo "✅ PASS: Received 504 Gateway Timeout (slow query caused timeout)"
  exit 0
else
  echo "❌ FAIL: Unexpected HTTP code $HTTP_CODE"
  exit 1
fi
