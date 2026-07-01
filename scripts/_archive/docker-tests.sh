#!/usr/bin/env bash
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/infra/docker-compose.tests.yml"
ENV_FILE="${REPO_ROOT}/.env"
PROJECT_NAME="${TEST_PROJECT_NAME:-ecole-tests}"

usage() {
  cat <<'USAGE'
Usage: scripts/docker-tests.sh [options] [suite...]

Suites:
  unit integration security contract edge performance full infra postman load

Options:
  --all             Run unit, integration, security, contract, edge, performance, infra, postman, and load
  --quick           Run unit, contract, edge, and infra
  --clean-first     Remove old Docker test containers and volumes before running
  --down-after      Stop and remove the Docker test stack after the run
  --no-build        Do not pass --build to docker compose run
  --continue-on-error  Continue running remaining suites after a failure (default: stop on first failure)
  --path <path>     Run only a specific test file or directory (backend suites only)
  --run-id <id>     Use a stable artifact folder name instead of a timestamp
  --help            Show this help

Examples:
  scripts/docker-tests.sh --all
  scripts/docker-tests.sh unit integration
  scripts/docker-tests.sh integration --path tests/integration/api/academic
  scripts/docker-tests.sh security --path tests/security/audit
  POSTMAN_ARGS="--full-collection" scripts/docker-tests.sh postman
  K6_SCENARIO="baseline/01_logins.js" scripts/docker-tests.sh load
USAGE
}

all_suites=(unit integration security contract edge performance infra postman load)
quick_suites=(unit contract edge infra)
suites=()
clean_first=0
down_after=0
with_build=1
fail_fast=1
pytest_target=""
run_id="${TEST_RUN_ID:-$(date +%Y%m%d_%H%M%S)}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      suites=("${all_suites[@]}")
      shift
      ;;
    --quick)
      suites=("${quick_suites[@]}")
      shift
      ;;
    --clean-first)
      clean_first=1
      shift
      ;;
    --down-after)
      down_after=1
      shift
      ;;
    --no-build)
      with_build=0
      shift
      ;;
    --continue-on-error)
      fail_fast=0
      shift
      ;;
    --path)
      pytest_target="$2"
      shift 2
      ;;
    --run-id)
      run_id="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      suites+=("$1")
      shift
      ;;
  esac
done

if [[ ${#suites[@]} -eq 0 ]]; then
  suites=("${all_suites[@]}")
fi

artifact_root="${REPO_ROOT}/artifacts/test-runs/${run_id}"
log_dir="${artifact_root}/logs"
status_dir="${artifact_root}/status"
mkdir -p "${log_dir}" "${status_dir}"

compose=(docker compose)
if [[ -f "${ENV_FILE}" ]]; then
  compose+=(--env-file "${ENV_FILE}")
fi
compose+=(-p "${PROJECT_NAME}" -f "${COMPOSE_FILE}")

export TEST_RUN_ID="${run_id}"

service_for_suite() {
  case "$1" in
    unit) echo "backend-unit-tests" ;;
    integration) echo "backend-integration-tests" ;;
    security) echo "backend-security-tests" ;;
    contract) echo "backend-contract-tests" ;;
    edge) echo "backend-edge-tests" ;;
    performance|perf) echo "backend-performance-tests" ;;
    full) echo "backend-full-tests" ;;
    infra) echo "infra-tests" ;;
    postman) echo "postman-tests" ;;
    load) echo "load-tests" ;;
    *)
      echo "Unknown suite: $1" >&2
      return 2
      ;;
  esac
}

