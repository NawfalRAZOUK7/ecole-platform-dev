# LMS Services

Learning Management System business logic, extracted into a dedicated subpackage for clarity.

## Files

- **_helpers.py** — Shared utility functions (date calculations, validation)
- **_serializers.py** — Response serialization helpers
- **course_service.py** — Course CRUD, enrollment management, content ordering
- **assignment_service.py** — Assignment lifecycle (create, submit, grade, return)
- **quiz_service.py** — Quiz management (question banks, attempts, auto-grading)
- **grading_service.py** — Grade calculation using Moroccan 0-20 scale with weighted categories
- **content_service.py** — Course content management (lessons, materials, ordering)
- **progress_service.py** — Student progress tracking and completion percentage

## Architecture

Each service follows the Router → Service → Repository pattern. Services receive `AsyncSession` via dependency injection and delegate data access to repositories.
