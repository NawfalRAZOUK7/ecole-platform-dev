# Step 4 — Core Business Modules Analysis

> **Source**: Direct code analysis of 80 service files (~32,577 LOC), 64 API route files, and supporting domain/repository/model layers.
> **Extraction date**: 2026-05-07

---

## 1. Module Index

The backend organizes business logic into **12 distinct functional modules**, each following the Router → Service → Repository layering established in the architecture. Every service method participates in the transactional UnitOfWork pattern and emits structured audit events.

| # | Module | Primary Service Files | LOC | API Routes |
|---|--------|----------------------|-----|------------|
| 1 | IAM (Identity & Access) | `auth.py` | 2,172 | `auth.py`, `invitations.py`, `recovery.py`, `profiles.py` |
| 2 | ERP (School Operations) | `erp.py`, `timetable_generator.py`, `attendance_analytics.py` | 2,728 | `classes.py`, `enrollments.py`, `attendance.py`, `timetable.py` |
| 3 | LMS (Learning) | `lms/` (6 sub-services), `gradebook.py` | 3,112 | `courses.py`, `assignments.py`, `submissions.py`, `content.py`, `quizzes.py`, `assessments.py` |
| 4 | Communication | `communication.py`, `notification_hub.py`, `event_dispatcher.py`, `delivery/` | 2,450 | `messaging.py`, `notifications.py`, `feed.py`, `consents.py` |
| 5 | Finance | `billing.py`, `budget_service.py`, `financial_health_service.py`, `payment_plan.py`, `payment_retry.py` | 3,848 | `billing.py`, `invoices.py`, `payments.py`, `budgets.py`, `financial_health.py` |
| 6 | Gamification | `rewards_service.py`, `game_service.py`, `difficulty_adapter.py` | 706 | `rewards.py`, `games.py`, `levels.py` |
| 7 | Analytics & Reporting | `analytics.py`, `kpi.py`, `dashboard_analytics.py` | 1,268 | `analytics.py`, `reports.py` |
| 8 | Admin | `admin.py`, `school.py`, `gdpr.py`, `compliance_service.py` | 1,217+ | `admin.py`, `schools.py`, `gdpr.py`, `compliance.py` |
| 9 | Program Management | `eligibility_engine.py`, `program_service.py` | 800+ | `programs.py`, `eligibility.py`, `enrollments.py` |
| 10 | Document Management | `document_service.py`, `resource_service.py`, `upload_service.py` | 1,200+ | `documents.py`, `resources.py`, `uploads.py` |
| 11 | MEN Compliance | `compliance_service.py`, `curriculum_service.py` | 600+ | `compliance.py`, `curriculum.py` |
| 12 | Micro-Schools | `micro_school_service.py` | 400+ | `micro_schools.py` |

---

## 2. IAM Module — Identity & Access Management

### 2.1 Purpose

Governs the complete user identity lifecycle: authentication, session management, invitation-based onboarding, account recovery, two-factor authentication, email verification, and admin impersonation. This module is the security boundary through which every other module operates.

### 2.2 Service Decomposition

The `auth.py` file (2,172 lines) contains **5 distinct service classes**, each handling a specific IAM sub-domain:

**AuthService** — Core authentication engine. Implements:
- **Login flow** with a 10-step pipeline: rate-limit check → credential verification → user status validation → membership verification → 2FA gate → session limit enforcement (max 5 concurrent, FIFO eviction) → device fingerprint computation (SHA-256 of user-agent + network prefix) → login history recording → token bundle issuance → new-device event dispatch.
- **Register flow** via invitation code: invitation hash validation (SHA-256) → expiry/consumption check → email uniqueness per school → password policy enforcement (8 rules, 12-char minimum) → atomic UnitOfWork creating user + membership + role-specific profile + optional parent-child link → invitation consumption → auto-login with token issuance.
- **Token refresh** with rotation: decode refresh JWT → CSRF double-submit validation → session DB verification → JTI rotation check (replay detection revokes session) → sliding-window expiry recalculation (extends when >75% consumed) → new token bundle.
- **Password change**: verify current password → enforce policy → hash with bcrypt (12 rounds) → revoke all other sessions (keep current).
- **Session management**: list active sessions with device metadata, revoke individual sessions (owner or admin), impersonation start/stop with shadow sessions.

**InvitationService** — Invitation code lifecycle:
- Code generation: `secrets.token_hex(4)` → 8 hex chars, stored as SHA-256 hash (plaintext returned once, never stored).
- Consumption: hash match → school scope check → expiry check → idempotent for same user → creates membership → triggers email verification if needed.
- Revocation: soft-revoke by setting `expires_at` to now.

