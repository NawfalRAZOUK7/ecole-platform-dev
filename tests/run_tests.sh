#!/usr/bin/env bash
# =============================================================================
# École Platform — Phase 12 API Test Runner
# Runs the Postman collection via Newman CLI
# Usage: ./tests/run_tests.sh [--env <env-file>] [--folder <folder-name>]
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COLLECTION="$SCRIPT_DIR/postman_collection_phase12.json"
ENV_FILE=""
FOLDER=""
REPORTERS="cli,json"
OUTPUT_DIR="$SCRIPT_DIR/reports"

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)       ENV_FILE="$2"; shift 2 ;;
    --folder)    FOLDER="$2"; shift 2 ;;
    --reporters) REPORTERS="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--env <file>] [--folder <name>] [--reporters cli,json,html]"
      echo ""
      echo "Options:"
      echo "  --env        Path to Newman environment JSON file"
      echo "  --folder     Run only a specific folder (e.g. '03 — Messaging')"
      echo "  --reporters  Comma-separated reporters (default: cli,json)"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Run all tests"
      echo "  $0 --folder '00 — Auth Setup'         # Run auth folder only"
      echo "  $0 --env staging.env.json              # Use staging environment"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Check Newman installed ---
if ! command -v newman &>/dev/null; then
  echo "❌ Newman is not installed. Install it with:"
  echo "   npm install -g newman"
  echo "   npm install -g newman-reporter-html  # optional HTML reports"
  exit 1
fi

# --- Check collection exists ---
if [[ ! -f "$COLLECTION" ]]; then
  echo "❌ Collection not found: $COLLECTION"
  exit 1
fi

# --- Prepare output directory ---
mkdir -p "$OUTPUT_DIR"

# --- Build Newman command ---
CMD=(newman run "$COLLECTION")

if [[ -n "$ENV_FILE" ]]; then
  CMD+=(-e "$ENV_FILE")
fi

if [[ -n "$FOLDER" ]]; then
  CMD+=(--folder "$FOLDER")
fi

# Add reporters
IFS=',' read -ra REP_LIST <<< "$REPORTERS"
for rep in "${REP_LIST[@]}"; do
  CMD+=(-r "$rep")
done

# JSON report output
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
CMD+=(--reporter-json-export "$OUTPUT_DIR/report_$TIMESTAMP.json")

# Timeout and retry settings
CMD+=(--timeout-request 10000)
CMD+=(--delay-request 100)

# --- Run ---
echo "🧪 École Platform — Phase 12 API Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Collection: $COLLECTION"
[[ -n "$ENV_FILE" ]] && echo "Environment: $ENV_FILE"
[[ -n "$FOLDER" ]] && echo "Folder: $FOLDER"
echo "Report: $OUTPUT_DIR/report_$TIMESTAMP.json"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

"${CMD[@]}"

EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
  echo "✅ All tests passed!"
else
  echo "❌ Some tests failed (exit code: $EXIT_CODE)"
fi

echo "📄 JSON report saved to: $OUTPUT_DIR/report_$TIMESTAMP.json"
exit $EXIT_CODE
