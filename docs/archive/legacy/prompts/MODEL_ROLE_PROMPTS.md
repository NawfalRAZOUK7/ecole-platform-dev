# Model & Role Enhancement Prompts — Ecole Platform

> Execute AFTER OOP refactor (Parts 1–2 complete).
> Each prompt is self-contained. Run one at a time.
> Reference: MODEL_ROLE_ARCHITECTURE.md

---

## Pre-Requisite

The AI agent MUST read MODEL_ROLE_ARCHITECTURE.md before running these prompts. It should also have read OOP_ARCHITECTURE_STANDARD.md and ENHANCEMENT_ARCHITECTURE.md from previous phases for full context.

---

## Phase MR-A: School Model + Model Mixins

### Prompt MR-A1: School Model + SchoolScopedMixin + SoftDeleteMixin

```
CONTEXT: You are working on Ecole Platform. Read MODEL_ROLE_ARCHITECTURE.md sections R6, M1, M2.

TASK: Create the School model, SchoolScopedMixin, and SoftDeleteMixin.

STEPS:
1. Create backend/app/models/school.py with the School model (exact spec from MODEL_ROLE_ARCHITECTURE.md R6).
   - Include all fields: name, name_ar, code, massar_code, status, address, city, region, phone, email, website, logo_path
   - Include subscription fields: max_students, max_teachers, subscription_plan, subscription_expires_at
   - Include preferences: timezone (default "Africa/Casablanca"), default_language (default "fr"), grading_scale (default "moroccan_20"), settings (JSONB)
   - Include SchoolStatus enum (active, suspended, trial)
   - Include is_active, is_subscription_valid properties
   - Include __repr__ and email validator
   - Include soft delete (deleted_at)

2. Add SchoolScopedMixin to backend/app/core/database.py:
   - school_id: Mapped[uuid.UUID] with ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
   - Import uuid and ForeignKey at top of file

3. Add SoftDeleteMixin to backend/app/core/database.py:
   - deleted_at: Mapped[datetime | None], nullable=True
   - is_deleted property
   - soft_delete() method (sets deleted_at to utcnow)
   - restore() method (sets deleted_at to None)

4. Update backend/app/models/__init__.py — add School, SchoolStatus exports.

5. Create Alembic migration G31a:
   - Create schools table with all columns
   - INSERT INTO schools (id, name, code, status) SELECT DISTINCT school_id, 'School ' || ROW_NUMBER(), 'SCH-' || ROW_NUMBER(), 'active' FROM users WHERE school_id IS NOT NULL
   - Add FK constraints from ALL tables that have school_id → schools.id (use batch ALTER TABLE)
   - Tables to update: users, memberships, sessions, login_history, invitation_codes, account_recovery_requests, courses, grade_categories, assignments, assessments, quizzes, question_bank_items, content_items, activities, academic_years, classes, attendance_sessions, attendance_alerts, timetable_constraints, timetable_generation_jobs, timetable_slots, timetable_exceptions, invoices, fee_structures, fee_assignments, sibling_discount_policies, late_fee_policies, payment_plans, consent_preferences, notifications, notification_preferences, device_tokens, notification_deliveries, parent_feed_items, conversations, announcements, documents, resources, student_document_requirements, events, report_schedules, report_jobs, data_exports

6. Replace school_id column definitions in ALL model files with SchoolScopedMixin inheritance:
   - iam.py: User, Membership, Session, LoginHistory, InvitationCode, AccountRecoveryRequest
   - lms.py: Course, GradeCategory, Assignment, Assessment, Quiz, QuestionBankItem, ContentItem, Activity
   - erp.py: AcademicYear, Class, AttendanceSession, AttendanceAlert, TimetableConstraint, TimetableGenerationJob, TimetableSlot, TimetableException
   - billing.py: Invoice, FeeStructure, FeeAssignment, SiblingDiscountPolicy, LateFeePolicy, PaymentPlan
   - com.py: ConsentPreference, Notification, NotificationPreference, DeviceToken, NotificationDelivery, ParentFeedItem, Conversation, Announcement
   - documents.py: Document, Resource, StudentDocumentRequirement
   - calendar.py: Event
   - reporting.py: ReportSchedule, ReportJob, DataExport
   For each model: add SchoolScopedMixin to class bases, remove the manual school_id column definition. Keep composite indexes that include school_id in __table_args__.

7. Replace deleted_at column definitions in Document, Resource, Event, Notification with SoftDeleteMixin inheritance:
   - documents.py: Document, Resource — add SoftDeleteMixin, remove deleted_at column
   - calendar.py: Event — add SoftDeleteMixin, remove deleted_at column
   - com.py: Notification — add SoftDeleteMixin, remove deleted_at column
   Keep existing idx_*_deleted_at indexes in __table_args__.

8. Create backend/app/repositories/school.py:
   - create_school(data) -> School
   - get_school(school_id) -> School | None
   - list_schools(cursor, limit, filters) -> list[School]
   - update_school(school_id, data) -> School
   - soft_delete_school(school_id) -> None

9. Create backend/app/services/school.py:
   - SchoolService with UoW pattern
   - create_school(), get_school(), list_schools(), update_school(), deactivate_school()

10. Create backend/app/schemas/school.py:
    - SchoolCreateRequest, SchoolUpdateRequest, SchoolResponse, SchoolListResponse

11. Create backend/app/api/v1/schools.py:
    - POST /schools — SUP only
    - GET /schools — SUP (all), ADM/DIR (own school)
    - GET /schools/{id} — SUP/ADM/DIR
    - PATCH /schools/{id} — SUP/ADM
    - DELETE /schools/{id} — SUP only (soft delete)

12. Add PERM_ADM_SCHOOL_MANAGE, PERM_ADM_SCHOOL_READ to permissions.py.
13. Assign: SUP gets both, ADM/DIR get SCHOOL_READ.
14. Register endpoints in router.py.

RULES:
- Use UnitOfWork for all write operations.
- All new code follows 3-tier pattern (Router → Service → Repository).
- Do NOT run any git command.
- SchoolScopedMixin replacement must NOT change the actual DB column — just the Python declaration.
- Keep all existing composite indexes unchanged.
```

