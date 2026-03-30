# Domain Value Objects

Immutable value objects implementing domain-specific types with built-in validation.

## Files

- **grade.py** — `Grade` value object enforcing Moroccan 0-20 scale with mention calculation (Très Bien, Bien, Assez Bien, Passable, Insuffisant)
- **money.py** — `Money` value object for MAD (Moroccan Dirham) with centimes precision and arithmetic operations
- **role_set.py** — `RoleSet` for managing combinations of the 8 system roles with hierarchy checks
- **typed_id.py** — Type-safe ID wrappers preventing ID type confusion (e.g., `UserId` vs `SchoolId`)

## Design

All value objects are frozen dataclasses — immutable after creation, compared by value (not identity), and self-validating on construction.
