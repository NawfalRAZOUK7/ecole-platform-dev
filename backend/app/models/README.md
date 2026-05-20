<!-- markdownlint-disable MD036 -->

# models/ — SQLAlchemy 2.0 ORM Models

Object-relational mapping (ORM) layer using SQLAlchemy 2.0 with modern `Mapped[]` type annotations. Models define database schema and relationships.

## Packaging roadmap (hybrid "A3")

Today, modules are **flat files** (`lms.py`, `erp.py`, …) while routers/services/schemas are already grouped by **bounded context** (same names as `api/v1/`).

| Phase     | Action                                                                                                                                                                               |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Now**   | Keep flat layout; treat this README + [`docs/DATABASE.md`](../../docs/DATABASE.md) as the logical map (G1–G9+ style groupings).                                                      |
| **Next**  | When a domain is heavily touched, introduce a **subpackage** (e.g. `models/lms/`) and re-export from `models/__init__.py` in a **dedicated PR** with a codemod (no behavior change). |
| **Avoid** | Big-bang move of all models in one PR (merge pain, Alembic autogenerate noise).                                                                                                      |

**Rename / split (only when justified)**  
Split oversized files (e.g. many unrelated tables in one module) only together with a clear migration story. Prefer **documentation** of legacy names (`com.py` = communication) over mass file renames that do not change tables.

## Directory Structure

```text
models/
├── iam.py                    # Identity & Access Management (G1)
├── school.py                 # School entity (G2)
├── erp.py                    # ERP — Academic years, classes, enrollments, attendance, timetable, programs (G2/G7)
├── lms.py                    # Learning Management System — courses, assignments, quizzes, content (G3)
├── com.py                    # Communication — notifications, messaging, announcements, feed (G4)
├── billing.py                # Billing, invoices, payments, fee structures (G5)
├── budget.py                 # Class micro-budgets (G5)
├── financial_health.py       # Retention, cashflow, cost-per-student (G5)
├── calendar.py               # Calendar events, RSVP, reminders (G4)
├── documents.py              # Document management with versioning (G9)
├── uploads.py                # Upload session tracking (G9)
├── sync_queue.py             # Offline sync devices, queue, conflicts (G9)
├── audit.py                  # Audit logging (G6)
├── ai.py                     # AI writing attempts, preferences (G6)
├── reporting.py              # Report jobs, schedules, exports (G8)
├── men_compliance.py         # MEN curriculum mapping & compliance (G8)
├── games.py                  # Mobile game configurations (G6)
├── rewards.py                # Student rewards, badges, XP (G6)
├── skill_passport.py         # Life-skills dimensions & milestones (G6)
├── micro_school.py           # Micro-schools & informal education (G6)
├── feature.py                # Feature toggles (G6)
├── levels.py                 # Level-age mappings (G46)
├── difficulty_adaptation.py  # Difficulty change audit log
└── reporting.py              # Report jobs, schedules, data exports
```

## ORM Patterns

All models use SQLAlchemy 2.0 features:

- **Mapped[]** for type-safe columns
- **Declarative base** for inheritance (`Base`, `SchoolScopedMixin`, `TimestampMixin`, `SoftDeleteMixin`, `NullableSchoolScopedMixin`)
- **Async support** via asyncpg driver
- **Relationships** with lazy loading strategies
- **Enums** using PostgreSQL `ENUM` type with `create_type=False`
- **CheckConstraints** and **UniqueConstraints** for data integrity

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, SchoolScopedMixin, TimestampMixin

class Course(TimestampMixin, SchoolScopedMixin, Base):
    __tablename__ = "courses"

    class_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)

    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
