# Execution Prompts — Ecole Platform

> **Unified prompt file for Testing + CI/CD + Infrastructure enhancements.**
> **Runner**: Codex or Claude Code — autonomous, no human interaction until the end.
> **Structure**: Each prompt has 3 macro phases: **ANALYZE** → **EXECUTE** → **VERIFY**.
> **Git**: Conditional — Codex commits after each prompt, Claude Code does not.

---

## Global Instructions (READ FIRST — applies to EVERY prompt)

```
ENVIRONMENT DETECTION:
- If running as OpenAI Codex: set CODEX_ENV=true
- If running as Claude Code: set CODEX_ENV=false
- Detection heuristic: check if `CODEX_ENV` env var is set, or if the runtime is sandboxed (Codex), or if you have access to Anthropic-style tool use (Claude Code).

GIT BEHAVIOR (end of every prompt):
- If CODEX_ENV=true → run: git add -A && git commit -m "<COMMIT_MSG>"
- If CODEX_ENV=false → do NOT run any git command. Print "SKIP GIT: Claude Code mode" instead.
- <COMMIT_MSG> is provided at the end of each prompt.

ERROR HANDLING:
- If a step fails, log the error, attempt a fix, and continue.
- If a fix is not possible, log "BLOCKED: <reason>" and continue to the next step.
- Do NOT stop execution. Continue until all steps are complete.

FILE PATHS:
- Project root: the directory containing backend/, web/, infra/, .github/
- All relative paths are from project root unless stated otherwise.

RULES (apply to ALL prompts):
- Do NOT delete existing files unless explicitly told to.
- Do NOT break existing tests — all changes are additive.
- Do NOT modify .env or any file containing real secrets.
- Preserve existing imports and code — extend, don't replace.
- Use realistic Moroccan data: Faker("fr_FR"), +212 phones, Africa/Casablanca timezone, MAD currency, 0-20 grading scale, fr/ar/en languages.
```

---

## ============================================================
## PART 1: TESTING (Prompts T-01 through T-13)
## ============================================================

---

### T-01: Test Infrastructure Setup

