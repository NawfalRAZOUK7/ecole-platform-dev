#!/usr/bin/env bash
# =============================================================================
#  Ecole Platform — Coverage Diagnostic Runner
#  -----------------------------------------------------------------------------
#  Runs the full backend test-coverage sequence end-to-end:
#    1) Upgrade sentry-sdk + verify app import
#    2) Bring up Postgres + Redis + load seeds + DB connectivity test
#    3) Full backend pytest with branch coverage
#
#  Streams progress live to your terminal AND saves everything under:
#    artifacts/test-runs/<UTC-timestamp>/
#  so the AI assistant can read the logs afterward.
#
#  Usage:
#    ./scripts/run-coverage-diagnostic.sh
#    (no arguments)
#
#  Constraints respected:
#    - No `git add` / `git commit` / `git push`
#    - No modification of app/ or models/
#    - No coverage threshold lowered
# =============================================================================

# Continue on errors (we want to capture the full picture even if a step fails)
set +e
set -o pipefail

# Colors (only if stdout is a TTY)
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

# -----------------------------------------------------------------------------
# Locate repo root (this script lives in scripts/, so repo root is its parent)
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# -----------------------------------------------------------------------------
# Setup output directory
# -----------------------------------------------------------------------------
TS="$(date -u +'%Y%m%d-%H%M%SZ')"
OUT_DIR="$REPO_ROOT/artifacts/test-runs/$TS"
mkdir -p "$OUT_DIR"

LOG_SENTRY="$OUT_DIR/01-sentry.log"
LOG_DB="$OUT_DIR/02-db.log"
LOG_COV="$OUT_DIR/03-coverage.log"
LOG_SUMMARY="$OUT_DIR/SUMMARY.log"
LOG_ENV="$OUT_DIR/00-env.log"

banner "Ecole Platform — Coverage Diagnostic"
{
  echo "Run timestamp (UTC) : $TS"
  echo "Repo root           : $REPO_ROOT"
  echo "Output directory    : $OUT_DIR"
  echo
  echo "Stream logs live in your terminal."
  echo "All output is persisted to the files below for later analysis :"
  echo "  - $LOG_ENV"
  echo "  - $LOG_SENTRY"
  echo "  - $LOG_DB"
  echo "  - $LOG_COV"
  echo "  - $LOG_SUMMARY"
} | tee "$LOG_ENV"

# -----------------------------------------------------------------------------
# Environment snapshot
# -----------------------------------------------------------------------------
{
  echo
  echo "--- system ---"
  uname -a
  echo
  echo "--- python (host) ---"
  command -v python3 && python3 --version
  echo
  echo "--- venv ---"
  if [ -x "$REPO_ROOT/backend/.venv/bin/python" ]; then
    "$REPO_ROOT/backend/.venv/bin/python" --version
    "$REPO_ROOT/backend/.venv/bin/pip" --version
  else
    echo "${RED}WARNING: backend/.venv/bin/python not found.${RESET}"
  fi
  echo
  echo "--- docker ---"
  command -v docker && docker --version
  docker compose version 2>/dev/null || true
  echo
  echo "--- make ---"
  command -v make && make --version | head -1
} | tee -a "$LOG_ENV"

