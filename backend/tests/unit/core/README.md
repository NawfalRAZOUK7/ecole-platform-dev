# Core Infrastructure Unit Tests

Tests for core system infrastructure: permission models, ABAC policy engine, and exception handling.

## Test Files

### test_abac.py - ABAC Policy Engine
Attribute-Based Access Control engine for fine-grained authorization.

**Coverage:**
- Policy evaluation with context attributes
- Effect resolution (Allow, Deny, Inherit)
- Resource-owner relationships (is parent of, teaches class)
- Temporal conditions (school calendar windows)
- Combining multiple policies
- Short-circuit evaluation (Deny always wins)

**Key Classes:**
- `ABACEngine` - Policy evaluation engine
- `ABACPolicy` - Single policy definition
- `ABACContext` - Request context with actor attributes

**Example Test Patterns:**
```python
# Policy: Parent can view child's grades
context = ABACContext(actor_id=parent.id, action="READ:GRADES")
assert engine.evaluate(context, resource=student)

# Deny takes precedence
context = ABACContext(actor_id=user.id, action="DELETE:ACCOUNT")
assert engine.evaluate(context, resource=self_account) == Deny()
```

### test_permissions.py - Permission Constants (166 permissions)
Catalog of all system permissions organized by domain.

**Permission Categories:**
- `AUTH_*` - Authentication operations (login, register, logout, MFA)
- `USER_*` - User management (read, create, update, delete, export)
- `SCHOOL_*` - School operations (manage, view, edit classes)
- `IAM_*` - Identity & Access Management (roles, permissions)
- `LMS_*` - Learning Management (courses, assignments, grades)
- `BILLING_*` - Billing operations (invoicing, payments, subscriptions)
- `COMMUNICATION_*` - Messaging, notifications, announcements
- `CALENDAR_*` - Calendar, events, scheduling
- `DOCUMENTS_*` - Document management, uploads, sharing
- `REPORTS_*` - Report generation, analytics, exports
- `AUDIT_*` - Audit logs, security events

**Key Assertions:**
- All permissions defined as string constants
- No duplicate permission codes
- Hierarchical permission naming (DOMAIN_RESOURCE_ACTION)
- Consistent casing (UPPER_SNAKE_CASE)

**Usage:**
```python
from backend.core.permissions import Permissions

assert user.has_permission(Permissions.SCHOOL_MANAGE)
assert user.has_permission(Permissions.LMS_GRADE_WRITE)
```

### test_exceptions_additional.py - Exception Hierarchy
Custom exception classes for domain-specific error handling.

**Exception Categories:**
- `AuthenticationError` - Login failures, invalid credentials
- `AuthorizationError` - Permission denied, insufficient privileges
- `ValidationError` - Input validation failures
- `NotFoundError` - Resource not found
- `ConflictError` - Resource already exists or state conflict
- `InternalServerError` - Unexpected application errors
- `ExternalServiceError` - Third-party API failures

**Key Tests:**
- Exception message formatting with context
- Exception chaining (from other exceptions)
- HTTP status code mapping
- Serialization to JSON error responses

**Example Test Pattern:**
```python
try:
    authenticate_user("invalid@school.ma", "wrong_password")
except AuthenticationError as e:
    assert e.code == "INVALID_CREDENTIALS"
    assert e.status_code == 401
```

## Running Tests

```bash
# All core infrastructure tests
pytest backend/tests/unit/core/

# Specific test file
pytest backend/tests/unit/core/test_abac.py
pytest backend/tests/unit/core/test_permissions.py
pytest backend/tests/unit/core/test_exceptions_additional.py

# With verbose output
pytest backend/tests/unit/core/ -vv

# With coverage
pytest backend/tests/unit/core/ --cov=backend.core --cov-report=html
```

## Key Testing Principles

1. **No Mocks for Domain Logic** - Test pure business logic without fixtures
2. **Isolation** - Core tests don't depend on external services
3. **Clarity** - Test names clearly state what policy/permission is tested
4. **Completeness** - All permission categories covered
5. **Edge Cases** - Test boundary conditions (empty context, missing attributes)

## Integration Points

- **Permission Checks** - Used in service layer authorization
- **ABAC Engine** - Used in request middleware for route-level authorization
- **Exception Handling** - Used in API error response middleware
- **Security Tests** - These core tests are validated in `security/` directory

## Related Documentation

- Parent: `backend/tests/unit/README.md`
- Security: `backend/tests/security/README.md` for full RBAC/ABAC validation
- Permissions: `backend/core/permissions.py` for permission definitions
