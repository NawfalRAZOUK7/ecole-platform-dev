# GitHub Actions CI/CD Workflows

Automated continuous integration and deployment workflows for Ecole Platform.

## Workflows

- **ci.yml** - Main CI pipeline: matrix testing across Python 3.12/3.13 and PostgreSQL 15/16/17; security scanning (Trivy, pip-audit, Bandit); migration safety validation
- **dependabot-automerge.yml** - Automatic merge of patch version dependency updates from Dependabot
- **cleanup-images.yml** - Automated cleanup of old container images from ghcr.io registry
- **docs.yml** - Generates Redoc API documentation and deploys to GitHub Pages

These workflows ensure code quality, security, and automated deployment of the Ecole Platform.
