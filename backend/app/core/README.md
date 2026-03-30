# core/ — Cross-Cutting Infrastructure

Foundational infrastructure services shared across the application. Handles authentication, authorization, database, caching, metrics, and other cross-domain concerns.

## Directory Structure

```
core/
├── config.py           # Pydantic settings (environment-driven config)
├── database.py         # Async SQLAlchemy engine, session factory
├── security.py         # JWT, password hashing, authentication context
├── permissions.py      # 166 RBAC permission constants (PERM-* codes)
├── abac.py            # Attribute-based access control rules
├── middleware.py      # CORS, request logging, error handling
├── rate_limit.py      # Per-user rate limiting via Redis
├── redis.py           # Redis client & connection pool
├── metrics.py         # Prometheus metrics & monitoring
├── business_metrics.py # KPI & analytics metrics
├── telemetry.py       # OpenTelemetry tracing & observability
├── exceptions.py      # Structured error definitions
├── dependencies.py    # FastAPI dependency injection contracts
├── response.py        # Standardized JSON response format
├── storage.py         # File upload/download handling
├── tasks.py           # Background job queue (arq integration)
├── totp.py            # 2FA time-based one-time passwords
├── password_policy.py # Password validation rules & constraints
├── idempotency.py     # Idempotent request handling (idempotency keys)
├── feature_flags.py   # Feature flag toggling & management
├── unit_of_work.py    # Transaction boundary pattern
├── ws_manager.py      # WebSocket connection management
├── db_routing.py      # Read replica routing strategy
├── filtering.py       # Dynamic query filter builders
├── search.py          # Full-text search implementation
└── request_utils.py   # HTTP request helper utilities
```

## Key Modules

### Authentication & Security

**security.py**
- JWT token generation & validation
- Password hashing (bcrypt)
- Session management
- Token refresh logic
- Current user dependency injection

**permissions.py**
- 166 permission constants (PERM-* format)
- Role-to-permission mapping (data-driven)
- Permission lookup by code
- Structured format: `PERM-{DOMAIN}:{resource}:{action}`

Example permissions:
```
PERM-LMS:course:create      # Teachers can create courses
PERM-LMS:course:view        # Students can view enrolled courses
PERM-IAM:user:manage        # Admins can manage users
PERM-BILLING:invoice:view   # Finance can view invoices
```

**abac.py**
- Attribute-based access control (beyond RBAC)
- Context-aware authorization
- Cross-tenant isolation
- Dynamic permission evaluation
- Resource-level access control

**totp.py**
- TOTP secret generation
- QR code generation for 2FA
- Time-based code verification
- Backup codes for account recovery

**password_policy.py**
- Password strength validation (length, complexity)
- Common password blacklist (`data/common_passwords.txt`)
- Password history enforcement
- Expiry policies

### Configuration

**config.py**
- Pydantic v2 settings management
- Environment variable loading
- Type-safe configuration with validation
- Settings categories:
  - Database (URL, pool size, timeout)
  - Redis (host, port, db)
  - JWT (secret, expiry, algorithms)
  - Email/SMS providers
  - File storage paths
  - CORS allowed origins
  - Feature flags
  - Logging level

### Database

**database.py**
- Async SQLAlchemy 2.0 engine factory
- Async session manager
- Connection pool configuration
- Lazy loading strategies
- Transaction management
- Database initialization

**db_routing.py**
- Read replica routing for scaling
- Write operations to primary
- Read operations to replicas
- Load balancing across replicas
- Fallback to primary if replica unavailable

**unit_of_work.py**
- Transaction boundary management
- Atomic operations across multiple repos
- Rollback on error
- Enables business transactions spanning services

### Caching & Async

**redis.py**
- Redis client initialization
- Connection pooling
- Pub/Sub for real-time messaging
- Cache operations (set, get, delete)
- Session storage
- Rate limit tracking

**tasks.py**
- Background job queue (arq)
- Job scheduling & retry logic
- Task monitoring & logging
- Integration with Prometheus

### Observability

**metrics.py**
- Prometheus metrics registration
- Request/response timing
- Error rate tracking
- Database query monitoring
- Cache hit/miss ratios
- Active connection count

**business_metrics.py**
- KPI computation (enrollment rates, graduation rates)
- Analytics metrics (course completion, attendance)
- Dashboard-ready metrics
- Aggregation across time periods

