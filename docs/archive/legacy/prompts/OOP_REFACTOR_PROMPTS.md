# OOP Refactor Prompts — Ecole Platform

> Execute these prompts sequentially using Claude Code or Codex.
> Each prompt is self-contained. Run one at a time, review changes, then proceed.
> Reference: OOP_ARCHITECTURE_STANDARD.md

---

## Pre-Requisite: Context Loading

Before running ANY prompt below, the AI agent MUST first execute META_PROMPT_1_CONTEXT.md to understand the full project. Then come back here and execute prompts in order.

---

## Phase OOP-A: Foundation Layer (Domain + Unit of Work)

### Prompt OOP-A1: Create Domain Directory Structure + Value Objects

```
CONTEXT: You are working on Ecole Platform, a K-12 EdTech SaaS for Moroccan schools.
Read OOP_ARCHITECTURE_STANDARD.md Part B (Value Objects) carefully.

TASK: Create the domain layer directory structure and all value objects.

STEPS:
1. Create directory: backend/app/domain/
2. Create directory: backend/app/domain/value_objects/
3. Create directory: backend/app/domain/events/
4. Create directory: backend/app/domain/protocols/
5. Create __init__.py in each directory (empty).
6. Create backend/app/domain/value_objects/grade.py — MoroccanGrade class exactly as specified in OOP_ARCHITECTURE_STANDARD.md Part B.
7. Create backend/app/domain/value_objects/money.py — Money class exactly as specified.
8. Create backend/app/domain/value_objects/typed_id.py — UserId + SchoolId classes exactly as specified.
9. Create backend/app/domain/value_objects/role_set.py — RoleSet class exactly as specified.
10. Verify all files exist and have correct imports.

RULES:
- Follow the exact code from OOP_ARCHITECTURE_STANDARD.md. Do not deviate.
- All value objects must be frozen=True dataclasses.
- All must have __post_init__ validation.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT modify any existing files in this prompt.
```

### Prompt OOP-A2: Create Unit of Work

```
CONTEXT: You are working on Ecole Platform, a K-12 EdTech SaaS for Moroccan schools.
Read OOP_ARCHITECTURE_STANDARD.md Part A (Unit of Work) carefully.

TASK: Create the UnitOfWork class and begin integrating it into services.

STEPS:
1. Create backend/app/core/unit_of_work.py exactly as specified in OOP_ARCHITECTURE_STANDARD.md Part A.
2. Update backend/app/services/auth.py:
   - Import UnitOfWork from app.core.unit_of_work.
   - In the register() method, wrap the user creation + membership creation in UnitOfWork.
   - In the login() method (session creation), wrap in UnitOfWork.
   - Remove direct db.commit() calls from these methods — use uow.commit() instead.
   - Keep db.commit() in read-heavy methods that don't write.
3. Update backend/app/services/billing.py:
   - Wrap create_invoice + add_invoice_items in a single UnitOfWork (atomic).
   - Wrap payment processing in UnitOfWork.
4. Update backend/app/services/erp.py:
   - Wrap enrollment creation + class assignment in UnitOfWork.
   - Wrap attendance batch updates in UnitOfWork.

RULES:
- Read-only methods do NOT need UnitOfWork.
- Repositories NEVER call commit() — only UnitOfWork does.
- Keep the existing try/except patterns but replace db.rollback() with uow.rollback().
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Test that imports resolve correctly after changes.
```

### Prompt OOP-A3: Integrate UnitOfWork into Remaining Services

