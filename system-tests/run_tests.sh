#!/usr/bin/env bash
# =============================================================================
# Ecole Platform Postman runner
#
# Safe by default: this script refuses localhost:8000 because that is the
# normal dev database target. Use api-test-up or pass a disposable base URL.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$SCRIPT_DIR/postman/env_local.json"
FOLDER=""
REPORTERS="cli,json"
OUTPUT_DIR="${POSTMAN_OUTPUT_DIR:-$SCRIPT_DIR/reports}"
BASE_URL="${POSTMAN_BASE_URL:-http://localhost:8000/api/v1}"
ALLOW_DEV_DB="${POSTMAN_ALLOW_DEV_DB:-0}"
ALLOW_UNASSERTED="${POSTMAN_ALLOW_UNASSERTED:-0}"
LIST_ONLY=0
declare -a COLLECTIONS=()

usage() {
  cat <<'USAGE'
Usage: system-tests/run_tests.sh [options]

Options:
  --include-scenarios       Also include system-tests/postman/scenario_*.postman_collection.json
  --full-collection         Run system-tests/postman/ecole_platform_full.postman_collection.json
  --all                     Run full collection and scenario collections
  --collection <file>       Run a specific collection file
  --env <file>              Newman environment JSON (default: system-tests/postman/env_local.json)
  --base-url <url>          API base URL, e.g. http://localhost:8010/api/v1
  --folder <name>           Run a specific Postman folder
  --reporters <list>        Comma-separated reporters (default: cli,json)
  --output-dir <dir>        Directory for Newman JSON reports
  --allow-dev-db            Permit localhost:8000 explicitly
  --allow-unasserted        Permit collections with zero test scripts
  --list                    Print selected collections and exit
  --help, -h                Show this help

Examples:
  system-tests/run_tests.sh --all --base-url http://localhost:8010/api/v1
  system-tests/run_tests.sh --full-collection --base-url http://localhost:8010/api/v1
USAGE
}

add_scenario_collections() {
  local file
  # Collections that intentionally mutate shared test users and break subsequent collections
  # when run in a single batch. Run them individually instead.
  local skip_list="scenario_account_lockout scenario_password_change scenario_password_reuse scenario_chaos scenario_direct_upload_flow scenario_email_recovery scenario_invoice_pdf_flow scenario_program_enrollment_flow scenario_register scenario_session_management scenario_sentry_testmail"
  while IFS= read -r file; do
    local basename
    basename=$(basename "$file" .postman_collection.json)
    if [[ " $skip_list " =~ " $basename " ]]; then
      continue
    fi
    COLLECTIONS+=("$file")
  done < <(find "$SCRIPT_DIR/postman" -maxdepth 1 -name 'scenario_*.postman_collection.json' | sort)
}

is_true() {
  case "${1:-}" in
    1|true|TRUE|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

normalize_base_urls() {
  API_BASE_URL="${BASE_URL%/}"
  if [[ "$API_BASE_URL" == */api/v1 ]]; then
    ROOT_BASE_URL="${API_BASE_URL%/api/v1}"
  else
    ROOT_BASE_URL="$API_BASE_URL"
    API_BASE_URL="$API_BASE_URL/api/v1"
  fi
  API_PREFIX="/api/v1"
}

assert_safe_target() {
  normalize_base_urls
  if [[ "$ROOT_BASE_URL" =~ ^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|\[::1\]):8000$ ]] && ! is_true "$ALLOW_DEV_DB"; then
    cat >&2 <<EOF
Refusing to run Postman against $API_BASE_URL.
That target is the normal dev DB. Use the disposable API-test stack instead:

  make api-test-up
  POSTMAN_BASE_URL=http://localhost:8010/api/v1 system-tests/run_tests.sh --all
  make api-test-down

If you intentionally want to dirty the dev DB, rerun with --allow-dev-db.
EOF
    exit 2
  fi
}

assert_collection_ready() {
  local collection="$1"
  if [[ ! -f "$collection" ]]; then
    echo "Collection not found: $collection" >&2
    exit 1
  fi

  if command -v jq >/dev/null 2>&1; then
    local test_count
    test_count="$(jq '[.. | objects | select(.listen? == "test")] | length' "$collection")"
    if [[ "$test_count" == "0" ]] && ! is_true "$ALLOW_UNASSERTED"; then
      echo "Refusing unasserted Postman collection: $collection" >&2
      echo "Add test scripts or pass --allow-unasserted for exploratory runs." >&2
      exit 3
    fi
  fi
}

