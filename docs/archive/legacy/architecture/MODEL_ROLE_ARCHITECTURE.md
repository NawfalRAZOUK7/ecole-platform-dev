# Model & Role Enhancement Architecture — Ecole Platform

> Design specifications for Model OOP Enhancements (M1–M6) and Role/Permission Fixes (R1–R8).
> Execute AFTER OOP refactor (Parts 1–2 complete) using MODEL_ROLE_PROMPTS.md.
> All enhancements follow the 3-tier pattern: Router → Service → Repository.

---

## Table of Contents

- [M1: SchoolScopedMixin](#m1-schoolscopedmixin)
- [M2: SoftDeleteMixin](#m2-softdeletemixin)
- [M3: Helper Properties](#m3-helper-properties)
- [M4: \_\_repr\_\_ Methods](#m4-repr-methods)
- [M5: SQLAlchemy Validators](#m5-sqlalchemy-validators)
- [M6: Enum Columns](#m6-enum-columns)
- [R1: DIR Permission Expansion](#r1-dir-permission-expansion)
- [R2: Hardcoded Role Strings → Permissions](#r2-hardcoded-role-strings)
- [R3: PAR ABAC Validation](#r3-par-abac-validation)
- [R4: STD Messaging with ABAC](#r4-std-messaging-with-abac)
- [R5: SUP Expansion](#r5-sup-expansion)
- [R6: School Model](#r6-school-model)
- [R7: CONTENT_MGR Scope Clarification](#r7-content_mgr-scope)
- [R8: Role Hierarchy](#r8-role-hierarchy)
- [Migration Plan](#migration-plan)

---

## M1: SchoolScopedMixin

**Purpose:** Eliminate ~40 duplicate `school_id` column definitions across models by extracting a reusable mixin.

**Affected models (all have `school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)`):**

| File | Models |
|------|--------|
| iam.py | User, Membership, Session, LoginHistory, InvitationCode, AccountRecoveryRequest |
| lms.py | Course, GradeCategory, Assignment, Assessment, Quiz, QuestionBankItem, ContentItem, Activity |
| erp.py | AcademicYear, Class, AttendanceSession, AttendanceAlert, TimetableConstraint, TimetableGenerationJob, TimetableSlot, TimetableException |
| billing.py | Invoice, FeeStructure, FeeAssignment, SiblingDiscountPolicy, LateFeePolicy, PaymentPlan |
| com.py | ConsentPreference, Notification, NotificationPreference, DeviceToken, NotificationDelivery, ParentFeedItem, Conversation, Announcement |
| documents.py | Document, Resource, StudentDocumentRequirement |
| calendar.py | Event |
| reporting.py | ReportSchedule, ReportJob, DataExport |

**Implementation (database.py):**
```python
class SchoolScopedMixin:
    """Mixin providing school_id FK for multi-tenant models.

    All models that belong to a school inherit this mixin.
    The FK references the new schools table (R6).
    """
    school_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
```

**Important:** After R6 (School model) is created, `school_id` becomes a true FK.
If R6 is deferred, omit the `ForeignKey(...)` and keep just `mapped_column(nullable=False)`.

**Steps:**
1. Add `SchoolScopedMixin` to `database.py`.
2. Replace `school_id` column in all ~40 models with the mixin inheritance.
3. Remove existing per-model `school_id` definitions.
4. Composite indexes that include `school_id` remain on the model's `__table_args__` (mixin provides only the column, not composite indexes).
5. No migration needed — column definition is identical, only Python code changes.

---

## M2: SoftDeleteMixin

**Purpose:** Unify the 4 models that use soft-delete (`deleted_at` column) into a mixin with a helper property.

**Affected models:** Document, Resource, Event, Notification

**Implementation (database.py):**
```python
class SoftDeleteMixin:
    """Mixin for soft-deletable models. Adds deleted_at + is_deleted property."""

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark as deleted. Call via UoW — does NOT commit."""
        from datetime import datetime, timezone
        self.deleted_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Undo soft-delete."""
        self.deleted_at = None
```

**Steps:**
1. Add `SoftDeleteMixin` to `database.py`.
2. Update Document, Resource, Event, Notification to inherit from `SoftDeleteMixin`.
3. Remove their individual `deleted_at` column definitions.
4. Existing `idx_*_deleted_at` indexes remain on each model's `__table_args__`.
5. No migration needed — column definition is identical.

---

## M3: Helper Properties

**Purpose:** Add computed `@property` methods to ~12 models for business-readable state checks. Currently only `Notification.is_read` exists.

**Properties to add:**

| Model | Property | Logic |
|-------|----------|-------|
| **User** (iam.py) | `is_active` | `self.status == UserStatus.ACTIVE.value` |
| **User** (iam.py) | `has_2fa` | `self.totp_secret is not None` |
| **User** (iam.py) | `is_email_verified` | `self.email_verified_at is not None` |
| **Membership** (iam.py) | `is_active` | `self.status == MembershipStatus.ACTIVE.value` |
| **Session** (iam.py) | `is_expired` | `self.expires_at < utcnow()` |
| **Session** (iam.py) | `is_impersonated` | `self.impersonator_id is not None` |
| **Session** (iam.py) | `is_revoked` | `self.revoked_at is not None` |
| **InvitationCode** (iam.py) | `is_expired` | `self.expires_at < utcnow()` |
| **InvitationCode** (iam.py) | `is_fully_used` | `self.current_uses >= self.max_uses` |
| **AccountRecoveryRequest** (iam.py) | `is_expired` | `self.expires_at < utcnow()` |
| **Invoice** (billing.py) | `is_overdue` | `self.status == "sent" and self.due_date < date.today()` |
| **Invoice** (billing.py) | `is_paid` | `self.status == "paid"` |
| **PaymentPlan** (billing.py) | `is_completed` | `self.status == "completed"` |
| **Installment** (billing.py) | `is_overdue` | `not self.paid_at and self.due_date < date.today()` |
| **Assignment** (lms.py) | `is_past_due` | `self.due_date and self.due_date < utcnow()` |
| **Assignment** (lms.py) | `accepts_late` | `self.allow_late and within grace period` |
| **Submission** (lms.py) | `is_graded` | `self.graded_at is not None` |
| **Quiz** (lms.py) | `is_active` | `self.published and within time window` |
| **Enrollment** (erp.py) | `is_active` | `self.status == "active"` |
| **AttendanceAlert** (erp.py) | `is_resolved` | `self.resolved_at is not None` |
| **Conversation** (com.py) | `is_group` | `self.type == ConversationType.GROUP.value` |
| **ReportJob** (reporting.py) | `is_complete` | `self.status == ReportJobStatus.READY.value` |
| **ReportJob** (reporting.py) | `is_expired` | `self.expires_at and self.expires_at < utcnow()` |
| **Document** (documents.py) | `is_expired` | `self.expires_at and self.expires_at < utcnow()` |
| **Event** (calendar.py) | `is_past` | `self.end_time < utcnow()` |
| **Event** (calendar.py) | `is_all_day` | `self.all_day is True` |

**Implementation pattern:**
```python
from datetime import datetime, timezone

@property
def is_overdue(self) -> bool:
    """True if invoice is sent but unpaid past due date."""
    return self.status == "sent" and self.due_date < date.today()
```

**Steps:**
1. Add helper properties to each model as specified above.
2. Each property must be a pure computation — no DB access, no side effects.
3. Import `datetime` and `date` where needed.
4. No migration needed — properties are Python-only.

---

## M4: __repr__ Methods

**Purpose:** Add `__repr__` to all models for debuggable logging output.

**Pattern:**
```python
def __repr__(self) -> str:
    return f"<User id={self.id} email={self.email} status={self.status}>"
```

**Rules:**
- Include `id` always (first 8 chars of UUID for readability: `str(self.id)[:8]`).
- Include 1–2 identifying fields (email, name, type, status).
- Never include sensitive data (password_hash, tokens, secrets).
- Never include large fields (JSONB, Text body).

**Models and their repr fields:**

| Model | Fields in repr |
|-------|---------------|
| User | id, email, status |
| Membership | id, user_id[:8], role_code |
| Session | id, user_id[:8], impersonated? |
| LoginHistory | id, user_id[:8], success |
| InvitationCode | id, code, role_code |
| StudentProfile | id, student_number |
| ParentProfile | id, user_id[:8] |
| TeacherProfile | id, employee_id |
| AdminProfile | id, department |
| ContentManagerProfile | id, specialization |
| Course | id, name |
| Assignment | id, title, type |
| Submission | id, student_id[:8], status |
| Grade | id, student_id[:8], score |
| Quiz | id, title, published |
| Invoice | id, status, total |
| PaymentAttempt | id, status, amount |
| Class | id, name, level |
| Enrollment | id, student_id[:8], status |
| AttendanceSession | id, class_id[:8], date |
| Notification | id, category, read? |
| Conversation | id, type, subject |
| Message | id, conversation_id[:8] |
| Document | id, filename, category |
| Resource | id, title, type |
| Event | id, title, start |
| ReportJob | id, type, status |
| AuditLog | id, action, entity_type |

No migration needed.

---

## M5: SQLAlchemy Validators

**Purpose:** Add Python-level validation for critical fields to catch bugs before they reach the DB.

**Implementation using `@validates` decorator:**

```python
from sqlalchemy.orm import validates

class User(TimestampMixin, Base):
    # ... columns ...

    @validates("email")
    def validate_email(self, key: str, value: str) -> str:
        if value and "@" not in value:
            raise ValueError(f"Invalid email format: {value}")
        return value.lower().strip()

    @validates("phone")
    def validate_phone(self, key: str, value: str | None) -> str | None:
        if value:
            cleaned = value.replace(" ", "").replace("-", "")
            if not cleaned.startswith("+"):
                raise ValueError("Phone must start with country code (+)")
            return cleaned
        return value
```

**Validators to add:**

| Model | Field | Validation |
|-------|-------|-----------|
| User | email | Contains `@`, lowercase, strip whitespace |
| User | phone | Starts with `+`, strip spaces/dashes |
| Invoice | total | Non-negative (`>= 0`) |
| Invoice | currency | Must be `"MAD"` (or in allowed list) |
| InvoiceItem | amount | Non-negative |
| Grade | score | Between 0 and 20 (Moroccan scale) |
| Grade | late_penalty | Non-negative |
| Assignment | max_score | Positive (`> 0`) |
| Assignment | late_penalty_per_day | Between 0 and 100 |
| Enrollment | status | Must be in `EnrollmentStatus` values |
| ResourceRating | rating | Between 1 and 5 |
| Installment | amount | Positive |
| ReportJob | status | Must be in `ReportJobStatus` values |
| GradeCategory | weight | Between 0 and 1 |
| SiblingDiscountPolicy | discount_percent | Between 0 and 100 |

**Steps:**
1. Add `from sqlalchemy.orm import validates` to each model file.
2. Add validators to specified models.
3. Each validator raises `ValueError` with a descriptive message.
4. No migration needed.

---

## M6: Enum Columns

**Purpose:** Replace `String(20)` / `String(50)` status columns that use enum defaults with proper PostgreSQL `Enum` types for type safety and DB-level constraint enforcement.

**Current anti-pattern:**
```python
# BAD: String column with enum default — DB allows any string
status: Mapped[str] = mapped_column(
    String(20), nullable=False, default=UserStatus.ACTIVE.value
)
```

**Target pattern:**
```python
# GOOD: Native PostgreSQL ENUM type — DB rejects invalid values
from sqlalchemy.dialects.postgresql import ENUM as PgEnum

status: Mapped[str] = mapped_column(
    PgEnum(UserStatus, name="user_status_enum", create_type=False),
    nullable=False,
    default=UserStatus.ACTIVE,
)
```

**Columns to convert:**

| Model | Column | Enum | PG type name |
|-------|--------|------|-------------|
| User | status | UserStatus | `user_status_enum` |
| Membership | status | MembershipStatus | `membership_status_enum` |
| Membership | role_code | RoleCode | `role_code_enum` |
| AccountRecoveryRequest | status | RecoveryStatus | `recovery_status_enum` |
| Invoice | status | InvoiceStatus | `invoice_status_enum` |
| PaymentAttempt | status | PaymentStatus | `payment_status_enum` |
| PaymentAttempt | method | PaymentMethod | `payment_method_enum` |
| Enrollment | status | EnrollmentStatus | `enrollment_status_enum` |
| AttendanceRecord | status | AttendanceStatus | `attendance_status_enum` |
| Notification | category | NotificationCategory | `notification_category_enum` |
| Notification | priority | NotificationPriority | `notification_priority_enum` |
| NotificationDelivery | channel | DeliveryChannel | `delivery_channel_enum` |
| NotificationDelivery | status | DeliveryStatus | `delivery_status_enum` |
| ConsentPreference | status | ConsentStatus | `consent_status_enum` |
| ConsentPreference | channel | DeliveryChannel | (reuse) |
| DeviceToken | platform | DevicePlatform | `device_platform_enum` |
| Conversation | type | ConversationType | `conversation_type_enum` |
| ConversationParticipant | role_in_conversation | ParticipantRole | `participant_role_enum` |
| Announcement | status | AnnouncementStatus | `announcement_status_enum` |
| ReportJob | status | ReportJobStatus | `report_job_status_enum` |
| ReportJob | type | ReportType | `report_type_enum` |
| ReportSchedule | report_type | ReportType | (reuse) |
| DataExport | format | DataExportFormat | `data_export_format_enum` |
| Document | category | DocumentCategory | `document_category_enum` |
| Resource | type | ResourceType | `resource_type_enum` |
| Resource | visibility | ResourceVisibility | `resource_visibility_enum` |
| Assignment | type | (need to define) | `assignment_type_enum` |
| Submission | status | (need to define) | `submission_status_enum` |
| QuizAttempt | status | (need to define) | `quiz_attempt_status_enum` |
| TimetableGenerationJob | status | (need to define) | `timetable_job_status_enum` |

**Migration strategy:**
```sql
-- For each enum, in migration:
-- 1. Create the PG enum type
CREATE TYPE user_status_enum AS ENUM ('active', 'inactive', 'suspended');

-- 2. Alter column from VARCHAR to ENUM
ALTER TABLE users
    ALTER COLUMN status TYPE user_status_enum
    USING status::user_status_enum;
```

**Steps:**
1. Identify any models that use string status columns but lack a Python enum — define enums for them.
2. Update each model column to use `PgEnum(EnumClass, name="...", create_type=False)`.
3. Create Alembic migration that: creates PG enum types, then alters columns.
4. Test that existing data converts cleanly (all current values must be valid enum members).

---

## R1: DIR Permission Expansion

**Purpose:** Director (DIR) is the school principal — should have near-ADM level access for their school.

**Permissions to ADD to DIR role:**

```python
# Billing management (DIR should manage school finances)
PERM_BIL_FEE_STRUCTURE_CREATE,
PERM_BIL_FEE_STRUCTURE_UPDATE,
PERM_BIL_FEE_STRUCTURE_DELETE,
PERM_BIL_INVOICE_VOID,
PERM_BIL_DISCOUNT_MANAGE,
PERM_BIL_LATE_FEE_MANAGE,
PERM_BIL_PAYMENT_PLAN_MANAGE,

# Timetable (DIR should oversee timetables)
PERM_ERP_TIMETABLE_GENERATE,
PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE,

# Admin operations DIR should have
PERM_ADM_SETTINGS_READ,
PERM_ADM_SETTINGS_UPDATE,
PERM_ADM_ANNOUNCEMENT_MANAGE,

# Report management
PERM_RPT_SCHEDULE_MANAGE,

# Document management
PERM_DOC_REQUIREMENT_MANAGE,
```

**Steps:**
1. Update `ROLE_PERMISSIONS[RoleCode.DIR]` in `permissions.py`.
2. Add all permissions listed above.
3. Verify DIR still doesn't get SUP/SYS-level permissions (platform ops, system accounts).

---

## R2: Hardcoded Role Strings → Permissions

**Purpose:** Replace 50+ instances of `if auth.role == "PAR"` with proper permission checks.

**Current anti-pattern (found in ~50 places):**
```python
# BAD: Hardcoded role check
if auth.role == "PAR":
    query = query.filter(parent_id=auth.user_id)
elif auth.role == "TCH":
    query = query.filter(teacher_id=auth.user_id)
```

**Target pattern — two categories:**

### Category A: Authorization checks → replace with permissions
```python
# BEFORE:
if auth.role != "ADM":
    raise HTTPException(403, "Admin only")

# AFTER:
require_permission(auth, PERM_ADM_USER_MANAGE)
```

### Category B: Data-scoping (ABAC) → extract to helper
```python
# BEFORE:
if auth.role == "PAR":
    query = query.filter(parent_id=auth.user_id)
elif auth.role == "TCH":
    query = query.filter(teacher_id=auth.user_id)
else:
    pass  # ADM/DIR see all

# AFTER: Use a scoping helper
from app.core.abac import apply_school_scope

query = apply_school_scope(query, model=Notification, auth=auth)
```

**New file: `backend/app/core/abac.py`**
```python
"""Attribute-Based Access Control — data scoping helpers.

These functions apply role-based data filters to queries.
They do NOT check permissions — use require_permission() for that.
"""
from sqlalchemy import Select
from app.core.auth_context import AuthContext


def apply_owner_scope(
    query: Select,
    *,
    auth: AuthContext,
    owner_field: str = "user_id",
    teacher_field: str | None = "teacher_id",
    parent_field: str | None = "parent_id",
    student_field: str | None = "student_id",
    admin_roles: tuple[str, ...] = ("ADM", "DIR", "SUP"),
) -> Select:
    """Apply data-scoping filter based on user role.

    - ADM/DIR/SUP: see all records in their school
    - TCH: see records where teacher_field = auth.user_id
    - PAR: see records where parent_field = auth.user_id
    - STD: see records where student_field = auth.user_id
    - Others: see only their own records (owner_field = auth.user_id)
    """
    if auth.role in admin_roles:
        return query  # School-wide access (school_id already filtered)

    if auth.role == "TCH" and teacher_field:
        return query.filter_by(**{teacher_field: auth.user_id})
    if auth.role == "PAR" and parent_field:
        return query.filter_by(**{parent_field: auth.user_id})
    if auth.role == "STD" and student_field:
        return query.filter_by(**{student_field: auth.user_id})

    return query.filter_by(**{owner_field: auth.user_id})


async def validate_parent_child_access(
    db, *, parent_id, student_id
) -> bool:
    """Verify that parent_id has a verified parent-child link to student_id."""
    from app.models.iam import ParentChildLink
    from sqlalchemy import select

    result = await db.execute(
        select(ParentChildLink.id).where(
            ParentChildLink.parent_id == parent_id,
            ParentChildLink.child_id == student_id,
            ParentChildLink.verified == True,
        )
    )
    return result.scalar_one_or_none() is not None


async def validate_teacher_class_access(
    db, *, teacher_id, class_id
) -> bool:
    """Verify that teacher_id is assigned to class_id."""
    from app.models.erp import TeacherAssignment
    from sqlalchemy import select

    result = await db.execute(
        select(TeacherAssignment.id).where(
            TeacherAssignment.teacher_id == teacher_id,
            TeacherAssignment.class_id == class_id,
        )
    )
    return result.scalar_one_or_none() is not None
```

**Scope of changes:**
- ~25 authorization checks → `require_permission(auth, PERM_*)`
- ~25 data-scoping checks → `apply_owner_scope()` or dedicated validators
- File-by-file refactoring list provided in MODEL_ROLE_PROMPTS.md

---

## R3: PAR ABAC Validation

**Purpose:** Ensure every parent-scoped query validates the parent-child relationship via `parent_child_links`, not just `auth.role == "PAR"`.

**Current problem:**
```python
# Many services just check role, not the actual parent-child link
if auth.role == "PAR":
    grades = await repo.get_grades(student_id=some_student_id)
    # No validation that this parent is actually linked to this student!
```

**Required pattern:**
```python
if auth.role == "PAR":
    is_valid = await validate_parent_child_access(
        db, parent_id=auth.user_id, student_id=student_id
    )
    if not is_valid:
        raise HTTPException(403, "Not authorized for this student")
```

**Services requiring PAR validation audit:**
- `lms/` — grade reads, assignment reads, submission reads, quiz results
- `erp/` — attendance records, enrollment info, class details
- `billing/` — invoice reads, payment history
- `communication/` — notification reads, feed items, conversation access
- `reports/` — report requests for specific students
- `student_documents/` — document reads

**Steps:**
1. Audit every service method that accepts a `student_id` parameter and is accessible by PAR.
2. Add `validate_parent_child_access()` call before data access.
3. Use the ABAC helper from R2's `abac.py`.

---

## R4: STD Messaging with ABAC

**Purpose:** Allow students to initiate conversations, scoped to teachers of their enrolled classes.

**Current state:** Messaging (Conversation model) exists but no explicit STD access.

**New permissions:**
```python
PERM_COM_STD_MESSAGE_SEND = "com:std_message:send"
PERM_COM_STD_MESSAGE_READ = "com:std_message:read"
```

**ABAC rule:** Student can only message teachers assigned to classes they are enrolled in.

**Validation function (add to abac.py):**
```python
async def validate_student_teacher_access(
    db, *, student_id, teacher_id
) -> bool:
    """Verify student and teacher share at least one class."""
    from app.models.erp import Enrollment, TeacherAssignment
    from sqlalchemy import select, exists

    # Student's classes
    student_classes = select(Enrollment.class_id).where(
        Enrollment.student_id == student_id,
        Enrollment.status == "active",
    )

    # Teacher's classes
    teacher_classes = select(TeacherAssignment.class_id).where(
        TeacherAssignment.teacher_id == teacher_id,
    )

    # Intersection
    result = await db.execute(
        select(
            exists(
                student_classes.intersect(teacher_classes)
            )
        )
    )
    return result.scalar()
```

**Service changes (communication.py):**
```python
async def create_conversation(self, ..., auth: AuthContext):
    if auth.role == "STD":
        require_permission(auth, PERM_COM_STD_MESSAGE_SEND)
        # Validate all participants are teachers of student's classes
        for participant_id in participant_ids:
            is_valid = await validate_student_teacher_access(
                db, student_id=auth.user_id, teacher_id=participant_id
            )
            if not is_valid:
                raise HTTPException(403, "Can only message teachers of your classes")
        # STD cannot create GROUP conversations — only DIRECT
        if len(participant_ids) > 1:
            raise HTTPException(400, "Students can only create direct conversations")
```

**Steps:**
1. Add STD messaging permissions to `permissions.py`.
2. Assign to STD role.
3. Add `validate_student_teacher_access()` to `abac.py`.
4. Update `communication.py` conversation creation to support STD with ABAC.
5. Update conversation list query to include STD as participant.

---

## R5: SUP Expansion

**Purpose:** Super-admin (SUP) needs read access across all schools for platform operations.

**Current state:** SUP has only 13 permissions — basically just IAM and system.

**Permissions to ADD to SUP role:**
```python
# Cross-school read access
PERM_ERP_SCHOOL_READ,       # Read all schools' data
PERM_ERP_CLASS_READ,
PERM_ERP_ENROLLMENT_READ,
PERM_ERP_ATTENDANCE_READ,
PERM_LMS_COURSE_READ,
PERM_BIL_INVOICE_READ,
PERM_BIL_PAYMENT_READ,
PERM_COM_NOTIFICATION_READ,
PERM_DOC_DOCUMENT_READ,
PERM_RPT_REPORT_READ,
PERM_CAL_EVENT_READ,

# Platform management
PERM_ADM_SCHOOL_MANAGE,      # Create/update/disable schools
PERM_ADM_PLATFORM_STATS,     # View platform-wide analytics
PERM_SYS_AUDIT_LOG_READ,     # Read audit logs across schools
```

**Important:** SUP bypasses school_id scoping. The `apply_owner_scope` function already handles this (SUP is in `admin_roles`).

---

## R6: School Model

**Purpose:** Create a first-class `School` entity instead of relying on bare `school_id` UUIDs scattered across all models.

**New model (models/school.py):**
```python
"""School entity — the root of multi-tenancy."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.core.database import Base, TimestampMixin


class SchoolStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class School(TimestampMixin, Base):
    """A school (tenant) on the platform.

    All school_id FKs across the system reference this table.
    Moroccan-specific: stores MASSAR integration code, language prefs.
    """

    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )  # Internal code (e.g., "ECO-CASA-001")
    massar_code: Mapped[str | None] = mapped_column(
        String(50), nullable=True, unique=True
    )  # Moroccan ministry school code
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=SchoolStatus.ACTIVE.value
    )
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Subscription / limits
    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_teachers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subscription_plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    subscription_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # School preferences
    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Africa/Casablanca"
    )
    default_language: Mapped[str] = mapped_column(
        String(5), nullable=False, default="fr"
    )
    grading_scale: Mapped[str] = mapped_column(
        String(20), nullable=False, default="moroccan_20"
    )
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def is_active(self) -> bool:
        return self.status == SchoolStatus.ACTIVE.value and self.deleted_at is None

    @property
    def is_subscription_valid(self) -> bool:
        if not self.subscription_expires_at:
            return True  # No expiry = unlimited
        from datetime import datetime, timezone
        return self.subscription_expires_at > datetime.now(timezone.utc)

    @validates("email")
    def validate_email(self, key: str, value: str | None) -> str | None:
        if value and "@" not in value:
            raise ValueError(f"Invalid school email: {value}")
        return value.lower().strip() if value else value

    def __repr__(self) -> str:
        return f"<School id={str(self.id)[:8]} name={self.name} status={self.status}>"
```

**Migration (G31a):**
1. Create `schools` table.
2. Populate from existing `school_id` values (SELECT DISTINCT school_id FROM users).
3. Add FK constraints from all tables with `school_id` → `schools.id`.

**New permissions:**
```python
PERM_ADM_SCHOOL_MANAGE = "adm:school:manage"  # CRUD school entity
PERM_ADM_SCHOOL_READ = "adm:school:read"
```

**Steps:**
1. Create `backend/app/models/school.py`.
2. Update `models/__init__.py`.
3. Create Alembic migration G31a.
4. Add permissions to `permissions.py`.
5. Create `backend/app/repositories/school.py`.
6. Create `backend/app/services/school.py`.
7. Create `backend/app/schemas/school.py`.
8. Create `backend/app/api/v1/schools.py`.
9. Register in router.py.
10. After migration, update SchoolScopedMixin to use FK.

---

## R7: CONTENT_MGR Scope Clarification

**Purpose:** Clarify that CONTENT_MGR is cross-school (platform-wide content) and ensure permissions reflect this.

**Current issue:** CONTENT_MGR has 24 permissions but no explicit cross-school flag. All queries filter by school_id, which breaks for platform-wide content managers.

**Solution:**
1. Add `is_platform_role` flag or check:
```python
PLATFORM_ROLES = {"SUP", "SYS", "CONTENT_MGR"}
```

2. Update `apply_owner_scope()` to treat CONTENT_MGR like SUP for content-related queries:
```python
def apply_owner_scope(query, *, auth, ...):
    if auth.role in admin_roles or (
        auth.role == "CONTENT_MGR" and is_content_query
    ):
        return query  # No school filter for platform content roles
```

3. Add missing permissions:
```python
# CONTENT_MGR should manage:
PERM_CMS_CONTENT_CREATE,
PERM_CMS_CONTENT_UPDATE,
PERM_CMS_CONTENT_DELETE,
PERM_CMS_CONTENT_PUBLISH,
PERM_LMS_QUESTION_BANK_MANAGE,  # Cross-school question bank
PERM_DOC_RESOURCE_MANAGE,        # Cross-school resources
```

---

## R8: Role Hierarchy

**Purpose:** Implement permission inheritance so higher roles automatically include lower role permissions.

**Hierarchy:**
```
SYS
 └── SUP
      └── ADM
           └── DIR
                ├── TCH
                │    └── STD (partial)
                └── PAR (separate branch)

CONTENT_MGR (lateral — not in hierarchy, platform-wide)
```

**Implementation (permissions.py):**
```python
ROLE_HIERARCHY: dict[str, list[str]] = {
    "SYS": ["SUP"],
    "SUP": ["ADM"],
    "ADM": ["DIR"],
    "DIR": ["TCH"],
    # TCH does NOT inherit STD — different permission domains
    # PAR is separate — not in hierarchy
    # CONTENT_MGR is lateral — not in hierarchy
}


def get_effective_permissions(role: str) -> set[str]:
    """Get all permissions for a role including inherited ones."""
    permissions = set(ROLE_PERMISSIONS.get(role, []))

    # Walk up the hierarchy
    inherited_roles = ROLE_HIERARCHY.get(role, [])
    for parent_role in inherited_roles:
        permissions |= get_effective_permissions(parent_role)

    return permissions
```

**Important:** This does NOT change how permissions are stored — it changes how they're resolved at runtime. The `ROLE_PERMISSIONS` dict still lists direct permissions. The `get_effective_permissions()` function computes the full set.

**Steps:**
1. Add `ROLE_HIERARCHY` dict to `permissions.py`.
2. Add `get_effective_permissions()` function.
3. Update `role_has_permission()` to use effective permissions.
4. Audit: ensure no circular references in hierarchy.
5. Remove redundant permission assignments that are now inherited.

---

## Migration Plan

| Migration | Phase | Description |
|-----------|-------|------------|
| G31a | MR-D | Create `schools` table, populate from existing school_ids, add FK constraints |
| G31b | MR-C | Create ~30 PostgreSQL ENUM types, alter columns from VARCHAR to ENUM |

**Note:** M1 (SchoolScopedMixin), M2 (SoftDeleteMixin), M3-M5 are Python-only changes — no migration needed. R1-R5, R7-R8 are permission/logic changes — no migration needed.

**Execution order matters:**
1. G31a (School model) first — SchoolScopedMixin's FK depends on it
2. G31b (Enum columns) second — can run independently but logically after model cleanup

---

## Dependencies Between Enhancements

```
M1 (SchoolScopedMixin) ──depends on──→ R6 (School Model) for FK
M2 (SoftDeleteMixin) ──independent──
M3 (Helper Props) ──independent──
M4 (__repr__) ──independent──
M5 (Validators) ──independent──
M6 (Enum Columns) ──independent──
R1 (DIR Perms) ──independent──
R2 (Hardcoded Roles) ──depends on──→ R3 (PAR ABAC) and R4 (STD ABAC) for abac.py
R3 (PAR ABAC) ──creates──→ abac.py
R4 (STD ABAC) ──depends on──→ R3 (PAR ABAC) for abac.py
R5 (SUP Expansion) ──independent──
R6 (School Model) ──independent──
R7 (CONTENT_MGR) ──uses──→ abac.py from R2/R3
R8 (Role Hierarchy) ──depends on──→ R1 (DIR) and R5 (SUP) for correct permission sets
```

**Recommended execution order:**
1. Phase MR-A: R6 (School) + M1 (SchoolScopedMixin) + M2 (SoftDeleteMixin)
2. Phase MR-B: M3 (Properties) + M4 (Repr) + M5 (Validators)
3. Phase MR-C: M6 (Enum Columns)
4. Phase MR-D: R1 (DIR) + R5 (SUP) + R7 (CONTENT_MGR) + R8 (Hierarchy)
5. Phase MR-E: R3 (PAR ABAC) + R4 (STD ABAC) + R2 (Hardcoded Roles)
6. Phase MR-F: Validation
