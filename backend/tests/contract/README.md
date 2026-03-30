# Contract Tests

**18 tests** validating API contracts and database migration safety. Tests ensure API schemas remain consistent and migrations are reversible without data loss.

## Overview

- **Scope**: OpenAPI schema compliance, migration contracts, version compatibility
- **Approach**: Schema validation, backward compatibility checking, migration verification
- **Tools**: jsonschema for OpenAPI, alembic for migration testing
- **Goal**: Prevent breaking changes and data loss in deployments

## Test Files

### test_api_contracts.py - OpenAPI Schema Compliance
Validates API responses match OpenAPI specification.

**Coverage:**

1. **Schema Definition Validation**
   ```python
   async def test_openapi_schema_valid():
       # Load OpenAPI spec from spec file
       spec = load_openapi_spec("backend/docs/openapi.yaml")
       # Validate spec itself is well-formed
       validator = OpenAPIValidator(spec)
       assert validator.is_valid()
   ```

2. **Response Schema Matching**
   ```python
   async def test_get_school_response_schema(test_client):
       # Execute endpoint
       response = await test_client.get(f"/api/schools/{school_id}")
       # Validate response matches OpenAPI schema
       validate_response(
           response=response,
           operation_id="get_school",
           spec="backend/docs/openapi.yaml"
       )
   ```

3. **Request Validation**
   ```python
   async def test_create_school_request_validation(test_client):
       # Invalid request (missing required field)
       response = await test_client.post(
           "/api/schools",
           json={"address": "123 Main St"}  # Missing 'name'
       )
       assert response.status_code == 422  # Unprocessable Entity
       assert "name" in response.json()["detail"][0]["loc"]
   ```

4. **Endpoint Coverage**
   - Authentication: `/auth/login`, `/auth/logout`, `/auth/refresh`
   - Schools: `/schools`, `/schools/{id}`, `/schools/{id}/classes`
   - Grades: `/grades`, `/grades/{id}`, `/grades/bulk`
   - Billing: `/invoices`, `/payments`, `/subscriptions`
   - Attendance: `/attendance`, `/attendance/analytics`
   - Communication: `/messages`, `/notifications`, `/announcements`

5. **Response Code Consistency**
   ```python
   async def test_http_status_codes(test_client):
       # Test typical status code patterns
       # Success
       response = await test_client.get(f"/api/schools/{school_id}")
       assert response.status_code == 200

       # Created
       response = await test_client.post(
           "/api/schools",
           json={"name": "New School", "phone": "+212612345678"}
       )
       assert response.status_code == 201

       # Bad Request
       response = await test_client.post(
           "/api/schools",
           json={"name": ""}  # Empty name invalid
       )
       assert response.status_code == 400

       # Not Found
       response = await test_client.get(f"/api/schools/{fake_uuid}")
       assert response.status_code == 404

       # Conflict
       response = await test_client.post(
           "/api/students",
           json=student_data  # Duplicate
       )
       assert response.status_code == 409
   ```

6. **Error Response Format**
   ```python
   async def test_error_response_format():
       response = await test_client.get(f"/api/schools/{invalid_id}")
       assert response.status_code == 404
       body = response.json()

       # Verify standard error fields
       assert "code" in body
       assert "message" in body
       assert "timestamp" in body
       assert "request_id" in body

       # Validate error code matches OpenAPI
       assert body["code"] in ["SCHOOL_NOT_FOUND", "INVALID_ID"]
   ```

7. **Data Type Validation**
   ```python
   async def test_response_data_types():
       response = await test_client.get(f"/api/schools/{school_id}")
       school = response.json()

       # Verify types match schema
       assert isinstance(school["id"], str)
       assert isinstance(school["name"], str)
       assert isinstance(school["phone"], str)  # +212 format
       assert isinstance(school["created_at"], str)  # ISO 8601
       assert isinstance(school["student_count"], int)
       assert isinstance(school["active"], bool)
   ```

### test_migration_contracts.py - Database Migration Safety
Validates migrations are reversible and preserve data integrity.

**Coverage:**

1. **Migration Executability**
   ```python
   async def test_migration_forward():
       # Start from known revision
       alembic_config = get_alembic_config()
       command.stamp(alembic_config, "abc123")  # Set to known revision

       # Apply new migration
       command.upgrade(alembic_config, "+1")

       # Verify migration succeeded
       current = command.current(alembic_config)
       assert current is not None
   ```

2. **Migration Reversibility**
   ```python
   async def test_migration_downgrade():
       # Forward
       command.upgrade(alembic_config, "+1")
       forward_revision = get_current_revision()

       # Backward
       command.downgrade(alembic_config, "-1")
       downgrade_revision = get_current_revision()

       # Verify reverted
       assert downgrade_revision == "previous_revision"
   ```

3. **Data Preservation**
   ```python
   async def test_migration_preserves_data():
       # Create test data before migration
       school = await create_test_school(session)
       school_id = school.id

       # Record data
       data_before = {
           "name": school.name,
           "phone": school.phone,
           "student_count": school.student_count
       }

       # Apply migration
       apply_migration("+1")

       # Verify data unchanged
       school_after = await fetch_school(session, school_id)
       assert school_after.name == data_before["name"]
       assert school_after.phone == data_before["phone"]
   ```