```
═══════════════════════════════════════════════════════════════
PROMPT T-01: TEST INFRASTRUCTURE — conftest, factories, config
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ and understand these files before making any changes:

1. backend/tests/conftest.py
   → Understand existing fixtures (db_session, client, auth tokens)
   → Note which fixtures must be preserved for backward compatibility

2. backend/app/core/database.py
   → Understand Base, TimestampMixin, SchoolScopedMixin, NullableSchoolScopedMixin, SoftDeleteMixin
   → Note the async engine and session setup

3. backend/app/models/iam.py (first 200 lines)
   → Understand User, Membership, Session, InvitationCode, ParentChildLink models
   → Note enums: UserStatus, RoleCode
   → Note validators and required fields

4. backend/app/models/school.py
   → Understand School model, SchoolStatus enum, all fields

5. backend/app/models/lms.py (first 200 lines)
   → Understand Course, Assignment, Submission, Grade models

6. backend/app/models/erp.py (first 200 lines)
   → Understand AcademicYear, Class, Enrollment, AttendanceSession, AttendanceRecord

7. backend/app/models/billing.py (first 200 lines)
   → Understand Invoice, InvoiceItem, PaymentAttempt, FeeStructure, PaymentPlan, Installment

8. backend/app/models/com.py
   → Understand Notification, Conversation, Message

9. backend/app/models/documents.py
   → Understand Document, Resource

10. backend/app/models/calendar.py
    → Understand Event, EventRSVP

11. backend/requirements-dev.txt
    → Note existing test dependencies

12. backend/pytest.ini or pyproject.toml
    → Note existing pytest configuration

13. TESTING_ARCHITECTURE.md (sections: Test Infrastructure, Directory Structure, Configuration)
    → This is the reference architecture. Follow it.

AFTER READING: Confirm you understand the model structure, existing fixtures, and what needs to be created. List the models that need factories.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create requirements-test.txt:
File: backend/requirements-test.txt
Content: Extend requirements-dev.txt with:
  -r requirements-dev.txt
  pytest-factoryboy==2.7.*
  testcontainers[postgres]==4.*
  pytest-xdist==3.5.*
  pytest-timeout==2.3.*
  pytest-mock==3.14.*
  respx==0.21.*
  freezegun==1.4.*
  hypothesis==6.100.*
  faker==24.*
  pytest-benchmark==4.0.*

Run: cd backend && pip install -r requirements-test.txt

STEP 2 — Create directory structure:
Create all these directories with __init__.py in each:
  backend/tests/factories/
  backend/tests/unit/
  backend/tests/unit/domain/
  backend/tests/unit/models/
  backend/tests/unit/core/
  backend/tests/unit/services/
  backend/tests/integration/
  backend/tests/integration/api/
  backend/tests/integration/db/
  backend/tests/security/
  backend/tests/edge/
  backend/tests/performance/
  backend/tests/contract/

STEP 3 — Create backend/tests/factories/base.py:
- Import factory, AsyncSession, Base from the project
- Create AsyncSQLAlchemyFactory:
  - class Meta: abstract = True
  - @classmethod async def create(cls, session: AsyncSession, **kwargs):
      obj = cls.build(**kwargs)
      session.add(obj)
      await session.flush()
      await session.refresh(obj)
      return obj
  - @classmethod async def create_batch(cls, session, size, **kwargs):
      return [await cls.create(session, **k) for k in [{**kwargs} for _ in range(size)]]

STEP 4 — Create backend/tests/factories/iam.py:
- Import all IAM models (User, Membership, Session as UserSession, InvitationCode, ParentChildLink)
- Import enums (UserStatus, RoleCode or string constants)
- UserFactory: email=LazyFunction(fake.email), full_name=LazyFunction(fake.name), phone=LazyFunction(lambda: f"+212{fake.msisdn()[4:]}"), password_hash="$2b$12$placeholder_hash_for_testing", status="active", school_id=LazyFunction(uuid4)
- MembershipFactory: user=SubFactory(UserFactory), role_code="STD", status="active"
- SessionFactory: user_id=LazyFunction(uuid4), token=LazyFunction(lambda: secrets.token_urlsafe(32)), expires_at=LazyFunction(lambda: datetime.now(UTC) + timedelta(hours=24)), impersonator_id=None
- InvitationCodeFactory: code=LazyFunction(lambda: f"INV-{fake.random_number(6)}"), role_code="STD", school_id=LazyFunction(uuid4), max_uses=10, current_uses=0
- ParentChildLinkFactory: parent_user_id=LazyFunction(uuid4), child_user_id=LazyFunction(uuid4), status="active"

STEP 5 — Create backend/tests/factories/school.py:
- SchoolFactory: name=LazyFunction(lambda: f"École {fake.last_name()}"), name_ar=None, code=LazyFunction(lambda: f"SCH-{fake.random_number(4)}"), city="Casablanca", region="Casablanca-Settat", status="active", preferences={"timezone": "Africa/Casablanca", "default_language": "fr", "grading_scale": "moroccan_20"}

STEP 6 — Create backend/tests/factories/lms.py:
- CourseFactory: name=Sequence(lambda n: f"Course {n}"), school_id, teacher_id, academic_year_id, status="active"
- AssignmentFactory: title=Sequence(lambda n: f"Assignment {n}"), course_id, total_points=20, due_at=LazyFunction(lambda: datetime.now(UTC) + timedelta(days=7)), allow_late=True, late_penalty_per_day=2.0, max_late_days=3, grace_period_hours=0
- SubmissionFactory: assignment_id, student_id, status="draft"
- GradeFactory: submission_id, grader_id, score=15.0, out_of=20

STEP 7 — Create backend/tests/factories/erp.py:
- AcademicYearFactory: school_id, name=Sequence(lambda n: f"2025-2026-{n}"), start_date, end_date, status="active"
- ClassFactory: school_id, academic_year_id, name=Sequence(lambda n: f"Classe {n}"), level="1BAC"
- EnrollmentFactory: student_id, class_id, academic_year_id, status="active"
- AttendanceSessionFactory: class_id, date=LazyFunction(date.today), period="morning"
- AttendanceRecordFactory: session_id, student_id, status="present"

STEP 8 — Create backend/tests/factories/billing.py:
- InvoiceFactory: school_id, student_id, total=Decimal("500.00"), currency="MAD", status="sent", due_date=LazyFunction(lambda: date.today() + timedelta(days=30))
- InvoiceItemFactory: invoice_id, description="Frais de scolarité", amount=Decimal("500.00")
- PaymentAttemptFactory: invoice_id, amount=Decimal("500.00"), method="card", status="pending"
- FeeStructureFactory: school_id, name="Frais standard", amount=Decimal("500.00"), frequency="monthly"
- PaymentPlanFactory: invoice_id, total_installments=3, status="active"
- InstallmentFactory: plan_id, amount=Decimal("166.67"), due_date, status="pending"

STEP 9 — Create backend/tests/factories/com.py:
- NotificationFactory: user_id, title="Notification", body="Contenu", channel="in_app", status="unread"
- ConversationFactory: school_id, type="direct", created_by_id
- MessageFactory: conversation_id, sender_id, content="Bonjour"

STEP 10 — Create backend/tests/factories/documents.py:
- DocumentFactory: school_id, student_id, type="bulletin", title="Bulletin scolaire", file_path="/docs/test.pdf"
- ResourceFactory: school_id, title="Ressource pédagogique", type="pdf"

STEP 11 — Create backend/tests/factories/calendar.py:
- EventFactory: school_id, title="Réunion parents", start_at, end_at, created_by_id
- EventRSVPFactory: event_id, user_id, status="accepted"

STEP 12 — Update backend/tests/conftest.py:
IMPORTANT: Do NOT remove existing fixtures. ADD new ones alongside.
Add:
  - @pytest.fixture(scope="session") postgres_url(): testcontainer PostgreSQL 16-alpine
  - @pytest.fixture(scope="session") async engine(postgres_url): create_async_engine + Base.metadata.create_all
  - @pytest.fixture async db_session(engine): per-test session with automatic rollback
  - @pytest.fixture admin_auth(): returns mock AuthContext(user_id=uuid4(), role="ADM", school_id=uuid4())
  - @pytest.fixture teacher_auth(): returns mock AuthContext(role="TCH", ...)
  - @pytest.fixture student_auth(): returns mock AuthContext(role="STD", ...)
  - @pytest.fixture parent_auth(): returns mock AuthContext(role="PAR", ...)
  - @pytest.fixture sup_auth(): returns mock AuthContext(role="SUP", ...)

If there's a name collision with existing fixtures, suffix new ones with _v2 and add a compatibility alias.

STEP 13 — Update pyproject.toml (or create pytest section):
Add/update:
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  asyncio_default_fixture_loop_scope = "session"
  markers = [
      "slow: marks tests as slow",
      "security: RBAC/ABAC security matrix tests",
      "performance: benchmark and load tests",
      "unit: fast unit tests with mocked dependencies",
      "integration: tests requiring real database",
  ]
  addopts = ["--strict-markers", "--tb=short", "-q"]

  [tool.coverage.run]
  source = ["app"]
  branch = true
  omit = ["app/alembic/*", "app/core/config.py"]

  [tool.coverage.report]
  fail_under = 90
  show_missing = true
  exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "if __name__"]

STEP 14 — Add Makefile targets (append to existing Makefile):
  test-unit:
  	cd backend && pytest tests/unit -m unit --timeout=10 -q
  test-integration:
  	cd backend && pytest tests/unit tests/integration -m "unit or integration" --timeout=30
  test-security:
  	cd backend && pytest tests/security -m security --timeout=60
  test-full:
  	cd backend && pytest --cov=app --cov-branch --cov-report=html --cov-report=term-missing
  test-perf:
  	cd backend && pytest tests/performance -m performance --timeout=300 --benchmark-enable

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: All factory files exist and are importable:
  cd backend && python -c "
  from tests.factories.base import AsyncSQLAlchemyFactory
  from tests.factories.iam import UserFactory, MembershipFactory
  from tests.factories.school import SchoolFactory
  from tests.factories.lms import CourseFactory, AssignmentFactory
  from tests.factories.erp import ClassFactory, EnrollmentFactory
  from tests.factories.billing import InvoiceFactory
  from tests.factories.com import NotificationFactory
  from tests.factories.documents import DocumentFactory
  from tests.factories.calendar import EventFactory
  print('ALL FACTORIES IMPORTED OK')
  "

CHECK 2: Directory structure exists:
  find backend/tests -type d | sort
  → Must show: factories, unit/domain, unit/models, unit/core, unit/services, integration/api, integration/db, security, edge, performance, contract

CHECK 3: Existing tests still pass:
  cd backend && pytest tests/ -x -q --timeout=60 2>&1 | tail -5
  → Must show existing tests passing (or SKIP if DB not available)

CHECK 4: pyproject.toml has coverage config:
  grep -A3 "fail_under" backend/pyproject.toml || grep -A3 "fail_under" pyproject.toml
  → Must show fail_under = 90

CHECK 5: Makefile targets exist:
  grep "test-unit\|test-integration\|test-security\|test-full\|test-perf" Makefile
  → Must show all 5 targets

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(infra): add test infrastructure — factories, conftest, directory structure, pytest config

- Create 9 factory files for all domain models (IAM, School, LMS, ERP, Billing, COM, Documents, Calendar)
- Add testcontainer PostgreSQL fixture with per-test rollback
- Add role-based auth fixtures (admin, teacher, student, parent, supervisor)
- Configure pytest markers, coverage branch tracking, fail_under=90
- Add Makefile targets: test-unit, test-integration, test-security, test-full, test-perf
- Install test dependencies: factoryboy, testcontainers, freezegun, hypothesis, faker"

If CODEX_ENV=true:
  git add -A && git commit -m "<COMMIT_MSG above>"
Else:
  echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-02: Domain Value Object Unit Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-02: DOMAIN VALUE OBJECT UNIT TESTS (~45 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ these files completely:

1. backend/app/domain/value_objects/grade.py
   → Understand MoroccanGrade: constructor, value property, mention property
   → Note validation rules: 0-20 range, mention brackets (Très Bien >=16, Bien >=14, Assez Bien >=12, Passable >=10, Insuffisant <10)
   → Note any arithmetic operators, equality, or comparison methods

2. backend/app/domain/value_objects/money.py
   → Understand Money: constructor, currency validation, arithmetic
   → Note: MAD is the primary currency, also EUR/USD

3. backend/app/domain/value_objects/typed_id.py
   → Understand UserId, SchoolId, and other typed ID classes
   → Note validation rules for UUID inputs

4. backend/app/domain/value_objects/role_set.py
   → Understand RoleSet: constructor, has_role(), membership checks
   → Note valid role codes from permissions.py

5. TESTING_ARCHITECTURE.md section "1A Domain Value Object Tests"
   → Follow the patterns and test examples shown

AFTER READING: List every public method/property on each value object that needs testing.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/tests/unit/domain/test_grade.py (~15 tests):
- TestMoroccanGrade:
  - test_valid_grade_zero: MoroccanGrade(0).value == 0
  - test_valid_grade_twenty: MoroccanGrade(20).value == 20
  - test_valid_grade_decimal: MoroccanGrade(15.75).value == 15.75
  - test_valid_grade_boundary_ten: MoroccanGrade(10).value == 10
  - test_invalid_negative: pytest.raises(ValueError) for MoroccanGrade(-1)
  - test_invalid_above_twenty: pytest.raises(ValueError) for MoroccanGrade(21)
  - test_invalid_large_number: pytest.raises(ValueError) for MoroccanGrade(100)
  - test_mention_tres_bien_at_16: MoroccanGrade(16).mention == "Très Bien"
  - test_mention_tres_bien_at_20: MoroccanGrade(20).mention == "Très Bien"
  - test_mention_bien_at_14: MoroccanGrade(14).mention == "Bien"
  - test_mention_bien_at_15_99: MoroccanGrade(15.99).mention == "Bien"
  - test_mention_assez_bien_at_12: MoroccanGrade(12).mention == "Assez Bien"
  - test_mention_passable_at_10: MoroccanGrade(10).mention == "Passable"
  - test_mention_insuffisant_at_9_99: MoroccanGrade(9.99).mention == "Insuffisant"
  - test_mention_insuffisant_at_0: MoroccanGrade(0).mention == "Insuffisant"
- Use @pytest.mark.parametrize for boundary values:
  @pytest.mark.parametrize("score,expected_mention", [
      (20, "Très Bien"), (16, "Très Bien"),
      (15.99, "Bien"), (14, "Bien"),
      (13.99, "Assez Bien"), (12, "Assez Bien"),
      (11.99, "Passable"), (10, "Passable"),
      (9.99, "Insuffisant"), (0, "Insuffisant"),
  ])

STEP 2 — Create backend/tests/unit/domain/test_money.py (~12 tests):
- TestMoney:
  - test_valid_mad: Money(100, "MAD") — value and currency correct
  - test_valid_zero: Money(0, "MAD") — allowed
  - test_valid_eur: Money(50, "EUR") — allowed
  - test_valid_usd: Money(75, "USD") — allowed
  - test_invalid_negative: pytest.raises for Money(-1, "MAD")
  - test_invalid_currency: pytest.raises for Money(100, "XXX")
  - test_decimal_precision: Money(Decimal("499.99"), "MAD")
  - test_large_amount: Money(Decimal("999999.99"), "MAD")
  - If arithmetic exists: test_add, test_subtract, test_add_different_currencies_raises
  - If comparison exists: test_equality, test_less_than

STEP 3 — Create backend/tests/unit/domain/test_typed_id.py (~8 tests):
- test_user_id_from_valid_uuid: UserId(uuid4()) — works
- test_school_id_from_valid_uuid: SchoolId(uuid4()) — works
- test_user_id_from_string: UserId(str(uuid4())) — works (if supported)
- test_invalid_input: pytest.raises for UserId("not-a-uuid")
- test_equality_same_id: id1 == id1 is True
- test_equality_different_ids: id1 != id2
- test_repr_contains_uuid: "UserId" in repr(id)
- test_hash_consistent: hash(id1) == hash(id1_copy) if same UUID

STEP 4 — Create backend/tests/unit/domain/test_role_set.py (~10 tests):
- test_valid_single_role: RoleSet({"ADM"}) — works
- test_valid_multiple_roles: RoleSet({"ADM", "TCH"}) — works
- test_invalid_role_code: pytest.raises for RoleSet({"INVALID"})
- test_has_role_true: rs.has_role("ADM") is True
- test_has_role_false: rs.has_role("STD") is False
- test_empty_set: RoleSet(set()) — check behavior
- test_all_valid_roles: RoleSet({"SYS", "SUP", "ADM", "DIR", "TCH", "PAR", "STD", "CONTENT_MGR"})
- test_is_admin_property: if exists
- test_is_platform_role: if exists
- test_iteration: can iterate over roles in set

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run the new tests:
  cd backend && pytest tests/unit/domain/ -v --tb=short 2>&1 | tail -20
  → All tests must PASS
  → Count: ~45 tests expected

CHECK 2: No import errors:
  cd backend && python -c "
  from tests.unit.domain.test_grade import *
  from tests.unit.domain.test_money import *
  from tests.unit.domain.test_typed_id import *
  from tests.unit.domain.test_role_set import *
  print('ALL DOMAIN TESTS IMPORTABLE')
  "

CHECK 3: Existing tests unaffected:
  cd backend && pytest tests/ -x -q --timeout=60 --ignore=tests/unit --ignore=tests/integration --ignore=tests/security --ignore=tests/edge --ignore=tests/performance --ignore=tests/contract 2>&1 | tail -3

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(domain): add value object unit tests — MoroccanGrade, Money, TypedId, RoleSet

- 45 tests covering boundaries, mentions, currency validation, UUID handling, role membership
- Parametrized boundary tests for Moroccan 0-20 grading scale
- All tests are pure unit tests — no DB, no async, no mocking"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-03: Model Validator + Property Unit Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-03: MODEL VALIDATOR + PROPERTY TESTS (~60 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ these files completely:

1. backend/app/models/iam.py
   → Find ALL @validates decorators (email, phone, etc.)
   → Find ALL @property methods (is_active, has_2fa, is_email_verified, etc.)
   → Find __repr__ — note what it includes/excludes

2. backend/app/models/lms.py
   → Find ALL @validates decorators (score, total_points, late_penalty, etc.)
   → Find ALL @property methods (is_past_due, is_graded, etc.)
   → Find __repr__

3. backend/app/models/erp.py
   → Find ALL @validates and @property
   → Note Enrollment.is_active, AttendanceRecord properties

4. backend/app/models/billing.py
   → Find ALL @validates (total, amount, discount_percent, etc.)
   → Find ALL @property (is_overdue, is_paid, etc.)

5. backend/app/models/com.py
   → Find SoftDeleteMixin usage on Notification
   → Find Conversation.is_group property

6. backend/app/models/documents.py
   → Find SoftDeleteMixin usage on Document, Resource

7. backend/app/models/calendar.py
   → Find SoftDeleteMixin on Event, is_past, is_all_day properties

8. backend/app/models/reporting.py
   → Find ReportJob.is_complete, is_expired properties

9. backend/app/core/database.py
   → Understand SoftDeleteMixin: is_deleted property, soft_delete(), restore()

AFTER READING: Create a complete list of every validator and every property to test, organized by model.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/tests/unit/models/test_validators.py (~30 tests):
For each model, test its @validates methods:

TestUserValidators:
  - test_email_lowercased: validate_email("JoHn@Test.COM") → "john@test.com"
  - test_email_stripped: validate_email(" a@b.c ") → "a@b.c"
  - test_email_invalid_no_at: validate_email("notanemail") → ValueError
  - test_email_empty_string: validate_email("") → ValueError
  - test_phone_normalized: validate_phone("+212 6-12-34-56-78") → "+212612345678"
  - test_phone_no_country_code: validate_phone("0612345678") → ValueError

TestGradeValidators:
  - test_score_valid_zero: 0 → 0
  - test_score_valid_twenty: 20 → 20
  - test_score_negative: -1 → ValueError
  - test_score_above_twenty: 21 → ValueError
  - test_late_penalty_valid: 0 → 0
  - test_late_penalty_negative: -1 → ValueError

TestInvoiceValidators:
  - test_total_valid_zero: 0 → 0
  - test_total_negative: -1 → ValueError
  - test_currency_mad: "MAD" → "MAD"
  - test_currency_invalid: "XYZ" → ValueError (if validated)

TestAssignmentValidators:
  - test_total_points_positive: 20 → 20
  - test_total_points_zero: 0 → ValueError (if applicable)
  - test_late_penalty_per_day_range: 0-100

For each: if the model doesn't have that specific validator, adapt to what actually exists in the code. Match the REAL validator names and signatures.

STEP 2 — Create backend/tests/unit/models/test_helper_properties.py (~25 tests):
Create model instances manually (no DB needed — just set attributes directly):

TestUserProperties:
  - test_is_active_true: User(status="active").is_active is True
  - test_is_active_false: User(status="suspended").is_active is False
  - test_has_2fa_with_secret: User(totp_secret="abc").has_2fa is True
  - test_has_2fa_without: User(totp_secret=None).has_2fa is False
  - test_is_email_verified: User(email_verified_at=datetime.now()).is_email_verified is True

TestSessionProperties (with freezegun):
  - test_is_expired_future: not expired
  - test_is_expired_past: expired
  - test_is_impersonated_true: impersonator_id set
  - test_is_impersonated_false: impersonator_id None
  - test_is_revoked_true: revoked_at set
  - test_is_revoked_false: revoked_at None

TestInvoiceProperties (with freezegun):
  - test_is_overdue_past_due_sent: True
  - test_is_overdue_future_due: False
  - test_is_overdue_already_paid: False
  - test_is_paid: status="paid" → True

TestSoftDeleteMixin:
  - test_is_deleted_with_deleted_at: True
  - test_is_deleted_without: False
  - test_soft_delete_sets_deleted_at: (if method exists)
  - test_restore_clears_deleted_at: (if method exists)

TestSchoolProperties:
  - test_is_active: active + not deleted
  - test_is_subscription_valid_future: True
  - test_is_subscription_valid_expired: False

Adapt each test to match the ACTUAL property names and return types found in Phase 1.

STEP 3 — Create backend/tests/unit/models/test_repr.py (~10 tests):
  - test_user_repr_has_email: "email" keyword or actual email in repr
  - test_user_repr_no_password: "password_hash" NOT in repr
  - test_school_repr_has_name: school name in repr
  - test_invoice_repr_has_id: some identifier in repr
  - test_course_repr: check format
  - Spot-check 5+ models

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run model tests:
  cd backend && pytest tests/unit/models/ -v --tb=short 2>&1 | tail -25
  → All pass, ~60 tests

CHECK 2: No test isolation issues:
  cd backend && pytest tests/unit/models/ --forked -q 2>&1 | tail -5
  (or without --forked if not available)

CHECK 3: Existing tests still pass:
  cd backend && pytest tests/ --ignore=tests/unit --ignore=tests/integration --ignore=tests/security --ignore=tests/edge --ignore=tests/performance --ignore=tests/contract -x -q --timeout=60 2>&1 | tail -3

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(models): add validator + property unit tests for all models

- 30 validator tests: email, phone, score, total, currency, discount ranges
- 25 property tests: is_active, is_expired, is_overdue, is_deleted, etc.
- 10 repr tests: ensure no sensitive data leaks in __repr__
- Uses freezegun for time-dependent property tests"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-04: Permission + ABAC Unit Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-04: PERMISSION + ABAC UNIT TESTS (~40 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ these files completely:

1. backend/app/core/permissions.py (ALL of it — ~622 lines)
   → Map out: PLATFORM_ROLES, ROLE_HIERARCHY, all PERM_* constants
   → Understand get_effective_permissions(role_code) → set
   → Understand role_has_permission(role_code, permission) → bool
   → Note the circular detection logic
   → Count total permissions per role (direct + inherited)

2. backend/app/core/abac.py (ALL of it)
   → Understand apply_owner_scope(query, auth, ...): how it filters by role
   → Understand validate_parent_child_access(db, parent_id, child_id)
   → Understand validate_teacher_class_access(db, teacher_id, class_id)
   → Understand validate_student_teacher_access(db, student_id, teacher_id)

AFTER READING: Create a permission matrix showing which roles have which critical permissions (at least 20 key permissions × 8 roles).

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/tests/unit/core/test_permissions.py (~25 tests):

TestGetEffectivePermissions:
  - test_sys_permissions: SYS has its own + inherited from SUP chain
  - test_sup_permissions: SUP has its own + inherited from ADM chain
  - test_adm_permissions: ADM has its own + inherited from DIR chain
  - test_dir_permissions: DIR has its own + inherited from TCH
  - test_tch_direct_permissions: TCH has only direct perms
  - test_std_no_inheritance: STD does NOT inherit from TCH
  - test_par_no_inheritance: PAR does NOT inherit from any
  - test_content_mgr_lateral: CONTENT_MGR is not in vertical hierarchy

TestRoleHierarchyInheritance:
  - test_dir_inherits_all_tch: get_effective_permissions("DIR").issuperset(get_effective_permissions("TCH"))
  - test_adm_inherits_all_dir: get_effective_permissions("ADM").issuperset(get_effective_permissions("DIR"))
  - test_sup_inherits_all_adm: get_effective_permissions("SUP").issuperset(get_effective_permissions("ADM"))
  - test_hierarchy_chain_complete: SYS ⊃ SUP ⊃ ADM ⊃ DIR ⊃ TCH

TestRoleHasPermission (parametrized):
  @pytest.mark.parametrize("role,perm,expected", [
      ("TCH", PERM_LMS_ASSIGNMENT_CREATE, True),
      ("DIR", PERM_LMS_ASSIGNMENT_CREATE, True),    # inherited
      ("ADM", PERM_LMS_ASSIGNMENT_CREATE, True),    # inherited
      ("STD", PERM_LMS_ASSIGNMENT_CREATE, False),   # not in hierarchy
      ("PAR", PERM_LMS_ASSIGNMENT_CREATE, False),
      ("DIR", PERM_ADM_BILLING_MANAGE, True),       # DIR direct
      ("TCH", PERM_ADM_BILLING_MANAGE, False),      # not inherited down
      ("SUP", PERM_ADM_SCHOOL_MANAGE, True),
      ("STD", PERM_ERP_ATTENDANCE_ANALYTICS_READ, False),  # intentional
      ("PAR", PERM_ERP_ATTENDANCE_ANALYTICS_READ, False),  # intentional
  ])

TestPlatformRoles:
  - test_platform_roles_constant: PLATFORM_ROLES == {"SUP", "SYS", "CONTENT_MGR"}
  - test_platform_roles_not_school_scoped: SUP/SYS/CONTENT_MGR are platform-wide

TestCircularDetection:
  - test_no_circular_in_current_hierarchy: get_effective_permissions for each role succeeds

STEP 2 — Create backend/tests/unit/core/test_abac.py (~15 tests):
Note: apply_owner_scope works on SQLAlchemy Select objects. Mock them.

TestApplyOwnerScope:
  - test_adm_role_no_filter: ADM bypasses owner scope
  - test_dir_role_no_filter: DIR bypasses (if in admin_roles)
  - test_sup_role_no_filter: SUP bypasses
  - test_tch_role_filters_by_teacher_field: adds WHERE teacher_id = auth.user_id
  - test_par_role_filters_by_parent_field: adds WHERE parent_id or via link
  - test_std_role_filters_by_student_field: adds WHERE student_id = auth.user_id
  - test_custom_admin_roles: passing custom admin_roles list
  - test_none_fields_fallback: falls back to owner_field
  Use unittest.mock.MagicMock for Select objects and check .where() was called.

TestValidateRelationships (these need AsyncMock for DB):
  - test_valid_parent_child_link: active link → no exception
  - test_invalid_parent_child_link: no link → raises
  - test_inactive_parent_child_link: pending link → raises
  - test_valid_teacher_class: assignment exists → no exception
  - test_invalid_teacher_class: no assignment → raises
  - test_valid_student_teacher: enrollment + teacher assignment intersection → no exception
  - test_invalid_student_teacher: no intersection → raises

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run permission tests:
  cd backend && pytest tests/unit/core/ -v --tb=short 2>&1 | tail -20
  → All pass, ~40 tests

CHECK 2: Permission count sanity:
  cd backend && python -c "
  from app.core.permissions import get_effective_permissions
  for role in ['SYS','SUP','ADM','DIR','TCH','PAR','STD','CONTENT_MGR']:
      perms = get_effective_permissions(role)
      print(f'{role}: {len(perms)} permissions')
  "
  → SYS should have the most, STD/PAR the fewest

CHECK 3: All new tests isolated:
  cd backend && pytest tests/unit/core/ -v --tb=short -q 2>&1 | tail -5

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(core): add permission hierarchy + ABAC unit tests

- 25 tests for role hierarchy, effective permissions, role_has_permission
- 15 tests for ABAC: apply_owner_scope, parent-child, teacher-class, student-teacher
- Parametrized matrix covering 8 roles × key permissions
- Validates Part 3 hierarchy: SYS⊃SUP⊃ADM⊃DIR⊃TCH, STD/PAR independent"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-05: LMS Service Unit Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-05: LMS SERVICE UNIT TESTS (~65 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ these files completely:

1. backend/app/services/lms/grading_service.py (ALL — ~178 lines)
   → Map every method: grade_submission(), override_late_penalty()
   → Note parameters, return types, exceptions raised
   → Note repository calls and event dispatches

2. backend/app/services/lms/assignment_service.py (ALL — ~393 lines)
   → Map: create_assignment, list_assignments, upload_exercise_pdf, create_submission, upload_submission_file, finalize_submission
   → Note validation logic, error paths

3. backend/app/services/lms/quiz_service.py (ALL)
   → Map: create_quiz, start_attempt, submit_attempt, generate_quiz_from_bank
   → Note auto-grading logic, time limits, max attempts

4. backend/app/services/lms/_helpers.py (first 200 lines)
   → Understand calculate_late_penalty() — parameters, formula, edge cases
   → Note MAX_FILES_PER_SUBMISSION constant

5. backend/app/services/lms/_serializers.py
   → Understand _*_to_dict methods (needed to verify return shapes)

6. backend/app/repositories/lms.py (first 100 lines)
   → Understand repository method signatures (what to mock)

7. backend/app/repositories/quiz.py (first 100 lines)
   → Understand quiz repository method signatures

AFTER READING: Create a list of every method to test, with its happy path, error paths, and edge cases.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/tests/unit/services/test_grading_service.py (~25 tests):
Setup: GradingService(db=AsyncMock()). Mock self.repo, self.quiz_repo, self._dispatcher.

TestGradeSubmission:
  - test_valid_grade_creates_record: repo returns submission + assignment → grade created
  - test_score_exceeds_total_points: score=25, total_points=20 → ValidationError
  - test_submission_not_found: repo returns None → NotFoundError
  - test_wrong_teacher: auth.user_id != assignment.teacher_id → AuthorizationError
  - test_rubric_assignment_rejected: assignment.grading_type="rubric" → ValidationError
  - test_late_penalty_applied: late submission → score adjusted
  - test_grade_update_existing: grade already exists → update, not create
  - test_publish_triggers_event: body.publish=True → event dispatched
  - test_draft_no_event: body.publish=False → no event
  - test_score_exactly_zero: valid edge case
  - test_score_exactly_total: valid edge case

TestOverrideLatePenalty:
  - test_restores_original_score: penalty removed, score back to original
  - test_no_penalty_to_override: raises ValidationError
  - test_already_overridden: returns current state
  - test_audit_log_created: override logged

TestCalculateLatePenalty (pure function):
  - test_within_grace_period: no penalty
  - test_one_day_late: 1 * penalty_per_day
  - test_three_days_late: 3 * penalty_per_day
  - test_max_days_exceeded: raises error
  - test_late_not_allowed: raises error
  - test_score_floors_at_zero: penalty > score → 0
  - test_exact_grace_boundary: submitted at grace_period_hours exactly
  - test_no_grace_period: grace_period_hours=0
  - test_penalty_per_day_zero: no deduction even if late

STEP 2 — Create backend/tests/unit/services/test_assignment_service.py (~20 tests):
Setup: AssignmentService(db=AsyncMock()). Mock self.repo.

TestCreateAssignment:
  - test_valid_creation: returns assignment dict
  - test_course_not_found: repo returns no course → NotFoundError
  - test_not_course_teacher: auth doesn't match → AuthorizationError
  - test_due_date_in_past: should warn or reject depending on logic

TestUploadExercisePdf:
  - test_valid_pdf: saved successfully
  - test_non_pdf_file: raises ValidationError
  - test_file_too_large: (if size limit exists)

TestCreateSubmission:
  - test_new_submission: created with status="draft"
  - test_existing_submission: returns existing
  - test_not_enrolled_student: raises AuthorizationError

TestFinalizeSubmission:
  - test_draft_to_submitted: status changes
  - test_already_submitted: raises ValidationError
  - test_no_files_warning: (if applicable)

TestUploadSubmissionFile:
  - test_valid_file: added to submission
  - test_max_files_exceeded: raises ValidationError (MAX_FILES_PER_SUBMISSION)
  - test_submission_not_draft: can't add to submitted

STEP 3 — Create backend/tests/unit/services/test_quiz_service.py (~20 tests):
Setup: QuizService(db=AsyncMock()). Mock self.repo, self.quiz_repo.

TestCreateQuiz:
  - test_valid_creation
  - test_course_not_found
  - test_not_teacher

TestStartAttempt:
  - test_first_attempt_created
  - test_max_attempts_exceeded: raises
  - test_quiz_not_published: raises
  - test_time_limit_set_on_attempt

TestSubmitAttempt:
  - test_auto_grading_calculates_score: MCQ answers → correct score
  - test_time_limit_exceeded: reject or mark as timed_out
  - test_partial_answers: some correct, some wrong
  - test_already_submitted: raises

TestGenerateFromBank:
  - test_correct_question_count: selects exact number
  - test_randomized_selection: (if applicable)
  - test_insufficient_questions: raises if bank too small

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run LMS service tests:
  cd backend && pytest tests/unit/services/test_grading_service.py tests/unit/services/test_assignment_service.py tests/unit/services/test_quiz_service.py -v --tb=short 2>&1 | tail -25
  → All pass, ~65 tests

CHECK 2: No real DB calls:
  Verify all tests use AsyncMock — grep for "AsyncSession" in test files should only appear in mock setup, never as a real connection.

CHECK 3: Test isolation:
  cd backend && pytest tests/unit/services/ -v -q 2>&1 | tail -5

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(lms): add LMS service unit tests — grading, assignment, quiz

- 25 grading tests: grade_submission, override_late_penalty, calculate_late_penalty
- 20 assignment tests: CRUD, PDF upload, submission flow, finalization
- 20 quiz tests: create, attempt lifecycle, auto-grading, time limits
- All repos mocked with AsyncMock — pure service logic testing"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-06: Billing + Auth + Attendance Service Unit Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-06: BILLING + AUTH + ATTENDANCE SERVICE TESTS (~60 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ these files completely:

1. backend/app/services/billing.py (ALL)
   → Map: generate_invoices, apply_late_fees, sibling discount logic
   → Note: MAD currency, Moroccan billing rules

2. backend/app/services/payment_plan.py (ALL)
   → Map: create_payment_plan, record_installment_payment
   → Note installment calculation logic

3. backend/app/services/attendance_analytics.py (ALL)
   → Map: check_thresholds_and_alert, compute_attendance_rate, attendance_trends
   → Note threshold values and alert severity levels

4. backend/app/services/auth.py (ALL)
   → Map: login, impersonate, stop_impersonation, token_refresh
   → Note: session limits, device detection, LoginHistory creation

5. backend/app/repositories/billing.py and billing_enhancements.py (first 100 lines each)
   → Understand method signatures to mock

6. backend/app/repositories/auth.py (first 100 lines)
   → Understand method signatures

AFTER READING: List every method and its expected behaviors.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/tests/unit/services/test_billing_service.py (~25 tests):
TestGenerateInvoices:
  - test_standard_invoice_created: one student → one invoice with correct total in MAD
  - test_sibling_discount_applied: 2 children of same parent → 2nd gets discount
  - test_sibling_discount_not_applied_single_child: only child → full price
  - test_multiple_fee_items: multiple line items summed correctly
  - test_currency_always_mad: verify currency="MAD"

TestApplyLateFees:
  - test_overdue_invoice_gets_fee: sent + past due → late fee added
  - test_paid_invoice_no_fee: paid → no change
  - test_already_max_fees: cap on total late fees
  - test_fee_amount_calculation: verify formula

TestPaymentPlan:
  - test_create_plan_valid: 3 installments, total matches invoice
  - test_create_plan_amounts_sum: all installments sum to invoice total
  - test_installment_due_dates: sequential monthly dates
  - test_record_payment_marks_paid: individual installment
  - test_all_installments_paid_completes_plan: plan status → completed
  - test_partial_payment: (if supported)

TestBillingEdgeCases:
  - test_zero_amount_invoice: edge case
  - test_large_amount: 999999.99 MAD
  - test_decimal_precision: Decimal rounding

STEP 2 — Create backend/tests/unit/services/test_auth_service.py (~20 tests):
TestLogin:
  - test_valid_credentials: tokens returned + LoginHistory created
  - test_invalid_password: LoginHistory with failure + raises
  - test_new_device_detected: is_new_device=True + event dispatched
  - test_known_device: is_new_device=False
  - test_session_limit_reached: oldest session revoked
  - test_inactive_user: raises AuthorizationError
  - test_locked_user: raises (if lockout exists)

TestImpersonate:
  - test_admin_impersonates: shadow session created
  - test_non_admin_rejected: raises AuthorizationError
  - test_cross_school_rejected: different school_id → error
  - test_impersonation_logged: audit event created

TestStopImpersonation:
  - test_revokes_shadow_session
  - test_not_impersonating_noop

TestTokenRefresh:
  - test_valid_refresh: new access token
  - test_expired_refresh: raises
  - test_revoked_session: raises
  - test_refresh_extends_session: (if applicable)

STEP 3 — Create backend/tests/unit/services/test_attendance_service.py (~15 tests):
TestThresholdAlerts:
  - test_above_threshold_no_alert: 95% → nothing
  - test_at_warning_threshold: 80% → warning alert
  - test_at_critical_threshold: 60% → critical alert + event
  - test_custom_thresholds: school-specific overrides

TestComputeAttendanceRate:
  - test_all_present: 100%
  - test_all_absent: 0%
  - test_mixed: correct percentage
  - test_no_records: 0% or None

TestAttendanceTrends:
  - test_daily_grouping: correct daily buckets
  - test_weekly_grouping: correct weekly buckets
  - test_empty_period: no records → empty trend
  - test_single_day: one data point

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run all three test files:
  cd backend && pytest tests/unit/services/test_billing_service.py tests/unit/services/test_auth_service.py tests/unit/services/test_attendance_service.py -v --tb=short 2>&1 | tail -25
  → All pass, ~60 tests

CHECK 2: Verify no DB connections:
  grep -r "create_async_engine\|AsyncSession(" tests/unit/services/test_billing_service.py tests/unit/services/test_auth_service.py tests/unit/services/test_attendance_service.py
  → Should find nothing (all mocked)

CHECK 3: All unit tests so far:
  cd backend && pytest tests/unit/ -v -q 2>&1 | tail -5
  → Total should be ~165+ tests (T-02 through T-06)

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(services): add billing, auth, attendance service unit tests

- 25 billing tests: invoice generation, sibling discounts, late fees, payment plans
- 20 auth tests: login, impersonation, session limits, device detection, token refresh
- 15 attendance tests: threshold alerts, rate computation, trend analysis
- All with mocked repositories — freezegun for date-dependent logic"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-07: Communication + School + Remaining Service Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-07: COMMUNICATION + SCHOOL + OTHER SERVICE TESTS (~50 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ completely:
1. backend/app/services/communication.py → conversations, messages, ABAC rules for STD/PAR
2. backend/app/services/school.py → CRUD, subscription, soft delete
3. backend/app/services/timetable_generator.py → constraint validation, backtracking, preview vs apply
4. backend/app/services/gradebook.py → weighted averages, GPA, Moroccan mentions
5. backend/app/services/report_scheduler.py or reports.py → schedule processing

AFTER READING: List methods and edge cases for each service.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — backend/tests/unit/services/test_communication_service.py (~15 tests):
- test_std_create_conversation_validates_teacher_relationship
- test_std_create_group_conversation_rejected (STD cannot create GROUP type)
- test_std_message_unrelated_teacher_rejected (ABAC)
- test_par_create_conversation_validates_parent_child_link
- test_par_inactive_link_rejected
- test_tch_create_conversation_allowed
- test_send_message_valid
- test_send_message_empty_content_rejected
- test_search_messages_filters_correctly
- test_mark_as_read
- test_unread_count

STEP 2 — backend/tests/unit/services/test_school_service.py (~10 tests):
- test_create_school_defaults (Africa/Casablanca, fr, moroccan_20)
- test_create_school_duplicate_code_error
- test_update_school_subscription
- test_deactivate_school_soft_delete
- test_get_school_sup_sees_any
- test_get_school_adm_sees_own_only
- test_list_schools_pagination

STEP 3 — backend/tests/unit/services/test_timetable_service.py (~15 tests):
- test_validate_no_overlaps: same teacher, same time → error
- test_validate_no_room_conflicts: same room, same time → error
- test_preview_returns_slots_without_commit
- test_apply_creates_timetable_rows
- test_teacher_availability_respected
- test_20_classes_within_time_limit (mark @pytest.mark.slow)
- test_impossible_constraints_detected
- test_partial_generation: some classes fit, others don't

STEP 4 — backend/tests/unit/services/test_gradebook_service.py (~15 tests):
- test_weighted_average_correct: weights sum to 1.0
- test_weighted_average_missing_grades: handles None
- test_moroccan_mention_calculation: each bracket
- test_class_averages_aggregation
- test_transcript_all_periods_included
- test_gpa_calculation: (if applicable)
- test_grade_category_weights

STEP 5 — backend/tests/unit/services/test_report_service.py (~10 tests):
- test_process_due_schedules_triggers_generation
- test_report_format_validation (pdf, xlsx)
- test_schedule_creation_cron
- test_expired_report_not_processed
- test_report_generation_dispatches_event

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Run all new tests:
  cd backend && pytest tests/unit/services/test_communication_service.py tests/unit/services/test_school_service.py tests/unit/services/test_timetable_service.py tests/unit/services/test_gradebook_service.py tests/unit/services/test_report_service.py -v --tb=short 2>&1 | tail -25

CHECK 2: Full unit test count:
  cd backend && pytest tests/unit/ --co -q 2>&1 | tail -3
  → Should be ~210+ collected tests

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(services): add communication, school, timetable, gradebook, report unit tests

- 15 communication tests: STD/PAR ABAC messaging rules, conversation lifecycle
- 10 school tests: CRUD, soft delete, subscription, role-scoped visibility
- 15 timetable tests: constraint validation, backtracking, preview vs apply
- 15 gradebook tests: weighted averages, Moroccan mentions, transcript
- 10 report tests: scheduling, format validation, event dispatch"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-08: API Integration Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-08: API INTEGRATION TESTS (~80 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/app/api/v1/schools.py → all endpoint signatures, decorators
2. backend/app/api/v1/gradebook.py → all endpoints
3. backend/app/api/v1/rubrics.py → all endpoints
4. backend/app/api/v1/billing.py and payments.py → all endpoints
5. backend/app/api/v1/attendance_analytics.py → all endpoints
6. backend/app/api/v1/timetable_generation.py → all endpoints
7. backend/tests/conftest.py → understand existing client fixture, auth helper
8. backend/app/api/v1/router.py → understand route registration

Map every endpoint: method, path, required auth, expected status codes.

── PHASE 2: EXECUTE ──────────────────────────────────────────

Use the testcontainer DB from conftest. Use factories to seed data.
Use httpx.AsyncClient with app for requests.

STEP 1 — backend/tests/integration/api/test_schools_api.py (~20 tests):
  - POST /api/v1/schools: SUP → 201
  - POST /api/v1/schools: ADM → 403
  - POST /api/v1/schools: no token → 401
  - POST /api/v1/schools: duplicate code → 409
  - GET /api/v1/schools: SUP sees all schools
  - GET /api/v1/schools: ADM sees own school only
  - GET /api/v1/schools/{id}: valid → 200
  - GET /api/v1/schools/{id}: not found → 404
  - PATCH /api/v1/schools/{id}: update name → 200
  - DELETE /api/v1/schools/{id}: soft delete → 204
  Each test: create data with factories → make request → assert status + body

STEP 2 — backend/tests/integration/api/test_gradebook_api.py (~15 tests)
STEP 3 — backend/tests/integration/api/test_rubrics_api.py (~15 tests)
STEP 4 — backend/tests/integration/api/test_billing_api.py (~15 tests)
STEP 5 — backend/tests/integration/api/test_attendance_analytics_api.py (~10 tests)
STEP 6 — backend/tests/integration/api/test_timetable_api.py (~10 tests)

Each file follows the same pattern: seed → request → assert.

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: cd backend && pytest tests/integration/api/ -v --tb=short 2>&1 | tail -30
CHECK 2: Verify factories created real DB records (no mock leakage)
CHECK 3: All status codes match expected (no 500s in happy paths)

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(api): add API integration tests for schools, gradebook, rubrics, billing, attendance, timetable

- 80 tests against real testcontainer PostgreSQL
- Full request→response testing with factory-seeded data
- Covers happy paths, auth errors (401/403), not found (404), conflicts (409)"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-09: Database Repository Integration Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-09: DB REPOSITORY INTEGRATION TESTS (~40 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/app/repositories/school.py → CRUD methods, pagination, soft delete
2. backend/app/repositories/lms.py → assignment CRUD, grade creation, FK constraints
3. backend/app/repositories/billing.py → invoice with items, sibling query, payment plan

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — backend/tests/integration/db/test_school_repo.py (~15 tests):
  - test_create_and_read, test_update, test_soft_delete_and_restore
  - test_pagination_with_cursor, test_unique_constraint_on_code
  - test_school_scoped_mixin_filtering

STEP 2 — backend/tests/integration/db/test_lms_repo.py (~15 tests):
  - test_assignment_fk_to_course, test_grade_fk_to_submission
  - test_pagination_with_filters, test_school_scoped_filtering
  - test_cascade_behavior

STEP 3 — backend/tests/integration/db/test_billing_repo.py (~10 tests):
  - test_invoice_with_items, test_get_siblings_query
  - test_payment_plan_with_installments, test_fk_constraints

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: cd backend && pytest tests/integration/db/ -v --tb=short 2>&1 | tail -20
CHECK 2: Verify real SQL executed (check logs or count queries)

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(db): add repository integration tests — school, LMS, billing

- 40 tests against real PostgreSQL via testcontainers
- Tests CRUD, pagination, FK constraints, soft delete, cascade behavior
- Validates SchoolScopedMixin filtering works correctly"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-10: RBAC + ABAC Security Matrix Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-10: RBAC + ABAC SECURITY MATRIX (~120 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/app/core/permissions.py → all PERM_* constants, ROLE_HIERARCHY
2. backend/app/core/abac.py → all validate_* functions
3. backend/app/api/v1/ — ALL endpoint files → identify permission decorators/checks
4. backend/tests/test_rbac_security.py → understand existing RBAC tests to NOT duplicate

Map: endpoint × role → expected status code. Create the full matrix.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — backend/tests/security/test_rbac_matrix.py (~80 tests):
For each NEW endpoint group, test each of 8 roles:
  @pytest.mark.parametrize("role,expected_status", [
      ("SYS", 200), ("SUP", 200), ("ADM", 200), ("DIR", 200),
      ("TCH", 403), ("PAR", 403), ("STD", 403), ("CONTENT_MGR", 403),
  ])
  Groups: schools, gradebook, rubrics, question-bank, payment-plans, attendance-analytics, timetable-generation
  Also test: no token → 401

STEP 2 — backend/tests/security/test_abac_parent_child.py (~15 tests):
  - PAR with active link → sees child's grades, attendance, billing, documents
  - PAR without link → 403
  - PAR with inactive link → 403

STEP 3 — backend/tests/security/test_abac_student_teacher.py (~15 tests):
  - STD messages enrolled teacher → 200
  - STD messages unrelated teacher → 403
  - STD creates group conversation → 400

STEP 4 — backend/tests/security/test_abac_teacher_class.py (~10 tests):
  - TCH grades own course → 200
  - TCH grades other's course → 403

STEP 5 — backend/tests/security/test_permission_escalation.py (~10 tests):
  - STD cannot hit ADM endpoints
  - PAR cannot impersonate
  - TCH cannot manage school settings

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: cd backend && pytest tests/security/ -v --tb=short 2>&1 | tail -30
CHECK 2: Verify no 500 status codes in any security test (should be 401/403/400 only)
CHECK 3: Count total: should be ~120 new security tests

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(security): add comprehensive RBAC matrix + ABAC security tests

- 80 RBAC matrix tests: 7 endpoint groups × 8 roles + no-token
- 15 parent-child ABAC tests across grades, attendance, billing, documents
- 15 student-teacher ABAC tests for messaging restrictions
- 10 teacher-class ABAC tests for grading scope
- 10 privilege escalation tests for role boundary enforcement"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-11: Edge Case + Boundary + Time Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-11: EDGE CASE + BOUNDARY + TIME TESTS (~80 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

Review all validators, properties, and service methods from T-02 through T-07 for edge cases not yet covered.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — backend/tests/edge/test_boundary_values.py (~30 tests):
  - Grade: 0, 20, 0.01, 19.99, 0.001 precision
  - Invoice: total=0, total=999999.99
  - Discount: 0%, 100%
  - Empty strings: email="", phone="", name=""
  - Max-length: 255 chars, 500 chars
  - Unicode: Arabic "أحمد المغربي", French "François Côté"
  - Pagination: limit=0, limit=1000, cursor="invalid"

STEP 2 — backend/tests/edge/test_time_dependent.py (~25 tests):
  All with @freeze_time:
  - Session expires at exact second
  - Assignment due at midnight Africa/Casablanca (UTC+1)
  - Invoice due + grace period
  - Subscription expiration edge
  - Academic year transition (June 30 → July 1)
  - Late penalty at day boundary (23:59:59 vs 00:00:00)
  - DST transitions (Morocco observes Ramadan time changes)

STEP 3 — backend/tests/edge/test_error_paths.py (~25 tests):
  - NotFound for every entity type (user, course, assignment, invoice, school, etc.)
  - Duplicate creation errors (invitation code, school code, enrollment)
  - Invalid state transitions (grade a draft, submit a graded)
  - Cascade effects (delete course with assignments)
  - Empty results (list with no matching records)
  - Concurrent modifications (if optimistic locking exists)

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: cd backend && pytest tests/edge/ -v --tb=short 2>&1 | tail -25
CHECK 2: All ~80 tests pass

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(edge): add boundary value, time-dependent, and error path tests

- 30 boundary tests: numeric limits, empty strings, Unicode, pagination edges
- 25 time tests: session expiry, due dates, timezone transitions, DST
- 25 error path tests: not found, duplicates, invalid transitions, cascades"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-12: Performance + Contract Tests

```
═══════════════════════════════════════════════════════════════
PROMPT T-12: PERFORMANCE + CONTRACT TESTS (~50 tests)
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ: TESTING_ARCHITECTURE.md sections 5 and 6.
Understand performance targets and contract validation patterns.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — backend/tests/performance/test_benchmarks.py (~20 tests):
  @pytest.mark.performance
  - benchmark get_effective_permissions for all 8 roles (target: <1ms each)
  - benchmark apply_owner_scope (target: <1ms)
  - benchmark MoroccanGrade creation (target: <0.1ms)
  - benchmark role_has_permission (target: <0.5ms)
  - benchmark calculate_late_penalty (target: <0.5ms)