---

## Phase MR-B: Helper Properties + Repr + Validators

### Prompt MR-B1: Helper Properties on All Models

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md section M3 (Helper Properties).

TASK: Add @property helper methods to ~12 model files for business-readable state checks.

STEPS:
1. backend/app/models/iam.py — add to User:
   - is_active: self.status == UserStatus.ACTIVE.value
   - has_2fa: self.totp_secret is not None
   - is_email_verified: self.email_verified_at is not None

2. backend/app/models/iam.py — add to Membership:
   - is_active: self.status == MembershipStatus.ACTIVE.value

3. backend/app/models/iam.py — add to Session:
   - is_expired: self.expires_at < datetime.now(timezone.utc)
   - is_impersonated: self.impersonator_id is not None
   - is_revoked: self.revoked_at is not None

4. backend/app/models/iam.py — add to InvitationCode:
   - is_expired: self.expires_at < datetime.now(timezone.utc)
   - is_fully_used: self.current_uses >= self.max_uses

5. backend/app/models/iam.py — add to AccountRecoveryRequest:
   - is_expired: self.expires_at < datetime.now(timezone.utc)

6. backend/app/models/billing.py — add to Invoice:
   - is_overdue: self.status == "sent" and self.due_date < date.today()
   - is_paid: self.status == "paid"

7. backend/app/models/billing.py — add to PaymentPlan:
   - is_completed: self.status == "completed"

8. backend/app/models/billing.py — add to Installment:
   - is_overdue: not self.paid_at and self.due_date < date.today()

9. backend/app/models/lms.py — add to Assignment:
   - is_past_due: self.due_date and self.due_date < datetime.now(timezone.utc)
   - accepts_late: self.allow_late and self.is_past_due (check grace period if grace_period_hours exists)

10. backend/app/models/lms.py — add to Submission:
    - is_graded: self.graded_at is not None

11. backend/app/models/lms.py — add to Quiz:
    - is_active: self.published and within start/end time window

12. backend/app/models/erp.py — add to Enrollment:
    - is_active: self.status == "active"

