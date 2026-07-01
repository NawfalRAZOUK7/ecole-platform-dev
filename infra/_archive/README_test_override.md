# docker-compose.test.override.yml — archived 2026-06-09

This override file is **no longer used**. Its single `tests` service was merged
directly into `infra/docker-compose.dev.yml` under the `tests` profile (one-shot
container `ecole-tests-runner`, mirroring `ecole-minio-init`): it now auto-starts
after the dev containers are healthy, runs the suite against the isolated
`ecole_platform_test` DB, writes coverage to `./test-artifacts/`, and stays as
`Exited (0)`.

Run it with `make dtest` (stays) or the ephemeral `make dtest-unit` / `dtest-seq`.
Kept here for history only — do not re-add `-f docker-compose.test.override.yml`.
