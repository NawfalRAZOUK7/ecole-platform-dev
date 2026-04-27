# Step 3 — Security Analysis

## 3.1 Security Architecture Overview

The platform implements a **defense-in-depth** security model with 6 layers, ordered from outermost to innermost:

```
Layer 1: Network (CORS, Rate Limiting, Idempotency)
Layer 2: Authentication (JWT access/refresh, 2FA/TOTP)
Layer 3: Authorization — RBAC (Role-Based Access Control)
Layer 4: Authorization — ABAC (Attribute-Based Access Control)
Layer 5: Data Isolation (School-scoped queries, multi-tenancy)
Layer 6: Audit (Append-only audit log, correlation tracking)
```

The security pipeline is explicitly documented in `dependencies.py` as: **AuthN → Context/Scope → RBAC → ABAC → INV → Audit → Events**. The deny ordering follows: **401 → 404 (masking) → 403**, deliberately returning 404 instead of 403 for scope violations to prevent information leakage.

---

## 3.2 Authentication Flow

### 3.2.1 JWT Token Architecture (`core/security.py`)

Two token types with different lifetimes and storage strategies:

**Access Token** (short-lived):
- Lifetime: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Storage: **in-memory only** on both web (JavaScript variable) and mobile (Riverpod state)
- Claims: `sub` (user_id), `role`, `school_id`, `session_id`, `exp`, `iat`, `jti` (unique ID), `type: "access"`
- Algorithm: HS256 (HMAC-SHA256)
- Transport: `Authorization: Bearer <token>` header

**Refresh Token** (long-lived):
- Lifetime: 2 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Storage: **HttpOnly cookie** (web) / **Flutter Secure Storage** (mobile)
- Claims: same as access but `type: "refresh"` and longer `exp`
- Returns `(token_string, jti)` — the `jti` is stored in Redis for rotation tracking
- Transport: HttpOnly/Secure/SameSite=Lax cookie

**Design rationale**: Storing the access token only in memory (never in localStorage) prevents XSS attacks from stealing it. The refresh token in an HttpOnly cookie prevents JavaScript access, limiting the attack surface to CSRF (which is separately mitigated by the CSRF double-submit cookie pattern).

### 3.2.2 JWT Key Rotation

The system supports **zero-downtime key rotation** via `jwt_previous_key`:
```python
def _decode_jwt(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, ...)
    except JWTError:
        if settings.jwt_previous_key:
            return jwt.decode(token, settings.jwt_previous_key, ...)
```
During rotation, both the current and previous key are accepted, allowing existing tokens to remain valid while new tokens use the new key.

### 3.2.3 Session Management

Each login creates a `Session` row in the database with:
- `user_agent`, `ip_address`, `device_name` — device fingerprinting
- `revoke_at` — NULL means active; set on logout/revocation
- `impersonator_id` — for admin impersonation support
- `correlation_id` — links the session to the originating request

**Session limits**: `max_sessions_per_user = 5` — oldest sessions are revoked when the limit is exceeded, preventing session accumulation.

**Session verification on every request**: The `get_current_user` dependency not only decodes the JWT but also queries the database to verify the session is still active (`revoke_at IS NULL`), providing immediate revocation capability.

### 3.2.4 Token Refresh Flow

Web client (`api/client.ts`):
1. API returns 401
2. Client calls `POST /auth/refresh` with HttpOnly cookie (includes CSRF token)
3. **Concurrent refresh deduplication**: `refreshPromise` singleton ensures only one refresh request is in flight
4. On success: new access token stored in memory, original request retried
5. On failure: user redirected to login

Mobile client (`api_client.dart`) mirrors this with Dio interceptors.

### 3.2.5 CSRF Protection

Double-submit cookie pattern:
- `create_csrf_token()` generates UUID v4
- CSRF token sent as cookie AND expected in `X-CSRF-Token` header
- Server compares both values — attacker cannot read the cookie to forge the header

---

## 3.3 Two-Factor Authentication (`core/totp.py`)

### 3.3.1 TOTP Implementation

Standard TOTP (RFC 6238) using `pyotp`:
- Secret: 32-byte base32-encoded random string
- Parameters: 6 digits, 30-second interval
- Drift tolerance: ±1 step (accepts codes from 0-60 seconds ago)
- Provisioning: `otpauth://` URI format for QR code scanning