**telemetry.py**
- OpenTelemetry trace instrumentation
- Distributed tracing
- Span context propagation
- Integration with observability backends (Jaeger, DataDog, etc.)

### HTTP & Responses

**middleware.py**
- CORS middleware configuration
- Request logging & tracing
- Error handling & translation
- Security headers (HSTS, CSP, etc.)
- Request ID generation
- Response time tracking

**response.py**
- Standardized JSON response envelope
- Success/error response builders
- HTTP status code mapping
- Error detail inclusion
- Pagination wrapper

**request_utils.py**
- Request context extraction
- Client IP resolution (with proxy awareness)
- User agent parsing
- Request body helpers

### API Protection

**rate_limit.py**
- Per-user rate limiting via Redis
- Configurable quotas per role
- Sliding window algorithm
- Rate limit headers in responses
- Graceful degradation if Redis unavailable

**idempotency.py**
- Idempotency key tracking
- Duplicate request detection
- Cached response return
- Storage of idempotency keys

### Features & Flags

**feature_flags.py**
- Feature toggle management
- Per-user feature enablement
- Per-school feature control
- A/B testing support
- Kill switches for emergency disablement

### File Management

**storage.py**
- File upload handling
- File download serving
- Virus scanning integration
- Storage backend abstraction (S3, local filesystem)
- File metadata tracking
- Quota enforcement per user/school

### Error Handling

**exceptions.py**
- Custom exception hierarchy
- Structured error codes
- HTTP status mapping
- Serializable error details
- Audit-friendly error logging

Exception types:
- `AuthenticationError` (401)
- `PermissionDeniedError` (403)
- `ResourceNotFoundError` (404)
- `ValidationError` (422)
- `ConflictError` (409)
- `InternalError` (500)

### Dependency Injection

**dependencies.py**
- FastAPI `Depends()` contract definitions
- Current user injection
- Service instance creation
- Database session provision
- Rate limit quota access
- Permission context setup

Common dependencies:
```python
get_current_user()        # Verify JWT, return authenticated User
get_current_user_or_none() # Optional authentication
get_db_session()          # Async SQLAlchemy session
check_permission()        # Verify RBAC/ABAC rules
get_rate_limit()          # Check per-user quotas
```

### Querying

**filtering.py**
- Dynamic filter builder from query params
- Operator support (eq, ne, gt, lt, in, etc.)
- Type-safe column filtering
- SQL injection prevention

Example: `?filter=status:active,created_at:gte:2024-01-01`

**search.py**
- Full-text search implementation
- Query term parsing
- Database-specific search strategies (PostgreSQL FTS)
- Search result ranking

## Security Pipeline

Every protected endpoint follows this pipeline:

```
Request
  ↓
1. Validate input (Pydantic schema)
  ↓
2. Authentication (JWT verification) [security.py]
  ↓
3. Extract current user context [dependencies.py]
  ↓
4. RBAC permission check [permissions.py]
  ↓
5. ABAC context-aware check [abac.py]
  ↓
6. Check rate limit [rate_limit.py]
  ↓
7. Idempotency check [idempotency.py]
  ↓
8. Business logic execution [services/]
  ↓
9. Audit log event [audit.py in services/]
  ↓
10. Format response [response.py]
  ↓
Response
```

## Configuration Management

Load settings via environment variables:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/ecole

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=86400

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587

# Feature flags
FEATURE_AI_ASSISTANT=true
FEATURE_ADVANCED_ANALYTICS=false
```

## Testing Utilities

Core modules provide test helpers:
```python
from app.core.config import settings
from app.core.database import AsyncSession
from app.core.security import create_access_token

# Generate test JWT
token = create_access_token(user_id=1)

# Use test database
async with AsyncSession() as session:
    user = await session.get(User, 1)
```

## Integration Points

- **FastAPI app** — Middleware registration, settings, exception handlers
- **Router layer** — Dependency injection, permission checks
- **Service layer** — Audit events, background tasks
- **Repository layer** — Database engine, query tracing
- **Monitoring** — Prometheus metrics, OpenTelemetry traces

## Next Steps

- See `permissions.py` for RBAC rule catalog
- See `abac.py` for attribute-based controls
- See `exceptions.py` for error code definitions
- See `config.py` for available settings
- See middleware.py for request/response handling
