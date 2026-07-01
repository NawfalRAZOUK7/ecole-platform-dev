# Step 1 — Project Structure Analysis

## 1.1 Global Project Overview

École Platform is a **modular monolith** SaaS platform for K-12 school management in Morocco. The codebase is organized as a single Git repository (monorepo) containing three independently deployable applications that share a common API contract:

| Layer | Technology | Files | Lines of Code |
|-------|-----------|-------|---------------|
| Backend API | Python 3.12 + FastAPI | 305 `.py` | ~95,000 LOC |
| Web Frontend | React 18 + TypeScript | 353 `.ts/.tsx` | ~55,000 LOC |
| Mobile App | Flutter 3 + Dart | 286 `.dart` | ~62,000 LOC |
| **Total** | | **944** | **~212,000 LOC** |

Additional components: 65+ Alembic migrations, 182 backend test files, 307 web test files, 41 mobile test files, 9 CI/CD workflows, 15 Kubernetes templates, 8 Grafana dashboards.

The monorepo approach was chosen deliberately: all three applications evolve against the same API contract, share the same deployment pipeline, and are maintained by a single developer (PFE context). This avoids the overhead of multi-repo synchronization while keeping clear separation between concerns.

---

## 1.2 Backend Architecture (Python/FastAPI)

### 1.2.1 Layered Architecture — Router → Service → Repository

The backend follows a strict **4-layer architecture** enforced by import direction:

```
┌─────────────────────────────────────────────┐
│  API Layer (api/v1/)                        │  ← 57 route modules
│  FastAPI routers, request/response handling  │
├─────────────────────────────────────────────┤
│  Service Layer (services/)                  │  ← 72 service files
│  Business logic, orchestration, validation  │
├─────────────────────────────────────────────┤
│  Repository Layer (repositories/)           │  ← 38 repository files
│  Data access, async queries, school-scoping │
├─────────────────────────────────────────────┤
│  Domain Layer (domain/ + models/)           │  ← 24 models + 19 domain files
│  SQLAlchemy ORM, domain events, value objs  │
└─────────────────────────────────────────────┘
```

**Import rules observed in the code:**
- Routes import Services (never Repositories directly)
- Services import Repositories (never Models directly for queries)
- Repositories inherit from `BaseRepository` which holds the `AsyncSession`
- Domain layer has zero dependencies on upper layers

### 1.2.2 Entry Point (`app/main.py`)

The application bootstraps via FastAPI's `lifespan` context manager:

1. **Startup**: Initializes WebSocket manager (`ws_manager.startup()`), optionally runs seed data for staging environments
2. **Middleware stack** (registered in order — outermost first):
   - `CorrelationIdMiddleware` — generates/propagates `X-Correlation-Id` via `contextvars`
   - `IdempotencyMiddleware` — deduplicates POST/PUT/PATCH requests via `Idempotency-Key` header
   - `RateLimitMiddleware` — Redis-backed token bucket with per-endpoint categories
   - `CORSMiddleware` — configured origins, exposes rate-limit and correlation headers
3. **Prometheus metrics** registered via `register_metrics(app)` before middleware
4. **OpenTelemetry tracing** conditionally enabled via `settings.enable_tracing`
5. **Shutdown**: Closes ARQ task pool and WebSocket manager

### 1.2.3 Router Aggregation (`api/v1/router.py`)

All 57 sub-routers are aggregated in a single `APIRouter` mounted at `/api/v1`. The router file also defines two system endpoints:
- `GET /health` — simple health check returning `{"status": "healthy", "version": "0.1.0"}`
- `GET /readiness` — deep probe that verifies PostgreSQL (`SELECT 1`) and Redis (`PING`) connectivity, returning HTTP 503 if degraded

Sub-routers are organized by development phase (Phase 2, 3, 4, 8, 9, 11, 14, 15, 16) reflecting the incremental development methodology.

### 1.2.4 Core Infrastructure (`core/`)

The `core/` package contains 26 modules providing cross-cutting infrastructure:

