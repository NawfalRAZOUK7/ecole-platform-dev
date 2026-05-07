# Step 2 — Database Analysis

## 2.1 Database Overview

The platform uses **PostgreSQL 16** accessed via **SQLAlchemy 2.0 async** (asyncpg driver). The schema consists of **131 tables** organized into 9+ migration groups, managed by **65+ Alembic migrations**. The models contain a total of **~850 constraint and index declarations** across 24 model files.

Connection configuration (from `core/database.py`):
- Async engine with `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`
- `expire_on_commit=False` for session efficiency
- `statement_cache_size=0` to avoid asyncpg/pgbouncer conflicts
- Optional read replica via `DATABASE_REPLICA_URL`

---

## 2.2 Base Model Design

All domain models inherit from a common architecture defined in `core/database.py`:

### 2.2.1 TimestampMixin

Every entity inherits `TimestampMixin` providing:
- `id: UUID` — primary key, auto-generated via `uuid.uuid4()` (no sequential IDs)
- `created_at: datetime` — UTC timezone-aware, set on creation
- `updated_at: datetime | None` — auto-updated via `onupdate=_utc_now`

**Design decision**: UUID primary keys were chosen over auto-increment integers for three reasons: (1) no information leakage about entity count, (2) safe for distributed generation without coordination, (3) merge-safe across multi-tenant school databases if future sharding is needed.

### 2.2.2 SchoolScopedMixin

Most models inherit `SchoolScopedMixin` which adds:
- `school_id: UUID` — NOT NULL foreign key to `schools.id` with `ondelete="CASCADE"` and automatic `index=True`

This is the **structural foundation of multi-tenancy**. Every school-scoped table has a mandatory `school_id`, ensuring data cannot exist without belonging to a school. The index on `school_id` ensures all school-filtered queries perform efficiently.

### 2.2.3 NullableSchoolScopedMixin

For platform-wide content (e.g., content items that can be shared across schools):
- `school_id: UUID | None` — nullable FK, still indexed

### 2.2.4 SoftDeleteMixin

Selected models use `SoftDeleteMixin`:
- `deleted_at: datetime | None` — null means active
- `is_deleted` property, `soft_delete()` and `restore()` methods

Used for entities where hard delete would break referential integrity or audit trails (e.g., conversations, messages).

---

## 2.3 Entity Groups and Relationships

### 2.3.1 Migration Group G1 — IAM (Identity & Access Management)

**Tables**: `users`, `memberships`, `sessions`, `login_history`, `invitation_codes`, `account_recovery_requests`, `parent_child_links`, `student_profiles`, `parent_profiles`, `teacher_profiles`, `admin_profiles`, `content_manager_profiles`

**Key entities and relationships:**

**User** — Central entity. Email uniqueness is scoped per school via `UniqueConstraint("email", "school_id")`, allowing the same person to exist in multiple schools. Key fields include `totp_secret` and `totp_enabled` for 2FA, `email_verified_at` for email verification, `backup_codes` (stored as text).

**Membership** — Many-to-many between User and School with role. Partial unique index ensures only one active membership per `(user_id, school_id, role_code)` using `postgresql_where="status = 'active'"`. This allows historical tracking of past memberships.

**Session** — Tracks JWT refresh sessions. `revoke_at IS NULL` means active. Includes `user_agent`, `ip_address`, `device_name` for device identification, and `impersonator_id` FK for admin impersonation support.

**ParentChildLink** — Explicit parent-child relationship for ABAC ownership. Links `parent_user_id → child_user_id` within a school, with `status` (active/revoked) and `linked_by` audit field.

**Profile tables** — One-to-one extensions (Student: student_number, DOB, gender; Parent: CIN number, relationship_type; Teacher: employee_id, subject_specialty, hire_date, reward_points; Admin: department, can_approve_budgets; ContentManager: specialization, languages).

**Indexes strategy**: Compound indexes on `(school_id, ...)` for tenant-scoped queries, separate indexes on foreign keys for join performance.

### 2.3.2 Migration Group G2 — ERP (Enterprise Resource Planning)

