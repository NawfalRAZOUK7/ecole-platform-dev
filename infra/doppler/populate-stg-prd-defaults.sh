#!/usr/bin/env bash
# Populate Doppler stg_main and prd_main configs with safe defaults
# Run this after confirming the script contents match your requirements.
# All secrets are set to CHANGE_ME_* placeholders — you must replace them before deploying.

set -euo pipefail

# Add doppler to PATH (Homebrew on macOS)
export PATH="/opt/homebrew/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "=== Doppler Config Populate Script ==="
echo ""
echo "Populating stg_main and prd_main Doppler configs with:"
echo "  - Non-secret defaults (ports, sample rates, log levels, CORS, TZ, feature flags)"
echo "  - CHANGE_ME_* placeholders for actual secrets"
echo ""

# ============================================================================
# stg_main (Staging)
# ============================================================================

echo ""
echo "Populating stg_main config..."

doppler secrets set APP_ENV staging --config stg_main
doppler secrets set LOG_LEVEL INFO --config stg_main
doppler secrets set SENTRY_TRACES_SAMPLE_RATE 0.5 --config stg_main
doppler secrets set SENTRY_PROFILES_SAMPLE_RATE 0.1 --config stg_main
doppler secrets set ENABLE_TRACING true --config stg_main
doppler secrets set ENABLE_STRICT_RATE_LIMIT true --config stg_main
doppler secrets set CORS_ORIGINS "https://staging.ecole-platform.ma" --config stg_main
doppler secrets set TZ "Africa/Casablanca" --config stg_main
doppler secrets set STORAGE_BACKEND s3 --config stg_main
doppler secrets set S3_FORCE_PATH_STYLE false --config stg_main
doppler secrets set VIRUS_SCAN_ENABLED true --config stg_main

# Secrets — CHANGE_ME placeholders
doppler secrets set JWT_SECRET_KEY "CHANGE_ME_BEFORE_DEPLOY_OPENSSL_RAND_HEX_32" --config stg_main
doppler secrets set DATABASE_URL "CHANGE_ME_DATABASE_URL" --config stg_main
doppler secrets set REDIS_URL "CHANGE_ME_REDIS_URL" --config stg_main
doppler secrets set S3_ENDPOINT "CHANGE_ME_S3_ENDPOINT" --config stg_main
doppler secrets set S3_ACCESS_KEY "CHANGE_ME_S3_ACCESS_KEY" --config stg_main
doppler secrets set S3_SECRET_KEY "CHANGE_ME_S3_SECRET_KEY" --config stg_main
doppler secrets set S3_BUCKET "CHANGE_ME_S3_BUCKET" --config stg_main
doppler secrets set SMTP_HOST "CHANGE_ME_SMTP_HOST" --config stg_main
doppler secrets set SMTP_PORT "587" --config stg_main
doppler secrets set SMTP_USER "CHANGE_ME_SMTP_USER" --config stg_main
doppler secrets set SMTP_PASSWORD "CHANGE_ME_SMTP_PASSWORD" --config stg_main
doppler secrets set SMTP_FROM_EMAIL "CHANGE_ME_SMTP_FROM" --config stg_main
doppler secrets set SMTP_FROM_NAME "Ecole Platform Staging" --config stg_main
doppler secrets set SMTP_USE_TLS "true" --config stg_main
doppler secrets set SENTRY_DSN "CHANGE_ME_SENTRY_DSN_BACKEND" --config stg_main
doppler secrets set MOBILE_SENTRY_DSN "CHANGE_ME_SENTRY_DSN_MOBILE" --config stg_main
doppler secrets set VITE_SENTRY_DSN "CHANGE_ME_SENTRY_DSN_WEB" --config stg_main
doppler secrets set TESTMAIL_API_KEY "CHANGE_ME_TESTMAIL_API_KEY" --config stg_main
doppler secrets set TESTMAIL_NAMESPACE "CHANGE_ME_TESTMAIL_NAMESPACE" --config stg_main
# OAuth (Phase 10)
doppler secrets set GOOGLE_OAUTH_ENABLED "false" --config stg_main
doppler secrets set GOOGLE_OAUTH_CLIENT_ID "CHANGE_ME_GOOGLE_CLIENT_ID" --config stg_main
doppler secrets set GOOGLE_OAUTH_CLIENT_SECRET "CHANGE_ME_GOOGLE_CLIENT_SECRET" --config stg_main
doppler secrets set MICROSOFT_OAUTH_ENABLED "false" --config stg_main
doppler secrets set MICROSOFT_OAUTH_CLIENT_ID "CHANGE_ME_MICROSOFT_CLIENT_ID" --config stg_main
doppler secrets set MICROSOFT_OAUTH_CLIENT_SECRET "CHANGE_ME_MICROSOFT_CLIENT_SECRET" --config stg_main
# Mock OAuth / SMS (Phase 10 — Testing)
doppler secrets set MOCK_OAUTH_ENABLED "false" --config stg_main
doppler secrets set MOCK_OAUTH_BASE_URL "http://mock-oauth:9999" --config stg_main
doppler secrets set MOCK_SMS_ENABLED "false" --config stg_main