| Module | Purpose |
|--------|---------|
| `config.py` | Pydantic `BaseSettings` with env vars, Docker secret file support (`_FILE` suffix pattern) |
| `database.py` | Async SQLAlchemy engine (pool_size=20, max_overflow=10, pool_pre_ping), `Base` declarative base, `TimestampMixin`, `SchoolScopedMixin`, `SoftDeleteMixin` |
| `dependencies.py` | FastAPI DI: `get_current_user` (AuthN), `RequiresPermission` (RBAC), `RequiresRole`, ABAC guards (`verify_school_boundary`, `verify_parent_child_ownership`, `verify_teacher_assignment`) |
| `security.py` | JWT encoding/decoding, password hashing (bcrypt) |
| `permissions.py` | Role-permission matrix (5 roles × N permissions), `role_has_permission()` lookup |
| `middleware.py` | `CorrelationIdMiddleware`, structured error handlers (Domain, Validation, Generic) |
| `rate_limit.py` | Redis-backed rate limiter with `X-RateLimit-*` response headers |
| `idempotency.py` | Idempotency-Key support for mutation endpoints |
| `redis.py` | Async Redis client dependency |
| `ws_manager.py` | WebSocket connection manager with Redis Pub/Sub for horizontal scaling |
| `unit_of_work.py` | Transaction boundary pattern with nestable depth tracking |
| `abac.py` | Attribute-Based Access Control rules |
| `telemetry.py` | OpenTelemetry tracing integration (Tempo exporter) |
| `metrics.py` | Prometheus instrumentation |
| `filtering.py` | Dynamic query filtering utilities |
| `search.py` | Full-text search helpers |
| `feature_flags.py` | Runtime feature toggle system |
| `tasks.py` | ARQ (async Redis queue) task management |
| `exceptions.py` | Domain exception hierarchy with error categories |
| `response.py` | Standardized response envelope builders |
| `password_policy.py` | Password complexity rules |
| `totp.py` | TOTP/2FA implementation |
| `storage.py` | File storage abstraction (local/MinIO/S3) |
| `db_routing.py` | Read replica routing logic |
| `business_metrics.py` | Business KPI computation |
| `request_utils.py` | Request parsing utilities |

### 1.2.5 Domain Layer (`domain/`)

The domain layer is organized into three sub-packages:

1. **Events** (`domain/events/`): 15 event modules defining domain events as frozen dataclasses. Base `DomainEvent` carries `event_id`, `occurred_at`, `school_id`, `actor_id`. Concrete events include `GradePublished`, `AssignmentCreated`, `PaymentReceived`, `DocumentUploaded`, `AttendanceThresholdExceeded`, etc.

2. **Value Objects** (`domain/value_objects/`): Immutable types — `Grade` (score validation), `Money` (currency arithmetic), `RoleSet` (role collection), `TypedId` (type-safe UUID wrappers).

3. **Protocols** (`domain/protocols/`): Python `Protocol` interfaces — `Evaluatable` (grading contract), `Grading` (grading strategy).

### 1.2.6 Repository Pattern (`repositories/`)

All 38 repositories extend `BaseRepository` which provides:
- `self.db: AsyncSession` — injected via constructor
- `_scoped_query(model, school_id)` — pre-filtered SELECT for school isolation
- `_scoped_exists(model, entity_id, school_id)` — existence check within school boundary

This enforces **multi-tenant school isolation at the data access level** — every query is automatically scoped to the authenticated user's school.

### 1.2.7 Service Layer (`services/`)

72 service files organized by domain, with notable sub-packages:
- `services/delivery/` — Notification delivery strategy pattern with `base.py` interface and 4 implementations: `InAppDeliveryStrategy`, `PushDeliveryStrategy`, `EmailDeliveryStrategy`, `SmsDeliveryStrategy`
- `services/lms/` — LMS-specific service decomposition: `assignment_service.py`, `content_service.py`, `course_service.py`, `grading_service.py`, `progress_service.py`, `quiz_service.py` with shared `_helpers.py` and `_serializers.py`

### 1.2.8 Schema Layer (`schemas/`)

34 Pydantic v2 schema modules defining request/response models. Schemas are strictly separated from ORM models — services perform the translation. This enables API evolution independent of database schema.

---

## 1.3 Frontend Web Architecture (React/TypeScript)

### 1.3.1 Feature-First Organization