**RecoveryService** — Account recovery with OTP:
- Anti-enumeration: always returns success regardless of user existence.
- OTP generation: 6-digit random code, stored as SHA-256 hash in Redis with 15-minute TTL.
- State machine: `pending` → `verified` → `reset`. Max 5 attempts with 30-minute lockout on exhaustion.
- Password reset revokes all active sessions, forcing re-authentication.

**TwoFactorService** — TOTP 2FA lifecycle:
- Setup: generates 32-byte base32 TOTP secret → provisioning URI for QR scanning.
- Verify setup: validates TOTP code (valid_window=1, ±30s drift) → generates 10 backup codes (8 chars each, bcrypt-hashed with rounds=10) → activates 2FA.
- Disable: requires valid TOTP or backup code. Backup codes are consumed on use (index removal from JSON array).
- Login verification: retrieves pending context from Redis (5-minute TTL), verifies TOTP/backup, creates session with full login pipeline.

**EmailVerificationService** — Email OTP verification triggered during invitation consumption.

### 2.3 Key Technical Choices

- **Redis for ephemeral state**: rate-limit counters, refresh JTI rotation, CSRF tokens, 2FA temp tokens, recovery OTPs, email verification OTPs — all stored in Redis with explicit TTLs rather than in the database.
- **Device fingerprinting**: SHA-256 hash of `user_agent|network_prefix` where network_prefix is first 3 octets (IPv4) or first 4 groups (IPv6), providing rough device identification without storing raw identifiers.
- **UnitOfWork transactional boundaries**: session creation, login history recording, and audit logging all happen within a single UoW transaction, ensuring atomicity.
- **Domain event dispatch**: `NewDeviceLogin` and `UserRegistered` events are dispatched *after* the UoW commit, following the outbox pattern where the event fires only after the state is persisted.

### 2.4 Internal Interactions

- **Inbound**: Every protected route depends on `get_current_user` (dependencies.py) which calls `AuthRepository.get_session_by_id` to verify the session is still active.
- **Outbound**: `EventDispatcher` for `NewDeviceLogin`, `UserRegistered`, `PasswordChanged`, `TwoFactorEnabled` events → routed to email/in-app delivery strategies. `AuditService` for every state transition (20+ action types: `AUTH_LOGIN_FAILED`, `AUTH_SESSION_OPENED`, `2FA_ENABLED`, etc.).

---

## 3. ERP Module — School Operations

### 3.1 Purpose

Manages the academic operational backbone: class organization, student enrollments, teacher assignments, attendance tracking with absence justification workflows, and timetable management including automated generation.

### 3.2 Workflow Analysis

**ERPService** (1,106 lines) handles:

**Enrollment workflow**: validates student exists → school boundary check → class exists → period is active → checks for existing active enrollment (idempotent) → checks for conflicting enrollment in same period (prevents dual enrollment) → creates enrollment within UoW + audit.

**Attendance pipeline**: validates class → teacher assignment verification (`verify_teacher_assignment`) → period active check → uniqueness check (class/date/slot) → creates `AttendanceSession` + bulk `AttendanceRecord` rows for all students → audit with record count.

**Absence justification state machine**: parent submits justification → `verify_parent_child_ownership` check → record must be "absent" or "late" → creates justification with status "pending". Teacher/admin reviews → decision: "justified" (→ record status becomes "excused") or "rejected" (requires rejection reason). Review creates a `JustificationReview` record.

**Timetable management**:
- Slot creation with conflict detection: checks both class-level and teacher-level overlaps using `find_overlapping_class_slot` and `find_overlapping_teacher_slot` queries.
- Weekly timetable aggregation: `_build_weekly_timetable` resolves slots for a week, joins exceptions (substitutions, room changes, cancellations), maps class names, and produces `WeeklyTimetableResponse` with exception overlays.
- Role-adaptive `get_my_weekly_timetable`: TCH → teacher slots, STD → class slots from active enrollment, PAR → first child's class slots.

**TimetableGenerator** (1,187 lines) — Constraint-based automated generation:
- Reads `TimetableConstraint` records (6 types: max_hours_per_day, min_break_between_slots, preferred_time_blocks, avoid_time_blocks, consecutive_subject_limit, room_capacity).
- Generates `TimetableGenerationJob` with JSONB snapshots for audit trail.
- Produces `TimetableSlot` entries respecting teacher availability, room capacity, and pedagogical constraints.

### 3.3 Key Technical Choices