run_collection() {
  local collection="$1"
  local stem
  local report
  local timestamp
  timestamp="$(date +%Y%m%d_%H%M%S)"
  stem="$(basename "$collection" .json | tr '/' '_')"
  report="$OUTPUT_DIR/${stem}_$timestamp.json"

  local cmd=(newman run "$collection")

  if [[ -n "$ENV_FILE" ]]; then
    cmd+=(-e "$ENV_FILE")
  fi

  if [[ -n "$FOLDER" ]]; then
    cmd+=(--folder "$FOLDER")
  fi

  IFS=',' read -ra rep_list <<< "$REPORTERS"
  local rep
  for rep in "${rep_list[@]}"; do
    cmd+=(-r "$rep")
  done

  cmd+=(--reporter-json-export "$report")
  cmd+=(--timeout-request 10000)
  cmd+=(--delay-request 100)
  cmd+=(--working-dir "$REPO_ROOT")
  cmd+=(--env-var "baseUrl=$API_BASE_URL")
  # Legacy scenario collections keep {{api_prefix}} as a URL path segment.
  # Passing "/api/v1" creates an empty path segment ("//api/v1"), so inject
  # the segment form while keeping baseUrl for phase collections.
  cmd+=(--env-var "base_url=$ROOT_BASE_URL")
  cmd+=(--env-var "api_prefix=api/v1")
  cmd+=(--env-var "schoolId=00000000-0000-4000-8000-000000000001")
  cmd+=(--env-var "school_id=00000000-0000-4000-8000-000000000001")
  cmd+=(--env-var "studentId=10000000-0000-4000-8000-000000000007")
  cmd+=(--env-var "student_id=10000000-0000-4000-8000-000000000007")
  cmd+=(--env-var "teacherId=10000000-0000-4000-8000-000000000003")
  cmd+=(--env-var "teacher_id=10000000-0000-4000-8000-000000000003")
  cmd+=(--env-var "academicYearId=20000000-0000-4000-8000-000000000001")
  cmd+=(--env-var "academic_year_id=20000000-0000-4000-8000-000000000001")
  cmd+=(--env-var "periodId=20000000-0000-4000-8000-000000000002")
  cmd+=(--env-var "period_id=20000000-0000-4000-8000-000000000002")

  echo "Collection: $collection"
  echo "Base URL:   $API_BASE_URL"
  [[ -n "$ENV_FILE" ]] && echo "Environment: $ENV_FILE"
  [[ -n "$FOLDER" ]] && echo "Folder: $FOLDER"
  echo "Report:    $report"
  echo ""

  "${cmd[@]}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-scenarios)
      add_scenario_collections
      shift
      ;;
    --full-collection)
      COLLECTIONS+=("$SCRIPT_DIR/postman/ecole_platform_full.postman_collection.json")
      shift
      ;;
    --all)
      add_scenario_collections
      COLLECTIONS+=("$SCRIPT_DIR/postman/ecole_platform_full.postman_collection.json")
      shift
      ;;
    --collection)
      COLLECTIONS+=("$2")
      shift 2
      ;;
    --env)
      ENV_FILE="$2"
      shift 2
      ;;
    --base-url)
      BASE_URL="$2"
      shift 2
      ;;
    --folder)
      FOLDER="$2"
      shift 2
      ;;
    --reporters)
      REPORTERS="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --allow-dev-db)
      ALLOW_DEV_DB=1
      shift
      ;;
    --allow-unasserted)
      ALLOW_UNASSERTED=1
      shift
      ;;
    --list)
      LIST_ONLY=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ${#COLLECTIONS[@]} -eq 0 ]]; then
  COLLECTIONS+=("$SCRIPT_DIR/postman/ecole_platform_full.postman_collection.json")
fi

normalize_base_urls

if [[ "$LIST_ONLY" -eq 1 ]]; then
  printf '%s\n' "${COLLECTIONS[@]}"
  exit 0
fi

assert_safe_target

if ! command -v newman >/dev/null 2>&1; then
  echo "Newman is not installed. Install it with: npm install -g newman" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

for collection in "${COLLECTIONS[@]}"; do
  assert_collection_ready "$collection"
done

echo "Ecole Platform Postman tests"
echo "==========================="
echo "Selected collections: ${#COLLECTIONS[@]}"
echo ""

for collection in "${COLLECTIONS[@]}"; do
  run_collection "$collection"
done
