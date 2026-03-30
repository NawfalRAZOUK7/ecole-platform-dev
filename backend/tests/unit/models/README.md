# ORM Model Unit Tests

SQLAlchemy ORM model validation and behavior testing. Tests repr methods, field validators, helper properties, and computed attributes.

## Test Files

### test_repr.py - Model String Representation
Tests SQLAlchemy model __repr__ methods for debuggability and log output.

**Coverage:**
- Accurate attribute representation
- Handling of None/null values
- Circular reference detection (prevent infinite loops)
- Foreign key relationship display
- Sensitive data masking (passwords, tokens)
- String length limits for large objects

**Key Tests:**
- Simple model repr: `User(id=uuid, email='user@school.ma', role='TEACHER')`
- With relationships: `School(id=uuid, name='Lycée Al-Khansaa', director=User(...))`
- Masked sensitive fields: `User(..., password='***')`
- Large collections: Truncate to first 5 items
- Circular refs: Break cycles with reference IDs

**Example Test Pattern:**
```python
user = User(id=user_id, email="user@school.ma", password_hash="secret")
repr_str = repr(user)
assert "User(" in repr_str
assert "email=" in repr_str
assert "secret" not in repr_str  # Masked
```

### test_additional_repr.py - Extended Representation Tests
Complex object graph representation and performance considerations.

**Coverage:**
- Deep nesting (School > Class > Student > Grades)
- Large collections (100+ items in relationship)
- Mixed types (users, schools, courses in single repr)
- Performance (no N+1 queries during repr)
- Unicode handling (Arabic names with diacritics)
- Special characters in strings

**Example Scenarios:**
- School with 50 classes and 1000 students
- User with 20+ role assignments
- Complex queries returning mixed model types

### test_validators.py - Field Validation
ORM field-level validators for data integrity.

**Moroccan-Specific Validators:**
- **Phone**: `+212` format with 9 digits (e.g., +212 612345678)
- **Email**: Standard RFC 5322 with domain validation
- **Grade**: 0-20 range with decimal precision
- **Currency**: MAD amounts with 2-decimal precision
- **Enum Fields**: Valid choices from predefined sets
- **URL/URI**: Valid format for document links
- **Name Fields**: Allow Arabic, French, special chars

**Key Tests:**
- Valid inputs: Validation passes silently
- Invalid inputs: Specific ValidationError raised
- Edge cases: Boundary values, unicode, empty strings
- Moroccan specifics:
  - Phone: `+212612345678`, `+212 61 234 56 78` (both valid)
  - Grade: `0`, `20`, `15.75` (valid), `21`, `-1` (invalid)
  - Currency: `1000.00`, `0.01` (valid), `1000.001` (invalid precision)

**Example Test Pattern:**
```python
user = User(phone="+212612345678")  # Valid
user.validate()  # No exception

user = User(phone="+1612345678")  # Invalid (not +212)
with pytest.raises(ValidationError):
    user.validate()
```

### test_helper_properties.py - Computed Properties
Tests for dynamically computed attributes and methods.

**Properties Tested:**
- **Grade Interpretation**: Letter grade from numeric value
- **Age Calculation**: From birthdate to current date
- **Status Derivation**: Computed from multiple fields
- **Relationship Helpers**:
  - User's all classes (via teacher or student enrollment)
  - School's academic year (derived from dates)
  - Student's grade point average (computed from grades)
  - Course's completion percentage
- **Counts**: Students in class, assignments in course
- **Boolean Flags**: is_active, is_verified, is_admin

**Key Tests:**
- Correct calculations with sample data
- Edge cases (age at birthday, leap years)
- Timezone awareness (Africa/Casablanca)
- Relationship depth (nested includes)
- Caching behavior (properties computed once)
- Null handling (properties with missing dependencies)

**Example Test Pattern:**
```python
student = Student(birthdate=date(2010, 3, 15))
today = date(2026, 3, 30)
# Age property uses today's date context
assert student.age == 16

grades = [Grade(value=18), Grade(value=16), Grade(value=14)]
student.grades = grades
assert student.gpa == Decimal("16.00")  # Average
```

## Running Tests

```bash
# All model tests
pytest backend/tests/unit/models/

# Specific test file
pytest backend/tests/unit/models/test_repr.py
pytest backend/tests/unit/models/test_validators.py
pytest backend/tests/unit/models/test_helper_properties.py

# By keyword
pytest backend/tests/unit/models/ -k "phone" -v
pytest backend/tests/unit/models/ -k "grade" -v

# With coverage
pytest backend/tests/unit/models/ --cov=backend.models --cov-report=html
```

## Key ORM Patterns

1. **Validators** - Called in `__init__` and before flush
2. **Properties** - Lazy computed attributes
3. **Relationships** - Lazy-loaded by default
4. **Hooks** - `before_insert`, `before_update`, `after_load` events
5. **Constraints** - DB-level unique, check, foreign key constraints

## Moroccan Model Context

Models include Morocco-specific fields:
- User `phone`: +212 format
- Grade `value`: 0-20 scale
- Money `currency`: "MAD" constant
- User `locale`: "fr_MA" or "ar_MA"
- Calendar `timezone`: "Africa/Casablanca"

## Test Fixtures

From parent `conftest.py`:
- `db_session` - SQLAlchemy session (not used here, models are independent)
- Model factories for creating test instances
- Moroccan locale fixtures

## Related Documentation

- Parent: `backend/tests/unit/README.md`
- Domain: `backend/tests/unit/domain/` for value object tests
- Models: `backend/models/` for actual model implementations
- Integration: `backend/tests/integration/db/` for database tests