### 3.3.2 Backup Codes

For recovery when authenticator is unavailable:
- 10 codes generated, each 8 characters (uppercase alphanumeric)
- Stored as **bcrypt hashes** (rounds=10) — plaintext shown to user once
- Single-use: consumed code is removed from the list
- Verification iterates all hashes (O(n) bcrypt comparisons — acceptable for n=10)

### 3.3.3 2FA Login Flow

1. User submits email + password → server validates credentials
2. If `totp_enabled`: server returns `temp_token` (not a full access token)
3. Client shows 2FA input
4. User submits TOTP code with `temp_token`
5. Server verifies code against stored secret
6. On success: full access + refresh tokens issued
7. Alternative: backup code verification if TOTP unavailable

---

## 3.4 RBAC — Role-Based Access Control (`core/permissions.py`)

### 3.4.1 Role Hierarchy

9 roles with a hierarchical inheritance chain:

```
SYS (System) → inherits SUP
  SUP (Super-admin) → inherits ADM
    ADM (Admin) → inherits DIR
      DIR (Director) → inherits TCH
        TCH (Teacher)
EDUCATOR (standalone — micro-school)
PAR (Parent)
STD (Student)
CONTENT_MGR (standalone — platform content)
PUBLIC (pseudo-role — unauthenticated)
```

The hierarchy means DIR automatically gets all TCH permissions, ADM gets all DIR+TCH permissions, etc. This is computed at runtime via `get_effective_permissions()` with circular dependency detection.

### 3.4.2 Permission Catalog

**140+ permission codes** organized by domain using format `PERM-{DOMAIN}:{resource}:{action}`:
- **IAM**: 14 permissions (session CRUD, invite, recovery, parent links, login history)
- **Admin**: 14 permissions (dashboard, users, audit, school settings, impersonation)
- **ERP**: 16 permissions (classes, enrollment, attendance, timetable)
- **LMS**: 22 permissions (courses, assignments, submissions, grades, content, rubrics, gradebook)
- **Billing**: 18 permissions (invoices, payments, fees, plans, discounts)
- **Communication**: 10 permissions (notifications, messaging, announcements, consent)
- **CMS**: 8 permissions (content create/publish/manage/review)
- **Quiz**: 6 permissions (create, manage, publish, attempt, analytics)
- **Documents**: 12 permissions (upload, read, delete, resources, bulk operations)
- **Budget**: 10 permissions (create, allocate, approve, transactions)
- **Skills**: 8 permissions (dimensions, milestones, progress, passport)
- **Compliance**: 7 permissions (curriculum, mappings, reports)
- **Sync**: 8 permissions (devices, push, pull, conflicts)
- **Financial Health**: 6 permissions (retention, cashflow, cost, snapshots)
- **Reporting**: 6 permissions (reports, analytics, exports, schedules)
- **Calendar**: 7 permissions (events, holidays, RSVPs)

### 3.4.3 Permission Enforcement

Implemented as composable FastAPI dependencies:

```python
# Role-based (strict role check)
@router.get("/admin", dependencies=[Depends(RequiresRole("ADM", "DIR"))])

# Permission-based (checks permission with hierarchy)
@router.post("/grades", dependencies=[Depends(RequiresPermission("PERM-LMS:submission:grade"))])

# Any-of (OR logic)
@router.get("/reports", dependencies=[Depends(RequiresAnyPermission("PERM-REP:report:read", "PERM-REP:analytics:read"))])
```

**Design decision**: Permissions are checked **after** AuthN but **before** ABAC. This order means the system first confirms the user's identity, then checks role-level access, then validates attribute-level access (school boundary, parent-child, teacher-class). This prevents unauthorized users from triggering expensive ABAC database queries.

---

## 3.5 ABAC — Attribute-Based Access Control

Three ABAC guard types, all implemented in `core/dependencies.py`:

### 3.5.1 School Boundary Guard

```python
def verify_school_boundary(resource_school_id: UUID, auth: AuthContext) -> None:
    if resource_school_id != auth.school_id:
        raise NotFoundError(...)  # 404, NOT 403
```

**Returns 404 (scope masking)** instead of 403 to prevent cross-tenant information leakage. An attacker cannot distinguish "this resource exists but I don't have access" from "this resource doesn't exist."

