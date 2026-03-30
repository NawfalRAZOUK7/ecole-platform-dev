# Domain Value Object Unit Tests

Pure, immutable value objects with built-in validation. No mocks, no database—just logic testing.

## Test Files

### test_grade.py - Moroccan 0-20 Grading System
Validates the Moroccan grading standard used across all academic operations.

**Grading Scale:**
- Valid range: 0 to 20 (inclusive)
- Precision: 2 decimal places (e.g., 15.75)
- Interpretation:
  - 18-20: Excellent (ممتاز)
  - 14-17: Good (جيد)
  - 10-13: Pass (مقبول)
  - 0-9: Fail (ضعيف)

**Key Tests:**
- Boundary values: 0, 20, 0.01, 19.99
- Invalid ranges: negative, > 20, invalid decimals
- Grade interpretation (letter grade mapping)
- Percentage conversion (grade × 5 = percentage)
- Immutability enforcement

**Example Test Pattern:**
```python
grade = Grade(value=15.5)
assert grade.value == Decimal("15.5")
assert grade.interpretation == GradeLevel.GOOD
assert grade.as_percentage() == Decimal("77.5")
```

### test_money.py - MAD (Moroccan Dirham) Currency
Type-safe monetary value handling with arithmetic operations.

**Specifications:**
- Currency: MAD (د.م.)
- Precision: 2 decimal places
- Exchange rate: Fixed in tests (1 MAD = 1 unit)
- Operations: Add, subtract, multiply, divide, comparison

**Key Tests:**
- Addition/subtraction of Money values
- Multiplication by scalar (e.g., price × quantity)
- Division operations
- Comparison operators (==, <, >, <=, >=)
- Negative amounts (refunds)
- Decimal precision preservation
- Currency mismatch exceptions

**Example Test Pattern:**
```python
amount1 = Money(amount=Decimal("100.00"), currency="MAD")
amount2 = Money(amount=Decimal("50.50"), currency="MAD")
total = amount1 + amount2
assert total.amount == Decimal("150.50")
```

### test_role_set.py - Set of Roles
Immutable set-like collection for managing user roles.

**Operations:**
- Membership testing (user in role_set)
- Union (combine role sets)
- Intersection (find common roles)
- Difference (roles in first but not second)
- Iteration
- String representation

**Key Tests:**
- Adding/removing roles
- Immutability (modifications create new sets)
- Role inheritance chains
- Empty role sets
- Duplicate handling

**Example Test Pattern:**
```python
teacher_roles = RoleSet({Role.TEACHER, Role.CONTENT_MGR})
admin_roles = RoleSet({Role.ADMIN, Role.CONTENT_MGR})

common = teacher_roles & admin_roles
assert common == RoleSet({Role.CONTENT_MGR})
```

### test_typed_id.py - Type-Safe Identifiers
Prevents ID mixing and ensures type safety across layers.

**Types:**
- `UserID` - User identifiers
- `SchoolID` - School identifiers
- `ClassID` - Class identifiers
- `CourseID` - Course identifiers
- And more...

**Key Tests:**
- UUID4 format validation
- Type mismatch exceptions (UserID ≠ SchoolID)
- Serialization to/from string
- Comparison operators
- JSON serialization compatibility
- Equality testing

**Example Test Pattern:**
```python
user_id = UserID(uuid4())
school_id = SchoolID(uuid4())

assert user_id != school_id  # Type-safe comparison
assert isinstance(user_id.value, UUID)
assert str(user_id) == user_id.value.hex
```

### test_value_object_additional.py - Supplementary Tests
Extended validation and edge case coverage.

**Coverage:**
- Multi-value objects (composite values)
- Comparison edge cases
- Serialization roundtrips
- Validation error messages
- Performance (immutable copy-on-write)

## Running Tests

```bash
# All domain tests
pytest backend/tests/unit/domain/

# Specific test file
pytest backend/tests/unit/domain/test_grade.py
pytest backend/tests/unit/domain/test_money.py
pytest backend/tests/unit/domain/test_role_set.py
pytest backend/tests/unit/domain/test_typed_id.py

# With coverage
pytest backend/tests/unit/domain/ --cov=backend.domain --cov-report=html

# Verbose
pytest backend/tests/unit/domain/ -vv
```

## Key Design Principles

1. **Immutability** - Once created, values cannot change
2. **Self-Validation** - Invalid values raise exceptions at creation
3. **Type Safety** - Each value object has distinct type
4. **Value Equality** - Two objects with same value are equal
5. **No Side Effects** - Operations return new objects without modification
6. **Serializable** - Values can convert to/from primitive types

## Moroccan Specificity

- **Grades**: 0-20 standard used in Moroccan schools
- **Currency**: MAD (Moroccan Dirham) for all financial operations
- **Phone**: +212 format (Moroccan country code)
- **Timezone**: Africa/Casablanca for all datetime operations
- **Language**: Fr/Ar name support (Moroccan bilingual education)

## Integration with Other Layers

These value objects are used in:
- **Service layer**: Business logic returns/accepts typed values
- **ORM models**: Fields store typed values
- **API responses**: Values serialized to JSON
- **Database**: Values persist as validated constraints
- **Unit tests**: Mocks use value objects directly

## Related Documentation

- Parent: `backend/tests/unit/README.md`
- Models: `backend/tests/unit/models/` for ORM integration
- Edge Cases: `backend/tests/edge/test_boundary_values.py` for Moroccan boundary testing