```

## Models by Domain

### G1 — IAM (`iam.py`)

Identity, access control, authentication, and security monitoring.

| Model                    | Description                                                                                                         |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `User`                   | Platform user (one row per person). Email uniqueness scoped per school. Supports TOTP, SMS 2FA, email verification. |
| `Membership`             | Links a user to a school with a role code (ADM, DIR, TCH, EDUCATOR, PAR, STD, SUP, SYS, CONTENT_MGR).               |
| `Session`                | JWT refresh session with revocation, impersonation, device fingerprint.                                             |
| `LoginHistory`           | Historical login attempts with geo/device info.                                                                     |
| `InvitationCode`         | One-time onboarding codes with role targeting and expiration.                                                       |
| `AccountRecoveryRequest` | Password reset flow with OTP and attempt tracking.                                                                  |
| `ParentChildLink`        | Explicit parent-student relationship for ABAC ownership guards.                                                     |
| `StudentProfile`         | Extended student data (student_number, DOB, gender, class_level).                                                   |
| `ParentProfile`          | Extended parent data (CIN, address, profession, emergency_phone).                                                   |
| `TeacherProfile`         | Extended teacher data (employee_id, subject_specialty, qualification, hire_date).                                   |
| `AdminProfile`           | Extended admin data (department, management_level, can_approve_budgets).                                            |
| `ContentManagerProfile`  | Extended CONTENT_MGR data (specialization, languages, approved_subjects).                                           |
| `WebAuthnCredential`     | Passkey credentials for passwordless authentication.                                                                |
| `OAuthAccount`           | Social login linkage (Google, Microsoft, Apple).                                                                    |
| `PasswordHistory`        | Prevents password reuse.                                                                                            |
| `FailedLoginAttempt`     | Tracks failed logins for account lockout.                                                                           |
| `KnownLocation`          | Known login locations for suspicious activity detection.                                                            |
| `KnownDevice`            | Known devices for suspicious activity detection.                                                                    |

**Key Enums**: `UserStatus`, `RoleCode` (9 roles), `MembershipStatus`, `RecoveryStatus`, `LinkStatus`, `Gender`, `RelationshipType`

### G2 — ERP (`school.py`, `erp.py`)

School operations, academic structure, attendance, and timetables.

| Model                    | Description                                                                   |
| ------------------------ | ----------------------------------------------------------------------------- |
| `School`                 | Tenant root. Banking details (RIB, IBAN, BIC), TVA fields, branding for PDFs. |
| `AcademicYear`           | School calendar boundaries with date validation.                              |
| `Period`                 | Semester/trimester within an academic year.                                   |
| `Class`                  | School class (e.g., 3eme A). Unique per (code, school, academic_year).        |
| `Enrollment`             | Student enrollment in a class for a period. Optional program_id (G49).        |
| `TeacherAssignment`      | Teacher assigned to a class for a period.                                     |
| `AttendanceSession`      | One attendance session per class/date/slot.                                   |
| `AttendanceRecord`       | Individual student attendance within a session.                               |
| `AbsenceJustification`   | Parent-submitted absence justification with attachments.                      |
| `JustificationReview`    | Teacher/admin review decision on a justification.                             |
| `AttendanceAlert`        | Threshold-based attendance alerts.                                            |
| `TimetableConstraint`    | Constraints for timetable generation.                                         |
| `TimetableGenerationJob` | Stored result of a timetable generation run.                                  |
| `TimetableSlot`          | Recurring weekly class period.                                                |
| `TimetableException`     | Cancellation, substitution, or room change for a slot.                        |

### G7 — Academic Programs (`erp.py`)

Program management, equivalences, snapshots, and eligibility.

| Model                    | Description                                                    |
| ------------------------ | -------------------------------------------------------------- |
| `Program`                | Academic program / filière (e.g., Sciences Maths).             |
| `ProgramVersion`         | Specific curriculum version of a program.                      |
| `ProgramAssignmentEvent` | Append-only audit log of student program changes.              |
| `ProgramEquivalence`     | Declared equivalence between two programs.                     |
| `AcademicSnapshot`       | Frozen JSONB document capturing student academic state.        |
| `EligibilityRule`        | Declarative rule for promotion/admission/transfer eligibility. |

### G3 — LMS (`lms.py`)

Learning management, content, quizzes, assignments, and grading.

| Model                                                        | Description                                                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| `Course`                                                     | Teacher-created course within a class.                                                            |
| `Assignment`                                                 | Teacher-created work for students.                                                                |
| `Submission`                                                 | Student submission for an assignment.                                                             |
| `SubmissionFile`                                             | File attachment on a submission.                                                                  |
| `Grade`                                                      | Teacher grade for a submission.                                                                   |
| `GradeCategory`                                              | Weighted grade category for a class and period.                                                   |
| `StudentPeriodAverage`                                       | Cached weighted average per student, class, and period.                                           |
| `Assessment` / `AssessmentResult`                            | Formal exam/quiz and student results.                                                             |
| `Rubric` / `RubricCriterion` / `RubricLevel` / `RubricScore` | Structured grading rubrics with criterion-level scoring.                                          |
| `ContentItem`                                                | Educational content (video, document, interactive). Nullable school_id for platform-wide content. |
| `ContentItemAsset`                                           | File/media asset attached to a content item.                                                      |
| `ContentProgress`                                            | Student progress tracking for a content item.                                                     |
| `ContentSubmission`                                          | School-scoped content submitted for platform promotion review.                                    |
| `ClassContentAssignment`                                     | Teacher assigns content to a class.                                                               |
| `Activity` / `ActivitySession`                               | Pedagogical activities and student sessions.                                                      |
| `Quiz` / `QuizQuestion` / `QuizAttempt` / `QuizResponse`     | Quiz engine with 5 question types.                                                                |
| `QuestionBankItem`                                           | Reusable school question bank for quiz generation.                                                |

### G5 — Billing (`billing.py`)

Invoices, payments, fee structures, and policies.

| Model                             | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| `Invoice` / `InvoiceItem`         | Invoices with TVA breakdown and line items.                 |
| `PaymentAttempt` / `PaymentProof` | Payment attempts and proof of payment.                      |
| `ProviderWebhookEvent`            | Idempotent webhook events from payment providers.           |
| `FeeStructure` / `FeeAssignment`  | Recurring/one-time fee definitions and student assignments. |
| `SiblingDiscountPolicy`           | School-level sibling discount tiers.                        |
| `LateFeePolicy`                   | Overdue invoice late-fee rules.                             |
| `PaymentPlan` / `Installment`     | Installment plans for invoices.                             |

### G5 — Budget (`budget.py`)

Class micro-budget decentralized spending.

| Model               | Description                                  |
| ------------------- | -------------------------------------------- |
| `MicroBudget`       | School budget envelope for an academic year. |
| `BudgetAllocation`  | Allocation of budget to a class/department.  |
| `BudgetRequest`     | Spending request with approval workflow.     |
| `BudgetTransaction` | Recorded transaction against an allocation.  |

### G5 — Financial Health (`financial_health.py`)

| Model                  | Description                              |
| ---------------------- | ---------------------------------------- |
| `RetentionMetric`      | Year-over-year student retention.        |
| `CashflowForecast`     | Projected monthly cashflow.              |
| `FinancialSnapshot`    | Point-in-time financial health snapshot. |
| `CostPerStudentMetric` | Computed cost per student.               |

### G4 — Communication (`com.py`)

Notifications, messaging, announcements, and parent feed.

| Model                                                                         | Description                                            |
| ----------------------------------------------------------------------------- | ------------------------------------------------------ |
| `ConsentPreference`                                                           | Per-user notification consent by topic/channel.        |
| `Notification`                                                                | Platform-generated notifications with idempotency key. |
| `NotificationPreference`                                                      | Per-user channel/category preferences.                 |
| `DeviceToken`                                                                 | Mobile/web push tokens.                                |
| `NotificationDelivery`                                                        | Per-channel delivery attempts.                         |
| `ParentFeedItem`                                                              | Aggregated parent activity feed items.                 |
| `Conversation` / `ConversationParticipant` / `Message` / `MessageReadReceipt` | Direct and group messaging.                            |
| `Announcement`                                                                | School-wide or targeted announcements.                 |
| `SharedReviewComment`                                                         | Parent comments on child learning sessions.            |

### G4 — Calendar (`calendar.py`)

| Model           | Description                                       |
| --------------- | ------------------------------------------------- |
| `Event`         | Calendar events with RSVP, reminders, recurrence. |
| `EventRSVP`     | Per-user RSVP state.                              |
| `EventReminder` | Scheduled reminder dispatches.                    |

### G6 — Gamification (`games.py`, `rewards.py`)

| Model           | Description                                              |
| --------------- | -------------------------------------------------------- |
| `GameConfig`    | Mobile game configuration (memory, sorting, vocabulary). |
| `RewardBadge`   | Badge definitions with trilingual titles.                |
| `StudentReward` | Aggregate rewards state (stars, XP, level, streak).      |
| `RewardEvent`   | Immutable record of awarded rewards.                     |

### G6 — Skill Passport (`skill_passport.py`)

| Model            | Description                                       |
| ---------------- | ------------------------------------------------- |
| `SkillDimension` | Top-level behavioral skill (e.g., collaboration). |
| `SkillMilestone` | Rule-driven milestone within a dimension.         |
| `SkillProgress`  | Student progress on a milestone.                  |

### G6 — Micro-Schools (`micro_school.py`)

| Model             | Description                                   |
| ----------------- | --------------------------------------------- |
| `MicroSchool`     | Informal education unit owned by an educator. |
| `MicroGroup`      | Learning group within a micro-school.         |
| `MicroEnrollment` | Child enrollment in a micro-group.            |
| `MicroPayment`    | Parent payment for micro-school attendance.   |
| `MicroResource`   | Shared content resources.                     |

### G8 — Compliance & Reporting (`men_compliance.py`, `reporting.py`)

| Model                            | Description                                              |
| -------------------------------- | -------------------------------------------------------- |
| `MenCurriculum` / `MenObjective` | MEN curriculum reference with objectives.                |
| `CurriculumMapping`              | School course mapping to MEN objectives.                 |
| `ComplianceReport`               | Generated compliance coverage report.                    |
| `ReportSchedule`                 | Scheduled report generation with role-targeted delivery. |
| `ReportJob`                      | Asynchronous PDF report generation job.                  |
| `DataExport`                     | CSV/XLSX export audit log.                               |

### G9 — Storage & Sync (`documents.py`, `uploads.py`, `sync_queue.py`)

| Model                                           | Description                                                |
| ----------------------------------------------- | ---------------------------------------------------------- |
| `Document`                                      | Uploaded binary asset with SHA-256 and virus scan status.  |
| `DocumentVersion`                               | Historical version snapshot for a document.                |
| `UploadSession`                                 | Direct-to-MinIO upload lifecycle (init → complete → scan). |
| `SyncDevice`                                    | Offline-capable device registration.                       |
| `SyncQueue` / `SyncCheckpoint` / `SyncConflict` | Offline sync queue, checkpoints, and conflict resolution.  |

### G6 — Feature Toggles (`feature.py`)

| Model           | Description                                       |
| --------------- | ------------------------------------------------- |
| `FeatureToggle` | Gradual feature rollout with school/role scoping. |

### Cross-Cutting (`ai.py`, `audit.py`, `levels.py`, `difficulty_adaptation.py`)

| Model                  | Description                                                                 |
| ---------------------- | --------------------------------------------------------------------------- |
| `WritingAttempt`       | Student writing assistance with AI response.                                |
| `AIPreference`         | AI personalization opt-out (parent on behalf of child).                     |
| `AuditLog`             | Append-only security-relevant event log.                                    |
| `LevelAgeMapping`      | Academic level to default age range (platform defaults + school overrides). |
| `DifficultyAdaptation` | Rule-based difficulty change audit log.                                     |

## Relationships Overview

Core relationship patterns (actual FKs in code):

```
User (1) ──────► Membership (n)  [per school/role]
User (1) ──────► Session (n)
User (1) ──────► LoginHistory (n)
User (1) ──────► StudentProfile / ParentProfile / TeacherProfile / AdminProfile / ContentManagerProfile
User (1) ──────► OAuthAccount (n)
User (1) ──────► WebAuthnCredential (n)