- **School boundary enforcement**: Every query passes through `verify_school_boundary`, which returns 404 (not 403) for cross-school access — information masking prevents enumeration of resources in other schools.
- **Partial unique indexes**: enrollments use `WHERE status = 'active'` partial unique index, allowing multiple historical enrollment records while enforcing uniqueness for active ones.
- **ABAC integration**: teacher-class assignment check uses `verify_teacher_assignment(class_id, teacher_classes)` where `teacher_classes` is a set of class UUIDs resolved per request.

### 3.4 Internal Interactions

- **IAM → ERP**: User identity and role drive access control. Teacher-class assignments define ABAC scope.
- **ERP → COM**: `AttendanceThresholdExceeded` event dispatched when absence rates cross configurable thresholds → notifications to parents, students, admins.
- **ERP → LMS**: Enrollment data determines which students see which courses/assignments.
- **ERP → Finance**: Class enrollment links to fee assignments for invoice generation.

---

## 4. LMS Module — Learning Management

### 4.1 Purpose

Manages the complete learning lifecycle: course creation, homework assignments with file uploads, student submissions, rubric-based and direct grading with late-penalty calculation, content delivery with progress tracking, quizzes with automated scoring, and activity sessions with attempt tracking.

### 4.2 Service Decomposition

The LMS module is split into 6 specialized sub-services sharing a common `LMSServiceBase` (helpers + serializers):

**CourseService** (218 lines): Course CRUD with teacher-assignment verification. List supports cursor-based pagination with filtering (`FilterSpec`, `SortSpec`) and full-text search. TCH role scopes to assigned classes only.

**AssignmentService** (417 lines): Assignment creation with class/course/teacher verification. Links to optional rubric. `due_at` deadline tracking. Supports `allow_late_submissions` and `late_penalty_percent_per_day` for graduated penalties.

**GradingService** (194 lines): Dual grading modes:
- Direct grading: teacher assigns score → `calculate_late_penalty` computes adjusted score based on submission lateness (days × penalty percent per day). Validates score ≤ total_points.
- Rubric grading: referenced via `rubric_id` on assignment, handled by separate endpoint.
- Late penalty override: teacher can restore original score, flagging `penalty_overridden=True`.
- **Moroccan scale**: `_score_on_moroccan_scale` normalizes scores to 0-20 scale for Prometheus grade distribution metrics.
- Grade publishing dispatches `GradePublished` domain event → push/email/in-app to student and parents.

**ContentService** (733 lines): Learning material management:
- Content items with status progression (`draft` → `published` → `archived`).
- File uploads via `storage` abstraction (local/S3).
- `ContentProgress` tracking per student per content item, with status states: `not_started` → `in_progress` → `completed`.
- `ContentPublished` domain event on publish.

**QuizService** (537 lines): Quiz lifecycle:
- Quiz creation with questions (multiple-choice, true/false, short answer).
- Quiz attempts with time tracking and auto-grading.
- Score computation and `QuizCompleted` domain event dispatch.

**ProgressService** (295 lines): Aggregated progress tracking across content and activities.

### 4.3 Key Technical Choices

- **Late penalty as first-class concept**: `calculate_late_penalty()` is a pure function that computes `original_score`, `adjusted_score`, `late_penalty`, and `late_days` as metadata stored alongside the grade — preserving full audit trail and enabling teacher override.
- **File upload limit**: `MAX_FILES_PER_SUBMISSION = 5` enforced at the service layer.
- **Storage abstraction**: `from app.core.storage import storage` provides a swappable backend (local filesystem for dev, S3-compatible for production) without any LMS code changes.
- **Prometheus grade metrics**: Every grading operation records the Moroccan-scale score to `grade_distribution` histogram, labeled by school and subject.

### 4.4 Internal Interactions

- **LMS → COM**: `GradePublished`, `AssignmentCreated`, `SubmissionReceived`, `ContentPublished`, `QuizCompleted` events → multi-channel notifications.
- **LMS → Gamification**: Quiz completions and activity completions trigger `RewardsService.award()` for stars/XP allocation.
- **LMS → Analytics**: Audit events feed KPI computation (content progress rates, submission counts).

---

## 5. Communication Module

### 5.1 Purpose

Provides three communication channels: direct messaging between stakeholders (parent-teacher, student-teacher), a multi-channel notification system with preference management, and a parent activity feed aggregating events across their children's school life.

### 5.2 Sub-Module Analysis

**CommunicationService** (580 lines) — Messaging:

