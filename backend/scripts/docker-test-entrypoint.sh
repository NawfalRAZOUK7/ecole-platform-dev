#!/bin/sh
# Entrypoint for the dockerised test runner (the `tests` profile service).
#
# 1. Hard safety guard: the test database URL MUST target a *_test database, so
#    the runner can never wipe the real `ecole_platform` data on the shared
#    Postgres container.
# 2. Ensure the isolated test database exists.
# 3. Hand off to the shared suite runner (run-backend-test-suite.sh), which
#    resets the schema, runs the requested suite, and writes coverage/junit to
#    /artifacts (mounted to the host).
set -eu

DB_URL="${TEST_DATABASE_URL:-${DATABASE_URL:-}}"
case "$DB_URL" in
  *_test*) : ;;  # OK — clearly a test database
  *)
    echo "REFUSING: TEST_DATABASE_URL/DATABASE_URL ('$DB_URL') does not target a *_test database." >&2
    echo "The dockerised test runner only operates on an isolated test database." >&2
    exit 2
    ;;
esac

cd /app
python scripts/ensure_test_db.py

exec /workspace/scripts/run-backend-test-suite.sh "$@"