School (1) ──────► AcademicYear (n)
School (1) ──────► Class (n)
School (1) ──────► MicroBudget (n)
School (1) ──────► Invoice (n)
School (1) ──────► Event (n)
School (1) ──────► Document (n)

AcademicYear (1) ──────► Period (n)
AcademicYear (1) ──────► Class (n)
AcademicYear (1) ──────► MicroBudget (n)

Class (1) ──────► Enrollment (n)
Class (1) ──────► Course (n)
Class (1) ──────► GradeCategory (n)

Course (1) ──────► Assignment (n)
Course (1) ──────► ClassContentAssignment (n)

Assignment (1) ──────► Submission (n)
Assignment (1) ──────► Grade (n)

Student (1) ──────► StudentReward (1)
Student (1) ──────► SkillProgress (n)
Student (1) ──────► RewardEvent (n)

Parent (1) ──────► ParentChildLink (n) ──────► Student (1)
```

## Base Mixins

| Mixin                       | Provides                                    |
| --------------------------- | ------------------------------------------- |
| `TimestampMixin`            | `created_at`, `updated_at`                  |
| `SoftDeleteMixin`           | `deleted_at` (soft delete support)          |
| `SchoolScopedMixin`         | `school_id` FK with index                   |
| `NullableSchoolScopedMixin` | `school_id` nullable for platform-wide rows |

## Next Steps

- See `repositories/` for how models are queried
- See `schemas/` for Pydantic serialization models
- See `alembic/versions/` for schema migration history
- See `docs/DATABASE.md` for migration group authority and DDL flow