```
CONTEXT: You are working on Ecole Platform. OOP-A2 added UnitOfWork to auth, billing, erp.
Read OOP_ARCHITECTURE_STANDARD.md Part A (Unit of Work) carefully.

TASK: Add UnitOfWork to ALL remaining services that perform write operations.

STEPS:
1. For EACH service file in backend/app/services/:
   - Identify all methods that call db.commit() or db.add() or db.delete().
   - Wrap the write logic in `async with UnitOfWork(self.db) as uow:`.
   - Replace db.commit() with uow.commit().
   - Replace db.rollback() with uow.rollback() (inside except blocks).
   - Pass uow.session to repository constructors within the UnitOfWork block.
2. Skip services already done in OOP-A2 (auth.py, billing.py, erp.py).
3. Skip services that are read-only (analytics.py, kpi.py, dashboard_analytics.py).
4. Verify no service directly calls db.commit() after this change (except in the UoW).

Services to update (write operations detected):
- admin.py, ai.py, audit.py, calendar.py, cms.py, communication.py
- data_export.py, email_digest.py, feature.py, gdpr.py, lms.py
- notification_hub.py, overdue_reminders.py, payment_retry.py
- profile.py, progress.py, push_config.py, quiz_grading.py
- realtime.py, reminders.py, reports.py, resource_library.py
- rsvp.py, student_documents.py

RULES:
- Do NOT change method signatures or return types.
- Do NOT change the router layer — only services.
- Repositories still receive AsyncSession (from uow.session).
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

---

## Phase OOP-B: Profile System Enhancement

### Prompt OOP-B1: Add AdminProfile + ContentManagerProfile Models & Migration

```
CONTEXT: You are working on Ecole Platform.
Read OOP_ARCHITECTURE_STANDARD.md Part C (ProfileLoader) carefully.

TASK: Add the two new profile model classes and create an Alembic migration.

STEPS:
1. Edit backend/app/models/iam.py:
   - Add AdminProfile class after TeacherProfile (exactly as in OOP_ARCHITECTURE_STANDARD.md Part C).
   - Add ContentManagerProfile class after AdminProfile (exactly as in the standard).
   - Import Boolean if not already imported.
2. Edit backend/app/models/__init__.py:
   - Add AdminProfile and ContentManagerProfile to the G1 IAM imports.
   - Add both to __all__.
3. Create a new Alembic migration file:
   - File: backend/alembic/versions/[generate_hash]_g26_oop_admin_content_manager_profiles.py
   - Migration should:
     a. Create admin_profiles table with columns: id (UUID PK), user_id (FK users.id UNIQUE), school_id (UUID), department (VARCHAR 100 nullable), management_level (VARCHAR 50 nullable), can_approve_budgets (BOOLEAN default false), created_at, updated_at.
     b. Create content_manager_profiles table with columns: id (UUID PK), user_id (FK users.id UNIQUE), school_id (UUID), specialization (VARCHAR 200 nullable), languages_managed (TEXT nullable), approved_subjects (TEXT nullable), created_at, updated_at.
     c. Add indexes as specified in the model classes.
   - Use the existing migration naming convention (e.g., a1b2c3d4e5f6_g26_...).
   - Set `down_revision` to the latest existing migration hash.
4. Verify the models import correctly.

RULES:
- Follow existing migration patterns (look at the latest migration for format reference).
- Use UUID primary keys with server_default for consistency.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

### Prompt OOP-B2: Create ProfileLoader Service + Repository

```
CONTEXT: You are working on Ecole Platform. OOP-B1 added AdminProfile and ContentManagerProfile.
Read OOP_ARCHITECTURE_STANDARD.md Part C (ProfileLoader) carefully.

TASK: Create the ProfileLoader service and supporting profile repository.

STEPS:
1. Create backend/app/repositories/profile_loader.py:
   - Extend BaseRepository.
   - Methods:
     a. find_student_profile(user_id) -> StudentProfile | None
     b. find_parent_profile(user_id) -> ParentProfile | None
     c. find_teacher_profile(user_id) -> TeacherProfile | None
     d. find_admin_profile(user_id) -> AdminProfile | None
     e. find_content_manager_profile(user_id) -> ContentManagerProfile | None
     f. find_profile(user_id, profile_type: str) -> Any — dispatches to the correct method.
     g. create_profile(user_id, school_id, profile_type: str) -> Any — creates empty profile.
2. Create backend/app/services/profile_loader.py exactly as in OOP_ARCHITECTURE_STANDARD.md Part C.
3. Update backend/app/services/auth.py:
   - Import ProfileLoader.
   - In the register() method, after creating membership, call profile_loader.ensure_profile().
   - In the /me endpoint logic, use ProfileLoader to load all profiles for the user.
4. Update backend/app/services/profile.py:
   - Use ProfileLoader instead of direct profile queries where applicable.
5. Update backend/app/repositories/__init__.py — add ProfileLoaderRepository to exports.

RULES:
- ProfileLoader MUST use UnitOfWork for create_profile writes.
- find_* methods are read-only, no UoW needed.
- Do NOT change the existing StudentProfile, ParentProfile, TeacherProfile models.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

---

## Phase OOP-C: Domain Events + Delivery Strategies

### Prompt OOP-C1: Create Domain Event Classes

```
CONTEXT: You are working on Ecole Platform.
Read OOP_ARCHITECTURE_STANDARD.md Part D (Domain Events) carefully.

