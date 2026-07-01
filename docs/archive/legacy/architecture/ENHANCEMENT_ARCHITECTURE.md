# Enhancement Architecture — Ecole Platform

> Design specifications for all 15 feature enhancements.
> To be executed AFTER OOP refactor (Phases OOP-A through OOP-F).
> All enhancements follow the 3-tier pattern: Router → Service → Repository.

---

## Table of Contents

- [ENH-A: IAM Enhancements](#enh-a-iam-enhancements)
  - [A1: Admin Impersonation](#a1-admin-impersonation)
  - [A2: Login History + Suspicious Alerts](#a2-login-history)
  - [A3: Concurrent Session Limits](#a3-session-limits)
- [ENH-B: LMS Enhancements](#enh-b-lms-enhancements)
  - [B1: Rubric Engine](#b1-rubric-engine)
  - [B2: Weighted Gradebook + GPA](#b2-weighted-gradebook)
  - [B3: Question Bank](#b3-question-bank)
  - [B4: Late Submission Penalties](#b4-late-penalties)
- [ENH-C: Billing & ERP Enhancements](#enh-c-billing-erp)
  - [C1: Sibling Discount Logic](#c1-sibling-discounts)
  - [C2: Late Fees + Payment Plans](#c2-late-fees)
  - [C3: Attendance Analytics + Alerts](#c3-attendance-analytics)
  - [C4: Timetable Auto-Generation](#c4-timetable-autogen)
- [ENH-D: Communication & Docs Enhancements](#enh-d-comms-docs)
  - [D1: Message Attachments + Search](#d1-message-attachments)
  - [D2: Document Versioning](#d2-document-versioning)
  - [D3: Report Scheduling + Email Delivery](#d3-report-scheduling)
  - [D4: AI Provider Abstraction](#d4-ai-provider)
- [New Models Summary](#new-models-summary)
- [New Permissions Summary](#new-permissions-summary)
- [Migration Plan](#migration-plan)

---

## ENH-A: IAM Enhancements

### A1: Admin Impersonation

**Purpose:** Let ADM/DIR "login as" another user to debug issues they report.

**How it works:**
1. Admin calls `POST /admin/impersonate/{user_id}`.
2. System creates a shadow session with `impersonator_id` field set.
3. Admin gets a new access_token with the target user's role + permissions.
4. Every action during impersonation is audit-logged with `impersonator_id`.
5. Admin calls `POST /admin/stop-impersonation` to return to their own session.

**Model changes:**
```python
# Add to Session model (iam.py):
impersonator_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("users.id", ondelete="SET NULL"), nullable=True
)
```

**New service methods (auth.py):**
```python
async def impersonate(self, target_user_id: UUID, admin_auth: AuthContext) -> TokenPair:
    """Create shadow session as target user. Admin-only."""
    # Verify admin role (ADM/DIR/SUP)
    # Verify target user exists in same school
    # Cannot impersonate SUP/SYS roles
    # Create session with impersonator_id = admin_auth.user_id
    # Return access_token with target user's permissions
    # Audit: ADMIN_IMPERSONATION_START

async def stop_impersonation(self, session_id: UUID) -> TokenPair:
    """End impersonation, return to admin session."""
    # Verify current session has impersonator_id
    # Revoke shadow session
    # Return admin's original session tokens
    # Audit: ADMIN_IMPERSONATION_END
```

**New endpoints:**
- `POST /admin/impersonate/{user_id}` — PERM_ADM_USER_MANAGE
- `POST /admin/stop-impersonation` — any authenticated (checks impersonator_id)

**New permissions:**
- `PERM_ADM_IMPERSONATE` — start impersonation

**New audit events:**
- `ADMIN_IMPERSONATION_START`, `ADMIN_IMPERSONATION_END`

---

### A2: Login History + Suspicious Alerts

**Purpose:** Track all login attempts and alert on new devices.

**New model:**
```python
class LoginHistory(TimestampMixin, Base):
    __tablename__ = "login_history"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    device_name: Mapped[str | None] = mapped_column(String(200))
    device_fingerprint: Mapped[str | None] = mapped_column(String(64))  # SHA256 of user_agent+screen
    city: Mapped[str | None] = mapped_column(String(100))  # From IP geolocation (optional)
    country: Mapped[str | None] = mapped_column(String(50))
    success: Mapped[bool] = mapped_column(nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(String(50))  # wrong_password, rate_limited, etc.
    is_new_device: Mapped[bool] = mapped_column(nullable=False, default=False)

    __table_args__ = (
        Index("idx_login_history_user_created", "user_id", "created_at"),
        Index("idx_login_history_school", "school_id"),
    )
```

**Service logic:**
- On every login (success or failure), create LoginHistory row.
- Compute `device_fingerprint` = SHA256(user_agent + ip_address first 3 octets).
- Check if fingerprint exists in user's last 30 days of history.
- If new device: set `is_new_device = True`, emit `NewDeviceLogin` domain event.
- `NewDeviceLogin` event triggers email: "New device logged into your account."

**New endpoints:**
- `GET /auth/login-history` — list own login history (paginated, last 90 days)
- `GET /admin/users/{user_id}/login-history` — admin view of user's login history

**New permissions:**
- `PERM_IAM_LOGIN_HISTORY_READ`

---

### A3: Concurrent Session Limits

**Purpose:** Limit active sessions per user to prevent credential sharing.

**Configuration:**
```python
# Add to core/config.py:
MAX_SESSIONS_PER_USER: int = 5  # Default, can be overridden per school
```

**Service logic (auth.py login method):**
```python
# After successful authentication, before creating new session:
active_count = await self._repo.count_active_sessions(user_id, school_id)
if active_count >= settings.MAX_SESSIONS_PER_USER:
    # Revoke oldest session(s) to make room
    oldest = await self._repo.get_oldest_active_session(user_id, school_id)
    await self._repo.revoke_session(oldest.id)
    # Audit: AUTH_SESSION_LIMIT_REACHED
```

No new model needed — just service logic + config setting.

---

## ENH-B: LMS Enhancements

### B1: Rubric Engine

**Purpose:** Structured grading with weighted criteria.

**New models (add to lms.py or create models/rubric.py):**
```python
class Rubric(TimestampMixin, Base):
    __tablename__ = "rubrics"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)  # Reusable templates

    __table_args__ = (
        Index("idx_rubrics_school_teacher", "school_id", "teacher_id"),
    )


class RubricCriterion(TimestampMixin, Base):
    __tablename__ = "rubric_criteria"

    rubric_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)  # Relative weight
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Sort order

    __table_args__ = (
        Index("idx_rubric_criteria_rubric", "rubric_id"),
    )


class RubricLevel(TimestampMixin, Base):
    __tablename__ = "rubric_levels"

    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubric_criteria.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(100), nullable=False)  # "Excellent", "Good", etc.
    description: Mapped[str | None] = mapped_column(Text)  # "Zero errors in grammar"
    points: Mapped[float] = mapped_column(Float, nullable=False)  # Points for this level
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_rubric_levels_criterion", "criterion_id"),
    )


class RubricScore(TimestampMixin, Base):
    """Teacher's score on each criterion for a specific submission."""
    __tablename__ = "rubric_scores"

    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubric_criteria.id", ondelete="CASCADE"))
    level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("rubric_levels.id", ondelete="SET NULL"))
    points_awarded: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        UniqueConstraint("submission_id", "criterion_id", name="uq_rubric_scores_sub_criterion"),
        Index("idx_rubric_scores_submission", "submission_id"),
    )
```

**Link to Assignment:**
```python
# Add to Assignment model:
rubric_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True
)
```

**Service: RubricService**
- `create_rubric(title, criteria_with_levels, teacher_id, school_id)`
- `get_rubric(rubric_id)` — full with criteria + levels
- `list_rubrics(school_id, teacher_id)` — teacher's rubrics + templates
- `duplicate_rubric(rubric_id)` — copy a template
- `grade_with_rubric(submission_id, scores: list[{criterion_id, level_id, points, comment}])`
  - Auto-calculates total = sum(points * weight) / sum(weights) * 20
  - Creates/updates Grade record with the total
  - Creates RubricScore records per criterion
- `get_rubric_results(submission_id)` — student view with per-criterion feedback

**New endpoints:**
- `POST /rubrics` — create rubric
- `GET /rubrics` — list rubrics
- `GET /rubrics/{id}` — get with criteria
- `POST /rubrics/{id}/duplicate` — copy template
- `POST /submissions/{id}/grade-rubric` — grade using rubric
- `GET /submissions/{id}/rubric-results` — student view

**New permissions:**
- `PERM_LMS_RUBRIC_CREATE`, `PERM_LMS_RUBRIC_READ`

---

### B2: Weighted Gradebook + GPA

**Purpose:** Category weights for semester averages, auto-calculated Moroccan mentions.

**New models:**
```python
class GradeCategory(TimestampMixin, Base):
    """Grade weight categories for a class (e.g., homework 20%, exams 50%)."""
    __tablename__ = "grade_categories"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("periods.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Devoirs", "Examens", etc.
    weight: Mapped[float] = mapped_column(Float, nullable=False)  # 0.20 = 20%
    position: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        Index("idx_grade_categories_class_period", "class_id", "period_id"),
        CheckConstraint("weight > 0 AND weight <= 1", name="ck_grade_categories_weight"),
    )


class StudentPeriodAverage(TimestampMixin, Base):
    """Cached computed average per student per period."""
    __tablename__ = "student_period_averages"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("periods.id", ondelete="CASCADE"))
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    weighted_average: Mapped[float] = mapped_column(Float, nullable=False)
    mention: Mapped[str] = mapped_column(String(30))  # "Très Bien", "Bien", etc.
    class_rank: Mapped[int | None] = mapped_column(Integer)
    total_students: Mapped[int | None] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("student_id", "class_id", "period_id", name="uq_spa_student_class_period"),
        Index("idx_spa_class_period", "class_id", "period_id"),
    )
```

**Link assignments to categories:**
```python
# Add to Assignment model:
grade_category_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("grade_categories.id", ondelete="SET NULL"), nullable=True
)
```

**Service: GradebookService**
- `set_grade_categories(class_id, period_id, categories: list[{name, weight}])`
  - Validates weights sum to 1.0
- `compute_student_average(student_id, class_id, period_id)` -> MoroccanGrade
  - Groups grades by category
  - Applies weights: sum(category_avg * weight)
  - Computes mention using MoroccanGrade.mention
- `compute_class_averages(class_id, period_id)` -> list
  - Computes all students, assigns ranks
  - Caches in StudentPeriodAverage
- `get_gradebook(class_id, period_id)` -> matrix
  - Returns students × assignments grid with averages
- `get_student_transcript(student_id, academic_year_id)` -> all periods

**New endpoints:**
- `POST /gradebook/categories` — set categories for class+period
- `GET /gradebook/categories/{class_id}/{period_id}` — get categories
- `POST /gradebook/compute/{class_id}/{period_id}` — trigger computation
- `GET /gradebook/{class_id}/{period_id}` — full gradebook matrix
- `GET /gradebook/transcript/{student_id}` — student transcript

**New permissions:**
- `PERM_LMS_GRADEBOOK_MANAGE`, `PERM_LMS_GRADEBOOK_READ`

---

### B3: Question Bank

**Purpose:** Reusable question library with random quiz generation.

**New models:**
```python
class QuestionBankItem(TimestampMixin, Base):
    __tablename__ = "question_bank_items"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str | None] = mapped_column(String(50))  # "3ème année", "Bac"
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)  # easy, medium, hard
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)  # MCQ, TRUE_FALSE, etc.
    question_data: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Same format as quiz questions
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(80)), default=list)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)  # How many quizzes used this
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        Index("idx_qb_school_subject", "school_id", "subject"),
        Index("idx_qb_school_difficulty", "school_id", "difficulty"),
        Index("idx_qb_teacher", "teacher_id"),
    )
```

**Service: QuestionBankService**
- `add_question(question_data, subject, level, difficulty, tags)`
- `list_questions(subject, level, difficulty, tags, search)` — paginated
- `import_from_quiz(quiz_id)` — save quiz questions to bank
- `generate_quiz_from_bank(subject, level, distribution: {easy: 5, medium: 3, hard: 2})` -> quiz draft
  - Randomly selects questions matching criteria
  - Creates quiz in DRAFT status with selected questions
  - Increments usage_count on each selected question
- `get_question_stats()` — usage analytics per subject/difficulty

**New endpoints:**
- `POST /question-bank` — add question
- `GET /question-bank` — list with filters
- `POST /question-bank/import/{quiz_id}` — import from quiz
- `POST /question-bank/generate-quiz` — generate quiz from bank
- `GET /question-bank/stats` — usage statistics

**New permissions:**
- `PERM_LMS_QUESTION_BANK_MANAGE`, `PERM_LMS_QUESTION_BANK_READ`

---

### B4: Late Submission Penalties

**Purpose:** Auto-penalty for late submissions.

**Model changes:**
```python
# Add to Assignment model:
grace_period_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
late_penalty_per_day: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # Points deducted per day
max_late_days: Mapped[int | None] = mapped_column(Integer)  # NULL = no limit
allow_late: Mapped[bool] = mapped_column(Boolean, default=True)
```

**Service logic (in AssignmentService.grade_submission):**
```python
# Calculate lateness
if submission.submitted_at and assignment.due_at:
    late_delta = submission.submitted_at - assignment.due_at
    grace = timedelta(hours=assignment.grace_period_hours)
    if late_delta > grace:
        late_days = math.ceil((late_delta - grace).total_seconds() / 86400)
        if assignment.max_late_days and late_days > assignment.max_late_days:
            # Reject: too late
            pass
        penalty = late_days * assignment.late_penalty_per_day
        adjusted_score = max(0, original_score - penalty)
        grade.late_penalty = penalty
        grade.late_days = late_days
        grade.original_score = original_score
        grade.score = adjusted_score
```

**Model changes to Grade:**
```python
# Add to Grade model:
original_score: Mapped[float | None] = mapped_column(Numeric(6, 2))
late_penalty: Mapped[float] = mapped_column(Float, default=0.0)
late_days: Mapped[int] = mapped_column(Integer, default=0)
penalty_overridden: Mapped[bool] = mapped_column(Boolean, default=False)
```

**New service method:**
- `override_late_penalty(submission_id, teacher_id)` — teacher removes penalty, restores original score

No new endpoints needed — existing grade/submission endpoints handle this. Add `override_late_penalty` to submissions router.

---

## ENH-C: Billing & ERP Enhancements

### C1: Sibling Discount Logic

**Purpose:** Auto-detect siblings and apply tiered discounts.

**New model:**
```python
class SiblingDiscountPolicy(TimestampMixin, Base):
    __tablename__ = "sibling_discount_policies"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    second_child_percent: Mapped[float] = mapped_column(Float, default=10.0)
    third_child_percent: Mapped[float] = mapped_column(Float, default=20.0)
    fourth_plus_percent: Mapped[float] = mapped_column(Float, default=30.0)
    apply_to_oldest_first: Mapped[bool] = mapped_column(Boolean, default=True)  # Oldest pays full

    __table_args__ = (
        Index("idx_sdp_school", "school_id"),
    )
```

**Service logic (in BillingService.generate_invoices):**
```python
# After resolving students from fee assignments:
# 1. Group students by parent (via parent_child_links)
# 2. For each parent group, sort children by age (oldest first)
# 3. Apply discount tier:
#    - 1st child: 0% discount (full price)
#    - 2nd child: second_child_percent
#    - 3rd child: third_child_percent
#    - 4th+: fourth_plus_percent
# 4. Discount stacks with manual fee_assignment discount
```

**New endpoints:**
- `GET /billing/sibling-policy` — get school policy
- `PUT /billing/sibling-policy` — update school policy (ADM only)

**New permissions:**
- `PERM_BILLING_SIBLING_POLICY_MANAGE`

---

### C2: Late Fees + Payment Plans

**Purpose:** Auto late fees + installment plans.

**New models:**
```python
class LateFeePolicy(TimestampMixin, Base):
    __tablename__ = "late_fee_policies"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    fee_type: Mapped[str] = mapped_column(String(20))  # "fixed" or "percent"
    amount: Mapped[float] = mapped_column(Float, default=0.0)  # MAD flat or percentage
    frequency: Mapped[str] = mapped_column(String(20))  # "once", "daily", "weekly"
    grace_days: Mapped[int] = mapped_column(Integer, default=5)
    max_fee: Mapped[float | None] = mapped_column(Float)  # Cap on total late fees


class PaymentPlan(TimestampMixin, Base):
    __tablename__ = "payment_plans"

    invoice_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("invoices.id", ondelete="CASCADE"))
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    total_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, canceled


class Installment(TimestampMixin, Base):
    __tablename__ = "installments"

    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("payment_plans.id", ondelete="CASCADE"))
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, paid, overdue
```

**Service: PaymentPlanService**
- `create_plan(invoice_id, num_installments)` — splits invoice into equal monthly installments
- `list_plans(parent_id)` — parent's active plans
- `mark_installment_paid(installment_id)` — when payment received

**Late fee logic (background task or service method):**
- `apply_late_fees()` — runs daily, checks overdue invoices, applies fees based on policy

**New endpoints:**
- `GET /billing/late-fee-policy`, `PUT /billing/late-fee-policy`
- `POST /billing/payment-plans` — create plan for invoice
- `GET /billing/payment-plans` — list plans
- `GET /billing/payment-plans/{id}` — plan with installments

**New permissions:**
- `PERM_BILLING_LATE_FEE_MANAGE`, `PERM_BILLING_PAYMENT_PLAN_CREATE`, `PERM_BILLING_PAYMENT_PLAN_READ`

---

### C3: Attendance Analytics + Alerts

**Purpose:** Absence rate tracking with configurable thresholds and alerts.

**New model:**
```python
class AttendanceAlert(TimestampMixin, Base):
    __tablename__ = "attendance_alerts"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("periods.id", ondelete="CASCADE"))
    absence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    absence_rate: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    threshold_exceeded: Mapped[str] = mapped_column(String(20))  # "warning" (15%), "critical" (25%)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("student_id", "period_id", "threshold_exceeded", name="uq_aa_student_period_threshold"),
        Index("idx_attendance_alerts_school", "school_id"),
    )
```

**Configuration (in settings or per-school):**
```python
ATTENDANCE_WARNING_THRESHOLD: float = 0.15  # 15%
ATTENDANCE_CRITICAL_THRESHOLD: float = 0.25  # 25%
```

**Service: AttendanceAnalyticsService**
- `compute_student_absence_rate(student_id, period_id)` -> {absence_count, total, rate, mention}
- `compute_class_absence_rates(class_id, period_id)` -> list of student rates
- `get_absence_trends(class_id, period_id)` -> daily/weekly trend data
- `check_thresholds_and_alert(school_id, period_id)` — batch check all students
  - Emits `AttendanceThresholdExceeded` domain event for notifications
  - Creates AttendanceAlert record

**New endpoints:**
- `GET /analytics/attendance/student/{id}` — individual student stats
- `GET /analytics/attendance/class/{id}` — class-level stats
- `GET /analytics/attendance/trends/{class_id}` — trend chart data
- `GET /analytics/attendance/alerts` — list alerts (ADM)
- `POST /analytics/attendance/check-thresholds` — trigger batch check (ADM/SYS)

**New permissions:**
- `PERM_ERP_ATTENDANCE_ANALYTICS_READ`, `PERM_ERP_ATTENDANCE_ALERT_MANAGE`

---

### C4: Timetable Auto-Generation

**Purpose:** Algorithm generates optimal weekly schedule from constraints.

**New models:**
```python
class TimetableConstraint(TimestampMixin, Base):
    __tablename__ = "timetable_constraints"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    constraint_type: Mapped[str] = mapped_column(String(50))
    # Types: "teacher_unavailable", "room_capacity", "max_hours_per_day",
    #        "subject_hours_per_week", "no_consecutive_same_subject"
    entity_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)  # teacher/class/room ID
    params: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # Examples:
    # teacher_unavailable: {"teacher_id": "...", "day": 2, "start": "08:00", "end": "12:00"}
    # subject_hours_per_week: {"class_id": "...", "subject": "Math", "hours": 6}
    # room_capacity: {"room": "A101", "max_students": 30}

    __table_args__ = (
        Index("idx_tc_school_year", "school_id", "academic_year_id"),
    )


class TimetableGenerationJob(TimestampMixin, Base):
    __tablename__ = "timetable_generation_jobs"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20))  # pending, running, completed, failed
    constraints_snapshot: Mapped[dict] = mapped_column(JSONB)
    result_slot_count: Mapped[int | None] = mapped_column(Integer)
    conflicts_found: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
```

**Service: TimetableGeneratorService**
- `set_constraints(school_id, academic_year_id, constraints: list)` — save constraints
- `list_constraints(school_id, academic_year_id)` — get all constraints
- `generate(school_id, academic_year_id)` -> job_id
  - Creates TimetableGenerationJob
  - Runs solver algorithm (backtracking + heuristics)
  - Algorithm: assign each (class, subject, hours_needed) to (day, timeslot, teacher, room)
  - Respects all constraints
  - Generates TimetableSlot rows as candidates (not committed yet)
- `get_job_status(job_id)` — check progress
- `apply_generated_timetable(job_id)` — admin approves, slots become active
- `preview_generated_timetable(job_id)` — view before applying

**New endpoints:**
- `POST /timetable/constraints` — set constraints
- `GET /timetable/constraints` — list constraints
- `POST /timetable/generate` — start generation job
- `GET /timetable/generate/{job_id}` — job status
- `GET /timetable/generate/{job_id}/preview` — preview result
- `POST /timetable/generate/{job_id}/apply` — apply to school

**New permissions:**
- `PERM_ERP_TIMETABLE_GENERATE`, `PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE`

**Algorithm note:** Implement as a greedy backtracking solver. For v1, don't use external libraries (no OR-Tools dependency). Start with simple constraint propagation. Can be improved later with more sophisticated algorithms.

---

## ENH-D: Communication & Docs Enhancements

### D1: Message Attachments + Search

**Purpose:** File attachments in messages + full-text search.

**Model changes:**
```python
# Add to Message model (com.py):
attachment_id: Mapped[uuid.UUID | None] = mapped_column(
    ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
)
```

**Search — add GIN index:**
```sql
-- Migration:
CREATE INDEX idx_messages_body_gin ON messages USING gin (to_tsvector('simple', body));
```

**Service changes (communication.py):**
- `send_message()` — accept optional `attachment_id`, validate document belongs to sender
- `search_messages(user_id, query)` — full-text search across user's conversations

**New endpoint:**
- `GET /messages/search?q=allergie` — search messages

---

### D2: Document Versioning

**Purpose:** Track document versions, view history, restore previous.

**New model:**
```python
class DocumentVersion(TimestampMixin, Base):
    __tablename__ = "document_versions"

    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    uploader_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    change_note: Mapped[str | None] = mapped_column(String(500))

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_versions_doc_version"),
        Index("idx_doc_versions_document", "document_id"),
    )
```

**Service changes (student_documents.py):**
- On upload: if document with same `linked_student_id + category` exists, create new version instead of new document.
- `list_versions(document_id)` — version history
- `restore_version(document_id, version_number)` — make old version current
- `get_version(document_id, version_number)` — download specific version

**New endpoints:**
- `GET /documents/{id}/versions` — list versions
- `POST /documents/{id}/versions/{n}/restore` — restore
- `GET /documents/{id}/versions/{n}` — download specific version

---

### D3: Report Scheduling + Email Delivery

**Purpose:** Automated report generation on schedule with email delivery.

**New model:**
```python
class ReportSchedule(TimestampMixin, Base):
    __tablename__ = "report_schedules"

    school_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)  # attendance, grades, billing
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, end_of_period
    parameters: Mapped[dict] = mapped_column(JSONB, default=dict)  # class_id, period_id, etc.
    recipient_roles: Mapped[list[str]] = mapped_column(ARRAY(String(20)))  # ["PAR", "TCH"]
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("idx_report_schedules_school", "school_id"),
        Index("idx_report_schedules_next_run", "next_run_at"),
    )
```

**Service: ReportSchedulerService**
- `create_schedule(report_type, frequency, params, recipients)`
- `list_schedules(school_id)` — all schedules
- `update_schedule(schedule_id, ...)` — modify
- `run_schedule(schedule_id)` — manual trigger
- `process_due_schedules()` — background task: find schedules where next_run_at <= now, generate report, email to recipients

**New endpoints:**
- `POST /reports/schedules` — create schedule
- `GET /reports/schedules` — list
- `PUT /reports/schedules/{id}` — update
- `DELETE /reports/schedules/{id}` — disable
- `POST /reports/schedules/{id}/run` — manual trigger

**New permissions:**
- `PERM_RPT_SCHEDULE_MANAGE`

---

### D4: AI Provider Abstraction

**Purpose:** Replace stubbed AI with provider-agnostic architecture. Mock provider returns realistic responses. Swap for real Claude/GPT when API key available.

**Architecture:**
```
backend/app/services/ai/
    __init__.py
    provider_base.py      # Abstract AIProvider protocol
    mock_provider.py      # Returns realistic canned responses (no API needed)
    claude_provider.py    # Real Claude API (uses API key from config)
    openai_provider.py    # Real OpenAI API (uses API key from config)
    provider_factory.py   # Creates correct provider from config
```

**Provider Protocol:**
```python
class AIProvider(Protocol):
    async def complete(self, prompt: str, system: str, max_tokens: int) -> str: ...
    async def analyze_writing(self, text: str, language: str) -> WritingFeedback: ...
    async def generate_recommendations(self, student_data: dict) -> list[Recommendation]: ...
    async def compute_kpi_insights(self, metrics: dict) -> list[str]: ...
```

**MockProvider:**
- `complete()` — returns template-based responses in fr/ar/en based on prompt keywords
- `analyze_writing()` — returns realistic grammar/structure feedback based on text length and language
- `generate_recommendations()` — returns recommendations based on grade ranges
- `compute_kpi_insights()` — returns insights based on metric thresholds

**ClaudeProvider (ready to use when API key added):**
```python
class ClaudeProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(self, prompt: str, system: str, max_tokens: int = 1024) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text
```

**Configuration:**
```python
# config.py:
AI_PROVIDER: str = "mock"  # "mock", "claude", "openai"
AI_API_KEY: str = ""  # Set when ready
AI_MODEL: str = ""  # Provider-specific model name
```

**Factory:**
```python
def create_ai_provider(settings) -> AIProvider:
    if settings.AI_PROVIDER == "claude":
        return ClaudeProvider(settings.AI_API_KEY, settings.AI_MODEL)
    elif settings.AI_PROVIDER == "openai":
        return OpenAIProvider(settings.AI_API_KEY, settings.AI_MODEL)
    return MockProvider()
```

The existing `ai.py` service methods (writing_attempt, recommendations, kpi_dashboard) would be updated to call `self._provider.complete(...)` instead of returning hardcoded responses.

---

## New Models Summary

| Model | Table | Module | Migration |
|-------|-------|--------|-----------|
| LoginHistory | login_history | iam.py | G27 |
| SiblingDiscountPolicy | sibling_discount_policies | billing.py | G27 |
| LateFeePolicy | late_fee_policies | billing.py | G27 |
| PaymentPlan | payment_plans | billing.py | G27 |
| Installment | installments | billing.py | G27 |
| Rubric | rubrics | lms.py | G28 |
| RubricCriterion | rubric_criteria | lms.py | G28 |
| RubricLevel | rubric_levels | lms.py | G28 |
| RubricScore | rubric_scores | lms.py | G28 |
| GradeCategory | grade_categories | lms.py | G28 |
| StudentPeriodAverage | student_period_averages | lms.py | G28 |
| QuestionBankItem | question_bank_items | lms.py | G28 |
| AttendanceAlert | attendance_alerts | erp.py | G29 |
| TimetableConstraint | timetable_constraints | erp.py | G29 |
| TimetableGenerationJob | timetable_generation_jobs | erp.py | G29 |
| DocumentVersion | document_versions | documents.py | G30 |
| ReportSchedule | report_schedules | reporting.py | G30 |

**Existing model changes:**
- Session: + `impersonator_id`
- Assignment: + `rubric_id`, `grade_category_id`, `grace_period_hours`, `late_penalty_per_day`, `max_late_days`, `allow_late`
- Grade: + `original_score`, `late_penalty`, `late_days`, `penalty_overridden`
- Message: + `attachment_id`

---

## New Permissions Summary

| Permission | Roles |
|-----------|-------|
| PERM_ADM_IMPERSONATE | ADM, DIR, SUP |
| PERM_IAM_LOGIN_HISTORY_READ | ADM, DIR, SUP + self |
| PERM_LMS_RUBRIC_CREATE | TCH, ADM |
| PERM_LMS_RUBRIC_READ | TCH, ADM, DIR |
| PERM_LMS_GRADEBOOK_MANAGE | TCH, ADM |
| PERM_LMS_GRADEBOOK_READ | TCH, ADM, DIR, PAR, STD |
| PERM_LMS_QUESTION_BANK_MANAGE | TCH, CONTENT_MGR |
| PERM_LMS_QUESTION_BANK_READ | TCH, CONTENT_MGR, ADM |
| PERM_BILLING_SIBLING_POLICY_MANAGE | ADM |
| PERM_BILLING_LATE_FEE_MANAGE | ADM |
| PERM_BILLING_PAYMENT_PLAN_CREATE | ADM |
| PERM_BILLING_PAYMENT_PLAN_READ | ADM, PAR |
| PERM_ERP_ATTENDANCE_ANALYTICS_READ | TCH, ADM, DIR |
| PERM_ERP_ATTENDANCE_ALERT_MANAGE | ADM |
| PERM_ERP_TIMETABLE_GENERATE | ADM |
| PERM_ERP_TIMETABLE_CONSTRAINT_MANAGE | ADM |
| PERM_RPT_SCHEDULE_MANAGE | ADM, DIR |

---

## Migration Plan

4 new migrations total:

- **G27**: IAM + Billing enhancements (login_history, Session.impersonator_id, sibling/late fee policies, payment plans)
- **G28**: LMS enhancements (rubrics, grade categories, question bank, Assignment/Grade field additions)
- **G29**: ERP enhancements (attendance alerts, timetable constraints/generation jobs)
- **G30**: Docs/Comms enhancements (document versions, report schedules, Message.attachment_id, messages GIN index)