STEP 2 — backend/tests/performance/test_load_patterns.py (~10 tests):
  @pytest.mark.slow
  - 100 concurrent permission checks
  - Batch grade creation (40 at once)
  - Paginate 1000 records

STEP 3 — backend/tests/contract/test_api_contracts.py (~15 tests):
  - Validate response envelopes match schema for key endpoints
  - Validate error responses have correct format
  - Validate pagination has cursor + has_more

STEP 4 — backend/tests/contract/test_migration_contracts.py (~5 tests):
  - All migration files have upgrade() and downgrade()
  - No duplicate revision IDs
  - Linear migration chain (single head)

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: cd backend && pytest tests/performance/ tests/contract/ -v --tb=short 2>&1 | tail -25
CHECK 2: Benchmarks complete within expected thresholds

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(perf+contract): add performance benchmarks and API contract tests

- 20 benchmarks: permission resolution, ABAC, grade creation targets
- 10 load pattern tests: concurrent permissions, batch grades, pagination
- 15 API contract tests: response schemas, error format, pagination structure
- 5 migration contract tests: upgrade/downgrade, linear chain, no duplicates"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### T-13: Coverage Gap Analysis + Fill

```
═══════════════════════════════════════════════════════════════
PROMPT T-13: COVERAGE GAP ANALYSIS + FILL TO 90%
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

Run full coverage:
  cd backend && pytest --cov=app --cov-branch --cov-report=term-missing --cov-report=html 2>&1

Analyze the output:
- Identify ALL files below 90% line coverage
- Identify ALL files below 85% branch coverage
- List uncovered lines/branches for each file
- Prioritize: services > core > models > repositories

── PHASE 2: EXECUTE ──────────────────────────────────────────

For each under-covered file:
1. Read the file and identify untested code paths
2. Write targeted tests in the appropriate test directory
3. Focus on:
   - Untested if/else branches
   - Error handlers and exception paths
   - Untested service methods
   - Edge cases in validators

Create new test files or add to existing ones as appropriate.
Target: 90%+ line coverage, 85%+ branch coverage for app/ directory.

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Full coverage run:
  cd backend && pytest --cov=app --cov-branch --cov-report=term-missing 2>&1 | grep -E "^(TOTAL|app/)" | tail -20
  → TOTAL must show ≥90% line, ≥85% branch

CHECK 2: No regressions:
  cd backend && pytest -x -q 2>&1 | tail -5
  → All tests pass

CHECK 3: Final test count:
  cd backend && pytest --co -q 2>&1 | tail -3
  → Should be ~1,200+ tests

CHECK 4: Generate final summary:
  echo "=== FINAL COVERAGE SUMMARY ==="
  cd backend && pytest --cov=app --cov-branch --cov-report=term 2>&1 | grep TOTAL

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "test(coverage): fill coverage gaps to reach 90%+ line, 85%+ branch

- Targeted tests for uncovered branches and error paths
- Final coverage: [LINE]% line, [BRANCH]% branch
- Total test count: ~1,200+"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

## ============================================================
## PART 2: CI/CD & INFRASTRUCTURE (Prompts CI-01 through CI-12)
## ============================================================

---

### CI-01: Pre-commit Hooks Setup

```
═══════════════════════════════════════════════════════════════
PROMPT CI-01: PRE-COMMIT HOOKS SETUP
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. CICD_INFRASTRUCTURE.md section "6B Pre-commit Hooks"
2. Makefile → understand existing lint targets (lint, lint-fix, format)
3. backend/pyproject.toml → check for existing ruff config
4. .pre-commit-config.yaml → check if already exists (may not)

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create .pre-commit-config.yaml at project root:
  repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.8.0
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format
    - repo: https://github.com/Yelp/detect-secrets
      rev: v1.5.0
      hooks:
        - id: detect-secrets
          args: ['--baseline', '.secrets.baseline']
    - repo: https://github.com/compilerla/conventional-pre-commit
      rev: v3.6.0
      hooks:
        - id: conventional-pre-commit
          stages: [commit-msg]
          args: [feat, fix, chore, docs, style, refactor, perf, test, ci, build]
    - repo: local
      hooks:
        - id: alembic-heads
          name: Check for multiple Alembic heads
          entry: bash -c 'cd backend && heads=$(alembic heads 2>/dev/null | wc -l); [ "$heads" -le 1 ]'
          language: system
          files: 'alembic/versions/.*\.py$'
          pass_filenames: false
    - repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.6.0
      hooks:
        - id: check-added-large-files
          args: ['--maxkb=5120']
        - id: check-merge-conflict
        - id: check-yaml
        - id: end-of-file-fixer
        - id: trailing-whitespace

