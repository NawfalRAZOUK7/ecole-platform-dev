# Auth Feature Audit

École Platform authentication and authorization capabilities assessment.

## Implemented Features

### Core Authentication

- **Login (POST /auth/login)**
  - Username/password authentication
  - JWT access token (short-lived)
  - HttpOnly/Secure/SameSite=Lax refresh token cookie
  - CSRF token cookie (double-submit pattern)
  - Device info capture (user_agent, device_name, ip_address)
  - Session creation in Redis
  - Login history tracking (90 days retention)
  - Supports 2FA flow (returns temp_token if 2FA enabled)

- **Token Refresh (POST /auth/refresh)**
  - Refresh access token using refresh cookie
  - CSRF token validation
  - Token rotation (old refresh token invalidated)
  - IP address tracking

- **Logout (POST /auth/logout)**
  - Revoke current session
  - Clear auth cookies
  - Idempotent (safe to call multiple times)

- **Current User (GET /auth/me)**
  - Return authenticated user profile
  - Include permissions and memberships
  - RBAC UI gating source of truth

- **Registration (POST /auth/register)**
  - Invitation-code based registration
  - Creates user + membership + role-specific profile in one transaction
  - Returns JWT tokens (immediate login)
  - Rate limited: 5 registrations per 15 minutes per IP
  - Triggers email verification OTP send

### Session Management

- **List Sessions (GET /auth/sessions)**
  - List all active sessions for authenticated user
  - Returns session_id, source, user_agent, ip_address, device_name, created_at, last_active

- **Revoke Session (DELETE /auth/sessions/{session_id})**
  - Revoke specific session by ID
  - Users can revoke their own sessions
  - ADM can revoke any session in the school
  - Invalidates refresh token and clears from Redis

- **Login History (GET /auth/login-history)**
  - Paginated login history (last 90 days)
  - Cursor-based pagination
  - Includes IP address, user_agent, timestamp

### Password Management

- **Change Password (POST /auth/change-password)**
  - Requires current password verification
  - Enforces password policy on new password
  - Revokes all other active sessions (keeps current session)

- **Password Policy**
  - Minimum 12 characters
  - At least 1 uppercase letter
  - At least 1 lowercase letter
  - At least 1 digit
  - At least 1 special character
  - Not in common passwords list (data/common_passwords.txt)
  - Must not contain user's name or email local part
  - Structured error messages for each failed rule

### Two-Factor Authentication (TOTP)

