# ANALYSIS_REPORT

Scope: read-only analysis of the requested execution surface for the Ecole Platform monorepo. Counts below use source-visible files from `rg --files` and exclude `__pycache__` artifacts. One exception: the requested output file itself, this report, is newly written.

## 1. Project Stats

### 1.1 Analysis-scope totals

| Metric | Value | Notes |
|---|---:|---|
| Scoped files | 248 | `backend/app/models`, `core`, `services`, `api/v1`, `repositories`, `domain`, `tests`, `.github/workflows`, `infra` |
| Scoped LOC | 67,571 | Source-visible LOC only |
| SQLAlchemy model classes | 91 | `Base` subclasses in `backend/app/models/*.py` |
| Service classes | 46 | `*Service` / `*LMSService` classes under `backend/app/services/**` |
| API endpoints | 264 | Route decorators in `backend/app/api/v1/*.py`, including `websocket` route |
| Test functions | 430 | Static count of `test_*` functions in `backend/tests/test_*.py` |
| Pytest collected tests | 508 | Verified with `cd backend && .venv/bin/python -m pytest --co -q` |
| CI workflows | 1 | `.github/workflows/ci.yml` |
| Infra files | 30 | Source-visible infra files |

### 1.2 Directory map

| Directory | Files | LOC |
|---|---:|---:|
| `backend/app/models` | 13 | 5,028 |
| `backend/app/core` | 24 | 4,915 |
| `backend/app/services` | 64 | 25,369 |
| `backend/app/api/v1` | 48 | 8,153 |
| `backend/app/repositories` | 31 | 9,989 |
| `backend/app/domain` | 17 | 680 |
| `backend/tests` | 20 | 8,022 |
| `.github/workflows` | 1 | 744 |
| `infra` | 30 | 4,671 |

### 1.3 Config and dependency snapshot

- `backend/requirements.txt`: FastAPI `0.115.*`, Uvicorn `0.34.*`, SQLAlchemy asyncio `2.0.*`, `asyncpg`, Alembic, Redis `5.2.*`, `python-jose`, `passlib[bcrypt]`, `httpx`, `arq`, `aiosmtplib`, `firebase-admin`, `weasyprint`, `openpyxl`, `Pillow`, `boto3`.
- `backend/requirements-dev.txt`: extends runtime deps with `pytest 8.3.*`, `pytest-asyncio 0.24.*`, `pytest-cov 6.0.*`, `websockets`, `ruff`.
- `backend/pyproject.toml`: not present. `backend/pytest.ini` is present and sets `asyncio_default_fixture_loop_scope = function`.
- `Makefile` first 150 lines: compose targets for dev/staging/prod/monitoring, backend test/lint/openapi, migrations, worker, DB shell, Redis shell.
- `.env.example`: DB/Redis/JWT/CORS/TZ/uploads/SMTP/S3/TOTP feature flags plus Grafana and Alertmanager settings.
- `.github/workflows/ci.yml`: 10 jobs covering lint, unit/integration/contract/security/e2e/load tests, coverage, web lint, and security audit.

## 2. Model Map

### 2.1 `backend/app/core/database.py`

| Item | Details |
|---|---|
| `Base` | `class Base(DeclarativeBase)` |
| `TimestampMixin` | `id`, `created_at`, `updated_at` |
| `SchoolScopedMixin` | required `school_id` FK to `schools.id`, indexed, `ondelete="CASCADE"` |
| `NullableSchoolScopedMixin` | nullable `school_id` FK to `schools.id`, indexed |
| `SoftDeleteMixin` | `deleted_at`, property `is_deleted`, methods `soft_delete()`, `restore()` |
| Engine | `create_async_engine(settings.database_url, echo=settings.app_env == "development", pool_size=20, max_overflow=10, pool_pre_ping=True)` |
| Session factory | `async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)` |
| DB dependency | `get_db()` yields session, commits on success, rollbacks on exception, closes always |

### 2.2 Model file summary

#### `iam.py`

Enums: `UserStatus`, `RoleCode`, `MembershipStatus`, `RecoveryStatus`, `LinkStatus`, `Gender`, `RelationshipType`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `User` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_email`, `validate_phone` | `is_active`, `has_2fa`, `is_email_verified` | Safe summary; explicitly excludes password and 2FA secrets |
| `Membership` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_active` | Includes id/user/role summary |
| `Session` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_expired`, `is_impersonated`, `is_revoked` | Includes id/user and impersonation state |
| `LoginHistory` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user and auth outcome context |
| `InvitationCode` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_expired`, `is_fully_used` | Includes id/role target/expiry context |
| `AccountRecoveryRequest` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_expired` | Includes id/user/status |
| `ParentChildLink` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes parent/child/status |
| `StudentProfile` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user |
| `ParentProfile` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user |
| `TeacherProfile` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user |
| `AdminProfile` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user |
| `ContentManagerProfile` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/user |

Validator/property notes:
- `User.validate_email`: strips, lowercases, requires `@`.
- `User.validate_phone`: strips spaces and dashes, requires leading `+`.
- `Session.is_expired`: checks `expires_at` via `getattr`, but `Session` does not define `expires_at`.
- `InvitationCode.is_fully_used`: checks `current_uses` and `max_uses` via `getattr`, but those fields are not defined.

#### `school.py`

Enums: `SchoolStatus`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `School` | `TimestampMixin`, `SoftDeleteMixin`, `Base` | `validate_email` | `is_active`, `is_subscription_valid` | Includes id/name/status |

Validator/property notes:
- `validate_email`: lowercases and strips if provided, requires `@`.
- `is_subscription_valid`: compares `subscription_end` against current UTC date.

#### `lms.py`

Enums: `CourseStatus`, `SubmissionStatus`, `AssessmentStatus`, `AssessmentResultStatus`, `ContentItemStatus`, `ContentProgressStatus`, `ActivitySessionStatus`, `ExerciseType`, `QuizStatus`, `QuestionType`, `QuizAttemptStatus`, `ContentOrigin`, `ContentSubmissionStatus`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `Course` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/title/status |
| `GradeCategory` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_weight` | - | Includes id/name/weight |
| `Rubric` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/title |
| `RubricCriterion` | `TimestampMixin`, `Base` | - | - | Includes id/title |
| `RubricLevel` | `TimestampMixin`, `Base` | - | - | Includes id/label/points |
| `Assignment` | `TimestampMixin`, `Base` | `validate_total_points`, `validate_late_penalty_per_day` | `is_past_due`, `accepts_late` | Includes id/title/type |
| `Submission` | `TimestampMixin`, `Base` | - | `is_graded` | Includes id/assignment/student/status |
| `SubmissionFile` | `TimestampMixin`, `Base` | - | - | Includes id/submission/file |
| `RubricScore` | `TimestampMixin`, `Base` | - | - | Includes submission/criterion/points |
| `Grade` | `TimestampMixin`, `Base` | `validate_score`, `validate_late_penalty` | - | Includes submission/score |
| `StudentPeriodAverage` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes student/class/period |
| `Assessment` | `TimestampMixin`, `Base` | - | - | Includes id/title/status |
| `AssessmentResult` | `TimestampMixin`, `Base` | - | - | Includes assessment/student/status |
| `ContentItem` | `TimestampMixin`, `NullableSchoolScopedMixin`, `Base` | - | - | Includes id/title/type/status |
| `ContentItemAsset` | `TimestampMixin`, `Base` | - | - | Includes id/content/file |
| `ContentProgress` | `TimestampMixin`, `Base` | - | - | Includes student/content/status |
| `Activity` | `TimestampMixin`, `NullableSchoolScopedMixin`, `Base` | - | - | Includes id/title/type |
| `ActivitySession` | `TimestampMixin`, `Base` | - | - | Includes id/student/activity/status |
| `ClassContentAssignment` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes class/content assignment |
| `ContentSubmission` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes content/submitted_by/status |
| `Quiz` | `TimestampMixin`, `NullableSchoolScopedMixin`, `Base` | - | `is_active` | Includes id/title/status |
| `QuizQuestion` | `TimestampMixin`, `Base` | - | - | Includes quiz/question type |
| `QuizAttempt` | `TimestampMixin`, `Base` | - | - | Includes quiz/student/status |
| `QuizResponse` | `TimestampMixin`, `Base` | - | - | Includes attempt/question |
| `QuestionBankItem` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes teacher/subject/difficulty |

Validator/property notes:
- `GradeCategory.validate_weight`: must be in `(0, 1]`.
- `Assignment.validate_total_points`: must be `> 0`.
- `Assignment.validate_late_penalty_per_day`: must be within `0..100`.
- `Grade.validate_score`: must be within `0..20`.
- `Grade.validate_late_penalty`: must be non-negative.
- `Quiz.is_active`: checks published status and start/end fields via `getattr`, but `start_at` / `starts_at` / `end_at` / `ends_at` are not declared on the model.

#### `erp.py`

Enums: `PeriodStatus`, `EnrollmentStatus`, `AttendanceStatus`, `JustificationStatus`, `ExceptionType`, `TimetableJobStatus`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `AcademicYear` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/date range |
| `Period` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/date range/status |
| `Class` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/code/name |
| `Enrollment` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_status` | `is_active` | Includes student/class/status |
| `TeacherAssignment` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes teacher/class |
| `AttendanceSession` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes class/date/slot |
| `AttendanceRecord` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes session/student/status |
| `AbsenceJustification` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes record/parent/status |
| `JustificationReview` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes justification/reviewer/decision |
| `AttendanceAlert` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_resolved` | Includes student/period/threshold |
| `TimetableConstraint` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes academic year/type |
| `TimetableGenerationJob` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes academic year/status |
| `TimetableSlot` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes class/day/time/teacher |
| `TimetableException` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes slot/date/type |

Validator/property notes:
- `Enrollment.validate_status`: validates membership in `EnrollmentStatus`.
- `AttendanceAlert.is_resolved`: checks `resolved_at` via `getattr`.

#### `billing.py`