TASK: Create all domain event classes.

STEPS:
1. Create backend/app/domain/events/base.py — DomainEvent base class (exactly as in standard).
2. Create backend/app/domain/events/lms.py with these events:
   - GradePublished (student_id, course_title, score, teacher_name)
   - AssignmentCreated (assignment_id, course_title, due_at, class_id)
   - QuizCompleted (student_id, quiz_title, score_percent)
   - SubmissionReceived (submission_id, student_name, assignment_title, teacher_id)
   - ContentPublished (content_id, title, class_id)
3. Create backend/app/domain/events/calendar.py with these events:
   - EventCreated (event_id, title, start_at, class_id)
   - EventUpdated (event_id, title, changes: dict)
   - HolidayAdded (holiday_name, start_date, end_date)
   - EventRSVPReceived (event_id, user_id, status)
4. Create backend/app/domain/events/billing.py with these events:
   - InvoiceGenerated (invoice_id, student_id, amount, due_date)
   - PaymentReceived (payment_id, invoice_id, amount, method)
   - PaymentFailed (payment_id, invoice_id, reason)
5. Create backend/app/domain/events/documents.py with these events:
   - DocumentUploaded (document_id, filename, student_id)
   - DocumentExpiring (document_id, student_id, document_name, expires_at)
   - ResourceShared (resource_id, title, class_id)
6. Create backend/app/domain/events/auth.py with these events:
   - UserRegistered (user_id, role, school_id)
   - PasswordChanged (user_id)
   - TwoFactorEnabled (user_id)
7. Update backend/app/domain/events/__init__.py — export all events.

RULES:
- All events are frozen=True dataclasses.
- All events extend DomainEvent.
- Every event field must have a default value (None for UUID, "" for str, 0.0 for float).
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

### Prompt OOP-C2: Create Delivery Strategies

```
CONTEXT: You are working on Ecole Platform. OOP-C1 created domain event classes.
Read OOP_ARCHITECTURE_STANDARD.md Part D (Domain Events) carefully.

TASK: Create delivery strategy classes that replace direct notification calls.

STEPS:
1. Create backend/app/services/delivery/ directory.
2. Create backend/app/services/delivery/__init__.py.
3. Create backend/app/services/delivery/base.py — DeliveryStrategy ABC (as in standard).
4. Create backend/app/services/delivery/push.py:
   - PushDeliveryStrategy extends DeliveryStrategy.
   - deliver() method creates Notification rows + NotificationDelivery rows.
   - Reuse existing logic from notification_hub.py but encapsulated in strategy pattern.
   - Import and use NotificationRepository for DB operations.
5. Create backend/app/services/delivery/email_delivery.py:
   - EmailDeliveryStrategy extends DeliveryStrategy.
   - deliver() method sends email using existing email.py service logic.
   - Renders templates from backend/app/templates/email/.
6. Create backend/app/services/delivery/sms_delivery.py:
   - SMSDeliveryStrategy extends DeliveryStrategy.
   - deliver() method uses existing sms.py service logic.
7. Create backend/app/services/delivery/in_app.py:
   - InAppDeliveryStrategy extends DeliveryStrategy.
   - deliver() creates Notification rows with is_read=False for in-app display.
8. Create backend/app/services/event_dispatcher.py:
   - EventDispatcher class (as in standard).
   - Register ALL events from OOP-C1 with appropriate strategies.
   - GradePublished -> push + email + in_app.
   - AssignmentCreated -> push + in_app.
   - InvoiceGenerated -> push + email.
   - DocumentExpiring -> push + email.
   - PaymentReceived -> push + in_app.
   - UserRegistered -> email (welcome).
   - All others -> in_app only.

RULES:
- Strategies must NOT import other services directly — use repositories.
- Each strategy is independent — failure in one doesn't block others (try/except per strategy).
- Do NOT delete notification_hub.py or email.py yet — strategies wrap their logic.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

### Prompt OOP-C3: Wire Domain Events into Services

```
CONTEXT: You are working on Ecole Platform. OOP-C1 and OOP-C2 created events and strategies.
Read OOP_ARCHITECTURE_STANDARD.md Part D (Domain Events) for the before/after pattern.

