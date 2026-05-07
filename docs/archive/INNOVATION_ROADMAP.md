# Ecole Platform Innovation Roadmap

**Status:** Blueprint for Autonomous Development — Decisions Finalized
**Created:** April 2026
**Target Environment:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL
**Execution Model:** Sequential Prompt Chain (ANALYZE → EXECUTE → VERIFY → GIT)

---

## Finalized Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Implementation Order** | Impact-first | Micro-École → Budget → Skills → Compliance → Sync → Financial Health |
| **Local-First Sync depth** | Full backend infrastructure | Complete sync queue, conflict resolution, device management APIs — ready for Flutter/React offline layer |
| **MEN seed data** | Sample: Math + Arabic for Collège 3ème | ~50 objectives, enough for convincing demo. Schools add more via API |
| **File format** | Single roadmap file | INNOVATION_ROADMAP.md as master document |

### Recommended Execution Order (Impact-First)

```
Priority 1 ★★★  MICRO-01→04   Micro-École         Strongest differentiator, "Blue Ocean" market
Priority 2 ★★★  BUDGET-01→04  Class Micro-Budget   Quick win, clean approval workflow
Priority 3 ★★☆  SKILL-01→04   Life Skills Passport High parent appeal, rule-based engine
Priority 4 ★★☆  COMPLY-01→04  MEN Compliance       Practical for inspections, seed Math+Arabic
Priority 5 ★☆☆  SYNC-01→04    Local-First Sync     Complex but foundational for offline
Priority 6 ★☆☆  HEALTH-01→04  Financial Health     Leverages existing billing data, do last
```

---

