# models/ — SQLAlchemy 2.0 ORM Models

Object-relational mapping (ORM) layer using SQLAlchemy 2.0 with modern `Mapped[]` type annotations. Models define database schema and relationships.

## Packaging roadmap (hybrid “A3”)

Today, modules are **flat files** (`lms.py`, `erp.py`, …) while routers/services/schemas are already grouped by **bounded context** (same names as `api/v1/`).

| Phase | Action |
|-------|--------|
| **Now** | Keep flat layout; treat this README + [`docs/DATABASE.md`](../../../docs/DATABASE.md) as the logical map (G1–G9 style groupings). |
| **Next** | When a domain is heavily touched, introduce a **subpackage** (e.g. `models/lms/`) and re-export from `models/__init__.py` in a **dedicated PR** with a codemod (no behavior change). |
| **Avoid** | Big-bang move of all models in one PR (merge pain, Alembic autogenerate noise). |

**Rename / split (only when justified)**  
Split oversized files (e.g. many unrelated tables in one module) only together with a clear migration story. Prefer **documentation** of legacy names (`com.py` = communication) over mass file renames that do not change tables.

## Directory Structure

```
models/
├── iam.py           # Identity & Access Management
├── school.py        # School structure & operations
├── lms.py           # Learning Management System
├── billing.py       # Billing & payments
├── calendar.py      # Calendar & events
├── com.py           # Communication (messages, notifications)
├── documents.py     # Document management
├── erp.py           # Enterprise Resource Planning
├── audit.py         # Audit logging & compliance
├── ai.py            # AI interactions & history
├── reporting.py     # Reports & schedules
└── feature.py       # Feature flags
```

## ORM Patterns

All models use SQLAlchemy 2.0 features:
- **Mapped[]** for type-safe columns
- **Declarative base** for inheritance
- **Async support** via asyncpg driver
- **Relationships** with lazy loading strategies

```python
from typing import Mapped, Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    country_code: Mapped[str] = mapped_column(String(2), default="MA")

    classes: Mapped[list["Class"]] = relationship(
        back_populates="school",
        cascade="all, delete-orphan"
    )
```

## Models by Domain

### iam.py — Identity & Access Management

User authentication and authorization:

**User**
- `id` — Primary key
- `email` — Unique email address
- `password_hash` — bcrypt hashed password
- `first_name`, `last_name` — Full name
- `school_id` — School association (foreign key)
- `is_active` — Account status
- `is_verified` — Email verified
- `email_verified_at` — Verification timestamp
- `last_login` — Last authentication
- `created_at`, `updated_at` — Timestamps
- Relationships: `roles`, `sessions`, `audit_logs`

**Role**
- `id` — Primary key
- `code` — Role code (ADM, DIR, TCH, PAR, STD, etc.)
- `name` — Human-readable name
- `school_id` — School-scoped role (optional)
- `permissions` — Many-to-many relationship
- Relationships: `users`, `permissions`

**Permission**
- `id` — Primary key
- `code` — Permission code (PERM-LMS:course:create)
- `name` — Description
- `description` — Long description
- Relationships: `roles`

**Session**
- `id` — Primary key (UUID)
- `user_id` — User (foreign key)
- `token_hash` — Hashed JWT
- `expires_at` — Expiry timestamp
- `ip_address` — Login IP
- `user_agent` — Browser/client info
- `created_at` — Creation timestamp

### school.py — School Structure

School organization and hierarchy:

**School**
- `id` — Primary key
- `name` — School name
- `code` — Short code (e.g., "HSC001")
- `country_code` — ISO code (default: "MA")
- `region` — School region/province
- `principal_id` — Principal user reference
- `subscription_tier` — Billing plan (starter, pro, enterprise)
- `is_active` — Active status
- `founded_year` — School establishment year
- `phone` — Contact number
- `email` — Contact email
- `address` — Physical address
- `created_at`, `updated_at` — Timestamps
- Relationships: `users`, `classes`, `courses`, `billing_profiles`

**AcademicYear**
- `id` — Primary key
- `school_id` — School (foreign key)
- `year` — Academic year (2023-2024)
- `start_date` — Year start date
- `end_date` — Year end date
- `is_active` — Current year flag
- Relationships: `classes`, `terms`

**Class**
- `id` — Primary key
- `school_id` — School (foreign key)
- `academic_year_id` — Academic year (foreign key)
- `name` — Class name (6ème A, 1ère S)
- `code` — Unique code
- `level` — Education level (collège, lycée)
- `capacity` — Maximum students
- `main_teacher_id` — Homeroom teacher
- `created_at`, `updated_at` — Timestamps
- Relationships: `students`, `courses`, `teacher_assignments`

**Enrollment**
- `id` — Primary key
- `student_id` — Student user (foreign key)
- `class_id` — Class (foreign key)
- `academic_year_id` — Academic year (foreign key)
- `enrollment_date` — When enrolled
- `status` — active/withdrawn/graduated
- Relationships: `student`, `class`

### lms.py — Learning Management

Course and assignment management:

**Course**
- `id` — Primary key
- `school_id` — School (foreign key)
- `code` — Course code
- `name` — Course name
- `description` — Course description
- `teacher_id` — Instructor (foreign key)
- `class_id` — Primary class (optional)
- `start_date` — Course start
- `end_date` — Course end
- `status` — draft/published/archived
- Relationships: `assignments`, `content_items`, `enrollments`

**Assignment**
- `id` — Primary key
- `course_id` — Course (foreign key)
- `title` — Assignment title
- `description` — Detailed instructions
- `due_date` — Submission deadline
- `max_score` — Points possible
- `weighting` — Grade weighting (%)
- `submission_type` — file/text/url
- Relationships: `submissions`, `rubric`

**Quiz**
- `id` — Primary key
- `course_id` — Course (foreign key)
- `title` — Quiz title
- `description` — Quiz instructions
- `question_count` — Number of questions
- `time_limit_minutes` — Time allowed
- `passing_score` — Minimum passing %
- `show_correct_answers` — Answer visibility
- Relationships: `questions`, `attempts`

**Grade**
- `id` — Primary key
- `student_id` — Student (foreign key)
- `assignment_id` or `quiz_id` — Evaluated item
- `score` — Earned points
- `max_score` — Possible points
- `percentage` — Calculated %
- `grade_value` — Letter/0-20 grade
- `graded_by` — Teacher (foreign key)
- `graded_at` — When graded
- Relationships: `feedback`, `rubric_scores`

**ContentItem**
- `id` — Primary key
- `course_id` — Course (foreign key)
- `title` — Content title
- `content_type` — lesson/video/pdf/reading
- `body` — Content (HTML or text)
- `position` — Sequence order
- `is_published` — Publishing status
- Relationships: `attachments`

### billing.py — Billing & Payments

Financial management:

**Invoice**
- `id` — Primary key
- `school_id` — School (foreign key)
- `number` — Invoice number (INV-2024-001)
- `student_id` — Student billed (optional, for tuition)
- `issue_date` — When issued
- `due_date` — Payment deadline
- `total_amount` — Total in MAD
- `paid_amount` — Amount paid
- `status` — draft/issued/paid/overdue/cancelled
- Relationships: `line_items`, `payments`

**LineItem**
- `id` — Primary key
- `invoice_id` — Invoice (foreign key)
- `description` — Item description
- `quantity` — Quantity
- `unit_price` — Price per unit
- `amount` — Total (quantity × unit_price)

**Payment**
- `id` — Primary key
- `invoice_id` — Invoice (foreign key)
- `amount` — Paid amount
- `method` — credit_card/bank_transfer/cash
- `reference` — Payment reference/receipt
- `paid_at` — Payment timestamp
- `status` — completed/pending/failed/refunded
- Relationships: `refunds`

**Subscription**
- `id` — Primary key
- `school_id` — School (foreign key)
- `plan_code` — Subscription plan
- `status` — active/cancelled/suspended
- `start_date` — Subscription start
- `end_date` — Subscription end
- `auto_renew` — Auto-renewal flag
- Relationships: `invoices`

### calendar.py — Calendar & Events

Calendar management:

**Event**
- `id` — Primary key
- `school_id` — School (foreign key)
- `title` — Event title
- `description` — Event details
- `start_datetime` — When event starts
- `end_datetime` — When event ends
- `location` — Physical location
- `event_type` — meeting/holiday/exam/parent-day
- `is_all_day` — All-day event flag
- Relationships: `rsvps`, `reminders`

**RSVP**
- `id` — Primary key
- `event_id` — Event (foreign key)
- `user_id` — Attendee (foreign key)
- `response` — accepted/declined/tentative
- `responded_at` — When responded

### com.py — Communication

Messaging and notifications:

**Message**
- `id` — Primary key
- `sender_id` — Sender user (foreign key)
- `recipient_id` — Recipient user (foreign key)
- `subject` — Message subject
- `body` — Message content (HTML)
- `is_read` — Read status
- `read_at` — When marked read
- `created_at` — Timestamp

**Notification**
- `id` — Primary key
- `user_id` — Recipient (foreign key)
- `type` — grade_published/assignment_due/payment_due
- `title` — Notification title
- `message` — Notification text
- `data` — JSON metadata (related IDs)
- `is_read` — Read status
- `read_at` — When read
- `delivery_status` — sent/pending/failed
- `created_at` — Timestamp

### documents.py — Document Management

File and document storage:

**Document**
- `id` — Primary key
- `school_id` — School (foreign key)
- `uploader_id` — Who uploaded (foreign key)
- `filename` — Original filename
- `file_path` — Storage path
- `file_size` — Size in bytes
- `mime_type` — Content type
- `document_type` — course_material/syllabus/policy
- `is_public` — Public or restricted
- `scanned_for_viruses` — Scan status
- `created_at`, `updated_at` — Timestamps
- Relationships: `access_logs`

**StudentFile**
- `id` — Primary key
- `student_id` — Student (foreign key)
- `assignment_id` — Associated assignment (optional)
- `filename` — Uploaded filename
- `file_path` — Storage path
- `file_size` — Size in bytes
- `uploaded_at` — Upload timestamp
- `scanned_for_viruses` — Antivirus status

