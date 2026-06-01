#!/usr/bin/env bash
# =============================================================================
#  Ecole Platform — Focused Test-Error Diagnostic
#  -----------------------------------------------------------------------------
#  Runs each test suite in turn with `-x` (stop at first failure) and
#  `--tb=short` (compact traceback) so we surface the ROOT CAUSE of the
#  setup errors (the "E" characters) without waiting for the full suite.
#
#  Why this script exists:
#    The previous run-coverage-diagnostic.sh ran pytest in -q mode, which only
#    prints dot/E/x markers during the run. The actual error tracebacks come
#    only at the very end. If you Ctrl-C early, you see lots of E but no info
#    about WHY. This script avoids that by stopping at the first error per
#    suite and printing its full short traceback.
#
#  Usage:
#    ./scripts/diagnose-test-errors.sh
#    (no arguments)
#
#  Output:
#    artifacts/test-runs/<UTC-timestamp>-diagnose/
#       ├── 00-env.log
#       ├── unit.log
#       ├── integration.log
#       ├── contract.log
#       ├── security.log
#       ├── edge.log
#       └── SUMMARY.log     ← paste this back to the AI assistant
#
#  Constraints respected:
#    - No git add / git commit / git push
#    - No modification of app/ or models/
# =============================================================================

set +e
set -o pipefail

# Colors
if [ -t 1 ]; then
  BOLD=$'\033[1m'; RED=$'\033[31m'; GREEN=$'\033[32m'
  YELLOW=$'\033[33m'; CYAN=$'\033[36m'; RESET=$'\033[0m'
else
  BOLD=""; RED=""; GREEN=""; YELLOW=""; CYAN=""; RESET=""
fi

banner() {
  local title="$1"
  echo
  echo "${BOLD}${CYAN}===============================================================================${RESET}"
  echo "${BOLD}${CYAN}  $title${RESET}"
  echo "${BOLD}${CYAN}===============================================================================${RESET}"
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

TS="$(date -u +'%Y%m%d-%H%M%SZ')"
OUT_DIR="$REPO_ROOT/artifacts/test-runs/${TS}-diagnose"
mkdir -p "$OUT_DIR"

LOG_ENV="$OUT_DIR/00-env.log"
LOG_SUMMARY="$OUT_DIR/SUMMARY.log"

banner "Ecole Platform — Focused Test-Error Diagnostic"
{
  echo "Run timestamp (UTC) : $TS"
  echo "Output directory    : $OUT_DIR"
  echo
  echo "This script runs each suite with -x (stop at first failure) so we get"
  echo "the actual error trace, instead of just E markers."
  echo
  echo "Logs persisted under :"
  echo "  - $OUT_DIR/*.log"
} | tee "$LOG_ENV"

# Activate venv
if [ -f "$REPO_ROOT/backend/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/backend/.venv/bin/activate"
else
  echo "${RED}venv missing — abort${RESET}" | tee -a "$LOG_ENV"
  exit 1
fi

# Confirm app imports OK before running suites
{
  echo
  echo "--- import sanity ---"
  ( cd "$REPO_ROOT/backend" && python -c "from app.main import app; print('app import OK')" 2>&1 )
  echo
  echo "--- pytest version ---"
  python -m pytest --version 2>&1 | head -3
} | tee -a "$LOG_ENV"

# -----------------------------------------------------------------------------
# Per-suite runner
# -----------------------------------------------------------------------------
run_suite() {
  local suite_name="$1"
  local suite_path="$2"
  local extra="$3"
  local log="$OUT_DIR/${suite_name}.log"

  banner "Suite: ${suite_name}  (${suite_path})  — stop at first failure"
  {
    if [ ! -d "$REPO_ROOT/backend/${suite_path}" ]; then
      echo "${YELLOW}Skipping ${suite_name}: directory backend/${suite_path} not found.${RESET}"
      return
    fi
    echo "$ pytest ${suite_path} -x --tb=short ${extra}"
    echo "(stops at first failure to surface the root cause fast)"
    echo
    cd "$REPO_ROOT/backend"
    # No -q (we want test ids), --tb=short keeps tracebacks compact,
    # -x stops at first failure/error, --no-header trims noise.
    python -m pytest "${suite_path}" \
        -x --tb=short --no-header \
        --color=no \
        ${extra}
    rc=$?
    echo
    echo "(pytest exit code: $rc)"
    cd "$REPO_ROOT"
  } 2>&1 | tee "$log"
}

# Run only a handful of files per suite the first time, to keep the run fast
# (we only need the FIRST error of each).
run_suite "unit"        "tests/unit"        ""
run_suite "edge"        "tests/edge"        ""
run_suite "contract"    "tests/contract"    ""
run_suite "security"    "tests/security"    ""
run_suite "integration" "tests/integration" ""

# -----------------------------------------------------------------------------
# Final summary (the file to paste back to the AI)
# -----------------------------------------------------------------------------
banner "SUMMARY"
{
  echo "Run timestamp (UTC) : $TS"
  echo "Output dir          : $OUT_DIR"
  echo
  for s in unit edge contract security integration; do
    log="$OUT_DIR/${s}.log"
    if [ -f "$log" ]; then
      echo
      echo "===== Suite: ${s} — last 80 lines ====="
      tail -80 "$log" 2>/dev/null
      echo
      echo "----- ${s}: grep ERROR/FAILED/AssertionError/Traceback -----"
      grep -nE "ERROR|FAILED|AssertionError|Traceback|asyncpg\.|sqlalchemy\.|ImportError|ModuleNotFoundError|TypeError|fixture .* not found" "$log" 2>/dev/null | head -40
    fi
  done
  echo
  echo "Run dir contents :"
  ls -la "$OUT_DIR"
} 2>&1 | tee "$LOG_SUMMARY"

echo
echo "${BOLD}${GREEN}Done.${RESET}"
echo "Paste this to share with the AI assistant :"
echo "  cat $LOG_SUMMARY"
echo
echo "Or, for a specific suite's full output :"
echo "  cat $OUT_DIR/unit.log"
echo "  cat $OUT_DIR/integration.log"
echo "  ... etc."