4. **Schema Constraints**
   ```python
   async def test_migration_enforces_constraints():
       # Apply migration that adds NOT NULL constraint
       apply_migration("+1")

       # Attempt to insert invalid data
       with pytest.raises(IntegrityError):
           await session.execute(
               insert(School).values(
                   id=uuid4(),
                   name=None  # Now NOT NULL
               )
           )
   ```

5. **Index Creation**
   ```python
   async def test_migration_creates_indices():
       # Apply migration that adds index
       apply_migration("+1")

       # Verify index exists
       indices = get_table_indices("schools")
       assert any(i["name"] == "idx_schools_phone" for i in indices)

       # Verify index speeds up queries
       start = time.time()
       await fetch_schools_by_phone(session, "+212612345678")
       duration = time.time() - start
       assert duration < 0.01  # Should be fast with index
   ```

6. **Foreign Key Integrity**
   ```python
   async def test_migration_maintains_foreign_keys():
       # Apply migration
       apply_migration("+1")

       # Create parent record
       school = await create_school(session, school_data)

       # Attempt to create orphaned child
       with pytest.raises(IntegrityError):
           await create_class(
               session,
               school_id=fake_uuid  # Non-existent school
           )
   ```

7. **Rollback Safety**
   ```python
   async def test_migration_rollback_on_failure():
       # Intentionally fail migration mid-way
       # (e.g., bad SQL, constraint violation)
       with pytest.raises(MigrationError):
           apply_migration_with_error("+1")

       # Database should be in original state
       current = get_current_revision()
       assert current != new_revision
   ```

8. **Concurrent Migration Safety**
   ```python
   async def test_migration_handles_concurrent_access():
       # One process applies migration
       # Another process attempts to read/write
       async with asyncio.TaskGroup() as tg:
           tg.create_task(apply_migration("+1"))
           tg.create_task(concurrent_database_access())
       # No deadlocks or data corruption
   ```

9. **Alembic Version Tracking**
   ```python
   async def test_alembic_version_consistency():
       # Verify alembic_version table accuracy
       current = get_current_revision()
       version_table = await fetch_alembic_version(session)
       assert version_table == current
   ```

## Contract Testing Patterns

### Schema Versioning
```python
async def test_api_version_compatibility():
    # Verify backward-compatible API versions
    # v1 endpoint should still work
    response_v1 = await test_client.get("/api/v1/schools")
    assert response_v1.status_code == 200

    # v2 endpoint with new fields
    response_v2 = await test_client.get("/api/v2/schools")
    assert response_v2.status_code == 200
    # v2 has additional fields
    assert "analytics" in response_v2.json()[0]
```

### Deprecation Warnings
```python
async def test_deprecated_endpoint_still_works():
    # Old endpoint should work but warn
    response = await test_client.get("/api/old/grades")
    assert response.status_code == 200
    assert "Deprecation" in response.headers
    assert response.headers["Deprecation"] == "true"
```

### Breaking Change Prevention
```python
async def test_breaking_changes_rejected():
    # Modified OpenAPI spec with removed field
    old_spec = load_openapi_spec("openapi.yaml")
    new_spec = load_openapi_spec("openapi.yaml.new")

    # Detect removed fields
    removed_fields = find_removed_fields(old_spec, new_spec)
    assert len(removed_fields) == 0, f"Breaking changes: {removed_fields}"
```

## Running Tests

```bash
# All contract tests
pytest backend/tests/contract/

# By file
pytest backend/tests/contract/test_api_contracts.py
pytest backend/tests/contract/test_migration_contracts.py -v

# Schema validation only
pytest backend/tests/contract/test_api_contracts.py -v

# Migration testing only
pytest backend/tests/contract/test_migration_contracts.py -v

# Check for breaking changes
pytest backend/tests/contract/ -k "breaking" -v
```

## OpenAPI Spec Location

- **Spec File**: `backend/docs/openapi.yaml`
- **Generation**: `poetry run python -m backend.docs.generate_spec`
- **Validation**: `poetry run python -m backend.docs.validate_spec`

## Alembic Migrations

- **Migrations Dir**: `backend/alembic/versions/`
- **Apply**: `alembic upgrade head`
- **Rollback**: `alembic downgrade -1`
- **Verify**: `alembic current` and `alembic history`

## Coverage Goals

- **API Contracts**: All public endpoints documented
- **Migrations**: All schema changes tested forward/backward
- **Breaking Changes**: Detected and prevented
- **Compatibility**: Old clients continue to work

## CI/CD Integration

- Run on every commit (quick validation)
- Full migration test suite on release builds
- Schema drift detection in PR reviews
- Backward compatibility checks before merge

## Related Documentation

- Parent: `backend/tests/README.md`
- Factories: `backend/tests/factories/README.md`
- API: `backend/tests/integration/api/README.md`
- OpenAPI: `backend/docs/openapi.yaml`
- Migrations: `backend/alembic/versions/`