Conversation model supports DIRECT (1:1) and GROUP types. ABAC enforcement is comprehensive:
- **Parents** can only message teachers assigned to their children's classes, or admins/directors.
- **Teachers** can only message parents whose children are in their classes, or admins/directors/other teachers.
- **Students** can only message teachers of their classes (validated via `validate_student_teacher_access`).
- **Admins/Directors** have unrestricted messaging.

Message flow: participant verification → ABAC validation → attachment ownership check → message creation within UoW → real-time WebSocket push via `publish_message_created` to all non-muted participants.

Read receipts: batch marking via `mark_read` up to a specific message timestamp, using `list_unread_message_ids` for efficient batch creation.

**NotificationHubService** (714 lines) — Notification Engine:

Acts as the central notification routing engine with four delivery channels:
- **IN_APP**: Always delivered. Creates `Notification` record + WebSocket push via `publish_event`.
- **PUSH**: Firebase Cloud Messaging via `PushConfigService`. Sent for HIGH/CRITICAL priority when user preference allows.
- **EMAIL**: Via `EmailDigestService` (supports digest batching with daily/weekly frequency). Sent for CRITICAL priority or billing-category NORMAL.
- **SMS**: Via `sms_service` as ultimate fallback. Only sent for CRITICAL priority when user has phone number.

Priority-based routing logic:
```
NORMAL → IN_APP only (+ EMAIL for billing)
HIGH   → IN_APP + PUSH
CRITICAL → IN_APP + PUSH + EMAIL + SMS
```

User preferences: lazy-initialized defaults (20 combinations: 4 channels × 5 categories), stored in `notification_preferences` table. Users can disable specific channel/category pairs.

Recipient resolution: accepts `user_ids`, `role_codes`, and `class_ids` as targeting dimensions. Class targeting resolves to students + their parents + assigned teachers.

Unread count caching: Redis with 30-second TTL, invalidated on notification creation and read/delete operations.

**EventDispatcher** (591 lines) — Domain Event Router:

Maps 20+ domain event types to delivery strategy lists using the `EVENT_HANDLERS` registry:
- `GradePublished` → Push + Email + InApp (3 channels)
- `AssignmentCreated` → Push + InApp
- `InvoiceGenerated` → Push + Email
- `AttendanceThresholdExceeded` → Push + Email
- `NewDeviceLogin` → Email only
- `UserRegistered` → Email only

Each handler entry specifies a `strategy` class and `template_key`. The dispatcher resolves recipients (role-aware: student→parents, class→all stakeholders), builds context from the domain event dataclass, then delegates to each strategy's `deliver()` method.

**Delivery Strategies** (570 lines total):
- `DeliveryStrategyBase`: abstract base with `deliver()` → `prepare_notification()` → `execute_delivery()` chain.
- `InAppDeliveryStrategy`: Creates `Notification` record via `NotificationHubService`.
- `PushDeliveryStrategy`: Formats push payload, delegates to Firebase.
- `EmailDeliveryStrategy`: Renders template, queues via email service.
- `SMSDeliveryStrategy`: Truncates message, sends via SMS provider.

### 5.3 Key Technical Choices

- **Strategy pattern for delivery**: New channels (WhatsApp, Telegram) can be added by implementing `DeliveryStrategyBase` and registering in `EVENT_HANDLERS`.
- **Idempotency**: Notifications use `idempotency_key` to prevent duplicate delivery from retries.
- **Preference-aware routing**: The system respects user opt-outs before delivering to any channel.
- **Real-time via Redis Pub/Sub**: `publish_message_created` and `publish_event` use `ws_manager` which runs Redis Pub/Sub for WebSocket broadcasting to connected clients.

---

## 6. Finance Module

### 6.1 Purpose

Manages the complete school financial workflow: fee structure definition, student fee assignments (individual and bulk), invoice generation with discount policies, payment initiation and webhook processing, late fee computation, sibling discount automation, budget management, financial health scoring, and overdue reminders.

### 6.2 Workflow Analysis

**BillingService** (1,270 lines) — Core financial engine:

**Fee Structure → Invoice pipeline**:
1. Admin creates `FeeStructure` (name, amount, currency, frequency, due_day, applies_to_level).
2. Students are assigned to fee structures individually or via bulk assignment (by class or level).
3. `generate_invoices()` processes all active fee assignments for a structure:
   - Resolves parent-child links to determine invoice recipients (parent_id).
   - Applies **sibling discount policy**: orders siblings by birth date, applies graduated discounts (e.g., 10% second child, 20% third, 30% fourth+).
   - Applies manual per-assignment discounts.
   - Total discount capped at 100%.
   - Creates `Invoice` with `InvoiceItem` records, using the `Money` value object for arithmetic safety.
   - Dispatches `InvoiceGenerated` domain event per invoice.

