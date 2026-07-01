#!/usr/bin/env bash
# Chaos: Sync Push 503 — test offline-first behaviour when sync push returns 503

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

echo "=== Chaos: Sync Push 503 ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Sample sync push payload
PAYLOAD='{
  "device_id": "chaos-test-device",
  "changes": [
    {
      "entity_type": "student",
      "entity_id": "12345",
      "action": "update",
      "data": {"name": "Chaos Test Student"}
    }
  ]
}'

# Send sync push
echo "POST ${BASE_URL}/sync/push"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -X POST "${BASE_URL}/sync/push" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Code: $HTTP_CODE"
echo "Response: $BODY"
echo ""

# Check for 503 (Requestly-injected) or 200 (normal)
if [[ "$HTTP_CODE" == "503" ]]; then
  echo "✅ PASS: Received 503 as expected (Requestly rule active)"
  exit 0
elif [[ "$HTTP_CODE" == "200" ]]; then
  echo "⚠️  INFO: Received 200 (Requestly rule not active or sync succeeded)"
  exit 0
else
  echo "❌ FAIL: Unexpected HTTP code $HTTP_CODE"
  exit 1
fi