TASK: Update services to emit domain events instead of directly calling notification/email services.

STEPS:
1. For EACH service that currently calls notification_hub directly, refactor to emit events:
   - backend/app/services/lms.py (or the split sub-services if OOP-F already done):
     a. publish_grade -> emit GradePublished
     b. create_assignment -> emit AssignmentCreated
     c. submit_quiz -> emit QuizCompleted
     d. receive_submission -> emit SubmissionReceived
   - backend/app/services/calendar.py:
     a. create_event -> emit EventCreated
     b. update_event -> emit EventUpdated
   - backend/app/services/billing.py:
     a. generate_invoices -> emit InvoiceGenerated
     b. process_payment -> emit PaymentReceived / PaymentFailed
   - backend/app/services/student_documents.py:
     a. upload_document -> emit DocumentUploaded
     b. check_expiring_documents -> emit DocumentExpiring per document
   - backend/app/services/resource_library.py:
     a. share_resource -> emit ResourceShared
   - backend/app/services/auth.py:
     a. register -> emit UserRegistered
2. Add EventDispatcher as a dependency in each updated service:
   - `self._dispatcher = EventDispatcher(self.db)`
3. Keep existing notification_hub calls as FALLBACK until all strategies are verified.
   - Add a comment: `# TODO: Remove after event dispatcher verification`

RULES:
- Emit events AFTER the UnitOfWork commit (data must be persisted first).
- Each emit call should be in a try/except so event dispatch failure doesn't break the main operation.
- Do NOT change router signatures or response shapes.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

---

## Phase OOP-D: Evaluatable Protocol + Student Work Unification

### Prompt OOP-D1: Create Protocols + Grading Strategies

```
CONTEXT: You are working on Ecole Platform.
Read OOP_ARCHITECTURE_STANDARD.md Part E (Evaluatable Protocol) carefully.

TASK: Create the Evaluatable protocol, GradingStrategy ABC, and concrete strategies.

STEPS:
1. Create backend/app/domain/protocols/evaluatable.py — Evaluatable Protocol (as in standard).
2. Create backend/app/domain/protocols/grading.py:
   - GradingStrategy ABC (as in standard).
   - QuizAutoGradeStrategy — auto-grades from JSONB answers.
   - ManualGradeStrategy — validates teacher-provided score using MoroccanGrade.
3. Update backend/app/domain/protocols/__init__.py — export all.
4. Update backend/app/repositories/quiz.py:
   - Add methods to satisfy Evaluatable protocol: list_for_class, list_for_student, get_detail, get_results.
   - These can wrap existing methods with the correct return signature.
5. Update backend/app/repositories/lms.py:
   - Add Evaluatable-compatible methods for assignments: list_for_class, list_for_student, get_detail, get_results.
   - Add Evaluatable-compatible methods for assessments: same pattern.
6. Verify that all three repositories satisfy the Evaluatable protocol at runtime.

RULES:
- Protocol methods return list[dict] for consistency across types.
- Each dict must include: id, title, type ("quiz"|"assignment"|"assessment"), due_at, status, total_points.
- GradingStrategy uses MoroccanGrade value object from domain/value_objects/grade.py.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

### Prompt OOP-D2: Create StudentWorkService + Router

```
CONTEXT: You are working on Ecole Platform. OOP-D1 created protocols and strategies.
Read OOP_ARCHITECTURE_STANDARD.md Part E (Evaluatable Protocol) carefully.

