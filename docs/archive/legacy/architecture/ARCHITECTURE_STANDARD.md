# École Platform — Architecture Standard

> This document is the single source of truth for all code architecture.
> ALL code — whether written by Claude Code, Codex, or manually — MUST follow these patterns.
> Read this file FIRST before writing any code.

---

## Overview

| Layer | Pattern | Status |
|-------|---------|--------|
| Backend (FastAPI) | 3-Tier: Router → Service → Repository | Refactoring in progress |
| Web (React) | Feature + Hooks: Pages → Custom Hooks → API Services | Refactoring in progress |
| Mobile (Flutter) | Clean Architecture: Presentation → Domain → Data | Already correct |
| Infra | Docker multi-env + CI/CD + monitoring | Security hardening needed |

---

# PART A — Backend (FastAPI)

## 1. The 3-Tier Pattern

Every backend feature follows this flow:

```
Router (API layer)  →  Service (Business logic)  →  Repository (Data access)
```

**Router** — Handles HTTP. Parses request, validates input via Pydantic schemas, calls service, returns response. ZERO business logic, ZERO SQL.

**Service** — Orchestrates business rules. Calls one or more repositories. Handles authorization checks, transformations, side effects (email, push, audit). ZERO raw SQL, ZERO `AsyncSession`.

**Repository** — Executes database queries. Returns domain objects or primitives. ZERO business logic, ZERO HTTP concepts.

---

## 2. File Structure

```
backend/app/
├── api/v1/              # Routers (one per domain)
│   ├── auth.py
│   ├── admin.py
│   └── ...
├── services/            # Business logic (one per domain)
│   ├── auth.py
│   └── ...
├── repositories/        # Data access (one per domain)
│   ├── auth.py
│   ├── __init__.py
│   └── ...
├── models/              # SQLAlchemy models (unchanged)
├── schemas/             # Pydantic schemas (unchanged)
├── core/                # Shared utilities
│   ├── dependencies.py  # FastAPI DI (get_db, get_current_user, etc.)
│   ├── request_utils.py # Shared router helpers (see §5)
│   ├── exceptions.py
│   └── ...
└── main.py
```

---

## 3. Repository Pattern

### 3.1 Base Repository

```python
# backend/app/repositories/base.py
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    """Base repository with shared DB session."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
```

### 3.2 Domain Repository Example

```python
# backend/app/repositories/auth.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.models.iam import User, Membership, Session as UserSession
from app.repositories.base import BaseRepository


class AuthRepository(BaseRepository):
    """Data access for authentication and user management."""

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        stmt = (
            select(User)
            .options(selectinload(User.memberships))
            .where(User.id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_session(self, user_id: UUID, **kwargs) -> UserSession:
        session = UserSession(user_id=user_id, **kwargs)
        self.db.add(session)
        await self.db.flush()
        return session

    async def revoke_session(self, session_id: UUID) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(revoked=True)
        )
        await self.db.execute(stmt)
```

### 3.3 Rules

- One repository per domain (auth, billing, lms, erp, calendar, notifications, etc.)
- Methods return model instances or primitives — never raw `Row` objects.
- Complex joins use `selectinload` / `joinedload` — never manual `.join()` where ORM relationships exist.
- Cursor-based pagination uses a shared helper: `_apply_cursor(stmt, cursor, limit)`.
- Repository methods do NOT call `await self.db.commit()` — the service or router handles transaction boundaries.

---

## 4. Service Pattern

### 4.1 Service Example

```python
# backend/app/services/auth.py
from __future__ import annotations

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.auth import AuthRepository
from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthError


class AuthService:
    """Business logic for authentication."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AuthRepository(db)
        self.db = db  # only for commit/rollback

    async def login(self, email: str, password: str, ip: str, ua: str) -> dict:
        user = await self.repo.get_user_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("ERR-IAM-401", "Invalid credentials")

        if not user.is_active:
            raise AuthError("ERR-IAM-403", "Account disabled")

        session = await self.repo.create_session(
            user_id=user.id, ip_address=ip, user_agent=ua
        )
        await self.db.commit()

        token = create_access_token(user_id=str(user.id), session_id=str(session.id))
        return {"access_token": token, "user": user}
```

### 4.2 Rules

