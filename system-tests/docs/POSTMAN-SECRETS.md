# Secrets Documentation for Postman Tests

This document describes the secrets required for running the Postman scenario tests.

## Required Secrets

### TestMail API (for email verification tests)
- `testmail_api_key`: Your TestMail API key from https://testmail.app
- `testmail_namespace`: Your TestMail namespace (e.g., "ecole-platform-test")
- `testmail_test_email`: Your TestMail test email address (e.g., "test@ecole-platform.testmail.app")

### Webhook Secret (for webhook tests)
- `webhook_secret`: Your webhook secret for validating webhook signatures

## Environment Files

- `env_scenarios.example.json`: Example environment with placeholder values
- `env_scenarios.json`: Your actual environment file (not committed to git)
- `env_staging.json`: Staging environment file (not committed to git)
- `env_local.json`: Local environment file (not committed to git)

## Setting Up Secrets

1. Copy `env_scenarios.example.json` to `env_scenarios.json`
2. Replace placeholder values with your actual secrets
3. Do not commit `env_scenarios.json` to version control (it's in .gitignore)

## Security Notes

- Never commit actual API keys or secrets to version control
- Use environment-specific files for different environments
- Rotate secrets regularly
- Use Doppler or similar secret management service for CI/CD pipelines