### erp.py — Enterprise Resource Planning

School operations:

**Timetable**
- `id` — Primary key
- `school_id` — School (foreign key)
- `academic_year_id` — Academic year (foreign key)
- `name` — Schedule name
- `is_active` — Active schedule flag
- `created_at`, `updated_at` — Timestamps
- Relationships: `slots`, `exceptions`

**TimeSlot**
- `id` — Primary key
- `timetable_id` — Timetable (foreign key)
- `day_of_week` — 0-6 (Monday-Sunday)
- `start_time` — Class start time
- `end_time` — Class end time
- `class_id` — Class (foreign key)
- `course_id` — Course (foreign key)
- `room_id` — Room/location (optional)
- Relationships: `class`, `course`

**Resource**
- `id` — Primary key
- `school_id` — School (foreign key)
- `name` — Resource name (Lab 1, Projector)
- `resource_type` — room/equipment/material
- `capacity` — Max capacity
- `available_from` — Available start time
- `available_to` — Available end time

### audit.py — Audit & Compliance

Audit logging for compliance:

**AuditLog**
- `id` — Primary key
- `user_id` — User performing action (optional)
- `action` — Action performed (create/update/delete)
- `resource_type` — Type of resource changed
- `resource_id` — ID of changed resource
- `changes` — JSON diff of before/after
- `ip_address` — Client IP address
- `user_agent` — Browser/client info
- `created_at` — When action occurred
- Indexes: (user_id, created_at), (resource_type, resource_id)

### ai.py — AI Interactions

AI feature tracking:

**AIInteraction**
- `id` — Primary key
- `user_id` — User (foreign key)
- `interaction_type` — question/assignment_help/grading_suggestion
- `prompt` — User's question/request
- `response` — AI's response
- `model_used` — Claude/GPT-4/etc.
- `tokens_used` — API token consumption
- `cost_usd` — API cost
- `created_at` — Timestamp
- Relationships: `feedback`

### reporting.py — Reports

Report generation:

**Report**
- `id` — Primary key
- `school_id` — School (foreign key)
- `created_by` — Creator user (foreign key)
- `report_type` — student_report_card/attendance_summary
- `title` — Report title
- `filters` — JSON report parameters
- `data` — Generated report data (JSON)
- `status` — generating/completed/failed
- `file_path` — PDF storage path
- `created_at` — Generation timestamp

**ReportSchedule**
- `id` — Primary key
- `school_id` — School (foreign key)
- `report_type` — Type of report
- `cron_expression` — Recurrence pattern
- `recipients` — Email addresses
- `is_active` — Enabled flag
- `last_run` — When last generated

### feature.py — Feature Flags

Feature toggle management:

**FeatureFlag**
- `id` — Primary key
- `code` — Feature code (ai_assistant, advanced_analytics)
- `name` — Human-readable name
- `is_enabled` — Global enable/disable
- `rollout_percentage` — Percentage of users (0-100)
- `allowed_schools` — JSON list of school IDs
- `expires_at` — Kill switch date (optional)
- `metadata` — JSON configuration
- `created_at`, `updated_at` — Timestamps

## Relationships Overview

Core relationship patterns:

```
User (n) ──────► School (1)
User (n) ──────► Role (n)  [many-to-many]
Role (n) ──────► Permission (n)  [many-to-many]

School (1) ──────► Class (n)
School (1) ──────► Course (n)
School (1) ──────► Invoice (n)

Class (1) ──────► Enrollment (n)
Class (1) ──────► TimeSlot (n)

Course (1) ──────► Assignment (n)
Course (1) ──────► Quiz (n)
Course (1) ──────► ContentItem (n)

Assignment (1) ──────► Submission (n)
Assignment (1) ──────► Grade (n)

User (1) ──────► Grade (n)  [as student]
User (1) ──────► Grade (n)  [as grader]

Invoice (1) ──────► Payment (n)
Invoice (1) ──────► LineItem (n)
```

## Indexes

Performance optimizations:

```python
# Foreign keys
Index(['user_id'])
Index(['school_id'])
Index(['class_id'])
Index(['course_id'])
Index(['assignment_id'])

# Filtering/sorting
Index(['status', 'created_at'])
Index(['user_id', 'created_at'])
Index(['school_id', 'status'])

# Search
Index(['email'], postgresql_using='gin')  # FTS

# Business queries
Index(['school_id', 'academic_year_id'])
Index(['due_date', 'status'])
```

## Constraints

Data integrity:

```python
# Check constraints
CheckConstraint('grade >= 0 AND grade <= 20')
CheckConstraint('capacity > 0')

# Unique constraints
UniqueConstraint(['school_id', 'code'])
UniqueConstraint(['invoice_id', 'number'])

# Foreign keys
ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
```

## Temporal Patterns

Most models include:
- `created_at` — Record creation timestamp
- `updated_at` — Last modification timestamp
- `deleted_at` — Soft delete timestamp (optional)

Enables:
- Audit trails
- Change history
- Soft deletes (privacy)

## Next Steps

- See `repositories/` for how models are queried
- See `schemas/` for model serialization
- See `alembic/versions/` for schema migrations
