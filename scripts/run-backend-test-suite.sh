#!/bin/sh
set -eu

suite="${1:-unit}"
artifact_root="${TEST_ARTIFACT_ROOT:-/artifacts/test-runs/manual}"
suite_dir="${artifact_root}/backend/${suite}"

mkdir -p "${suite_dir}"
cd /app

python --version > "${suite_dir}/environment.txt"
python -m pytest --version >> "${suite_dir}/environment.txt"

if [ "${RESET_TEST_DB:-1}" = "1" ]; then
  python scripts/reset_test_database.py
fi

case "${suite}" in
  unit)
    target="${PYTEST_TARGET:-tests/unit}"
    ;;
  integration)
    target="${PYTEST_TARGET:-tests/integration}"
    ;;
  security)
    target="${PYTEST_TARGET:-tests/security}"
    ;;
  contract)
    target="${PYTEST_TARGET:-tests/contract}"
    ;;
  edge)
    target="${PYTEST_TARGET:-tests/edge}"
    ;;
  performance|perf)
    mkdir -p "${suite_dir}"
    exec python -m pytest "${PYTEST_TARGET:-tests/performance}" \
      --maxfail=5 \
      --benchmark-enable \
      --benchmark-json="${suite_dir}/benchmark.json" \
      --junitxml="${suite_dir}/junit.xml"
    ;;
  full)
    target="${PYTEST_TARGET:-tests}"
    ;;

  seq)
    # Sequential pipeline: unit → integration → security → contract → edge
    # Stops immediately on first failure; generates combined coverage only when all pass.
    groups="unit integration security contract edge"
    first=1

    for group in $groups; do
      group_dir="${suite_dir}/${group}"
      mkdir -p "${group_dir}"

      printf '\n'
      printf '═══════════════════════════════════════════\n'
      printf '  ▶  %-12s tests\n' "${group}"
      printf '═══════════════════════════════════════════\n'

      if [ "${first}" = "1" ]; then
        python -m pytest "tests/${group}" \
          -x \
          --junitxml="${group_dir}/junit.xml" \
          --cov=app \
          --cov-branch \
          --cov-report= \
          || { printf '\n✗  %s tests FAILED — pipeline stopped.\n' "${group}" >&2; exit 1; }
        first=0
      else
        python -m pytest "tests/${group}" \
          -x \
          --junitxml="${group_dir}/junit.xml" \
          --cov=app \
          --cov-branch \
          --cov-append \
          --cov-report= \
          || { printf '\n✗  %s tests FAILED — pipeline stopped.\n' "${group}" >&2; exit 1; }
      fi

      printf '✓  %s passed\n' "${group}"
    done

    printf '\n'
    printf '═══════════════════════════════════════════\n'
    printf '  All groups passed — generating coverage\n'
    printf '═══════════════════════════════════════════\n'
    python -m coverage report \
      --fail-under="${COV_FAIL_UNDER:-0}" \
      --show-missing
    python -m coverage html -d "${suite_dir}/htmlcov"
    python -m coverage xml -o "${suite_dir}/coverage.xml"
    printf '\nCoverage report → %s/htmlcov/index.html\n' "${suite_dir}"
    exit 0
    ;;

  *)
    echo "Unknown backend test suite: ${suite}" >&2
    echo "Expected one of: unit, integration, security, contract, edge, performance, full, seq" >&2
    exit 2
    ;;
esac

exec python -m pytest "${target}" \
  --maxfail=5 \
  --junitxml="${suite_dir}/junit.xml" \
  --cov=app \
  --cov-branch \
  --cov-fail-under="${COV_FAIL_UNDER:-0}" \
  --cov-report="xml:${suite_dir}/coverage.xml" \
  --cov-report="html:${suite_dir}/htmlcov" \
  --cov-report=term-missing