TASK: Create the unified StudentWorkService and expose it via a new router endpoint.

STEPS:
1. Create backend/app/services/student_work.py — StudentWorkService (as in standard).
   - list_all_for_student: combines assignments + quizzes + assessments.
   - list_all_for_class: combines all for a class view.
   - Each item includes: id, type, title, due_at, status, total_points, grading_type.
2. Create backend/app/schemas/student_work.py:
   - StudentWorkItem schema (id, type, title, due_at, status, total_points, grading_type).
   - StudentWorkListResponse schema (items: list[StudentWorkItem], total: int).
3. Add endpoints to backend/app/api/v1/content.py (or create a new router):
   - GET /student-work — list all work for current student.
   - GET /student-work/class/{class_id} — list all work for a class (teacher view).
   Both return StudentWorkListResponse.
4. Register new endpoints in backend/app/api/v1/router.py.
5. Add appropriate permissions:
   - Student viewing own work: PERM_LMS_CONTENT_READ
   - Teacher viewing class work: PERM_LMS_CONTENT_READ + class ownership check.

RULES:
- StudentWorkService delegates to repositories, does not query DB directly.
- Response shape is unified — frontend doesn't need to know which table data came from.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

---

## Phase OOP-E: LMS Service Splitting

### Prompt OOP-E1: Split lms.py into Sub-Services

```
CONTEXT: You are working on Ecole Platform. backend/app/services/lms.py is 76KB.
Read OOP_ARCHITECTURE_STANDARD.md Part F (LMS Service Splitting) carefully.

TASK: Split lms.py into focused sub-services.

STEPS:
1. Create directory: backend/app/services/lms/
2. Analyze backend/app/services/lms.py — identify method groups:
   - Course methods: create_course, update_course, list_courses, get_course, delete_course, etc.
   - Assignment methods: create_assignment, update_assignment, list_assignments, etc.
   - Quiz methods: create_quiz, update_quiz, list_quizzes, attempt_quiz, grade_quiz, etc.
   - Content methods: create_content_item, update_content_item, publish_content, track_progress, etc.
   - Progress methods: get_student_progress, get_class_progress, aggregate_progress, etc.
3. Create backend/app/services/lms/course_service.py:
   - Move all Course-related methods from lms.py.
   - Class: CourseService(db: AsyncSession).
   - Keep exact same method signatures and return types.
4. Create backend/app/services/lms/assignment_service.py:
   - Move all Assignment + Submission + Grade methods.
   - Class: AssignmentService(db: AsyncSession).
5. Create backend/app/services/lms/quiz_service.py:
   - Move all Quiz + QuizAttempt methods.
   - Class: QuizService(db: AsyncSession).
6. Create backend/app/services/lms/content_service.py:
   - Move all ContentItem + ContentProgress methods.
   - Class: ContentService(db: AsyncSession).
7. Create backend/app/services/lms/progress_service.py:
   - Move all progress aggregation methods.
   - Class: ProgressService(db: AsyncSession).
8. Create backend/app/services/lms/_helpers.py:
   - Move shared helper functions used across multiple sub-services.
9. Create backend/app/services/lms/__init__.py:
   - Re-export all service classes.
   - Also export a backward-compatible LMSService that delegates to sub-services.
10. Update ALL routers that import from services/lms.py:
    - Change `from app.services.lms import LMSService` to specific sub-service.
    - Update service instantiation in each router endpoint.
    - Routers to update: courses.py, assignments.py, submissions.py, quizzes.py, content.py, content_library.py, results.py, progress.py, assessments.py, activities.py.
11. Delete the original backend/app/services/lms.py (replaced by lms/ directory).

RULES:
- Each sub-service must use UnitOfWork for write operations.
- Method signatures MUST NOT change — same params, same return types.
- If a method in one sub-service needs to call another sub-service, create the dependency in __init__.
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Test each router still resolves its imports after the split.
```