**Payment lifecycle**:
- Parent initiates payment → creates `PaymentAttempt` with `idempotency_key` (prevents duplicate charges).
- Payment provider sends webhook → `handle_provider_webhook`:
  - Status "paid" → finalize payment → mark invoice "paid" → `PaymentReceived` event → Prometheus revenue counter.
  - Status "failed" → `PaymentFailed` event → schedules retry via `schedule_retry_for_failed_payment`.
  - Status "canceled" → finalize as canceled.
  - Real-time WebSocket push via `publish_payment_updated`.

**Late fee engine** (`apply_late_fees`):
- School configures `LateFeePolicy` (fee_type: fixed/percent, frequency: once/daily/weekly, grace_days, max_fee cap).
- Computes overdue days → calculates fee units → applies delta from existing late fee items.
- Uses `Money` value object for precision. Respects max_fee cap.

**BudgetService** (1,079 lines): School budget management with allocation tracking, expenditure approval workflows, and budget-vs-actual variance analysis.

**FinancialHealthService** (749 lines): Computes school financial health scores across multiple dimensions: collection rate, outstanding balance, payment velocity, budget adherence.

### 6.3 Key Technical Choices

- **Money value object** (`app.domain.value_objects.money.Money`): Wraps `Decimal` arithmetic to prevent floating-point precision issues in financial calculations. All fee, discount, and total computations use `Money.from_float()` and `Money` arithmetic operators.
- **Sibling discount ordering**: Deterministic ordering by birth date (with fallback to full_name alphabetical, then UUID) ensures consistent discount assignment across invoice regenerations.
- **Prometheus business metrics**: `billing_collection` counter (labeled by school/status) and `billing_revenue` counter (labeled by school/plan) provide real-time financial monitoring.
- **Webhook idempotency**: `provider_event_id` uniqueness prevents double-processing of payment provider callbacks.

### 6.4 Internal Interactions

- **Finance → COM**: `InvoiceGenerated` (push + email to parent), `PaymentReceived` (push + in-app), `PaymentFailed` (in-app + retry scheduling).
- **Finance → ERP**: Fee assignments use class/level enrollment data for bulk targeting.
- **Finance → Real-time**: Payment status changes broadcast via WebSocket to connected parent clients.
- **Finance → Overdue Reminders**: Scheduled task scans for overdue invoices and triggers notification batches.

---

## 7. Gamification Module

### 7.1 Purpose

Implements a kid-facing reward system with stars, XP, levels, streaks, badges, and class leaderboards. Integrated with the mobile game engine for completion-based reward flows.

### 7.2 Service Analysis

**RewardsService** (350 lines):

**XP → Level progression**: Uses a quadratic formula — `threshold(level) = 50 × (level−1) × level`. Level 2 requires 100 XP, level 3 requires 300 XP, level 10 requires 4,500 XP. `_level_from_xp()` iterates until threshold exceeds current XP. `_level_progress()` computes percentage within current level.

**Streak tracking**: `_update_streak()` checks `last_activity_at`:
- Same day → no change.
- Previous day → increment streak.
- Any other → reset to 1.
- `longest_streak` maintains all-time high.

**Award pipeline**: `award()` receives `event_type`, `stars`, `xp`, `source_type` (content/quiz/game/coloring/login), `source_id`. Creates `RewardEvent` audit record → updates cumulative `StudentReward` → recalculates level.

**Leaderboard**: `get_leaderboard()` queries by class, returns ranked students by stars with level display.

**Access control** is role-adaptive:
- STD: can view own rewards.
- TCH: can view/award rewards for students in assigned classes.
- PAR: can view rewards for linked children.
- ADM/DIR/SUP/SYS: full access.

**GameService** (242 lines):

Manages mobile game configurations with trilingual titles (en/fr/ar). Key features:
- `GameConfig` with `game_type` enum (coloring, puzzle, matching, sorting, tracing), `difficulty` enum (easy/medium/hard), target age range, subject, JSONB config payload.
- `complete_config()` is the reward bridge: on game completion, calls `RewardsService.award()` with the game's configured `reward_stars` and `reward_xp`.
- Platform-level vs. school-level configs: `school_id = None` for global configs (only PLATFORM_ROLES can manage).

**DifficultyAdapter** (114 lines): Adaptive difficulty engine that adjusts game parameters based on student performance history.

### 7.3 Key Technical Choices