- Service `__init__` receives `AsyncSession` and creates its repository instances.
- Service NEVER writes raw SQL (`select`, `insert`, `update`).
- Service handles `await self.db.commit()` after the business operation succeeds.
- Service may call multiple repositories (e.g., `AuthRepository` + `AuditRepository`).
- Side effects (email, push, audit) are triggered from the service layer.

---

## 5. Router Pattern

### 5.1 Shared Helpers

All routers import shared helpers from one place:

```python
# backend/app/core/request_utils.py
from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For or direct connection."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def request_locale(request: Request) -> str:
    """Extract locale from Accept-Language header."""
    accept = request.headers.get("accept-language", "fr")
    return accept.split(",")[0].split("-")[0].strip()[:2]
```

### 5.2 Router Example

```python
# backend/app/api/v1/auth.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.request_utils import get_client_ip
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    svc = AuthService(db)
    result = await svc.login(
        email=body.email,
        password=body.password,
        ip=get_client_ip(request),
        ua=request.headers.get("user-agent", ""),
    )
    return LoginResponse(
        access_token=result["access_token"],
        user=result["user"],
    )
```

### 5.3 Rules

- Router NEVER instantiates a repository directly — only services.
- Router NEVER calls `db.execute()` or writes SQL.
- Router does NOT define local helper functions like `_get_client_ip()` — import from `core/request_utils.py`.
- OpenAPI metadata (`summary`, `response_description`) on every endpoint.
- Error responses use schemas from `core/exceptions.py`.

---

## 6. Naming Conventions

| Layer | File | Class | Method |
|-------|------|-------|--------|
| Router | `api/v1/auth.py` | — (functions) | `async def login()` |
| Service | `services/auth.py` | `AuthService` | `async def login()` |
| Repository | `repositories/auth.py` | `AuthRepository` | `async def get_user_by_email()` |
| Model | `models/iam.py` | `User` | — |
| Schema | `schemas/auth.py` | `LoginRequest` | — |

Repository method naming: `get_*`, `list_*`, `create_*`, `update_*`, `delete_*`, `count_*`, `exists_*`.

---

## 7. Dependency Injection Flow

```python
# In router:
db = Depends(get_db)           # AsyncSession
user = Depends(get_current_user)  # User model
svc = AuthService(db)           # Service creates its own repos

# In service:
self.repo = AuthRepository(db)  # One or more repos
self.audit = AuditRepository(db)

# In repository:
self.db = db                    # Raw session for queries
```

---

## 8. Testing Strategy

With repositories extracted, tests become:

- **Unit tests**: Mock the repository, test service logic in isolation.
- **Integration tests**: Hit the real API with Docker services (existing approach).
- **Repository tests**: Optional, test complex queries against a test DB.

```python
# Unit test example
async def test_login_invalid_password():
    mock_repo = AsyncMock(spec=AuthRepository)
    mock_repo.get_user_by_email.return_value = User(password_hash="wrong")

    svc = AuthService.__new__(AuthService)
    svc.repo = mock_repo

    with pytest.raises(AuthError):
        await svc.login("test@test.com", "bad", "127.0.0.1", "")
```

---

## 9. Migration Checklist (Per Service)

When refactoring a service to 3-tier:

- [ ] Create `repositories/{domain}.py` with `BaseRepository` subclass
- [ ] Move all `select()`, `insert()`, `update()`, `delete()` calls from service to repository
- [ ] Update service to instantiate repository in `__init__`
- [ ] Replace all `self.db.execute(select(...))` with `self.repo.method_name(...)`
- [ ] Service keeps only: business decisions, validations, orchestration, side effects
- [ ] Remove `from sqlalchemy import select, ...` from service (only keep `AsyncSession` for commit)
- [ ] Router unchanged (already calls service)
- [ ] Run existing tests — all must pass without modification
- [ ] Add OpenAPI metadata to router endpoints if missing

---

## 10. What NOT to Change (Backend)

- Models (`backend/app/models/`) — stay as-is
- Schemas (`backend/app/schemas/`) — stay as-is
- Core utilities (`backend/app/core/`) — stay as-is (except adding `request_utils.py` and `repositories/base.py`)
- Test assertions — must continue passing as-is

---

# PART B — Web Frontend (React)

## 11. The Hook + Service Pattern

Every web feature follows this flow:

```
Page (UI)  →  Custom Hook (state + logic)  →  API Service (HTTP calls)
```