# Activate venv (best effort)
if [ -f "$REPO_ROOT/backend/.venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source "$REPO_ROOT/backend/.venv/bin/activate"
  echo "${GREEN}venv activated.${RESET}" | tee -a "$LOG_ENV"
else
  echo "${RED}Cannot activate venv — aborting.${RESET}" | tee -a "$LOG_ENV"
  exit 1
fi

# =============================================================================
# STEP 1 — upgrade sentry-sdk + verify import
# =============================================================================
banner "STEP 1 / 3 — sentry-sdk upgrade + app.main import sanity"
{
  echo "$ pip install -U 'sentry-sdk[fastapi]>=2.27,<3.0'"
  pip install -U "sentry-sdk[fastapi]>=2.27,<3.0"
  echo
  echo "$ python -c 'import sentry_sdk; print(sentry_sdk.VERSION)'"
  python -c "import sentry_sdk; print('sentry-sdk version:', sentry_sdk.VERSION)"
  echo
  echo "$ python -c 'from app.main import app; print(\"app import OK\")'"
  ( cd "$REPO_ROOT/backend" && python -c "from app.main import app; print('app import OK')" )
  rc=$?
  echo
  if [ $rc -eq 0 ]; then
    echo "${GREEN}STEP 1 OK — Sentry option enable_logs accepted, app imports cleanly.${RESET}"
  else
    echo "${RED}STEP 1 FAILED — app import still errors. Coverage rerun cannot succeed.${RESET}"
    echo "Look at the error above. Probable causes: pip upgrade blocked, or another option mismatch."
  fi
} 2>&1 | tee "$LOG_SENTRY"

# =============================================================================
# STEP 2 — Postgres + Redis + seeds + connectivity
# =============================================================================
banner "STEP 2 / 3 — docker compose up + seeds + DB connectivity"
# The project compose file is infra/docker-compose.dev.yml (cf. Makefile DC).
COMPOSE_FLAGS="-f $REPO_ROOT/infra/docker-compose.dev.yml"
{
  echo "$ docker compose $COMPOSE_FLAGS ps (before)"
  docker compose $COMPOSE_FLAGS ps 2>&1 || true
  echo
  echo "$ docker compose $COMPOSE_FLAGS up -d postgres redis"
  docker compose $COMPOSE_FLAGS up -d postgres redis 2>&1
  echo
  echo "Waiting 8s for postgres to accept connections..."
  sleep 8
  echo
  echo "$ docker compose $COMPOSE_FLAGS ps (after)"
  docker compose $COMPOSE_FLAGS ps 2>&1
  echo

  echo "$ make seed"
  make seed 2>&1
  seed_rc=$?
  echo "(make seed exit code: $seed_rc)"
  echo

  echo "$ python connectivity test (asyncpg)"
  ( cd "$REPO_ROOT/backend" && python - <<'PY'
import asyncio, sys
try:
    import asyncpg
except Exception as e:
    print(f"asyncpg import failed: {e}")
    sys.exit(1)
try:
    from app.core.config import settings
except Exception as e:
    print(f"settings import failed: {e}")
    sys.exit(2)

async def main():
    raw = settings.database_url
    # asyncpg.connect doesn't take "+asyncpg" suffix
    dsn = raw.replace("postgresql+asyncpg://", "postgresql://")
    print("Using DSN :", dsn)
    try:
        conn = await asyncpg.connect(dsn, timeout=5)
        val = await conn.fetchval("SELECT 1")
        print("SELECT 1 ->", val)
        # Count a few tables to confirm seeds are loaded
        try:
            users = await conn.fetchval("SELECT count(*) FROM users")
            print("users count :", users)
        except Exception as e:
            print(f"users count failed ({e})")
        try:
            schools = await conn.fetchval("SELECT count(*) FROM schools")
            print("schools count :", schools)
        except Exception as e:
            print(f"schools count failed ({e})")
        await conn.close()
        print("DB connectivity OK")
    except Exception as e:
        print(f"DB connectivity FAILED: {e!r}")
        sys.exit(3)

asyncio.run(main())
PY
  )
  db_rc=$?
  echo "(connectivity test exit code: $db_rc)"
  echo
  if [ $db_rc -eq 0 ]; then
    echo "${GREEN}STEP 2 OK — Postgres reachable, seeds visible.${RESET}"
  else
    echo "${YELLOW}STEP 2 WARNING — DB connectivity issue detected. Integration suite will likely have errors.${RESET}"
    echo "Will still continue to STEP 3 to capture as much coverage as possible."
  fi
} 2>&1 | tee "$LOG_DB"

# =============================================================================
# STEP 2.5 — export DATABASE_URL from .env into the shell
# -----------------------------------------------------------------------------
# Why: backend/tests/conftest.py:313-325 defines the `postgres_url` fixture as:
#
#   def postgres_url() -> str:
#       return (
#           os.getenv("TEST_DATABASE_URL")
#           or os.getenv("DATABASE_URL")
#           or "postgresql+asyncpg://ecole:change-me@localhost:5432/ecole_platform_test"
#       )
#
# This reads from os.environ ONLY. pydantic-settings reads .env into the
# Settings object but does NOT pollute os.environ. So unless DATABASE_URL is
# exported into the shell, pytest falls back to the hard-coded URL with
# password "change-me" and DB "ecole_platform_test" — both wrong locally.
# We fix it here by sourcing .env and exporting.
# =============================================================================
banner "STEP 2.5 — export DATABASE_URL / TEST_DATABASE_URL from .env"
# CRITICAL: `export` must run in the PARENT shell. We cannot wrap it in a
# `{ ... } | tee` brace group because the pipe creates a subshell and `export`
# would not propagate. So we resolve the value first (no pipe), export it,
# then log inside a piped block which is harmless.
ROOT_ENV="$REPO_ROOT/.env"
DB_FROM_ENV=""
if [ -f "$ROOT_ENV" ]; then
  DB_FROM_ENV=$(grep -E '^DATABASE_URL=' "$ROOT_ENV" | head -1 | cut -d'=' -f2-)
fi
if [ -n "$DB_FROM_ENV" ]; then
  # NOTE: these `export` statements affect the CURRENT shell, NOT a subshell.
  export DATABASE_URL="$DB_FROM_ENV"
  export TEST_DATABASE_URL="$DB_FROM_ENV"
fi
{
  if [ -n "$DB_FROM_ENV" ]; then
    echo "Exported DATABASE_URL      : $DATABASE_URL"
    echo "Exported TEST_DATABASE_URL : $TEST_DATABASE_URL"
    echo "${GREEN}OK — conftest engine fixture will now use this URL.${RESET}"
  elif [ -f "$ROOT_ENV" ]; then
    echo "${YELLOW}WARNING: no DATABASE_URL line found in $ROOT_ENV${RESET}"
  else
    echo "${YELLOW}WARNING: $ROOT_ENV not found${RESET}"
  fi
  echo
  echo "Verification (read-back in same shell):"
  echo "  DATABASE_URL      = $DATABASE_URL"
  echo "  TEST_DATABASE_URL = $TEST_DATABASE_URL"
} 2>&1 | tee -a "$LOG_DB"

# =============================================================================
# STEP 3 — full backend coverage
# =============================================================================
banner "STEP 3 / 3 — pytest --cov=app --cov-branch (full suite)"
{
  cd "$REPO_ROOT/backend"
  echo "$ rm -rf htmlcov coverage.xml .coverage.pytest"
  rm -rf htmlcov coverage.xml .coverage.pytest
  echo
  echo "Effective env for pytest :"
  echo "  DATABASE_URL      = $DATABASE_URL"
  echo "  TEST_DATABASE_URL = $TEST_DATABASE_URL"
  echo

  echo "$ pytest --cov=app --cov-branch (full suite)"
  echo "(this will take 2-5 minutes depending on hardware)"
  echo
  python -m pytest \
    --cov=app --cov-branch \
    --cov-report=xml:coverage.xml \
    --cov-report=html:htmlcov \
    --cov-report=term-missing \
    -q
  pytest_rc=$?
  echo
  echo "(pytest exit code: $pytest_rc)"
  cd "$REPO_ROOT"
} 2>&1 | tee "$LOG_COV"

# Copy coverage XML/HTML into the run dir for archival
if [ -f "$REPO_ROOT/backend/coverage.xml" ]; then
  cp "$REPO_ROOT/backend/coverage.xml" "$OUT_DIR/coverage.xml" 2>/dev/null || true
fi
if [ -d "$REPO_ROOT/backend/htmlcov" ]; then
  cp -R "$REPO_ROOT/backend/htmlcov" "$OUT_DIR/htmlcov" 2>/dev/null || true
fi

# =============================================================================
# SUMMARY
# =============================================================================
banner "SUMMARY (saved to $LOG_SUMMARY)"
{
  echo "Run timestamp (UTC) : $TS"
  echo "Output dir          : $OUT_DIR"
  echo

  echo "===== STEP 1 (sentry) — last 15 lines ====="
  tail -15 "$LOG_SENTRY" 2>/dev/null
  echo

  echo "===== STEP 2 (db) — last 30 lines ====="
  tail -30 "$LOG_DB" 2>/dev/null
  echo

  echo "===== STEP 3 (coverage) — pytest tail (last 120 lines) ====="
  tail -120 "$LOG_COV" 2>/dev/null
  echo

  echo "===== Headline counts from pytest output ====="
  grep -E "^(=+ |passed|failed|error|skipped|TOTAL|coverage:|FAILED |ERROR |Coverage XML|Coverage HTML)" "$LOG_COV" 2>/dev/null | tail -40
  echo

  echo "===== Top 30 lowest-covered files (parsed from coverage.xml if present) ====="
  if [ -f "$OUT_DIR/coverage.xml" ]; then
    python - <<PY 2>&1
import xml.etree.ElementTree as ET
try:
    tree = ET.parse("$OUT_DIR/coverage.xml")
    root = tree.getroot()
    print(f"Global line-rate : {float(root.get('line-rate'))*100:.2f}%")
    print(f"Global branch-rate: {float(root.get('branch-rate'))*100:.2f}%")
    print(f"Lines valid       : {root.get('lines-valid')}")
    print(f"Lines covered     : {root.get('lines-covered')}")
    print()
    rows = []
    for cls in root.iter('class'):
        name = cls.get('filename')
        rate = float(cls.get('line-rate'))
        lines = cls.findall('lines/line')
        total = len(lines)
        if total > 5:
            rows.append((rate, total, name))
    rows.sort()
    print(f"{'rate':>7s}  {'lines':>5s}  file")
    for r, t, n in rows[:30]:
        print(f"{r*100:6.2f}%  {t:5d}  {n}")
except Exception as e:
    print(f"(could not parse coverage.xml: {e})")
PY
  else
    echo "(coverage.xml not generated)"
  fi
  echo

  echo "Run dir contents :"
  ls -la "$OUT_DIR"
} 2>&1 | tee "$LOG_SUMMARY"

# Final on-screen reminder
echo
echo "${BOLD}${GREEN}Done.${RESET}"
echo "All logs persisted under: ${BOLD}$OUT_DIR${RESET}"
echo
echo "To share with the AI assistant, paste this in chat:"
echo "  cat $LOG_SUMMARY"
echo
echo "Or for the full pytest output:"
echo "  cat $LOG_COV"