- **2FA Setup (POST /auth/2fa/setup)**
  - Generate new TOTP secret (base32, 32 bytes)
  - Return QR code provisioning URI (otpauth:// format)
  - 2FA not yet active until verified

- **2FA Verification (POST /auth/2fa/verify-setup)**
  - Verify first TOTP code to activate 2FA
  - Returns 10 single-use backup codes (shown once)
  - Backup codes are bcrypt-hashed for storage

- **2FA Disable (POST /auth/2fa/disable)**
  - Disable 2FA
  - Requires valid TOTP code or backup code

- **2FA Login (POST /auth/2fa/verify)**
  - Verify TOTP code during login flow
  - Called after login returns requires_2fa=true
  - Accepts temp_token + TOTP code (or backup code)
  - Returns full tokens on success

- **TOTP Implementation Details**
  - 6-digit codes
  - 30-second interval
  - ±1 step drift tolerance (clock skew allowance)
  - Backup codes: 10 codes, 8 alphanumeric chars each
  - Backup codes are single-use (consumed after use)

### Email Verification

- **Send Verification OTP (triggered on registration)**
  - Sends OTP to user's email
  - OTP stored in Redis with TTL
  - IP address tracking

- **Verify Email (POST /auth/verify-email)**
  - Verify email address via OTP
  - Transitions user from unverified to verified state

### Account Recovery

- **Request Recovery (POST /recovery/request)**
  - Start password recovery flow
  - Always returns 200 (no email enumeration)
  - Creates recovery request and generates OTP
  - OTP logged in dev environment

- **Verify Recovery OTP (POST /recovery/verify)**
  - Verify recovery OTP
  - Transitions status: pending -> verified
  - Lockout after 5 failed attempts (30-minute lock)

- **Reset Password (POST /recovery/reset)**
  - Reset user's password
  - Requires status=verified
  - Enforces password policy
  - Revokes all active sessions (force re-login)
  - State machine: pending -> verified -> reset (no backward transitions)

### Security Features

- **Rate Limiting**
  - Auth category: 5 registrations per 15 minutes per IP
  - Other endpoints may have additional rate limits

- **Session Security**
  - Refresh tokens stored in Redis
  - CSRF protection via double-submit cookie pattern
  - Session revocation capability
  - Device info tracking

- **Password Security**
  - Bcrypt hashing (configurable rounds)
  - Strong password policy
  - Common password blacklist
  - No password reuse enforcement (not implemented)

- **Email Security**
  - Email enumeration prevention (recovery always returns 200)
  - OTP-based verification (not link-based)

## Gaps / Missing Features

### Not Implemented

- **Password Reuse Policy**
  - Prevent users from reusing recent passwords
  - Password history tracking

- **Account Lockout on Failed Login**
  - Progressive lockout after N failed attempts
  - Currently only OTP verification has lockout (5 attempts)

- **Multi-Device 2FA Enforcement**
  - Require 2FA for all sessions once enabled
  - Currently 2FA is optional per-user

- **WebAuthn / Passkeys**
  - Passwordless authentication
  - Hardware key support

- **Social Login (OAuth)**
  - Google, Microsoft, Apple login
  - SAML SSO for schools

- **Phone Verification**
  - SMS-based 2FA (TOTP is currently app-based only)
  - Phone number verification

- **Account Deletion / Data Export**
  - GDPR right to be forgotten
  - GDPR right to data portability

- **Suspicious Activity Detection**
  - Alert on login from new location/device
  - Alert on multiple failed logins

- **Admin Password Reset**
  - Admin can force-reset user passwords without email
  - Currently users must use self-service recovery

## External Dependencies

### Required

- **Redis**
  - Session storage (refresh tokens, session data)
  - OTP storage (email verification, recovery)
  - Rate limiting
  - Caching

- **SMTP / Email Service**
  - Email delivery for verification OTPs
  - Email delivery for recovery OTPs
  - Currently using TestMail for dev, production SMTP required

- **Database (PostgreSQL)**
  - User, membership, session, login history storage
  - TOTP secrets and backup codes
  - Recovery requests

### Optional

- **Sentry**
  - Error tracking for auth failures
  - Performance monitoring for auth endpoints

- **Authenticator Apps (User-Provided)**
  - Google Authenticator, Authy, etc.
  - For TOTP 2FA

## Configuration Requirements

### Environment Variables

- `JWT_SECRET_KEY` - JWT signing key
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token TTL
- `SENTRY_DSN` - Sentry error tracking
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` - Email delivery
- `TESTMAIL_API_KEY`, `TESTMAIL_NAMESPACE` - TestMail for dev email testing

### Doppler Configs

- **dev** - Development secrets (TestMail, local SMTP, etc.)
- **stg_main** - Staging secrets (production SMTP, staging Sentry DSN)
- **prd_main** - Production secrets (production SMTP, production Sentry DSN)

## Testing Coverage

### Postman Collections

- `scenario_2fa.postman_collection.json` - Full 2FA flow test
- `scenario_email_recovery.postman_collection.json` - Password recovery with TestMail
- `scenario_sentry_testmail.postman_collection.json` - Sentry and TestMail validation

### Manual Testing

- Use `system-tests/chaos/curl/` scripts for load testing and rate limit validation
- Use `system-tests/chaos/requestly-rules.json` for chaos engineering (503, latency, etc.)

## Security Considerations

- **PII Gating**
  - Sentry PII disabled in production (send_default_pii=false)
  - Email addresses logged in dev only

- **Environment Tagging**
  - Sentry events tagged with APP_ENV (development, staging, production)
  - Separate DSNs per environment (backend, web, mobile)

- **Secrets Management**
  - All secrets stored in Doppler
  - No hardcoded secrets in code
  - Change logs tracked via Doppler

## Recommendations

### High Priority

1. **Implement Password Reuse Policy**
   - Track last 5-10 password hashes
   - Prevent reuse during password change

2. **Implement Account Lockout on Failed Login**
   - Progressive lockout (5 attempts = 15 min, 10 attempts = 1 hour)
   - Email notification on lockout

3. **Add Suspicious Activity Detection**
   - Alert on login from new country/region
   - Alert on login from new device type

### Medium Priority

4. **Add WebAuthn/Passkeys Support**
   - Passwordless authentication option
   - Hardware key support for high-security accounts

5. **Add Social Login (OAuth)**
   - Google, Microsoft, Apple login
   - Reduce friction for new users

6. **Add Phone Verification**
   - SMS-based 2FA alternative
   - Phone number verification for account recovery

### Low Priority

7. **Add Account Deletion / Data Export**
   - GDPR compliance
   - Right to be forgotten

8. **Add Admin Password Reset**
   - Admin can force-reset user passwords
   - Audit trail for admin actions