Enums: `InvoiceStatus`, `PaymentAttemptStatus`, `PaymentMethod`, `WebhookEventStatus`, `FeeFrequency`, `FeeStructureStatus`, `FeeAssignmentStatus`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `Invoice` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_total_amount`, `validate_currency` | `is_overdue`, `is_paid` | Includes id/status/parent |
| `InvoiceItem` | `TimestampMixin`, `Base` | `validate_amount` | - | Includes invoice/description |
| `PaymentAttempt` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes invoice/status/provider |
| `PaymentProof` | `TimestampMixin`, `Base` | - | - | Includes payment/file hash |
| `ProviderWebhookEvent` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes provider event id/status |
| `FeeStructure` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes id/name/status |
| `FeeAssignment` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes structure/student/status |
| `SiblingDiscountPolicy` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_discount_percent` | - | Includes policy percentages |
| `LateFeePolicy` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes grace/percent/fixed |
| `PaymentPlan` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_completed` | Includes invoice/installment state |
| `Installment` | `TimestampMixin`, `Base` | `validate_amount` | `is_overdue` | Includes plan/installment/due date |

Validator/property notes:
- `Invoice.validate_total_amount`: must be non-negative.
- `Invoice.validate_currency`: must be in `ALLOWED_CURRENCIES`.
- `SiblingDiscountPolicy.validate_discount_percent`: each percent must be within `0..100`.
- `Installment.validate_amount`: must be `> 0`.

#### `com.py`

Enums: `ConsentStatus`, `ConsentScopeType`, `DeliveryChannel`, `DeliveryStatus`, `NotificationCategory`, `NotificationPriority`, `DigestFrequency`, `DevicePlatform`, `ConversationType`, `ParticipantRole`, `AnnouncementStatus`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `ConsentPreference` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes user/topic/channel |
| `Notification` | `TimestampMixin`, `SchoolScopedMixin`, `SoftDeleteMixin`, `Base` | - | `is_read` | Includes id/parent/category |
| `NotificationPreference` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes user/channel/category |
| `DeviceToken` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes user/platform |
| `NotificationDelivery` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `delivery_status` | Includes notification/channel/provider |
| `ParentFeedItem` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes parent/source/title |
| `Conversation` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | `is_group` | Includes conversation type/creator |
| `ConversationParticipant` | `TimestampMixin`, `Base` | - | - | Includes conversation/user/role |
| `Message` | `TimestampMixin`, `Base` | - | - | Includes conversation/sender |
| `MessageReadReceipt` | `TimestampMixin`, `Base` | - | - | Includes message/user/read timestamp |
| `Announcement` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes author/title/status |

#### `documents.py`

Enums: `DocumentCategory`, `ResourceType`, `ResourceVisibility`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `Document` | `TimestampMixin`, `SchoolScopedMixin`, `SoftDeleteMixin`, `Base` | - | `is_expired` | Includes filename/category/student linkage |
| `DocumentVersion` | `TimestampMixin`, `Base` | - | - | Includes document/version |
| `Resource` | `TimestampMixin`, `SchoolScopedMixin`, `SoftDeleteMixin`, `Base` | - | - | Includes title/type/visibility |
| `ResourceRating` | `TimestampMixin`, `Base` | `validate_rating` | - | Includes resource/user/rating |
| `StudentDocumentRequirement` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes category requirement |

#### `calendar.py`

Enums: `EventType`, `EventVisibility`, `EventRsvpStatus`, `EventReminderChannel`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `Event` | `TimestampMixin`, `SchoolScopedMixin`, `SoftDeleteMixin`, `Base` | - | `is_past` | Includes title/type/date window |
| `EventRSVP` | `TimestampMixin`, `Base` | - | - | Includes event/user/status |
| `EventReminder` | `TimestampMixin`, `Base` | - | - | Includes event/remind_at/channel |
| `EventReminderPreference` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes user/event type |
| `MoroccanHoliday` | `TimestampMixin`, `Base` | - | - | Includes code/date/name |

#### `reporting.py`

Enums: `ReportType`, `ReportJobStatus`, `DataExportFormat`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `ReportSchedule` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes creator/report/frequency |
| `ReportJob` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | `validate_status` | `is_complete`, `is_expired` | Includes requester/type/status |
| `DataExport` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes entity/format/requester |

#### `audit.py`

| Model | Mixins | Validators | Properties | `__repr__` |
|---|---|---|---|---|
| `AuditLog` | `TimestampMixin`, `SchoolScopedMixin`, `Base` | - | - | Includes action type / target type / outcome summary |

## 3. Permission Matrix

### 3.1 Core findings

- `PERM_*` constant names: 166
- Unique permission values: 158
- `PLATFORM_ROLES = {SUP, SYS, CONTENT_MGR}`
- `ROLE_HIERARCHY = {'SYS': ['SUP'], 'SUP': ['ADM'], 'ADM': ['DIR'], 'DIR': ['TCH']}`
- `get_effective_permissions(role_code, _stack=None)` recursively unions direct and inherited permissions and raises `ValueError("Circular role hierarchy detected at role ...")` on cycles.
- `role_has_permission(role_code, permission)` is a direct membership check against `get_effective_permissions(role_code)`.

### 3.2 Role counts

| Role | Direct | Inherited | Effective |
|---|---:|---:|---:|
| `SYS` | 4 | 130 | 134 |
| `SUP` | 7 | 124 | 131 |
| `ADM` | 19 | 105 | 124 |
| `DIR` | 41 | 64 | 105 |
| `TCH` | 64 | 0 | 64 |
| `PAR` | 44 | 0 | 44 |
| `STD` | 40 | 0 | 40 |
| `CONTENT_MGR` | 32 | 0 | 32 |

### 3.3 24-permission role matrix

| Permission | SYS | SUP | ADM | DIR | TCH | PAR | STD | CONTENT_MGR |
|---|---|---|---|---|---|---|---|---|
| `PERM_ADM_SCHOOL_READ` | Y | Y | Y | Y | N | N | N | N |
| `PERM_ADM_SCHOOL_MANAGE` | Y | Y | Y | N | N | N | N | N |
| `PERM_IAM_SESSION_CREATE` | Y | Y | Y | Y | Y | Y | Y | Y |
| `PERM_IAM_PASSWORD_CHANGE` | Y | Y | Y | Y | Y | Y | Y | Y |
| `PERM_ERP_ATTENDANCE_ANALYTICS_READ` | Y | Y | Y | Y | Y | N | N | N |
| `PERM_ERP_ATTENDANCE_ALERT_MANAGE` | Y | Y | Y | N | N | N | N | N |
| `PERM_ERP_TIMETABLE_GENERATE` | Y | Y | Y | Y | N | N | N | N |
| `PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE` | Y | Y | Y | Y | N | N | N | N |
| `PERM_LMS_ASSIGNMENT_CREATE` | Y | Y | Y | Y | Y | N | N | N |
| `PERM_LMS_SUBMISSION_CREATE` | N | N | N | N | N | N | Y | N |
| `PERM_LMS_SUBMISSION_GRADE` | Y | Y | Y | Y | Y | N | N | N |
| `PERM_LMS_RUBRIC_CREATE` | Y | Y | Y | Y | Y | N | N | N |
| `PERM_LMS_GRADEBOOK_READ` | Y | Y | Y | Y | Y | Y | Y | N |
| `PERM_LMS_QUESTION_BANK_MANAGE` | Y | Y | Y | Y | Y | N | N | Y |
| `PERM_BIL_FEE_CREATE` | Y | Y | Y | Y | N | N | N | N |
| `PERM_BIL_INVOICE_GENERATE` | Y | Y | Y | Y | N | N | N | N |
| `PERM_BIL_PAYMENT_INITIATE` | N | N | N | N | N | Y | N | N |
| `PERM_BIL_PAYMENT_RECONCILE` | Y | N | N | N | N | N | N | N |
| `PERM_COM_CONVERSATION_CREATE` | Y | Y | Y | Y | Y | Y | N | N |
| `PERM_COM_STD_MESSAGE_SEND` | N | N | N | N | N | N | Y | N |
| `PERM_REP_REPORT_GENERATE` | Y | Y | Y | Y | Y | Y | Y | N |
| `PERM_RPT_SCHEDULE_MANAGE` | Y | Y | Y | Y | N | N | N | N |
| `PERM_DOC_RESOURCE_MANAGE` | N | N | N | N | N | N | N | Y |
| `PERM_SYS_FEATURE_MANAGE` | Y | N | N | N | N | N | N | Y |

### 3.4 ABAC helpers (`backend/app/core/abac.py`)

- `apply_owner_scope(query, auth, owner_field="user_id", teacher_field="teacher_id", parent_field="parent_id", student_field="student_id", admin_roles=("ADM", "DIR", "SUP"))`
  - `ADM`, `DIR`, `SUP`: no scoping.
  - `TCH`: filters by `teacher_field == auth.user_id`.
  - `PAR`: filters by `parent_field == auth.user_id`.
  - `STD`: filters by `student_field == auth.user_id`.
  - fallback: filters by `owner_field == auth.user_id`.
- `validate_parent_child_access(db, parent_id, student_id)`: checks active `ParentChildLink` row for parent-child pair.
- `validate_teacher_class_access(db, teacher_id, class_id)`: checks `TeacherAssignment`.
- `validate_student_teacher_access(db, student_id, teacher_id)`: intersects enrolled classes and teacher-assigned classes.

## 4. Service Map

Coverage status below is qualitative: `Strong` means dedicated tests or multiple direct API/security flows; `Partial` means indirect coverage only; `None` means no dedicated coverage found.

### 4.1 LMS services

- `GradingService` in `backend/app/services/lms/grading_service.py`
  - Dependencies: inherited LMS base repos plus event dispatcher.
  - Public methods:
    - `grade_submission(submission_id, body, auth, ip_address) -> dict`: loads submission context, validates teacher ownership and grading mode, computes final score, persists grade/submission state, dispatches grade-published event.
    - `override_late_penalty(submission_id, auth, ip_address) -> dict`: removes late penalty from an existing grade and updates submission summary.
  - Repository surface to mock: `get_submission_with_context`, `get_grade_for_submission`, `save_grade`, `create_grade`, `save_submission`.
  - Events: `GradePublished`.
  - Common exceptions: `NotFoundError`, `AuthorizationError`, `ValidationError`.
  - Test coverage: `None`.

- `AssignmentService` in `backend/app/services/lms/assignment_service.py`
  - Dependencies: LMS repository, LMS serializer mixin, event dispatcher.
  - Public methods:
    - `create_assignment(...) -> dict`
    - `list_assignments(...) -> tuple[list[dict], str | None, bool]`
    - `upload_exercise_pdf(...) -> dict`
    - `create_submission(...) -> dict`
    - `upload_submission_file(...) -> dict`
    - `finalize_submission(...) -> dict`
  - Key logic: ownership checks, printable-PDF workflow, duplicate submission prevention, per-submission file-count cap, submission finalization checks.
  - Repository surface to mock: `get_course`, `list_assignments`, `get_assignment_with_course`, `find_active_submission`, `get_submission_with_context`, `count_submission_files`.
  - Events: `AssignmentCreated`, `SubmissionReceived`.
  - Common exceptions: `NotFoundError`, `AuthorizationError`, `ValidationError`.
  - Test coverage: `Partial` via API/security flows.

- `QuizService` in `backend/app/services/lms/quiz_service.py`
  - Dependencies: `QuizRepository`, LMS serializer mixin, event dispatcher.
  - Public methods:
    - `create_quiz(...) -> dict`
    - `list_quizzes(...) -> tuple[list[dict], str | None, bool]`
    - `get_quiz(quiz_id, auth) -> dict`
    - `update_quiz(...) -> dict`
    - `publish_quiz(...) -> dict`
    - `start_quiz_attempt(...) -> dict`
    - `respond_to_quiz_question(...) -> dict`
    - `submit_quiz_attempt(...) -> dict`
    - `get_quiz_analytics(...) -> dict`
  - Key logic: draft-only editing, max-attempt enforcement, time-limit enforcement, auto-grading submission flow, analytics aggregation.
  - Repository surface to mock: `list_quizzes_for_actor`, `get_question_counts`, `get_quiz`, `list_quiz_questions`, `count_quiz_questions`, `count_student_attempts`, `get_active_attempt`, `get_quiz_attempt`, `get_quiz_question`, `get_quiz_response`, `get_attempt_stats`, `sum_quiz_points`, `get_question_response_stats`.
  - Events: `QuizCompleted`.
  - Common exceptions: `NotFoundError`, `ValidationError`.
  - Test coverage: `Partial`.

- `LMSServiceBase` in `backend/app/services/lms/_helpers.py`
  - Dependencies: `LMSRepository`, `QuizRepository`, `EventDispatcher`.
  - Public methods:
    - `get_exercise_pdf(...) -> tuple[str, str, str]`
    - `get_submission_file(...) -> tuple[str, str, str]`
    - `preview_submission_files(...) -> dict`
    - `get_content_item(...) -> dict`
    - `get_content_asset(...) -> tuple[str, str, str]`
    - `get_quiz_attempt_results(...) -> dict`
  - Important helper: `calculate_late_penalty(assignment, submission, original_score)` returns original score when not late, enforces grace-period and max-late-days rules, raises `ValidationError` if late work is disallowed, and computes per-day penalty using `math.ceil(...)`.
  - Test coverage: `None`.

- `LMSSerializerMixin` in `backend/app/services/lms/_serializers.py`
  - Public methods: none. Internal serializer helpers only.
  - Protected serializers: `_course_to_dict`, `_assignment_to_dict`, `_submission_to_dict`, `_grade_to_dict`, `_content_item_to_dict`, `_assessment_to_dict`, `_activity_to_dict`, `_activity_session_to_dict`, `_quiz_to_dict`, `_quiz_question_to_dict`, `_attempt_to_dict`.
  - Test coverage: `None`.

### 4.2 Billing / IAM / ERP / reporting services

- `BillingService` in `backend/app/services/billing.py`
  - Dependencies: `BillingRepository`, `BillingEnhancementsRepository`, `AuditService`, `EventDispatcher`.
  - Public methods: `create_fee_structure`, `list_fee_structures`, `update_fee_structure`, `create_fee_assignment`, `bulk_create_fee_assignments`, `list_fee_assignments`, `get_sibling_policy`, `update_sibling_policy`, `get_late_fee_policy`, `update_late_fee_policy`, `generate_invoices`, `apply_late_fees`, `initiate_payment`, `get_payment_status`, `handle_provider_webhook`, `list_invoices`, `get_invoice`.
  - Key logic: fee setup/assignment, sibling discount application, invoice generation, late fee application, payment initiation and webhook reconciliation.
  - Repository surface to mock: `get_academic_year`, `create_fee_structure`, `get_fee_structure`, `save_fee_structure`, `get_user_by_id`, `get_fee_assignment`, `create_fee_assignment`, `create_fee_assignments`, `list_active_fee_assignments`, `get_invoice_by_id`, `get_payment_by_idempotency_key`, `get_payment_by_id`, `get_webhook_event_by_provider_event_id`, plus enhancement repo policy getters.
  - Events: invoice-generation and payment reconciliation events dispatched through `_dispatcher`.
  - Common exceptions: `NotFoundError`, `ConflictError`, `ValidationError`.
  - Test coverage: `Partial`.

- `PaymentPlanService` in `backend/app/services/payment_plan.py`
  - Dependencies: `BillingRepository`, `BillingEnhancementsRepository`, `AuditService`.
  - Public methods: `create_plan`, `list_plans`, `get_plan`, `mark_installment_paid`.
  - Key logic: invoice eligibility checks, installment splitting, plan retrieval and installment completion.
  - Repository surface to mock: `get_invoice_by_id`, `get_active_payment_plan_for_invoice`, `list_payment_plans`, `get_payment_plan`, `get_installment`.
  - Common exceptions: `NotFoundError`, `ConflictError`.
  - Test coverage: `None`.

- `AuthService` / `InvitationService` / `RecoveryService` / `TwoFactorService` / `EmailVerificationService` in `backend/app/services/auth.py`
  - Dependencies: `AuthRepository`, `AuditService`, Redis, `EventDispatcher`.
  - Public methods:
    - `AuthService`: `login`, `register`, `refresh`, `logout`, `get_profile`, `list_sessions`, `list_login_history`, `impersonate`, `stop_impersonation`, `revoke_session`, `change_password`
    - `InvitationService`: `create_invite`, `consume_invite`, `revoke_invite`
    - `RecoveryService`: `request_recovery`, `verify_otp`, `reset_password`
    - `TwoFactorService`: `setup`, `verify_setup`, `disable`, `verify_login`
    - `EmailVerificationService`: `send_verification_otp`, `verify_email`
  - Key logic: token issuance/rotation, session revocation, impersonation controls, recovery OTP and 2FA lifecycle, invitation consumption and membership creation.
  - Repository surface to mock: `get_user_by_email`, `get_membership`, `get_session_by_id`, `list_active_sessions`, `get_user_by_id`, `list_memberships`, `get_invitation_by_code_hash`, `create_invitation`, `consume_invitation`, `create_membership`, `create_recovery_request`, `get_recovery_request`, `save_recovery_request`, `revoke_all_sessions`, `save_user`.
  - Events: `UserRegistered` plus audit events and token/2FA state changes.
  - Common exceptions: `AuthenticationError`, `AuthorizationError`, `ConflictError`, `NotFoundError`, `RateLimitError`, `ValidationError`.
  - Test coverage: `Strong`.

- `AttendanceAnalyticsService` in `backend/app/services/attendance_analytics.py`
  - Dependencies: `AttendanceAnalyticsRepository`, `ERPRepository`, `AuditService`, `EventDispatcher`.
  - Public methods: `compute_student_absence_rate`, `compute_class_absence_rates`, `get_absence_trends`, `list_alerts`, `check_thresholds_and_alert`.
  - Key logic: role-scoped student/class analytics, threshold evaluation, alert creation, alert enrichment.
  - Repository surface to mock: `compute_student_absence_count`, `list_class_students`, `compute_class_absence_rates`, `get_absence_trends`, `list_alerts`, `list_user_names`.
  - Events: `AttendanceThresholdExceeded`.
  - Common exceptions: `NotFoundError`.
  - Test coverage: `None`.

- `CommunicationService` in `backend/app/services/communication.py`
  - Dependencies: `MessagingRepository`, `AuditService`.
  - Public methods: `create_conversation`, `list_conversations`, `list_messages`, `send_message`, `search_messages`, `mark_read`, `get_read_status`, `list_feed`.
  - Key logic: messaging ABAC for parent/teacher/student combinations, participant verification, attachment ownership validation, read-receipt updates, parent feed listing.
  - Repository surface to mock: `get_membership`, `list_conversations_for_user`, `list_conversation_messages`, `get_message_sent_at`, `search_messages`, `get_message_in_conversation`, `list_unread_message_ids`, `list_read_receipts`, `list_parent_feed_items`.
  - Events: realtime message publishing through messaging stack.
  - Common exceptions: `ValidationError`, `NotFoundError`.
  - Test coverage: `Partial`.

- `SchoolService` in `backend/app/services/school.py`
  - Dependencies: `SchoolRepository`.
  - Public methods: `create_school`, `get_school`, `list_schools`, `update_school`, `deactivate_school`.
  - Key logic: `SUP`-only create/deactivate, scoped school access for `ADM`/`DIR`, soft deactivation.
  - Repository surface to mock: `get_school`, `list_schools`, create/save helpers.
  - Common exceptions: `NotFoundError`.
  - Test coverage: `None`.

- `TimetableGeneratorService` in `backend/app/services/timetable_generator.py`
  - Dependencies: `TimetableGenerationRepository`, `AuditService`.
  - Public methods: `set_constraints`, `list_constraints`, `generate`, `get_job_status`, `preview_generated`, `apply_generated`.
  - Key logic: academic-year validation, solver input assembly, generation job lifecycle, preview/apply split.
  - Repository surface to mock: `list_constraints`, `list_classes_for_academic_year`, `get_class_student_counts`, `list_teacher_assignments_for_academic_year`, `list_existing_subject_teacher_pairs`, `list_existing_room_names`, `get_job`.
  - Common exceptions: `NotFoundError`, `ConflictError`.
  - Test coverage: `None`.

- `GradebookService` in `backend/app/services/gradebook.py`
  - Dependencies: `GradebookRepository`, `ERPRepository`, inherited LMS helpers.
  - Public methods: `set_grade_categories`, `list_grade_categories`, `compute_student_average`, `compute_class_averages`, `get_gradebook`, `get_student_transcript`.
  - Key logic: grade-category validation, weighted-average computation, transcript aggregation, student visibility enforcement.
  - Repository surface to mock: `list_grade_categories`, `get_student_grades_by_category`, `get_student_transcript`, `list_student_period_enrollments`, `get_academic_year`.
  - Common exceptions: `ValidationError`, `NotFoundError`.
  - Test coverage: `None`.

- `ReportSchedulerService` in `backend/app/services/report_scheduler.py`
  - Dependencies: `ReportScheduleRepository`, `ReportsRepository`, `AuditService`.
  - Public methods: `create_schedule`, `list_schedules`, `update_schedule`, `disable_schedule`, `run_schedule`, `process_due_schedules`.
  - Key logic: schedule validation, enabled/disabled state management, immediate/manual execution, periodic batch processing.
  - Repository surface to mock: `list_schedules`, `get_schedule`, `list_due_schedules` plus report job submission helpers.
  - Common exceptions: `NotFoundError`.
  - Test coverage: `Partial`.

- `ReportsService` in `backend/app/services/reports.py`
  - Dependencies: `ReportsRepository`, `DashboardAnalyticsService`.
  - Public methods: `submit_report_job`, `list_report_jobs`, `get_report_options`, `get_job_for_reader`, `get_job_for_token`, `serialize_job`, `build_download_token`, `parse_download_token`, `generate_report_job`, `cleanup_expired_reports`.
  - Key logic: cached report reuse, role-aware option generation, signed download token handling, template render, cleanup of expired files.
  - Repository surface to mock: `find_cached_report`, `list_report_jobs`, `list_periods`, `list_classes_for_teacher`, `list_students_for_class`, `list_classes`, `list_users_by_role`, `list_children`, `get_user_in_school`, `get_report_job`, `list_expired_report_jobs`.
  - Common exceptions: `NotFoundError`.
  - Test coverage: `Partial`.

## 5. Domain Value Objects / Events / Protocols

### 5.1 Value objects

- `MoroccanGrade` (`backend/app/domain/value_objects/grade.py`)
  - Immutable `Decimal` grade on `0..20`.
  - `from_float()` quantizes to `0.01` with `ROUND_HALF_UP`.
  - `average()` rejects empty list.
  - `mention` thresholds:
    - `>= 16`: `Très Bien`
    - `>= 14`: `Bien`
    - `>= 12`: `Assez Bien`
    - `>= 10`: `Passable`
    - else: `Insuffisant`
- `Money` (`backend/app/domain/value_objects/money.py`)
  - Immutable non-negative `Decimal`, currency default `MAD`.
  - `from_float()` and `zero()` constructors.
  - `__add__` / `__sub__` reject currency mismatch; subtraction also rejects negative result.
  - `__mul__` rounds to `0.01`.
- `UserId` / `SchoolId` (`backend/app/domain/value_objects/typed_id.py`)
  - Frozen typed UUID wrappers.
  - `from_str()` validates UUID format through `uuid.UUID(...)`.
  - Equality/hash behavior is dataclass-derived.
- `RoleSet` (`backend/app/domain/value_objects/role_set.py`)
  - Validates against `VALID_ROLES = {"STD", "PAR", "TCH", "ADM", "DIR", "SYS", "CONTENT_MGR", "SUP"}`.
  - `has()`, `has_any()`, `is_staff`, `is_educator`, `primary_role`.
  - Primary-role priority: `SUP > SYS > DIR > ADM > CONTENT_MGR > TCH > PAR > STD`.

### 5.2 Domain events

| File | Event classes |
|---|---|
| `events/base.py` | `DomainEvent(event_id, occurred_at, school_id, actor_id)` |
| `events/auth.py` | `UserRegistered(user_id, role, school_id)`, `PasswordChanged(user_id)`, `TwoFactorEnabled(user_id)`, `NewDeviceLogin(user_id, device_name, ip_address, user_agent)` |
| `events/billing.py` | `InvoiceGenerated(invoice_id, student_id, amount, due_date)`, `PaymentReceived(payment_id, invoice_id, amount, method)`, `PaymentFailed(payment_id, invoice_id, reason)` |
| `events/erp.py` | `AttendanceThresholdExceeded(student_id, period_id, student_name, absence_count, total_sessions, absence_rate, threshold_exceeded)` |
| `events/documents.py` | `DocumentUploaded(document_id, filename, student_id)`, `DocumentExpiring(document_id, student_id, document_name, expires_at)`, `ResourceShared(resource_id, title, class_id)` |
| `events/calendar.py` | `EventCreated(event_id, title, start_at, class_id)`, `EventUpdated(event_id, title, changes)`, `HolidayAdded(holiday_name, start_date, end_date)`, `EventRSVPReceived(event_id, user_id, status)` |
| `events/lms.py` | `GradePublished(student_id, course_title, score, teacher_name)`, `AssignmentCreated(assignment_id, course_title, due_at, class_id)`, `QuizCompleted(student_id, quiz_title, score_percent)`, `SubmissionReceived(submission_id, student_name, assignment_title, teacher_id)`, `ContentPublished(content_id, title, class_id)` |

### 5.3 Protocols / interfaces

- `Evaluatable` (`protocols/evaluatable.py`)
  - `list_for_class(school_id, class_id, status=None) -> list[dict]`
  - `list_for_student(school_id, student_id) -> list[dict]`
  - `get_detail(item_id) -> dict | None`
  - `get_results(item_id) -> list[dict]`
- `protocols/grading.py`
  - `QuizAttemptLike`, `QuizQuestionLike`, `QuizResponseLike`: structural quiz protocols.
  - `QuizGradingRepository`: `get_latest_attempt_for_student`, `list_quiz_questions`, `list_attempt_responses`.
  - `GradingStrategy`: abstract `grade(...) -> MoroccanGrade`, `can_auto_grade() -> bool`.
  - `QuizAutoGradeStrategy`: auto-grades stored quiz responses.
  - `ManualGradeStrategy`: wraps manually supplied score.

## 6. API Map

### 6.1 Focus files

| File | Prefix | Endpoints | Permission/auth pattern |
|---|---|---:|---|
| `schools.py` | `/schools` | 5 | `requires_role(SUP)` or `requires_permission(PERM_ADM_SCHOOL_*)` |
| `gradebook.py` | `/gradebook` | 5 | `get_current_user` only; authorization pushed into service layer |
| `rubrics.py` | `/` | 6 | `PERM_LMS_RUBRIC_*`, `PERM_LMS_SUBMISSION_GRADE`, one `get_current_user` read |
| `billing.py` | `/billing` | 14 | literal `PERM-BIL:*` strings |
| `payments.py` | `/payments` | 3 | literal `PERM-BIL:payment:*` strings |
| `attendance_analytics.py` | `/analytics/attendance` | 5 | literal `PERM-ERP:attendance-*` strings |
| `timetable_generation.py` | `/timetable` | 6 | literal `PERM-ERP:timetable-*` strings |
| `messaging.py` | `/messages` | 7 | `requires_any_permission(...)` |
| `question_bank.py` | `/` | 5 | `PERM_LMS_QUESTION_BANK_READ/MANAGE` |
| `assignments.py` | `/assignments` | 4 | all endpoints currently use `PERM_LMS_ASSIGNMENT_CREATE` |
| `submissions.py` | `/submissions` | 7 | submission create/grade/file permissions |

Detailed focus endpoints:

- `schools.py`
  - `POST /schools` -> `requires_role(SUP)`
  - `GET /schools` -> `PERM_ADM_SCHOOL_READ`
  - `GET /schools/{school_id}` -> `PERM_ADM_SCHOOL_READ`
  - `PATCH /schools/{school_id}` -> `PERM_ADM_SCHOOL_MANAGE`
  - `DELETE /schools/{school_id}` -> `requires_role(SUP)`
- `gradebook.py`
  - `POST /gradebook/categories`
  - `GET /gradebook/categories/{class_id}/{period_id}`
  - `POST /gradebook/compute/{class_id}/{period_id}`
  - `GET /gradebook/transcript/{student_id}`
  - `GET /gradebook/{class_id}/{period_id}`
  - All use `Depends(get_current_user)`; no decorator-level permission constant.
- `rubrics.py`
  - `POST /rubrics` -> `PERM_LMS_RUBRIC_CREATE`
  - `GET /rubrics` -> `PERM_LMS_RUBRIC_READ`
  - `GET /rubrics/{rubric_id}` -> `PERM_LMS_RUBRIC_READ`
  - `POST /rubrics/{rubric_id}/duplicate` -> `PERM_LMS_RUBRIC_CREATE`
  - `POST /submissions/{submission_id}/grade-rubric` -> `PERM_LMS_SUBMISSION_GRADE`
  - `GET /submissions/{submission_id}/rubric-results` -> `get_current_user`
- `billing.py`
  - fee-structure CRUD, fee-assignment create/bulk/list, invoice generation, sibling-policy get/update, late-fee-policy get/update, payment plan create/list/get.
- `payments.py`
  - `POST /payments/initiate`
  - `GET /payments/{attempt_id}`
  - `POST /payments/webhook/provider`
- `attendance_analytics.py`
  - student analytics, class analytics, trends, alerts, threshold check.
- `timetable_generation.py`
  - constraints set/list, generation start, job read, preview, apply.
- `messaging.py`
  - create/list conversations, search, list messages, send, mark-read, read-status.
- `question_bank.py`
  - add question, list questions, import from quiz, generate quiz, stats.
- `assignments.py`
  - create/list assignments, upload/download exercise PDF.
- `submissions.py`
  - create submission, grade, override late penalty, upload/download files, finalize, preview.

### 6.2 Full API inventory

Appendix B contains all 48 API files with prefixes and endpoint lists.

## 7. Existing Test Inventory

### 7.1 `backend/tests/conftest.py`

| Fixture | Scope | Provides |
|---|---|---|
| `base_url` | function | `BASE_URL` env or default `http://localhost:8000/api/v1` |
| `school_id` | function | fixed seeded school UUID |
| `client` | function | async `httpx.AsyncClient(base_url=BASE_URL)` |
| `admin_token` | function | seeded admin login token |
| `teacher_token` | function | seeded teacher login token |
| `student_token` | function | seeded student login token |
| `parent_token` | function | seeded parent login token |