- **Quadratic XP curve**: non-linear progression prevents level inflation while keeping early levels achievable for young students.
- **Source type validation**: `ALLOWED_SOURCE_TYPES = {"content", "quiz", "game", "coloring", "login"}` enforced at service boundary.
- **Trilingual game metadata**: `title`, `title_ar`, `title_fr` fields for Moroccan curriculum requirements (Arabic, French, English).

---

## 8. Analytics & Reporting Module

### 8.1 Purpose

Provides school-level KPI computation, analytics event emission with PII protection, and dashboard aggregation.

### 8.2 Service Analysis

**Analytics event emitter** (415 lines):
- Structured JSON events for Loki/Promtail ingestion.
- HMAC-SHA256 pseudonymization of `actor_id` — raw UUIDs never appear in analytics stream.
- Per-event property whitelist prevents accidental PII leakage.
- Schema versioning (current: v1) for CI drift detection.
- Role → ActorType mapping (STD→student, PAR→parent, TCH→teacher, etc.).

**KPI computation** (227 lines):
- `KPI-G1-001`: Pilot adoption activation (active users / total accounts over period).
- `KPI-G1-002`: Critical journey usage (users performing key actions like content progress, payments, submissions).
- Computable by school and configurable time period.

**DashboardAnalytics** (626 lines): Aggregated metrics for admin dashboards — enrollment trends, attendance rates, grade distributions, payment collection rates.

### 8.3 Key Technical Choices

- **PII-first design**: Both input sanitization and output validation, with trilingual regex patterns for Moroccan market (phone format: `(?:\+?212|0)[5-7]\d{8}`).
- **Actor pseudonymization**: `hmac.new(key, str(uuid), sha256).hexdigest()` — irreversible, consistent, enables analytics without GDPR exposure.

---

## 9. Admin Module

### 9.1 Purpose

Provides school administration capabilities: dashboard statistics, user management (CRUD with role-specific profiles), audit log access, school settings, GDPR compliance tools, and compliance reporting.

### 9.2 Service Analysis

**AdminService** (616 lines):
- `get_dashboard_stats()`: Aggregates users, active sessions, active invitations, 24h audit events, pending justifications, users-by-role breakdown — all in a single response for the admin dashboard widget.
- `list_users()`: Paginated user listing with search (by name/email), role filter, status filter, cursor-based pagination.
- User CRUD: create user with auto-password generation + invitation code issuance, update user with role change propagation, deactivate (soft, preserves data).
- Audit log listing with date range, action type, and actor filters.

**GDPRService** (436 lines):
- `export_user_data()`: Exports all data associated with a user across all modules (profile, enrollments, attendance, grades, notifications, payments) as structured JSON — GDPR data portability (Article 20).
- `anonymize_user()`: Replaces PII fields with anonymized values, preserving referential integrity for aggregate analytics while removing personal identifiers.
- `delete_user_data()`: Full erasure with cascade tracking — GDPR right to erasure (Article 17).
- `list_data_processing_activities()`: Documents all data processing activities per GDPR Article 30.

**ComplianceService**: Monitors data retention policies, generates compliance reports, tracks consent statuses.

### 9.3 Internal Interactions

- **Admin → IAM**: User creation, invitation management, session monitoring.
- **Admin → ERP/LMS/Finance**: Read access for dashboard aggregation.
- **Admin → Audit**: Full audit log access with filtering.

---

## 10. Program Management (v1.1, G49–G50)

### 10.1 Purpose

Manages the complete academic program lifecycle: program definition, versioning, eligibility rules, student enrollment with immutable snapshots, and inter-program equivalences. This module enables schools to define flexible pedagogical tracks (e.g., "Cycle primaire bilingue", "Filière internationale") and manage student transitions between them.

### 10.2 Service Decomposition

**ProgramService** — Program lifecycle:
- `create_program()`: Defines a program with code, title, target level, description, and active status. Programs are school-scoped and versioned.
- `create_version()`: Creates a new version of a program with effective dates and snapshot JSONB. Versions are the unit of enrollment, not programs themselves.
- `list_programs()`: Paginated listing with filtering by level, status, and school.

**EligibilityEngine** — Rule evaluation:
- Evaluates `EligibilityRule` predicates in order: pre-filters (age, level) → heavy predicates (transcripts, equivalences).
- Results: `eligible`, `eligible_with_conditions`, `ineligible`.
- Cacheable by `(student_id, version_id)` since deterministic.

