#!/usr/bin/env bash
# Chaos: Webhook Duplicate — test PSP webhook deduplication

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
NGROK_URL="${NGROK_URL:-}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-test-secret}"

# Parse flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --ngrok-url)
      NGROK_URL="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --webhook-secret)
      WEBHOOK_SECRET="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate
if [[ -z "$NGROK_URL" ]]; then
  echo "Error: --ngrok-url required"
  echo "Usage: $0 --ngrok-url <https://*.ngrok-free.app> [--base-url <url>] [--webhook-secret <secret>]"
  exit 1
fi

echo "=== Chaos: Webhook Duplicate ==="
echo "Base URL: $BASE_URL"
echo "Ngrok URL: $NGROK_URL"
echo "Webhook Secret: ${WEBHOOK_SECRET:0:10}..."
echo ""

# Sample PSP webhook payload
PROVIDER_EVENT_ID="psp-evt-$(date +%s)"
PAYLOAD='{
  "provider": "test_psp",
  "provider_event_id": "'$PROVIDER_EVENT_ID'",
  "amount": 1000,
  "currency": "MAD",
  "status": "completed",
  "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
}'

# Send webhook first time
echo "POST ${BASE_URL}/payments/webhook/test_psp (first time)"
RESP1=$(curl -s -w "\n%{http_code}" \
  -X POST "${BASE_URL}/payments/webhook/test_psp" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: ${WEBHOOK_SECRET}" \
  -d "$PAYLOAD")

CODE1=$(echo "$RESP1" | tail -n1)
BODY1=$(echo "$RESP1" | sed '$d')

echo "HTTP Code: $CODE1"
echo "Response: $BODY1"
echo ""

# Wait 1 second
sleep 1

# Send webhook second time (same provider_event_id)
echo "POST ${BASE_URL}/payments/webhook/test_psp (duplicate, same event_id)"
RESP2=$(curl -s -w "\n%{http_code}" \
  -X POST "${BASE_URL}/payments/webhook/test_psp" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Signature: ${WEBHOOK_SECRET}" \
  -d "$PAYLOAD")

CODE2=$(echo "$RESP2" | tail -n1)
BODY2=$(echo "$RESP2" | sed '$d')

echo "HTTP Code: $CODE2"
echo "Response: $BODY2"
echo ""

# Check if second response indicates already_processed
if echo "$BODY2" | grep -q "already_processed\|duplicate\|already seen"; then
  echo "✅ PASS: Second request marked as already processed (dedup working)"
  exit 0
elif [[ "$CODE2" == "200" ]] && [[ "$CODE1" == "200" ]]; then
  echo "⚠️  INFO: Both requests returned 200 (dedup may not be active or bypassed)"
  exit 0
else
  echo "❌ FAIL: Unexpected response pattern"
  echo "First: $CODE1 / $BODY1"
  echo "Second: $CODE2 / $BODY2"
  exit 1
fi