Backward-compatibility requirements:
- Tests assume a running backend, not an in-process app.
- Tests assume seeded credentials and fixed school ID from the seeding flow.
- Auth response shape must continue exposing `response.json()["data"]["access_token"]`.

### 7.2 Test files and counts

| Test file | Count | Coverage summary |
|---|---:|---|
| `test_auth.py` | 30 | auth/session flows |
| `test_contract.py` | 36 | API contracts / response shapes |
| `test_phase13_notifications.py` | 10 | notifications |
| `test_phase14_reports_analytics.py` | 5 | reports / analytics |
| `test_phase15_calendar_events.py` | 5 | calendar/events |
| `test_phase16_document_management.py` | 6 | documents/resources |
| `test_phase1b_profiles.py` | 24 | profiles |
| `test_phase2c_register.py` | 21 | registration |
| `test_phase2d_family.py` | 31 | family / parent-child flows |
| `test_phase3.py` | 44 | mixed platform flows |
| `test_phase3b_uploads.py` | 11 | uploads |
| `test_phase3c_websocket.py` | 6 | realtime/websocket |
| `test_phase3d_filters.py` | 29 | filtering/search behavior |
| `test_phase3e_tasks.py` | 23 | tasks/background work |
| `test_rbac_security.py` | 56 | permissions / RBAC |
| `test_security_audit.py` | 19 | security audit paths |
| `test_unit_iam.py` | 31 | IAM unit tests |
| `test_unit_response.py` | 43 | response envelope/unit behavior |

