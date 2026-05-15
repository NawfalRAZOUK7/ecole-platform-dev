#!/bin/sh
set -eu

artifact_root="${TEST_ARTIFACT_ROOT:-/artifacts/test-runs/manual}"
infra_dir="${artifact_root}/infra"
mkdir -p "${infra_dir}"

cd /workspace

export POSTGRES_USER="${POSTGRES_USER:-ecole}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-change-me}"
export POSTGRES_DB="${POSTGRES_DB:-ecole_platform}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-change-me-dev-redis}"
export REPLICATOR_PASSWORD="${REPLICATOR_PASSWORD:-change-me-replicator}"
export IMAGE_TAG="${IMAGE_TAG:-test}"

if ! docker compose version > "${infra_dir}/docker-compose-version.txt" 2>&1; then
  echo "docker compose is not available in the infra test container" >&2
  cat "${infra_dir}/docker-compose-version.txt" >&2 || true
  exit 2
fi

compose_files="
infra/docker-compose.dev.yml
infra/docker-compose.api-test.yml
infra/docker-compose.tests.yml
infra/docker-compose.monitoring.yml
infra/docker-compose.staging.yml
infra/docker-compose.prod.yml
infra/docker-compose.blue.yml
infra/docker-compose.green.yml
"

for file in ${compose_files}; do
  if [ ! -f "${file}" ]; then
    echo "Missing compose file: ${file}" >&2
    exit 1
  fi

  name="$(basename "${file}" .yml)"
  echo "Validating ${file}"
  if [ -f .env ]; then
    docker compose --env-file .env -f "${file}" config -q > "${infra_dir}/${name}.config.log"
  else
    docker compose -f "${file}" config -q > "${infra_dir}/${name}.config.log"
  fi
done

if [ -f .env ]; then
  services="$(docker compose --env-file .env -f infra/docker-compose.tests.yml config --services)"
else
  services="$(docker compose -f infra/docker-compose.tests.yml config --services)"
fi
printf '%s\n' "${services}" > "${infra_dir}/docker-compose.tests.services.txt"

required_services="
postgres
redis
minio
backend-api
backend-unit-tests
backend-integration-tests
backend-security-tests
backend-contract-tests
postman-tests
load-tests
infra-tests
"

for service in ${required_services}; do
  if ! printf '%s\n' "${services}" | grep -qx "${service}"; then
    echo "Missing required test service: ${service}" >&2
    exit 1
  fi
done

for file in infra/k8s/Chart.yaml infra/k8s/values.yaml infra/k8s/values-local.yaml infra/k8s/values-staging.yaml infra/k8s/values-prod.yaml; do
  if [ ! -s "${file}" ]; then
    echo "Missing or empty Kubernetes file: ${file}" >&2
    exit 1
  fi
done

echo "Infra compose and Kubernetes file checks passed"