### 3.5.2 Parent-Child Ownership Guard

```python
async def get_parent_child_ids(parent_user_id, school_id, db) -> set[UUID]:
    # Queries parent_child_links table for active links
    
def verify_parent_child_ownership(child_id, allowed_child_ids) -> None:
    if child_id not in allowed_child_ids:
        raise NotFoundError(...)  # 404 masking
```

Parents can ONLY access data for children explicitly linked to them. The `parent_child_links` table with `status = 'active'` filter ensures revoked links immediately remove access.

### 3.5.3 Teacher-Class Assignment Guard

```python
async def get_teacher_class_ids(teacher_user_id, school_id, db) -> set[UUID]:
    # Queries teacher_assignments table
    
def verify_teacher_assignment(class_id, allowed_class_ids) -> None:
    if class_id not in allowed_class_ids:
        raise NotFoundError(...)  # 404 masking
```

Teachers can only access classes they are assigned to. This prevents a teacher from viewing another teacher's class data.

### 3.5.4 Generic Owner Scope Filter (`core/abac.py`)

```python
def apply_owner_scope(query, auth, owner_field, teacher_field, ...):
    if auth.role in admin_roles: return query  # ADM/DIR/SUP see all
    if auth.role == "TCH": return query.filter_by(teacher_id=auth.user_id)
    if auth.role == "PAR": return query.filter_by(parent_id=auth.user_id)
    if auth.role == "STD": return query.filter_by(student_id=auth.user_id)
```

This reusable filter applies role-specific data scoping to any query, ensuring users only see their own data.

---

## 3.6 Password Security (`core/password_policy.py`)

### 3.6.1 Password Policy

8 validation rules enforced at registration and password change:

1. **Minimum 12 characters** (exceeds NIST 800-63 recommendation of 8)
2. **At least 1 uppercase letter**
3. **At least 1 lowercase letter**
4. **At least 1 digit**
5. **At least 1 special character** (`!@#$%^&*()_+-=[]{}...`)
6. **Not in common passwords list** — loaded from `data/common_passwords.txt` with normalization (strips case, punctuation, trailing digits to catch `Password1234!` variants)
7. **Must not contain email local part** (3+ char match)
8. **Must not contain parts of user's name** (3+ char match)

### 3.6.2 Password Hashing

bcrypt with **12 rounds** (`bcrypt.gensalt(rounds=12)`). At 12 rounds, each hash takes ~250ms, providing strong brute-force resistance while remaining acceptable for login latency.

### 3.6.3 Why These Choices

- **bcrypt over SHA/PBKDF2**: bcrypt is GPU-resistant by design (memory-hard), making hardware acceleration attacks less effective
- **12 rounds**: balances security (2^12 iterations) with user-facing latency
- **Common password list**: prevents users from choosing known-compromised passwords
- **Personal information check**: prevents trivially guessable passwords based on account details

---

## 3.7 Rate Limiting (`core/rate_limit.py`)

Redis-backed sliding window with three categories:

| Category | Limit | Window | Applied to |
|----------|-------|--------|-----------|
| `auth` | 5 requests | 15 minutes | Login, register, refresh, 2FA verify, recovery |
| `write` | 30 requests | 1 minute | POST, PUT, PATCH, DELETE |
| `read` | 100 requests | 1 minute | GET, HEAD, OPTIONS |

Response headers on all requests:
- `X-RateLimit-Limit` — maximum allowed
- `X-RateLimit-Remaining` — remaining in window
- `X-RateLimit-Reset` — Unix timestamp when window resets

**Auth rate limiting** is intentionally strict (5/15min) to prevent brute-force login attempts. The `enable_strict_rate_limit` flag allows tighter enforcement in production/staging.

---

## 3.8 Audit Trail (`services/audit.py` + `models/audit.py`)

### 3.8.1 Audit Log Structure

Append-only table (`audit_logs`) recording:
- `actor_id` — who performed the action (NULL only for SYS-originated events)
- `action_type` — what was done (e.g., `user.login`, `grade.publish`, `payment.create`)
- `target_type` + `target_id` — what was affected
- `entity_before` / `entity_after` — JSONB state snapshots (before/after)
- `outcome` — success or denied
- `error_code` — if denied, which error
- `correlation_id` — links to the request for end-to-end tracing
- `ip_address` — request origin