**EnrollmentService** — Student program enrollment:
- `enroll_student()`: Creates enrollment with immutable `ProgramSnapshot` capturing the version state at enrollment time.
- `transfer_student()`: Creates `ProgramAssignmentEvent` audit trail (INITIAL → TRANSFER/PROMOTION).
- Tracks enrollment status: pending → active → completed → withdrawn.

### 10.3 Key Entities

| Entity | Role |
|--------|------|
| `Program` | Pedagogical track definition |
| `ProgramVersion` | Dated version (unit of enrollment) |
| `ProgramEquivalence` | Cross-version credit recognition |
| `EligibilityRule` | Declarative admission criteria |
| `Enrollment` | Student-version link with snapshot |
| `ProgramSnapshot` | Immutable version state at enrollment |
| `ProgramAssignmentEvent` | Audit trail of all program changes |

---

## 11. Document Management

### 11.1 Purpose

Centralizes all document handling: uploaded files, versioning, shared resources, and direct-to-S3 upload lifecycle. Supports three storage backends (local, MinIO, AWS S3) behind a unified `StorageBackend` protocol.

### 11.2 Service Decomposition

**DocumentService** — File lifecycle:
- `upload_document()`: Creates `Document` + `DocumentVersion` records, triggers async ClamAV scan via ARQ worker.
- `get_signed_download_url()`: Returns HTTP 307 redirect to presigned S3/MinIO URL (5-minute TTL).
- `share_resource()`: Creates `Resource` entries with visibility (school/class/private) and tags.

**UploadService** — Direct-to-S3 uploads:
- `initiate_upload()`: Returns presigned PUT URL; client uploads bytes directly to MinIO/S3.
- `complete_upload()`: Verifies checksum, triggers virus scan, updates `UploadSession` status.
- Three backends: `LocalStorage` (dev), `MinioStorage` (staging), `S3Storage` (production).

### 11.3 Security

- All file downloads via presigned URLs (no API file streaming)
- ClamAV async scan on every upload completion
- Infected files automatically deleted + uploader notified
- Prometheus metrics: `virus_scan_total{result}`, `virus_scan_duration_seconds`

---

## 12. MEN Compliance

### 12.1 Purpose