## Table of Contents
1. [Overview & Architecture](#overview--architecture)
2. [Feature Matrix](#feature-matrix)
3. [Global Instructions & Conventions](#global-instructions--conventions)
4. [Feature 1: Micro-École Module (MICRO-01 → MICRO-04)](#feature-1-micro-école-module)
5. [Feature 2: Local-First / Offline Mode (SYNC-01 → SYNC-04)](#feature-2-local-first--offline-mode)
6. [Feature 3: Life Skills Passport (SKILL-01 → SKILL-04)](#feature-3-life-skills-passport)
7. [Feature 4: MEN Compliance Checker (COMPLY-01 → COMPLY-04)](#feature-4-men-compliance-checker)
8. [Feature 5: Class Micro-Budget (BUDGET-01 → BUDGET-04)](#feature-5-class-micro-budget)
9. [Feature 6: Financial Health Dashboard (HEALTH-01 → HEALTH-04)](#feature-6-financial-health-dashboard)
10. [Execution Checklist](#execution-checklist)
11. [Dependency Order & Mega-Prompts](#dependency-order--mega-prompts)
12. [Summary & Success Criteria](#summary--success-criteria)

---

## Overview & Architecture

### Vision
Six innovative backend features for **Ecole Platform**, a K-12 EdTech SaaS targeting Moroccan schools. These features extend core functionality (user management, billing, academics) with specialized capabilities for informal education, offline resilience, behavioral tracking, regulatory compliance, decentralized budgeting, and financial analytics.

### Design Principles
- **Backend-Only:** No mobile/web UI changes. All features delivered via REST APIs.
- **3-Tier Architecture:** Router → Service → Repository layer, every time.
- **Moroccan-Native:** Grades 0-20, MAD currency, +212 phones, Africa/Casablanca timezone, trilingual support (ar/fr/en).
- **Type-Safe:** Full type hints, Pydantic schemas, SQLAlchemy Mapped[] columns.
- **Testable:** pytest + factories (AsyncSQLAlchemyFactory) + testcontainers. RBAC boundary checks mandatory.
- **Auditable:** Domain events (frozen dataclass extending DomainEvent), permission checks at every endpoint, request logging.
- **Autonomous:** Every prompt runnable independently or sequentially with identical output (CODEX or Claude Code).

### Features at a Glance

| # | Feature | Scope | Tables | Endpoints | Est. Time |
|---|---------|-------|--------|-----------|-----------|
| 1 | Micro-École | Informal education (الروض) for small groups | 6 | 14 | 3h |
| 2 | Local-First Sync | Offline-capable with deferred sync & conflict resolution | 4 | 10 | 3h |
| 3 | Life Skills Passport | Behavioral milestone tracking from activity logs | 4 | 12 | 3h |
| 4 | MEN Compliance | Curriculum coverage against Moroccan standards | 4 | 12 | 2.5h |
| 5 | Class Micro-Budget | Decentralized financial management per class/teacher | 4 | 14 | 3h |
| 6 | Financial Health | KPI dashboard (retention, cashflow, cost analysis) | 4 | 12 | 2.5h |
| — | **TOTAL** | — | **26** | **74** | **~17h** |

---

## Feature Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│ MICRO-01: Models & Migrations    │ MICRO-02: Repo & Service      │
│ 6 models, 1 migration, 12 perms  │ 6 schemas, 1 service          │
├─────────────────────────────────────────────────────────────────┤
│ MICRO-03: API Endpoints          │ MICRO-04: Tests & Factories   │
│ 14 routes, OpenAPI tags          │ ~60 tests, full RBAC          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ SYNC-01: Models & Migrations     │ SYNC-02: Repo & Service       │
│ 4 models, 1 migration, 8 perms   │ 4 schemas, 1 service          │
├─────────────────────────────────────────────────────────────────┤
│ SYNC-03: API Endpoints           │ SYNC-04: Tests & Factories    │
│ 10 routes, conflict resolution   │ ~55 tests, sync scenarios     │
└─────────────────────────────────────────────────────────────────┘

[Repeat pattern for SKILL, COMPLY, BUDGET, HEALTH features...]
```

---

## Global Instructions & Conventions

### 1. Environment Detection & Git Behavior

```bash
CODEX_ENV="${CODEX_ENV:-false}"

# Every prompt must conditionally commit:
COMMIT_MSG="feat(domain): <specific change>"
if [ "$CODEX_ENV" = "true" ]; then
  git add -A && git commit -m "$COMMIT_MSG"
else
  echo "SKIP GIT: Claude Code mode — user handles git manually"
fi
```

### 2. Error Handling
- **Stop immediately** on any error (no auto-fix attempts).
- Print full traceback and exit with status code.
- Do **NOT** proceed to the next step until issue resolved.
- User must manually investigate before rerunning prompt.

### 3. File Conventions

```
backend/
├── app/
│   ├── models/
│   │   ├── micro_school.py          # Feature 1 models
│   │   ├── sync_queue.py            # Feature 2 models
│   │   ├── skill_passport.py        # Feature 3 models
│   │   ├── men_compliance.py        # Feature 4 models
│   │   ├── budget.py                # Feature 5 models
│   │   └── financial_health.py      # Feature 6 models
│   ├── repositories/
│   │   ├── micro_school.py
│   │   ├── sync_queue.py
│   │   └── ...
│   ├── services/
│   │   ├── micro_school_service.py
│   │   └── ...
│   ├── schemas/
│   │   ├── micro_school.py
│   │   └── ...
│   ├── api/v1/
│   │   ├── micro_school.py          # Feature 1 endpoints
│   │   ├── sync.py                  # Feature 2 endpoints
│   │   └── ...
│   ├── core/
│   │   ├── permissions.py           # ALL permission constants
│   │   ├── dependencies.py
│   │   ├── response.py
│   │   └── exceptions.py
│   └── domain/
│       └── events/
│           ├── micro_school.py
│           └── ...
├── alembic/
│   └── versions/                    # One .py file per feature per prompt X-01
├── tests/
│   ├── factories/
│   │   ├── micro_school.py
│   │   └── ...
│   ├── unit/services/
│   │   ├── test_micro_school_service.py
│   │   └── ...
│   ├── integration/api/
│   │   ├── test_micro_school_api.py
│   │   └── ...
│   └── security/
│       ├── test_micro_school_rbac.py
│       └── ...
```

### 4. Import Patterns (copy-paste ready)

```python
# Models
from app.models.micro_school import MicroSchool, MicroGroup, MicroEnrollment
from app.models.sync_queue import SyncQueue, SyncConflict, SyncDevice
from app.models.skill_passport import SkillDimension, SkillMilestone, SkillProgress, SkillPassport
from app.models.men_compliance import MenCurriculum, MenObjective, CurriculumMapping
from app.models.budget import MicroBudget, BudgetAllocation, BudgetRequest, BudgetTransaction
from app.models.financial_health import RetentionMetric, CashflowForecast, CostPerStudent, FinancialSnapshot

# Repositories
from app.repositories.micro_school import MicroSchoolRepository, MicroGroupRepository
from app.repositories.sync_queue import SyncQueueRepository
from app.repositories.skill_passport import SkillProgressRepository
# ... etc

# Services
from app.services.micro_school_service import MicroSchoolService
from app.services.sync_service import SyncService
# ... etc

# Schemas
from app.schemas.micro_school import MicroSchoolRequest, MicroSchoolResponse, MicroGroupResponse
# ... etc

# Permissions
from app.core.permissions import (
    PERM_MICRO_SCHOOL_CREATE,
    PERM_MICRO_SCHOOL_READ,
    PERM_SYNC_PUSH,
    PERM_SKILL_PASSPORT_READ,
    # ... etc
)

# Core utilities
from app.core.dependencies import requires_permission, get_db, get_client_ip
from app.core.response import success_response, list_response
from app.core.exceptions import NotFoundError, ConflictError, ValidationError, PermissionDeniedError
from app.domain.events import DomainEvent

# Testing
from tests.factories.micro_school import MicroSchoolFactory, MicroGroupFactory
from sqlalchemy.ext.asyncio import AsyncSession
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
```

### 5. Moroccan Data Convention (Test Fixtures)

```python
# Grades: 0-20 scale
GOOD_GRADE = 16  # Excellent
AVERAGE_GRADE = 12  # Acceptable
POOR_GRADE = 5  # Needs improvement

# Currency: always "MAD"
MONTHLY_PAYMENT = Decimal("500.00")  # 500 MAD
ANNUAL_TUITION = Decimal("15000.00")  # 15,000 MAD

# Phones: +212XXXXXXXXX
PARENT_PHONE = "+212612345678"

# Timezone: Africa/Casablanca
import pytz
TZ = pytz.timezone("Africa/Casablanca")

# Languages: ar, fr, en
LANGUAGES = ["ar", "fr", "en"]

# Names
NAMES_AR = ["أحمد", "فاطمة", "يوسف", "خديجة", "محمد"]
NAMES_FR = ["Youssef", "Fatima", "Ahmed", "Khadija", "Mohammed"]

# Cities
CITIES = ["Casablanca", "Rabat", "Marrakech", "Fès", "Tanger", "Agadir"]
```

### 6. Standard Method Signatures in Services

```python
# All async
async def create_{entity}(self, school_id: UUID, data: CreateRequest, db: AsyncSession) -> Response
async def get_{entity}(self, entity_id: UUID, db: AsyncSession) -> Response | None
async def list_{entity}(self, school_id: UUID, filters: dict, db: AsyncSession) -> list[Response]
async def update_{entity}(self, entity_id: UUID, data: UpdateRequest, db: AsyncSession) -> Response
async def delete_{entity}(self, entity_id: UUID, db: AsyncSession) -> bool

# Domain logic
async def compute_{metric}(self, school_id: UUID, db: AsyncSession) -> MetricResponse
async def validate_{rule}(self, data: DataClass) -> bool | ValidationError
```

### 7. Endpoint Response Pattern

```python
# Success responses
@router.post("/", status_code=201, tags=["feature"])
async def create_item(
    request: CreateRequest,
    db: AsyncSession = Depends(get_db),
    user = Depends(requires_permission("PERM_FEATURE_CREATE")),
) -> dict:
    item = await service.create_item(user.school_id, request, db)
    return success_response(item, status_code=201)

# List responses
@router.get("/", tags=["feature"])
async def list_items(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    user = Depends(requires_permission("PERM_FEATURE_READ")),
) -> dict:
    items, total = await service.list_items(user.school_id, skip, limit, db)
    return list_response(items, total=total, skip=skip, limit=limit)

# Error responses
@router.delete("/{id}", tags=["feature"])
async def delete_item(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    user = Depends(requires_permission("PERM_FEATURE_MANAGE")),
) -> dict:
    success = await service.delete_item(id, db)
    if not success:
        raise NotFoundError(f"Item {id} not found")
    return success_response({"deleted": True})
```

### 8. Domain Events Pattern

```python
from dataclasses import dataclass
from app.domain.events import DomainEvent
from uuid import UUID

@dataclass(frozen=True)
class MicroSchoolCreatedEvent(DomainEvent):
    school_id: UUID
    educator_id: UUID
    name: str
    neighborhood: str

    def event_type(self) -> str:
        return "micro_school.created"

# Emit during service
async def create_micro_school(self, school_id: UUID, data: CreateRequest, db: AsyncSession):
    micro_school = MicroSchool(...)
    db.add(micro_school)
    await db.commit()

    self.event_bus.emit(MicroSchoolCreatedEvent(
        school_id=micro_school.id,
        educator_id=data.educator_id,
        name=data.name,
        neighborhood=data.neighborhood,
    ))

    return MicroSchoolResponse.from_orm(micro_school)
```

### 9. Test Pattern (pytest + factories)

```python
@pytest.mark.asyncio
class TestMicroSchoolService:
    @pytest_asyncio.fixture
    async def setup(self):
        # Testcontainer PostgreSQL, AsyncSession
        pass

    async def test_create_micro_school_success(self, setup):
        # Arrange
        factory = MicroSchoolFactory()
        request = MicroSchoolRequest(...)

        # Act
        result = await service.create_micro_school(school_id, request, db)

        # Assert
        assert result.id is not None
        assert result.name == request.name
        assert len(result.id) == 36  # UUID format

    async def test_create_micro_school_duplicate_raises_conflict(self, setup):
        # Arrange
        existing = await MicroSchoolFactory.create_async(db, name="Test")
        request = MicroSchoolRequest(name="Test", ...)

        # Act & Assert
        with pytest.raises(ConflictError):
            await service.create_micro_school(school_id, request, db)

    async def test_rbac_educator_cannot_list_other_school(self, setup):
        # Verify permission check
        with pytest.raises(PermissionDeniedError):
            await service.list_micro_schools(OTHER_SCHOOL_ID, db)
```

### 10. Permission Format

```python
# In app/core/permissions.py
PERM_MICRO_SCHOOL_CREATE = "PERM-MICRO:school:create"
PERM_MICRO_SCHOOL_READ = "PERM-MICRO:school:read"
PERM_MICRO_SCHOOL_MANAGE = "PERM-MICRO:school:manage"

PERM_SYNC_PUSH = "PERM-SYNC:data:push"
PERM_SYNC_PULL = "PERM-SYNC:data:pull"
PERM_SYNC_CONFLICT_RESOLVE = "PERM-SYNC:conflict:resolve"

# Add to ROLE_PERMISSIONS mapping
ROLE_PERMISSIONS = {
    RoleCode.EDUCATOR: [
        PERM_MICRO_SCHOOL_CREATE,
        PERM_MICRO_SCHOOL_READ,
        PERM_MICRO_SCHOOL_MANAGE,
        PERM_MICRO_GROUP_CREATE,
        # ...
    ],
    RoleCode.PARENT: [
        PERM_MICRO_PROGRESS_READ,
        PERM_MICRO_PAYMENT_READ,
        PERM_SYNC_PULL,
        # ...
    ],
}
```

---

## Feature 1: Micro-École Module

**Domain:** Informal education (الروض) — kindergarten/preschool management for small groups.
**Scope:** New role (EDUCATOR), 6 models, 14 endpoints, 12 permissions.
**Time Estimate:** 3 hours

### 1.1 Models & Data Structure

#### Table: `micro_schools`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| educator_id | UUID | FK users.id | Educator who created school |
| name | String(200) | NOT NULL | e.g., "روضة الحي الجديد" |
| neighborhood | String(200) | NOT NULL | الحي / district |
| city | String(100) | NOT NULL | Casablanca, Rabat, etc. |
| phone | String(20) | NOT NULL | +212XXXXXXXXX |
| max_capacity | Integer | default 20, CHECK > 0 | |
| status | Enum | active/suspended/closed | |
| created_at | DateTime | DEFAULT NOW() | |
| updated_at | DateTime | DEFAULT NOW() | |

#### Table: `micro_groups`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| micro_school_id | UUID | FK CASCADE | |
| name | String(100) | default "المجموعة" | |
| age_range_min | Integer | CHECK 2-6 | |
| age_range_max | Integer | CHECK 2-6 | |
| created_at | DateTime | DEFAULT NOW() | |
| updated_at | DateTime | DEFAULT NOW() | |

#### Table: `micro_enrollments`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| micro_group_id | UUID | FK CASCADE | |
| child_name | String(200) | NOT NULL | |
| parent_id | UUID | FK users.id | |
| date_of_birth | Date | NOT NULL | |
| enrolled_at | DateTime | DEFAULT NOW() | |
| status | Enum | active/withdrawn | |

#### Table: `micro_payments`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| micro_school_id | UUID | FK CASCADE | |
| parent_id | UUID | FK users.id | |
| child_enrollment_id | UUID | FK micro_enrollments.id | |
| amount | Numeric(10,2) | CHECK > 0 | |
| currency | String(3) | default "MAD" | |
| period_type | Enum | weekly/monthly | |
| period_start | Date | NOT NULL | |
| period_end | Date | NOT NULL | |
| paid_at | DateTime | nullable | |
| status | Enum | pending/paid/overdue | |

#### Table: `micro_resources`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| title | String(300) | NOT NULL | |
| description | Text | nullable | |
| resource_type | Enum | activity_sheet/song/game/lesson_plan | |
| age_group | String(20) | NOT NULL | "2-3", "4-6" |
| language | String(5) | default "ar" | ar/fr/en |
| file_url | String(500) | nullable | |
| is_premium | Boolean | default false | |
| created_at | DateTime | DEFAULT NOW() | |

#### Table: `micro_progress_logs`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| micro_enrollment_id | UUID | FK CASCADE | |
| educator_id | UUID | FK users.id | |
| date | Date | NOT NULL | |
| note | Text | NOT NULL | |
| photo_url | String(500) | nullable | |
| milestone_tag | String(50) | nullable | "alphabet_learned", etc. |
| created_at | DateTime | DEFAULT NOW() | |

### 1.2 Permissions (12 total)

```python
PERM_MICRO_SCHOOL_CREATE = "PERM-MICRO:school:create"
PERM_MICRO_SCHOOL_READ = "PERM-MICRO:school:read"
PERM_MICRO_SCHOOL_MANAGE = "PERM-MICRO:school:manage"
PERM_MICRO_GROUP_CREATE = "PERM-MICRO:group:create"
PERM_MICRO_GROUP_READ = "PERM-MICRO:group:read"
PERM_MICRO_ENROLLMENT_CREATE = "PERM-MICRO:enrollment:create"
PERM_MICRO_ENROLLMENT_READ = "PERM-MICRO:enrollment:read"
PERM_MICRO_PAYMENT_CREATE = "PERM-MICRO:payment:create"
PERM_MICRO_PAYMENT_READ = "PERM-MICRO:payment:read"
PERM_MICRO_RESOURCE_READ = "PERM-MICRO:resource:read"
PERM_MICRO_RESOURCE_MANAGE = "PERM-MICRO:resource:manage"
PERM_MICRO_PROGRESS_CREATE = "PERM-MICRO:progress:create"
PERM_MICRO_PROGRESS_READ = "PERM-MICRO:progress:read"

# EDUCATOR role (new) gets all MICRO perms
# PARENT gets PERM_MICRO_PROGRESS_READ, PERM_MICRO_PAYMENT_READ
# ADMIN/SUPER gets PERM_MICRO_SCHOOL_READ, PERM_MICRO_SCHOOL_MANAGE
```

### 1.3 API Endpoints (14 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| POST | /micro-schools | 201 | PERM_MICRO_SCHOOL_CREATE | Create micro-school |
| GET | /micro-schools | 200 | PERM_MICRO_SCHOOL_READ | List educator's schools |
| GET | /micro-schools/{id} | 200 | PERM_MICRO_SCHOOL_READ | School detail |
| PATCH | /micro-schools/{id} | 200 | PERM_MICRO_SCHOOL_MANAGE | Update school |
| POST | /micro-schools/{id}/groups | 201 | PERM_MICRO_GROUP_CREATE | Create group |
| GET | /micro-schools/{id}/groups | 200 | PERM_MICRO_GROUP_READ | List groups |
| POST | /micro-groups/{id}/enrollments | 201 | PERM_MICRO_ENROLLMENT_CREATE | Enroll child |
| GET | /micro-groups/{id}/enrollments | 200 | PERM_MICRO_ENROLLMENT_READ | List children in group |
| POST | /micro-payments | 201 | PERM_MICRO_PAYMENT_CREATE | Record payment |
| GET | /micro-payments | 200 | PERM_MICRO_PAYMENT_READ | List payments |
| GET | /micro-resources | 200 | PERM_MICRO_RESOURCE_READ | Browse resource library |
| POST | /micro-progress | 201 | PERM_MICRO_PROGRESS_CREATE | Log child progress |
| GET | /micro-progress/child/{enrollment_id} | 200 | PERM_MICRO_PROGRESS_READ | Child progress history |
| GET | /micro-progress/daily | 200 | PERM_MICRO_PROGRESS_READ | Daily summary for parents |

### 1.4 Service Methods

```python
class MicroSchoolService:
    async def create_micro_school(self, educator_id: UUID, data: CreateMicroSchoolRequest, db: AsyncSession) -> MicroSchoolResponse
    async def get_micro_school(self, school_id: UUID, db: AsyncSession) -> MicroSchoolResponse | None
    async def list_micro_schools(self, educator_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[MicroSchoolResponse], int]
    async def update_micro_school(self, school_id: UUID, data: UpdateMicroSchoolRequest, db: AsyncSession) -> MicroSchoolResponse
    async def delete_micro_school(self, school_id: UUID, db: AsyncSession) -> bool

class MicroGroupService:
    async def create_group(self, school_id: UUID, data: CreateMicroGroupRequest, db: AsyncSession) -> MicroGroupResponse
    async def list_groups(self, school_id: UUID, db: AsyncSession) -> list[MicroGroupResponse]

class MicroEnrollmentService:
    async def enroll_child(self, group_id: UUID, data: CreateMicroEnrollmentRequest, db: AsyncSession) -> MicroEnrollmentResponse
    async def list_enrollments(self, group_id: UUID, db: AsyncSession) -> list[MicroEnrollmentResponse]

class MicroPaymentService:
    async def record_payment(self, school_id: UUID, data: CreateMicroPaymentRequest, db: AsyncSession) -> MicroPaymentResponse
    async def list_payments(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[MicroPaymentResponse], int]
    async def mark_overdue(self, db: AsyncSession) -> int  # Cron task

class MicroResourceService:
    async def list_resources(self, language: str, age_group: str | None, skip: int, limit: int, db: AsyncSession) -> tuple[list[MicroResourceResponse], int]

class MicroProgressService:
    async def log_progress(self, enrollment_id: UUID, data: CreateMicroProgressRequest, db: AsyncSession) -> MicroProgressResponse
    async def get_child_progress(self, enrollment_id: UUID, days: int = 30, db: AsyncSession) -> list[MicroProgressResponse]
    async def daily_summary(self, parent_id: UUID, db: AsyncSession) -> DailySummaryResponse
```

---

## Feature 2: Local-First / Offline Mode

**Domain:** Offline-capable sync engine with deferred writes and conflict resolution.
**Scope:** 4 models, 10 endpoints, 8 permissions.
**Time Estimate:** 3 hours

### 2.1 Models & Data Structure

#### Table: `sync_devices`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| device_name | String(200) | NOT NULL | "Laptop-Ahmed-123" |
| device_type | Enum | local_server/mobile/browser | |
| last_seen_at | DateTime | NOT NULL | |
| firmware_version | String(50) | nullable | |
| is_active | Boolean | default true | |
| created_at | DateTime | DEFAULT NOW() | |

#### Table: `sync_queue`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| device_id | UUID | FK CASCADE | |
| school_id | UUID | FK CASCADE | |
| entity_type | String(100) | NOT NULL | "attendance", "grade", etc. |
| entity_id | UUID | NOT NULL | |
| operation | Enum | create/update/delete | |
| payload | JSONB | NOT NULL | Change data |
| created_at | DateTime | NOT NULL | Client timestamp |
| synced_at | DateTime | nullable | Server confirmation |
| status | Enum | pending/synced/conflict/failed | |
| retry_count | Integer | default 0, CHECK <= 5 | |

#### Table: `sync_conflicts`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| queue_item_id | UUID | FK CASCADE | |
| school_id | UUID | FK CASCADE | |
| entity_type | String(100) | NOT NULL | |
| entity_id | UUID | NOT NULL | |
| client_payload | JSONB | NOT NULL | What device sent |
| server_payload | JSONB | NOT NULL | Current server state |
| resolution | Enum | pending/client_wins/server_wins/manual | |
| resolved_by | UUID | FK users.id nullable | |
| resolved_at | DateTime | nullable | |

#### Table: `sync_checkpoints`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| device_id | UUID | FK CASCADE | |
| school_id | UUID | FK CASCADE | |
| last_sync_at | DateTime | NOT NULL | |
| last_entity_type | String(100) | NOT NULL | |
| last_entity_id | UUID | NOT NULL | |
| records_synced | Integer | default 0 | |

### 2.2 Permissions (8 total)

```python
PERM_SYNC_DEVICE_REGISTER = "PERM-SYNC:device:register"
PERM_SYNC_DEVICE_READ = "PERM-SYNC:device:read"
PERM_SYNC_DEVICE_MANAGE = "PERM-SYNC:device:manage"
PERM_SYNC_PUSH = "PERM-SYNC:data:push"
PERM_SYNC_PULL = "PERM-SYNC:data:pull"
PERM_SYNC_CONFLICT_READ = "PERM-SYNC:conflict:read"
PERM_SYNC_CONFLICT_RESOLVE = "PERM-SYNC:conflict:resolve"
PERM_SYNC_STATUS_READ = "PERM-SYNC:status:read"

# ADMIN/DIRECTOR: all perms
# TEACHER: push, pull, status_read
# PARENT: pull, status_read
```

### 2.3 API Endpoints (10 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| POST | /sync/devices | 201 | PERM_SYNC_DEVICE_REGISTER | Register device |
| GET | /sync/devices | 200 | PERM_SYNC_DEVICE_READ | List devices |
| POST | /sync/push | 202 | PERM_SYNC_PUSH | Upload offline changes |
| POST | /sync/pull | 200 | PERM_SYNC_PULL | Download server changes |
| GET | /sync/status | 200 | PERM_SYNC_STATUS_READ | Sync status for device |
| GET | /sync/conflicts | 200 | PERM_SYNC_CONFLICT_READ | List unresolved conflicts |
| POST | /sync/conflicts/{id}/resolve | 200 | PERM_SYNC_CONFLICT_RESOLVE | Resolve conflict |
| GET | /sync/checkpoints | 200 | PERM_SYNC_DEVICE_READ | List checkpoints |
| POST | /sync/checkpoint | 201 | PERM_SYNC_PUSH | Create checkpoint |
| GET | /sync/health | 200 | PERM_SYNC_STATUS_READ | Sync service health |

### 2.4 Service Methods

```python
class SyncService:
    async def register_device(self, school_id: UUID, data: RegisterDeviceRequest, db: AsyncSession) -> SyncDeviceResponse
    async def push_changes(self, device_id: UUID, payload: PushPayload, db: AsyncSession) -> PushResponse  # Enqueues items, handles conflicts
    async def pull_changes(self, device_id: UUID, since_checkpoint: str | None, db: AsyncSession) -> PullResponse  # Returns items since checkpoint
    async def get_sync_status(self, device_id: UUID, db: AsyncSession) -> SyncStatusResponse
    async def list_conflicts(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[SyncConflictResponse], int]
    async def resolve_conflict(self, conflict_id: UUID, resolution: str, db: AsyncSession) -> SyncConflictResponse
    async def process_queue_item(self, item_id: UUID, db: AsyncSession) -> QueueItemResponse  # Background job
    async def get_device_health(self, device_id: UUID, db: AsyncSession) -> HealthResponse
```

---

## Feature 3: Life Skills Passport

**Domain:** Behavioral competency tracking based on platform usage logs.
**Scope:** 4 models, 12 endpoints, 8 permissions.
**Time Estimate:** 3 hours

### 3.1 Models & Data Structure

#### Table: `skill_dimensions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| code | String(50) | UNIQUE | autonomy, regularity, collaboration, curiosity, perseverance |
| name_fr | String(200) | NOT NULL | "Autonomie" |
| name_ar | String(200) | NOT NULL | "الاستقلالية" |
| name_en | String(200) | NOT NULL | "Autonomy" |
| description_fr | Text | nullable | |
| icon | String(50) | nullable | "autonomy-icon" |
| display_order | Integer | NOT NULL | Sort order |
| is_active | Boolean | default true | |

#### Table: `skill_milestones`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| dimension_id | UUID | FK CASCADE | |
| code | String(100) | NOT NULL | "autonomy_level_1" |
| name_fr | String(200) | NOT NULL | |
| name_ar | String(200) | NOT NULL | |
| level | Integer | CHECK 1-5 | |
| rule_config | JSONB | NOT NULL | `{"metric": "modules_without_help", "threshold": 5, "period_days": 30}` |
| badge_icon | String(50) | nullable | |
| is_active | Boolean | default true | |

#### Table: `skill_progress`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| student_id | UUID | FK CASCADE | |
| school_id | UUID | FK CASCADE | |
| milestone_id | UUID | FK CASCADE | |
| unlocked_at | DateTime | nullable | |
| current_value | Float | default 0 | Progress toward threshold (0-100%) |
| status | Enum | locked/in_progress/unlocked | |
| evidence | JSONB | nullable | `{"sessions_completed": 12, "on_time_submissions": 8}` |
| academic_year_id | UUID | FK | |
| UNIQUE | (student_id, milestone_id, academic_year_id) | | |

#### Table: `skill_passports`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| student_id | UUID | FK CASCADE | |
| school_id | UUID | FK CASCADE | |
| academic_year_id | UUID | FK | |
| generated_at | DateTime | NOT NULL | |
| pdf_url | String(500) | nullable | |
| total_milestones | Integer | NOT NULL | |
| unlocked_milestones | Integer | NOT NULL | |
| overall_score | Float | CHECK 0-100 | Percentage |
| UNIQUE | (student_id, academic_year_id) | | |

### 3.2 Permissions (8 total)

```python
PERM_SKILL_DIMENSION_READ = "PERM-SKILL:dimension:read"
PERM_SKILL_DIMENSION_MANAGE = "PERM-SKILL:dimension:manage"
PERM_SKILL_MILESTONE_READ = "PERM-SKILL:milestone:read"
PERM_SKILL_MILESTONE_MANAGE = "PERM-SKILL:milestone:manage"
PERM_SKILL_PROGRESS_READ = "PERM-SKILL:progress:read"
PERM_SKILL_PROGRESS_EVALUATE = "PERM-SKILL:progress:evaluate"
PERM_SKILL_PASSPORT_READ = "PERM-SKILL:passport:read"
PERM_SKILL_PASSPORT_GENERATE = "PERM-SKILL:passport:generate"

# TEACHER/DIRECTOR: evaluate + read progress
# PARENT/STUDENT: read progress + passport
# ADMIN: manage dimensions/milestones
```

### 3.3 API Endpoints (12 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| GET | /skills/dimensions | 200 | PERM_SKILL_DIMENSION_READ | List dimensions |
| POST | /skills/dimensions | 201 | PERM_SKILL_DIMENSION_MANAGE | Create dimension (ADMIN) |
| GET | /skills/milestones | 200 | PERM_SKILL_MILESTONE_READ | List milestones, filter by dimension |
| POST | /skills/milestones | 201 | PERM_SKILL_MILESTONE_MANAGE | Create milestone (ADMIN) |
| GET | /skills/progress/student/{student_id} | 200 | PERM_SKILL_PROGRESS_READ | Student progress detail |
| POST | /skills/evaluate/{student_id} | 202 | PERM_SKILL_PROGRESS_EVALUATE | Trigger evaluation engine |
| GET | /skills/passport/{student_id} | 200 | PERM_SKILL_PASSPORT_READ | Get passport data |
| POST | /skills/passport/{student_id}/generate | 202 | PERM_SKILL_PASSPORT_GENERATE | Generate PDF |
| GET | /skills/passport/{student_id}/download | 200 | PERM_SKILL_PASSPORT_READ | Download PDF |
| GET | /skills/analytics/class/{class_id} | 200 | PERM_SKILL_PROGRESS_READ | Class-level stats |
| GET | /skills/analytics/school | 200 | PERM_SKILL_PROGRESS_READ | School-level stats |
| GET | /skills/leaderboard/{class_id} | 200 | PERM_SKILL_PROGRESS_READ | Anonymized leaderboard |

### 3.4 Service Methods

```python
class SkillDimensionService:
    async def list_dimensions(self, skip: int, limit: int, db: AsyncSession) -> tuple[list[SkillDimensionResponse], int]
    async def create_dimension(self, data: CreateSkillDimensionRequest, db: AsyncSession) -> SkillDimensionResponse

class SkillMilestoneService:
    async def list_milestones(self, dimension_id: UUID | None, skip: int, limit: int, db: AsyncSession) -> tuple[list[SkillMilestoneResponse], int]
    async def create_milestone(self, data: CreateSkillMilestoneRequest, db: AsyncSession) -> SkillMilestoneResponse

class SkillProgressService:
    async def get_student_progress(self, student_id: UUID, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> list[SkillProgressResponse]
    async def evaluate_student(self, student_id: UUID, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> EvaluationResult  # Triggers evaluation engine
    async def analyze_activity_logs(self, student_id: UUID, db: AsyncSession) -> dict  # Extracts metrics from logs

class SkillPassportService:
    async def get_passport(self, student_id: UUID, academic_year_id: UUID, db: AsyncSession) -> SkillPassportResponse
    async def generate_passport(self, student_id: UUID, academic_year_id: UUID, db: AsyncSession) -> SkillPassportResponse  # Creates/updates passport
    async def generate_pdf(self, passport_id: UUID, db: AsyncSession) -> str  # Returns URL
    async def download_pdf(self, passport_id: UUID, db: AsyncSession) -> bytes

class SkillAnalyticsService:
    async def class_analytics(self, class_id: UUID, db: AsyncSession) -> ClassAnalyticsResponse
    async def school_analytics(self, school_id: UUID, db: AsyncSession) -> SchoolAnalyticsResponse
    async def leaderboard(self, class_id: UUID, limit: int, db: AsyncSession) -> list[LeaderboardEntry]
```

---

## Feature 4: MEN Compliance Checker

**Domain:** Curriculum coverage tracker against Moroccan Ministry of Education standards.
**Scope:** 4 models, 12 endpoints, 8 permissions.
**Time Estimate:** 2.5 hours

### 4.1 Models & Data Structure

#### Table: `men_curricula`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| level | String(50) | NOT NULL | primaire, college, lycee |
| grade | String(20) | NOT NULL | 1ere, 2eme, ..., terminale |
| subject | String(100) | NOT NULL | mathematics, arabic, french, physics, etc. |
| academic_year | String(10) | NOT NULL | "2025-2026" |
| version | String(20) | default "1.0" | |
| is_active | Boolean | default true | |
| created_at | DateTime | DEFAULT NOW() | |

#### Table: `men_objectives`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| curriculum_id | UUID | FK CASCADE | |
| code | String(50) | NOT NULL | "MATH-3C-01" |
| title_fr | String(500) | NOT NULL | |
| title_ar | String(500) | NOT NULL | |
| description_fr | Text | nullable | |
| trimester | Integer | CHECK 1-3 | |
| unit_number | Integer | NOT NULL | |
| is_mandatory | Boolean | default true | |
| hours_recommended | Float | nullable | |
| display_order | Integer | NOT NULL | |

#### Table: `curriculum_mappings`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| objective_id | UUID | FK CASCADE | |
| course_id | UUID | FK courses.id nullable | |
| content_item_id | UUID | nullable | |
| mapped_by | UUID | FK users.id | |
| mapped_at | DateTime | NOT NULL | |
| coverage_percent | Integer | default 100, CHECK 0-100 | |
| notes | Text | nullable | |
| UNIQUE | (school_id, objective_id, course_id) | | |

#### Table: `compliance_reports`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| curriculum_id | UUID | FK CASCADE | |
| generated_at | DateTime | NOT NULL | |
| generated_by | UUID | FK users.id | |
| total_objectives | Integer | NOT NULL | |
| mapped_objectives | Integer | NOT NULL | |
| compliance_percent | Float | CHECK 0-100 | |
| unmapped_objectives | JSONB | NOT NULL | List of objective codes |
| pdf_url | String(500) | nullable | |
| academic_year_id | UUID | FK | |

### 4.2 Permissions (8 total)

```python
PERM_COMPLY_CURRICULUM_READ = "PERM-COMPLY:curriculum:read"
PERM_COMPLY_CURRICULUM_MANAGE = "PERM-COMPLY:curriculum:manage"
PERM_COMPLY_OBJECTIVE_READ = "PERM-COMPLY:objective:read"
PERM_COMPLY_MAPPING_CREATE = "PERM-COMPLY:mapping:create"
PERM_COMPLY_MAPPING_READ = "PERM-COMPLY:mapping:read"
PERM_COMPLY_REPORT_READ = "PERM-COMPLY:report:read"
PERM_COMPLY_REPORT_GENERATE = "PERM-COMPLY:report:generate"
PERM_COMPLY_SEED = "PERM-COMPLY:data:seed"  # SUPER/SYS only

# TEACHER: map + read
# DIRECTOR/ADMIN: report + read + generate
# SUPER/SYS: manage + seed
```

### 4.3 API Endpoints (12 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| GET | /compliance/curricula | 200 | PERM_COMPLY_CURRICULUM_READ | List curricula |
| POST | /compliance/curricula | 201 | PERM_COMPLY_CURRICULUM_MANAGE | Create curriculum (SYS) |
| GET | /compliance/curricula/{id}/objectives | 200 | PERM_COMPLY_OBJECTIVE_READ | List objectives |
| POST | /compliance/curricula/{id}/objectives | 201 | PERM_COMPLY_CURRICULUM_MANAGE | Create objective (SYS) |
| POST | /compliance/mappings | 201 | PERM_COMPLY_MAPPING_CREATE | Map course to objective |
| GET | /compliance/mappings | 200 | PERM_COMPLY_MAPPING_READ | List mappings for school |
| DELETE | /compliance/mappings/{id} | 204 | PERM_COMPLY_MAPPING_CREATE | Remove mapping |
| GET | /compliance/dashboard | 200 | PERM_COMPLY_REPORT_READ | Compliance % per subject |
| POST | /compliance/reports/generate | 202 | PERM_COMPLY_REPORT_GENERATE | Generate report |
| GET | /compliance/reports | 200 | PERM_COMPLY_REPORT_READ | List reports |
| GET | /compliance/reports/{id} | 200 | PERM_COMPLY_REPORT_READ | Report detail |
| GET | /compliance/reports/{id}/download | 200 | PERM_COMPLY_REPORT_READ | Download PDF |

### 4.4 Service Methods

```python
class MenCurriculumService:
    async def list_curricula(self, level: str | None, grade: str | None, skip: int, limit: int, db: AsyncSession) -> tuple[list[MenCurriculumResponse], int]
    async def create_curriculum(self, data: CreateMenCurriculumRequest, db: AsyncSession) -> MenCurriculumResponse
    async def list_objectives(self, curriculum_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[MenObjectiveResponse], int]
    async def create_objective(self, curriculum_id: UUID, data: CreateMenObjectiveRequest, db: AsyncSession) -> MenObjectiveResponse

class CurriculumMappingService:
    async def create_mapping(self, school_id: UUID, data: CreateMappingRequest, db: AsyncSession) -> MappingResponse
    async def list_mappings(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[MappingResponse], int]
    async def delete_mapping(self, mapping_id: UUID, db: AsyncSession) -> bool

class ComplianceReportService:
    async def get_dashboard(self, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> DashboardResponse
    async def generate_report(self, school_id: UUID, curriculum_id: UUID, db: AsyncSession) -> ComplianceReportResponse
    async def list_reports(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[ComplianceReportResponse], int]
    async def get_report(self, report_id: UUID, db: AsyncSession) -> ComplianceReportResponse
    async def download_pdf(self, report_id: UUID, db: AsyncSession) -> bytes
    async def seed_reference_curricula(self, db: AsyncSession) -> int  # Returns count of curricula created
```

---

## Feature 5: Class Micro-Budget

**Domain:** Decentralized financial management per class/teacher with approval flow.
**Scope:** 4 models, 14 endpoints, 10 permissions.
**Time Estimate:** 3 hours

### 5.1 Models & Data Structure

#### Table: `micro_budgets`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| academic_year_id | UUID | FK | |
| total_amount | Numeric(12,2) | CHECK >= 0 | |
| allocated_amount | Numeric(12,2) | default 0 | Sum of allocations |
| remaining_amount | Numeric(12,2) | computed | total - allocated |
| currency | String(3) | default "MAD" | |
| status | Enum | active/frozen/closed | |
| created_by | UUID | FK users.id | |
| created_at | DateTime | DEFAULT NOW() | |
| updated_at | DateTime | DEFAULT NOW() | |

#### Table: `budget_allocations`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| budget_id | UUID | FK CASCADE | |
| class_id | UUID | FK classes.id nullable | |
| teacher_id | UUID | FK users.id nullable | |
| label | String(200) | NOT NULL | "Budget Arts Plastiques 3ème A" |
| amount | Numeric(10,2) | CHECK > 0 | |
| spent | Numeric(10,2) | default 0 | Sum of approved requests |
| remaining | Numeric(10,2) | computed | amount - spent |
| currency | String(3) | default "MAD" | |
| allocated_by | UUID | FK users.id | |
| allocated_at | DateTime | NOT NULL | |
| status | Enum | active/exhausted/frozen | |

#### Table: `budget_requests`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| allocation_id | UUID | FK CASCADE | |
| requester_id | UUID | FK users.id | |
| amount | Numeric(10,2) | CHECK > 0 | |
| currency | String(3) | default "MAD" | |
| description | Text | NOT NULL | "Achat de peinture et pinceaux" |
| justification | Text | nullable | |
| status | Enum | pending/approved/rejected/cancelled | |
| reviewed_by | UUID | FK users.id nullable | |
| reviewed_at | DateTime | nullable | |
| review_comment | Text | nullable | |
| created_at | DateTime | DEFAULT NOW() | |

#### Table: `budget_transactions`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| allocation_id | UUID | FK CASCADE | |
| request_id | UUID | FK budget_requests.id nullable | |
| amount | Numeric(10,2) | NOT NULL | |
| transaction_type | Enum | allocation/expense/refund/adjustment | |
| description | String(300) | NOT NULL | |
| receipt_url | String(500) | nullable | |
| recorded_by | UUID | FK users.id | |
| recorded_at | DateTime | DEFAULT NOW() | |

### 5.2 Permissions (10 total)

```python
PERM_BUDGET_CREATE = "PERM-BUDGET:budget:create"
PERM_BUDGET_READ = "PERM-BUDGET:budget:read"
PERM_BUDGET_MANAGE = "PERM-BUDGET:budget:manage"
PERM_BUDGET_ALLOCATE = "PERM-BUDGET:allocation:allocate"
PERM_BUDGET_REQUEST_CREATE = "PERM-BUDGET:request:create"
PERM_BUDGET_REQUEST_READ = "PERM-BUDGET:request:read"
PERM_BUDGET_APPROVE = "PERM-BUDGET:request:approve"
PERM_BUDGET_TRANSACTION_CREATE = "PERM-BUDGET:transaction:create"
PERM_BUDGET_TRANSACTION_READ = "PERM-BUDGET:transaction:read"
PERM_BUDGET_ANALYTICS_READ = "PERM-BUDGET:analytics:read"

# ADMIN/DIRECTOR: create, allocate, approve, analytics
# TEACHER: request, read own allocations
# SUPER: manage
```

### 5.3 API Endpoints (14 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| POST | /budgets | 201 | PERM_BUDGET_CREATE | Create school budget |
| GET | /budgets | 200 | PERM_BUDGET_READ | List budgets |
| GET | /budgets/{id} | 200 | PERM_BUDGET_READ | Budget detail |
| POST | /budgets/{id}/allocations | 201 | PERM_BUDGET_ALLOCATE | Allocate to class/teacher |
| GET | /budgets/{id}/allocations | 200 | PERM_BUDGET_READ | List allocations |
| GET | /allocations/{id} | 200 | PERM_BUDGET_READ | Allocation detail |
| POST | /allocations/{id}/requests | 201 | PERM_BUDGET_REQUEST_CREATE | Submit expense request |
| GET | /allocations/{id}/requests | 200 | PERM_BUDGET_REQUEST_READ | List requests |
| POST | /requests/{id}/approve | 200 | PERM_BUDGET_APPROVE | Approve request (auto-deduct) |
| POST | /requests/{id}/reject | 200 | PERM_BUDGET_APPROVE | Reject request |
| GET | /requests/{id} | 200 | PERM_BUDGET_REQUEST_READ | Request detail |
| POST | /allocations/{id}/transactions | 201 | PERM_BUDGET_TRANSACTION_CREATE | Record transaction |
| GET | /allocations/{id}/transactions | 200 | PERM_BUDGET_TRANSACTION_READ | Transaction history |
| GET | /budgets/analytics | 200 | PERM_BUDGET_ANALYTICS_READ | Budget analytics dashboard |

### 5.4 Service Methods

```python
class MicroBudgetService:
    async def create_budget(self, school_id: UUID, data: CreateBudgetRequest, db: AsyncSession) -> BudgetResponse
    async def list_budgets(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[BudgetResponse], int]
    async def get_budget(self, budget_id: UUID, db: AsyncSession) -> BudgetResponse

class BudgetAllocationService:
    async def allocate(self, budget_id: UUID, data: CreateAllocationRequest, db: AsyncSession) -> AllocationResponse
    async def list_allocations(self, budget_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[AllocationResponse], int]
    async def get_allocation(self, allocation_id: UUID, db: AsyncSession) -> AllocationResponse

class BudgetRequestService:
    async def create_request(self, allocation_id: UUID, requester_id: UUID, data: CreateRequestRequest, db: AsyncSession) -> RequestResponse
    async def list_requests(self, allocation_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[RequestResponse], int]
    async def get_request(self, request_id: UUID, db: AsyncSession) -> RequestResponse
    async def approve_request(self, request_id: UUID, approver_id: UUID, db: AsyncSession) -> RequestResponse  # Updates request + creates transaction
    async def reject_request(self, request_id: UUID, approver_id: UUID, reason: str, db: AsyncSession) -> RequestResponse

class BudgetTransactionService:
    async def record_transaction(self, allocation_id: UUID, data: CreateTransactionRequest, db: AsyncSession) -> TransactionResponse
    async def list_transactions(self, allocation_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[TransactionResponse], int]

class BudgetAnalyticsService:
    async def budget_analytics(self, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> AnalyticsResponse
```

---

## Feature 6: Financial Health Dashboard

**Domain:** Advanced financial KPIs for school owners (retention, cashflow, cost analysis).
**Scope:** 4 models, 12 endpoints, 6 permissions.
**Time Estimate:** 2.5 hours

### 6.1 Models & Data Structure

#### Table: `retention_metrics`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| academic_year_from | String(10) | NOT NULL | "2024-2025" |
| academic_year_to | String(10) | NOT NULL | "2025-2026" |
| total_students_start | Integer | NOT NULL | |
| total_students_end | Integer | NOT NULL | |
| retained | Integer | NOT NULL | |
| new_enrollments | Integer | NOT NULL | |
| withdrawals | Integer | NOT NULL | |
| retention_rate | Float | CHECK 0-100 | Percentage |
| computed_at | DateTime | NOT NULL | |

#### Table: `cashflow_forecasts`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| forecast_month | Date | NOT NULL | First of month |
| expected_income | Numeric(14,2) | NOT NULL | Based on invoice schedule |
| expected_expenses | Numeric(14,2) | NOT NULL | |
| actual_income | Numeric(14,2) | nullable | |
| actual_expenses | Numeric(14,2) | nullable | |
| currency | String(3) | default "MAD" | |
| confidence_score | Float | CHECK 0-1 | Based on payment history |
| computed_at | DateTime | NOT NULL | |

#### Table: `cost_per_student`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| academic_year_id | UUID | FK | |
| total_operational_cost | Numeric(14,2) | NOT NULL | |
| total_students | Integer | CHECK > 0 | |
| cost_per_student | Numeric(10,2) | computed | |
| revenue_per_student | Numeric(10,2) | computed | |
| margin_per_student | Numeric(10,2) | computed | |
| currency | String(3) | default "MAD" | |
| computed_at | DateTime | NOT NULL | |

#### Table: `financial_snapshots`
| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| school_id | UUID | FK CASCADE | |
| snapshot_date | Date | NOT NULL | |
| total_receivable | Numeric(14,2) | NOT NULL | Unpaid invoices |
| total_collected | Numeric(14,2) | NOT NULL | Paid invoices |
| collection_rate | Float | CHECK 0-100 | Percentage |
| overdue_amount | Numeric(14,2) | NOT NULL | |
| overdue_count | Integer | NOT NULL | |
| avg_payment_delay_days | Float | nullable | |
| currency | String(3) | default "MAD" | |
| computed_at | DateTime | NOT NULL | |

### 6.2 Permissions (6 total)

```python
PERM_FINHEALTH_RETENTION_READ = "PERM-FINHEALTH:retention:read"
PERM_FINHEALTH_CASHFLOW_READ = "PERM-FINHEALTH:cashflow:read"
PERM_FINHEALTH_COST_READ = "PERM-FINHEALTH:cost:read"
PERM_FINHEALTH_SNAPSHOT_READ = "PERM-FINHEALTH:snapshot:read"
PERM_FINHEALTH_COMPUTE = "PERM-FINHEALTH:compute"
PERM_FINHEALTH_EXPORT = "PERM-FINHEALTH:export"

# ADMIN/DIRECTOR/SUPER: all perms
```

### 6.3 API Endpoints (12 total)

| Method | Path | Status | Permission | Notes |
|--------|------|--------|-----------|-------|
| GET | /financial-health/retention | 200 | PERM_FINHEALTH_RETENTION_READ | Retention metrics |
| POST | /financial-health/retention/compute | 202 | PERM_FINHEALTH_COMPUTE | Compute retention |
| GET | /financial-health/cashflow | 200 | PERM_FINHEALTH_CASHFLOW_READ | Cashflow forecast |
| POST | /financial-health/cashflow/compute | 202 | PERM_FINHEALTH_COMPUTE | Generate forecast |
| GET | /financial-health/cost-per-student | 200 | PERM_FINHEALTH_COST_READ | Cost analysis |
| POST | /financial-health/cost-per-student/compute | 202 | PERM_FINHEALTH_COMPUTE | Compute costs |
| GET | /financial-health/snapshot | 200 | PERM_FINHEALTH_SNAPSHOT_READ | Current financial snapshot |
| POST | /financial-health/snapshot/compute | 202 | PERM_FINHEALTH_COMPUTE | Generate snapshot |
| GET | /financial-health/dashboard | 200 | PERM_FINHEALTH_RETENTION_READ | Combined KPI dashboard |
| GET | /financial-health/trends | 200 | PERM_FINHEALTH_RETENTION_READ | Historical trend data |
| GET | /financial-health/export/csv | 200 | PERM_FINHEALTH_EXPORT | Export financial data (CSV) |
| GET | /financial-health/export/pdf | 200 | PERM_FINHEALTH_EXPORT | Export PDF report |

### 6.4 Service Methods

```python
class RetentionMetricsService:
    async def list_retention_metrics(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[RetentionMetricResponse], int]
    async def compute_retention(self, school_id: UUID, from_year: str, to_year: str, db: AsyncSession) -> RetentionMetricResponse

class CashflowForecastService:
    async def list_forecasts(self, school_id: UUID, skip: int, limit: int, db: AsyncSession) -> tuple[list[CashflowForecastResponse], int]
    async def compute_forecast(self, school_id: UUID, months_ahead: int = 6, db: AsyncSession) -> list[CashflowForecastResponse]

class CostPerStudentService:
    async def get_cost_analysis(self, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> CostPerStudentResponse
    async def compute_cost(self, school_id: UUID, academic_year_id: UUID, db: AsyncSession) -> CostPerStudentResponse

class FinancialSnapshotService:
    async def get_snapshot(self, school_id: UUID, snapshot_date: date | None, db: AsyncSession) -> FinancialSnapshotResponse
    async def compute_snapshot(self, school_id: UUID, db: AsyncSession) -> FinancialSnapshotResponse

class FinancialHealthService:
    async def get_dashboard(self, school_id: UUID, db: AsyncSession) -> DashboardResponse  # Combines all KPIs
    async def get_trends(self, school_id: UUID, months: int = 12, db: AsyncSession) -> TrendResponse
    async def export_csv(self, school_id: UUID, db: AsyncSession) -> bytes
    async def export_pdf(self, school_id: UUID, db: AsyncSession) -> bytes
```

---

## Execution Checklist

### MICRO-01: Models & Migrations

- [ ] **ANALYZE**
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/billing.py` for pattern reference
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/core/permissions.py` for existing constants
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/__init__.py` for model registration
  - [ ] Check RoleCode enum in `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/user.py`

- [ ] **EXECUTE**
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/micro_school.py` with 6 models: MicroSchool, MicroGroup, MicroEnrollment, MicroPayment, MicroResource, MicroProgressLog
  - [ ] Create Alembic migration file for micro_schools, micro_groups, micro_enrollments, micro_payments, micro_resources, micro_progress_logs
  - [ ] Add 13 constants to `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/core/permissions.py`: PERM_MICRO_SCHOOL_*, PERM_MICRO_GROUP_*, PERM_MICRO_ENROLLMENT_*, PERM_MICRO_PAYMENT_*, PERM_MICRO_RESOURCE_*, PERM_MICRO_PROGRESS_*
  - [ ] Add EDUCATOR role to RoleCode enum (if not exists)
  - [ ] Add EDUCATOR permissions to ROLE_PERMISSIONS mapping in permissions.py
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/domain/events/micro_school.py` with domain events: MicroSchoolCreatedEvent, MicroSchoolUpdatedEvent, MicroEnrollmentCreatedEvent, MicroPaymentRecordedEvent
  - [ ] Update `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/__init__.py` to import all 6 new models

- [ ] **VERIFY**
  - [ ] Run `alembic upgrade head` — should succeed with 6 new tables
  - [ ] Run `alembic downgrade -1 && alembic upgrade head` — round-trip test should pass
  - [ ] Run `python -c "from app.models.micro_school import MicroSchool, MicroGroup, MicroEnrollment, MicroPayment, MicroResource, MicroProgressLog; print('OK')"` — import check
  - [ ] Query database: `SELECT COUNT(*) FROM information_schema.tables WHERE table_name LIKE 'micro_%';` — expect 6 rows
  - [ ] Verify CheckConstraints on amount/price columns (positive values only)

- [ ] **GIT** (Conditional)
  - [ ] If CODEX_ENV=true: `git add -A && git commit -m "feat(micro-ecole): add models, migrations, permissions, and domain events"`
  - [ ] Else: Skip git, user handles manually

---

### MICRO-02: Repository & Service

- [ ] **ANALYZE**
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/micro_school.py` (just created)
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/repositories/billing.py` for repository pattern
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/services/billing_service.py` for service pattern
  - [ ] Check existing schema patterns in `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/schemas/`

- [ ] **EXECUTE**
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/repositories/micro_school.py` with classes:
    - MicroSchoolRepository (extend BaseRepository)
    - MicroGroupRepository (extend BaseRepository)
    - MicroEnrollmentRepository (extend BaseRepository)
    - MicroPaymentRepository (extend BaseRepository)
    - MicroResourceRepository (extend BaseRepository)
    - MicroProgressRepository (extend BaseRepository)
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/schemas/micro_school.py` with Pydantic schemas:
    - CreateMicroSchoolRequest, UpdateMicroSchoolRequest, MicroSchoolResponse
    - CreateMicroGroupRequest, MicroGroupResponse
    - CreateMicroEnrollmentRequest, MicroEnrollmentResponse
    - CreateMicroPaymentRequest, MicroPaymentResponse
    - MicroResourceResponse
    - CreateMicroProgressRequest, MicroProgressResponse
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/services/micro_school_service.py` with classes:
    - MicroSchoolService (with create, get, list, update, delete methods)
    - MicroGroupService
    - MicroEnrollmentService
    - MicroPaymentService
    - MicroResourceService
    - MicroProgressService

- [ ] **VERIFY**
  - [ ] Run `python -c "from app.repositories.micro_school import *; from app.services.micro_school_service import *; print('OK')"` — import check
  - [ ] Verify all methods have type hints (no `Any` without explicit reason)
  - [ ] Verify all repositories inherit from BaseRepository
  - [ ] Verify all services use AsyncSession parameter

- [ ] **GIT** (Conditional)
  - [ ] If CODEX_ENV=true: `git add -A && git commit -m "feat(micro-ecole): add repositories, schemas, and services"`
  - [ ] Else: Skip git

---

### MICRO-03: API Endpoints

- [ ] **ANALYZE**
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/services/micro_school_service.py` (just created)
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/api/v1/billing.py` for endpoint pattern
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/api/v1/router.py` for router registration

- [ ] **EXECUTE**
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/api/v1/micro_school.py` with 14 routes:
    - POST /micro-schools (create)
    - GET /micro-schools (list educator's schools)
    - GET /micro-schools/{id} (detail)
    - PATCH /micro-schools/{id} (update)
    - POST /micro-schools/{id}/groups (create group)
    - GET /micro-schools/{id}/groups (list groups)
    - POST /micro-groups/{id}/enrollments (enroll child)
    - GET /micro-groups/{id}/enrollments (list children)
    - POST /micro-payments (record payment)
    - GET /micro-payments (list payments)
    - GET /micro-resources (browse library)
    - POST /micro-progress (log progress)
    - GET /micro-progress/child/{enrollment_id} (child progress)
    - GET /micro-progress/daily (daily summary for parents)
  - [ ] Register router in `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/api/v1/router.py`: `router.include_router(micro_school.router, prefix="/micro-schools", tags=["micro-ecole"])`
  - [ ] Add OpenAPI tags with description

- [ ] **VERIFY**
  - [ ] Start dev server: `python -m uvicorn backend.app.main:app --reload`
  - [ ] Navigate to `http://localhost:8000/docs` and verify all 14 endpoints listed under `micro-ecole` tag
  - [ ] Verify each endpoint has correct method, status code, permission check
  - [ ] Make a test request (GET /micro-schools) with auth token — expect 200 (empty list)

- [ ] **GIT** (Conditional)
  - [ ] If CODEX_ENV=true: `git add -A && git commit -m "feat(micro-ecole): add API endpoints and router"`
  - [ ] Else: Skip git

---

### MICRO-04: Tests & Factories

- [ ] **ANALYZE**
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/models/micro_school.py`
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/app/services/micro_school_service.py`
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/factories/billing.py` for factory pattern
  - [ ] Read `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/unit/services/test_billing_service.py` for test pattern

- [ ] **EXECUTE**
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/factories/micro_school.py` with factories:
    - MicroSchoolFactory (educator_id, name, neighborhood, city, phone, max_capacity, status)
    - MicroGroupFactory (micro_school_id, name, age_range_min, age_range_max)
    - MicroEnrollmentFactory (micro_group_id, child_name, parent_id, date_of_birth)
    - MicroPaymentFactory (micro_school_id, parent_id, child_enrollment_id, amount, period_type, status)
    - MicroResourceFactory (title, resource_type, age_group, language, is_premium)
    - MicroProgressFactory (micro_enrollment_id, educator_id, note, date)
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/unit/services/test_micro_school_service.py` with ~35 unit tests:
    - test_create_micro_school_success
    - test_create_micro_school_duplicate_raises_conflict
    - test_get_micro_school_success
    - test_get_micro_school_not_found_raises_error
    - test_list_micro_schools_success
    - test_list_micro_schools_empty
    - test_update_micro_school_success
    - test_delete_micro_school_success
    - test_create_group_success
    - test_enroll_child_success
    - test_enroll_child_max_capacity_check
    - test_record_payment_success
    - test_record_payment_overdue_check
    - test_log_progress_success
    - ... (more edge cases)
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/integration/api/test_micro_school_api.py` with ~15 integration tests:
    - test_post_micro_school_returns_201
    - test_get_micro_schools_requires_auth
    - test_get_micro_schools_returns_200_with_list
    - test_update_micro_school_returns_200
    - test_delete_micro_school_returns_204
    - ... (more API contracts)
  - [ ] Create `/sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend/tests/security/test_micro_school_rbac.py` with ~10 RBAC tests:
    - test_educator_can_create_micro_school
    - test_parent_cannot_create_micro_school
    - test_parent_can_read_progress
    - test_parent_cannot_manage_payment
    - test_admin_can_read_any_school
    - ... (permission boundary checks)

- [ ] **VERIFY**
  - [ ] Run `pytest backend/tests/unit/services/test_micro_school_service.py -v` — all pass
  - [ ] Run `pytest backend/tests/integration/api/test_micro_school_api.py -v` — all pass
  - [ ] Run `pytest backend/tests/security/test_micro_school_rbac.py -v` — all pass
  - [ ] Run `pytest backend/tests/ -k micro_school --cov=backend/app --cov-report=term-missing` — target ~80% coverage
  - [ ] Total test count: ~60 tests

- [ ] **GIT** (Conditional)
  - [ ] If CODEX_ENV=true: `git add -A && git commit -m "feat(micro-ecole): add comprehensive test suite and factories"`
  - [ ] Else: Skip git

---

### SYNC-01: Models & Migrations

- [ ] **ANALYZE**
  - [ ] Read existing models and permissions structure
  - [ ] Review Alembic patterns from MICRO-01

- [ ] **EXECUTE**
  - [ ] Create models file with 4 models: SyncDevice, SyncQueue, SyncConflict, SyncCheckpoint
  - [ ] Create Alembic migration
  - [ ] Add 8 permission constants (PERM_SYNC_*)
  - [ ] Add to ROLE_PERMISSIONS
  - [ ] Create domain events

- [ ] **VERIFY**
  - [ ] Alembic round-trip
  - [ ] Import check
  - [ ] Verify 4 tables in database

- [ ] **GIT** (Conditional)

---

### SYNC-02: Repository & Service

- [ ] **ANALYZE**
- [ ] **EXECUTE**
- [ ] **VERIFY**
- [ ] **GIT** (Conditional)

---

### SYNC-03: API Endpoints

- [ ] **ANALYZE**
- [ ] **EXECUTE**
  - [ ] 10 routes for device registration, push/pull sync, conflict resolution, health
- [ ] **VERIFY**
  - [ ] Verify endpoints in /docs
- [ ] **GIT** (Conditional)

---

### SYNC-04: Tests & Factories

- [ ] **ANALYZE**
- [ ] **EXECUTE**
  - [ ] ~55 tests covering sync queue, push/pull, conflict detection, checkpoint logic
- [ ] **VERIFY**
  - [ ] pytest coverage >= 80%
- [ ] **GIT** (Conditional)

---

### SKILL-01: Models & Migrations
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/lms.py for pattern reference
  - [ ] Read backend/app/core/permissions.py for existing constants
  - [ ] Read backend/app/models/__init__.py for model registration
- [ ] **EXECUTE**
  - [ ] Create backend/app/models/skill_passport.py with 4 models (SkillDimension, SkillMilestone, SkillProgress, SkillPassport)
  - [ ] Create Alembic migration for skill passport tables
  - [ ] Add 8 PERM_SKILL_* constants to permissions.py
  - [ ] Add role mappings: TCH/DIR → evaluate+read, PAR/STD → read, ADM → manage
  - [ ] Create backend/app/domain/events/skill_passport.py
  - [ ] Update backend/app/models/__init__.py imports
- [ ] **VERIFY**
  - [ ] alembic upgrade head (success)
  - [ ] alembic downgrade -1 && alembic upgrade head (round-trip)
  - [ ] python -c "from app.models.skill_passport import *" (import check)
  - [ ] Verify 4 new tables in DB
- [ ] **GIT**
  - [ ] Conditional commit: "feat(skills): add models and migrations for life skills passport"

### SKILL-02: Repository & Service
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/skill_passport.py
  - [ ] Read backend/app/repositories/base.py for CRUD pattern
  - [ ] Read backend/app/services/gradebook.py for analytics pattern
- [ ] **EXECUTE**
  - [ ] Create backend/app/schemas/skill_passport.py (8 schemas: dimension, milestone, progress, passport create/response)
  - [ ] Create backend/app/repositories/skill_passport.py (SkillPassportRepository)
  - [ ] Create backend/app/services/skill_passport_service.py (SkillPassportService)
  - [ ] Implement milestone evaluation engine (rule_config JSON parsing, threshold checks)
  - [ ] Implement PDF passport generation method
- [ ] **VERIFY**
  - [ ] python -c "from app.services.skill_passport_service import SkillPassportService"
  - [ ] python -c "from app.schemas.skill_passport import *"
  - [ ] Verify all method signatures have type hints
- [ ] **GIT**
  - [ ] Conditional commit: "feat(skills): add repository, service, and schemas for life skills passport"

### SKILL-03: API Endpoints
- [ ] **ANALYZE**
  - [ ] Read backend/app/services/skill_passport_service.py
  - [ ] Read backend/app/api/v1/router.py for registration pattern
- [ ] **EXECUTE**
  - [ ] Create backend/app/api/v1/skills.py with 12 endpoints
  - [ ] Register skills_router in router.py
  - [ ] Endpoints: dimensions CRUD, milestones CRUD, progress read, evaluate, passport generate/download, analytics class/school, leaderboard
- [ ] **VERIFY**
  - [ ] Start server, verify /docs shows skills endpoints
  - [ ] Verify all 12 endpoints appear with correct methods
- [ ] **GIT**
  - [ ] Conditional commit: "feat(skills): add API endpoints for life skills passport"

### SKILL-04: Tests & Factories
- [ ] **ANALYZE**
  - [ ] Read backend/tests/factories/lms.py for factory pattern
  - [ ] Read backend/tests/unit/services/test_gradebook_service.py for test pattern
- [ ] **EXECUTE**
  - [ ] Create backend/tests/factories/skill_passport.py (SkillDimensionFactory, SkillMilestoneFactory, SkillProgressFactory, SkillPassportFactory)
  - [ ] Create backend/tests/unit/services/test_skill_passport_service.py (~25 tests)
  - [ ] Create backend/tests/integration/api/test_skills_api.py (~15 tests)
  - [ ] Create backend/tests/security/test_skills_rbac.py (~15 tests: TCH can evaluate, PAR can read only, STD can view own passport)
  - [ ] Create backend/tests/edge/test_skill_edge.py (~10 tests: milestone threshold boundaries, empty logs, duplicate evaluations)
- [ ] **VERIFY**
  - [ ] pytest backend/tests/ -k "skill" --tb=short (all pass)
  - [ ] pytest backend/tests/ -k "skill" --cov=app --cov-report=term (coverage ≥ 80%)
  - [ ] Verify ~65 tests total
- [ ] **GIT**
  - [ ] Conditional commit: "test(skills): add tests and factories for life skills passport"

---

### COMPLY-01: Models & Migrations
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/lms.py for course model references
  - [ ] Read backend/app/core/permissions.py for existing constants
- [ ] **EXECUTE**
  - [ ] Create backend/app/models/men_compliance.py with 4 models (MenCurriculum, MenObjective, CurriculumMapping, ComplianceReport)
  - [ ] Create Alembic migration for compliance tables
  - [ ] Add 8 PERM_COMPLY_* constants to permissions.py
  - [ ] Add role mappings: TCH → map+read, DIR/ADM → report+read, SUP/SYS → manage+seed
  - [ ] Create backend/app/domain/events/men_compliance.py
  - [ ] Update backend/app/models/__init__.py imports
- [ ] **VERIFY**
  - [ ] alembic upgrade head (success)
  - [ ] alembic downgrade -1 && alembic upgrade head (round-trip)
  - [ ] python -c "from app.models.men_compliance import *" (import check)
  - [ ] Verify 4 new tables in DB
- [ ] **GIT**
  - [ ] Conditional commit: "feat(compliance): add models and migrations for MEN compliance checker"

### COMPLY-02: Repository & Service
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/men_compliance.py
  - [ ] Read backend/app/repositories/base.py for CRUD pattern
- [ ] **EXECUTE**
  - [ ] Create backend/app/schemas/men_compliance.py (8 schemas: curriculum, objective, mapping, report)
  - [ ] Create backend/app/repositories/men_compliance.py (ComplianceRepository)
  - [ ] Create backend/app/services/compliance_service.py (ComplianceService)
  - [ ] Implement compliance percentage calculator (mapped/total objectives)
  - [ ] Implement seed_men_curriculum() for MEN reference data
  - [ ] Implement PDF compliance report generation
- [ ] **VERIFY**
  - [ ] python -c "from app.services.compliance_service import ComplianceService"
  - [ ] python -c "from app.schemas.men_compliance import *"
- [ ] **GIT**
  - [ ] Conditional commit: "feat(compliance): add repository, service, and schemas for MEN compliance"

### COMPLY-03: API Endpoints
- [ ] **ANALYZE**
  - [ ] Read backend/app/services/compliance_service.py
  - [ ] Read backend/app/api/v1/router.py
- [ ] **EXECUTE**
  - [ ] Create backend/app/api/v1/compliance.py with 12 endpoints
  - [ ] Register compliance_router in router.py
  - [ ] Endpoints: curricula list/create, objectives list/create, mappings CRUD, dashboard, report generate/list/detail/download
- [ ] **VERIFY**
  - [ ] Start server, verify /docs shows compliance endpoints
  - [ ] Verify all 12 endpoints appear
- [ ] **GIT**
  - [ ] Conditional commit: "feat(compliance): add API endpoints for MEN compliance checker"

### COMPLY-04: Tests & Factories
- [ ] **ANALYZE**
  - [ ] Read backend/tests/factories/lms.py for factory pattern
- [ ] **EXECUTE**
  - [ ] Create backend/tests/factories/men_compliance.py (MenCurriculumFactory, MenObjectiveFactory, CurriculumMappingFactory, ComplianceReportFactory)
  - [ ] Create backend/tests/unit/services/test_compliance_service.py (~20 tests)
  - [ ] Create backend/tests/integration/api/test_compliance_api.py (~15 tests)
  - [ ] Create backend/tests/security/test_compliance_rbac.py (~10 tests: TCH can map, STD cannot, SYS can seed)
  - [ ] Create backend/tests/edge/test_compliance_edge.py (~10 tests: 0% coverage, 100% coverage, unmapped objectives, duplicate mappings)
- [ ] **VERIFY**
  - [ ] pytest backend/tests/ -k "compliance" --tb=short (all pass)
  - [ ] pytest backend/tests/ -k "compliance" --cov=app --cov-report=term (coverage ≥ 80%)
  - [ ] Verify ~55 tests total
- [ ] **GIT**
  - [ ] Conditional commit: "test(compliance): add tests and factories for MEN compliance checker"

---

### BUDGET-01: Models & Migrations
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/billing.py for financial model patterns
  - [ ] Read backend/app/core/permissions.py for existing constants
- [ ] **EXECUTE**
  - [ ] Create backend/app/models/budget.py with 4 models (MicroBudget, BudgetAllocation, BudgetRequest, BudgetTransaction)
  - [ ] Create Alembic migration for budget tables
  - [ ] Add 10 PERM_BUDGET_* constants to permissions.py
  - [ ] Add role mappings: ADM/DIR → create+allocate+approve, TCH → request+read own, SUP → manage
  - [ ] Create backend/app/domain/events/budget.py
  - [ ] Update backend/app/models/__init__.py imports
- [ ] **VERIFY**
  - [ ] alembic upgrade head (success)
  - [ ] alembic downgrade -1 && alembic upgrade head (round-trip)
  - [ ] python -c "from app.models.budget import *" (import check)
  - [ ] Verify 4 new tables in DB
- [ ] **GIT**
  - [ ] Conditional commit: "feat(budget): add models and migrations for class micro-budget"

### BUDGET-02: Repository & Service
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/budget.py
  - [ ] Read backend/app/repositories/billing.py for financial repo pattern
  - [ ] Read backend/app/services/billing.py for approval workflow pattern
- [ ] **EXECUTE**
  - [ ] Create backend/app/schemas/budget.py (10 schemas: budget, allocation, request, transaction create/response/update)
  - [ ] Create backend/app/repositories/budget.py (BudgetRepository)
  - [ ] Create backend/app/services/budget_service.py (BudgetService)
  - [ ] Implement allocation flow (admin → class with MAD amount)
  - [ ] Implement request → approval → auto-deduct workflow
  - [ ] Implement budget analytics (spent vs remaining)
- [ ] **VERIFY**
  - [ ] python -c "from app.services.budget_service import BudgetService"
  - [ ] python -c "from app.schemas.budget import *"
- [ ] **GIT**
  - [ ] Conditional commit: "feat(budget): add repository, service, and schemas for class micro-budget"

### BUDGET-03: API Endpoints
- [ ] **ANALYZE**
  - [ ] Read backend/app/services/budget_service.py
  - [ ] Read backend/app/api/v1/router.py
- [ ] **EXECUTE**
  - [ ] Create backend/app/api/v1/budgets.py with 14 endpoints
  - [ ] Register budgets_router in router.py
  - [ ] Endpoints: budget CRUD, allocations CRUD, request submit/list/approve/reject, transactions record/list, analytics
- [ ] **VERIFY**
  - [ ] Start server, verify /docs shows budget endpoints
  - [ ] Verify all 14 endpoints appear
- [ ] **GIT**
  - [ ] Conditional commit: "feat(budget): add API endpoints for class micro-budget"

### BUDGET-04: Tests & Factories
- [ ] **ANALYZE**
  - [ ] Read backend/tests/factories/billing.py for financial factory pattern
- [ ] **EXECUTE**
  - [ ] Create backend/tests/factories/budget.py (MicroBudgetFactory, BudgetAllocationFactory, BudgetRequestFactory, BudgetTransactionFactory)
  - [ ] Create backend/tests/unit/services/test_budget_service.py (~20 tests)
  - [ ] Create backend/tests/integration/api/test_budgets_api.py (~15 tests)
  - [ ] Create backend/tests/security/test_budget_rbac.py (~12 tests: TCH can request, cannot approve; DIR can approve; STD cannot access)
  - [ ] Create backend/tests/edge/test_budget_edge.py (~13 tests: overspend prevention, negative amounts, exhausted budget, concurrent requests, MAD currency enforcement)
- [ ] **VERIFY**
  - [ ] pytest backend/tests/ -k "budget" --tb=short (all pass)
  - [ ] pytest backend/tests/ -k "budget" --cov=app --cov-report=term (coverage ≥ 80%)
  - [ ] Verify ~60 tests total
- [ ] **GIT**
  - [ ] Conditional commit: "test(budget): add tests and factories for class micro-budget"

---

### HEALTH-01: Models & Migrations
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/billing.py for financial data patterns
  - [ ] Read backend/app/core/permissions.py for existing constants
- [ ] **EXECUTE**
  - [ ] Create backend/app/models/financial_health.py with 4 models (RetentionMetric, CashflowForecast, CostPerStudent, FinancialSnapshot)
  - [ ] Create Alembic migration for financial health tables
  - [ ] Add 6 PERM_FINHEALTH_* constants to permissions.py
  - [ ] Add role mappings: ADM/DIR/SUP → read+compute, SYS → manage
  - [ ] Create backend/app/domain/events/financial_health.py
  - [ ] Update backend/app/models/__init__.py imports
- [ ] **VERIFY**
  - [ ] alembic upgrade head (success)
  - [ ] alembic downgrade -1 && alembic upgrade head (round-trip)
  - [ ] python -c "from app.models.financial_health import *" (import check)
  - [ ] Verify 4 new tables in DB
- [ ] **GIT**
  - [ ] Conditional commit: "feat(finhealth): add models and migrations for financial health dashboard"

### HEALTH-02: Repository & Service
- [ ] **ANALYZE**
  - [ ] Read backend/app/models/financial_health.py
  - [ ] Read backend/app/repositories/billing.py for data aggregation pattern
  - [ ] Read backend/app/services/analytics.py for KPI computation pattern
- [ ] **EXECUTE**
  - [ ] Create backend/app/schemas/financial_health.py (8 schemas: retention, cashflow, cost, snapshot response + compute request)
  - [ ] Create backend/app/repositories/financial_health.py (FinancialHealthRepository)
  - [ ] Create backend/app/services/financial_health_service.py (FinancialHealthService)
  - [ ] Implement retention rate calculator (year-over-year student comparison)
  - [ ] Implement cashflow forecast engine (invoice schedule + payment history reliability)
  - [ ] Implement cost-per-student calculator
  - [ ] Implement financial snapshot generator (receivable, collected, overdue, avg delay)
- [ ] **VERIFY**
  - [ ] python -c "from app.services.financial_health_service import FinancialHealthService"
  - [ ] python -c "from app.schemas.financial_health import *"
- [ ] **GIT**
  - [ ] Conditional commit: "feat(finhealth): add repository, service, and schemas for financial health dashboard"

### HEALTH-03: API Endpoints
- [ ] **ANALYZE**
  - [ ] Read backend/app/services/financial_health_service.py
  - [ ] Read backend/app/api/v1/router.py
- [ ] **EXECUTE**
  - [ ] Create backend/app/api/v1/financial_health.py with 12 endpoints
  - [ ] Register financial_health_router in router.py
  - [ ] Endpoints: retention read/compute, cashflow read/compute, cost read/compute, snapshot read/compute, dashboard, trends, export CSV, export PDF
- [ ] **VERIFY**
  - [ ] Start server, verify /docs shows financial-health endpoints
  - [ ] Verify all 12 endpoints appear
- [ ] **GIT**
  - [ ] Conditional commit: "feat(finhealth): add API endpoints for financial health dashboard"

### HEALTH-04: Tests & Factories
- [ ] **ANALYZE**
  - [ ] Read backend/tests/factories/billing.py for financial factory pattern
- [ ] **EXECUTE**
  - [ ] Create backend/tests/factories/financial_health.py (RetentionMetricFactory, CashflowForecastFactory, CostPerStudentFactory, FinancialSnapshotFactory)
  - [ ] Create backend/tests/unit/services/test_financial_health_service.py (~20 tests)
  - [ ] Create backend/tests/integration/api/test_financial_health_api.py (~12 tests)
  - [ ] Create backend/tests/security/test_finhealth_rbac.py (~10 tests: ADM/DIR can read, TCH/PAR/STD cannot, SYS can manage)
  - [ ] Create backend/tests/edge/test_finhealth_edge.py (~13 tests: no invoices, 100% retention, 0% collection, negative margins, division by zero students, MAD currency)
- [ ] **VERIFY**
  - [ ] pytest backend/tests/ -k "finhealth or financial_health" --tb=short (all pass)
  - [ ] pytest backend/tests/ -k "finhealth or financial_health" --cov=app --cov-report=term (coverage ≥ 80%)
  - [ ] Verify ~55 tests total
- [ ] **GIT**
  - [ ] Conditional commit: "test(finhealth): add tests and factories for financial health dashboard"

---

## Dependency Order & Mega-Prompts

### Execution Order (Impact-First)

Each feature is implemented fully (01→04) before moving to the next.
Within each feature, prompts must run sequentially: Models → Repo/Service → Endpoints → Tests.

```
┌──────────────────────────────────────────────────────────────────┐
│ PRIORITY 1 ★★★  Micro-École (strongest differentiator)          │
│   MICRO-01 → MICRO-02 → MICRO-03 → MICRO-04                    │
│   Commit after each prompt (if Codex)                            │
├──────────────────────────────────────────────────────────────────┤
│ PRIORITY 2 ★★★  Class Micro-Budget (quick win, clean workflow)  │
│   BUDGET-01 → BUDGET-02 → BUDGET-03 → BUDGET-04                │
├──────────────────────────────────────────────────────────────────┤
│ PRIORITY 3 ★★☆  Life Skills Passport (high parent appeal)      │
│   SKILL-01 → SKILL-02 → SKILL-03 → SKILL-04                    │
├──────────────────────────────────────────────────────────────────┤
│ PRIORITY 4 ★★☆  MEN Compliance (practical for inspections)     │
│   COMPLY-01 → COMPLY-02 → COMPLY-03 → COMPLY-04                │
│   Seed: Math + Arabic for Collège 3ème (~50 objectives)         │
├──────────────────────────────────────────────────────────────────┤
│ PRIORITY 5 ★☆☆  Local-First Sync (complex, foundational)       │
│   SYNC-01 → SYNC-02 → SYNC-03 → SYNC-04                        │
│   Full backend infrastructure (queue, conflicts, checkpoints)    │
├──────────────────────────────────────────────────────────────────┤
│ PRIORITY 6 ★☆☆  Financial Health (leverages billing data)       │
│   HEALTH-01 → HEALTH-02 → HEALTH-03 → HEALTH-04                │
├──────────────────────────────────────────────────────────────────┤
│ FINAL: Run GLOBAL-VERIFY                                         │
│   Check all 26 models, 74 endpoints, 350+ tests                 │
└──────────────────────────────────────────────────────────────────┘
```

### Dependencies Between Features

- Features are independent — no cross-feature dependencies
- Within each feature: X-01 → X-02 → X-03 → X-04 (strict order)
- HEALTH-01→04 benefits from existing billing data but does not require other innovation features
- COMPLY-01 includes a seed script; run it after migration to populate MEN reference data

### Three Mega-Prompts

#### GLOBAL-ANALYZE: Pre-flight Check

```markdown
## GLOBAL-ANALYZE: Read Entire Codebase

Before executing any feature prompts, run this analysis:

1. Read all existing code structure:
   - backend/app/models/*.py (all models, especially user, billing)
   - backend/app/repositories/*.py (all repository patterns)
   - backend/app/services/*.py (all service patterns)
   - backend/app/api/v1/*.py (all endpoint patterns)
   - backend/app/core/permissions.py (all existing perms)
   - backend/app/core/dependencies.py (auth/perm checks)
   - backend/app/core/response.py (response helpers)
   - backend/app/core/exceptions.py (all custom exceptions)
   - backend/alembic/versions/ (migration patterns)
   - backend/tests/factories/*.py (factory patterns)
   - backend/tests/unit/services/*.py (test patterns)
   - backend/tests/security/*.py (RBAC test patterns)

2. Verify environment:
   - Python 3.11+
   - FastAPI, SQLAlchemy 2.0, Alembic, Pydantic
   - PostgreSQL testcontainer available
   - pytest, pytest-asyncio installed

3. Document findings:
   - List all RoleCode enum values
   - List all existing permission groups
   - List all response helper functions
   - List all custom exceptions
   - Identify any naming conflicts with planned feature names

Output: Checklist of 20+ verification items, all passing before proceeding
```

#### GLOBAL-EXECUTE: Run All 24 Prompts

**Behavior:** Execute each prompt as a standalone unit — ANALYZE → EXECUTE → VERIFY → GIT COMMIT.
After each prompt completes and commits, move to the next. This is identical to copy-pasting each prompt one by one. Do NOT skip the git step between prompts.

```markdown
## GLOBAL-EXECUTE: Sequential Feature Implementation

You are executing 24 prompts in strict order. For EACH prompt:
1. Run its ANALYZE phase (read files listed in the checklist)
2. Run its EXECUTE phase (create/modify files)
3. Run its VERIFY phase (run checks, fix any errors)
4. Run GIT: git add -A && git commit -m "<COMMIT_MSG>"
5. Print "✓ PROMPT {ID} COMPLETE" before moving to the next

IMPORTANT RULES:
- EVERY prompt gets its own separate git commit
- If a VERIFY step fails, fix the issue BEFORE committing
- Do NOT batch multiple prompts into one commit
- Do NOT skip any prompt
- If you run out of context or time, print "PAUSED AT: {PROMPT_ID}" so I can say "continue"
- The git behavior is: ALWAYS commit (whether Codex or Claude Code), because this mega-prompt is meant to be autonomous

### EXECUTION SEQUENCE (Impact-First Order):

═══════════════════════════════════════════════════════
FEATURE 1: MICRO-ÉCOLE (Priority ★★★)
═══════════════════════════════════════════════════════

PROMPT 1/24 — MICRO-01: Models & Migrations
  → Read: models/billing.py, models/lms.py, core/permissions.py, models/__init__.py
  → Create: models/micro_school.py (6 models: MicroSchool, MicroGroup, MicroEnrollment, MicroPayment, MicroResource, MicroProgressLog)
  → Create: alembic migration for 6 tables
  → Modify: core/permissions.py (add 13 PERM_MICRO_* constants + EDUCATOR role mapping)
  → Create: domain/events/micro_school.py
  → Modify: models/__init__.py (add imports)
  → Verify: alembic upgrade head, downgrade -1, upgrade head
  → Verify: python -c "from app.models.micro_school import *"
  → GIT: git add -A && git commit -m "feat(micro-ecole): add 6 models, migration, and 13 permissions for micro-school module"

PROMPT 2/24 — MICRO-02: Repository & Service
  → Read: repositories/base.py, repositories/billing.py, services/billing.py
  → Create: schemas/micro_school.py (14 schemas: create/update/response for each entity)
  → Create: repositories/micro_school.py (MicroSchoolRepository with CRUD for all 6 entities)
  → Create: services/micro_school_service.py (MicroSchoolService, MicroGroupService, MicroPaymentService, MicroProgressService)
  → Verify: python -c "from app.services.micro_school_service import *"
  → Verify: python -c "from app.schemas.micro_school import *"
  → GIT: git add -A && git commit -m "feat(micro-ecole): add repository, service, and schemas for micro-school module"

PROMPT 3/24 — MICRO-03: API Endpoints
  → Read: api/v1/billing.py, api/v1/router.py
  → Create: api/v1/micro_school.py (14 endpoints)
  → Modify: api/v1/router.py (register micro_school_router)
  → Verify: python -c "from app.api.v1.micro_school import router"
  → GIT: git add -A && git commit -m "feat(micro-ecole): add 14 API endpoints for micro-school module"

PROMPT 4/24 — MICRO-04: Tests & Factories
  → Read: tests/factories/billing.py, tests/unit/services/test_billing_service.py, tests/security/test_rbac_matrix.py
  → Create: tests/factories/micro_school.py (6 factories)
  → Create: tests/unit/services/test_micro_school_service.py (~25 tests)
  → Create: tests/integration/api/test_micro_school_api.py (~15 tests)
  → Create: tests/security/test_micro_school_rbac.py (~12 tests)
  → Create: tests/edge/test_micro_school_edge.py (~8 tests)
  → Verify: pytest backend/tests/ -k "micro" --tb=short (all pass)
  → Verify: pytest backend/tests/ -k "micro" --cov=app --cov-report=term (coverage ≥ 80%)
  → GIT: git add -A && git commit -m "test(micro-ecole): add 60 tests and factories for micro-school module"

═══════════════════════════════════════════════════════
FEATURE 2: CLASS MICRO-BUDGET (Priority ★★★)
═══════════════════════════════════════════════════════

PROMPT 5/24 — BUDGET-01: Models & Migrations
  → Create: models/budget.py (4 models: MicroBudget, BudgetAllocation, BudgetRequest, BudgetTransaction)
  → Create: alembic migration for 4 tables
  → Modify: core/permissions.py (add 10 PERM_BUDGET_* constants)
  → Create: domain/events/budget.py
  → Verify: alembic upgrade/downgrade round-trip
  → GIT: git add -A && git commit -m "feat(budget): add 4 models, migration, and 10 permissions for class micro-budget"

PROMPT 6/24 — BUDGET-02: Repository & Service
  → Create: schemas/budget.py, repositories/budget.py, services/budget_service.py
  → Implement: allocation flow, request→approve→deduct workflow, budget analytics
  → Verify: import checks
  → GIT: git add -A && git commit -m "feat(budget): add repository, service, and schemas for class micro-budget"

PROMPT 7/24 — BUDGET-03: API Endpoints
  → Create: api/v1/budgets.py (14 endpoints)
  → Modify: api/v1/router.py
  → Verify: endpoint registration
  → GIT: git add -A && git commit -m "feat(budget): add 14 API endpoints for class micro-budget"

PROMPT 8/24 — BUDGET-04: Tests & Factories
  → Create: factories, unit tests, integration tests, security tests, edge tests (~60 total)
  → Verify: pytest -k "budget" all pass, coverage ≥ 80%
  → GIT: git add -A && git commit -m "test(budget): add 60 tests and factories for class micro-budget"

═══════════════════════════════════════════════════════
FEATURE 3: LIFE SKILLS PASSPORT (Priority ★★☆)
═══════════════════════════════════════════════════════

PROMPT 9/24 — SKILL-01: Models & Migrations
  → Create: models/skill_passport.py (4 models: SkillDimension, SkillMilestone, SkillProgress, SkillPassport)
  → Create: alembic migration, permissions (8 PERM_SKILL_*), domain events
  → Verify: migration round-trip
  → GIT: git add -A && git commit -m "feat(skills): add 4 models, migration, and 8 permissions for life skills passport"

PROMPT 10/24 — SKILL-02: Repository & Service
  → Create: schemas, repository, service (including milestone evaluation engine + PDF generation)
  → Verify: import checks
  → GIT: git add -A && git commit -m "feat(skills): add repository, service, and schemas for life skills passport"

PROMPT 11/24 — SKILL-03: API Endpoints
  → Create: api/v1/skills.py (12 endpoints)
  → Modify: router.py
  → GIT: git add -A && git commit -m "feat(skills): add 12 API endpoints for life skills passport"

PROMPT 12/24 — SKILL-04: Tests & Factories
  → Create: tests (~65 total)
  → Verify: all pass
  → GIT: git add -A && git commit -m "test(skills): add 65 tests and factories for life skills passport"

═══════════════════════════════════════════════════════
FEATURE 4: MEN COMPLIANCE CHECKER (Priority ★★☆)
═══════════════════════════════════════════════════════

PROMPT 13/24 — COMPLY-01: Models & Migrations
  → Create: models/men_compliance.py (4 models: MenCurriculum, MenObjective, CurriculumMapping, ComplianceReport)
  → Create: alembic migration, permissions (8 PERM_COMPLY_*), domain events
  → Create: scripts/seed_men_curriculum.py (seed Math + Arabic for Collège 3ème, ~50 objectives)
  → Verify: migration round-trip, run seed script
  → GIT: git add -A && git commit -m "feat(compliance): add 4 models, migration, 8 permissions, and MEN seed data"

PROMPT 14/24 — COMPLY-02: Repository & Service
  → Create: schemas, repository, service (compliance % calculator, PDF report generation)
  → Verify: import checks
  → GIT: git add -A && git commit -m "feat(compliance): add repository, service, and schemas for MEN compliance"

PROMPT 15/24 — COMPLY-03: API Endpoints
  → Create: api/v1/compliance.py (12 endpoints)
  → Modify: router.py
  → GIT: git add -A && git commit -m "feat(compliance): add 12 API endpoints for MEN compliance checker"

PROMPT 16/24 — COMPLY-04: Tests & Factories
  → Create: tests (~55 total)
  → Verify: all pass
  → GIT: git add -A && git commit -m "test(compliance): add 55 tests and factories for MEN compliance checker"

═══════════════════════════════════════════════════════
FEATURE 5: LOCAL-FIRST SYNC (Priority ★☆☆)
═══════════════════════════════════════════════════════

PROMPT 17/24 — SYNC-01: Models & Migrations
  → Create: models/sync_queue.py (4 models: SyncDevice, SyncQueue, SyncConflict, SyncCheckpoint)
  → Create: alembic migration, permissions (8 PERM_SYNC_*), domain events
  → Verify: migration round-trip
  → GIT: git add -A && git commit -m "feat(sync): add 4 models, migration, and 8 permissions for local-first sync"

PROMPT 18/24 — SYNC-02: Repository & Service
  → Create: schemas, repository, service (push/pull logic, conflict resolution engine, checkpoint management)
  → Verify: import checks
  → GIT: git add -A && git commit -m "feat(sync): add repository, service, and schemas for local-first sync"

PROMPT 19/24 — SYNC-03: API Endpoints
  → Create: api/v1/sync.py (10 endpoints)
  → Modify: router.py
  → GIT: git add -A && git commit -m "feat(sync): add 10 API endpoints for local-first sync"

PROMPT 20/24 — SYNC-04: Tests & Factories
  → Create: tests (~55 total)
  → Verify: all pass
  → GIT: git add -A && git commit -m "test(sync): add 55 tests and factories for local-first sync"

═══════════════════════════════════════════════════════
FEATURE 6: FINANCIAL HEALTH DASHBOARD (Priority ★☆☆)
═══════════════════════════════════════════════════════

PROMPT 21/24 — HEALTH-01: Models & Migrations
  → Create: models/financial_health.py (4 models: RetentionMetric, CashflowForecast, CostPerStudent, FinancialSnapshot)
  → Create: alembic migration, permissions (6 PERM_FINHEALTH_*), domain events
  → Verify: migration round-trip
  → GIT: git add -A && git commit -m "feat(finhealth): add 4 models, migration, and 6 permissions for financial health dashboard"

PROMPT 22/24 — HEALTH-02: Repository & Service
  → Create: schemas, repository, service (retention calculator, cashflow forecast, cost-per-student, financial snapshot)
  → Verify: import checks
  → GIT: git add -A && git commit -m "feat(finhealth): add repository, service, and schemas for financial health dashboard"

PROMPT 23/24 — HEALTH-03: API Endpoints
  → Create: api/v1/financial_health.py (12 endpoints)
  → Modify: router.py
  → GIT: git add -A && git commit -m "feat(finhealth): add 12 API endpoints for financial health dashboard"

PROMPT 24/24 — HEALTH-04: Tests & Factories
  → Create: tests (~55 total)
  → Verify: all pass
  → GIT: git add -A && git commit -m "test(finhealth): add 55 tests and factories for financial health dashboard"

═══════════════════════════════════════════════════════
DONE: Print final summary
═══════════════════════════════════════════════════════

After all 24 prompts complete:
  git log --oneline -24  (show all 24 commits)
  echo "✓ ALL 24 PROMPTS COMPLETE — Ready for GLOBAL-VERIFY"
```

#### GLOBAL-VERIFY: Final Integration Check

```markdown
## GLOBAL-VERIFY: Integration & Sanity Check

After all 24 prompts complete, run comprehensive verification:

1. **Database Schema**
   - [ ] All 26 new feature tables exist among the public tables: `SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('micro_schools','micro_groups','micro_enrollments','micro_payments','micro_resources','micro_progress_logs','sync_devices','sync_queue','sync_conflicts','sync_checkpoints','skill_dimensions','skill_milestones','skill_progress','skill_passports','men_curricula','men_objectives','curriculum_mappings','compliance_reports','micro_budgets','budget_allocations','budget_requests','budget_transactions','retention_metrics','cashflow_forecasts','cost_per_student','financial_snapshots');`
   - [ ] All foreign keys valid: Check CASCADE constraints
   - [ ] All CHECK constraints in place: Amounts > 0, grades 0-20, etc.
   - [ ] All indexes present on FK columns

2. **Code Quality**
   - [ ] No unused imports
   - [ ] New feature files pass mypy: `mypy --strict --follow-imports=silent backend/app/models/micro_school.py backend/app/models/sync_queue.py backend/app/models/skill_passport.py backend/app/models/men_compliance.py backend/app/models/budget.py backend/app/models/financial_health.py backend/app/services/micro_school_service.py backend/app/services/sync_queue_service.py backend/app/services/skill_passport_service.py backend/app/services/compliance_service.py backend/app/services/budget_service.py backend/app/services/financial_health_service.py backend/app/repositories/micro_school.py backend/app/repositories/sync_queue.py backend/app/repositories/skill_passport.py backend/app/repositories/men_compliance.py backend/app/repositories/budget.py backend/app/repositories/financial_health.py backend/app/schemas/micro_school.py backend/app/schemas/sync_queue.py backend/app/schemas/skill_passport.py backend/app/schemas/men_compliance.py backend/app/schemas/budget.py backend/app/schemas/financial_health.py backend/app/api/v1/micro_school.py backend/app/api/v1/sync.py backend/app/api/v1/skills.py backend/app/api/v1/compliance.py backend/app/api/v1/budgets.py backend/app/api/v1/financial_health.py`
   - [ ] All new feature modules, public classes, and feature route handlers have docstrings: `ruff check backend/app/models/micro_school.py backend/app/models/sync_queue.py backend/app/models/skill_passport.py backend/app/models/men_compliance.py backend/app/models/budget.py backend/app/models/financial_health.py backend/app/services/micro_school_service.py backend/app/services/sync_queue_service.py backend/app/services/skill_passport_service.py backend/app/services/compliance_service.py backend/app/services/budget_service.py backend/app/services/financial_health_service.py backend/app/repositories/micro_school.py backend/app/repositories/sync_queue.py backend/app/repositories/skill_passport.py backend/app/repositories/men_compliance.py backend/app/repositories/budget.py backend/app/repositories/financial_health.py backend/app/schemas/micro_school.py backend/app/schemas/sync_queue.py backend/app/schemas/skill_passport.py backend/app/schemas/men_compliance.py backend/app/schemas/budget.py backend/app/schemas/financial_health.py backend/app/api/v1/micro_school.py backend/app/api/v1/sync.py backend/app/api/v1/skills.py backend/app/api/v1/compliance.py backend/app/api/v1/budgets.py backend/app/api/v1/financial_health.py --select D100,D101,D103,D104`
   - [ ] All permission checks in place

3. **API Contract**
   - [ ] All 74 new feature endpoints registered. Verify route prefixes in OpenAPI: `/api/v1/micro`, `/api/v1/budgets`, `/api/v1/sync`, `/api/v1/skills`, `/api/v1/compliance`, `/api/v1/financial-health`. Expected total: 14 + 14 + 10 + 12 + 12 + 12 = 74 endpoints across the six feature domains.
   - [ ] All endpoints have correct HTTP methods, status codes
   - [ ] All endpoints have correct permission checks
   - [ ] All request/response schemas documented

4. **Test Coverage**
   - [ ] Total test count >= 350: `pytest --collect-only | grep "test_" | wc -l`
   - [ ] All tests pass: `pytest -v --tb=short`
   - [ ] Coverage >= 80%: `pytest --cov=backend/app --cov-report=term-missing`
   - [ ] All RBAC tests pass: `pytest backend/tests/security/ -v`

5. **Git History**
   - [ ] At least 24 commits present (one per prompt), plus any verification fix commits: `git log --oneline b76c192..HEAD | wc -l` >= 24
   - [ ] Each commit message follows conventional commits: `type(scope): description` where `type` is `feat`, `test`, or `fix`. Verify all commits since `b76c192` match `^(feat|test|fix)\\(.+\\):`
   - [ ] No uncommitted changes: `git status` shows clean

6. **Data Integrity**
   - [ ] All Moroccan sample data loads correctly
   - [ ] All timezone conversions work (Africa/Casablanca)
   - [ ] All monetary values use MAD (Moroccan Dirham): the `Money` value object defaults to MAD and rejects mixed-currency operations

Output: Green checklist with 50+ items, all passing. Ready for QA.
```

---

## Summary & Success Criteria

### Feature Completion Metrics

| Feature | Models | Endpoints | Tests | Status |
|---------|--------|-----------|-------|--------|
| Micro-École | 6 | 14 | ~60 | READY |
| Local-First Sync | 4 | 10 | ~55 | READY |
| Life Skills Passport | 4 | 12 | ~65 | READY |
| MEN Compliance | 4 | 12 | ~55 | READY |
| Class Micro-Budget | 4 | 14 | ~60 | READY |
| Financial Health | 4 | 12 | ~55 | READY |
| **TOTALS** | **26** | **74** | **~350** | **READY** |

### Success Criteria Checklist

- [ ] All 26 models created with full type hints and docstrings
- [ ] All migrations pass alembic upgrade/downgrade round-trip
- [ ] All 74 endpoints registered, documented, and permission-checked
- [ ] All 350+ tests pass with >=80% coverage
- [ ] No TypeErrors, ImportErrors, or SQLAlchemy warnings
- [ ] All Moroccan context data (grades, currency, phones, timezone) implemented correctly
- [ ] All 3-tier architecture (Router → Service → Repository) followed consistently
- [ ] All domain events emitted at business logic points
- [ ] All permission checks enforced at endpoint level
- [ ] All RBAC boundary tests pass
- [ ] All requests use success_response() / list_response() helpers
- [ ] All models use Mapped[] columns with explicit mapped_column()
- [ ] All services use AsyncSession pattern
- [ ] All repositories extend BaseRepository
- [ ] 24 git commits, one per prompt, all with descriptive messages
- [ ] Zero technical debt: all code is production-ready
- [ ] Documentation complete in this roadmap file

### Time Estimate

- **Total Implementation Time:** ~17 hours
  - Phase 1 (Models): 3-4 hours
  - Phase 2 (Repositories & Services): 4-5 hours
  - Phase 3 (API Endpoints): 4-5 hours
  - Phase 4 (Tests): 4-5 hours

---

## Quick Reference: File Locations

```
Backend Root: /sessions/confident-sweet-faraday/mnt/Ecole-Platform/ecole-platform-dev/backend

Models:
  - micro_school.py
  - sync_queue.py
  - skill_passport.py
  - men_compliance.py
  - budget.py
  - financial_health.py

Repositories:
  - micro_school.py
  - sync_queue.py
  - skill_passport.py
  - men_compliance.py
  - budget.py
  - financial_health.py

Services:
  - micro_school_service.py
  - sync_service.py
  - skill_passport_service.py
  - men_compliance_service.py
  - budget_service.py
  - financial_health_service.py

Schemas:
  - micro_school.py
  - sync.py
  - skill_passport.py
  - men_compliance.py
  - budget.py
  - financial_health.py

API Routers:
  - micro_school.py
  - sync.py
  - skill_passport.py
  - men_compliance.py
  - budget.py
  - financial_health.py

Tests - Factories:
  - micro_school.py
  - sync.py
  - skill_passport.py
  - men_compliance.py
  - budget.py
  - financial_health.py

Tests - Unit Services:
  - test_micro_school_service.py
  - test_sync_service.py
  - test_skill_passport_service.py
  - test_men_compliance_service.py
  - test_budget_service.py
  - test_financial_health_service.py

Tests - Integration API:
  - test_micro_school_api.py
  - test_sync_api.py
  - test_skill_passport_api.py
  - test_men_compliance_api.py
  - test_budget_api.py
  - test_financial_health_api.py

Tests - Security/RBAC:
  - test_micro_school_rbac.py
  - test_sync_rbac.py
  - test_skill_passport_rbac.py
  - test_men_compliance_rbac.py
  - test_budget_rbac.py
  - test_financial_health_rbac.py
```

---

## End of Roadmap

**Document Status:** Complete and Ready for Execution
**Last Updated:** April 2026
**Target Audiences:** Codex, Claude Code, Human Developers
**Execution Model:** Autonomous sequential prompts with conditional git integration

All 24 prompts are self-contained, copy-paste ready, and follow identical patterns for output consistency across execution environments.