Areas with no dedicated direct tests found:
- `GradingService`
- `LMSServiceBase` helper methods / late penalty edge cases
- `PaymentPlanService`
- `AttendanceAnalyticsService`
- `SchoolService`
- `TimetableGeneratorService`
- `GradebookService`
- `ReportSchedulerService`

### 7.3 Test collection command

Collection results:

- `cd backend && .venv/bin/python -m pytest --co -q` -> `508 tests collected in 14.26s`
- `cd backend && .venv/bin/python -m pytest tests/test_unit_iam.py -q` -> `31 passed`

Notes:
- Running pytest from repo root still picks up the root `.env`, which is not compatible with the current `Settings` model because it contains extra variables.
- Running from `backend/` with `backend/.venv` works correctly.

## 8. Infrastructure Map

### 8.1 CI (`.github/workflows/ci.yml`)

Trigger:
- `push` and `pull_request` on `main` and `develop`

Jobs:

| Job | Needs | Services |
|---|---|---|
| `lint` | - | - |
| `unit-tests` | `lint` | - |
| `integration-tests` | `unit-tests` | Postgres, Redis |
| `contract-tests` | `integration-tests` | Postgres, Redis |
| `security-tests` | `integration-tests` | Postgres, Redis |
| `coverage-report` | `unit-tests`, `integration-tests`, `contract-tests`, `security-tests`, `e2e-tests`, `security-audit`, `load-tests` | - |
| `web-lint` | - | - |
| `e2e-tests` | `web-lint`, `integration-tests` | Postgres, Redis |
| `security-audit` | `integration-tests` | Postgres, Redis |
| `load-tests` | `integration-tests` | Postgres, Redis |

### 8.2 Compose / runtime topology

- `infra/docker-compose.dev.yml`
  - Services: `postgres`, `redis`, `backend`, `worker`, `web`
  - Named network: `ecole-network`
  - Volumes: `postgres_data`, `redis_data`, `web_node_modules`, `upload_data`
- `infra/docker-compose.staging.yml`
  - Services: `postgres`, `redis`, `backend`, `nginx`
  - Differences from dev: production backend target, stricter flags, WAL archiving, no local dev web/worker stack.
- `infra/docker-compose.prod.yml`
  - Services: `backend`, `postgres`, `redis`, `web`, `nginx`, `worker`, `certbot`
  - Docker secrets for DB/Redis/JWT/SMTP credentials
  - Resource limits and healthchecks configured
  - Backend intentionally omits `container_name` to preserve scaling
- `infra/docker-compose.monitoring.yml`
  - Services: `prometheus`, `grafana`, `alertmanager`, `loki`, `promtail`

### 8.3 Dockerfiles / reverse proxy / monitoring

- `backend/Dockerfile`
  - `development` and `production` targets
  - production runs as non-root `appuser`
  - healthcheck: `http://localhost:8000/api/v1/health`
- `web/Dockerfile`
  - dev stage, build stage, nginx production stage
- `infra/nginx/nginx-prod.conf`
  - TLS `1.2/1.3`
  - HSTS enabled
  - rate limits for API/web/auth
  - security headers (`X-Frame-Options`, `CSP`, `Permissions-Policy`, etc.)
  - WebSocket proxy on `/api/v1/ws`
  - `/metrics` restricted to internal ranges
- `infra/prometheus/prometheus.yml`
  - scrape targets: backend metrics, Prometheus self-scrape
  - alertmanager target configured
- `infra/prometheus/alert_rules.yml`
  - severity groups `sev1_critical`, `sev2_major`, `sev3_warning`
  - alert coverage: API availability/latency/error rate, DB pool, webhook failures, auth success rate, backup failures, payment failures
- `infra/loki/loki-config.yml`
  - TSDB schema, filesystem storage, retention-enabled compactor, ingestion/burst limits
- `infra/loki/promtail-config.yml`
  - Docker service discovery
  - labels service/container/level/correlation_id
  - redaction pipeline for password/token fields

### 8.4 Ops scripts / DB / Redis

- `infra/scripts/deploy.sh`: preflight checks, image backup tags, build/pull, optional migrations, staged restart, backend rollback on failed health.
- `infra/scripts/healthcheck.sh`: checks API, Postgres, Redis, disk, certificates, and container health with plain/JSON/quiet outputs.
- `infra/postgres/init.sql`: creates `app_user` and `app_readonly`, grants schema/default privileges, enables `uuid-ossp` and `pgcrypto`.
- `infra/redis/redis.conf`: `maxmemory 256mb`, `allkeys-lru`, AOF enabled, protected mode on.

## 9. Reference Documents

- `TESTING_ARCHITECTURE.md`
  - Defines the intended test pyramid, categories, factory strategy, integration/security/contract/performance split, and recommended tooling.
- `CICD_INFRASTRUCTURE.md`
  - Defines the target-state CI/CD hardening plan: security scanning, migration safety, Docker optimization, deployment/backup strategy, observability, alerting, and onboarding.
- `EXECUTION_PROMPTS.md`
  - Lists all 25 execution prompts: `T-01` through `T-13`, and `CI-01` through `CI-12`.
- `EXECUTION_CHECKLIST.md`
  - Progress checklist aligned to the 25 prompts and final validation pass.
- `FINAL_VERIFICATION_REPORT.md`
  - Claims `28/28` checks passing and explicitly states the LMS split introduced `grading_service.py` and `_serializers.py`.
- `DEPLOYMENT.md`
  - Repo-root shim now exists and points to the canonical guide at `infra/DEPLOYMENT.md`.

## 10. Risk Assessment

### 10.1 Previously identified blockers now resolved

- `backend/app/api/v1/submissions.py`
  - Grading endpoints now use `GradingService` directly instead of calling grading methods on `AssignmentService`.
- `DEPLOYMENT.md`
  - Repo-root shim now exists and forwards readers to `infra/DEPLOYMENT.md`.

### 10.2 Remaining high-risk inconsistencies

- `backend/app/models/iam.py` / `backend/app/models/lms.py`
  - `Session.is_expired`, `InvitationCode.is_fully_used`, and `Quiz.is_active` are now explicitly documented as compatibility hooks for legacy or future dynamic attributes rather than current persisted schema fields.
- API permission drift
  - `billing.py`, `payments.py`, `attendance_analytics.py`, `timetable_generation.py`, `attendance.py`, `notifications.py`, `invitations.py`, `timetable.py`, and similar files use literal permission strings rather than imported constants.
  - That increases mismatch risk against `core/permissions.py`.
- Coarse endpoint gating
  - `assignments.py` uses `PERM_LMS_ASSIGNMENT_CREATE` even for list and file download operations.
  - `gradebook.py` exposes endpoints with `get_current_user` only and relies on service-layer checks.

### 10.3 Test and environment risks

- Pytest works via `backend/.venv`, but running it from repo root still loads the root `.env` and fails settings validation because of extra variables not declared in `app.core.config.Settings`.
- Several high-change areas targeted by the execution prompts have weak or absent direct tests: grading, timetable generation, gradebook, attendance analytics, payment plans, report scheduling.

### 10.4 Structural readiness notes

- No fatal circular import surfaced during read-through.
- Permissions hierarchy code explicitly defends against circular role inheritance.
- Repository/service/API layering is now consistent for the submissions/grading split.

## 11. Factory Requirements

Required fields below are the strictly required model-local constructor fields inferred from mapped columns, plus required mixin-provided `school_id` where applicable. Defaults, nullable fields, timestamps, and generated IDs are omitted.

### 11.1 `iam.py`

- `User`: `school_id`, `email`, `full_name`, `password_hash`
- `Membership`: `school_id`, `user_id`, `role_code`
- `Session`: `school_id`, `user_id`
- `LoginHistory`: `school_id`, `user_id`
- `InvitationCode`: `school_id`, `code_hash`, `role_target`, `expires_at`
- `AccountRecoveryRequest`: `school_id`, `user_id`, `expires_at`
- `ParentChildLink`: `school_id`, `parent_user_id`, `child_user_id`, `linked_at`
- `StudentProfile`: `school_id`, `user_id`
- `ParentProfile`: `school_id`, `user_id`
- `TeacherProfile`: `school_id`, `user_id`
- `AdminProfile`: `school_id`, `user_id`
- `ContentManagerProfile`: `school_id`, `user_id`

### 11.2 `school.py`

- `School`: `name`, `code`

### 11.3 `lms.py`

- `Course`: `school_id`, `class_id`, `teacher_id`, `title`
- `GradeCategory`: `school_id`, `class_id`, `period_id`, `name`, `weight`
- `Rubric`: `school_id`, `teacher_id`, `title`
- `RubricCriterion`: `rubric_id`, `title`
- `RubricLevel`: `criterion_id`, `label`, `points`
- `Assignment`: `course_id`, `teacher_id`, `title`
- `Submission`: `assignment_id`, `student_id`
- `SubmissionFile`: `submission_id`, `file_path`
- `RubricScore`: `submission_id`, `criterion_id`, `points_awarded`
- `Grade`: `submission_id`, `teacher_id`, `score`
- `StudentPeriodAverage`: `school_id`, `student_id`, `class_id`, `period_id`, `weighted_average`, `mention`, `computed_at`
- `Assessment`: `class_id`, `teacher_id`, `title`
- `AssessmentResult`: `assessment_id`, `student_id`
- `ContentItem`: `title`, `content_type`
- `ContentItemAsset`: `content_item_id`, `file_path`
- `ContentProgress`: `student_id`, `content_item_id`
- `Activity`: `type`, `title`
- `ActivitySession`: `student_id`, `activity_id`
- `ClassContentAssignment`: `school_id`, `teacher_id`, `class_id`, `content_item_id`
- `ContentSubmission`: `school_id`, `content_item_id`, `submitted_by`
- `Quiz`: `created_by`, `title`
- `QuizQuestion`: `quiz_id`, `question_type`, `question_text`, `correct_answer`
- `QuizAttempt`: `quiz_id`, `student_id`
- `QuizResponse`: `attempt_id`, `question_id`
- `QuestionBankItem`: `school_id`, `teacher_id`, `subject`, `difficulty`, `question_type`, `question_data`

### 11.4 `erp.py`

- `AcademicYear`: `school_id`, `date_start`, `date_end`
- `Period`: `school_id`, `academic_year_id`, `date_start`, `date_end`
- `Class`: `school_id`, `code`, `academic_year_id`, `name`
- `Enrollment`: `school_id`, `student_id`, `class_id`, `period_id`
- `TeacherAssignment`: `school_id`, `teacher_id`, `class_id`, `period_id`
- `AttendanceSession`: `school_id`, `class_id`, `period_id`, `teacher_id`, `session_date`, `slot`
- `AttendanceRecord`: `school_id`, `attendance_session_id`, `student_id`, `status`
- `AbsenceJustification`: `school_id`, `attendance_record_id`, `parent_id`
- `JustificationReview`: `school_id`, `justification_id`, `reviewer_id`, `decision`
- `AttendanceAlert`: `school_id`, `student_id`, `period_id`, `absence_count`, `total_sessions`, `absence_rate`, `threshold_exceeded`
- `TimetableConstraint`: `school_id`, `academic_year_id`, `constraint_type`
- `TimetableGenerationJob`: `school_id`, `academic_year_id`
- `TimetableSlot`: `school_id`, `class_id`, `academic_year_id`, `day_of_week`, `start_time`, `end_time`, `subject`, `teacher_id`
- `TimetableException`: `school_id`, `timetable_slot_id`, `exception_date`, `exception_type`

### 11.5 `billing.py`

- `Invoice`: `school_id`, `parent_id`, `issued_date`, `due_date`
- `InvoiceItem`: `invoice_id`, `description`, `amount`, `unit_price`
- `PaymentAttempt`: `school_id`, `invoice_id`, `parent_id`, `idempotency_key`
- `PaymentProof`: `payment_attempt_id`, `proof_hash`, `received_at`
- `ProviderWebhookEvent`: `school_id`, `provider_event_id`, `provider_event_received_at`
- `FeeStructure`: `school_id`, `academic_year_id`, `name`, `amount`
- `FeeAssignment`: `school_id`, `fee_structure_id`, `student_id`
- `SiblingDiscountPolicy`: `school_id`
- `LateFeePolicy`: `school_id`
- `PaymentPlan`: `school_id`, `invoice_id`, `total_installments`
- `Installment`: `plan_id`, `installment_number`, `amount`, `due_date`

