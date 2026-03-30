# Test Data Factories

Factory_boy + Faker-based test data generation. All factories produce **Moroccan-specific data** aligned with production schemas.

## Overview

- **Technology**: factory_boy with Faker localization
- **Locale**: Morocco (fr_MA / ar_MA)
- **Base Class**: `BaseFactory` with async `create()` support
- **Data Standards**: See property details below

## Factory Files

### Core Infrastructure
- **base.py** - `BaseFactory` with async creation, SQLAlchemy ORM integration
  - Provides async `create()`, `create_batch()`, `build()` methods
  - Handles transaction management for test isolation

### IAM Factories (Identity & Access Management)
- **iam.py** - User, Role, and Permission factories
  - `UserFactory` - Creates test users with hashed passwords
  - `RoleFactory` - Creates system/admin/director/teacher/parent/student/content manager roles
  - Permission seeds for 166+ permission constants

### School/Organizational Factories
- **school.py** - School and Class factories
  - `SchoolFactory` - Creates schools with Moroccan addresses, phone (+212)
  - `ClassFactory` - Creates classes with section/level/academic year

### LMS Factories (Learning Management)
- **lms.py** - Course, Assignment, Quiz, and Lesson factories
  - `CourseFactory` - Creates courses with prerequisites, credits
  - `AssignmentFactory` - Creates assignments with due dates, rubrics
  - `QuizFactory` - Creates quizzes with questions and scoring

### Billing Factories
- **billing.py** - Subscription, Invoice, and Payment factories
  - Currency: **MAD** (Moroccan Dirham)
  - `SubscriptionFactory` - School subscription plans
  - `InvoiceFactory` - Payment invoices with line items
  - `PaymentFactory` - Payment records with status tracking

### Calendar Factories
- **calendar.py** - Academic Calendar, Event, and Schedule factories
  - `AcademicCalendarFactory` - School calendar with Moroccan holidays
  - `EventFactory` - Event scheduling with timezone support (Africa/Casablanca)

### Communication Factories
- **com.py** - Notification, Message, and Announcement factories
  - `NotificationFactory` - System notifications
  - `MessageFactory` - User-to-user messages
  - `AnnouncementFactory` - School announcements

### Document Factories
- **documents.py** - Document, Attachment, and FileStorage factories
  - `DocumentFactory` - Document records with metadata
  - File type support: PDF, DOCX, XLSX, images

### ERP Factories (Enterprise Resource Planning)
- **erp.py** - Employee, Attendance, and Leave factories
  - `EmployeeFactory` - Staff employee records
  - `AttendanceFactory` - Attendance records with timestamps
  - `LeaveFactory` - Leave request workflow

## Moroccan-Specific Data Standards

### Grading (Morocco uses 0-20 scale)
- Valid grades: 0-20
- Decimal precision: 2 places (e.g., 15.75)
- Exception: Out-of-range grades trigger validation errors

### Currency (MAD - Moroccan Dirham)
- All monetary values in MAD
- Symbol: د.م. or MAD
- Precision: 2 decimal places
- Overflow boundaries tested in edge cases

### Phone Numbers (+212 format)
- Format: +212 6xx-xxx-xxx or +212 5xx-xxx-xxx (mobile)
- Format: +212 5xx-xxx-xxx (landline)
- Validates against regex in models

### Names & Localization
- French names (common in French-speaking schools)
- Arabic names (Al- prefixes, common patterns)
- Locale factories: fr_MA, ar_MA

### Timezone
- Primary timezone: **Africa/Casablanca** (WET/WEST)
- All timestamp factories use Casablanca offset
- DST handling for summer time transitions

## Usage Example

```python
from backend.tests.factories import UserFactory, SchoolFactory, CourseFactory

# Create a test user
user = UserFactory()  # async
school = SchoolFactory(name="Lycée Al-Khansaa")
course = CourseFactory(school=school, title="Mathématiques")

# Batch creation
users = UserFactory.create_batch(5)

# Override defaults
admin = UserFactory(role="ADMIN", email="admin@school.ma")
student = UserFactory(
    role="STUDENT",
    first_name="Ahmed",
    last_name="Ben Ali"
)
```

## Key Factory Features

- **Async-Safe**: All factories support async create/build
- **Relational Integrity**: Foreign key relationships maintained
- **Moroccan Defaults**: Locale-aware name generation
- **Flexible Overrides**: Pass kwargs to customize any field
- **Batch Operations**: `create_batch(n)` for multiple instances
- **Lazy Evaluation**: Use `SubFactory` for relationships

## Testing Boundaries

Factories support testing edge cases:
- Grade boundaries: 0, 20, decimals (test_boundary_values.py)
- Currency overflow: MAD ceiling values (test_boundary_values.py)
- Timezone DST transitions: 2:59 AM clock changes (test_time_dependent.py)
- Name edge cases: Unicode, multi-byte characters

## Coverage Integration

Factories are used across all test categories:
- **Unit**: Mock factories for isolated tests
- **Integration**: Real persistence with testcontainers
- **Security**: Fixture factories for RBAC/ABAC tests
- **Edge**: Boundary value factories
- **Performance**: Batch factories for load testing
- **Contract**: API payload factories

See parent **README.md** for test statistics.