13. backend/app/models/erp.py — add to AttendanceAlert:
    - is_resolved: self.resolved_at is not None

14. backend/app/models/com.py — add to Conversation:
    - is_group: self.type == ConversationType.GROUP.value

15. backend/app/models/reporting.py — add to ReportJob:
    - is_complete: self.status == ReportJobStatus.READY.value
    - is_expired: self.expires_at and self.expires_at < datetime.now(timezone.utc)

16. backend/app/models/documents.py — add to Document:
    - is_expired: self.expires_at and self.expires_at < datetime.now(timezone.utc)

17. backend/app/models/calendar.py — add to Event:
    - is_past: self.end_time < datetime.now(timezone.utc)
    - is_all_day: self.all_day is True

18. Add necessary imports: from datetime import datetime, timezone, date at top of each file where needed.

RULES:
- Every property must be pure computation — no DB access, no side effects.
- Add from datetime import datetime, timezone where missing.
- Do NOT modify any existing code — only add new @property methods.
- Do NOT run any git command.
```

### Prompt MR-B2: __repr__ Methods on All Models

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md section M4 (__repr__ Methods).

TASK: Add __repr__ methods to ALL models for debug-friendly logging.

PATTERN:
def __repr__(self) -> str:
    return f"<ModelName id={str(self.id)[:8]} field1={self.field1} field2={self.field2}>"

STEPS:
1. backend/app/models/iam.py — add __repr__ to ALL models:
   - User: id[:8], email, status
   - Membership: id[:8], user_id[:8], role_code
   - Session: id[:8], user_id[:8], "impersonated" if impersonator_id
   - LoginHistory: id[:8], user_id[:8], success
   - InvitationCode: id[:8], code, role_code
   - AccountRecoveryRequest: id[:8], user_id[:8], status
   - ParentChildLink: id[:8], parent_id[:8], child_id[:8]
   - StudentProfile: id[:8], student_number
   - ParentProfile: id[:8], user_id[:8]
   - TeacherProfile: id[:8], employee_id
   - AdminProfile: id[:8], department
   - ContentManagerProfile: id[:8], specialization

2. backend/app/models/lms.py — add __repr__ to ALL models:
   - Course: id[:8], name
   - GradeCategory: id[:8], name, weight
   - Rubric: id[:8], name
   - RubricCriterion: id[:8], name
   - RubricLevel: id[:8], label
   - Assignment: id[:8], title, type
   - Submission: id[:8], student_id[:8], status
   - SubmissionFile: id[:8], filename
   - RubricScore: id[:8], submission_id[:8]
   - Grade: id[:8], student_id[:8], score
   - StudentPeriodAverage: id[:8], student_id[:8], average
   - Assessment: id[:8], name, type
   - AssessmentResult: id[:8], student_id[:8], score
   - Quiz: id[:8], title, published
   - QuizQuestion: id[:8], quiz_id[:8]
   - QuizAttempt: id[:8], student_id[:8], status
   - QuizResponse: id[:8], attempt_id[:8]
   - QuestionBankItem: id[:8], subject
   - ContentItem: id[:8], title, type
   - ContentItemAsset: id[:8], content_item_id[:8]
   - ContentProgress: id[:8], student_id[:8], percent
   - Activity: id[:8], title, type
   - ActivitySession: id[:8], activity_id[:8]
   - ClassContentAssignment: id[:8], class_id[:8]
   - ContentSubmission: id[:8], student_id[:8]

3. backend/app/models/erp.py — add __repr__ to ALL models:
   - AcademicYear: id[:8], name
   - Period: id[:8], name, type
   - Class: id[:8], name, level
   - Enrollment: id[:8], student_id[:8], status
   - TeacherAssignment: id[:8], teacher_id[:8], class_id[:8]
   - AttendanceSession: id[:8], class_id[:8], date
   - AttendanceRecord: id[:8], student_id[:8], status
   - AbsenceJustification: id[:8], record_id[:8]
   - JustificationReview: id[:8], justification_id[:8]
   - AttendanceAlert: id[:8], student_id[:8], type
   - TimetableConstraint: id[:8], type
   - TimetableGenerationJob: id[:8], status
   - TimetableSlot: id[:8], day, start_time
   - TimetableException: id[:8], date

4. backend/app/models/billing.py — add __repr__ to ALL models.
5. backend/app/models/com.py — add __repr__ to ALL models.
6. backend/app/models/documents.py — add __repr__ to ALL models.
7. backend/app/models/calendar.py — add __repr__ to ALL models.
8. backend/app/models/reporting.py — add __repr__ to ALL models.
9. backend/app/models/audit.py — add __repr__ to AuditLog.

RULES:
- NEVER include password_hash, tokens, secrets, or JSONB bodies in __repr__.
- Use str(self.id)[:8] for all UUIDs.
- Do NOT run any git command.
```

