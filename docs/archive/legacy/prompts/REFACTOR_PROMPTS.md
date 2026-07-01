# École Platform — 3-Tier Refactoring Prompts

> Each prompt is self-contained. Copy-paste it into a new session.
> After finishing a batch, close the session and open a new one for the next batch.
> Works identically in Claude Code or Codex — both produce the same 3-tier output.
> **Open folder:** `Ecole-Platform/ecole-platform-dev/` (NOT the parent folder)

---

## Pre-Requisite: Shared Utilities (Run this FIRST)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture (Router → Service → Repository).

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — this is the mandatory pattern. Follow it exactly.
2. Read backend/app/core/dependencies.py — understand existing DI
3. Read backend/app/repositories/ — see existing repositories (notifications.py, calendar.py, documents.py, reports.py)
4. Read backend/app/core/exceptions.py — understand error patterns

TASK: Create the shared foundation files.

STEP 1 — Create backend/app/repositories/base.py:
- BaseRepository class with __init__(self, db: AsyncSession)
- That's it — simple base class

STEP 2 — Create backend/app/core/request_utils.py:
- Move/consolidate duplicated helper functions from routers into this shared module
- Search ALL files in backend/app/api/v1/ for functions named: _get_client_ip, _request_locale, _optional_current_user, _serialize_device, or any other locally-defined helpers
- Create clean shared versions in request_utils.py
- DO NOT change any router code yet — just create the shared file

STEP 3 — Update existing repositories to extend BaseRepository:
- backend/app/repositories/notifications.py
- backend/app/repositories/calendar.py
- backend/app/repositories/documents.py
- backend/app/repositories/reports.py
- Make them inherit from BaseRepository instead of taking db in __init__ manually
- Keep all their existing methods unchanged

STEP 4 — Wire existing repositories to their services:
- Read backend/app/services/notification_hub.py — update it to use NotificationRepository
- Read backend/app/services/calendar.py — update it to use CalendarRepository
- Read backend/app/services/student_documents.py — update it to use DocumentRepository
- Read backend/app/services/reports.py — update it to use ReportRepository
- For each: replace self.db.execute(select(...)) calls with self.repo.method() calls
- Service keeps self.db ONLY for commit/rollback

STEP 5 — Update routers to use shared helpers:
- In ALL router files under backend/app/api/v1/, replace local _get_client_ip() and _request_locale() with imports from app.core.request_utils
- Delete the local function definitions after replacing

STEP 6 — Verify:
- Run: cd backend && python -c "from app.repositories.base import BaseRepository; print('OK')"
- Run: cd backend && python -c "from app.core.request_utils import get_client_ip, request_locale; print('OK')"
- Check that no router file defines _get_client_ip or _request_locale locally anymore

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior — same input, same output
- Do NOT change any model or schema
- Do NOT change any test file
- Follow ARCHITECTURE_STANDARD.md exactly
```

---

## Batch 1 — Core Authentication & Audit (Phases 2, 2A, 2B)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — this is the mandatory pattern. Follow it exactly.
2. Read backend/app/repositories/base.py — the base class
3. Read backend/app/services/auth.py — current service (2-tier, has embedded SQL)
4. Read backend/app/services/audit.py — current audit service
5. Read backend/app/models/iam.py — User, Membership, Session, Invitation models
6. Read backend/app/api/v1/auth.py — current router
7. Read backend/app/api/v1/recovery.py — account recovery router
8. Read backend/app/api/v1/invitations.py — invitation router

TASK: Extract AuthRepository and AuditRepository from their services.

STEP 1 — Create backend/app/repositories/auth.py:
- Class AuthRepository(BaseRepository)
- Extract ALL SQLAlchemy queries from services/auth.py into repository methods
- Methods should include (but discover all by reading auth.py):
  - get_user_by_email(email) → User | None
  - get_user_by_id(user_id) → User | None
  - get_user_with_memberships(user_id) → User | None
  - create_user(**kwargs) → User
  - update_user(user_id, **kwargs) → User
  - create_session(user_id, ip, ua, ...) → Session
  - revoke_session(session_id) → None
  - revoke_all_sessions(user_id) → int (count)
  - get_session_by_id(session_id) → Session | None
  - get_membership(user_id, school_id) → Membership | None
  - list_memberships(user_id) → list[Membership]
  - get_invitation_by_code(code) → Invitation | None
  - consume_invitation(invitation_id) → None
  - create_recovery_request(user_id, token, ...) → RecoveryRequest
  - get_recovery_by_token(token) → RecoveryRequest | None
  - Read auth.py carefully — extract EVERY query, don't miss any

STEP 2 — Create backend/app/repositories/audit.py:
- Class AuditRepository(BaseRepository)
- Extract from services/audit.py:
  - create_log(action, actor_id, resource_type, resource_id, ...) → AuditLog
  - list_logs(filters, cursor, limit) → list[AuditLog]

STEP 3 — Update backend/app/services/auth.py:
- Add: self.repo = AuthRepository(db) in __init__
- Add: self.audit = AuditRepository(db) in __init__
- Replace every self.db.execute(select(User)...) with self.repo.get_user_by_*()
- Replace every self.db.add(Session(...)) with self.repo.create_session(...)
- Remove all sqlalchemy query imports (select, update, delete, etc.)
- Keep self.db ONLY for commit() and rollback()
- Keep all business logic (password checks, JWT creation, rate limiting, 2FA verification)

STEP 4 — Update backend/app/services/audit.py:
- Same pattern: use AuditRepository, remove direct SQL

STEP 5 — Update routers if needed:
- backend/app/api/v1/auth.py — ensure it uses shared helpers from core/request_utils.py
- backend/app/api/v1/recovery.py — same
- backend/app/api/v1/invitations.py — same
- Add OpenAPI metadata (summary, response_description) if missing

STEP 6 — Run verification:
- Run: cd backend && python -c "from app.repositories.auth import AuthRepository; print('OK')"
- Run: cd backend && python -c "from app.services.auth import AuthService; print('OK')"
- Confirm no import errors

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior — same input, same output
- Do NOT change any model or schema
- Do NOT change or delete any test — all existing tests must still pass
- Follow ARCHITECTURE_STANDARD.md exactly
- auth.py is 1,707 lines — take your time, don't miss any query
```

