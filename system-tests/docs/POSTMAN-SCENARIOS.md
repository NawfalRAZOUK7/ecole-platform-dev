# Scenario Test Setup Guide

This guide explains how to set up and configure the Postman scenario tests for the École Platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [TestMail Setup](#testmail-setup)
- [Test User Setup](#test-user-setup)
- [Invitation Code Generation](#invitation-code-generation)
- [Running Scenario Tests](#running-scenario-tests)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Node.js and npm installed (for Newman CLI)
- Backend services running (or use Docker Compose)

## Environment Configuration

### Step 1: Create Environment File

Copy the example environment file:

```bash
cp system-tests/postman/env_scenarios.example.json system-tests/postman/env_scenarios.json
```

### Step 2: Configure Required Variables

Edit `system-tests/postman/env_scenarios.json` with your configuration:

**Required for all tests:**
- `base_url` - API base URL (default: `http://localhost:8000/api/v1`)
- `school_id` - Test school UUID (default: `00000000-0000-4000-8000-000000000001`)
- `email` - Test user email (default: `admin@ecole-benani.ma`)
- `password` - Test user password (default: `admin123`)

**2FA tests:**
- `totp_code` - 6-digit TOTP code from your authenticator app

**Email recovery tests:**
- `testmail_api_key` - TestMail API key (get from https://testmail.app)
- `testmail_namespace` - TestMail namespace for your test emails
- `testmail_test_email` - Test email address configured in TestMail

**Registration tests:**
- `invite_code` - Invitation code (generate via POST /invites/create with admin token)
- `new_user_email` - Email for new user registration
- `new_user_password` - Password for new user registration

**Session management tests:**
- `token` - JWT token (automatically set during login)

## TestMail Setup

TestMail is a disposable email testing service that allows you to receive emails during testing.

### Step 1: Get TestMail API Key

1. Go to https://testmail.app
2. Sign up for a free account
3. Navigate to the API section
4. Copy your API key

### Step 2: Configure TestMail Namespace

1. In TestMail, create a namespace (e.g., `ibatt`)
2. Note down your namespace name

### Step 3: Configure Environment Variables

Add your TestMail credentials to `system-tests/postman/env_scenarios.json`:

```json
{
  "testmail_api_key": "your-api-key-here",
  "testmail_namespace": "your-namespace",
  "testmail_test_email": "test@your-namespace.testmail.app"
}
```

### Step 4: Verify TestMail Setup

Test your TestMail configuration:

```bash
curl "https://api.testmail.app/api/json?apikey=YOUR_API_KEY&namespace=YOUR_NAMESPACE"
```

You should see a JSON response with your email inbox.

## Test User Setup

### Step 1: Seed Test Data

If using Docker Compose, the test data is seeded automatically:

```bash
make up
```

Or manually seed the database:

```bash
cd backend
python -m app.seed
```

### Step 2: Verify Test Users

The seed script creates the following test users:

- **Admin**: `admin@ecole-benani.ma` / `admin123` (role: ADM)
- **Teacher**: `teacher1@ecole-benani.ma` / `teacher123` (role: TCH)
- **Parent**: `parent1@ecole-benani.ma` / `parent123` (role: PAR)
- **Student**: `student1@ecole-benani.ma` / `student123` (role: STD)

### Step 3: Create Additional Test Users

To create additional test users, use the registration flow with an invitation code (see below).

## Invitation Code Generation

### Step 1: Login as Admin

Get an admin token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecole-benani.ma","password":"admin123","school_id":"00000000-0000-4000-8000-000000000001"}'
```

Copy the `access_token` from the response.

### Step 2: Generate Invitation Code

Create an invitation code:

```bash
curl -X POST http://localhost:8000/api/v1/invites/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "email": "newuser@example.com",
    "role": "TCH",
    "school_id": "00000000-0000-4000-8000-000000000001"
  }'
```

Copy the `code` from the response and add it to your environment file.

## Running Scenario Tests

### Using Newman CLI

Run a specific scenario collection:

```bash
# Email recovery test
npx newman run system-tests/postman/scenario_email_recovery.postman_collection.json \
  -e system-tests/postman/env_scenarios.json

# 2FA test
npx newman run system-tests/postman/scenario_2fa.postman_collection.json \
  -e system-tests/postman/env_scenarios.json

# Session management test
npx newman run system-tests/postman/scenario_session_management.postman_collection.json \
  -e system-tests/postman/env_scenarios.json

# Password change test
npx newman run system-tests/postman/scenario_password_change.postman_collection.json \
  -e system-tests/postman/env_scenarios.json

# Registration test
npx newman run system-tests/postman/scenario_register.postman_collection.json \
  -e system-tests/postman/env_scenarios.json
```

### Using the Test Runner Script

Run all scenario tests:

```bash
system-tests/run_tests.sh --include-scenarios
```

Run a specific scenario:

```bash
system-tests/run_tests.sh --include-scenarios --scenario email_recovery
```

### Data-Driven Tests

Run multi-role login tests with CSV data:

```bash
npx newman run system-tests/postman/scenario_multi_role_login.postman_collection.json \
  -d system-tests/postman/data_users.csv \
  -e system-tests/postman/env_scenarios.json
```

### Edge Case Tests

Run edge case tests:

```bash
npx newman run system-tests/postman/scenario_edge_cases.postman_collection.json \
  -e system-tests/postman/env_scenarios.json
```

## Troubleshooting

### Issue: "401 Unauthorized" on login

**Solution:** Verify your test user credentials match the seeded data. Check the `email` and `password` in your environment file.

### Issue: "Invalid OTP" in email recovery test

**Solution:** In development mode, the OTP is returned in the API response. Ensure the backend is running with `APP_ENV=development`. The test should automatically extract the OTP from the response.

### Issue: TestMail not receiving emails

**Solution:** 
1. Verify your TestMail API key is correct
2. Check that your namespace is properly configured
3. Ensure the backend SMTP settings are correct (Mailhog on port 1025 for local testing)

### Issue: Invitation code expired

**Solution:** Generate a new invitation code using the admin token. Invitation codes have an expiration time.

### Issue: "Rate limit exceeded" errors

**Solution:** Clear the Redis rate limit cache:

```bash
docker exec ecole-redis redis-cli -a change-me-dev-redis FLUSHDB
```

### Issue: Database connection errors

**Solution:** Ensure the PostgreSQL service is running and the database has been seeded:

```bash
make up
cd backend
alembic upgrade head
python -m app.seed
```

### Issue: Port already in use

**Solution:** Check if the backend is already running on port 8000:

```bash
lsof -i :8000
```

Stop the existing process or use a different port in your environment file.

## Development Mode Notes

In development mode (`APP_ENV=development`), the backend returns the OTP directly in the API response for testing purposes. This allows you to test the email recovery flow without actually sending emails.

**Important:** This behavior is only enabled in development mode. In production, OTPs are sent via email and not returned in the response.