**Tables**: `schools`, `academic_years`, `periods`, `classes`, `enrollments`, `teacher_assignments`, `attendance_sessions`, `attendance_records`, `absence_justifications`, `justification_reviews`, `attendance_alerts`, `timetable_slots`, `timetable_exceptions`, `timetable_constraints`, `timetable_generation_jobs`, `moroccan_holidays`

**Entity hierarchy:**
```
School (root)
  └── AcademicYear (date_start, date_end)
       ├── Period (trimester/semester, status: active/closed)
       │    ├── Enrollment (student → class, status: active/transferred/dropped)
       │    └── TeacherAssignment (teacher → class)
       └── Class (code, name)
            ├── TimetableSlot (recurring weekly, day_of_week, start_time, end_time)
            │    └── TimetableException (cancellation, substitution, room change)
            ├── AttendanceSession (date + slot)
            │    └── AttendanceRecord (student status: present/absent/excused/late)
            │         └── AbsenceJustification → JustificationReview
            └── AttendanceAlert (threshold-based warnings per student per period)
```

**Key constraints observed in code:**
- `CheckConstraint("date_end > date_start")` on AcademicYear and Period
- `UniqueConstraint("code", "school_id", "academic_year_id")` on Class — class codes unique per school/year
- Partial unique index on Enrollment: one active enrollment per student per period (`postgresql_where="status = 'active'"`)
- `UniqueConstraint("class_id", "session_date", "slot")` on AttendanceSession — no duplicate attendance marking
- `UniqueConstraint("attendance_session_id", "student_id")` on AttendanceRecord — one record per student per session
- `CheckConstraint("absence_rate >= 0 AND absence_rate <= 1")` on AttendanceAlert
- `CheckConstraint("end_time > start_time")` and `CheckConstraint("day_of_week >= 0 AND day_of_week <= 6")` on TimetableSlot
- TimetableConstraint type validation via `CheckConstraint IN (...)` for 6 constraint types

**Timetable generation**: `TimetableGenerationJob` stores `constraints_snapshot` (JSONB) and `result_payload` (JSONB), enabling reproducible generation runs with status tracking (pending → running → completed/failed → applied).

### 2.3.3 Migration Group G3 — LMS (Learning Management System)

**Tables**: `courses`, `assignments`, `submissions`, `submission_files`, `grades`, `grade_categories`, `student_period_averages`, `content_items`, `content_item_assets`, `content_progress`, `class_content_assignments`, `content_submissions`, `activities`, `activity_sessions`, `assessments`, `assessment_results`, `quizzes`, `quiz_questions`, `quiz_attempts`, `quiz_responses`, `question_bank_items`, `rubrics`, `rubric_criteria`, `rubric_levels`, `rubric_scores`, `writing_attempts`, `resources`, `resource_ratings`

**Course → Assignment → Submission chain:**
- Course belongs to teacher + class, has status (draft/published/archived)
- Assignment references course, has type (STANDARD, PRINTABLE_PDF, QUIZ), due_date
- Submission links student to assignment, tracks status (draft → submitted → graded → returned)
- SubmissionFile stores file attachments with MIME type and size

**Content system:**
- ContentItem: learning materials with type (video, document, interactive, story, coloring, writing_prompt), difficulty level, language
- ContentProgress: per-student tracking (not_started → in_progress → completed) with `percent_complete`, `time_spent_seconds`
- ClassContentAssignment: maps content to classes
- NullableSchoolScopedMixin on ContentItem — content can be platform-wide or school-specific

**Assessment engine:**
- Assessments (exams) with publishing workflow
- AssessmentResults with score tracking
- Quizzes with nested QuizQuestions (JSONB for flexible question types)
- QuizAttempts tracking student attempts with time limits
- QuestionBankItems for reusable question pools

**Rubric engine:**
- Rubric → RubricCriteria → RubricLevels (hierarchical scoring definitions)
- RubricScores link rubric criteria to submissions for granular grading

**Gradebook:**
- Grades with category weighting (GradeCategory per course)
- StudentPeriodAverages for computed period-level averages