### Prompt MR-B3: SQLAlchemy Validators

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md section M5 (SQLAlchemy Validators).

TASK: Add @validates decorators to critical model fields.

STEPS:
1. Add `from sqlalchemy.orm import validates` to each model file that needs validators.

2. backend/app/models/iam.py — User:
   - validate_email: contains "@", lowercase, strip whitespace
   - validate_phone: starts with "+", strip spaces/dashes (if not None)

3. backend/app/models/billing.py — Invoice:
   - validate_total: >= 0
   - validate_currency: must be "MAD" (or in allowed currencies list ["MAD", "EUR", "USD"])

4. backend/app/models/billing.py — InvoiceItem:
   - validate_amount: >= 0

5. backend/app/models/billing.py — Installment:
   - validate_amount: > 0

6. backend/app/models/billing.py — SiblingDiscountPolicy:
   - validate_discount_percent: between 0 and 100

7. backend/app/models/lms.py — Grade:
   - validate_score: between 0 and 20 (Moroccan scale)
   - validate_late_penalty: >= 0

8. backend/app/models/lms.py — Assignment:
   - validate_max_score: > 0
   - validate_late_penalty_per_day: between 0 and 100

9. backend/app/models/lms.py — GradeCategory:
   - validate_weight: between 0 and 1

10. backend/app/models/lms.py — ResourceRating (in documents.py):
    - validate_rating: between 1 and 5

11. backend/app/models/documents.py — ResourceRating:
    - validate_rating: between 1 and 5

RULES:
- Each validator raises ValueError with a descriptive message.
- Validators normalize input where appropriate (email lowercase, phone strip).
- Do NOT run any git command.
```

---

## Phase MR-C: Enum Columns

### Prompt MR-C1: Define Missing Enums + Create PG Enum Types

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md section M6 (Enum Columns).

TASK: Define any missing Python enums and create Alembic migration for PostgreSQL ENUM types.

STEPS:
1. Audit all model files — find String columns that use enum defaults but lack a corresponding Python enum.
   Known missing enums to create:
   - lms.py: AssignmentType (homework, project, exam, lab, etc.) if not exists
   - lms.py: SubmissionStatus (draft, submitted, graded, returned) if not exists
   - lms.py: QuizAttemptStatus (in_progress, completed, timed_out) if not exists
   - erp.py: TimetableJobStatus (pending, running, completed, failed) if not exists
   - erp.py: EnrollmentStatus (active, withdrawn, transferred, graduated) if not exists
   - erp.py: AttendanceStatus (present, absent, late, excused) if not exists
   - billing.py: InvoiceStatus (draft, sent, paid, overdue, void, cancelled) if not exists
   - billing.py: PaymentStatus (pending, completed, failed, refunded) if not exists
   - billing.py: PaymentMethod (cash, bank_transfer, card, check) if not exists

2. Add any missing enums to their respective model files, following the existing pattern:
   class EnumName(str, enum.Enum):
       VALUE = "value"

3. Create Alembic migration G31b — PostgreSQL ENUM types:
   For EACH enum (full list in MODEL_ROLE_ARCHITECTURE.md M6):
   a. CREATE TYPE enum_name AS ENUM ('value1', 'value2', ...)
   b. ALTER TABLE table_name ALTER COLUMN column_name TYPE enum_name USING column_name::enum_name

   Downgrade: reverse each ALTER to VARCHAR, then DROP TYPE.

4. Update model column definitions to use PgEnum:
   from sqlalchemy.dialects.postgresql import ENUM as PgEnum

   status: Mapped[str] = mapped_column(
       PgEnum(UserStatus, name="user_status_enum", create_type=False),
       nullable=False,
       default=UserStatus.ACTIVE,
   )

   Apply to ALL ~30 columns listed in MODEL_ROLE_ARCHITECTURE.md M6.

RULES:
- create_type=False on ALL PgEnum usages (migration handles type creation).
- Migration must be reversible — downgrade converts back to VARCHAR.
- Do NOT run any git command.
- Verify all existing data values are valid members of their enum before migration.
```