### 11.6 `com.py`

- `ConsentPreference`: `school_id`, `user_id`, `topic`, `channel`, `scope_type`
- `Notification`: `school_id`, `parent_id`, `idempotency_key`, `title`
- `NotificationPreference`: `school_id`, `user_id`, `channel`, `category`
- `DeviceToken`: `school_id`, `user_id`, `token`, `platform`, `last_active_at`
- `NotificationDelivery`: `school_id`, `notification_id`, `channel`
- `ParentFeedItem`: `school_id`, `parent_id`, `source_type`, `title`
- `Conversation`: `school_id`, `created_by`
- `ConversationParticipant`: `conversation_id`, `user_id`, `joined_at`
- `Message`: `conversation_id`, `sender_id`, `body`, `sent_at`
- `MessageReadReceipt`: `message_id`, `user_id`, `read_at`
- `Announcement`: `school_id`, `author_id`, `title`, `body`

### 11.7 `documents.py`

- `Document`: `school_id`, `uploader_id`, `filename`, `original_filename`, `mime_type`, `size_bytes`, `sha256`, `storage_path`
- `DocumentVersion`: `document_id`, `version_number`, `uploader_id`, `filename`, `original_filename`, `mime_type`, `storage_path`, `size_bytes`, `sha256`
- `Resource`: `school_id`, `uploader_id`, `title`, `type`, `file_id`
- `ResourceRating`: `resource_id`, `user_id`, `rating`
- `StudentDocumentRequirement`: `school_id`, `category`

### 11.8 `calendar.py`

- `Event`: `school_id`, `title_fr`, `type`, `visibility`, `start_at`, `end_at`, `created_by`
- `EventRSVP`: `event_id`, `user_id`, `status`, `responded_at`
- `EventReminder`: `event_id`, `remind_at`, `channel`
- `EventReminderPreference`: `school_id`, `user_id`, `event_type`
- `MoroccanHoliday`: `code`, `holiday_date`, `name_fr`

### 11.9 `reporting.py`

- `ReportSchedule`: `school_id`, `created_by`, `report_type`, `frequency`
- `ReportJob`: `school_id`, `requester_id`, `type`, `parameters_hash`
- `DataExport`: `school_id`, `requester_id`, `entity`, `format`

### 11.10 `audit.py`

- `AuditLog`: `school_id`, `action_type`, `outcome`

## 12. Readiness Confirmation

`READY TO EXECUTE`

Non-blocking but high-risk:

- weak direct test coverage on several execution-prompt target areas
- pytest should be run from `backend/` using `backend/.venv`

The codebase is structurally ready for prompt-by-prompt execution with the current caveats above.

---

## Appendix A. File Inventory

### `backend/app/models` (13 files, 5,028 LOC)

- `backend/app/models/reporting.py`
- `backend/app/models/lms.py`
- `backend/app/models/com.py`
- `backend/app/models/calendar.py`
- `backend/app/models/feature.py`
- `backend/app/models/__init__.py`
- `backend/app/models/ai.py`
- `backend/app/models/documents.py`
- `backend/app/models/erp.py`
- `backend/app/models/iam.py`
- `backend/app/models/billing.py`
- `backend/app/models/audit.py`
- `backend/app/models/school.py`

### `backend/app/core` (24 files, 4,915 LOC)

- `backend/app/core/unit_of_work.py`
- `backend/app/core/dependencies.py`
- `backend/app/core/middleware.py`
- `backend/app/core/exceptions.py`
- `backend/app/core/search.py`
- `backend/app/core/permissions.py`
- `backend/app/core/rate_limit.py`
- `backend/app/core/storage.py`
- `backend/app/core/abac.py`
- `backend/app/core/redis.py`
- `backend/app/core/ws_manager.py`
- `backend/app/core/response.py`
- `backend/app/core/feature_flags.py`
- `backend/app/core/__init__.py`
- `backend/app/core/security.py`
- `backend/app/core/database.py`
- `backend/app/core/filtering.py`
- `backend/app/core/idempotency.py`
- `backend/app/core/request_utils.py`
- `backend/app/core/config.py`
- `backend/app/core/password_policy.py`
- `backend/app/core/tasks.py`
- `backend/app/core/metrics.py`
- `backend/app/core/totp.py`

### `backend/app/services` (64 files, 25,369 LOC)

- `backend/app/services/payment_plan.py`
- `backend/app/services/sms.py`
- `backend/app/services/gradebook.py`
- `backend/app/services/email_digest.py`
- `backend/app/services/payment_retry.py`
- `backend/app/services/progress.py`
- `backend/app/services/report_scheduler.py`
- `backend/app/services/kpi.py`
- `backend/app/services/analytics.py`
- `backend/app/services/dashboard_analytics.py`
- `backend/app/services/admin.py`
- `backend/app/services/calendar.py`
- `backend/app/services/rsvp.py`
- `backend/app/services/student_work.py`
- `backend/app/services/push_config.py`
- `backend/app/services/data_export.py`
- `backend/app/services/email.py`
- `backend/app/services/question_bank.py`
- `backend/app/services/notification_hub.py`
- `backend/app/services/feature.py`
- `backend/app/services/resource_library.py`
- `backend/app/services/file_storage.py`
- `backend/app/services/communication.py`
- `backend/app/services/quiz_grading.py`
- `backend/app/services/timetable_generator.py`
- `backend/app/services/student_documents.py`
- `backend/app/services/reports.py`
- `backend/app/services/reminders.py`
- `backend/app/services/profile_loader.py`
- `backend/app/services/__init__.py`
- `backend/app/services/gdpr.py`
- `backend/app/services/event_dispatcher.py`
- `backend/app/services/profile.py`
- `backend/app/services/cms.py`
- `backend/app/services/realtime.py`
- `backend/app/services/erp.py`
- `backend/app/services/billing.py`
- `backend/app/services/audit.py`
- `backend/app/services/school.py`
- `backend/app/services/overdue_reminders.py`
- `backend/app/services/auth.py`
- `backend/app/services/rubric.py`
- `backend/app/services/attendance_analytics.py`
- `backend/app/services/delivery/push.py`
- `backend/app/services/delivery/base.py`
- `backend/app/services/delivery/in_app.py`
- `backend/app/services/delivery/__init__.py`
- `backend/app/services/delivery/email_delivery.py`
- `backend/app/services/delivery/sms_delivery.py`
- `backend/app/services/ai/claude_provider.py`
- `backend/app/services/ai/provider_base.py`
- `backend/app/services/ai/provider_factory.py`
- `backend/app/services/ai/__init__.py`
- `backend/app/services/ai/mock_provider.py`
- `backend/app/services/ai/ai_service.py`
- `backend/app/services/lms/_serializers.py`
- `backend/app/services/lms/_helpers.py`
- `backend/app/services/lms/assignment_service.py`
- `backend/app/services/lms/content_service.py`
- `backend/app/services/lms/quiz_service.py`
- `backend/app/services/lms/course_service.py`
- `backend/app/services/lms/progress_service.py`
- `backend/app/services/lms/grading_service.py`
- `backend/app/services/lms/__init__.py`

### `backend/app/api/v1` (48 files, 8,153 LOC)

- `backend/app/api/v1/payments.py`
- `backend/app/api/v1/exports.py`
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/activities.py`
- `backend/app/api/v1/recovery.py`
- `backend/app/api/v1/class_assignments.py`
- `backend/app/api/v1/quizzes.py`
- `backend/app/api/v1/timetable_generation.py`
- `backend/app/api/v1/billing.py`
- `backend/app/api/v1/teacher.py`
- `backend/app/api/v1/results.py`
- `backend/app/api/v1/attendance_analytics.py`
- `backend/app/api/v1/events.py`
- `backend/app/api/v1/messaging.py`
- `backend/app/api/v1/content_library.py`
- `backend/app/api/v1/consents.py`
- `backend/app/api/v1/profiles.py`
- `backend/app/api/v1/rubrics.py`
- `backend/app/api/v1/gradebook.py`
- `backend/app/api/v1/announcements.py`
- `backend/app/api/v1/devices.py`
- `backend/app/api/v1/assessments.py`
- `backend/app/api/v1/submissions.py`
- `backend/app/api/v1/router.py`
- `backend/app/api/v1/progress.py`
- `backend/app/api/v1/classes.py`
- `backend/app/api/v1/analytics.py`
- `backend/app/api/v1/invoices.py`
- `backend/app/api/v1/courses.py`
- `backend/app/api/v1/invitations.py`
- `backend/app/api/v1/notifications.py`
- `backend/app/api/v1/reports.py`
- `backend/app/api/v1/timetable.py`
- `backend/app/api/v1/admin.py`
- `backend/app/api/v1/content.py`
- `backend/app/api/v1/assignments.py`
- `backend/app/api/v1/ws.py`
- `backend/app/api/v1/question_bank.py`
- `backend/app/api/v1/enrollments.py`
- `backend/app/api/v1/schools.py`
- `backend/app/api/v1/feed.py`
- `backend/app/api/v1/features.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/api/v1/gdpr.py`
- `backend/app/api/v1/ai.py`
- `backend/app/api/v1/documents.py`
- `backend/app/api/v1/attendance.py`
- `backend/app/api/v1/cms.py`

### `backend/app/repositories` (31 files, 9,989 LOC)

- `backend/app/repositories/login_history.py`
- `backend/app/repositories/messaging.py`
- `backend/app/repositories/base.py`
- `backend/app/repositories/gradebook.py`
- `backend/app/repositories/progress.py`
- `backend/app/repositories/billing_enhancements.py`
- `backend/app/repositories/analytics.py`
- `backend/app/repositories/notifications.py`
- `backend/app/repositories/reports.py`
- `backend/app/repositories/lms.py`
- `backend/app/repositories/admin.py`
- `backend/app/repositories/calendar.py`
- `backend/app/repositories/question_bank.py`
- `backend/app/repositories/feature.py`
- `backend/app/repositories/profile_loader.py`
- `backend/app/repositories/__init__.py`
- `backend/app/repositories/report_schedule.py`
- `backend/app/repositories/gdpr.py`
- `backend/app/repositories/profile.py`
- `backend/app/repositories/ai.py`
- `backend/app/repositories/documents.py`
- `backend/app/repositories/cms.py`
- `backend/app/repositories/attendance_analytics.py`
- `backend/app/repositories/erp.py`
- `backend/app/repositories/billing.py`
- `backend/app/repositories/audit.py`
- `backend/app/repositories/timetable_generation.py`
- `backend/app/repositories/quiz.py`
- `backend/app/repositories/school.py`
- `backend/app/repositories/auth.py`
- `backend/app/repositories/rubric.py`

### `backend/app/domain` (17 files, 680 LOC)

- `backend/app/domain/__init__.py`
- `backend/app/domain/protocols/evaluatable.py`
- `backend/app/domain/protocols/__init__.py`
- `backend/app/domain/protocols/grading.py`
- `backend/app/domain/events/base.py`
- `backend/app/domain/events/lms.py`
- `backend/app/domain/events/calendar.py`
- `backend/app/domain/events/__init__.py`
- `backend/app/domain/events/documents.py`
- `backend/app/domain/events/erp.py`
- `backend/app/domain/events/billing.py`
- `backend/app/domain/events/auth.py`
- `backend/app/domain/value_objects/typed_id.py`
- `backend/app/domain/value_objects/role_set.py`
- `backend/app/domain/value_objects/__init__.py`
- `backend/app/domain/value_objects/money.py`
- `backend/app/domain/value_objects/grade.py`

### `backend/tests` (20 files, 8,022 LOC)

- `backend/tests/test_rbac_security.py`
- `backend/tests/test_phase15_calendar_events.py`
- `backend/tests/test_unit_iam.py`
- `backend/tests/test_phase3d_filters.py`
- `backend/tests/test_security_audit.py`
- `backend/tests/test_phase2c_register.py`
- `backend/tests/test_phase3c_websocket.py`
- `backend/tests/test_contract.py`
- `backend/tests/test_phase14_reports_analytics.py`
- `backend/tests/test_phase16_document_management.py`
- `backend/tests/__init__.py`
- `backend/tests/test_phase3.py`
- `backend/tests/test_phase13_notifications.py`
- `backend/tests/test_phase3b_uploads.py`
- `backend/tests/test_unit_response.py`
- `backend/tests/test_auth.py`
- `backend/tests/test_phase1b_profiles.py`
- `backend/tests/conftest.py`
- `backend/tests/test_phase2d_family.py`
- `backend/tests/test_phase3e_tasks.py`

### `.github/workflows` (1 file, 744 LOC)

- `.github/workflows/ci.yml`

### `infra` (30 files, 4,671 LOC)

- `infra/backup/pg_backup.sh`
- `infra/backup/pg_restore.sh`
- `infra/backup/audit_worm_export.sh`
- `infra/backup/restore_drill.sh`
- `infra/prometheus/prometheus.yml`
- `infra/prometheus/alert_rules.yml`
- `infra/docker-compose.prod.yml`
- `infra/scripts/healthcheck.sh`
- `infra/scripts/ssl-renew.sh`
- `infra/scripts/deploy.sh`
- `infra/docker-compose.override.yml.example`
- `infra/nginx/nginx.conf`
- `infra/nginx/nginx-staging.conf`
- `infra/nginx/nginx-prod.conf`
- `infra/DEPLOYMENT.md`
- `infra/certs/.gitignore`
- `infra/postgres/init.sql`
- `infra/docker-compose.dev.yml`
- `infra/docker-compose.monitoring.yml`
- `infra/docker-compose.staging.yml`
- `infra/grafana/dashboards/api-overview.json`
- `infra/grafana/dashboards/billing-providers.json`
- `infra/grafana/dashboards/db-redis-health.json`
- `infra/grafana/dashboards/auth-sessions.json`
- `infra/alertmanager/alertmanager.yml`
- `infra/redis/redis.conf`
- `infra/loki/loki-config.yml`
- `infra/loki/promtail-config.yml`
- `infra/grafana/provisioning/dashboards/dashboards.yml`
- `infra/grafana/provisioning/datasources/datasources.yml`

## Appendix B. Full API Inventory

### `__init__.py` (prefix `/`, 0 endpoints)

### `activities.py` (prefix `/activities`, 3 endpoints)

- `GET /activities` :: `list_activities` :: response model not declared :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_LMS_ACTIVITY_SESSION_CREATE)`, `get_db`
- `POST /activities/sessions` :: `create_activity_session` :: response model not declared :: deps `requires_permission(PERM_LMS_ACTIVITY_SESSION_CREATE)`, `get_db`
- `POST /activities/sessions/{session_id}/complete` :: `complete_activity_session` :: response model not declared :: deps `requires_permission(PERM_LMS_ACTIVITY_SESSION_COMPLETE)`, `get_db`

