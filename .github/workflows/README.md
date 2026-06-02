# GitHub Actions CI/CD Workflows

Automated validation and deployment workflows for Ecole Platform.

## Required PR Gates

- **ci.yml** - Umbrella backend/system coordinator. Runs backend lint/format, security scans, unit, integration, contract, security, security audit, Postman/Newman, k6, backend coverage aggregation, image publishing on `main`, and the final dual coverage summary.
- **web-ci.yml** - Primary web gate. Runs install, lint/typecheck, unit test matrix, web unit coverage, and production build.
- **mobile-ci.yml** - Primary mobile gate. Runs Flutter dependency install, analyze, unit tests with coverage, and iOS integration test matrix.
- **architecture-check.yml** - Web architecture/import-boundary checks only. Lint/typecheck/build remain in `web-ci.yml`.

## E2E, System, And Optional Workflows

- **web-e2e.yml** - Playwright browser E2E. Uploads Playwright reports and is behavioral coverage by default.
- **k8s-e2e.yml** - Kind-based Kubernetes E2E validation. Counts as behavioral/system coverage, not numeric code coverage.
- **deploy-k8s.yml** - Kubernetes deployment on `main` and `develop`. If `KUBE_CONFIG` is not configured, deploy steps are intentionally skipped with an Actions notice.
- **deploy-staging.yml** - Staging deployment workflow for `develop`.
- **docs.yml** - Redoc API documentation generation and GitHub Pages deploy.
- **cleanup-images.yml** - Scheduled/manual GHCR image retention cleanup.
- **dependabot-automerge.yml** - Automatic patch-version Dependabot merge helper.

## Trigger Rules

- `ci.yml` runs on pushes and pull requests targeting `main` or `develop`.
- `web-ci.yml` runs only when `web/**`, OpenAPI export files, or its workflow file changes.
- `mobile-ci.yml` runs only when `mobile/**` or its workflow file changes.
- `architecture-check.yml` runs on PRs to `main` when web or architecture workflow files change, and by manual dispatch.
- Deploy, docs, cleanup, and some E2E workflows may be branch-filtered, path-filtered, scheduled, or manual.

Skipped jobs are acceptable only when their branch/path/manual/secret conditions explain the skip. Unexpected required-gate skips are reported by the `CI Coordinator Summary` job in `ci.yml`.

## Coverage Model

- **Code coverage** is numeric coverage from instrumentation:
  - backend: `coverage.py` from unit, integration, contract, security, security-audit, and Postman API runtime tests;
  - web unit: Vitest V8 coverage;
  - mobile unit: Flutter `lcov.info`.
- **Behavioral test coverage** records which test families ran:
  - backend unit/integration/security/contract;
  - Postman full and scenario collections;
  - web unit shards and Playwright E2E;
  - mobile unit and integration files;
  - k6 and Kubernetes/system gates.

`ci.yml` uploads `test-coverage-summary.json` and `test-coverage-summary.md` to show both coverage types separately. K8s E2E and most E2E flows are behavioral coverage unless instrumented runtime coverage is explicitly added later.