---

## Phase OOP-F: Validation + Cleanup

### Prompt OOP-F1: Full Validation

```
CONTEXT: You are working on Ecole Platform. All OOP refactoring prompts (A1-E1) have been executed.

TASK: Validate that all OOP patterns are correctly implemented.

CHECKS:
1. Unit of Work:
   - grep for "db.commit()" in ALL service files — should be ZERO occurrences (only uow.commit).
   - grep for "db.rollback()" in ALL service files — should be ZERO (only uow.rollback).
   - Verify UnitOfWork import exists in every service that writes data.

2. Value Objects:
   - Verify all files exist in backend/app/domain/value_objects/.
   - Verify MoroccanGrade validates 0-20 range.
   - Verify Money validates non-negative.
   - Verify RoleSet validates against VALID_ROLES.

3. ProfileLoader:
   - Verify AdminProfile and ContentManagerProfile models exist in iam.py.
   - Verify migration file exists and creates both tables.
   - Verify ProfileLoader service loads profiles for all 5 role types.

4. Domain Events:
   - Verify all event files exist in domain/events/.
   - Verify EventDispatcher has all events registered.
   - Verify at least 5 services emit events instead of direct notification calls.

5. Evaluatable Protocol:
   - Verify QuizRepository, AssignmentRepository (in LMS), and AssessmentRepository all satisfy the Evaluatable protocol.
   - Verify StudentWorkService combines all three.
   - Verify /student-work endpoint exists in router.py.

6. LMS Split:
   - Verify backend/app/services/lms/ directory exists with 5 sub-service files.
   - Verify original lms.py is gone (replaced by directory).
   - Verify all routers that used LMSService now use specific sub-services.
   - Verify each sub-service is under 500 lines.

7. Import Health:
   - Run: python -c "from app.core.unit_of_work import UnitOfWork; print('OK')"
   - Run: python -c "from app.domain.value_objects.grade import MoroccanGrade; print('OK')"
   - Run: python -c "from app.domain.events.lms import GradePublished; print('OK')"
   - Run: python -c "from app.services.lms import CourseService; print('OK')"
   - Run: python -c "from app.services.event_dispatcher import EventDispatcher; print('OK')"

OUTPUT: A table with PASS/FAIL for each check, plus details on any failures.

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- If any check fails, list the specific files and lines that need fixing.
- Do NOT fix issues in this prompt — just report them.
```

---

## Summary

| Phase | Prompt | What It Does | New Files |
|-------|--------|-------------|-----------|
| OOP-A1 | Value Objects | domain/ directory + 4 value objects | ~8 files |
| OOP-A2 | UnitOfWork (core) | UoW class + integrate into auth/billing/erp | 1 new + 3 modified |
| OOP-A3 | UnitOfWork (all) | Integrate UoW into all remaining services | ~20 modified |
| OOP-B1 | Profile Models | AdminProfile + ContentManagerProfile + migration | 2 modified + 1 new |
| OOP-B2 | ProfileLoader | ProfileLoader service + repository | 2 new + 3 modified |
| OOP-C1 | Domain Events | All event dataclasses | ~7 files |
| OOP-C2 | Delivery Strategies | Push/Email/SMS/InApp strategies + dispatcher | ~7 files |
| OOP-C3 | Wire Events | Services emit events instead of direct calls | ~10 modified |
| OOP-D1 | Protocols | Evaluatable + GradingStrategy + repo updates | ~4 files |
| OOP-D2 | StudentWork | Unified service + router + schema | 3 new + 1 modified |
| OOP-E1 | LMS Split | Split 76KB lms.py into 5 sub-services | 7 new + ~10 modified |
| OOP-F1 | Validation | Full check of all patterns | 0 files (report only) |