The web application follows a **feature-first** architecture with 37 feature modules:

```
web/src/
├── app/              # App root, routing (App.tsx, LazyPages.tsx)
├── features/         # 37 feature modules (self-contained)
│   ├── auth/         # Login, register, forgot password, role guards
│   ├── admin/        # Dashboard, users, invitations, audit, settings
│   ├── teacher/      # Classes, courses, submissions, attendance
│   ├── student/      # Home, content, quiz, story viewer
│   ├── rewards/      # Stars, XP, badges, leaderboard
│   ├── games/        # Game configs, game player
│   ├── attendance/   # Marking, history, analytics, justifications
│   ├── billing/      # Fee structures, invoices, payment plans
│   ├── ... (30 more modules)
│   └── sync/         # Offline sync status, conflicts
├── services/         # Global services
│   ├── api/client.ts      # Unified fetch-based API client
│   ├── auth/AuthContext.tsx # React Context for auth state
│   ├── ws/WebSocketClient.ts # Real-time WebSocket
│   ├── rewards.service.ts # Rewards data normalization
│   ├── games.service.ts   # Games API service
│   └── levels.service.ts  # Level system service
└── shared/           # Reusable code
    ├── ui/           # 30+ UI components (StatCard, DataTable, PlatformBridgeCard, etc.)
    ├── hooks/        # Custom hooks (useTheme, useAgeTheme, useNetworkStatus, etc.)
    ├── i18n/         # i18next setup + 3 locale files (ar.json, fr.json, en.json)
    ├── types/        # Shared TypeScript types (api.ts, models.ts, forms.ts)
    ├── styles/       # Age-based CSS themes (maternelle, primaire, college)
    └── validation/   # Zod validation schemas
```

### 1.3.2 Each Feature Module Pattern

Every feature module is self-contained with:
- **Page component(s)** — e.g., `AttendancePage.tsx`, `AttendanceHistoryPage.tsx`
- **Service file** — API calls and data transformation (e.g., `attendance.service.ts`)
- **Custom hook** — React Query integration (e.g., `useAttendance.ts`)
- **Types** (optional) — module-specific TypeScript interfaces

### 1.3.3 API Client Architecture

The API client (`services/api/client.ts`) is a custom fetch-based implementation (no Axios) with:
- **In-memory access token** (never stored in localStorage — security decision)
- **Auto-refresh on 401** with deduplication of concurrent refresh calls (`refreshPromise` singleton)
- **Exponential backoff** for retryable errors (up to 3 retries)
- **Mandatory headers**: `Authorization`, `Accept-Language` (from i18next), `X-Correlation-Id` (crypto.randomUUID), `X-Client-Version`, `X-Client-Platform: web`
- **Typed convenience methods**: `api.get<T>()`, `api.list<T>()`, `api.post<T>()`, `api.patch<T>()`, `api.put<T>()`, `api.delete<T>()`
- **Cursor-based pagination** support via `ApiListResponse<T>` envelope

### 1.3.4 Authentication Context

`AuthContext.tsx` provides:
- React Context wrapping auth state: `user`, `isAuthenticated`, `isLoading`, `error`, `twoFactorPending`
- Methods: `login()`, `verify2fa()`, `cancel2fa()`, `logout()`, `clearError()`
- 2FA flow: login returns `tempToken` → user enters TOTP code → `verify2fa()` completes
- Error mapping: backend error codes are mapped to i18n translation keys

### 1.3.5 Routing Strategy

React Router v6 with:
- `ProtectedRoute` component wrapping role-based guards (`roles={['ADM', 'DIR']}`)
- `RoleRedirect` at `/` redirecting to role-appropriate home page
- Lazy-loaded pages via `React.lazy()` (code splitting) defined in `LazyPages.tsx`
- Suspense fallback to `<LoadingState />`

### 1.3.6 Shared UI Components

30+ reusable components including:
- `PlatformBridgeCard` — informs users when a feature is available on another platform (mobile/web)
- `DataTable` — sortable, filterable table with cursor pagination
- `StatCard` — metric display with trend indicator (direction + percentage)
- `CelebrationOverlay` — confetti animation for gamification rewards
- `OfflineIndicator` — network status banner
- Age-based themes (`maternelle.css`, `primaire.css`, `college.css`) with `useAgeTheme` hook