---

## Phase MR-D: Permission Fixes (DIR, SUP, CONTENT_MGR, Hierarchy)

### Prompt MR-D1: DIR + SUP + CONTENT_MGR Permission Expansion + Role Hierarchy

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md sections R1, R5, R7, R8.

TASK: Expand DIR/SUP/CONTENT_MGR permissions and implement role hierarchy.

STEPS:
1. backend/app/core/permissions.py — expand DIR permissions:
   Add to ROLE_PERMISSIONS[RoleCode.DIR]:
   - PERM_BIL_FEE_STRUCTURE_CREATE, PERM_BIL_FEE_STRUCTURE_UPDATE, PERM_BIL_FEE_STRUCTURE_DELETE
   - PERM_BIL_INVOICE_VOID
   - PERM_BIL_DISCOUNT_MANAGE, PERM_BIL_LATE_FEE_MANAGE, PERM_BIL_PAYMENT_PLAN_MANAGE
   - PERM_ERP_TIMETABLE_GENERATE, PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE
   - PERM_ADM_SETTINGS_READ, PERM_ADM_SETTINGS_UPDATE
   - PERM_ADM_ANNOUNCEMENT_MANAGE
   - PERM_RPT_SCHEDULE_MANAGE
   - PERM_DOC_REQUIREMENT_MANAGE
   (If any permission constant doesn't exist yet, create it first.)

2. backend/app/core/permissions.py — expand SUP permissions:
   Add to ROLE_PERMISSIONS[RoleCode.SUP]:
   - PERM_ERP_SCHOOL_READ (create if needed), PERM_ERP_CLASS_READ, PERM_ERP_ENROLLMENT_READ, PERM_ERP_ATTENDANCE_READ
   - PERM_LMS_COURSE_READ
   - PERM_BIL_INVOICE_READ, PERM_BIL_PAYMENT_READ
   - PERM_COM_NOTIFICATION_READ
   - PERM_DOC_DOCUMENT_READ
   - PERM_RPT_REPORT_READ
   - PERM_CAL_EVENT_READ
   - PERM_ADM_SCHOOL_MANAGE, PERM_ADM_PLATFORM_STATS (create if needed)
   - PERM_SYS_AUDIT_LOG_READ (create if needed)

3. backend/app/core/permissions.py — clarify CONTENT_MGR:
   Add PLATFORM_ROLES constant:
   PLATFORM_ROLES = {"SUP", "SYS", "CONTENT_MGR"}

   Add to ROLE_PERMISSIONS[RoleCode.CONTENT_MGR]:
   - PERM_LMS_QUESTION_BANK_MANAGE (if not already)
   - PERM_DOC_RESOURCE_MANAGE (create if needed)

4. backend/app/core/permissions.py — implement role hierarchy:
   Add ROLE_HIERARCHY dict:
   ROLE_HIERARCHY = {
       "SYS": ["SUP"],
       "SUP": ["ADM"],
       "ADM": ["DIR"],
       "DIR": ["TCH"],
   }

   Add get_effective_permissions(role: str) -> set[str] function:
   - Gets direct permissions from ROLE_PERMISSIONS
   - Recursively includes permissions from inherited roles via ROLE_HIERARCHY
   - Returns the full set

   Update role_has_permission() to use get_effective_permissions() instead of just ROLE_PERMISSIONS.

5. After implementing hierarchy, audit for redundant permissions:
   - If DIR now inherits from TCH, remove permissions from DIR that TCH already has.
   - If ADM inherits from DIR, remove permissions from ADM that DIR already has.
   - If SUP inherits from ADM, remove permissions from SUP that ADM already has.
   - Document which permissions were de-duplicated.

RULES:
- Do NOT remove any permission constants — only modify role assignments.
- Ensure no circular references in ROLE_HIERARCHY.
- Do NOT run any git command.
- Test: get_effective_permissions("DIR") should include all TCH permissions.
- Test: get_effective_permissions("SUP") should include all ADM + DIR + TCH permissions.
```

---

## Phase MR-E: ABAC Validation + Hardcoded Role Removal

### Prompt MR-E1: ABAC Helper Module + PAR Validation

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md sections R2, R3, R4.

TASK: Create the ABAC helper module and implement parent-child access validation.

STEPS:
1. Create backend/app/core/abac.py with:
   - apply_owner_scope(query, *, auth, owner_field, teacher_field, parent_field, student_field, admin_roles) -> Select
   - validate_parent_child_access(db, *, parent_id, student_id) -> bool
   - validate_teacher_class_access(db, *, teacher_id, class_id) -> bool
   - validate_student_teacher_access(db, *, student_id, teacher_id) -> bool
   (Exact implementations in MODEL_ROLE_ARCHITECTURE.md R2, R3, R4)

2. Add STD messaging permissions to backend/app/core/permissions.py:
   - PERM_COM_STD_MESSAGE_SEND = "com:std_message:send"
   - PERM_COM_STD_MESSAGE_READ = "com:std_message:read"
   - Assign both to STD role

3. Update backend/app/services/communication.py (or messaging service):
   - In create_conversation: if auth.role == "STD", validate via validate_student_teacher_access()
   - STD can only create DIRECT conversations (not GROUP)
   - STD can only message teachers of their enrolled classes

4. Audit and fix PAR access in these service files — add validate_parent_child_access() where missing:
   - services/lms/ (all sub-services): any method that takes student_id and is PAR-accessible
   - services/erp.py (or attendance/enrollment services): attendance reads, enrollment info
   - services/billing.py: invoice reads for specific students
   - services/communication.py: notification reads, feed items
   - services/reports.py: report requests for specific students
   - services/student_documents.py: document reads for specific students

   Pattern for each:
   if auth.role == "PAR":
       from app.core.abac import validate_parent_child_access
       is_valid = await validate_parent_child_access(db, parent_id=auth.user_id, student_id=student_id)
       if not is_valid:
           raise HTTPException(403, "Not authorized for this student")

RULES:
- Do NOT remove existing role checks that serve as ABAC scoping — augment them with proper validation.
- validate_parent_child_access checks parent_child_links table for verified=True link.
- Do NOT run any git command.
```

### Prompt MR-E2: Replace Hardcoded Role Strings with Permissions

```
CONTEXT: Read MODEL_ROLE_ARCHITECTURE.md section R2. ABAC helpers from MR-E1 are now available.

TASK: Replace ~50 hardcoded role string comparisons with proper permission checks or ABAC helpers.

APPROACH: There are two categories:
A) Authorization checks (if auth.role != "ADM") → replace with require_permission()
B) Data-scoping checks (if auth.role == "PAR": filter by parent_id) → replace with apply_owner_scope()

STEPS:
1. Search all files in backend/app/services/ for patterns:
   - auth.role == "
   - auth.role != "
   - auth.role in [
   - auth.role in (
   - role == "
   - role != "

2. For EACH match, classify as Category A or B:
   - Category A (authorization): Replace with require_permission(auth, PERM_*)
   - Category B (data scoping): Replace with apply_owner_scope() or validate_*_access()

3. File-by-file refactoring — process each service file:
   - services/lms/course_service.py
   - services/lms/assignment_service.py
   - services/lms/quiz_service.py
   - services/lms/content_service.py
   - services/lms/progress_service.py
   - services/erp.py (or split sub-services)
   - services/billing.py
   - services/communication.py
   - services/notification_hub.py
   - services/calendar.py
   - services/reports.py
   - services/student_documents.py
   - services/resource_library.py
   - services/admin.py
   - services/timetable_generator.py
   - services/data_export.py
   - services/profile.py
   - services/attendance_analytics.py

4. Also check router files in backend/app/api/v1/ for hardcoded role checks.

5. Import ABAC helpers where needed:
   from app.core.abac import apply_owner_scope, validate_parent_child_access

6. Keep a count of replacements made per file. Target: zero hardcoded role string comparisons remaining in services.

RULES:
- Do NOT break existing functionality — each replacement must be semantically equivalent.
- If a permission constant doesn't exist for an authorization check, create it in permissions.py and assign to appropriate roles.
- apply_owner_scope handles the common pattern; use specific validators for parent/teacher checks.
- Do NOT run any git command.
- If uncertain about a specific case, leave a TODO comment rather than breaking the logic.
```

---

## Phase MR-F: Model & Role Validation

### Prompt MR-F1: Full Model & Role Validation

```
CONTEXT: All MODEL_ROLE_ARCHITECTURE.md enhancements (M1-M6, R1-R8) should now be implemented.

TASK: Validate every enhancement was correctly implemented.

CHECKLIST:
1. SchoolScopedMixin (M1):
   - [ ] SchoolScopedMixin exists in database.py
   - [ ] ~40 models inherit from it
   - [ ] No duplicate school_id definitions remain
   - [ ] All composite indexes still reference school_id correctly

2. SoftDeleteMixin (M2):
   - [ ] SoftDeleteMixin exists in database.py with is_deleted, soft_delete(), restore()
   - [ ] Document, Resource, Event, Notification use it
   - [ ] No duplicate deleted_at definitions on those 4 models

3. Helper Properties (M3):
   - [ ] User has is_active, has_2fa, is_email_verified
   - [ ] Session has is_expired, is_impersonated, is_revoked
   - [ ] Invoice has is_overdue, is_paid
   - [ ] Assignment has is_past_due
   - [ ] Submission has is_graded
   - [ ] ReportJob has is_complete, is_expired
   - [ ] All properties are pure (no DB access)

4. __repr__ (M4):
   - [ ] Every model has __repr__
   - [ ] No sensitive data in any __repr__
   - [ ] All use str(self.id)[:8] format

5. Validators (M5):
   - [ ] User.email validator normalizes and validates
   - [ ] Grade.score validator checks 0-20
   - [ ] Invoice.total validator checks >= 0
   - [ ] All validators raise ValueError

6. Enum Columns (M6):
   - [ ] Migration G31b exists and creates ~30 PG ENUM types
   - [ ] All String status columns now use PgEnum
   - [ ] create_type=False on all PgEnum usages

7. School Model (R6):
   - [ ] School model exists in models/school.py
   - [ ] Migration G31a creates schools table
   - [ ] SchoolService, SchoolRepository, SchoolSchema exist
   - [ ] /schools endpoints registered

8. Permissions (R1, R5, R7):
   - [ ] DIR has billing management permissions
   - [ ] SUP has cross-school read access
   - [ ] CONTENT_MGR has cross-school content permissions
   - [ ] PLATFORM_ROLES constant exists

9. Role Hierarchy (R8):
   - [ ] ROLE_HIERARCHY dict exists
   - [ ] get_effective_permissions() works correctly
   - [ ] role_has_permission() uses effective permissions
   - [ ] DIR inherits TCH permissions
   - [ ] ADM inherits DIR + TCH permissions

10. ABAC (R2, R3, R4):
    - [ ] abac.py exists with apply_owner_scope, validate_parent_child_access, validate_teacher_class_access, validate_student_teacher_access
    - [ ] Zero hardcoded role string comparisons in services
    - [ ] PAR access validates parent-child link
    - [ ] STD messaging validates student-teacher class relationship
    - [ ] STD limited to DIRECT conversations only

11. Import health check:
    - [ ] python -c "from app.models import *" succeeds
    - [ ] python -c "from app.core.database import SchoolScopedMixin, SoftDeleteMixin" succeeds
    - [ ] python -c "from app.core.abac import apply_owner_scope" succeeds
    - [ ] python -c "from app.core.permissions import get_effective_permissions, ROLE_HIERARCHY" succeeds

RULES:
- Fix any issues found during validation.
- Do NOT run any git command.
- Report a summary of: passed checks, failed checks, fixes applied.
```