### `admin.py` (prefix `/admin`, 15 endpoints)

- `GET /admin/dashboard` :: `dashboard_stats` :: deps `requires_permission(PERM_ADM_DASHBOARD_READ)`, `get_db`
- `GET /admin/users` :: `list_users` :: deps `requires_permission(PERM_ADM_USER_READ)`, `get_db`
- `POST /admin/impersonate/{user_id}` :: `impersonate_user` :: deps `requires_permission(PERM_ADM_IMPERSONATE)`, `get_db`, `get_redis`
- `POST /admin/stop-impersonation` :: `stop_impersonation` :: deps `get_current_user`, `get_db`, `get_redis`
- `GET /admin/users/{user_id}/login-history` :: `list_user_login_history` :: deps `requires_role(ADM, DIR, SUP)`, `get_db`, `get_redis`
- `PUT /admin/users/{user_id}/suspend` :: `suspend_user` :: deps `requires_permission(PERM_ADM_USER_MANAGE)`, `get_db`
- `PUT /admin/users/{user_id}/activate` :: `activate_user` :: deps `requires_permission(PERM_ADM_USER_MANAGE)`, `get_db`
- `PUT /admin/users/{user_id}/role` :: `change_user_role` :: deps `requires_permission(PERM_ADM_USER_MANAGE)`, `get_db`
- `GET /admin/invitations` :: `list_invitations` :: deps `requires_permission(PERM_ADM_INVITATION_READ)`, `get_db`
- `GET /admin/audit-logs` :: `list_audit_logs` :: deps `requires_permission(PERM_ADM_AUDIT_READ)`, `get_db`
- `GET /admin/justifications` :: `list_justifications` :: deps `requires_permission(PERM_ERP_ABSENCE_REVIEW)`, `get_db`
- `POST /admin/register-batch` :: `register_batch` :: deps `requires_permission(PERM_ADM_USER_CREATE)`, `get_db`
- `POST /admin/parent-child-links` :: `create_parent_child_link` :: deps `requires_permission(PERM_IAM_PARENT_LINK_CREATE)`, `get_db`
- `GET /admin/parent-child-links` :: `list_parent_child_links` :: deps `requires_permission(PERM_IAM_PARENT_LINK_READ)`, `get_db`
- `DELETE /admin/parent-child-links/{link_id}` :: `revoke_parent_child_link` :: deps `requires_permission(PERM_IAM_PARENT_LINK_DELETE)`, `get_db`

### `ai.py` (prefix `/`, 5 endpoints)

- `POST /writing-attempts` :: `create_writing_attempt` :: deps `requires_permission(PERM_IA_WRITING_ATTEMPT_CREATE)`, `get_db`
- `POST /ai/preferences/opt-out` :: `update_ai_opt_out` :: deps `requires_permission(PERM_IA_PREFERENCE_UPDATE)`, `get_db`
- `GET /recommendations` :: `get_recommendations` :: deps `requires_permission(PERM_IA_RECOMMENDATION_READ)`, `get_db`
- `GET /kpis` :: `get_kpis` :: deps `requires_permission(PERM_IA_REQUEST_READ)`, `get_db`
- `GET /events/schema` :: `get_event_schema` :: deps `requires_permission(PERM_IA_REQUEST_READ)`, `get_db`

### `analytics.py` (prefix `/analytics`, 5 endpoints)

- `GET /analytics/overview` :: `analytics_overview` :: deps `requires_permission(PERM_REP_ANALYTICS_READ)`, `get_db`
- `GET /analytics/attendance` :: `analytics_attendance` :: deps `requires_permission(PERM_REP_ANALYTICS_READ)`, `get_db`
- `GET /analytics/grades` :: `analytics_grades` :: deps `requires_permission(PERM_REP_ANALYTICS_READ)`, `get_db`
- `GET /analytics/billing` :: `analytics_billing` :: deps `requires_permission(PERM_REP_ANALYTICS_READ)`, `get_db`
- `GET /analytics/engagement` :: `analytics_engagement` :: deps `requires_permission(PERM_REP_ANALYTICS_READ)`, `get_db`

### `announcements.py` (prefix `/announcements`, 4 endpoints)

- `POST /announcements` :: `create_announcement` :: deps `requires_permission(PERM_COM_ANNOUNCEMENT_CREATE)`, `get_db`
- `GET /announcements` :: `list_announcements` :: deps `requires_permission(PERM_COM_ANNOUNCEMENT_READ)`, `get_db`
- `PUT /announcements/{announcement_id}` :: `update_announcement` :: deps `requires_permission(PERM_COM_ANNOUNCEMENT_CREATE)`, `get_db`
- `POST /announcements/{announcement_id}/publish` :: `publish_announcement` :: deps `requires_permission(PERM_COM_ANNOUNCEMENT_PUBLISH)`, `get_db`

### `assessments.py` (prefix `/assessments`, 4 endpoints)

- `POST /assessments` :: `create_assessment` :: deps `requires_permission(PERM_LMS_ASSESSMENT_CREATE)`, `get_db`
- `GET /assessments` :: `list_assessments` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_LMS_ASSESSMENT_READ)`, `get_db`
- `POST /assessments/{assessment_id}/publish` :: `publish_assessment` :: deps `requires_permission(PERM_LMS_ASSESSMENT_PUBLISH)`, `get_db`
- `POST /assessments/{assessment_id}/results` :: `submit_assessment_result` :: deps `requires_permission(PERM_LMS_ASSESSMENT_SUBMIT)`, `get_db`

### `assignments.py` (prefix `/assignments`, 4 endpoints)

- `POST /assignments` :: `create_assignment` :: deps `requires_permission(PERM_LMS_ASSIGNMENT_CREATE)`, `get_db`
- `GET /assignments` :: `list_assignments` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_LMS_ASSIGNMENT_CREATE)`, `get_db`
- `POST /assignments/{assignment_id}/exercise-pdf` :: `upload_exercise_pdf` :: deps `requires_permission(PERM_LMS_ASSIGNMENT_CREATE)`, `get_db`
- `GET /assignments/{assignment_id}/exercise-pdf` :: `download_exercise_pdf` :: deps `requires_permission(PERM_LMS_ASSIGNMENT_CREATE)`, `get_db`

### `attendance.py` (prefix `/attendance`, 3 endpoints)

- `POST /attendance/sessions` :: `create_attendance_session` :: deps `requires_permission('PERM-ERP:attendance:mark')`, `get_db`
- `POST /attendance/justifications` :: `create_justification` :: deps `requires_permission('PERM-ERP:absence:justify')`, `get_db`
- `POST /attendance/justifications/{justification_id}/review` :: `review_justification` :: deps `requires_permission('PERM-ERP:absence:review')`, `get_db`

### `attendance_analytics.py` (prefix `/analytics/attendance`, 5 endpoints)

- `GET /analytics/attendance/student/{student_id}` :: `get_student_attendance_analytics` :: deps `requires_permission('PERM-ERP:attendance-analytics:read')`, `get_db`
- `GET /analytics/attendance/class/{class_id}` :: `get_class_attendance_analytics` :: deps `requires_permission('PERM-ERP:attendance-analytics:read')`, `get_db`
- `GET /analytics/attendance/trends/{class_id}` :: `get_attendance_trends` :: deps `requires_permission('PERM-ERP:attendance-analytics:read')`, `get_db`
- `GET /analytics/attendance/alerts` :: `list_attendance_alerts` :: deps `requires_permission('PERM-ERP:attendance-alert:manage')`, `get_db`
- `POST /analytics/attendance/check-thresholds` :: `check_attendance_thresholds` :: deps `requires_permission('PERM-ERP:attendance-alert:manage')`, `get_db`

### `auth.py` (prefix `/auth`, 14 endpoints)

- `POST /auth/login` :: `login` :: deps `get_db`, `get_redis`
- `POST /auth/register` :: `register` :: deps `get_db`, `get_redis`
- `POST /auth/refresh` :: `refresh` :: deps `get_db`, `get_redis`
- `POST /auth/logout` :: `logout` :: deps `get_current_user`, `get_db`, `get_redis`
- `GET /auth/me` :: `me` :: deps `get_current_user`, `get_db`, `get_redis`
- `GET /auth/sessions` :: `list_sessions` :: deps `get_current_user`, `get_db`, `get_redis`
- `GET /auth/login-history` :: `login_history` :: deps `get_current_user`, `get_db`, `get_redis`
- `DELETE /auth/sessions/{session_id}` :: `revoke_session` :: deps `get_current_user`, `get_db`, `get_redis`
- `POST /auth/change-password` :: `change_password` :: deps `get_current_user`, `get_db`, `get_redis`
- `POST /auth/2fa/setup` :: `two_factor_setup` :: deps `get_current_user`, `get_db`, `get_redis`
- `POST /auth/2fa/verify-setup` :: `two_factor_verify_setup` :: deps `get_current_user`, `get_db`, `get_redis`
- `POST /auth/2fa/disable` :: `two_factor_disable` :: deps `get_current_user`, `get_db`, `get_redis`
- `POST /auth/2fa/verify` :: `two_factor_verify_login` :: deps `get_db`, `get_redis`
- `POST /auth/verify-email` :: `verify_email` :: deps `get_db`, `get_redis`

### `billing.py` (prefix `/billing`, 14 endpoints)

- `POST /billing/fee-structures` :: `create_fee_structure` :: deps `requires_permission('PERM-BIL:fee:create')`, `get_db`
- `GET /billing/fee-structures` :: `list_fee_structures` :: deps `requires_permission('PERM-BIL:fee:read')`, `get_db`
- `PUT /billing/fee-structures/{fee_structure_id}` :: `update_fee_structure` :: deps `requires_permission('PERM-BIL:fee:update')`, `get_db`
- `POST /billing/fee-assignments` :: `create_fee_assignment` :: deps `requires_permission('PERM-BIL:fee:assign')`, `get_db`
- `POST /billing/fee-assignments/bulk` :: `bulk_create_fee_assignments` :: deps `requires_permission('PERM-BIL:fee:assign')`, `get_db`
- `GET /billing/fee-assignments` :: `list_fee_assignments` :: deps `requires_permission('PERM-BIL:fee:read')`, `get_db`
- `POST /billing/generate-invoices` :: `generate_invoices` :: deps `requires_permission('PERM-BIL:invoice:generate')`, `get_db`
- `GET /billing/sibling-policy` :: `get_sibling_policy` :: deps `requires_permission('PERM-BIL:sibling-policy:manage')`, `get_db`
- `PUT /billing/sibling-policy` :: `update_sibling_policy` :: deps `requires_permission('PERM-BIL:sibling-policy:manage')`, `get_db`
- `GET /billing/late-fee-policy` :: `get_late_fee_policy` :: deps `requires_permission('PERM-BIL:late-fee:manage')`, `get_db`
- `PUT /billing/late-fee-policy` :: `update_late_fee_policy` :: deps `requires_permission('PERM-BIL:late-fee:manage')`, `get_db`
- `POST /billing/payment-plans` :: `create_payment_plan` :: deps `requires_permission('PERM-BIL:payment-plan:create')`, `get_db`
- `GET /billing/payment-plans` :: `list_payment_plans` :: deps `requires_permission('PERM-BIL:payment-plan:read')`, `get_db`
- `GET /billing/payment-plans/{plan_id}` :: `get_payment_plan` :: deps `requires_permission('PERM-BIL:payment-plan:read')`, `get_db`

### `class_assignments.py` (prefix `/class-assignments`, 1 endpoint)

- `POST /class-assignments` :: `create_teacher_assignment` :: deps `requires_permission('PERM-ERP:assignment:update')`, `get_db`

### `classes.py` (prefix `/classes`, 1 endpoint)

- `GET /classes/{class_id}` :: `get_class` :: deps `requires_permission('PERM-ERP:class:read')`, `get_db`

### `cms.py` (prefix `/cms`, 6 endpoints)