**Page** — Renders UI. Calls a custom hook. Handles layout, user interaction, navigation. ZERO `api.get()` calls, ZERO `useState` for server data.

**Custom Hook** — Manages server state via React Query. Exposes data, loading, error, and mutation functions. Contains domain logic (filtering, sorting, transforms). ZERO direct `fetch` calls.

**API Service** — Pure functions that call the API client. Returns typed responses. ZERO React hooks, ZERO state.

---

## 12. Web File Structure

```
web/src/
├── app/
│   └── App.tsx              # Routes + guards (unchanged)
├── features/                 # Feature modules (unchanged structure)
│   ├── notifications/
│   │   ├── NotificationsPage.tsx    # UI only
│   │   ├── useNotifications.ts      # NEW: Custom hook
│   │   ├── notifications.service.ts # NEW: API service
│   │   └── types.ts                 # Types (unchanged)
│   ├── auth/
│   ├── admin/
│   └── ...
├── services/
│   ├── api/client.ts         # HTTP client (unchanged)
│   ├── auth/AuthContext.tsx   # Auth context (unchanged)
│   └── ws/WebSocketClient.ts # WebSocket (unchanged)
├── shared/
│   ├── hooks/
│   │   └── useQueryDefaults.ts # Shared React Query config
│   ├── i18n/
│   └── ui/
└── main.tsx                   # Add QueryClientProvider
```

---

## 13. API Service Pattern

### 13.1 Service Example

```typescript
// web/src/features/notifications/notifications.service.ts
import { api } from '@/services/api/client';
import type { NotificationItem, NotificationPreference } from './types';

export const notificationsService = {
  async list(params: { category?: string; read?: boolean; cursor?: string }) {
    return api.list<NotificationItem>('/notifications', params);
  },

  async markRead(id: string, read: boolean) {
    return api.patch<NotificationItem>(`/notifications/${id}/read`, { read });
  },

  async markAllRead() {
    return api.patch<void>('/notifications/mark-all-read', {});
  },

  async getPreferences() {
    return api.get<NotificationPreference[]>('/notifications/preferences');
  },

  async updatePreference(id: string, data: Partial<NotificationPreference>) {
    return api.patch<NotificationPreference>(`/notifications/preferences/${id}`, data);
  },
};
```

### 13.2 Rules

- One service object per domain (notifications, calendar, admin, etc.)
- Pure functions — no React, no hooks, no state
- Returns the typed API response directly
- Lives in the feature folder: `{feature}/{feature}.service.ts`

---

## 14. Custom Hook Pattern (React Query)

### 14.1 Hook Example

```typescript
// web/src/features/notifications/useNotifications.ts
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { notificationsService } from './notifications.service';
import type { NotificationItem } from './types';

export function useNotifications(params: { category?: string; read?: boolean }) {
  return useInfiniteQuery({
    queryKey: ['notifications', params],
    queryFn: ({ pageParam }) =>
      notificationsService.list({ ...params, cursor: pageParam }),
    getNextPageParam: (last) => (last.meta.has_more ? last.meta.next_cursor : undefined),
    staleTime: 2 * 60 * 1000, // 2 minutes (matches backend cache)
  });
}

export function useMarkNotificationRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, read }: { id: string; read: boolean }) =>
      notificationsService.markRead(id, read),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}

export function useMarkAllRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => notificationsService.markAllRead(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  });
}
```

### 14.2 Rules

- One hook file per feature: `use{Feature}.ts`
- Use `useQuery` for reads, `useMutation` for writes
- Use `useInfiniteQuery` for cursor-paginated lists
- `queryKey` includes all filter parameters for automatic cache invalidation
- `staleTime` matches the backend cache TTL for that resource
- Mutations invalidate relevant queries via `queryClient.invalidateQueries()`
- Hook returns React Query result directly — page destructures `{ data, isLoading, error, fetchNextPage }`

---

## 15. Page Pattern

### 15.1 Page Example

