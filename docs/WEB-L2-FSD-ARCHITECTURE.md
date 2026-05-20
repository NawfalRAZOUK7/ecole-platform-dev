# Web Level 2 — Feature-Sliced Design (FSD) Architecture

Migrate from flat features to a full **Feature-Sliced Design** with strict layer boundaries: `shared` → `entities` → `features` → `widgets` → `pages`.

---

## What Changes from L1

L1 added internal folders (`api/`, `model/`, `ui/`) **inside** each feature. L2 reorients the **root structure** by splitting features into layers by business abstraction:

```
src/
├── app/                  # entry point, providers, router, global styles
│   ├── App.tsx
│   ├── providers/
│   ├── router/
│   └── layouts/
│
├── shared/
│   ├── api/              # (already exists) core API client
│   ├── ui/               # (already exists) generic components
│   ├── hooks/            # (already exists) generic hooks
│   ├── lib/              # utils, helpers
│   ├── types/            # global types
│   └── config/           # env, constants
│
├── entities/             # business domain models (NO user actions)
│   ├── user/
│   ├── school/
│   ├── course/
│   ├── invoice/
│   ├── attendance/
│   └── ...
│
├── features/               # user actions / use-cases (L1 structure preserved)
│   ├── auth/
│   ├── billing/
│   ├── lms/
│   └── ...
│
├── widgets/               # composed UI blocks used across pages
│   ├── dashboard-sidebar/
│   ├── top-navbar/
│   ├── analytics-overview/
│   ├── calendar-widget/
│   └── ...
│
└── pages/                 # route-level composition ONLY
    ├── auth/
    ├── dashboard/
    ├── admin/
    └── ...
```

---

## Dependency Rule (Strict)

A layer can only import from layers **below** it:

```
pages     → widgets, features, entities, shared, app
widgets   → features, entities, shared
features  → entities, shared
entities  → shared
shared    → (nothing or only shared/)
app       → (everything — bootstrap layer)
```

**Never:**
- entities → features
- features → widgets
- widgets → pages
- pages → pages

---

## What Goes Where (Concrete Examples)

### `entities/` — Pure Business Data

Contains types, API models, mappers, and **display-only** components (no actions).

```
entities/user/
├── api/
│   └── user.api.ts          # GET /users/:id, list, etc. (read-only)
├── model/
│   ├── types.ts             # User, UserProfile, Membership types
│   └── mapper.ts            # snake_case → camelCase
├── ui/
│   ├── UserAvatar.tsx       # display-only avatar
│   ├── UserCard.tsx         # display-only card
│   └── UserBadge.tsx        # role badge display
└── index.ts                 # exports types + UI components only
```

**Rule:** No mutations, no forms, no dialogs. If it requires user interaction, it belongs in `features/`.

### `features/` — User Actions (L1 Structure)

Kept from L1. Focuses on user interactions: login, create invoice, submit quiz, etc.

```
features/billing/
├── create-invoice/
│   ├── api/
│   │   └── create-invoice.api.ts
│   ├── model/
│   │   ├── useCreateInvoice.ts
│   │   └── invoice.schema.ts   # zod / yup validation
│   ├── ui/
│   │   ├── CreateInvoiceForm.tsx
│   │   └── CreateInvoiceButton.tsx
│   └── index.ts
│
├── pay-invoice/
├── generate-reports/
└── ...
```

**Key change from L1:** Features become **granular user actions** rather than "billing everything." Instead of one giant `billing/` with all pages, split into `create-invoice/`, `pay-invoice/`, `list-invoices/`, etc.

### `widgets/` — Composed UI Sections

Reusable compositions of features + entities. Used by multiple pages.

```
widgets/dashboard-sidebar/
├── ui/
│   ├── DashboardSidebar.tsx     # uses entities/user/ui + features/auth/model
│   └── SidebarNavItem.tsx
└── index.ts

widgets/top-navbar/
├── ui/
│   ├── TopNavbar.tsx            # uses entities/user + features/notifications
│   └── NotificationBell.tsx
└── index.ts

widgets/analytics-overview/
├── ui/
│   ├── AnalyticsOverview.tsx    # uses entities/school + features/reports
│   └── StatCardGrid.tsx
└── index.ts
```

**Rule:** A widget never defines its own data model. It consumes from features/entities.

### `pages/` — Route-Level Assembly ONLY

Thin glue layer. Imports widgets, features, and entities to assemble a route.

```
pages/dashboard/
├── ui/
│   └── DashboardPage.tsx        # assembles widgets + features, no logic
└── index.ts

pages/admin/
├── ui/
│   └── AdminPage.tsx
└── index.ts
```

**Rule:** Pages never contain business logic, API calls, or local state beyond layout toggles. All data comes from widgets/features.

---

## Migration Map: L1 → L2

### Step 1: Create `entities/`

Move pure business types + read APIs out of features:

| Current L1 location | L2 Target |
|--------------------|-----------|
| `features/auth/api/auth.types.ts` | `entities/user/api/types.ts` |
| `features/school/api/school.api.ts` (GET only) | `entities/school/api/school.api.ts` |
| `features/academic/attendance/api/attendance.api.ts` (GET only) | `entities/attendance/api/attendance.api.ts` |
| `features/content/catalog/api/content.api.ts` (GET only) | `entities/content/api/content.api.ts` |
| `features/billing/invoices/api/invoices.api.ts` (GET list, GET detail) | `entities/invoice/api/invoice.api.ts` |

### Step 2: Split features into user actions

Instead of monolithic `features/billing/`, create action-level features:

```
features/
├── create-invoice/           (was billing/ui/CreateInvoicePage + billing/api create)
├── pay-invoice/              (was billing/ui/Payment related)
├── manage-fee-structures/    (was billing/ui/FeeStructuresPage)
├── create-budget/            (was billing/budgets/ create flow)
├── approve-budget/           (was billing/budgets/ approval flow)
└── ...
```

Same for academic:
```
features/
├── mark-attendance/          (was academic/attendance/ mark flow)
├── view-attendance-history/ (was academic/attendance/ history page)
├── create-program/           (was academic/programs/ create)
├── enroll-student/           (was academic/programs/ enrollment)
└── ...
```

### Step 3: Extract widgets from features

Identify UI compositions used by 2+ pages and move to `widgets/`:

| Component | Used by | Target |
|-----------|---------|--------|
| DataTable | Many pages | Already in `shared/ui/` (keep) |
| StatCardGrid | Dashboard, Reports, Admin | `widgets/analytics-overview/` |
| NotificationBell | TopNavbar, Dashboard | `widgets/top-navbar/` |
| Sidebar | All admin pages | `widgets/dashboard-sidebar/` |
| CalendarMini | Dashboard, CalendarPage | `widgets/calendar-widget/` |
| UserMenu | TopNavbar | `widgets/top-navbar/ui/UserMenu.tsx` |

### Step 4: Move pages from features → pages/

```
features/auth/ui/LoginPage.tsx     → pages/auth/ui/LoginPage.tsx
features/admin/ui/DashboardPage.tsx → pages/admin/ui/AdminDashboardPage.tsx
features/billing/ui/FeeStructuresPage.tsx → pages/billing/ui/FeeStructuresPage.tsx
features/academic/attendance/ui/AttendancePage.tsx → pages/attendance/ui/AttendancePage.tsx
```

Each page becomes a thin composition:

```tsx
// pages/auth/ui/LoginPage.tsx
import { LoginForm } from '@/features/auth/login';
export function LoginPage() {
  return <LoginForm />;
}
```

---

## Phases

### Phase 1 — Create `entities/` layer
1. Create `entities/user/`, `entities/school/`, `entities/course/`, etc.
2. Move pure types + read APIs from features to entities
3. Update all feature imports to pull from entities instead
4. Verify: `grep "from '@/features" entities/` should return nothing

### Phase 2 — Split monolithic features into user actions
1. Audit each feature for distinct user actions
2. Create action-level folders (e.g. `features/create-invoice/`)
3. Move relevant api/model/ui into each action folder
4. Add `index.ts` barrel for each action

### Phase 3 — Extract `widgets/` layer
1. Identify repeated compositions across pages
2. Create `widgets/` folders
3. Move composed components from features/pages to widgets
4. Update page imports

### Phase 4 — Create `pages/` layer
1. Move all `*Page.tsx` from `features/*/ui/` to `pages/*/ui/`
2. Replace pages with thin composition imports
3. Update router (App.tsx) to import from `pages/`

### Phase 5 — Enforce dependency rules
1. Add ESLint rule: `no-restricted-imports` per folder
2. Block entities from importing features
3. Block features from importing widgets/pages
4. Block pages from importing pages

---

## Concrete: Auth Before & After

### Before (L1)
```
features/auth/
├── api/auth.api.ts
├── model/useAuth.ts
├── ui/LoginPage.tsx
├── ui/RegisterPage.tsx
└── index.ts
```

### After (L2)
```
entities/user/
├── api/user.api.ts          # GET /users/me, list users
├── model/types.ts           # User, UserProfile
├── ui/UserAvatar.tsx        # display only
└── index.ts

features/
├── auth/login/
│   ├── api/login.api.ts     # POST /auth/login
│   ├── model/useLogin.ts
│   ├── ui/LoginForm.tsx     # NOT the page
│   └── index.ts
│
├── auth/register/
│   ├── api/register.api.ts
│   ├── model/useRegister.ts
│   ├── ui/RegisterForm.tsx
│   └── index.ts
│
├── auth/session/
│   ├── model/useSession.ts  # (was useAuth — manages token)
│   └── index.ts
│
└── auth/logout/
    ├── api/logout.api.ts
    ├── model/useLogout.ts
    └── ui/LogoutButton.tsx

widgets/
└── top-navbar/
    └── ui/
        └── UserMenu.tsx     # uses entities/user + features/auth/session

pages/
├── auth/
│   └── ui/
│       ├── LoginPage.tsx    # assembles features/auth/login/ui/LoginForm
│       └── RegisterPage.tsx # assembles features/auth/register/ui/RegisterForm
└── ...
```

---

## When to Start L2

**Prerequisites (L1 must be complete):**
1. All features have `api/`, `model/`, `ui/`, `lib/`, `index.ts`
2. No flat files remain at feature root
3. AuthContext/ProtectedRoute live in `app/`
4. Cross-feature imports go through barrels, not deep paths
5. Build passes, tests pass

**Start L2 when:**
- You have 2+ developers working on frontend
- Features like billing/academic are growing beyond ~15 files
- You need to reuse the same data model across 3+ features
- You're planning to add microfrontends or split the SPA

---

## Effort Estimate

| Phase | Files touched | Complexity |
|-------|--------------|------------|
| 1. entities/ | 80+ | Medium |
| 2. split features | 120+ | High |
| 3. widgets/ | 30+ | Medium |
| 4. pages/ | 60+ | Low |
| 5. ESLint rules | 1 config | Low |
| **Total** | **~300** | **High** |

**This is larger than L1.** Consider doing it in 2–3 sprints, not one session.