---

## Batch 2 — Billing & Payments (Phase 3 billing domain)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — follow it exactly.
2. Read backend/app/repositories/base.py
3. Read backend/app/services/payment_retry.py — payment retry logic
4. Read backend/app/services/overdue_reminders.py — invoice reminder logic
5. Read backend/app/models/billing.py — Invoice, Payment, PaymentAttempt models
6. Read backend/app/api/v1/billing.py — billing router (674 lines)
7. Read backend/app/api/v1/payments.py — payments router
8. Read backend/app/api/v1/invoices.py — invoices router

TASK: Extract BillingRepository from the billing services and routers.

STEP 1 — Create backend/app/repositories/billing.py:
- Class BillingRepository(BaseRepository)
- Extract ALL invoice/payment queries from:
  - services/payment_retry.py
  - services/overdue_reminders.py
  - AND any inline queries in api/v1/billing.py, payments.py, invoices.py
- Methods should include:
  - get_invoice_by_id(invoice_id) → Invoice | None
  - list_invoices(school_id, filters, cursor, limit) → list[Invoice]
  - create_invoice(**kwargs) → Invoice
  - update_invoice(invoice_id, **kwargs) → Invoice
  - get_payment_by_id(payment_id) → Payment | None
  - list_payments(invoice_id) → list[Payment]
  - create_payment(**kwargs) → Payment
  - get_failed_attempts(since, limit) → list[PaymentAttempt]
  - get_overdue_invoices(days_overdue, limit) → list[Invoice]
  - Discover ALL queries by reading the source files