STEP 2 — Generate .secrets.baseline:
  pip install detect-secrets --break-system-packages
  detect-secrets scan > .secrets.baseline

STEP 3 — Add Makefile target:
  hooks-install: ## Install pre-commit hooks
  	pip install pre-commit --break-system-packages
  	pre-commit install
  	pre-commit install --hook-type commit-msg
  	@echo "Pre-commit hooks installed"

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: YAML valid: python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"
CHECK 2: .secrets.baseline exists and is valid JSON: python -c "import json; json.load(open('.secrets.baseline'))"
CHECK 3: Makefile target exists: grep "hooks-install" Makefile

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "ci(hooks): add pre-commit hooks — ruff, detect-secrets, conventional commits

- Ruff lint+format matching CI pipeline version
- Secret detection with baseline
- Conventional commit message enforcement
- Alembic migration head conflict detection
- Large file, merge conflict, YAML, whitespace checks"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-02: CI Pipeline Hardening

```
═══════════════════════════════════════════════════════════════
PROMPT CI-02: CI PIPELINE HARDENING — Matrix + Security + Migration
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ completely:
1. .github/workflows/ci.yml (ALL of it)
2. CICD_INFRASTRUCTURE.md Category 1 (sections 1A, 1B, 1C)
3. backend/pyproject.toml → existing tool config

Map: current job names, dependencies (needs), services, triggers.

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Add strategy.matrix to unit-tests and integration-tests jobs:
  strategy:
    fail-fast: false
    matrix:
      python-version: ["3.12", "3.13"]
      postgres-version: ["15", "16", "17"]

STEP 2 — Add pip cache to ALL Python jobs:
  - uses: actions/cache@v4
    with:
      path: ~/.cache/pip
      key: pip-${{ matrix.python-version || '3.12' }}-${{ hashFiles('backend/requirements*.txt') }}

STEP 3 — Add npm cache to web jobs:
  - uses: actions/cache@v4
    with:
      path: ~/.npm
      key: npm-${{ hashFiles('web/package-lock.json') }}

STEP 4 — Add security-trivy job (after lint):
  Image scan with aquasecurity/trivy-action, CRITICAL+HIGH, exit-code: 1

STEP 5 — Add security-pip-audit job:
  pip-audit -r backend/requirements.txt --strict

STEP 6 — Add security-bandit job:
  bandit -r backend/app/ -c pyproject.toml, upload JSON report artifact

STEP 7 — Add migration-safety job (conditional on alembic/ changes):
  PostgreSQL 16 → alembic upgrade head → downgrade base → upgrade head

STEP 8 — Add migration head check to lint job:
  alembic heads | wc -l → fail if >1

STEP 9 — Add [tool.bandit] to pyproject.toml:
  exclude_dirs = ["tests", "alembic"]
  skips = ["B101"]

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: YAML valid: python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
CHECK 2: All new jobs have correct needs dependencies
CHECK 3: pyproject.toml is valid TOML: python -c "import tomllib; tomllib.load(open('backend/pyproject.toml','rb'))" (or pyproject.toml at root)

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "ci(pipeline): add matrix testing, security scanning, migration safety

- Matrix: Python 3.12/3.13 × PostgreSQL 15/16/17
- Security: Trivy container scan, pip-audit, Bandit static analysis
- Migration safety: forward/downgrade/re-forward dry-run on PRs
- Dependency caching for pip and npm"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-03: Docker Build Optimization

```
═══════════════════════════════════════════════════════════════
PROMPT CI-03: DOCKER BUILD OPTIMIZATION
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/Dockerfile (ALL)
2. web/Dockerfile (ALL)
3. CICD_INFRASTRUCTURE.md section 2A