### 2.3.4 Migration Group G4 — Communication

**Tables**: `consent_preferences`, `notifications`, `notification_deliveries`, `notification_preferences`, `device_tokens`, `parent_feed_items`, `conversations`, `conversation_participants`, `messages`, `message_read_receipts`, `announcements`

**Notification architecture:**
- `notifications` stores the event record with JSONB `payload`, category (academic/billing/attendance/system/announcement), priority (low/normal/high)
- `notification_deliveries` tracks per-channel delivery (in_app/email/sms/push) with status chain: queued → sent → delivered → failed/bounced/clicked/opened
- `device_tokens` for push notification targeting (FCM tokens)
- `notification_preferences` for per-user opt-in/opt-out per category per channel

**Messaging:**
- Conversations with participants (many-to-many via ConversationParticipant)
- Messages within conversations with read receipts
- SoftDeleteMixin on Conversation and Message for data retention

**Consent:**
- Per-user consent preferences with scope (school/student level)
- Status: opted_in/opted_out

### 2.3.5 Migration Group G5 — Billing & Finance

**Tables**: `invoices`, `invoice_items`, `payment_attempts`, `payment_proofs`, `provider_webhook_events`, `fee_structures`, `fee_assignments`, `late_fee_policies`, `sibling_discount_policies`, `payment_plans`, `installments`, `micro_budgets`, `budget_allocations`, `budget_requests`, `budget_transactions`, `financial_snapshots`, `retention_metrics`, `cashflow_forecasts`, `cost_per_student`, `data_exports`

**Invoice chain:**
- FeeStructure defines fee types with frequency (monthly/trimestrial/annual/one_time)
- FeeAssignment links fee structures to students/classes
- Invoice generated from fee assignments with line items (InvoiceItem)
- PaymentAttempt tracks payment attempts per invoice (method: cash/bank_transfer/card/check)
- PaymentProof stores proof-of-payment documents
- PaymentPlan allows installment splitting
- ProviderWebhookEvent logs external payment provider callbacks

**Currency**: `ALLOWED_CURRENCIES = {"MAD", "EUR", "USD"}` — Moroccan Dirham is the primary currency, with Euro and USD for international schools.

**Financial health analytics:**
- FinancialSnapshot: periodic aggregate metrics
- RetentionMetrics: student retention tracking
- CashflowForecast: predicted revenue
- CostPerStudent: unit economics

**Micro-budgets:**
- MicroBudget per class, with BudgetAllocations, BudgetRequests (approval workflow), and BudgetTransactions

### 2.3.6 Migration Group G6 — Audit, Gamification & Specialized

**Tables**: `audit_logs`, `student_rewards`, `reward_events`, `reward_badges`, `game_configs`, `difficulty_adaptations`, `skill_dimensions`, `skill_milestones`, `skill_passports`, `skill_progress`, `level_age_mappings`, `events` (calendar), `event_rsvps`, `event_reminders`, `event_reminder_preferences`, `documents`, `document_versions`, `student_document_requirements`, `compliance_reports`, `curriculum_mappings`, `men_curricula`, `men_objectives`, `sync_devices`, `sync_queue`, `sync_conflicts`, `sync_checkpoints`, `micro_schools`, `micro_groups`, `micro_enrollments`, `micro_payments`, `micro_progress_logs`, `micro_resources`, `feature_toggles`, `report_jobs`, `report_schedules`, `shared_review_comments`

**Audit log** (append-only):
- `actor_id`, `action_type`, `target_type`, `target_id`
- `entity_before` / `entity_after` as JSONB — captures state changes
- `outcome` (success/failure), `error_code`, `correlation_id`, `ip_address`
- Indexed on `(school_id, created_at)` for time-range queries and `(actor_id, action_type)` for user activity

**Rewards system:**
- StudentRewards: per-student aggregate (stars, xp, level, streak_days, longest_streak, badges as JSONB array)
- RewardEvents: granular event log (source: content/quiz/game/coloring/login, stars_earned, xp_earned)
- RewardBadge: badge definitions with trilingual titles (en/fr/ar), criteria (type + threshold value)