```typescript
// web/src/features/notifications/NotificationsPage.tsx
import { useNotifications, useMarkNotificationRead, useMarkAllRead } from './useNotifications';

export default function NotificationsPage() {
  const [category, setCategory] = useState<string>();
  const [readFilter, setReadFilter] = useState<boolean>();

  const { data, isLoading, error, fetchNextPage, hasNextPage } = useNotifications({
    category,
    read: readFilter,
  });

  const markRead = useMarkNotificationRead();
  const markAll = useMarkAllRead();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorBanner error={error} />;

  const items = data?.pages.flatMap((p) => p.data) ?? [];

  return (
    <div>
      <FilterBar category={category} onCategoryChange={setCategory} />
      <button onClick={() => markAll.mutate()}>Mark all read</button>
      {items.map((n) => (
        <NotificationCard
          key={n.id}
          item={n}
          onMarkRead={() => markRead.mutate({ id: n.id, read: true })}
        />
      ))}
      {hasNextPage && <button onClick={() => fetchNextPage()}>Load more</button>}
    </div>
  );
}
```

### 15.2 Rules

- Page NEVER calls `api.get()` directly — always use the custom hook
- Page uses `useState` ONLY for UI state (filters, modals, form fields) — never for server data
- Server data comes from React Query via the custom hook
- Loading/error states use shared components (`LoadingState`, `ErrorBanner`)

---

## 16. React Query Setup

```typescript
// web/src/main.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,    // 5 min default
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

// Wrap <App /> with <QueryClientProvider client={queryClient}>
```

---

## 17. Web Migration Checklist (Per Feature)

When refactoring a page:

- [ ] Create `{feature}.service.ts` — extract all `api.*()` calls from page
- [ ] Create `use{Feature}.ts` — wrap service calls in React Query hooks
- [ ] Update page — replace `useState` + `useEffect` + `api.*()` with hook calls
- [ ] Remove loading/error `useState` — React Query manages these
- [ ] Remove `useCallback` fetch functions — React Query handles refetching
- [ ] Remove `useEffect` data fetching — React Query handles lifecycle
- [ ] Test: page still renders, filters work, pagination works, mutations update UI

---

# PART C — Infrastructure Security

## 18. Security Hardening Rules

### 18.1 Secrets Management

- `.env` file MUST be in `.gitignore` — NEVER committed to git
- Production secrets use Docker secrets (`/run/secrets/`) — NEVER env vars
- Generate unique secrets per environment: `openssl rand -hex 32`
- Rotate JWT secret quarterly

### 18.2 Redis Security

```conf
# infra/redis/redis.conf
requirepass ${REDIS_PASSWORD}
bind 127.0.0.1
protected-mode yes
```

### 18.3 PostgreSQL Security

- Remove hardcoded passwords from `infra/postgres/init.sql`
- Use environment variables for role passwords
- Different credentials per environment (dev/staging/prod)

### 18.4 Monitoring Security

- Change Grafana default password on first deployment
- Restrict Prometheus `/metrics` endpoint to internal network only
- Enable Alertmanager webhook receivers for production

### 18.5 Checklist

- [ ] `.env` removed from git history (`git filter-branch` or BFG)
- [ ] `.env` added to `.gitignore`
- [ ] `.env.example` has placeholder values only (no real secrets)
- [ ] Redis `protected-mode yes` and `requirepass` set
- [ ] PostgreSQL init.sql uses env vars for passwords
- [ ] Grafana admin password changed from default
- [ ] Alertmanager webhooks configured (Slack/PagerDuty)
- [ ] Staging uses different credentials than dev
- [ ] Production uses Docker secrets, not env vars
- [ ] JWT_SECRET_KEY is unique per environment

---

# PART D — Mobile (Flutter) — Reference Only

## 19. Current Mobile Architecture (Already Correct)

The mobile app follows Clean Architecture. No refactoring needed, just reference:

```
mobile/lib/
├── domain/              # Pure business logic (no framework deps)
│   ├── entities/        # Value objects (User, FeedItem, etc.)
│   └── repositories/    # Abstract interfaces
├── data/                # Implementation layer
│   ├── api/             # Dio HTTP client + WebSocket
│   ├── repositories_impl/  # Concrete repository implementations
│   ├── dto/             # JSON ↔ Entity mappers
│   └── local_store/     # SQLite cache + offline queue
├── features/            # Presentation layer (screens + providers)
│   ├── auth/
│   ├── feed/
│   └── ...
├── shared/              # Cross-cutting: secure storage, push, connectivity
└── app/                 # DI (providers.dart) + routing (router.dart)
```

This pattern is maintained. New mobile features follow the same structure.