---

## 1.4 Mobile Architecture (Flutter/Dart)

### 1.4.1 Clean Architecture Layers

The mobile app follows **Clean Architecture** with strict layer separation:

```
mobile/lib/
├── app/              # App configuration
│   ├── providers.dart    # Riverpod DI — wires repos to API client
│   └── router.dart       # GoRouter with auth guards
├── domain/           # Business rules (pure Dart, no framework dependencies)
│   ├── entities/         # 27 entity files (data models)
│   └── repositories/     # 21 abstract repository interfaces
├── data/             # Implementation details
│   ├── api/              # Dio HTTP client + WebSocket client
│   ├── dto/mappers.dart  # DTO-to-entity mapping
│   ├── local_store/      # SQLite/SharedPreferences offline storage (8 stores)
│   └── repositories_impl/ # 25+ concrete repository implementations
├── features/         # 35 feature modules (UI + state)
├── presentation/     # Shell screen (bottom navigation)
├── shared/           # Cross-cutting utilities
│   ├── ui/               # Theme, tokens (colors, spacing, typography, radii)
│   ├── widgets/          # 15+ reusable widgets
│   └── services/         # Offline content manager, TTS service
└── l10n/             # Localization files
```

### 1.4.2 Dependency Injection via Riverpod

`providers.dart` defines the global provider tree following a **3-layer chain**:
```
Providers (Riverpod) → Repository Implementations → API Client / Local Stores
```

Each repository is registered as a Riverpod provider, with the `ApiClient` and `CacheStore` injected. This enables:
- Easy testing via provider overrides
- Automatic dependency resolution
- Lifecycle management (dispose on container disposal)

### 1.4.3 Offline-First Infrastructure

The mobile app has significant offline support:
- **8 local stores**: `cache_store.dart`, `offline_queue.dart`, `attendance_store.dart`, `events_store.dart`, `documents_store.dart`, `notifications_store.dart`, `quiz_offline_store.dart`, `reports_store.dart`
- `OfflineQueue` — queues mutations when offline, replays when connectivity returns
- `ConnectivityService` — monitors network state
- `OfflineContentManager` — pre-caches content for offline access
- `SyncRepository` — server-side sync queue with conflict resolution

### 1.4.4 Mobile-Specific Features

Features unique to mobile (not on web):
- **Coloring book** (`features/coloring/`) — interactive drawing with `DrawingOverlay` widget
- **Educational games** — Memory Match, Sorting Game, Vocabulary Cards (dedicated screens)
- **Story reader** — Arabic letter learning with TTS (Text-to-Speech) integration
- **Biometric authentication** — fingerprint/face login
- **Push notifications** — Firebase Cloud Messaging integration
- **Secure storage** — Flutter Secure Storage for tokens

### 1.4.5 API Client (Dio)

`data/api/api_client.dart` mirrors the web client with:
- Dio HTTP client with interceptors
- Same mandatory headers (`Authorization`, `Accept-Language`, `X-Correlation-Id`, `X-Client-Version`, `X-Client-Platform: mobile`)
- Auto-refresh on 401 with retry
- Exponential backoff with jitter for retryable errors
- Token stored in Flutter Secure Storage (not SharedPreferences)

---

## 1.5 Internal Communication Flow

### 1.5.1 Request Flow (Backend)

```
Client Request
  ↓
CORS Middleware → Rate Limit → Idempotency → Correlation ID
  ↓
FastAPI Router (api/v1/*)
  ↓
AuthN Dependency (get_current_user) → JWT decode → Session verification
  ↓
RBAC Guard (RequiresPermission / RequiresRole)
  ↓
ABAC Guard (school boundary / parent-child / teacher-assignment)
  ↓
Service Layer (business logic)
  ↓
Repository Layer (school-scoped queries)
  ↓
PostgreSQL (async via SQLAlchemy 2.0)
```

### 1.5.2 Domain Event Flow

The `EventDispatcher` implements a **Strategy pattern** for multi-channel notification delivery:

```
Service performs action
  ↓
Creates DomainEvent (frozen dataclass)
  ↓
EventDispatcher.dispatch(event)
  ↓
Resolves recipients (student, parents, teachers, admins — context-dependent)
  ↓
Routes to registered handlers (per event type):
  → InAppDeliveryStrategy (stores in notifications table)
  → PushDeliveryStrategy (Firebase Cloud Messaging)
  → EmailDeliveryStrategy (SMTP via Jinja2 templates)
  → SmsDeliveryStrategy (SMS gateway)
```

20+ domain events are registered with specific delivery strategies. For example:
- `GradePublished` → Push + Email + In-App
- `InvoiceGenerated` → Push + Email
- `QuizCompleted` → In-App only
- `AttendanceThresholdExceeded` → Push + Email (high priority, includes admins)

### 1.5.3 Real-Time Communication

WebSocket connections are managed by `ws_manager` with Redis Pub/Sub for horizontal scaling:
- Backend: `core/ws_manager.py` manages connections per user
- Web: `services/ws/WebSocketClient.ts` connects with auth token
- Mobile: `data/api/ws_client.dart` mirrors the web implementation
- Events propagate server → Redis Pub/Sub → all connected instances → WebSocket → clients

---

## 1.6 Module Dependency Map

### 1.6.1 Backend Module Dependencies

```
IAM (auth, sessions, users, roles) ← Foundation, no dependencies
  ↑
ERP (schools, classes, enrollments, attendance, timetable)
  ↑
LMS (courses, assignments, submissions, content, quizzes, assessments)
  ↑
Communication (notifications, messaging, announcements, feed, calendar)
  ↑
Finance (invoices, payments, billing, budgets, financial health)
  ↑
Gamification (rewards, games, badges, levels, leaderboard)
  ↑
Analytics (reports, exports, dashboards, compliance)
```

Cross-cutting dependencies:
- **All modules** depend on IAM for authentication context
- **ERP** provides the organizational structure that LMS, Communication, and Finance operate within
- **Event Dispatcher** is the central coupling point — services emit events, the dispatcher handles multi-channel delivery
- **Audit service** is injected across modules for compliance logging

### 1.6.2 Frontend Dependency Rules

Feature modules follow strict isolation:
- Features **cannot** import from other features directly
- Inter-feature communication goes through `shared/` (UI components, hooks, types) or `services/` (API, auth, WebSocket)
- Only `app/App.tsx` imports from multiple features (for routing)

---

## 1.7 Architecture Observations

### 1.7.1 Key Design Decisions Observed in Code

1. **Modular Monolith over Microservices**: All 57 API modules live in one process. This is appropriate for a PFE-scale project — avoids distributed system complexity while maintaining clear module boundaries.

2. **School-Scoped Multi-Tenancy**: The `SchoolScopedMixin` and `BaseRepository._scoped_query()` enforce data isolation at the ORM level. Every query is automatically filtered by `school_id`, making cross-tenant data leakage structurally difficult.

3. **Security Pipeline as Dependency Chain**: The security pipeline (AuthN → Scope → RBAC → ABAC → Audit) is implemented as composable FastAPI dependencies, not middleware. This allows per-endpoint granularity and makes the security contract explicit in the route signature.

4. **Event-Driven Decoupling**: Services don't directly call notification logic. Instead, they emit domain events that the `EventDispatcher` routes to delivery strategies. This decouples business logic from notification concerns.

5. **Identical API Contract Across Clients**: Both web and mobile clients implement the same request pattern (mandatory headers, cursor pagination, error handling, retry logic). The API design drives both implementations.

6. **Offline-First Mobile Architecture**: The mobile app has 8 local stores and an offline queue, acknowledging that Moroccan network connectivity can be unreliable. The web app has a simpler `OfflineIndicator` — teachers/admins are expected to have stable connections.

7. **Age-Based UI Theming**: The web frontend has CSS themes per school level (maternelle, primaire, college), and the mobile app has `KidsContentColors`. This reflects the K-12 audience range — younger students need different visual treatment.

8. **Cross-Platform Bridge Pattern**: `PlatformBridgeCard` (implemented in both React and Flutter) explicitly handles feature asymmetry between platforms, directing users to the appropriate client rather than degrading silently.