**Skill Passport:**
- SkillDimension → SkillMilestone (hierarchical life-skills framework)
- SkillPassport per student, SkillProgress per milestone per student

**Sync system (offline-first mobile):**
- SyncDevice: registered devices per user
- SyncQueue: pending mutations with JSONB payload
- SyncConflict: detected conflicts during sync
- SyncCheckpoint: last sync timestamp per device

---

## 2.4 Indexing Strategy

The codebase implements a deliberate indexing strategy with **736 total constraint/index declarations**:

1. **School-scoped composite indexes**: Nearly every table has `Index("idx_*_school_*", "school_id", ...)` because all queries are school-filtered. This is the most critical index pattern.

2. **Foreign key indexes**: All foreign keys have explicit indexes (SQLAlchemy doesn't create these automatically in PostgreSQL). A dedicated migration `g37a_add_missing_fk_indexes` and `g37b_legacy_fk_indexes` ensure coverage.

3. **Partial unique indexes**: Used extensively for business rules that apply only to active records:
   - `uq_memberships_user_school_role_active` (where status='active')
   - `uq_enrollments_school_student_period_active` (where status='active')
   - `idx_sessions_school_user_active` (where revoke_at IS NULL)

4. **Compound indexes for common query patterns**:
   - `idx_audit_logs_school_created` — time-range audit queries
   - `idx_attendance_records_school_student` — student attendance lookups
   - `idx_login_history_user_created` — login history by user + time

5. **Check constraints for data integrity**:
   - Date ordering (`date_end > date_start`)
   - Numeric bounds (`absence_rate >= 0 AND absence_rate <= 1`)
   - Enum validation via `CheckConstraint IN (...)`
   - Non-negative values on counters

---

## 2.5 Migration Strategy

### 2.5.1 Alembic Configuration

65+ migrations organized by groups (G1–G54+), each prefixed with a short hash and group identifier:
- Naming convention: `{hash}_g{group_number}_{description}.py`
- Examples: `g12_role_specific_profiles`, `g20_add_quiz_engine`, `g42_student_rewards`

### 2.5.2 Migration Groups and Dependencies

```
G1-IAM  (no deps)           → users, memberships, sessions, invitations
G2-ERP  (depends on G1)     → schools, years, classes, enrollments, attendance
G3-LMS  (depends on G1, G2) → courses, assignments, submissions, grades
G4-COM  (depends on G1)     → notifications, messaging, consent
G5-Billing (depends on G1, G2) → invoices, payments, fees
G6-Audit (depends on G1)    → audit_logs
```

Later groups add features incrementally: G12 (profiles), G19 (teacher rewards), G20 (quiz engine), G21 (content library), G22 (notifications center), G23 (reports), G24 (calendar), G25 (documents), G26 (content manager profiles), G27 (impersonation), G28 (rubrics), G30 (report schedules), G31 (school mixins/enums), G32 (micro-schools, budgets), G33 (skills passport), G34 (MEN compliance), G35 (offline sync), G36 (financial health), G37 (FK indexes), G42 (rewards), G46 (level-age), G48 (merge heads), G49 (academic programs), G50 (eligibility/enrollments), G51 (invoice TVA + school branding), G52 (storage objects + upload sessions), G53 (longest streak), G54 (timetable constraints).

### 2.5.3 Merge migrations

`g48_merge_heads` indicates that parallel development branches were merged, a common pattern in rapid feature development.

---

## 2.6 Normalization and Design Decisions

### 2.6.1 Normalization Level

The schema is primarily in **3NF (Third Normal Form)**:
- No repeating groups (1NF)
- No partial dependencies on composite keys (2NF) — UUID PKs avoid composite keys
- No transitive dependencies (3NF) — profile data is separated into role-specific tables

**Intentional denormalization** exists in strategic places:
- `student_period_averages` — pre-computed aggregates to avoid expensive JOIN + AVG queries on every gradebook load
- `student_rewards` — aggregate table (total stars, xp, level, streak) rather than computing from `reward_events` on every request
- `financial_snapshots` — periodic aggregate snapshots of financial metrics
- `entity_before` / `entity_after` JSONB on `audit_logs` — captures full state without needing JOINs to reconstruct history

### 2.6.2 JSONB Usage

PostgreSQL's JSONB type is used strategically for flexibility:
- `quiz_questions.options` — question answer choices vary by type
- `game_configs.config` — game parameters vary by game type
- `sync_queue.payload` — arbitrary mutation payloads
- `timetable_constraints.params` — constraint parameters vary by type
- `audit_logs.entity_before/entity_after` — schema-agnostic state capture
- `notification.payload` — notification data varies by event type

**Design rationale**: These are all semi-structured data where a rigid relational schema would require excessive tables or polymorphic patterns. JSONB preserves queryability (GIN indexes) while allowing per-record schema variation.

### 2.6.3 Enum Strategy

Enums are defined as Python `str, enum.Enum` classes and mapped to PostgreSQL ENUM types via `PgEnum(... create_type=False)`. The `create_type=False` pattern means enums are created in migrations, not at table creation time — allowing controlled type evolution.

### 2.6.4 Multi-Tenancy Isolation

The school-scoped design ensures complete data isolation between schools without the complexity of separate databases or schemas:
- Every query goes through `BaseRepository._scoped_query()` which adds `WHERE school_id = ?`
- ABAC guards (`verify_school_boundary()`) validate school_id matches the authenticated user's school
- Even cross-tenant JOIN attacks are prevented because school_id is required (NOT NULL) on virtually all tables

### 2.6.5 Soft Delete Strategy

Selective application: only entities where deletion history matters use `SoftDeleteMixin` (conversations, messages). Other entities use hard delete with `ondelete="CASCADE"` on foreign keys, keeping the schema clean. The audit log captures deletion events for entities that are hard-deleted.

---

## 2.7 Data Flow Patterns

### 2.7.1 Write Path
```
API Handler → Service.create() → UnitOfWork → Repository.create() → SQLAlchemy → PostgreSQL
                                                                    → EventDispatcher.dispatch()
```

The `UnitOfWork` pattern ensures write operations are atomic. Nestable depth tracking allows services to compose without double-commit.

### 2.7.2 Read Path
```
API Handler → Service.get/list() → Repository.query() → school-scoped SELECT → AsyncSession → Result
```

Read queries use `expire_on_commit=False` to avoid unnecessary lazy loads after commit.

### 2.7.3 Pagination
Cursor-based pagination (not offset-based) is used throughout, avoiding the performance degradation of `OFFSET` on large tables. Cursors are based on `created_at` + `id` for stable ordering.

---

## 2.8 Seed & Demo Data Architecture

### 2.8.1 Coverage

The seed system achieves **~93% table coverage** (122 of 131 tables populated) across **two demo schools**:
- **Ecole Benani** (premium) — full dataset with 31 users, 8 classes, 9 class levels
- **Ecole Atlas** (trial) — minimal multi-tenant demo with 4 users, 1 class, 1 invoice

### 2.8.2 Seed Architecture

Three coordinated modules:
- **`seed.py`** — Core seed orchestrator (~3,700 LOC). Clears data via `TRUNCATE CASCADE`, seeds in dependency order, generates `seed-report.md`
- **`seed_extensions.py`** — Extended seeders for newer features (documents, reporting, program management, device tokens)
- **`seed_enhanced.py`** — High-volume demo seeders (22 functions) covering rubrics, question bank, quiz responses, micro-schools, sync queue, attendance alerts, absence justifications, budget, financial health, payment plans, billing policies, shared reviews, program assignment events

### 2.8.3 Fixture System

7 binary stub files in `backend/app/templates/fixtures/` provide realistic document references:
- PDF stubs (bulletins, worksheets, submissions, coloring pages)
- JPEG stub (national ID scan)
- XLSX stubs (invoice template, attendance export)

### 2.8.4 Idempotency

The seed is fully idempotent: `clear_all()` truncates all tables in reverse dependency order with `CASCADE`, then re-seeds from scratch. This enables rapid environment reset for CI, demos, and development.