- `POST /cms/content` :: `create_cms_content` :: deps `requires_permission(PERM_CMS_CONTENT_CREATE)`, `get_db`
- `GET /cms/content` :: `list_cms_content` :: deps `requires_permission(PERM_CMS_CONTENT_MANAGE)`, `get_db`
- `PUT /cms/content/{content_id}` :: `update_cms_content` :: deps `requires_permission(PERM_CMS_CONTENT_MANAGE)`, `get_db`
- `DELETE /cms/content/{content_id}` :: `delete_cms_content` :: deps `requires_permission(PERM_CMS_CONTENT_DELETE)`, `get_db`
- `GET /cms/submissions` :: `list_submissions` :: deps `requires_permission(PERM_CMS_CONTENT_REVIEW)`, `get_db`
- `POST /cms/submissions/{submission_id}/review` :: `review_submission` :: deps `requires_permission(PERM_CMS_CONTENT_REVIEW)`, `get_db`

### `consents.py` (prefix `/consents`, 2 endpoints)

- `GET /consents` :: `list_consents` :: deps `requires_permission(PERM_COM_CONSENT_UPDATE)`, `get_db`
- `PUT /consents/{consent_id}` :: `update_consent` :: deps `requires_permission(PERM_COM_CONSENT_UPDATE)`, `get_db`

### `content.py` (prefix `/content-items`, 6 endpoints)

- `GET /content-items` :: `list_content_items` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_LMS_CONTENT_READ)`, `get_db`
- `GET /content-items/{content_item_id}` :: `get_content_item` :: deps `requires_permission(PERM_LMS_CONTENT_READ)`, `get_db`
- `POST /content-items/{content_item_id}/progress` :: `update_content_progress` :: deps `requires_permission(PERM_LMS_CONTENT_PROGRESS_WRITE)`, `get_db`
- `POST /content-items/{content_item_id}/assets` :: `upload_content_asset` :: deps `requires_permission(PERM_LMS_CONTENT_ASSET_UPLOAD)`, `get_db`
- `GET /content-items/{content_item_id}/assets/{asset_id}` :: `download_content_asset` :: deps `requires_permission(PERM_LMS_CONTENT_ASSET_READ)`, `get_db`
- `DELETE /content-items/{content_item_id}/assets/{asset_id}` :: `delete_content_asset` :: deps `requires_permission(PERM_LMS_CONTENT_ASSET_DELETE)`, `get_db`

### `content_library.py` (prefix `/`, 6 endpoints)

- `GET /content/library` :: `browse_content_library` :: deps `requires_permission(PERM_LMS_CONTENT_READ)`, `get_db`
- `POST /content/assign` :: `assign_content_to_class` :: deps `requires_permission(PERM_CMS_CONTENT_ASSIGN)`, `get_db`
- `DELETE /content/assign/{assignment_id}` :: `unassign_content` :: deps `requires_permission(PERM_CMS_CONTENT_ASSIGN)`, `get_db`
- `POST /content/submit-for-review` :: `submit_for_review` :: deps `requires_permission(PERM_CMS_CONTENT_SUBMIT)`, `get_db`
- `GET /content/my-submissions` :: `list_my_submissions` :: deps `requires_permission(PERM_CMS_CONTENT_SUBMIT)`, `get_db`
- `GET /classes/{class_id}/content` :: `list_class_content` :: deps `requires_permission(PERM_LMS_CONTENT_READ)`, `get_db`

### `courses.py` (prefix `/courses`, 2 endpoints)

- `POST /courses` :: `create_course` :: deps `requires_permission(PERM_LMS_COURSE_PUBLISH)`, `get_db`
- `GET /courses` :: `list_courses` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_LMS_COURSE_PUBLISH)`, `get_db`

### `devices.py` (prefix `/devices`, 3 endpoints)

- `GET /devices` :: `list_devices` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `POST /devices/register` :: `register_device` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `DELETE /devices/{device_id}` :: `delete_device` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`

### `documents.py` (prefix `/`, 24 endpoints)

- `POST /documents/upload` :: `upload_document` :: deps `requires_permission(PERM_DOC_DOCUMENT_UPLOAD)`, `get_db`
- `GET /documents` :: `list_documents` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `GET /documents/options` :: `get_document_options` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `GET /documents/{document_id}/versions` :: `list_document_versions` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `GET /documents/{document_id}/versions/{version_number}` :: `get_document_version` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `POST /documents/{document_id}/versions/{version_number}/restore` :: `restore_document_version` :: deps `requires_permission(PERM_DOC_DOCUMENT_UPLOAD)`, `get_db`
- `GET /documents/{document_id}` :: `get_document` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `GET /documents/{document_id}/download` :: `download_document` :: deps `optional_current_user`, `get_db`
- `GET /documents/{document_id}/preview` :: `preview_document` :: deps `optional_current_user`, `get_db`
- `DELETE /documents/{document_id}` :: `delete_document` :: deps `requires_permission(PERM_DOC_DOCUMENT_DELETE)`, `get_db`
- `POST /documents/bulk-download` :: `create_bulk_download` :: deps `requires_permission(PERM_DOC_BULK_DOWNLOAD)`, `get_db`
- `GET /documents/bulk-download` :: `download_bulk_archive` :: deps `get_db`
- `POST /documents/bulk-delete` :: `bulk_delete_documents` :: deps `requires_permission(PERM_DOC_BULK_DELETE)`, `get_db`
- `POST /students/{student_id}/documents` :: `link_student_document` :: deps `requires_permission(PERM_DOC_STUDENT_DOCUMENT_LINK)`, `get_db`
- `GET /students/{student_id}/documents` :: `list_student_documents` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `GET /students/{student_id}/documents/checklist` :: `get_student_document_checklist` :: deps `requires_permission(PERM_DOC_DOCUMENT_READ)`, `get_db`
- `POST /resources` :: `create_resource` :: deps `requires_permission(PERM_DOC_RESOURCE_CREATE)`, `get_db`
- `GET /resources` :: `list_resources` :: deps `requires_permission(PERM_DOC_RESOURCE_READ)`, `get_db`
- `GET /resources/{resource_id}` :: `get_resource` :: deps `requires_permission(PERM_DOC_RESOURCE_READ)`, `get_db`
- `PUT /resources/{resource_id}` :: `update_resource` :: deps `requires_permission(PERM_DOC_RESOURCE_UPDATE)`, `get_db`
- `DELETE /resources/{resource_id}` :: `delete_resource` :: deps `requires_permission(PERM_DOC_RESOURCE_DELETE)`, `get_db`
- `GET /resources/{resource_id}/download` :: `download_resource` :: deps `optional_current_user`, `get_db`
- `POST /resources/{resource_id}/rate` :: `rate_resource` :: deps `requires_permission(PERM_DOC_RESOURCE_RATE)`, `get_db`
- `GET /resources/{resource_id}/rating` :: `get_resource_rating` :: deps `requires_permission(PERM_DOC_RESOURCE_READ)`, `get_db`

### `enrollments.py` (prefix `/enrollments`, 1 endpoint)

- `POST /enrollments` :: `create_enrollment` :: deps `requires_permission('PERM-ERP:enrollment:assign')`, `get_db`

### `events.py` (prefix `/`, 15 endpoints)

- `GET /events` :: `list_events` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `GET /calendar/holidays` :: `list_holidays` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `POST /calendar/holidays` :: `create_holiday` :: deps `requires_permission(PERM_CAL_HOLIDAY_MANAGE)`, `get_db`
- `PUT /calendar/holidays/{holiday_id}` :: `update_holiday` :: deps `requires_permission(PERM_CAL_HOLIDAY_MANAGE)`, `get_db`
- `DELETE /calendar/holidays/{holiday_id}` :: `delete_holiday` :: deps `requires_permission(PERM_CAL_HOLIDAY_MANAGE)`, `get_db`
- `POST /events` :: `create_event` :: deps `requires_permission(PERM_CAL_EVENT_CREATE)`, `get_db`
- `GET /events/{event_id}` :: `get_event` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `PUT /events/{event_id}` :: `update_event` :: deps `requires_permission(PERM_CAL_EVENT_UPDATE)`, `get_db`
- `DELETE /events/{event_id}` :: `delete_event` :: deps `requires_permission(PERM_CAL_EVENT_DELETE)`, `get_db`
- `POST /events/{event_id}/rsvp` :: `respond_to_event` :: deps `requires_permission(PERM_CAL_RSVP_RESPOND)`, `get_db`
- `GET /events/{event_id}/rsvp` :: `get_own_rsvp` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `GET /events/{event_id}/rsvps` :: `list_event_rsvps` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `POST /events/reminder-preferences` :: `update_reminder_preferences` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `GET /calendar/options` :: `calendar_options` :: deps `requires_permission(PERM_CAL_EVENT_READ)`, `get_db`
- `GET /calendar/ical` :: `calendar_ical_feed` :: deps `get_db`

### `exports.py` (prefix `/export`, 2 endpoints)

- `GET /export/csv` :: `export_csv` :: deps `requires_permission(PERM_REP_EXPORT_CREATE)`, `get_db`
- `GET /export/xlsx` :: `export_xlsx` :: deps `requires_permission(PERM_REP_EXPORT_CREATE)`, `get_db`

### `features.py` (prefix `/features`, 6 endpoints)

- `GET /features/active` :: `get_active_features_for_user` :: deps `get_current_user`, `get_db`
- `POST /features` :: `create_feature_toggle` :: deps `requires_permission(PERM_SYS_FEATURE_MANAGE)`, `get_db`
- `GET /features` :: `list_feature_toggles` :: deps `requires_permission(PERM_SYS_FEATURE_MANAGE)`, `get_db`
- `GET /features/{toggle_id}` :: `get_feature_toggle` :: deps `requires_permission(PERM_SYS_FEATURE_MANAGE)`, `get_db`
- `PUT /features/{toggle_id}` :: `update_feature_toggle` :: deps `requires_permission(PERM_SYS_FEATURE_MANAGE)`, `get_db`
- `DELETE /features/{toggle_id}` :: `delete_feature_toggle` :: deps `requires_permission(PERM_SYS_FEATURE_MANAGE)`, `get_db`

### `feed.py` (prefix `/feed`, 1 endpoint)

- `GET /feed` :: `list_feed` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission(PERM_COM_NOTIFICATION_READ)`, `get_db`

### `gdpr.py` (prefix `/users`, 3 endpoints)

- `GET /users/{user_id}/data-export` :: `data_export` :: deps `requires_permission(PERM_IAM_SESSION_LIST)`, `get_db`
- `POST /users/{user_id}/data-deletion` :: `data_deletion` :: deps `requires_permission(PERM_GDPR_DATA_DELETE)`, `get_db`
- `GET /users/{user_id}/consent-log` :: `consent_log` :: deps `requires_permission(PERM_IAM_SESSION_LIST)`, `get_db`

### `gradebook.py` (prefix `/gradebook`, 5 endpoints)

- `POST /gradebook/categories` :: `set_grade_categories` :: deps `get_current_user`, `get_db`
- `GET /gradebook/categories/{class_id}/{period_id}` :: `list_grade_categories` :: deps `get_current_user`, `get_db`
- `POST /gradebook/compute/{class_id}/{period_id}` :: `compute_class_averages` :: deps `get_current_user`, `get_db`
- `GET /gradebook/transcript/{student_id}` :: `get_student_transcript` :: deps `get_current_user`, `get_db`
- `GET /gradebook/{class_id}/{period_id}` :: `get_gradebook` :: deps `get_current_user`, `get_db`

### `invitations.py` (prefix `/invites`, 3 endpoints)

- `POST /invites/create` :: `create_invite` :: deps `requires_permission('PERM-IAM:invite:create')`, `get_db`, `get_redis`
- `POST /invites/consume` :: `consume_invite` :: deps `requires_permission('PERM-IAM:invite:consume')`, `get_db`, `get_redis`
- `POST /invites/revoke` :: `revoke_invite` :: deps `requires_permission('PERM-IAM:invite:revoke')`, `get_db`, `get_redis`

### `invoices.py` (prefix `/invoices`, 2 endpoints)

- `GET /invoices` :: `list_invoices` :: deps `parse_filters`, `parse_sort`, `parse_search`, `requires_permission('PERM-BIL:invoice:read')`, `get_db`
- `GET /invoices/{invoice_id}` :: `get_invoice` :: deps `requires_permission('PERM-BIL:invoice:read')`, `get_db`

### `messaging.py` (prefix `/messages`, 7 endpoints)

- `POST /messages/conversations` :: `create_conversation` :: deps `requires_any_permission(PERM_COM_CONVERSATION_CREATE, PERM_COM_STD_MESSAGE_SEND)`, `get_db`
- `GET /messages/conversations` :: `list_conversations` :: deps `requires_any_permission(PERM_COM_CONVERSATION_READ, PERM_COM_STD_MESSAGE_READ)`, `get_db`
- `GET /messages/search` :: `search_messages` :: deps `requires_any_permission(PERM_COM_CONVERSATION_READ, PERM_COM_STD_MESSAGE_READ)`, `get_db`
- `GET /messages/conversations/{conversation_id}/messages` :: `list_messages` :: deps `requires_any_permission(PERM_COM_CONVERSATION_READ, PERM_COM_STD_MESSAGE_READ)`, `get_db`
- `POST /messages/conversations/{conversation_id}/messages` :: `send_message` :: deps `requires_any_permission(PERM_COM_MESSAGE_SEND, PERM_COM_STD_MESSAGE_SEND)`, `get_db`
- `POST /messages/conversations/{conversation_id}/read` :: `mark_read` :: deps `requires_any_permission(PERM_COM_CONVERSATION_READ, PERM_COM_STD_MESSAGE_READ)`, `get_db`
- `GET /messages/conversations/{conversation_id}/read-status` :: `get_read_status` :: deps `requires_any_permission(PERM_COM_CONVERSATION_READ, PERM_COM_STD_MESSAGE_READ)`, `get_db`

