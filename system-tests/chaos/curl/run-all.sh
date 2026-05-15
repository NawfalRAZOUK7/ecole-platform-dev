#!/usr/bin/env bash
# Chaos Test Orchestrator — runs all 5 curl chaos scripts in sequence

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BASE_URL="${BASE_URL:-http://localhost:8000/api/v1}"
TOKEN="${TOKEN:-}"
NGROK_URL="${NGROK_URL:-}"
WEBHOOK_SECRET="${WEBHOOK_SECRET:-test-secret}"

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
    --ngrok-url)
      NGROK_URL="$2"
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

echo "=== Chaos Test Orchestrator ==="
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "Ngrok URL: ${NGROK_URL:0:30}..."
echo "Webhook Secret: ${WEBHOOK_SECRET:0:10}..."
echo ""

# Export for child scripts
export BASE_URL
export TOKEN
export NGROK_URL
export WEBHOOK_SECRET

declare -a RESULTS
declare -i PASSED=0
declare -i FAILED=0

# Run each script
SCRIPTS=(
  "01_sync_push_503.sh:Sync Push 503"
  "02_webhook_duplicate.sh:Webhook Duplicate"
  "03_rate_limit_429.sh:Rate Limit 429"
  "04_latency_800ms.sh:Latency 800ms"
  "05_load_smoke.sh:Load Smoke"
)

for SCRIPT_ENTRY in "${SCRIPTS[@]}"; do
  IFS=':' read -r SCRIPT_NAME SCRIPT_DESC <<< "$SCRIPT_ENTRY"
  echo "=== Running: $SCRIPT_DESC ==="
  
  if bash "${SCRIPT_DIR}/${SCRIPT_NAME}"; then
    echo "✅ $SCRIPT_DESC: PASSED"
    ((PASSED++)) || true
    RESULTS+=("$SCRIPT_DESC: ✅ PASS")
  else
    echo "❌ $SCRIPT_DESC: FAILED"
    ((FAILED++)) || true
    RESULTS+=("$SCRIPT_DESC: ❌ FAIL")
  fi
  echo ""
done

# Summary
echo "=== Summary ==="
for RESULT in "${RESULTS[@]}"; do
  echo "  $RESULT"
done
echo ""
echo "Total: $((PASSED + FAILED))"
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [[ $FAILED -eq 0 ]]; then
  echo "✅ All chaos tests passed"
  exit 0
else
  echo "❌ $FAILED chaos test(s) failed"
  exit 1
fi
