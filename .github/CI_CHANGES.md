# CI/CD changes — advanced refactor (2026-06)

> ⚠️ **These workflow changes have NOT been executed.** They are YAML-valid and
> logically reviewed, but GitHub Actions semantics (composite-action resolution,
> `fromJson` dynamic matrix, artifact wiring) can only be fully confirmed by a
> real run. **Validate on a throwaway branch (or with [`act`](https://github.com/nektos/act)) before relying on them.**

## 1. Composite actions (DRY — no more repeated setup blocks)

- `.github/actions/setup-backend` — Python + pip cache + install a requirements
  file. Inputs: `python-version` (default 3.12), `requirements`
  (default `requirements-test.txt`), `working-directory` (default `backend`).
- `.github/actions/setup-node-app` — Node + built-in npm cache + `npm ci`.
  Inputs: `node-version` (default 22), `working-directory` (default `web`).

Applied in **7 backend jobs** (lint, unit, integration, contract, security-tests,
coverage-report, security-audit) and **all 4 web-ci jobs**. Jobs that install
extra tooling (newman, k6…) were intentionally left untouched.

## 2. Matrix-of-matrix — dynamic integration fan-out

`integration-tests` no longer runs the whole API suite once per `py × pg` combo.
Instead:

- a new **`discover-suites`** job enumerates `tests/integration/api/*` and emits a
  JSON matrix (`outputs.combos`) — so the matrix never drifts from the filesystem;
- `integration-tests` consumes it via `matrix: { include: ${{ fromJson(...) }} }`:
  - **one job per API suite** on the primary interpreter/DB (Py 3.12 / PG 17) →
    fast, pinpointed per-domain feedback;
  - **3 cross-version "full suite" compat combos** (3.13/17, 3.12/15, 3.13/16).

Coverage still aggregates correctly: each job uploads
`coverage-data-integration-<suite>-py<py>-pg<pg>`, which the `coverage-report`
job already collects via `pattern: coverage-data-*` + `coverage combine`.

> Trade-off: more parallel jobs (≈18 vs 6) → faster wall-clock, more runner
> minutes. To reduce cost, trim the compat list in `discover-suites`.

## 3. Hardening (all 11 workflows)

- **Concurrency**: cancel superseded runs on CI/test workflows
  (`cancel-in-progress: true`); **serialize** deploy/cleanup/docs
  (`cancel-in-progress: false`) so deployments are never interrupted.
- **Least-privilege**: top-level `permissions: contents: read`; jobs that publish
  images / deploy / comment keep their explicit elevated grants.
- **Timeouts**: every job has `timeout-minutes: 45` (default was 6 h).
- **Pinned** `aquasecurity/trivy-action@master` → `@0.28.0`.

## 4. Run it locally

The root `Makefile` already mirrors CI (`test-unit`, `test-integration`,
`lint`, `format`, `test-security`). Added:

- `make ci-local` — the core gate (ruff lint+format, OpenAPI drift, single
  alembic head, unit tests) before pushing.
- `make test-integration-suite SUITE=onboarding` — run one integration suite,
  mirroring the CI matrix fan-out.

## First-run checklist (on a branch)

1. Push to a branch; confirm `discover-suites` prints a valid `combos=[…]` and the
   `integration-tests` matrix expands to one job per suite + compat combos.
2. Confirm the composite actions resolve (the `./.github/actions/...` path
   requires the repo to be checked out — `actions/checkout` runs first in every
   job, so this holds).
3. Confirm `coverage-report` still combines all `coverage-data-*` artifacts.