Ensures alignment with Moroccan Ministry of Education (Ministère de l'Éducation Nationale — MEN) curricula and objectives. Maps platform content to official pedagogical standards and generates compliance reports for school inspections.

### 12.2 Service Decomposition

**ComplianceService**:
- `generate_compliance_report()`: Analyzes content coverage against MEN curricula per level/subject.
- `map_curriculum()`: Links `ContentItem` or `Course` to `MenObjective` via `CurriculumMapping`.
- Tracks coverage gaps and generates actionable recommendations for school directors.

**Key entities**: `MenCurriculum`, `MenObjective`, `CurriculumMapping`, `ComplianceReport`.

---

## 13. Micro-Schools

### 13.1 Purpose

Supports informal education structures (micro-écoles, centres de soutien) with lightweight enrollment, group-based organization, simplified payments, and progress tracking outside the formal academic year system.

### 13.2 Service Decomposition

**MicroSchoolService**:
- `create_micro_school()`: Lightweight school record without academic year dependency.
- `create_group()`: Student groups within a micro-school.
- `track_payment()`: Simplified payment recording per enrollment.
- `log_progress()`: Qualitative progress notes per student per group.

**Key entities**: `MicroSchool`, `MicroGroup`, `MicroEnrollment`, `MicroPayment`, `MicroResource`, `MicroProgressLog`.

---

## 14. Cross-Cutting Services

### 10.1 Audit Service

`AuditService.log_event()` is called from every module (200+ call sites). Records: `school_id`, `actor_id`, `action_type`, `target_type`, `target_id`, `entity_before` (JSONB), `entity_after` (JSONB), `outcome`, `error_code`, `correlation_id` (from contextvars), `ip_address`. Uses an independent commit to ensure audit persistence even if the parent transaction fails.

### 10.2 Calendar Service

`CalendarService` (1,166 lines): School event management with recurring events, holidays, RSVP tracking, conflict detection, and timezone handling. Dispatches `EventCreated`, `EventUpdated`, `HolidayAdded`, `EventRSVPReceived` domain events.

### 10.3 File Storage

`FileStorageService`: Abstracted file storage supporting local filesystem and S3-compatible backends. Used by LMS content uploads, submission attachments, justification documents, student documents, and profile photos.

### 10.4 Real-time Service

`realtime.py`: Publishes events via `ws_manager` (Redis Pub/Sub → WebSocket) for:
- `publish_grade_published`: student/parent grade notifications.
- `publish_message_created`: chat message delivery.
- `publish_payment_updated`: payment status changes.
- `publish_event`: generic notification push.

### 10.5 Skill Passport

`SkillPassportService` (1,317 lines): Tracks student competency acquisition across subjects, maps to curriculum standards, generates skill profiles and progress reports.

---

## 15. Inter-Module Communication Map

```
IAM ──────→ (auth context) ──→ ALL MODULES
  │
  └── events: UserRegistered, NewDeviceLogin, PasswordChanged, TwoFactorEnabled
                          ↓
                    EventDispatcher ──→ Delivery Strategies ──→ NotificationHub
                          ↑                                          │
ERP ──── AttendanceThresholdExceeded ──────────────────────→         │
LMS ──── GradePublished, AssignmentCreated, etc. ──────────→    COM Module
Finance ─ InvoiceGenerated, PaymentReceived, etc. ─────────→         │
Calendar ─ EventCreated, HolidayAdded, etc. ───────────────→         │
                                                                     ↓
                                                              IN_APP + PUSH
                                                              + EMAIL + SMS
                                                              + WebSocket

LMS ─── quiz/activity completion ──→ Gamification (RewardsService.award)
Finance ─── enrollment data ←───── ERP
Analytics ─ audit events ←────────── ALL MODULES (KPI computation)
Admin ──── read access ──→ ALL MODULES (dashboard aggregation)
```

---

## 16. Business Value per Module

| Module | Business Value for Moroccan K-12 Schools |
|--------|------------------------------------------|
| **IAM** | Invitation-based onboarding eliminates open registration risks. School-scoped multi-tenancy isolates each school's data. 2FA protects admin/teacher accounts. |
| **ERP** | Digitizes attendance (replacing paper registers), enables parent visibility into absences, automates timetable generation respecting Moroccan academic constraints. |
| **LMS** | Replaces fragmented homework/grading tools. Late-penalty automation enforces school policies consistently. Moroccan 0-20 scale integration. |
| **Communication** | ABAC-enforced messaging ensures appropriate parent-teacher communication channels. Multi-channel notification reduces missed school events. |
| **Finance** | Automates fee collection with sibling discount policies common in Moroccan schools. Late fee automation with configurable grace periods. MAD currency native support. |
| **Gamification** | Engages young students (K-12) with age-appropriate game mechanics. Trilingual badges/titles for Arabic-French-English curriculum. |
| **Admin** | Single dashboard for school operations. GDPR/Loi 09-08 compliance tools (data export, anonymization, erasure). |
| **Program Management** | Enables flexible pedagogical tracks (bilingual, international). Immutable enrollment snapshots guarantee rule stability for enrolled students. |
| **Document Management** | Centralizes all school documents with versioning, virus scanning, and S3-compatible storage. Replaces scattered file shares. |
| **MEN Compliance** | Maps platform content to official Moroccan curricula. Generates inspection-ready compliance reports for school directors. |
| **Micro-Schools** | Supports informal education (centres de soutien) with lightweight enrollment and simplified payment tracking. |
| **Seed System** | ~93% table coverage with realistic demo data enables sales demos, CI testing, and rapid developer onboarding without manual data entry. |

---

## 17. Key Architecture Observations

1. **Consistent service contract**: Every service method follows the pattern: validate input → check authorization (ABAC) → execute within UnitOfWork → audit → dispatch events. This uniformity across 80+ service files (61+ service classes) reduces cognitive load and makes the codebase predictable.

2. **Domain events as integration backbone**: The 20+ domain event types with the `EventDispatcher` + `DeliveryStrategy` pattern decouple business modules from notification logic. Adding a new event type requires only: define the event dataclass, register handlers in `EVENT_HANDLERS`, implement recipient resolution.

3. **Financial precision**: The `Money` value object, combined with `Decimal`-backed database columns and structured invoice item breakdown, prevents the floating-point errors that plague naive financial implementations.

4. **Trilingual from the ground up**: Not a retrofit — game titles, notification templates, and badge descriptions all have `_ar`, `_fr`, `_en` variants as first-class fields.

5. **ABAC depth**: The communication module's 4-tier ABAC validation (parent→child-teacher, teacher→class-parent, student→class-teacher, admin→unrestricted) demonstrates genuine multi-role authorization beyond simple role checks.

6. **Module LOC distribution**: The Finance module is the densest (3,848 LOC) reflecting the complexity of fee structures, discount policies, payment flows, and late fee calculations. IAM (2,172 LOC) is second, reflecting the security surface area. LMS (3,112 LOC) is third, split across 6 sub-services for maintainability.
