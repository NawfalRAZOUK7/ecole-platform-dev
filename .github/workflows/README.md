# GitHub Actions CI/CD Workflows

Automated continuous integration and deployment workflows for Ecole Platform.

## Workflows

- **ci.yml** - Main backend/system pipeline: test matrices, migrations, security scans, Postman scenarios, cleanup, and k6 baseline jobs.
- **mobile-ci.yml** - Flutter mobile checks: dependency install, analyze, tests with coverage, and build validation.
- **web-ci.yml** - Web checks: install, lint/typecheck, architecture checks, tests, and build.
- **web-e2e.yml** - Browser end-to-end coverage for the web app.
- **architecture-check.yml** - Repository architecture compliance and import-boundary checks.
- **deploy-staging.yml** - Staging deployment workflow.
- **deploy-k8s.yml** - Kubernetes deployment workflow.
- **k8s-e2e.yml** - Kubernetes end-to-end validation workflow.
- **docs.yml** - Redoc API documentation generation and GitHub Pages deploy.
- **cleanup-images.yml** - Container image retention cleanup for ghcr.io.
- **dependabot-automerge.yml** - Automatic patch-version Dependabot merges.

These workflows ensure code quality, security, and automated deployment of the Ecole Platform.