### `notifications.py` (prefix `/notifications`, 13 endpoints)

- `GET /notifications` :: `list_notifications` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `GET /notifications/unread-count` :: `unread_count` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `GET /notifications/preferences` :: `get_preferences` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `POST /notifications/preferences` :: `post_preferences` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `PUT /notifications/preferences` :: `put_preferences` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `GET /notifications/digest/preferences` :: `get_digest_preferences` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `POST /notifications/digest/preferences` :: `update_digest_preferences` :: deps `get_current_user`, `get_db`
- `PATCH /notifications/mark-all-read` :: `mark_all_read` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `PATCH /notifications/{notification_id}/read` :: `mark_notification_read` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `POST /notifications/batch` :: `batch_notifications` :: deps `requires_permission('PERM-COM:notification:batch-create')`, `get_db`
- `DELETE /notifications/{notification_id}` :: `delete_notification` :: deps `requires_permission('PERM-COM:notification:read')`, `get_db`
- `GET /notifications/unsubscribe` :: `unsubscribe_notifications` :: deps `get_db`
- `GET /notifications/email-open` :: `track_email_open` :: deps `get_db`

### `payments.py` (prefix `/payments`, 3 endpoints)

- `POST /payments/initiate` :: `initiate_payment` :: deps `requires_permission('PERM-BIL:payment:initiate')`, `get_db`
- `GET /payments/{attempt_id}` :: `get_payment_status` :: deps `requires_permission('PERM-BIL:payment:read')`, `get_db`
- `POST /payments/webhook/provider` :: `handle_provider_webhook` :: deps `requires_permission('PERM-BIL:payment:reconcile')`, `get_db`

### `profiles.py` (prefix `/`, 4 endpoints)

- `GET /me/profile` :: `get_my_profile` :: deps `get_current_user`, `get_db`
- `PUT /me/profile` :: `update_my_profile` :: deps `get_current_user`, `get_db`
- `GET /admin/users/{user_id}/profile` :: `admin_get_user_profile` :: deps `requires_permission(PERM_PROF_ADMIN_READ)`, `get_db`
- `GET /me/children` :: `get_my_children` :: deps `requires_permission(PERM_PROF_CHILD_READ)`, `get_db`

### `progress.py` (prefix `/progress`, 4 endpoints)

- `GET /progress/student/{student_id}` :: `get_student_progress` :: deps `requires_permission(PERM_PROGRESS_READ)`, `get_db`
- `GET /progress/class/{class_id}` :: `get_class_progress` :: deps `requires_permission(PERM_PROGRESS_CLASS_READ)`, `get_db`
- `GET /progress/me` :: `get_my_progress` :: deps `requires_permission(PERM_PROGRESS_READ)`, `get_db`
- `GET /progress/children` :: `get_children_progress` :: deps `requires_permission(PERM_PROGRESS_READ)`, `get_db`

### `question_bank.py` (prefix `/`, 5 endpoints)

- `POST /question-bank` :: `add_question` :: deps `requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)`, `get_db`
- `GET /question-bank` :: `list_questions` :: deps `requires_permission(PERM_LMS_QUESTION_BANK_READ)`, `get_db`
- `POST /question-bank/import/{quiz_id}` :: `import_from_quiz` :: deps `requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)`, `get_db`
- `POST /question-bank/generate-quiz` :: `generate_quiz_from_bank` :: deps `requires_permission(PERM_LMS_QUESTION_BANK_MANAGE)`, `get_db`
- `GET /question-bank/stats` :: `get_question_stats` :: deps `requires_permission(PERM_LMS_QUESTION_BANK_READ)`, `get_db`

### `quizzes.py` (prefix `/`, 10 endpoints)

- `POST /quizzes` :: `create_quiz` :: deps `requires_permission(PERM_QUIZ_CREATE)`, `get_db`
- `GET /quizzes` :: `list_quizzes` :: deps `requires_permission(PERM_QUIZ_READ)`, `get_db`
- `GET /quizzes/{quiz_id}` :: `get_quiz` :: deps `requires_permission(PERM_QUIZ_READ)`, `get_db`
- `PUT /quizzes/{quiz_id}` :: `update_quiz` :: deps `requires_permission(PERM_QUIZ_MANAGE)`, `get_db`
- `POST /quizzes/{quiz_id}/publish` :: `publish_quiz` :: deps `requires_permission(PERM_QUIZ_PUBLISH)`, `get_db`
- `POST /quizzes/{quiz_id}/start` :: `start_attempt` :: deps `requires_permission(PERM_QUIZ_ATTEMPT)`, `get_db`
- `POST /attempts/{attempt_id}/respond` :: `respond_to_question` :: deps `requires_permission(PERM_QUIZ_ATTEMPT)`, `get_db`
- `POST /attempts/{attempt_id}/submit` :: `submit_attempt` :: deps `requires_permission(PERM_QUIZ_ATTEMPT)`, `get_db`
- `GET /attempts/{attempt_id}/results` :: `get_attempt_results` :: deps `requires_permission(PERM_QUIZ_READ)`, `get_db`
- `GET /quizzes/{quiz_id}/analytics` :: `quiz_analytics` :: deps `requires_permission(PERM_QUIZ_ANALYTICS)`, `get_db`

### `recovery.py` (prefix `/recovery`, 3 endpoints)

- `POST /recovery/request` :: `request_recovery` :: deps `get_db`, `get_redis`
- `POST /recovery/verify` :: `verify_recovery` :: deps `get_db`, `get_redis`
- `POST /recovery/reset` :: `reset_password` :: deps `get_db`, `get_redis`

### `reports.py` (prefix `/reports`, 10 endpoints)

- `POST /reports/generate` :: `generate_report` :: deps `requires_permission(PERM_REP_REPORT_GENERATE)`, `get_db`
- `GET /reports` :: `list_reports` :: deps `requires_permission(PERM_REP_REPORT_READ)`, `get_db`
- `GET /reports/options` :: `get_report_options` :: deps `requires_permission(PERM_REP_REPORT_GENERATE)`, `get_db`
- `POST /reports/schedules` :: `create_report_schedule` :: deps `requires_permission(PERM_RPT_SCHEDULE_MANAGE)`, `get_db`
- `GET /reports/schedules` :: `list_report_schedules` :: deps `requires_permission(PERM_RPT_SCHEDULE_MANAGE)`, `get_db`
- `PUT /reports/schedules/{schedule_id}` :: `update_report_schedule` :: deps `requires_permission(PERM_RPT_SCHEDULE_MANAGE)`, `get_db`
- `DELETE /reports/schedules/{schedule_id}` :: `disable_report_schedule` :: deps `requires_permission(PERM_RPT_SCHEDULE_MANAGE)`, `get_db`
- `POST /reports/schedules/{schedule_id}/run` :: `run_report_schedule` :: deps `requires_permission(PERM_RPT_SCHEDULE_MANAGE)`, `get_db`
- `GET /reports/{job_id}/status` :: `get_report_status` :: deps `requires_permission(PERM_REP_REPORT_READ)`, `get_db`
- `GET /reports/{job_id}/download` :: `download_report` :: deps `optional_current_user`, `get_db`

### `results.py` (prefix `/results`, 1 endpoint)

- `GET /results` :: `list_results` :: deps `requires_permission(PERM_LMS_RESULT_READ)`, `get_db`

### `router.py` (prefix `/`, 1 endpoint)

- `GET /health` :: `health_check` :: deps none

### `rubrics.py` (prefix `/`, 6 endpoints)

- `POST /rubrics` :: `create_rubric` :: deps `requires_permission(PERM_LMS_RUBRIC_CREATE)`, `get_db`
- `GET /rubrics` :: `list_rubrics` :: deps `requires_permission(PERM_LMS_RUBRIC_READ)`, `get_db`
- `GET /rubrics/{rubric_id}` :: `get_rubric` :: deps `requires_permission(PERM_LMS_RUBRIC_READ)`, `get_db`
- `POST /rubrics/{rubric_id}/duplicate` :: `duplicate_rubric` :: deps `requires_permission(PERM_LMS_RUBRIC_CREATE)`, `get_db`
- `POST /submissions/{submission_id}/grade-rubric` :: `grade_submission_with_rubric` :: deps `requires_permission(PERM_LMS_SUBMISSION_GRADE)`, `get_db`
- `GET /submissions/{submission_id}/rubric-results` :: `get_rubric_results` :: deps `get_current_user`, `get_db`

### `schools.py` (prefix `/schools`, 5 endpoints)

- `POST /schools` :: `create_school` :: deps `requires_role(SUP)`, `get_db`
- `GET /schools` :: `list_schools` :: deps `requires_permission(PERM_ADM_SCHOOL_READ)`, `get_db`
- `GET /schools/{school_id}` :: `get_school` :: deps `requires_permission(PERM_ADM_SCHOOL_READ)`, `get_db`
- `PATCH /schools/{school_id}` :: `update_school` :: deps `requires_permission(PERM_ADM_SCHOOL_MANAGE)`, `get_db`
- `DELETE /schools/{school_id}` :: `delete_school` :: deps `requires_role(SUP)`, `get_db`

### `submissions.py` (prefix `/submissions`, 7 endpoints)

- `POST /submissions` :: `create_submission` :: deps `requires_permission(PERM_LMS_SUBMISSION_CREATE)`, `get_db`
- `POST /submissions/{submission_id}/grade` :: `grade_submission` :: deps `requires_permission(PERM_LMS_SUBMISSION_GRADE)`, `get_db`
- `POST /submissions/{submission_id}/override-penalty` :: `override_late_penalty` :: deps `requires_permission(PERM_LMS_SUBMISSION_GRADE)`, `get_db`
- `POST /submissions/{submission_id}/files` :: `upload_submission_file` :: deps `requires_permission(PERM_LMS_SUBMISSION_FILE_UPLOAD)`, `get_db`
- `GET /submissions/{submission_id}/files/{file_id}` :: `download_submission_file` :: deps `requires_permission(PERM_LMS_SUBMISSION_FILE_READ)`, `get_db`
- `POST /submissions/{submission_id}/submit` :: `finalize_submission` :: deps `requires_permission(PERM_LMS_SUBMISSION_CREATE)`, `get_db`
- `GET /submissions/{submission_id}/preview` :: `preview_submission_files` :: deps `requires_permission(PERM_LMS_SUBMISSION_GRADE)`, `get_db`

### `teacher.py` (prefix `/teacher`, 4 endpoints)

- `GET /teacher/classes` :: `list_teacher_classes` :: deps `requires_permission(PERM_ERP_CLASS_READ)`, `get_db`
- `GET /teacher/classes/{class_id}/students` :: `list_class_students` :: deps `requires_permission(PERM_ERP_CLASS_READ)`, `get_db`
- `GET /teacher/submissions` :: `list_teacher_submissions` :: deps `requires_permission(PERM_LMS_SUBMISSION_GRADE)`, `get_db`
- `GET /teacher/periods` :: `list_active_periods` :: deps `requires_permission(PERM_ERP_CLASS_READ)`, `get_db`

### `timetable.py` (prefix `/timetable`, 9 endpoints)

- `POST /timetable/slots` :: `create_timetable_slots` :: deps `requires_permission('PERM-ERP:timetable:create')`, `get_db`
- `GET /timetable/slots` :: `list_timetable_slots` :: deps `requires_permission('PERM-ERP:timetable:read')`, `get_db`
- `PUT /timetable/slots/{slot_id}` :: `update_timetable_slot` :: deps `requires_permission('PERM-ERP:timetable:update')`, `get_db`
- `DELETE /timetable/slots/{slot_id}` :: `delete_timetable_slot` :: deps `requires_permission('PERM-ERP:timetable:delete')`, `get_db`
- `GET /timetable/class/{class_id}/weekly` :: `get_class_weekly_timetable` :: deps `requires_permission('PERM-ERP:timetable:read')`, `get_db`
- `GET /timetable/teacher/{teacher_id}/weekly` :: `get_teacher_weekly_timetable` :: deps `requires_permission('PERM-ERP:timetable:read')`, `get_db`
- `GET /timetable/me/weekly` :: `get_my_weekly_timetable` :: deps `get_current_user`, `get_db`
- `POST /timetable/exceptions` :: `create_timetable_exception` :: deps `requires_permission('PERM-ERP:timetable-exception:create')`, `get_db`
- `GET /timetable/exceptions` :: `list_timetable_exceptions` :: deps `requires_permission('PERM-ERP:timetable-exception:read')`, `get_db`

### `timetable_generation.py` (prefix `/timetable`, 6 endpoints)

- `POST /timetable/constraints` :: `set_timetable_constraints` :: deps `requires_permission('PERM-ERP:timetable-constraint:manage')`, `get_db`
- `GET /timetable/constraints` :: `list_timetable_constraints` :: deps `requires_permission('PERM-ERP:timetable-constraint:manage')`, `get_db`
- `POST /timetable/generate` :: `generate_timetable` :: deps `requires_permission('PERM-ERP:timetable:generate')`, `get_db`
- `GET /timetable/generate/{job_id}` :: `get_timetable_generation_job` :: deps `requires_permission('PERM-ERP:timetable:generate')`, `get_db`
- `GET /timetable/generate/{job_id}/preview` :: `preview_generated_timetable` :: deps `requires_permission('PERM-ERP:timetable:generate')`, `get_db`
- `POST /timetable/generate/{job_id}/apply` :: `apply_generated_timetable` :: deps `requires_permission('PERM-ERP:timetable:generate')`, `get_db`

### `ws.py` (prefix `/`, 1 endpoint)

- `WEBSOCKET /ws` :: `websocket_endpoint`
