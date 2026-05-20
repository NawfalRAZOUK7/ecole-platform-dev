# Postman Collections

API scenario collections for manual and automated testing.

## Files

### Full Smoke

- `ecole_platform_full.postman_collection.json` — Covers all major endpoints

### Domain Scenarios

- `scenario_academic_year_lifecycle.json` — Academic year CRUD
- `scenario_student_lifecycle.json` — Student enrollment and progress
- `scenario_teacher_workflow.json` — Teacher assignments and grading
- `scenario_parent_journey.json` — Parent feed, notifications, billing
- `scenario_admin_operations.json` — User and school management
- `scenario_billing_cycle.json` — Invoices, payments, fee structures
- `scenario_quiz_assessment_flow.json` — Quiz lifecycle
- `scenario_content_management.json` — CMS content operations
- `scenario_error_handling.json` — Error paths and validation
- `scenario_rbac_matrix.json` — Role permission boundaries
- `scenario_abac_policies.json` — Attribute-based policies
- `scenario_security_hardening.json` — Security boundary tests
- `scenario_direct_upload_flow.json` — Signed upload → scan → download
- `scenario_invoice_pdf_flow.json` — Invoice → PDF → redirect
- `scenario_program_enrollment_flow.json` — Program → eligibility → enrollment

### Auth Scenarios

- `scenario_register.postman_collection.json` — User registration with invitation code and email verification
- `scenario_session_management.postman_collection.json` — Session management (list, revoke, login history)
- `scenario_password_change.postman_collection.json` — Password change flow with verification
- `scenario_2fa.postman_collection.json` — Two-Factor Authentication (TOTP) flow
- `scenario_email_recovery.postman_collection.json` — Password recovery with TestMail verification

### Integration & Validation

- `scenario_chaos.postman_collection.json` — Chaos engineering (503, rate limit, latency, load)
- `scenario_sentry_testmail.postman_collection.json` — Sentry error/transaction capture and TestMail email delivery

### Environment Files

- `env_local.json` — Local development
- `env_staging.json` — Staging environment

### Fixtures

- `fixtures/sample-document.pdf` — Sample upload file

## Usage

```bash
# Full smoke
newman run ecole_platform_full.postman_collection.json -e env_local.json

# Single scenario
newman run scenario_billing_cycle.postman_collection.json -e env_local.json

# Run all scenario collections
system-tests/run_tests.sh --include-scenarios --allow-dev-db
```

## Environment Configuration

### Scenario Tests Environment

For scenario tests (2FA, email recovery, registration, session management, password change), use `env_scenarios.json`:

1. Copy the example file:

   ```bash
   cp system-tests/postman/env_scenarios.example.json system-tests/postman/env_scenarios.json
   ```

2. Configure the following variables:

   **Required for all tests:**
   - `base_url` - API base URL (default: `http://localhost:8000/api/v1`)
   - `school_id` - Test school UUID (default: `00000000-0000-4000-8000-000000000001`)
   - `email` - Test user email
   - `password` - Test user password

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
   - `otp` - OTP code received via email

   **Session management tests:**
   - `token` - JWT access token (obtained from login)
   - `session_id` - Session ID to revoke (obtained from GET /auth/sessions)

   **Password change tests:**
   - `new_password` - New password to set

   **Chaos tests:**
   - `webhook_secret` - Webhook signature secret for payment webhooks

### TestMail Setup

1. Sign up at https://testmail.app
2. Create a namespace (e.g., "ecole-platform-test")
3. Get your API key from the dashboard
4. Configure a test email address in your namespace
5. Update `testmail_api_key`, `testmail_namespace`, and `testmail_test_email` in `env_scenarios.json`