── PHASE 2: EXECUTE ──────────────────────────────────────────

Rewrite backend/Dockerfile with:
- # syntax=docker/dockerfile:1.7
- ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
- System deps layer with rm -rf /var/lib/apt/lists/*
- --mount=type=cache,target=/root/.cache/pip for pip install
- test stage: runs ruff check + ruff format --check
- development stage: with reload
- production stage: non-root appuser, 4 workers, healthcheck

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Dockerfile syntax valid: docker build --check ./backend (or just verify no syntax errors)
CHECK 2: All stages defined: grep "^FROM" backend/Dockerfile → should show base, test, development, production

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "build(docker): optimize backend Dockerfile with BuildKit caching

- Multi-stage: base → test → development → production
- BuildKit cache mounts for pip (faster rebuilds)
- Test stage runs ruff lint+format check
- Production: non-root user, 4 workers, httpx healthcheck"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-04: Container Registry + Versioned Tags

```
═══════════════════════════════════════════════════════════════
PROMPT CI-04: CONTAINER REGISTRY + VERSIONED TAGS + SBOM
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. .github/workflows/ci.yml → existing jobs, understand where to add publish
2. CICD_INFRASTRUCTURE.md section 2B

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Add publish-images job to ci.yml:
  - Only on push to main
  - needs: [unit-tests, integration-tests, security-trivy]
  - Login to ghcr.io, build+push backend and web images
  - Tags: SHA (8 chars) + latest
  - SBOM generation with anchore/sbom-action

STEP 2 — Create .github/workflows/cleanup-images.yml:
  - Weekly Sunday 3AM
  - Delete untagged, keep min 10 versions

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: Both YAML files valid
CHECK 2: publish-images job correctly gated on main push
CHECK 3: cleanup workflow has correct schedule

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "ci(registry): add ghcr.io image publishing with SHA tags and SBOM

- Publish backend+web images on merge to main
- Tags: git SHA (8 chars) + latest
- SBOM generation (SPDX format) for compliance
- Weekly cleanup of old untagged images"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-05: PgBouncer Connection Pooling

```
═══════════════════════════════════════════════════════════════
PROMPT CI-05: PGBOUNCER CONNECTION POOLING
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. infra/docker-compose.prod.yml (ALL)
2. infra/docker-compose.staging.yml (ALL)
3. backend/app/core/database.py → engine creation, connect_args
4. CICD_INFRASTRUCTURE.md section 3C

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Add pgbouncer service to docker-compose.prod.yml and staging.yml
STEP 2 — Update backend DATABASE_URL to point to pgbouncer:6432
STEP 3 — Add statement_cache_size=0 to connect_args in database.py

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: docker compose -f infra/docker-compose.prod.yml config (validates)
CHECK 2: grep "statement_cache_size" backend/app/core/database.py → found
CHECK 3: grep "pgbouncer" infra/docker-compose.prod.yml → service exists

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "infra(db): add PgBouncer transaction-level connection pooling

- PgBouncer in prod+staging: 50 server connections, 200 client max
- Backend routes through pgbouncer:6432 instead of direct postgres
- Disabled asyncpg statement cache for PgBouncer compatibility"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-06: Read Replica + DB Routing

```
═══════════════════════════════════════════════════════════════
PROMPT CI-06: READ REPLICA + SQLALCHEMY ROUTING
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. infra/docker-compose.prod.yml → postgres service config
2. infra/postgres/init.sql → existing roles
3. backend/app/core/database.py → current engine/session setup
4. backend/app/core/config.py → settings class
5. CICD_INFRASTRUCTURE.md section 3B

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Add replicator role to init.sql
STEP 2 — Add postgres-replica service to docker-compose.prod.yml
STEP 3 — Ensure primary has wal_level=replica, max_wal_senders=5
STEP 4 — Create backend/app/core/db_routing.py:
  engine_primary, engine_replica, get_read_db(), get_write_db()
STEP 5 — Add DATABASE_REPLICA_URL to config.py (Optional, default None)
STEP 6 — Add DATABASE_REPLICA_URL to .env.example

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: docker compose -f infra/docker-compose.prod.yml config
CHECK 2: python -c "from app.core.db_routing import get_read_db, get_write_db"
CHECK 3: grep "DATABASE_REPLICA_URL" .env.example

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "infra(db): add PostgreSQL read replica with SQLAlchemy routing

- Streaming replica with pg_basebackup from primary
- db_routing.py: get_read_db() for analytics/reports, get_write_db() for mutations
- Falls back to primary if DATABASE_REPLICA_URL not set"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-07: Automated Backups + S3 + Restore Drill

```
═══════════════════════════════════════════════════════════════
PROMPT CI-07: AUTOMATED BACKUPS WITH S3 + RESTORE DRILL
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. infra/backup/ → existing backup scripts
2. CICD_INFRASTRUCTURE.md section 3A
3. .env.example → check for S3 vars

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create infra/scripts/backup-s3.sh (pg_dump + gzip + S3 upload + cleanup)
STEP 2 — Create infra/scripts/restore-drill.sh (download + restore + validate + cleanup)
STEP 3 — chmod +x both scripts
STEP 4 — Add Makefile targets: backup, restore-drill, backup-status
STEP 5 — Add S3_BUCKET to .env.example
STEP 6 — Add cron documentation to DEPLOYMENT.md

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: shellcheck infra/scripts/backup-s3.sh (or bash -n)
CHECK 2: shellcheck infra/scripts/restore-drill.sh
CHECK 3: Both scripts are executable: ls -la infra/scripts/*.sh
CHECK 4: grep "S3_BUCKET" .env.example

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "infra(backup): add automated S3 backups with weekly restore drill

- Daily pg_dump + gzip → S3 (STANDARD_IA, 30-day retention)
- Weekly restore drill: download → temp DB → validate tables → cleanup
- Makefile targets: backup, restore-drill, backup-status"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-08: OpenTelemetry APM Setup

```
═══════════════════════════════════════════════════════════════
PROMPT CI-08: OPENTELEMETRY APM + GRAFANA TEMPO
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/requirements.txt → existing deps
2. backend/app/core/config.py → settings structure
3. backend/app/main.py → startup/lifespan events
4. infra/docker-compose.monitoring.yml → current monitoring stack
5. infra/grafana/provisioning/datasources/ → existing datasources
6. CICD_INFRASTRUCTURE.md section 4A

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Add OpenTelemetry packages to requirements.txt
STEP 2 — Create backend/app/core/telemetry.py: setup_telemetry(app, engine)
STEP 3 — Add ENABLE_TRACING and OTEL_EXPORTER_ENDPOINT to config.py
STEP 4 — Call setup_telemetry in main.py (guarded by settings.ENABLE_TRACING)
STEP 5 — Create infra/tempo/tempo.yml
STEP 6 — Add tempo service to docker-compose.monitoring.yml
STEP 7 — Add Tempo datasource to Grafana provisioning
STEP 8 — Add env vars to .env.example

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: pip install succeeds for new packages
CHECK 2: python -c "from app.core.telemetry import setup_telemetry"
CHECK 3: docker compose -f infra/docker-compose.monitoring.yml config
CHECK 4: grep "ENABLE_TRACING" .env.example

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "feat(observability): add OpenTelemetry distributed tracing with Grafana Tempo

- Auto-instrument FastAPI, SQLAlchemy, Redis
- Grafana Tempo for trace storage (30-day retention)
- Trace-to-log correlation via Loki integration
- Guarded by ENABLE_TRACING feature flag"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-09: Business Metrics + Log-Based Alerting

```
═══════════════════════════════════════════════════════════════
PROMPT CI-09: BUSINESS METRICS + LOG ALERTING
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. backend/app/core/metrics.py → existing Prometheus metrics
2. backend/app/services/lms/grading_service.py → where to add grade metric
3. backend/app/services/billing.py → where to add billing metrics
4. infra/loki/loki-config.yml → current config
5. infra/grafana/dashboards/ → existing dashboards
6. CICD_INFRASTRUCTURE.md sections 4B and 4C

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/app/core/business_metrics.py with education-specific Prometheus metrics
STEP 2 — Add metric .observe()/.inc() calls to relevant service methods (lightweight, 1-line each)
STEP 3 — Create infra/grafana/dashboards/business-education.json (7 panels)
STEP 4 — Add ruler config to infra/loki/loki-config.yml
STEP 5 — Create infra/loki/rules/ecole-alerts.yml (5 alert rules)

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: python -c "from app.core.business_metrics import active_students, grade_distribution"
CHECK 2: JSON valid: python -c "import json; json.load(open('infra/grafana/dashboards/business-education.json'))"
CHECK 3: YAML valid: python -c "import yaml; yaml.safe_load(open('infra/loki/rules/ecole-alerts.yml'))"

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "feat(monitoring): add education business metrics + Loki log alerting

- Prometheus metrics: active students, grade distribution, billing revenue (MAD)
- Grafana dashboard: 7 panels for education KPIs
- Loki alerts: error rate, brute force, pool exhaustion, webhook failures, migration errors"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-10: Security Hardening

```
═══════════════════════════════════════════════════════════════
PROMPT CI-10: SECURITY — Secret Rotation + WAF + Dependabot
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. infra/nginx/nginx-prod.conf → current rate limiting, security headers
2. infra/scripts/ → existing scripts
3. .github/ → check for existing dependabot.yml
4. CICD_INFRASTRUCTURE.md sections 5A, 5B, 5C

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create infra/scripts/rotate-secrets.sh (jwt, db, redis, all)
STEP 2 — Update nginx-prod.conf: per-user rate limiting, WAF rules, per-endpoint body limits
STEP 3 — Create .github/dependabot.yml (pip, npm, docker, github-actions)
STEP 4 — Create .github/workflows/dependabot-automerge.yml
STEP 5 — Add Makefile targets: rotate-jwt, rotate-db, rotate-redis, rotate-all

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: bash -n infra/scripts/rotate-secrets.sh
CHECK 2: YAML valid for dependabot.yml and automerge workflow
CHECK 3: Nginx config syntax check: grep "limit_req_zone" infra/nginx/nginx-prod.conf
CHECK 4: All Makefile targets: grep "rotate-" Makefile

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "security: add secret rotation, WAF rules, Dependabot vulnerability management

- Zero-downtime secret rotation (JWT dual-key, DB, Redis)
- Nginx WAF: SQL injection, XSS, path traversal blocking
- Per-user JWT rate limiting + per-endpoint body size limits
- Dependabot: pip/npm/docker/actions with auto-merge for patches"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-11: Blue-Green Deployment

```
═══════════════════════════════════════════════════════════════
PROMPT CI-11: BLUE-GREEN DEPLOYMENT
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. infra/docker-compose.prod.yml → services and networks
2. infra/nginx/nginx-prod.conf → current upstream config
3. infra/scripts/deploy.sh → current deployment logic
4. CICD_INFRASTRUCTURE.md section 2C

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create infra/docker-compose.blue.yml (backend-blue, worker-blue)
STEP 2 — Create infra/docker-compose.green.yml (backend-green, worker-green)
STEP 3 — Create infra/scripts/blue-green-deploy.sh (switch logic)
STEP 4 — Create infra/nginx/upstream.conf
STEP 5 — Update nginx-prod.conf to include upstream.conf
STEP 6 — Add Makefile targets: deploy-blue-green, deploy-rollback, deploy-status

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: docker compose -f infra/docker-compose.blue.yml config
CHECK 2: docker compose -f infra/docker-compose.green.yml config
CHECK 3: bash -n infra/scripts/blue-green-deploy.sh
CHECK 4: grep "backend_active" infra/nginx/upstream.conf

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "infra(deploy): add blue-green deployment with instant rollback

- Dual-stack compose files (blue/green)
- Nginx upstream switching for zero-downtime deploys
- Health check gated traffic switch (<5s rollback)
- Makefile: deploy-blue-green, deploy-rollback, deploy-status"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

### CI-12: Developer Onboarding + Documentation

```
═══════════════════════════════════════════════════════════════
PROMPT CI-12: DEV ONBOARDING + API DOCS GENERATION
═══════════════════════════════════════════════════════════════

── PHASE 1: ANALYZE ──────────────────────────────────────────

READ:
1. Makefile → existing targets
2. .env.example → current env vars
3. backend/app/main.py → FastAPI app instance for OpenAPI
4. CICD_INFRASTRUCTURE.md sections 6A and 6C

── PHASE 2: EXECUTE ──────────────────────────────────────────

STEP 1 — Create backend/app/scripts/seed_demo.py:
  Idempotent async script that creates:
  - 1 demo school (Lycée Mohammed V, LMV-001, Casablanca)
  - Users: 1 admin, 3 teachers, 2 parents, 5 students
  - 3 classes, 5 courses, enrollments, teacher assignments
  - 1 billing plan (500 MAD/month)

STEP 2 — Add Makefile targets: dev-init, dev-reset, seed-demo

STEP 3 — Create .github/workflows/docs.yml:
  - On push to main when backend/app/** changes
  - Export OpenAPI spec → build Redoc static site → deploy to GitHub Pages

STEP 4 — Add Makefile targets: docs, docs-schema

── PHASE 3: VERIFY ───────────────────────────────────────────

CHECK 1: python -c "from app.scripts.seed_demo import *" (import check)
CHECK 2: grep "dev-init\|dev-reset\|seed-demo" Makefile
CHECK 3: YAML valid for docs.yml
CHECK 4: grep "docs\|docs-schema" Makefile

── GIT (conditional) ─────────────────────────────────────────

COMMIT_MSG: "feat(dx): add dev-init one-command setup, demo seed data, API docs generation

- seed_demo.py: Lycée Mohammed V demo school with full sample data
- make dev-init: .env → build → migrate → seed → start (3 min onboarding)
- Auto-deploy Redoc API docs to GitHub Pages on merge to main
- make docs + make docs-schema for local documentation"

If CODEX_ENV=true: git add -A && git commit -m "<COMMIT_MSG>"
Else: echo "SKIP GIT: Claude Code mode"

═══════════════════════════════════════════════════════════════
```

---

## ============================================================
## END OF EXECUTION PROMPTS
## ============================================================

## Summary Table

| # | ID | Domain | Focus | Est. Tests | Est. Time |
|---|----|--------|-------|-----------|-----------|
| 1 | T-01 | Testing | Infrastructure setup | 0 | 20 min |
| 2 | T-02 | Testing | Domain value objects | ~45 | 15 min |
| 3 | T-03 | Testing | Model validators + properties | ~60 | 20 min |
| 4 | T-04 | Testing | Permissions + ABAC | ~40 | 15 min |
| 5 | T-05 | Testing | LMS services | ~65 | 25 min |
| 6 | T-06 | Testing | Billing + Auth + Attendance | ~60 | 25 min |
| 7 | T-07 | Testing | Communication + School + Others | ~50 | 20 min |
| 8 | T-08 | Testing | API integration tests | ~80 | 30 min |
| 9 | T-09 | Testing | DB repository tests | ~40 | 20 min |
| 10 | T-10 | Testing | RBAC + ABAC security matrix | ~120 | 30 min |
| 11 | T-11 | Testing | Edge cases + boundaries | ~80 | 25 min |
| 12 | T-12 | Testing | Performance + contracts | ~50 | 20 min |
| 13 | T-13 | Testing | Coverage gap fill | ~80 | 30 min |
| 14 | CI-01 | CI/CD | Pre-commit hooks | — | 15 min |
| 15 | CI-02 | CI/CD | Pipeline hardening | — | 30 min |
| 16 | CI-03 | CI/CD | Docker optimization | — | 20 min |
| 17 | CI-04 | CI/CD | Container registry | — | 20 min |
| 18 | CI-05 | Infra | PgBouncer | — | 15 min |
| 19 | CI-06 | Infra | Read replica | — | 25 min |
| 20 | CI-07 | Infra | Automated backups | — | 20 min |
| 21 | CI-08 | Infra | OpenTelemetry APM | — | 25 min |
| 22 | CI-09 | Infra | Business metrics + alerts | — | 30 min |
| 23 | CI-10 | Security | Secret rotation + WAF | — | 30 min |
| 24 | CI-11 | Infra | Blue-green deployment | — | 25 min |
| 25 | CI-12 | DX | Dev onboarding + docs | — | 25 min |

**Total: 25 prompts, ~770 new tests, ~9 hours estimated execution time.**
