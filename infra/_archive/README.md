# Archived Legacy Test Infrastructure

## What was archived

| File | Original location |
|------|-------------------|
| `docker-compose.tests.yml` | `infra/docker-compose.tests.yml` |
| `docker-compose.api-test.yml` | `infra/docker-compose.api-test.yml` |
| `docker-tests.sh` | `scripts/docker-tests.sh` (moved to `scripts/_archive/`) |

## Why

These files each defined their own duplicate Postgres, Redis, MinIO, and backend
containers for running tests. This caused credential drift, port conflicts, and
required maintaining a second full compose stack.

## Replacement

All Dockerized backend tests now run via the consolidated runner:

- **`infra/docker-compose.test.override.yml`** — adds a single `tests` service
  (profile `tests`) that reuses the dev stack containers (`ecole-postgres`,
  `ecole-redis`, `ecole-minio`, `ecole-mock-oauth`) on `ecole-network`.
  Tests run against an isolated `ecole_platform_test` database — the real
  `ecole_platform` database is never touched.
- **`scripts/run-backend-test-suite.sh`** — entrypoint script inside the container,
  supports individual suites (`unit`, `integration`, `security`, `contract`, `edge`)
  and the sequential pipeline (`seq`).
- **`backend/scripts/docker-test-entrypoint.sh`** — container entrypoint that
  wires the suite runner.

### Key Makefile targets

```bash
make dtest-seq   # sequential pipeline: unit→integration→security→contract→edge (fail-fast + combined coverage)
make dtest-cov   # dtest-seq + open HTML coverage report
make dtest-unit  # single suite
make dtest-up    # start support stack only
make dtest-down  # tear down support stack
```

## Date archived

2026-06-09