STEP 2 — Create backend/app/services/billing.py (if it doesn't exist as a unified service):
- BillingService that orchestrates billing business logic
- Uses BillingRepository for all data access
- Integrates payment_retry and overdue_reminders logic

STEP 3 — Update existing services:
- payment_retry.py → use BillingRepository
- overdue_reminders.py → use BillingRepository

STEP 4 — Update routers:
- billing.py, payments.py, invoices.py → call BillingService, not raw SQL
- Use shared helpers from core/request_utils.py
- Add OpenAPI metadata if missing

STEP 5 — Verify: no import errors, no raw SQL in services/routers

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior
- Do NOT change any model or schema
- Do NOT change any test
- Follow ARCHITECTURE_STANDARD.md exactly
```

---

## Batch 3 — ERP Domain: Classes, Attendance, Timetable (Phase 3 ERP)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — follow it exactly.
2. Read backend/app/repositories/base.py
3. Read backend/app/models/erp.py — AcademicYear, Period, Class, Enrollment, Attendance models
4. Read backend/app/api/v1/classes.py
5. Read backend/app/api/v1/attendance.py (387 lines)
6. Read backend/app/api/v1/timetable.py (874 lines)
7. Read backend/app/api/v1/enrollments.py
8. Read backend/app/api/v1/class_assignments.py

TASK: Extract ERPRepository (or split into ClassRepository, AttendanceRepository, TimetableRepository if too large).

STEP 1 — Create backend/app/repositories/erp.py:
- Extract ALL ERP queries from the routers above
- If routers contain inline SQL (common in Phase 3), extract those too
- Methods for:
  - Classes: get_class, list_classes, create_class, update_class
  - Enrollments: enroll_student, list_enrollments, remove_enrollment
  - Attendance: create_session, mark_attendance, list_attendance, get_stats
  - Timetable: get_weekly_schedule, create_slot, update_slot, detect_conflicts

STEP 2 — Create backend/app/services/erp.py (unified ERP service, or split if >500 lines):
- Business logic: enrollment validation, conflict detection, attendance rules
- Uses ERPRepository for all data access

STEP 3 — Update routers:
- classes.py, attendance.py, timetable.py, enrollments.py, class_assignments.py
- Replace inline SQL with service calls
- Use shared helpers from core/request_utils.py

STEP 4 — Verify: no import errors, no raw SQL in routers

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior
- Do NOT change any model or schema
- Do NOT change any test
- Follow ARCHITECTURE_STANDARD.md exactly
- timetable.py is 874 lines — be thorough
```

---

## Batch 4 — LMS Domain: Content, Assignments, Submissions, Quizzes (Phase 3 LMS)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — follow it exactly.
2. Read backend/app/repositories/base.py
3. Read backend/app/models/lms.py (700 lines) — Courses, Assignments, Submissions, Grades, Content
4. Read backend/app/services/resource_library.py (464 lines)
5. Read backend/app/services/quiz_grading.py (145 lines)
6. Read backend/app/api/v1/content.py (511 lines)
7. Read backend/app/api/v1/assignments.py (369 lines)
8. Read backend/app/api/v1/submissions.py (700 lines)
9. Read backend/app/api/v1/quizzes.py (795 lines)
10. Read backend/app/api/v1/courses.py
11. Read backend/app/api/v1/content_library.py (447 lines)
12. Read backend/app/api/v1/assessments.py (396 lines)
13. Read backend/app/api/v1/results.py

TASK: Extract LMS repositories from services and routers.

STEP 1 — Create backend/app/repositories/lms.py:
- Class LMSRepository(BaseRepository) — or split into CourseRepository, AssignmentRepository, etc. if too large
- Extract ALL LMS queries from services AND routers
- This is the biggest domain — be thorough

STEP 2 — Create backend/app/repositories/quiz.py:
- Class QuizRepository(BaseRepository)
- Extract from quiz_grading.py and quizzes.py router

STEP 3 — Create/update backend/app/services/lms.py:
- LMSService using LMSRepository
- Keep resource_library.py and quiz_grading.py but update to use repositories

STEP 4 — Update ALL LMS routers to use services instead of inline SQL

STEP 5 — Verify: no import errors, no raw SQL in services/routers

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior
- Do NOT change any model or schema
- Do NOT change any test
- Follow ARCHITECTURE_STANDARD.md exactly
- submissions.py (700 lines) and quizzes.py (795 lines) are large — don't skip queries
```

---

## Batch 5 — Communication, Progress & Analytics (Phases 3C, 3E, 8, 14)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — follow it exactly.
2. Read backend/app/repositories/base.py
3. Read backend/app/services/progress.py (816 lines)
4. Read backend/app/services/dashboard_analytics.py (605 lines)
5. Read backend/app/services/kpi.py (355 lines)
6. Read backend/app/services/data_export.py (186 lines)
7. Read backend/app/api/v1/progress.py
8. Read backend/app/api/v1/analytics.py
9. Read backend/app/api/v1/exports.py
10. Read backend/app/api/v1/messaging.py (705 lines)
11. Read backend/app/api/v1/announcements.py (407 lines)
12. Read backend/app/api/v1/cms.py (468 lines)
13. Read backend/app/api/v1/feed.py

TASK: Extract repositories for progress, analytics, messaging, and CMS.

STEP 1 — Create backend/app/repositories/progress.py:
- Extract from services/progress.py: student progress queries, completion tracking, grade aggregation

STEP 2 — Create backend/app/repositories/analytics.py:
- Extract from services/dashboard_analytics.py and services/kpi.py
- KPI computation queries, aggregation logic

STEP 3 — Create backend/app/repositories/messaging.py:
- Extract from api/v1/messaging.py: conversation queries, message CRUD

STEP 4 — Create backend/app/repositories/cms.py:
- Extract from api/v1/cms.py and announcements.py: page CRUD, announcement queries

STEP 5 — Update all services to use their repositories
STEP 6 — Update all routers to use services (not inline SQL)
STEP 7 — Update data_export.py to use repositories for its queries

STEP 8 — Verify: no import errors, no raw SQL in services/routers

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior
- Do NOT change any model or schema
- Do NOT change any test
- Follow ARCHITECTURE_STANDARD.md exactly
```

---

## Batch 6 — Admin, Profiles, GDPR & Feature Flags (Remaining)

```md
I'm refactoring "École Platform" backend to a consistent 3-tier architecture.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — follow it exactly.
2. Read backend/app/repositories/base.py
3. Read backend/app/api/v1/admin.py (902 lines) — largest router
4. Read backend/app/api/v1/profiles.py (315 lines)
5. Read backend/app/api/v1/teacher.py (270 lines)
6. Read backend/app/api/v1/gdpr.py (469 lines)
7. Read backend/app/api/v1/features.py (289 lines)
8. Read backend/app/api/v1/consents.py (163 lines)
9. Read backend/app/api/v1/ai.py (429 lines)
10. Read backend/app/services/ai.py (565 lines)

TASK: Extract remaining repositories and ensure full 3-tier coverage.

STEP 1 — Create backend/app/repositories/admin.py:
- Extract from admin.py router: user management, school config, bulk operations

STEP 2 — Create backend/app/repositories/profile.py:
- Extract from profiles.py and teacher.py: profile CRUD, role-specific data

STEP 3 — Create backend/app/repositories/gdpr.py:
- Extract from gdpr.py: data export queries, deletion requests, consent management

STEP 4 — Create backend/app/repositories/feature.py:
- Extract from features.py: feature flag queries, targeting rules

STEP 5 — Update ai.py service if it has any DB logic

STEP 6 — Update ALL routers to use services
STEP 7 — Admin.py is 902 lines — extract into AdminService + AdminRepository carefully

FINAL VERIFICATION — After this batch, run these checks:
- Search ALL files in backend/app/api/v1/ for "from sqlalchemy" — there should be ZERO matches (except possibly for type annotations)
- Search ALL files in backend/app/services/ for "select(" — there should be ZERO matches
- Every service should only import AsyncSession for commit/rollback
- Every repository should extend BaseRepository

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any API endpoint behavior
- Do NOT change any model or schema
- Do NOT change any test
- Follow ARCHITECTURE_STANDARD.md exactly
- admin.py is the largest router (902 lines) — be very thorough
```

---

## Post-Refactor: Final Validation Prompt

```md
I've just finished refactoring "École Platform" backend to a 3-tier architecture across 6 batches.

BEFORE ANYTHING, read ARCHITECTURE_STANDARD.md to understand the pattern.

TASK: Full validation pass.

STEP 1 — Verify no SQL leaks:
- Search backend/app/api/v1/ for any remaining "from sqlalchemy import" or "select(" or "db.execute"
- Search backend/app/services/ for any remaining "select(" or "from sqlalchemy import select"
- List any violations found

STEP 2 — Verify all repositories extend BaseRepository:
- List all files in backend/app/repositories/
- Check each one inherits from BaseRepository

STEP 3 — Verify all services use repositories:
- List all files in backend/app/services/
- Check each one creates repository instances in __init__
- Confirm no service directly calls db.execute()

STEP 4 — Verify shared helpers:
- Search backend/app/api/v1/ for any local definitions of _get_client_ip or _request_locale
- There should be ZERO — all should import from app.core.request_utils

STEP 5 — Run import checks:
- python -c "from app.repositories import *; print('All repos OK')"
- python -c "from app.services import *; print('All services OK')"

STEP 6 — Fix any violations found

STEP 7 — List all files you changed so I can review and commit myself.

Do NOT change any API behavior. Do NOT change tests. Only fix architectural violations.
Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
```

---

# PART A2 — Fix Missing Features from Phases 14-16

---

## Fix Phase 14 Gaps: PDF Templates & Analytics

```md
I'm fixing missing features from Phase 14 (Reports & Analytics) in "École Platform".

BEFORE YOU WRITE ANY CODE, read:
1. Read ARCHITECTURE_STANDARD.md — follow the 3-tier pattern
2. Read backend/app/services/reports.py — understand the report generation service
3. Read backend/app/templates/email/ — see existing Jinja2 email templates as reference
4. Read backend/app/api/v1/analytics.py — current analytics endpoints
5. Read CLAUDE_PROMPTS_2.md Phase 14 section — the original specification

TASK: Complete the missing Phase 14 deliverables.

STEP 1 — Create PDF report templates:
Create backend/app/templates/reports/ directory with these Jinja2 HTML templates:
- student_report_card.html — Student name, photo placeholder, grades table (subject, grade/20, teacher comment, class average), attendance summary, teacher remarks, principal signature block
- class_summary.html — Class name, academic year, student roster with averages, subject breakdown, ranking table, class statistics
- attendance_report.html — Date range, per-student attendance (present/absent/late counts), justification status, percentage chart placeholder
- billing_statement.html — Parent name, student name, invoice list with amounts, payments received, balance due, payment history table

TEMPLATE REQUIREMENTS:
- All templates must support fr/ar/en via conditional blocks: {% if lang == 'ar' %}...{% endif %}
- Arabic templates must use dir="rtl" on the HTML body
- Use the Moroccan 0-20 grading scale in grade displays
- Use Moroccan date format (dd/mm/yyyy)
- Professional styling: clean tables, school logo placeholder, page borders
- WeasyPrint-compatible CSS (no flexbox, use tables for layout)

STEP 2 — Add weekly analytics aggregation:
In backend/app/services/dashboard_analytics.py:
- Add 'weekly' as a valid bucket option alongside 'daily' and 'monthly'
- Implement week-based grouping in get_attendance() and get_engagement()

STEP 3 — Verify:
- python -c "from jinja2 import Environment, FileSystemLoader; e=Environment(loader=FileSystemLoader('app/templates/reports')); print([t for t in e.list_templates()])"

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Follow existing template patterns from email templates
- Do NOT change any API endpoint behavior
- Do NOT change any existing template
```

---

## Fix Phase 15 Gaps: Holiday CRUD & Event Colors

```md
I'm fixing missing features from Phase 15 (Calendar & Events) in "École Platform".

BEFORE YOU WRITE ANY CODE, read:
1. Read ARCHITECTURE_STANDARD.md — follow the 3-tier pattern
2. Read backend/app/services/calendar.py — current calendar service
3. Read backend/app/models/calendar.py — MoroccanHoliday model
4. Read backend/app/api/v1/events.py — current event endpoints
5. Read backend/app/core/permissions.py — current permissions

TASK: Complete the missing Phase 15 deliverables.

STEP 1 — Add Holiday CRUD endpoints:
In backend/app/api/v1/events.py (or a new holidays.py router):
- POST /calendar/holidays — Create holiday (ADM/DIR only)
- PUT /calendar/holidays/{id} — Update holiday (ADM/DIR only)
- DELETE /calendar/holidays/{id} — Delete holiday (ADM/DIR only)
- GET /calendar/holidays — List holidays for academic year (all roles, read-only)

Add permission constants if needed:
- PERM_CAL_HOLIDAY_MANAGE in permissions.py, assigned to ADM and DIR

Use the repository pattern — create or update the calendar repository.

STEP 2 — Add event type color coding:
In the Event response schema (or in calendar.py service):
- Add a color field to event responses based on event type:
  - holiday: #E8F5E9 (green)
  - exam: #FFEBEE (red)
  - meeting: #E3F2FD (blue)
  - excursion: #FFF3E0 (orange)
  - ceremony: #F3E5F5 (purple)
  - custom: #F5F5F5 (grey)

STEP 3 — Verify:
- python -c "from app.api.v1.events import router; print([r.path for r in router.routes])"

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Follow 3-tier pattern (Router → Service → Repository)
- Do NOT change existing endpoint behavior
```

---

## Fix Phase 16 Gaps: ResourcesPage, Expiry, Bulk Ops

```md
I'm fixing missing features from Phase 16 (Document Management) in "École Platform".

BEFORE YOU WRITE ANY CODE, read:
1. Read ARCHITECTURE_STANDARD.md — follow web patterns (PART B) and backend patterns (PART A)
2. Read web/src/features/documents/DocumentsPage.tsx — working documents page as reference
3. Read web/src/features/documents/ResourcesPage.tsx — current stub (137 bytes)
4. Read backend/app/api/v1/documents.py — current document endpoints
5. Read backend/app/services/resource_library.py — resource library service
6. Read backend/app/services/student_documents.py — student documents service

TASK: Complete the missing Phase 16 deliverables.

STEP 1 — Implement ResourcesPage.tsx:
Create a full implementation with:
- Resource list with search bar (full-text search)
- Filters: subject, level, type, tags
- Card layout: title, description, type badge, author, avg rating, download count
- Upload form (TCH/ADM only): title, description, subject, level, type, tags, file
- Click → resource detail with download button
- Rate resource (1-5 stars)
- Pagination (cursor-based)
- Loading/error/empty states
- Use the web Hook + Service pattern from ARCHITECTURE_STANDARD.md if React Query is already set up, otherwise use direct api calls for now

STEP 2 — Add document expiry notifications:
In backend/app/services/student_documents.py or a new scheduled task:
- Add method: check_expiring_documents() — find documents expiring within 30 days
- For each expiring document, create a notification via NotificationHubService:
  - category: "system"
  - recipients: document uploader + linked student's parents
  - message: "Document {name} expires on {date}"
- Register this as an ARQ periodic task (daily at 08:00 Africa/Casablanca)

STEP 3 — Add bulk document operations:
In backend/app/api/v1/documents.py:
- POST /documents/bulk-download — Accept list of document_ids, create ZIP file, return download URL
- POST /documents/bulk-delete — Accept list of document_ids, soft-delete all (ADM only)
Add permissions: PERM_DOC_BULK_DOWNLOAD, PERM_DOC_BULK_DELETE if needed

STEP 4 — Verify:
- cd web && npm run build
- python -c "from app.api.v1.documents import router; print([r.path for r in router.routes])"

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Follow ARCHITECTURE_STANDARD.md patterns
- ResourcesPage must be >200 lines with real functionality
- Bulk operations must respect RBAC
```

---

# PART B — Web Frontend Refactoring (React Query + Hooks + Services)

---

## Web Pre-Requisite: Install React Query & Create Shared Setup

```md
I'm refactoring the "École Platform" React web frontend to use React Query with a Hook + Service pattern.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — sections 11-17 (PART B - Web Frontend)
2. Read web/package.json — current dependencies
3. Read web/src/main.tsx — current app entry
4. Read web/src/services/api/client.ts — current API client
5. Read web/src/services/auth/AuthContext.tsx — current auth context
6. Read web/src/app/App.tsx — current routing

TASK: Install React Query and set up the shared foundation.

STEP 1 — Install @tanstack/react-query:
- Run: cd web && npm install @tanstack/react-query@5

STEP 2 — Update web/src/main.tsx:
- Import QueryClient and QueryClientProvider from @tanstack/react-query
- Create QueryClient with defaults:
  - staleTime: 5 * 60 * 1000 (5 min)
  - retry: 2
  - refetchOnWindowFocus: true
- Wrap the existing app tree with QueryClientProvider
- Keep BrowserRouter and AuthProvider as-is

STEP 3 — Create web/src/shared/hooks/useQueryDefaults.ts:
- Export stale time constants matching backend cache TTLs:
  - STALE_FEED: 5 min
  - STALE_NOTIFICATIONS: 2 min
  - STALE_CONTENT: 15 min
  - STALE_RESULTS: 10 min
  - STALE_INVOICES: 10 min
  - STALE_DEFAULT: 5 min

STEP 4 — Verify:
- Run: cd web && npm run build (should compile with no errors)

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change any page component yet
- Do NOT change the API client
- Do NOT change AuthContext
- Do NOT change routing
```

---

## Web Batch 1 — Core Features: Notifications, Feed, Calendar

```md
I'm refactoring the "École Platform" React web frontend to use React Query.

BEFORE YOU WRITE ANY CODE, read these files in this exact order:
1. Read ARCHITECTURE_STANDARD.md — sections 11-17 (PART B)
2. Read web/src/shared/hooks/useQueryDefaults.ts — stale time constants
3. Read web/src/services/api/client.ts — API client methods
4. Read web/src/features/notifications/NotificationsPage.tsx
5. Read web/src/features/notifications/NotificationSettingsPage.tsx
6. Read web/src/features/notifications/types.ts (if exists)
7. Read web/src/features/feed/FeedPage.tsx
8. Read web/src/features/calendar/CalendarPage.tsx
9. Read web/src/features/calendar/EventDetailPage.tsx (if exists)
10. Read web/src/features/calendar/CreateEventPage.tsx (if exists)

TASK: Extract services and hooks for notifications, feed, and calendar.

FOR EACH FEATURE (notifications, feed, calendar):

STEP 1 — Create {feature}.service.ts:
- Extract ALL api.get/post/patch/list/delete calls from the page into a service object
- Each method is a pure async function returning typed response
- Follow ARCHITECTURE_STANDARD.md §13 exactly

STEP 2 — Create use{Feature}.ts:
- For list endpoints: use useInfiniteQuery with cursor pagination
- For single-item endpoints: use useQuery
- For mutations (mark read, create event, etc.): use useMutation with query invalidation
- Set staleTime from useQueryDefaults constants
- Follow ARCHITECTURE_STANDARD.md §14 exactly

STEP 3 — Update the page:
- Remove all useState for server data (items, loading, error, cursor, hasMore)
- Remove all useEffect for data fetching
- Remove all useCallback fetch functions
- Replace with hook calls: const { data, isLoading, error, fetchNextPage } = use{Feature}()
- Keep useState ONLY for UI state (filters, modals, form inputs)
- Follow ARCHITECTURE_STANDARD.md §15 exactly

STEP 4 — Verify:
- cd web && npm run build (no errors)

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT change the API client
- Do NOT change routing or auth
- Pages must look and behave exactly the same
- Filters and pagination must still work
```

---

## Web Batch 2 — Teacher & Admin Features

```md
I'm refactoring the "École Platform" React web frontend to use React Query.

BEFORE YOU WRITE ANY CODE, read ARCHITECTURE_STANDARD.md sections 11-17.

Read ALL page files in these feature folders:
- web/src/features/admin/ (10 pages: Dashboard, Users, Invitations, etc.)
- web/src/features/teacher/ (9 pages: Classes, Assignments, Submissions, Attendance, etc.)

TASK: For each page in admin/ and teacher/:

1. Create {feature}.service.ts (can have admin.service.ts with all admin API calls, teacher.service.ts with all teacher calls)
2. Create useAdmin.ts / useTeacher.ts (or split: useAdminUsers.ts, useAdminDashboard.ts if too large)
3. Update each page to use hooks instead of direct API calls

Special considerations:
- Admin dashboard uses multiple data sources — create separate query keys per widget
- Teacher classes page has nested data (class → students → grades) — use dependent queries
- Forms (create user, create assignment) — use useMutation with onSuccess to invalidate lists

Verify: cd web && npm run build
```

---

## Web Batch 3 — Student, Messages, Progress & Remaining Features

```md
I'm refactoring the "École Platform" React web frontend to use React Query.

BEFORE YOU WRITE ANY CODE, read ARCHITECTURE_STANDARD.md sections 11-17.

Read ALL page files in:
- web/src/features/student/
- web/src/features/messages/
- web/src/features/progress/
- web/src/features/content/
- web/src/features/results/
- web/src/features/invoices/
- web/src/features/documents/
- web/src/features/submissions/
- web/src/features/reports/
- web/src/features/analytics/
- web/src/features/profile/
- web/src/features/family/
- web/src/features/timetable/
- web/src/features/cms/

TASK: For EVERY remaining page that has direct api.* calls:

1. Create the service file (or add to existing domain service)
2. Create the hook file
3. Update the page

FINAL VERIFICATION — After this batch:
- Search ALL files in web/src/features/ for "api.get(" or "api.list(" or "api.post(" or "api.patch(" or "api.delete("
  - These should ONLY appear inside *.service.ts files, never in *Page.tsx files
- Search for "useState" in page files — should only be UI state (filters, modals), never server data
- Run: cd web && npm run build

Fix any violations found.
```

---

# PART C — Infrastructure Security Hardening

---

## Infra Security: Single Prompt

```md
I'm hardening the "École Platform" infrastructure for production security.

BEFORE YOU WRITE ANY CODE, read ARCHITECTURE_STANDARD.md section 18 (PART C - Infrastructure Security).

ALSO read these files:
1. Read .env — current environment variables
2. Read .env.example — template
3. Read .gitignore — check if .env is excluded
4. Read infra/docker-compose.dev.yml
5. Read infra/docker-compose.prod.yml
6. Read infra/redis/redis.conf
7. Read infra/postgres/init.sql
8. Read infra/docker-compose.monitoring.yml
9. Read infra/alertmanager/alertmanager.yml

TASK: Fix all security issues.

STEP 1 — Remove .env from git:
- Add .env to .gitignore if not already there
- Create .env.example with placeholder values (NEVER real secrets):
  - JWT_SECRET_KEY=change-me-generate-with-openssl-rand-hex-32
  - DATABASE_PASSWORD=change-me
  - REDIS_PASSWORD=change-me
  - SMTP_PASSWORD=change-me
- NOTE: Do NOT run git filter-branch to remove .env from history — just tell me to do it manually, as it rewrites history and is destructive

STEP 2 — Fix Redis security:
- Update infra/redis/redis.conf:
  - Add: requirepass ${REDIS_PASSWORD} (or a placeholder that gets replaced)
  - Change: protected-mode yes
  - Change: bind 127.0.0.1
- Update all docker-compose files that use Redis to pass REDIS_PASSWORD
- Update backend config to include Redis password in connection URL

STEP 3 — Fix PostgreSQL security:
- Update infra/postgres/init.sql:
  - Replace hardcoded password 'ecole' with environment variable reference
  - Or use Docker entrypoint env vars for role creation
- Ensure dev, staging, and prod use DIFFERENT database passwords

STEP 4 — Fix monitoring security:
- In infra/docker-compose.monitoring.yml:
  - Replace hardcoded Grafana password 'ecole-grafana' with environment variable
  - Add comment: "CHANGE THIS ON FIRST DEPLOYMENT"

STEP 5 — Fix alertmanager:
- In infra/alertmanager/alertmanager.yml:
  - Uncomment the webhook/Slack receiver section
  - Add placeholder URL with comment: "Replace with your actual Slack webhook"

STEP 6 — Verify .env.example:
- Ensure .env.example has every variable that .env has, but with safe placeholder values
- Ensure .env.example has comments explaining each variable

STEP 7 — Create infra/secrets/README.md update:
- Document the full secret generation process:
  - JWT: openssl rand -hex 32
  - DB password: openssl rand -base64 24
  - Redis password: openssl rand -base64 24
- Document which secrets go where per environment

RULES:
- Do NOT run any git command (no git add, commit, push, stash, checkout). I handle git myself.
- Do NOT delete the .env file — just ensure it's gitignored
- Do NOT modify any application code (backend, web, mobile)
- Do NOT change any API behavior
- Do NOT modify Docker image builds
- Be careful with redis.conf — keep existing performance settings, only add security
```

---

# PART D — Final Validation (All Layers)

---

## Full-Stack Validation Prompt

```md
I've just finished refactoring "École Platform" across all layers.

Read ARCHITECTURE_STANDARD.md to understand all patterns.

TASK: Full validation across backend, web, and infra.

BACKEND CHECKS:
1. Search backend/app/api/v1/ for "from sqlalchemy import" or "select(" — should be ZERO
2. Search backend/app/services/ for "select(" — should be ZERO
3. All repositories extend BaseRepository
4. All services create repositories in __init__
5. No router defines local _get_client_ip or _request_locale

WEB CHECKS:
6. Search web/src/features/ for "api.get(" in *Page.tsx files — should be ZERO
7. Every feature with API calls has a .service.ts file
8. Every feature with a service has a use*.ts hook file
9. React Query is configured in main.tsx
10. Run: cd web && npm run build

INFRA CHECKS:
11. .env is in .gitignore
12. .env.example has no real secrets
13. Redis has requirepass in config
14. PostgreSQL init.sql has no hardcoded passwords
15. Grafana password is not 'ecole-grafana' in docker-compose

Fix any violations. Report results.
```

---

## Notes

### Running Order (Full Refactoring)

**Phase 1 — Backend 3-Tier (8 batches):**
1. Pre-Requisite (shared utilities + BaseRepository) — MUST run first
2. Batch 1 (Auth & Audit) — most critical, largest service
3. Batch 2 (Billing & Payments)
4. Batch 3 (ERP: Classes, Attendance, Timetable)
5. Batch 4 (LMS: Content, Assignments, Quizzes) — largest batch
6. Batch 5 (Communication, Progress & Analytics)
7. Batch 6 (Admin, Profiles, GDPR & remaining)
8. Backend Validation

**Phase 2 — Fix Missing Features (3 batches):**
9. Phase 14 gaps (PDF templates, Arabic RTL, weekly analytics)
10. Phase 15 gaps (Holiday CRUD, event colors)
11. Phase 16 gaps (ResourcesPage, expiry notifications, bulk ops)

**Phase 3 — Web React Query (4 batches):**
12. Web Pre-Requisite (React Query setup)
13. Web Batch 1 (Notifications, Feed, Calendar)
14. Web Batch 2 (Teacher & Admin)
15. Web Batch 3 (All remaining features)

**Phase 4 — Infra Security (1 batch):**
16. Infra Security hardening

**Phase 5 — Validation:**
17. Full-Stack Validation (use META_PROMPT_3_VERIFY.md)

### Tool Compatibility
These prompts work identically in:
- **Claude Code**: Open `ecole-platform-dev/` folder, paste prompt
- **Codex (ChatGPT)**: Open `ecole-platform-dev/` folder, paste prompt
- **Cursor/Windsurf**: Same approach

The key is ARCHITECTURE_STANDARD.md — it ensures every tool produces the same output because the pattern is fully specified with examples.

### Time Estimate
- Backend 3-Tier (8 prompts): ~5 hours
- Fix Missing Features (3 prompts): ~2 hours
- Web React Query (4 prompts): ~3 hours
- Infra Security (1 prompt): ~30 min
- Validation (1 prompt): ~30 min
- **Total: ~11 hours**

### After Refactoring
Once complete, ALL future phases (17, 18, and beyond) will automatically follow the standard because:
1. ARCHITECTURE_STANDARD.md is the reference for all layers
2. Every existing service/hook/repository shows the pattern
3. Any AI tool will see the structure and follow the convention
4. Backend has repositories/, web has *.service.ts + use*.ts, infra has secure configs
