# scripts/ — Backend Utility Scripts

Development and operational utility scripts for managing the backend system.

## Directory Structure

```
scripts/
├── export_openapi.py         # Export OpenAPI 3.0 specification
├── validate_event_schema.py  # Validate domain event definitions
└── validate_migrations.py    # Check migration consistency
```

## export_openapi.py — OpenAPI Specification Export

Exports the OpenAPI 3.0 specification for documentation and code generation.

### Purpose

- Generate OpenAPI spec for GitHub Pages documentation
- Share API contract with frontend teams
- Use with Swagger/ReDoc for interactive docs
- Generate SDKs from specification
- API contract testing

### Usage

```bash
# Export to stdout
python scripts/export_openapi.py

# Export to file
python scripts/export_openapi.py --output openapi.json

# Export to docs folder (for GitHub Pages)
python scripts/export_openapi.py --output docs/openapi.json

# Include examples
python scripts/export_openapi.py --with-examples

# Pretty-print JSON
python scripts/export_openapi.py --pretty
```

### Output

Generates OpenAPI 3.0 JSON:

```json
{
  "openapi": "3.0.3",
  "info": {
    "title": "École Platform API",
    "version": "1.0.0",
    "description": "K-12 EdTech SaaS for Moroccan schools"
  },
  "servers": [
    {
      "url": "https://api.ecole.ma",
      "description": "Production"
    },
    {
      "url": "http://localhost:8000",
      "description": "Development"
    }
  ],
  "paths": {
    "/auth/login": {
      "post": {
        "tags": ["auth"],
        "summary": "Login user",
        "requestBody": { ... },
        "responses": {
          "200": {
            "description": "Successful login",
            "content": { ... }
          }
        }
      }
    },
    ...
  }
}
```

### Integration

```bash
# In CI/CD pipeline
python scripts/export_openapi.py --output ./docs/openapi.json
git add docs/openapi.json
git commit -m "docs: update OpenAPI spec"

# Before deployment
python scripts/export_openapi.py --validate

# In pre-commit hook
#!/bin/bash
python scripts/export_openapi.py > /tmp/openapi.json
if ! git diff --quiet /tmp/openapi.json docs/openapi.json; then
    echo "OpenAPI spec has changed. Update it."
    exit 1
fi
```

## validate_event_schema.py — Event Schema Validation

Validates domain event definitions for consistency.

### Purpose

- Check all events inherit from BaseEvent
- Verify required event fields present
- Ensure event handlers are registered
- Check event naming conventions
- Validate event metadata structure

### Usage

```bash
# Validate all domain events
python scripts/validate_event_schema.py

# Validate specific domain
python scripts/validate_event_schema.py --domain lms

# Show detailed validation report
python scripts/validate_event_schema.py --verbose

# Fix naming issues automatically
python scripts/validate_event_schema.py --fix
```

### Output

```
Event Schema Validation
=======================

Checking: app/domain/events/

✓ BaseEvent definition
  - Includes: id, aggregate_id, aggregate_type, timestamp, user_id, school_id

✓ auth.py (7 events)
  - UserRegisteredEvent
  - UserLoggedInEvent
  - PasswordResetRequestedEvent
  ...

✓ lms.py (12 events)
  - CourseCreatedEvent
  - AssignmentCreatedEvent
  ...

✓ billing.py (8 events)
  - InvoiceGeneratedEvent
  - InvoicePaidEvent
  ...

Checking: services/event_dispatcher.py

✓ Event handlers registered
  - UserRegisteredEvent → [EmailNotificationHandler, AuditLogHandler]
  - InvoiceGeneratedEvent → [InvoiceMetricsHandler, EmailNotificationHandler]
  ...

Summary
-------
Total events: 45
Events with handlers: 45
Unhandled events: 0
✓ All validations passed
```

### Validation Rules

1. **Naming** — Event names end with `Event`
2. **Inheritance** — All events inherit from BaseEvent
3. **Fields** — Required fields: aggregate_id, event_type, timestamp
4. **Handlers** — All events have at least one registered handler
5. **Metadata** — Event metadata is properly typed
6. **Documentation** — Events have docstrings

## validate_migrations.py — Migration Validation

Ensures database migrations are consistent and reversible.

### Purpose

- Verify migrations are in order
- Check for duplicate revision IDs
- Validate upgrade/downgrade functions
- Test migration reversibility
- Check dependencies

### Usage

```bash
# Validate all migrations
python scripts/validate_migrations.py

# Test migration reversibility
python scripts/validate_migrations.py --test-reversibility

# Simulate applying all migrations
python scripts/validate_migrations.py --simulate-upgrade

# Simulate reverting all migrations
python scripts/validate_migrations.py --simulate-downgrade

# Generate migration graph
python scripts/validate_migrations.py --graph > migrations.dot
dot -Tpng migrations.dot > migrations.png
```

### Output

```
Migration Validation Report
============================

Location: alembic/versions/

Revision Chain
--------------
✓ 001_initial_schema.py
  └─ 002_add_user_verification.py
     └─ 003_add_invoices.py
        └─ 004_add_courses.py
           └─ ... (31 more)
              └─ 034_add_feature_flags.py

Total migrations: 35
Revision IDs: Valid (all unique)

Upgrade/Downgrade Functions
----------------------------
✓ All migrations have upgrade()
✓ All migrations have downgrade()
✓ No migrations are marked as irreversible

Dependency Checks
-----------------
✓ All down_revision values are valid
✓ No circular dependencies
✓ No orphaned migrations

Simulating Migration Chain
---------------------------
Testing: 001 → 002 → ... → 035
✓ Forward direction: OK (passes all steps)
✓ Backward direction: OK (downgrade works)
✓ Idempotent: OK (upgrade then downgrade → original state)

Schema Validation
-----------------
✓ Schema matches models
✓ No missing migrations
✓ No extra tables/columns

Summary
-------
✓ All validations passed
Status: Ready for production
```

### Integration

```bash
# In pre-deployment checklist
python scripts/validate_migrations.py --test-reversibility
python scripts/validate_migrations.py --simulate-upgrade

# In pre-commit
#!/bin/bash
alembic_files=$(git diff --cached --name-only | grep 'alembic/versions/')
if [ -n "$alembic_files" ]; then
    python scripts/validate_migrations.py || exit 1
fi
```

## Common Workflows

### Before Deployment

```bash
# Validate everything
python scripts/validate_migrations.py --test-reversibility
python scripts/validate_event_schema.py --verbose
python scripts/export_openapi.py --validate

# Run tests
pytest tests/ -v --cov

# Check code quality
ruff check .
mypy app/
```

### Release Process

```bash
# Update OpenAPI spec
python scripts/export_openapi.py --output docs/openapi.json

# Tag version
git tag -a v1.2.0 -m "Release 1.2.0"

# Check migrations
python scripts/validate_migrations.py

# Commit & push
git commit -am "Release: version 1.2.0"
git push origin main v1.2.0
```

### Development Loop

```bash
# Create feature branch
git checkout -b feature/new-endpoint

# Add endpoint, service, schema
# ...

# Validate new event
python scripts/validate_event_schema.py

# Export updated OpenAPI
python scripts/export_openapi.py --output docs/openapi.json

# Run tests
pytest tests/ -v

# Commit
git add .
git commit -m "feat: add new endpoint"
```

## Next Steps

- See `app/main.py` for FastAPI app configuration
- See `alembic/` for migration management
- See `domain/events/` for event definitions