### 3.8.2 Audit Triggers

- All **401/403/404 (scope-masked)** responses
- Sensitive allow events: payment state changes, support access grants, AI requests
- User lifecycle: registration, login, logout, password change, 2FA enable/disable
- Data mutations: create, update, delete on sensitive entities

### 3.8.3 Login History

Separate `login_history` table tracks:
- All login attempts (successful and failed) with `success` boolean
- `failure_reason` for failed attempts
- `device_fingerprint` for device identification
- `is_new_device` flag for new device detection (triggers `NewDeviceLogin` domain event → email notification)
- `city`, `country` for geo-location context

---

## 3.9 API Protection Mechanisms

### 3.9.1 CORS Configuration

```python
CORSMiddleware(
    allow_origins=settings.cors_origins_list,  # ["http://localhost:5173", "http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "X-Correlation-Id", "X-CSRF-Token", "Idempotency-Key", ...],
    expose_headers=["X-Correlation-Id", "X-RateLimit-*"],
)
```

### 3.9.2 Idempotency (`core/idempotency.py`)

`IdempotencyMiddleware` deduplicates POST/PUT/PATCH requests using `Idempotency-Key` header + Redis. This prevents duplicate payment processing, double enrollment, etc. when clients retry on network errors.

### 3.9.3 Correlation ID Tracking (`core/middleware.py`)

Every request gets a `X-Correlation-Id` (preserved from client or generated). Stored in `contextvars` for propagation to:
- All log messages
- Audit trail entries
- Error responses
- Outgoing service calls

This enables end-to-end request tracing across the entire system.

### 3.9.4 Structured Error Responses

All errors follow a uniform structure:
```json
{
  "error": {
    "code": "ERR-IAM-401",
    "message": "Invalid or expired access token",
    "category": "authn",
    "correlation_id": "uuid",
    "retryable": false,
    "details": null,
    "timestamp": "2026-04-25T12:00:00Z"
  }
}
```

10 error categories: `validation`, `authn`, `authz`, `conflict`, `external`, `system`, `rate_limit`, `network`, `not_found`, `policy`. Three-level exception hierarchy: generic → 500, DomainException → structured response, specific (AuthenticationError, AuthorizationError, NotFoundError, ConflictError, ValidationError, RateLimitError).

### 3.9.5 Input Validation

Pydantic v2 schemas validate all request bodies before they reach service logic. Validation errors are caught by `validation_exception_handler` and returned as structured 422 responses with per-field error details.

### 3.9.6 File Upload Security

- `max_file_size_mb = 25` (documents: 50MB)
- MIME type whitelist: PDF, Office documents, images, video, audio
- Optional virus scanning via ClamAV (`virus_scan_enabled`, `virus_scan_host`)
- Document storage abstraction (local/S3) with download TTL

### 3.9.7 Docker Secret Support

Sensitive configuration values support Docker secret files via `_FILE` suffix pattern:
```python
def _read_secret_file(env_name: str) -> str | None:
    file_path = os.getenv(f"{env_name}_FILE")  # e.g., DATABASE_URL_FILE
    return Path(file_path).read_text().strip()
```

This prevents secrets from appearing in environment variables, process listings, or Docker inspect output.

---

## 3.10 Client-Side Security

### 3.10.1 Web (`services/api/client.ts`)

- Access token in memory only (never localStorage/sessionStorage)
- Refresh token in HttpOnly cookie (JavaScript can't access)
- CSRF double-submit pattern
- Credentials: `include` on all requests
- Error messages mapped to i18n keys (no raw backend errors shown to users)

### 3.10.2 Mobile (`data/api/api_client.dart`)

- Tokens stored in **Flutter Secure Storage** (Keychain on iOS, Keystore on Android)
- Biometric authentication option (fingerprint/face)
- Certificate pinning capability via Dio interceptors
- Offline queue with encrypted local SQLite storage

---

## 3.11 GDPR Compliance

Implemented via `api/v1/gdpr.py`:
- Data export: user can request a complete export of their personal data
- Data deletion: right to be forgotten — cascade deletion with audit trail
- Consent management: per-category, per-channel opt-in/opt-out
- Notifications digest: `Africa/Casablanca` timezone awareness for Moroccan users
- Document retention: `document_deleted_retention_days = 30` soft-delete before permanent removal