echo "✅ stg_main populated"

# ============================================================================
# prd_main (Production)
# ============================================================================

echo ""
echo "Populating prd_main config..."

doppler secrets set APP_ENV production --config prd_main
doppler secrets set LOG_LEVEL WARNING --config prd_main
doppler secrets set SENTRY_TRACES_SAMPLE_RATE 0.1 --config prd_main
doppler secrets set SENTRY_PROFILES_SAMPLE_RATE 0.05 --config prd_main
doppler secrets set ENABLE_TRACING true --config prd_main
doppler secrets set ENABLE_STRICT_RATE_LIMIT true --config prd_main
doppler secrets set CORS_ORIGINS "https://app.ecole-platform.ma,https://admin.ecole-platform.ma" --config prd_main
doppler secrets set TZ "Africa/Casablanca" --config prd_main
doppler secrets set STORAGE_BACKEND s3 --config prd_main
doppler secrets set S3_FORCE_PATH_STYLE false --config prd_main
doppler secrets set VIRUS_SCAN_ENABLED true --config prd_main

# Secrets — CHANGE_ME placeholders
doppler secrets set JWT_SECRET_KEY "CHANGE_ME_BEFORE_DEPLOY_OPENSSL_RAND_HEX_32" --config prd_main
doppler secrets set DATABASE_URL "CHANGE_ME_DATABASE_URL" --config prd_main
doppler secrets set REDIS_URL "CHANGE_ME_REDIS_URL" --config prd_main
doppler secrets set S3_ENDPOINT "CHANGE_ME_S3_ENDPOINT" --config prd_main
doppler secrets set S3_ACCESS_KEY "CHANGE_ME_S3_ACCESS_KEY" --config prd_main
doppler secrets set S3_SECRET_KEY "CHANGE_ME_S3_SECRET_KEY" --config prd_main
doppler secrets set S3_BUCKET "CHANGE_ME_S3_BUCKET" --config prd_main
doppler secrets set SMTP_HOST "CHANGE_ME_SMTP_HOST" --config prd_main
doppler secrets set SMTP_PORT "587" --config prd_main
doppler secrets set SMTP_USER "CHANGE_ME_SMTP_USER" --config prd_main
doppler secrets set SMTP_PASSWORD "CHANGE_ME_SMTP_PASSWORD" --config prd_main
doppler secrets set SMTP_FROM_EMAIL "CHANGE_ME_SMTP_FROM" --config prd_main
doppler secrets set SMTP_FROM_NAME "Ecole Platform" --config prd_main
doppler secrets set SMTP_USE_TLS "true" --config prd_main
doppler secrets set SENTRY_DSN "CHANGE_ME_SENTRY_DSN_BACKEND" --config prd_main
doppler secrets set MOBILE_SENTRY_DSN "CHANGE_ME_SENTRY_DSN_MOBILE" --config prd_main
doppler secrets set VITE_SENTRY_DSN "CHANGE_ME_SENTRY_DSN_WEB" --config prd_main
doppler secrets set TESTMAIL_API_KEY "CHANGE_ME_TESTMAIL_API_KEY" --config prd_main
doppler secrets set TESTMAIL_NAMESPACE "CHANGE_ME_TESTMAIL_NAMESPACE" --config prd_main
# OAuth (Phase 10)
doppler secrets set GOOGLE_OAUTH_ENABLED "false" --config prd_main
doppler secrets set GOOGLE_OAUTH_CLIENT_ID "CHANGE_ME_GOOGLE_CLIENT_ID" --config prd_main
doppler secrets set GOOGLE_OAUTH_CLIENT_SECRET "CHANGE_ME_GOOGLE_CLIENT_SECRET" --config prd_main
doppler secrets set MICROSOFT_OAUTH_ENABLED "false" --config prd_main
doppler secrets set MICROSOFT_OAUTH_CLIENT_ID "CHANGE_ME_MICROSOFT_CLIENT_ID" --config prd_main
doppler secrets set MICROSOFT_OAUTH_CLIENT_SECRET "CHANGE_ME_MICROSOFT_CLIENT_SECRET" --config prd_main
# Mock OAuth / SMS (Phase 10 — Testing)
doppler secrets set MOCK_OAUTH_ENABLED "false" --config prd_main
doppler secrets set MOCK_OAUTH_BASE_URL "http://mock-oauth:9999" --config prd_main
doppler secrets set MOCK_SMS_ENABLED "false" --config prd_main

echo "✅ prd_main populated"

# ============================================================================
# Verification
# ============================================================================

echo ""
echo "=== Verification ==="
echo ""
echo "stg_main secrets (names only):"
doppler secrets get --only-names --config stg_main | head -20
echo ""
echo "prd_main secrets (names only):"
doppler secrets get --only-names --config prd_main | head -20
echo ""
echo "=== Done ==="
echo ""
echo "Next steps:"
echo "1. Review the configs: doppler secrets get --only-names --config stg_main"
echo "2. Replace all CHANGE_ME_* values with actual secrets before deploying"
echo "3. For JWT_SECRET_KEY, generate with: openssl rand -hex 32"