write_summary() {
  local failed="$1"
  local summary_md="${artifact_root}/summary.md"
  local summary_json="${artifact_root}/summary.json"

  {
    echo "# Docker Test Run ${run_id}"
    echo
    echo "| Suite | Status | Log |"
    echo "| --- | --- | --- |"
    for suite in "${suites[@]}"; do
      local status
      status="$(cat "${status_dir}/${suite}.status" 2>/dev/null || echo "not-run")"
      if [[ "${status}" == "0" ]]; then
        echo "| ${suite} | passed | logs/${suite}.log |"
      else
        if [[ "${status}" == "skipped" ]]; then
        echo "| ${suite} | skipped | logs/${suite}.log |"
      else
        echo "| ${suite} | failed (${status}) | logs/${suite}.log |"
      fi
      fi
    done
    echo
    echo "Artifacts: ${artifact_root}"
    if [[ "${down_after}" -eq 0 ]]; then
      echo "Docker stack: ${PROJECT_NAME} left running for log inspection."
    fi
  } > "${summary_md}"

  {
    echo "{"
    echo "  \"run_id\": \"${run_id}\","
    echo "  \"artifact_root\": \"${artifact_root}\","
    echo "  \"failed\": ${failed},"
    echo "  \"suites\": ["
    local first=1
    for suite in "${suites[@]}"; do
      local status
      status="$(cat "${status_dir}/${suite}.status" 2>/dev/null || echo "not-run")"
      if [[ "${first}" -eq 0 ]]; then
        echo ","
      fi
      first=0
      printf '    {"name": "%s", "exit_code": "%s", "log": "logs/%s.log"}' "${suite}" "${status}" "${suite}"
    done
    echo
    echo "  ]"
    echo "}"
  } > "${summary_json}"
}

if [[ "${clean_first}" -eq 1 ]]; then
  "${compose[@]}" down -v --remove-orphans
fi

overall_failed=0

total_suites=${#suites[@]}
suite_idx=0

for suite in "${suites[@]}"; do
  suite_idx=$((suite_idx + 1))
  service="$(service_for_suite "${suite}")" || exit $?
  log_file="${log_dir}/${suite}.log"

  echo ""
  echo "========================================"
  echo "==> [${suite_idx}/${total_suites}] Running ${suite} in Docker service ${service}"
  echo "========================================"
  echo ""

  if [[ "${suite}" == "postman" || "${suite}" == "load" ]]; then
    "${compose[@]}" rm -sf backend-api worker > /dev/null 2>&1 || true
    # Also restart Redis and clear its persistent volume to remove stale
    # rate limits / sessions from previous runs.
    "${compose[@]}" rm -sf redis > /dev/null 2>&1 || true
    docker volume rm "${PROJECT_NAME}_tests_redis_data" > /dev/null 2>&1 || true
    "${compose[@]}" up -d redis > /dev/null 2>&1 || true
  fi

  run_args=()
  if [[ -n "${pytest_target}" ]]; then
    run_args+=(-e "PYTEST_TARGET=${pytest_target}")
  fi

  if [[ "${with_build}" -eq 1 ]]; then
    "${compose[@]}" run --rm --build "${run_args[@]}" "${service}" 2>&1 | tee "${log_file}"
    status=${PIPESTATUS[0]}
  else
    "${compose[@]}" run --rm "${run_args[@]}" "${service}" 2>&1 | tee "${log_file}"
    status=${PIPESTATUS[0]}
  fi

  echo "${status}" > "${status_dir}/${suite}.status"
  if [[ "${status}" -ne 0 ]]; then
    overall_failed=1
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo "!!! SUITE FAILED: ${suite} (exit ${status})"
    echo "!!! Log: ${log_file}"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo ""
    if [[ "${fail_fast}" -eq 1 ]]; then
      echo "--fail-fast is active. Stopping remaining suites."
      # Mark remaining suites as skipped
      for remaining in "${suites[@]}"; do
        if [[ ! -f "${status_dir}/${remaining}.status" ]]; then
          echo "skipped" > "${status_dir}/${remaining}.status"
        fi
      done
      break
    fi
  else
    echo ""
    echo "========================================"
    echo "==> [${suite_idx}/${total_suites}] PASSED: ${suite}"
    echo "========================================"
    echo ""
  fi
done

"${compose[@]}" ps > "${log_dir}/compose-ps.log" 2>&1 || true
"${compose[@]}" logs --no-color > "${log_dir}/compose-services.log" 2>&1 || true

if [[ "${down_after}" -eq 1 ]]; then
  "${compose[@]}" down -v --remove-orphans >> "${log_dir}/compose-down.log" 2>&1 || true
fi

write_summary "${overall_failed}"

echo "Docker test summary: ${artifact_root}/summary.md"
exit "${overall_failed}"
