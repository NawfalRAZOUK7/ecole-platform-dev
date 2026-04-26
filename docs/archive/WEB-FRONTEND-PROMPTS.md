# Ecole Platform — Web Frontend Detailed Prompts

> Generated: 2026-04-06
> Usage: Copy-paste any prompt into Codex, Claude Code, or any AI coding tool.
> Each prompt is self-contained and produces deterministic output.
> Prompts follow: CONTEXT → TASK → CONSTRAINTS → OUTPUT → VERIFY → GIT

---

## Prompt Naming Convention

```
WEB-P{phase}-{number}  (e.g., WEB-P0-1 = Phase 0, Task 1)
```

---

## PHASE 0 — Infrastructure & Shared Foundation

---

### WEB-P0-1 — Install Form Library & Create Form Components

```
CONTEXT
-------
Project: ecole-platform-dev/web (React 18 + Vite 6 + TypeScript 5.6 strict)
State management: TanStack React Query v5.95.2
CSS: Custom CSS with CSS variables (no Tailwind, no Material UI)
i18n: i18next with react-i18next (FR default, AR RTL, EN)
Current forms: All use raw useState — no validation library exists
Package manager: npm

TASK
----
1. Install react-hook-form, @hookform/resolvers, and zod:
   cd web && npm install react-hook-form @hookform/resolvers zod

2. Create web/src/shared/validation/schemas.ts with these zod schemas:
   - emailSchema: z.string().email()
   - phoneSchema: z.string().regex(/^\+?[0-9]{8,15}$/)
   - gradeSchema: z.number().min(0).max(20) (Moroccan 0-20 scale)
   - currencySchema: z.number().min(0) (MAD currency, 2 decimal places)
   - dateSchema: z.string().datetime() (ISO format, Africa/Casablanca)
   - requiredString: z.string().min(1, "required")
   - paginationSchema: z.object({ page: z.number().min(1), pageSize: z.number().min(1).max(100) })

3. Create these files in web/src/shared/ui/:

   FormField.tsx:
   - Props: name, label (i18n key), type, placeholder, disabled, className
   - Uses useFormContext() from react-hook-form (no prop drilling)
   - Renders: <label> + <input> + error message from formState.errors
   - Error messages passed through t() for i18n
   - Supports RTL via dir="auto" on input
   - CSS classes: .form-field, .form-field__label, .form-field__input, .form-field__error

   FormSelect.tsx:
   - Props: name, label, options: {value: string, label: string}[], placeholder
   - Same pattern as FormField but renders <select>
   - CSS classes: .form-select, .form-select__label, .form-select__input, .form-select__error

   FormTextarea.tsx:
   - Props: name, label, rows (default 4), maxLength
   - Same pattern, renders <textarea>

   FormCheckbox.tsx:
   - Props: name, label, description (optional helper text)
   - Renders checkbox with label to the right (or left for RTL)

   FormDatePicker.tsx:
   - Props: name, label, minDate, maxDate
   - Renders native <input type="date">
   - Default timezone: Africa/Casablanca

4. Add CSS for all form components to web/src/app/styles.css:
   - .form-field, .form-select, .form-textarea, .form-checkbox, .form-date
   - Error state: red border, red error text below input
   - Disabled state: opacity 0.6, cursor not-allowed
   - Use existing CSS variables: var(--color-primary), var(--color-error), var(--color-border)

CONSTRAINTS
-----------
- Do NOT install any CSS framework (no Tailwind, no styled-components)
- All components must be fully typed with TypeScript generics
- All labels must use i18n: const { t } = useTranslation()
- All components must support RTL (use CSS logical properties: margin-inline-start, padding-inline-end, etc.)
- Do NOT modify any existing feature page yet (that comes in later prompts)
- Export all new components from web/src/shared/ui/index.ts (create barrel file if it doesn't exist)

OUTPUT
------
New files:
  web/src/shared/validation/schemas.ts
  web/src/shared/ui/FormField.tsx
  web/src/shared/ui/FormSelect.tsx
  web/src/shared/ui/FormTextarea.tsx
  web/src/shared/ui/FormCheckbox.tsx
  web/src/shared/ui/FormDatePicker.tsx
  web/src/shared/ui/index.ts (barrel)
Modified files:
  web/package.json (new deps)
  web/src/app/styles.css (new form CSS)

VERIFY
------
cd web
npx tsc --noEmit                    # Zero errors
npm run lint                         # Zero warnings
npm run build                        # Clean production build
grep -r "react-hook-form" src/shared/ui/ | wc -l   # Should be >= 5
grep -r "useFormContext" src/shared/ui/ | wc -l     # Should be >= 5
grep -r "zod" src/shared/validation/ | wc -l        # Should be >= 7

GIT (Codex only — skip if using Claude Code)
---
git add web/package.json web/package-lock.json web/src/shared/validation/ web/src/shared/ui/FormField.tsx web/src/shared/ui/FormSelect.tsx web/src/shared/ui/FormTextarea.tsx web/src/shared/ui/FormCheckbox.tsx web/src/shared/ui/FormDatePicker.tsx web/src/shared/ui/index.ts web/src/app/styles.css
git commit -m "feat(web): add react-hook-form + zod form components with i18n & RTL support"
```

---

### WEB-P0-2 — Create Shared Component Library

```
CONTEXT
-------
Project: ecole-platform-dev/web (React 18 + TypeScript 5.6 strict)
Existing shared UI: EmptyState.tsx, ErrorBanner.tsx, FileUpload.tsx, LanguageSwitcher.tsx, Layout.tsx, LoadingState.tsx
CSS: Custom CSS with variables (no Tailwind)
i18n: i18next (FR, AR, EN)
The project has NO: DataTable, Pagination, ConfirmDialog, Skeleton, Badge, Tabs, Breadcrumb, SearchInput, StatCard

TASK
----
Create these components in web/src/shared/ui/:

1. DataTable.tsx (~150 lines):
   - Generic: DataTable<T>
   - Props: columns: ColumnDef<T>[], data: T[], loading: boolean, emptyMessage: string, onRowClick?: (row: T) => void, sortable?: boolean
   - ColumnDef<T>: { key: keyof T, header: string (i18n key), render?: (value: T[keyof T], row: T) => ReactNode, sortable?: boolean, width?: string }
   - Built-in: sort by column click (asc/desc/none), loading skeleton rows, empty state via <EmptyState>
   - Renders <table> with <thead>/<tbody>, uses CSS classes .data-table, .data-table__header, .data-table__row, .data-table__cell
   - Row hover highlight, pointer cursor if onRowClick provided
   - Responsive: horizontal scroll on mobile (<768px)

2. Pagination.tsx (~60 lines):
   - Props: currentPage: number, totalPages: number, pageSize: number, pageSizeOptions?: number[], onPageChange: (page: number) => void, onPageSizeChange?: (size: number) => void
   - Renders: Previous/Next buttons, page numbers (show max 5 with ellipsis), page size selector dropdown
   - Disabled state for first/last page buttons
   - CSS: .pagination, .pagination__btn, .pagination__btn--active, .pagination__size-select

3. ConfirmDialog.tsx (~80 lines):
   - Props: open: boolean, title: string, message: string, confirmLabel?: string, cancelLabel?: string, variant?: "danger" | "warning" | "info", onConfirm: () => void, onCancel: () => void, loading?: boolean
   - Modal overlay with focus trap (first/last focusable element loop)
   - Close on Escape key, close on overlay click
   - Danger variant: red confirm button
   - CSS: .confirm-dialog, .confirm-dialog__overlay, .confirm-dialog__content, .confirm-dialog__actions

4. Skeleton.tsx (~40 lines):
   - Props: variant: "line" | "card" | "table-row" | "circle", width?: string, height?: string, count?: number
   - Renders animated pulse placeholder (CSS animation)
   - count > 1 renders multiple skeletons stacked
   - CSS: .skeleton, .skeleton--line, .skeleton--card, .skeleton--table-row, .skeleton--circle, @keyframes skeleton-pulse

5. Badge.tsx (~25 lines):
   - Props: variant: "success" | "warning" | "error" | "info" | "neutral", children: ReactNode, size?: "sm" | "md"
   - Small colored pill/tag component
   - CSS: .badge, .badge--success (green), .badge--warning (orange), .badge--error (red), .badge--info (blue), .badge--neutral (gray)

6. Tabs.tsx (~70 lines):
   - Props: tabs: {id: string, label: string (i18n key), content: ReactNode}[], defaultTab?: string, onChange?: (tabId: string) => void
   - Keyboard accessible: Arrow Left/Right to move, Enter/Space to activate
   - ARIA: role="tablist", role="tab", role="tabpanel", aria-selected, aria-controls
   - CSS: .tabs, .tabs__list, .tabs__tab, .tabs__tab--active, .tabs__panel

7. Breadcrumb.tsx (~30 lines):
   - Props: items: {label: string, href?: string}[]
   - Last item rendered as plain text (current page), others as <Link>
   - Separator: / (or ← for RTL)
   - ARIA: nav aria-label="breadcrumb", aria-current="page" on last item
   - CSS: .breadcrumb, .breadcrumb__item, .breadcrumb__separator

8. SearchInput.tsx (~45 lines):
   - Props: value: string, onChange: (value: string) => void, placeholder: string (i18n key), debounceMs?: number (default 300)
   - Debounced: only calls onChange after debounceMs of inactivity
   - Clear button (X) when value is non-empty
   - CSS: .search-input, .search-input__field, .search-input__clear

9. StatCard.tsx (~35 lines):
   - Props: label: string (i18n key), value: string | number, trend?: { direction: "up" | "down" | "flat", percentage: number }, icon?: ReactNode
   - Dashboard metric card with large value, small label, optional trend indicator
   - CSS: .stat-card, .stat-card__value, .stat-card__label, .stat-card__trend, .stat-card__trend--up (green), .stat-card__trend--down (red)

10. Update web/src/shared/ui/index.ts barrel file to export all new components AND all existing ones.

11. Add ALL CSS for the above to web/src/app/styles.css at the end of the file.

CONSTRAINTS
-----------
- All components must be fully typed with TypeScript (no `any`)
- All text labels must use i18n: useTranslation()
- All interactive components must have ARIA attributes
- All components must support RTL (CSS logical properties)
- CSS must use existing CSS variables where applicable
- Do NOT import any external UI library

OUTPUT
------
New files:
  web/src/shared/ui/DataTable.tsx
  web/src/shared/ui/Pagination.tsx
  web/src/shared/ui/ConfirmDialog.tsx
  web/src/shared/ui/Skeleton.tsx
  web/src/shared/ui/Badge.tsx
  web/src/shared/ui/Tabs.tsx
  web/src/shared/ui/Breadcrumb.tsx
  web/src/shared/ui/SearchInput.tsx
  web/src/shared/ui/StatCard.tsx
Modified files:
  web/src/shared/ui/index.ts
  web/src/app/styles.css

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
ls src/shared/ui/*.tsx | wc -l     # Should be >= 15 (6 existing + 9 new)
grep "export" src/shared/ui/index.ts | wc -l  # Should be >= 15

GIT (Codex only)
---
git add web/src/shared/ui/ web/src/app/styles.css
git commit -m "feat(web): add shared component library — DataTable, Pagination, ConfirmDialog, Skeleton, Badge, Tabs, Breadcrumb, SearchInput, StatCard"
```

---

### WEB-P0-3 — Error Boundaries & Network Status

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current error handling: ErrorBanner.tsx (95 lines) + errorUtils.ts — both are inline error display
No React Error Boundary exists anywhere in the codebase
App.tsx (495 lines) has 50+ routes, none wrapped in error boundaries
QueryClient is configured in App.tsx with default options

TASK
----
1. Create web/src/shared/ui/ErrorBoundary.tsx:
   - Class component (Error Boundaries require class components in React 18)
   - Props: fallback?: ReactNode, onError?: (error: Error, errorInfo: ErrorInfo) => void, children: ReactNode
   - State: { hasError: boolean, error: Error | null }
   - Renders fallback UI with: error message, "Try Again" button that resets state, link to home page
   - Default fallback: card with error icon, translated message, retry button
   - CSS: .error-boundary, .error-boundary__card, .error-boundary__actions

2. Create web/src/shared/ui/OfflineIndicator.tsx:
   - Uses useNetworkStatus hook (created below)
   - Renders fixed top banner when offline: "You are offline. Some features may not work."
   - Auto-hides when back online with 2s delay
   - CSS: .offline-indicator (position fixed, top 0, z-index 9999, yellow/amber background)

3. Create web/src/shared/hooks/useNetworkStatus.ts:
   - Returns { isOnline: boolean, wasOffline: boolean }
   - Listens to window 'online'/'offline' events
   - wasOffline stays true for 3 seconds after reconnect (to show "back online" message)

4. Create web/src/shared/ui/RetryButton.tsx:
   - Props: onRetry: () => void, loading?: boolean
   - Simple button with retry icon and "Retry" label
   - Shows spinner when loading

5. Modify web/src/app/App.tsx:
   - Import ErrorBoundary
   - Wrap the main <Routes> block with <ErrorBoundary>
   - Add <OfflineIndicator /> inside the app root, above the router
   - Add <Suspense fallback={<LoadingState />}> around the Routes if not already present
   - Add a global QueryClient defaultOptions.queries.retry = 2, defaultOptions.mutations.retry = 0
   - Add QueryClient onError default handler that logs to console.error

CONSTRAINTS
-----------
- ErrorBoundary must be a class component (React 18 requirement)
- Do NOT modify the route structure in App.tsx (only add wrappers)
- OfflineIndicator must work across all pages (placed at app root level)
- All text must use i18n

OUTPUT
------
New files:
  web/src/shared/ui/ErrorBoundary.tsx
  web/src/shared/ui/OfflineIndicator.tsx
  web/src/shared/ui/RetryButton.tsx
  web/src/shared/hooks/useNetworkStatus.ts
Modified files:
  web/src/app/App.tsx
  web/src/shared/ui/index.ts (add exports)
  web/src/app/styles.css (add CSS)

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
grep "ErrorBoundary" src/app/App.tsx | wc -l   # Should be >= 1
grep "OfflineIndicator" src/app/App.tsx | wc -l # Should be >= 1
grep "class ErrorBoundary" src/shared/ui/ErrorBoundary.tsx | wc -l # Should be 1

GIT (Codex only)
---
git add web/src/shared/ui/ErrorBoundary.tsx web/src/shared/ui/OfflineIndicator.tsx web/src/shared/ui/RetryButton.tsx web/src/shared/hooks/useNetworkStatus.ts web/src/app/App.tsx web/src/shared/ui/index.ts web/src/app/styles.css
git commit -m "feat(web): add React Error Boundary, OfflineIndicator, and global error handling"
```

---

### WEB-P0-4 — Accessibility Foundation

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current accessibility: Only 3 files have ARIA attributes (DocumentsPage, Layout, ErrorBanner)
Layout.tsx (300+ lines) has sidebar navigation with no keyboard support
No skip-to-content link exists
No focus management on route changes

TASK
----
1. Update ALL components in web/src/shared/ui/ to include proper ARIA:
   - DataTable: role="table", role="rowgroup", role="row", role="columnheader", role="cell", aria-sort on sortable columns
   - ErrorBanner: role="alert", aria-live="assertive"
   - LoadingState: role="status", aria-live="polite", aria-label="Loading"
   - FileUpload: aria-label on drop zone, aria-describedby for instructions
   - EmptyState: role="status"

2. Update web/src/shared/ui/Layout.tsx:
   - Add <a href="#main-content" className="skip-link">Skip to content</a> as first child
   - Add id="main-content" to the main content area
   - Add role="navigation" and aria-label="Main navigation" to sidebar <nav>
   - Add aria-current="page" to the active sidebar link
   - Add keyboard navigation to sidebar: Arrow Up/Down to move between links, Enter to navigate
   - Add aria-expanded to collapsible sidebar sections (if any)

3. Add to web/src/app/styles.css:
   .skip-link {
     position: absolute;
     top: -100%;
     left: 0;
     z-index: 10000;
     padding: 0.5rem 1rem;
     background: var(--color-primary);
     color: white;
   }
   .skip-link:focus {
     top: 0;
   }

4. Create web/src/shared/hooks/useFocusManagement.ts:
   - Hook that focuses the <h1> or main content area on route change
   - Uses useLocation() from react-router-dom
   - Uses useEffect to set focus after navigation

5. Add useFocusManagement to Layout.tsx so focus moves to main content on every route change.

6. Add prefers-reduced-motion media query to all existing CSS animations in styles.css:
   @media (prefers-reduced-motion: reduce) {
     *, *::before, *::after {
       animation-duration: 0.01ms !important;
       transition-duration: 0.01ms !important;
     }
   }

CONSTRAINTS
-----------
- Do NOT change any visual appearance
- Do NOT add any new dependencies
- All ARIA attributes must follow WAI-ARIA 1.2 spec
- Test keyboard navigation manually: Tab through all interactive elements

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
grep -r "aria-" src/shared/ui/ | wc -l        # Should be >= 20
grep -r "role=" src/shared/ui/ | wc -l         # Should be >= 10
grep "skip-link" src/shared/ui/Layout.tsx | wc -l  # Should be >= 1

GIT (Codex only)
---
git add web/src/shared/ui/ web/src/shared/hooks/useFocusManagement.ts web/src/app/styles.css
git commit -m "feat(web): add accessibility foundation — ARIA labels, keyboard nav, skip-link, focus management"
```

---

### WEB-P0-5 — Dark Mode

```
CONTEXT
-------
Project: ecole-platform-dev/web
CSS: web/src/app/styles.css (2,426 lines)
Current CSS variables (defined in :root):
  --color-primary, --color-primary-light, --color-primary-dark
  --color-secondary, --color-accent
  --color-success, --color-warning, --color-error, --color-info
  --color-bg, --color-surface, --color-border
  --color-text, --color-text-secondary
No dark mode support exists

TASK
----
1. Create web/src/shared/hooks/useTheme.ts:
   - Returns { theme: "light" | "dark", toggleTheme: () => void, setTheme: (t: "light" | "dark") => void }
   - On mount: check localStorage key "ecole-theme", fallback to window.matchMedia("(prefers-color-scheme: dark)")
   - On change: update document.documentElement.setAttribute("data-theme", theme) and localStorage
   - Listen for system preference changes via matchMedia.addEventListener

2. Add dark mode variables to web/src/app/styles.css AFTER the existing :root block:
   [data-theme="dark"] {
     --color-primary: #6B8AFF;
     --color-primary-light: #8BA4FF;
     --color-primary-dark: #4A6AE5;
     --color-secondary: #A78BFA;
     --color-accent: #F59E0B;
     --color-success: #34D399;
     --color-warning: #FBBF24;
     --color-error: #F87171;
     --color-info: #60A5FA;
     --color-bg: #0F172A;
     --color-surface: #1E293B;
     --color-border: #334155;
     --color-text: #F1F5F9;
     --color-text-secondary: #94A3B8;
   }

3. Audit web/src/app/styles.css for ALL hardcoded color values (hex codes like #fff, #000, #333, rgb(), hsl()) and replace with CSS variable references. Common patterns to fix:
   - background: #fff → background: var(--color-bg)
   - color: #333 → color: var(--color-text)
   - border: 1px solid #ddd → border: 1px solid var(--color-border)
   - background: #f5f5f5 → background: var(--color-surface)

4. Add theme toggle button to web/src/shared/ui/Layout.tsx header area:
   - Moon icon (dark) / Sun icon (light) — use simple SVG inline icons
   - aria-label="Toggle dark mode"
   - Position: in the header bar, near the language switcher

5. CSS for toggle button:
   .theme-toggle { background: none; border: none; cursor: pointer; padding: 0.5rem; border-radius: 50%; }
   .theme-toggle:hover { background: var(--color-surface); }
   .theme-toggle svg { width: 20px; height: 20px; fill: var(--color-text); }

CONSTRAINTS
-----------
- Do NOT add any npm dependencies
- Do NOT change the light mode appearance (it must look identical to before)
- All new dark values must maintain WCAG AA contrast ratio (4.5:1 for text)
- RTL + dark mode must work together (test mentally)
- Recharts components will inherit colors — ensure chart colors are visible in dark mode

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
grep "data-theme" src/app/styles.css | wc -l         # Should be >= 1
grep "useTheme" src/shared/hooks/useTheme.ts | wc -l  # Should be >= 1
grep "theme-toggle" src/shared/ui/Layout.tsx | wc -l   # Should be >= 1
# Manual: Open in browser, toggle dark mode, verify all pages render correctly

GIT (Codex only)
---
git add web/src/shared/hooks/useTheme.ts web/src/app/styles.css web/src/shared/ui/Layout.tsx
git commit -m "feat(web): add dark mode with system preference detection and manual toggle"
```

---

### WEB-P0-6 — TypeScript Types & Route Constants

```
CONTEXT
-------
Project: ecole-platform-dev/web (TypeScript 5.6 strict mode)
Current types: Only 3 type files exist (calendar/types.ts, feed/types.ts, notifications/types.ts)
Routes: Hardcoded strings throughout App.tsx (495 lines) and all feature services
API responses: No shared response type — each service defines its own

TASK
----
1. Create web/src/shared/types/api.ts:
   interface PaginatedResponse<T> { items: T[]; total: number; page: number; page_size: number; pages: number; }
   interface ApiError { detail: string; code?: string; field_errors?: Record<string, string[]>; }
   interface ApiSuccess<T> { data: T; message?: string; }
   type ApiResponse<T> = { data: T; error: null } | { data: null; error: ApiError }

2. Create web/src/shared/types/models.ts with core domain types matching backend Pydantic schemas:
   - User: { id: string; email: string; first_name: string; last_name: string; role: UserRole; is_active: boolean; }
   - UserRole: "SYS" | "SUP" | "ADM" | "DIR" | "TCH" | "EDUCATOR" | "PAR" | "STD" | "CONTENT_MGR" | "PUBLIC"
   - School: { id: string; name: string; code: string; address: string; city: string; is_active: boolean; }
   - Class: { id: string; name: string; level: string; school_id: string; academic_year: string; }
   - Student: { id: string; user_id: string; class_id: string; enrollment_date: string; }
   - Grade: { id: string; student_id: string; assessment_id: string; value: number; /* 0-20 */ comment?: string; }
   - Invoice: { id: string; school_id: string; student_id: string; amount: number; currency: "MAD"; status: "draft" | "sent" | "paid" | "overdue"; }

3. Create web/src/shared/types/forms.ts:
   - FormMode: "create" | "edit" | "view"
   - FormState<T>: { values: T; isDirty: boolean; isSubmitting: boolean; errors: Partial<Record<keyof T, string>>; }

4. Create web/src/app/routes.ts — all route path constants:
   export const ROUTES = {
     HOME: "/",
     LOGIN: "/login",
     REGISTER: "/register",
     VERIFY_2FA: "/verify-2fa",
     DASHBOARD: "/dashboard",
     ATTENDANCE: "/attendance",
     ATTENDANCE_HISTORY: "/attendance/history",
     GRADEBOOK: "/gradebook",
     INVOICES: "/invoices",
     INVOICE_DETAIL: "/invoices/:id",
     BUDGETS: "/budgets",
     BUDGET_DETAIL: "/budgets/:id",
     MICRO_SCHOOLS: "/micro-schools",
     MICRO_SCHOOL_DETAIL: "/micro-schools/:id",
     SKILLS: "/skills",
     SKILL_PASSPORT: "/skills/passport/:studentId",
     COMPLIANCE: "/compliance",
     SYNC: "/sync",
     FINANCIAL_HEALTH: "/financial-health",
     // ... all existing routes from App.tsx
   } as const;

5. Create barrel: web/src/shared/types/index.ts exporting all types.

CONSTRAINTS
-----------
- All types must match the backend Pydantic schemas exactly (check backend/app/schemas/ if unsure)
- UserRole must match the 10 roles defined in backend
- Do NOT refactor App.tsx to use ROUTES yet (that happens in feature prompts)
- Use TypeScript `as const` for route constants

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
wc -l src/shared/types/*.ts     # Should total >= 100 lines
wc -l src/app/routes.ts          # Should be >= 40 lines

GIT (Codex only)
---
git add web/src/shared/types/ web/src/app/routes.ts
git commit -m "feat(web): add shared TypeScript types for API, models, forms, and route constants"
```

---

## PHASE 1 — Complete Partial Features + First Innovation Features

---

### WEB-P1-1 — Attendance Module (Full Build)

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current state: web/src/features/attendance/ has 3 files totaling 22 lines:
  - attendance.service.ts (12 lines) — only has getAttendance()
  - useAttendance.ts (10 lines) — only useAttendance query
  - ParentJustificationPage.tsx (133 lines) — parent view only
Backend endpoints (3 in attendance.py + 5 in attendance_analytics.py):
  GET  /attendance/class/{class_id}        — get class attendance for a date
  POST /attendance/class/{class_id}        — mark attendance (bulk)
  POST /attendance/{record_id}/justify     — submit justification
  GET  /analytics/attendance/trends        — attendance trends
  GET  /analytics/attendance/alerts        — absenteeism alerts
  GET  /analytics/attendance/student/{id}  — student attendance history
  GET  /analytics/attendance/class/{id}    — class attendance stats
  GET  /analytics/attendance/export        — export attendance data
Shared components available: DataTable, Pagination, Badge, Skeleton, FormField, FormSelect, FormDatePicker, StatCard, Tabs, SearchInput
CSS: custom CSS variables, no framework
i18n: FR (default), AR (RTL), EN — use t() from useTranslation()

TASK
----
1. Create web/src/features/attendance/attendance.types.ts:
   - AttendanceStatus: "present" | "absent" | "late" | "excused"
   - AttendanceRecord: { id: string; student_id: string; student_name: string; class_id: string; date: string; status: AttendanceStatus; justified: boolean; justification?: string; marked_by: string; }
   - BulkAttendancePayload: { class_id: string; date: string; records: { student_id: string; status: AttendanceStatus; note?: string; }[] }
   - AttendanceTrend: { date: string; present: number; absent: number; late: number; total: number; }
   - AttendanceAlert: { student_id: string; student_name: string; absent_count: number; consecutive_absences: number; alert_level: "warning" | "critical"; }

2. Rewrite web/src/features/attendance/attendance.service.ts:
   - getClassAttendance(classId: string, date: string): GET /attendance/class/{classId}?date={date}
   - markAttendance(payload: BulkAttendancePayload): POST /attendance/class/{classId}
   - submitJustification(recordId: string, justification: string, file?: File): POST /attendance/{recordId}/justify
   - getAttendanceTrends(classId: string, from: string, to: string): GET /analytics/attendance/trends
   - getAttendanceAlerts(schoolId: string): GET /analytics/attendance/alerts
   - getStudentHistory(studentId: string): GET /analytics/attendance/student/{studentId}
   - getClassStats(classId: string): GET /analytics/attendance/class/{classId}
   - exportAttendance(classId: string, format: "csv" | "pdf"): GET /analytics/attendance/export
   Use the api client from web/src/services/api/client.ts (import { api } from "@/services/api/client")

3. Rewrite web/src/features/attendance/useAttendance.ts:
   - useClassAttendance(classId, date) — useQuery
   - useMarkAttendance() — useMutation with optimistic update
   - useSubmitJustification() — useMutation
   - useAttendanceTrends(classId, dateRange) — useQuery
   - useAttendanceAlerts(schoolId) — useQuery
   - useStudentHistory(studentId) — useQuery

4. Create web/src/features/attendance/AttendancePage.tsx (~250 lines):
   Teacher/Director view for marking daily attendance:
   - Top bar: class selector dropdown + date picker (default: today)
   - DataTable showing all students in class: Name, Status (toggle buttons: Present/Absent/Late), Note (optional text input)
   - "Mark All Present" button above table
   - Submit button at bottom (calls useMarkAttendance mutation)
   - Loading: show Skeleton while fetching
   - Success: show toast/banner "Attendance saved"
   - Guards: TCH, DIR, ADM roles only

5. Create web/src/features/attendance/AttendanceHistoryPage.tsx (~180 lines):
   Student/Parent view:
   - Calendar heatmap (30-day grid, color-coded: green=present, red=absent, yellow=late, gray=excused)
   - Stats summary: total days, present %, absent count, late count
   - Use StatCard components for summary stats
   - Filterable by date range

6. Create web/src/features/attendance/AttendanceAnalyticsPage.tsx (~200 lines):
   Director/Admin view:
   - Tabs: "Trends" | "Alerts"
   - Trends tab: Recharts LineChart showing attendance rate over time (use useAttendanceTrends)
   - Alerts tab: DataTable of students with high absenteeism (use useAttendanceAlerts) with Badge for alert level
   - Export button (CSV/PDF)

7. Add routes to web/src/app/App.tsx:
   - /attendance → AttendancePage (TCH, DIR, ADM guard)
   - /attendance/history → AttendanceHistoryPage (STD, PAR guard)
   - /attendance/analytics → AttendanceAnalyticsPage (DIR, ADM guard)
   Keep the existing /attendance/justify route for ParentJustificationPage.

8. Add i18n keys to web/src/shared/i18n/locales/en.json, fr.json, ar.json under "attendance" namespace:
   attendance.title, attendance.markAll, attendance.submit, attendance.present, attendance.absent, attendance.late, attendance.excused, attendance.history, attendance.analytics, attendance.trends, attendance.alerts, attendance.export, attendance.saved, attendance.noRecords

CONSTRAINTS
-----------
- Use ONLY existing shared components (DataTable, Pagination, Badge, StatCard, Tabs, Skeleton, FormDatePicker, FormSelect)
- Use react-hook-form for any form inputs (justification form)
- Use Recharts for charts (already in package.json)
- All API calls through api client (web/src/services/api/client.ts)
- All text through i18n t() function
- All CSS in styles.css using CSS variables (no inline styles except for dynamic values like heatmap colors)
- Moroccan context: date format DD/MM/YYYY, timezone Africa/Casablanca

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
ls src/features/attendance/*.tsx | wc -l    # Should be >= 4
wc -l src/features/attendance/*.ts src/features/attendance/*.tsx | tail -1  # Should be >= 500 total

GIT (Codex only)
---
git add web/src/features/attendance/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build complete attendance module — marking, history, analytics with i18n & RTL"
```

---

### WEB-P1-2 — Gradebook Module (New Build)

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current state: No web/src/features/gradebook/ directory exists
Backend endpoints (5 in gradebook.py):
  GET    /gradebook/class/{class_id}                    — class gradebook grid
  GET    /gradebook/student/{student_id}                — student grade summary
  PUT    /gradebook/class/{class_id}/grades             — bulk grade update
  GET    /gradebook/class/{class_id}/weighted-summary   — weighted averages
  POST   /gradebook/class/{class_id}/export             — export grades
Additional related: rubrics.py (6 endpoints), assessments.py (4 endpoints)
Morocco: 0-20 grading scale, weighted averages

TASK
----
1. Create web/src/features/gradebook/ directory with:

   gradebook.types.ts:
   - GradebookEntry: { student_id: string; student_name: string; grades: Record<string, number | null>; weighted_average: number; }
   - GradebookColumn: { assessment_id: string; title: string; weight: number; max_score: 20; date: string; type: "exam" | "quiz" | "homework" | "project"; }
   - GradebookGrid: { class_id: string; class_name: string; columns: GradebookColumn[]; entries: GradebookEntry[]; }
   - BulkGradeUpdate: { class_id: string; grades: { student_id: string; assessment_id: string; value: number; }[] }

   gradebook.service.ts:
   - getClassGradebook(classId): GET /gradebook/class/{classId}
   - getStudentGrades(studentId): GET /gradebook/student/{studentId}
   - updateGrades(payload: BulkGradeUpdate): PUT /gradebook/class/{classId}/grades
   - getWeightedSummary(classId): GET /gradebook/class/{classId}/weighted-summary
   - exportGrades(classId, format): POST /gradebook/class/{classId}/export

   useGradebook.ts:
   - useClassGradebook(classId) — useQuery
   - useStudentGrades(studentId) — useQuery
   - useUpdateGrades() — useMutation
   - useWeightedSummary(classId) — useQuery

2. Create GradebookPage.tsx (~300 lines):
   Teacher view — spreadsheet-like grade entry:
   - Top: class selector dropdown, academic period selector
   - Grid: rows = students, columns = assessments (dynamic from API)
   - Each cell: editable number input (0-20 validation via zod, step 0.5)
   - Column headers show assessment title + weight percentage
   - Last column: weighted average (read-only, auto-calculated)
   - Color coding: >= 10 green, < 10 red (Moroccan pass/fail threshold)
   - Bottom toolbar: "Save All" button, "Export" dropdown (CSV/PDF)
   - Use react-hook-form with zod for the entire grid (useFieldArray or dynamic fields)
   - Guards: TCH, DIR roles

3. Create GradeDetailPage.tsx (~200 lines):
   Student/Parent view:
   - Student name + class at top
   - Recharts BarChart: grades by assessment (bars colored green/red based on 10 threshold)
   - Stats: overall average, highest grade, lowest grade, grade trend (improving/declining)
   - Table: all grades with assessment name, date, score, weight
   - Guards: STD, PAR roles

4. Wire routes in App.tsx:
   - /gradebook → GradebookPage (TCH, DIR)
   - /gradebook/student/:studentId → GradeDetailPage (STD, PAR, TCH, DIR)

5. Add i18n keys under "gradebook" namespace in all 3 locale files.

CONSTRAINTS
-----------
- Grade values MUST be validated 0-20 (Moroccan scale)
- Weighted average calculation: sum(grade * weight) / sum(weight)
- Use zod schema: z.number().min(0).max(20).step(0.5)
- Use existing shared components
- All API calls through api client

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
ls src/features/gradebook/*.tsx src/features/gradebook/*.ts | wc -l  # Should be >= 5

GIT (Codex only)
---
git add web/src/features/gradebook/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build gradebook module — spreadsheet grade entry, student view, 0-20 Moroccan scale"
```

---

### WEB-P1-3 — Invoices Enhancement

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current: web/src/features/invoices/ has 3 files, 70 lines total
  - InvoicesPage.tsx (177 lines) — basic list only
  - invoices.service.ts (33 lines) — list + detail
  - useInvoices.ts (37 lines) — useInvoices query only
Backend endpoints: invoices.py (2), payments.py (3)
  GET  /invoices/                    — list invoices
  GET  /invoices/{id}                — invoice detail
  POST /payments/                    — create payment
  POST /payments/{id}/proof          — upload payment proof
  GET  /payments/{invoice_id}        — get payments for invoice

TASK
----
1. Expand invoices.service.ts — add: getInvoiceDetail(id), createPayment(invoiceId, amount, method), uploadPaymentProof(paymentId, file), getInvoicePayments(invoiceId)

2. Expand useInvoices.ts — add: useInvoiceDetail(id), useCreatePayment(), useUploadProof(), useInvoicePayments(invoiceId)

3. Rewrite InvoicesPage.tsx to use DataTable:
   - Columns: Invoice #, Student, Amount (MAD), Status (Badge), Due Date, Actions
   - Filters: status dropdown, date range, search by student name
   - Pagination component
   - Click row → navigate to /invoices/:id

4. Create InvoiceDetailPage.tsx (~250 lines):
   - Invoice header: number, date, due date, status badge
   - Line items table: description, quantity, unit price, total
   - Payment history section: DataTable of payments (date, amount, method, status)
   - Upload payment proof section: FileUpload component
   - Total and balance due prominently displayed
   - Currency: all amounts in MAD with Moroccan number formatting

5. Wire route: /invoices/:id → InvoiceDetailPage (PAR, ADM, DIR)

6. Add i18n keys under "invoices" namespace.

CONSTRAINTS
-----------
- Currency: always MAD, format with Intl.NumberFormat('fr-MA', { style: 'currency', currency: 'MAD' })
- Use FileUpload from shared/ui for proof upload
- Status badges: draft=neutral, sent=info, paid=success, overdue=error

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build

GIT (Codex only)
---
git add web/src/features/invoices/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): enhance invoices — detail page, payment proof upload, MAD currency formatting"
```

---

### WEB-P1-4 — Innovation: Micro-Budgets Module

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current state: No web/src/features/budgets/ directory exists
Backend: budgets.py — 14 endpoint functions
  GET    /budgets/                          — list budget envelopes
  POST   /budgets/                          — create budget envelope
  GET    /budgets/{id}                      — budget detail
  PUT    /budgets/{id}                      — update budget
  DELETE /budgets/{id}                      — delete budget
  GET    /budgets/{id}/allocations          — list allocations
  POST   /budgets/{id}/allocations          — create allocation
  PUT    /budgets/allocations/{id}          — update allocation
  GET    /budgets/requests                  — list budget requests
  POST   /budgets/requests                  — create request
  PUT    /budgets/requests/{id}/approve     — approve request
  PUT    /budgets/requests/{id}/reject      — reject request
  GET    /budgets/{id}/transactions         — list transactions
  GET    /budgets/analytics                 — budget analytics

TASK
----
1. Create web/src/features/budgets/ with full module:
   budgets.types.ts, budgets.service.ts (all 14 endpoints), useBudgets.ts (queries + mutations)

2. Create BudgetListPage.tsx (~180 lines):
   - DataTable: Name, Total Amount (MAD), Spent, Remaining, Status (Badge), Actions
   - Filters: status, date range
   - "Create Budget" button (ADM/DIR only) → modal/inline form
   - Guards: ADM, DIR

3. Create BudgetDetailPage.tsx (~250 lines):
   - Budget info card (name, total, period)
   - Recharts PieChart: allocation breakdown by category
   - Tabs: "Allocations" | "Transactions" | "Requests"
   - Allocations tab: DataTable of allocations
   - Transactions tab: DataTable of transactions (date, amount, type, description)
   - Requests tab: pending requests with approve/reject buttons (for DIR role)

4. Create BudgetRequestPage.tsx (~150 lines):
   - Form to submit new budget request: amount, category, justification (react-hook-form + zod)
   - List of user's own pending requests

5. Create BudgetAnalyticsPage.tsx (~180 lines):
   - StatCards: total budget, total spent, remaining, request count
   - Recharts: spending trend line, category breakdown bar chart

6. Wire routes: /budgets, /budgets/:id, /budgets/requests, /budgets/analytics
7. Add sidebar nav entry for ADM, DIR roles in Layout.tsx
8. Add i18n keys under "budgets" namespace

CONSTRAINTS
-----------
- All amounts in MAD
- Use shared components: DataTable, Pagination, Badge, StatCard, Tabs, ConfirmDialog (for delete), FormField
- Approve/reject actions must use ConfirmDialog

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build
ls src/features/budgets/*.tsx src/features/budgets/*.ts | wc -l  # >= 7

GIT (Codex only)
---
git add web/src/features/budgets/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build micro-budgets module — envelopes, allocations, requests, analytics with MAD currency"
```

---

### WEB-P1-5 — Innovation: Micro-Schools Module

```
CONTEXT
-------
Project: ecole-platform-dev/web
Current state: No web/src/features/micro-schools/ directory exists
Backend: micro_school.py — 14 endpoint functions
  GET    /micro/                           — list micro-schools
  POST   /micro/                           — create micro-school
  GET    /micro/{id}                       — detail
  PUT    /micro/{id}                       — update
  DELETE /micro/{id}                       — delete
  GET    /micro/{id}/enrollments           — list enrollments
  POST   /micro/{id}/enrollments           — enroll student
  DELETE /micro/{id}/enrollments/{eid}     — unenroll
  GET    /micro/{id}/payments              — list payments
  POST   /micro/{id}/payments              — create payment
  GET    /micro/{id}/resources             — list resources
  POST   /micro/{id}/resources             — add resource
  GET    /micro/{id}/progress              — aggregated progress
  GET    /micro/{id}/progress/{sid}        — student progress

TASK
----
1. Create web/src/features/micro-schools/ with full module:
   micro-schools.types.ts, micro-schools.service.ts (all 14), useMicroSchools.ts

2. Create MicroSchoolListPage.tsx (~180 lines):
   - Card grid layout (not table): school name, student count, status badge, capacity bar
   - Search + status filter
   - "Create" button for ADM/DIR
   - Click card → navigate to detail

3. Create MicroSchoolDetailPage.tsx (~280 lines):
   - Header: school name, description, location, capacity
   - Tabs: "Students" | "Resources" | "Payments" | "Progress"
   - Students tab: DataTable with enroll/unenroll actions
   - Resources tab: list with add resource form
   - Payments tab: payment history table
   - Progress tab: Recharts progress overview

4. Create MicroSchoolEnrollPage.tsx (~150 lines):
   - Enrollment form: student selector, payment info
   - react-hook-form + zod validation

5. Wire routes: /micro-schools, /micro-schools/:id, /micro-schools/:id/enroll
6. Add sidebar nav for ADM, DIR, PAR
7. Add i18n keys

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/micro-schools/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build micro-schools module — CRUD, enrollments, resources, progress tracking"
```

---

## PHASE 2 — Remaining Partial + Next Innovation

---

### WEB-P2-1 — Activities Enhancement

```
CONTEXT
-------
Current: web/src/features/activities/ — 3 files, 69-line ActivitiesPage.tsx (basic list only)
Backend: activities.py (3 endpoints): list, create session, get activity detail

TASK
----
1. Expand service + hook with session management, detail fetch
2. Create ActivityDetailPage.tsx — sessions list, student participation, grading
3. Add filters, search, activity type tabs to ActivitiesPage.tsx
4. Wire route: /activities/:id
5. Add i18n keys

CONSTRAINTS: Use existing shared components. All i18n. No new deps.

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/activities/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): enhance activities module — detail page, sessions, filters"
```

---

### WEB-P2-2 — Content Management Enhancement

```
CONTEXT
-------
Current: web/src/features/content/ — 3 files, 103-line ContentPage.tsx
Backend: content.py (9 endpoints), content_library.py (6 endpoints)

TASK
----
1. Expand service with progress tracking, publish toggle, content ordering
2. Create ContentDetailPage.tsx — single item view, progress bar, student analytics
3. Create ContentPlayerPage.tsx — consume content (video embed, document viewer, quiz launch)
4. Add content type tabs (video, document, quiz, link) to ContentPage.tsx
5. Wire routes: /content/:id, /content/:id/play
6. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/content/ web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): enhance content module — detail, player, type filters, progress tracking"
```

---

### WEB-P2-3 — Feed Enhancement

```
CONTEXT
-------
Current: web/src/features/feed/ — 4 files, 95-line FeedPage.tsx
Backend: feed.py (1 endpoint), WebSocket events for real-time updates
WebSocket client: web/src/services/ws/WebSocketClient.ts (154 lines) — supports 7 event types

TASK
----
1. Expand service with mark-as-read, filter by type
2. Create FeedItem.tsx — individual feed entry component (announcement, grade update, attendance alert, etc.)
3. Integrate WebSocket for real-time feed updates (new items appear at top without refresh)
4. Add real-time unread badge count in sidebar nav (update Layout.tsx)
5. Add infinite scroll (intersection observer) to FeedPage.tsx
6. Add filters: type, date, read/unread
7. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/feed/ web/src/shared/ui/Layout.tsx web/src/app/App.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): enhance feed — real-time WebSocket updates, infinite scroll, filters, unread badge"
```

---

### WEB-P2-4 — Innovation: Skills Passport

```
CONTEXT
-------
No web/src/features/skills/ exists
Backend: skills.py (12 endpoints): dimensions CRUD, milestones, evaluations, passports, analytics

TASK
----
1. Create full module: types, service (12 endpoints), hooks
2. SkillsOverviewPage.tsx — radar chart of skill dimensions (Recharts RadarChart)
3. SkillPassportPage.tsx — printable student passport (all dimensions, milestones achieved, overall level)
4. SkillEvaluationPage.tsx — teacher form: evaluate student per dimension (slider 1-5 or rubric)
5. SkillAnalyticsPage.tsx — class-wide analytics, comparison charts
6. Wire routes: /skills, /skills/passport/:studentId, /skills/evaluate, /skills/analytics
7. Add sidebar nav for TCH, DIR, PAR, STD
8. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/skills/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build skills passport module — radar charts, evaluations, printable passport"
```

---

### WEB-P2-5 — Innovation: MEN Compliance

```
CONTEXT
-------
No web/src/features/compliance/ exists
Backend: compliance.py (12 endpoints): curriculum mappings, dashboards, reports

TASK
----
1. Create full module: types, service (12 endpoints), hooks
2. ComplianceDashboardPage.tsx — gauge charts showing compliance percentage per subject, gap analysis table
3. CurriculumMappingPage.tsx — drag-and-drop or selection UI to map courses to MEN standards
4. ComplianceReportPage.tsx — generate and export MEN compliance reports (PDF/CSV)
5. Wire routes: /compliance, /compliance/mapping, /compliance/reports
6. Add sidebar nav for ADM, DIR
7. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/compliance/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build MEN compliance module — dashboard, curriculum mapping, report generation"
```

---

## PHASE 3 — Final Innovation + Polish

---

### WEB-P3-1 — Innovation: Offline Sync

```
CONTEXT
-------
No web/src/features/sync/ exists
Backend: sync.py (10 endpoints): device registration, queue push/pull, conflicts, checkpoints

TASK
----
1. Create full module: types, service (10 endpoints), hooks
2. SyncStatusPage.tsx — device list, sync status, last checkpoint timestamp, conflict count
3. SyncConflictsPage.tsx — conflict resolution UI (keep local / keep remote / manual merge)
4. SyncSettingsPage.tsx — sync interval config, data scope selection, device management
5. Add sync status indicator icon in Layout.tsx header (green=synced, yellow=syncing, red=conflict)
6. Wire routes: /sync, /sync/conflicts, /sync/settings
7. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/sync/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build offline sync module — device management, conflict resolution, status indicator"
```

---

### WEB-P3-2 — Innovation: Financial Health

```
CONTEXT
-------
No web/src/features/financial-health/ exists
Backend: financial_health.py (12 endpoints): retention, cashflow, cost-per-student, snapshots, exports

TASK
----
1. Create full module: types, service (12 endpoints), hooks
2. FinancialDashboardPage.tsx — multi-chart dashboard:
   - StatCards: retention rate, avg cost per student, monthly cashflow, outstanding balance
   - Recharts: retention trend (LineChart), cashflow waterfall (BarChart), cost comparison (BarChart)
3. FinancialSnapshotsPage.tsx — historical snapshots table with date, key metrics, export button
4. FinancialExportPage.tsx — generate financial reports (select date range, format PDF/Excel)
5. Wire routes: /financial-health, /financial-health/snapshots, /financial-health/export
6. Add sidebar nav for ADM, SYS
7. All amounts in MAD
8. Add i18n keys

VERIFY
------
cd web && npx tsc --noEmit && npm run lint && npm run build

GIT (Codex only)
---
git add web/src/features/financial-health/ web/src/app/App.tsx web/src/shared/ui/Layout.tsx web/src/shared/i18n/locales/
git commit -m "feat(web): build financial health module — dashboard, snapshots, exports with MAD currency"
```

---

### WEB-P3-3 — Component Splitting (Large Files)

```
CONTEXT
-------
These files exceed 400 lines and need splitting into focused sub-components:
  QuizBuilderPage.tsx (711 lines), DocumentsPage.tsx (646 lines), CalendarPage.tsx (539 lines) + shared.tsx (610 lines), ContentLibraryPage.tsx (534 lines), ProfilePage.tsx (499 lines), RegisterPage.tsx (494 lines), TimetablePage.tsx (470 lines)

TASK
----
For EACH file listed above:
1. Read the file and identify logical sections/blocks
2. Extract each section into its own component file in the same feature directory
3. The parent page imports and composes the sub-components
4. Move component-specific types to a types.ts file if one doesn't exist
5. Each sub-component must be < 200 lines

Specific splits:
- QuizBuilderPage.tsx → QuizBuilderForm.tsx, QuestionEditor.tsx, QuestionList.tsx, QuizPreview.tsx
- DocumentsPage.tsx → DocumentList.tsx, DocumentUpload.tsx, DocumentViewer.tsx, DocumentFilters.tsx
- CalendarPage.tsx + shared.tsx → CalendarGrid.tsx, EventForm.tsx, EventDetail.tsx, CalendarFilters.tsx, calendar.types.ts (move types from shared.tsx)
- ContentLibraryPage.tsx → LibraryGrid.tsx, ContentCard.tsx, ContentFilters.tsx
- ProfilePage.tsx → ProfileInfo.tsx, ProfileForm.tsx, AvatarUpload.tsx, SecuritySettings.tsx
- RegisterPage.tsx → RegisterSteps.tsx, PersonalInfoStep.tsx, SchoolInfoStep.tsx, VerificationStep.tsx
- TimetablePage.tsx → TimetableGrid.tsx, SlotEditor.tsx, TimetableFilters.tsx

CONSTRAINTS
-----------
- Do NOT change any functionality or visual appearance
- All existing imports in other files that reference these pages must still work (keep re-exports)
- Each new sub-component must be typed with explicit Props interface

VERIFY
------
cd web
npx tsc --noEmit
npm run lint
npm run build
# Verify no file > 300 lines in the split features:
find src/features/cms src/features/documents src/features/calendar src/features/teacher src/features/profile src/features/auth src/features/timetable -name "*.tsx" -exec wc -l {} + | awk '$1 > 300 {print "WARN: " $0}'

GIT (Codex only)
---
git add web/src/features/cms/ web/src/features/documents/ web/src/features/calendar/ web/src/features/teacher/ web/src/features/profile/ web/src/features/auth/ web/src/features/timetable/
git commit -m "refactor(web): split 7 oversized page components into focused sub-components (all < 200 lines)"
```

---

### WEB-P3-4 — Dark Mode Polish

```
CONTEXT
-------
Dark mode variables and toggle were added in WEB-P0-5.
Now need to verify and fix all feature pages.

TASK
----
1. Audit EVERY feature page for hardcoded colors that slipped through P0-5:
   grep -rn "#[0-9a-fA-F]\{3,6\}" src/features/ src/shared/ --include="*.tsx" --include="*.ts"
   Replace all findings with CSS variable references.

2. Audit Recharts usage — ensure all chart colors use CSS variables or theme-aware values:
   grep -rn "fill=" src/features/ --include="*.tsx"
   grep -rn "stroke=" src/features/ --include="*.tsx"
   Replace with: fill="var(--color-primary)" or a useTheme()-aware color array

3. Ensure all new feature pages (attendance, gradebook, budgets, micro-schools, skills, compliance, sync, financial-health) render correctly in dark mode. Fix any issues.

4. Test RTL (Arabic) + dark mode combination — fix any layout issues.

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build
# Should be zero hardcoded colors in TSX files:
grep -rn "#[0-9a-fA-F]\{3,6\}" src/features/ --include="*.tsx" | wc -l  # Target: 0

GIT (Codex only)
---
git add web/src/
git commit -m "fix(web): audit and fix dark mode across all feature pages and Recharts components"
```

---

### WEB-P3-5 — Full Accessibility Audit

```
CONTEXT
-------
Accessibility foundation was added in WEB-P0-4.
Now need to extend to ALL feature pages.

TASK
----
1. Add aria-label to every DataTable usage across all feature pages
2. Add aria-label to every form <input>, <select>, <textarea> not using FormField components
3. Add alt="" to all <img> tags (or meaningful alt text if image conveys information)
4. Add role="status" to all loading indicators
5. Add aria-live="polite" to all async result areas (query results, form submission feedback)
6. Verify every ConfirmDialog usage has proper focus management
7. Ensure all buttons have descriptive text or aria-label (no icon-only buttons without labels)
8. Add aria-label to all navigation links in sidebar

VERIFY
------
cd web
npx tsc --noEmit && npm run lint && npm run build
grep -rn "aria-" src/features/ --include="*.tsx" | wc -l  # Target: >= 50

GIT (Codex only)
---
git add web/src/
git commit -m "feat(web): comprehensive accessibility audit — ARIA labels, focus management, screen reader support"
```

---

## PHASE 4 — Testing & Verification

---

### WEB-P4-1 — Test Infrastructure

```
CONTEXT
-------
Current test state: 2 unit tests (api-client.test.ts, auth-context.test.tsx), 5 E2E tests
Vitest configured in web/vitest.config.ts with jsdom, vmThreads pool
Test setup: web/tests/setup.ts (imports @testing-library/jest-dom)
No MSW, no test utilities, no factories

TASK
----
1. Install msw@2: cd web && npm install -D msw

2. Create web/tests/utils/render.tsx:
   Custom render function that wraps components with:
   - QueryClientProvider (fresh QueryClient per test)
   - MemoryRouter (from react-router-dom)
   - AuthContext mock (configurable: authenticated/unauthenticated, role)
   - i18n provider (test locale = en)
   Export: renderWithProviders(ui, { route?, user?, queryClient? })

3. Create web/tests/utils/mocks.ts:
   MSW handlers for core endpoints:
   - GET /api/v1/auth/me → mock user
   - GET /api/v1/attendance/class/:id → mock attendance data
   - GET /api/v1/gradebook/class/:id → mock gradebook data
   - GET /api/v1/invoices/ → mock invoice list
   - GET /api/v1/budgets/ → mock budget list
   Add server setup/teardown in tests/setup.ts

4. Create web/tests/utils/factories.ts:
   Factory functions: createUser(), createSchool(), createClass(), createStudent(), createGrade(), createInvoice(), createBudget()
   Each returns a fully typed object with sensible defaults and optional overrides.

5. Update web/tests/setup.ts to include MSW server setup.

VERIFY
------
cd web
npx tsc --noEmit
npm run test    # Existing 2 tests still pass

GIT (Codex only)
---
git add web/tests/ web/package.json web/package-lock.json
git commit -m "feat(web): add test infrastructure — MSW handlers, custom render, test factories"
```

---

### WEB-P4-2 — Shared Component Tests

```
CONTEXT
-------
Test utils from WEB-P4-1 are available.
Shared components in web/src/shared/ui/ need unit tests.

TASK
----
Create tests in web/tests/unit/shared/:

1. DataTable.test.tsx:
   - Renders columns and data correctly
   - Sorts by column click (asc → desc → none)
   - Shows empty state when data is empty
   - Shows skeleton when loading
   - Calls onRowClick when row is clicked

2. FormField.test.tsx:
   - Renders label and input
   - Shows validation error from react-hook-form
   - Supports disabled state

3. ConfirmDialog.test.tsx:
   - Opens and renders title/message
   - Calls onConfirm when confirm clicked
   - Calls onCancel when cancel clicked or Escape pressed
   - Traps focus within dialog

4. Pagination.test.tsx:
   - Renders page numbers
   - Disables prev on first page, next on last page
   - Calls onPageChange with correct page number

5. SearchInput.test.tsx:
   - Debounces onChange calls
   - Clear button resets value

6. ErrorBoundary.test.tsx:
   - Catches error and shows fallback
   - Retry button resets error state

7. Badge.test.tsx:
   - Renders all variants with correct CSS classes

VERIFY
------
cd web
npm run test  # All tests pass
npm run test -- --reporter=verbose | grep "PASS\|FAIL"  # Should show all PASS

GIT (Codex only)
---
git add web/tests/unit/shared/
git commit -m "test(web): add unit tests for all shared UI components"
```

---

### WEB-P4-3 — Feature Page Tests

```
CONTEXT
-------
Test utils and MSW handlers from WEB-P4-1 are available.

TASK
----
Create tests in web/tests/unit/features/:

1. AttendancePage.test.tsx — loads student list, toggles status, submits
2. GradebookPage.test.tsx — loads grid, enters grade (0-20 validation), saves
3. InvoiceDetailPage.test.tsx — loads invoice, displays line items, shows payment history
4. BudgetListPage.test.tsx — loads budgets, filters by status
5. MicroSchoolListPage.test.tsx — loads schools, search, navigate to detail
6. SkillsOverviewPage.test.tsx — loads skill dimensions, renders content
7. ComplianceDashboardPage.test.tsx — loads compliance data, renders metrics
8. FinancialDashboardPage.test.tsx — loads financial data, renders stat cards
9. AuthContext.test.tsx — login flow, 2FA verify, token refresh, logout (enhance existing)

Each test should:
- Use renderWithProviders() with appropriate role
- Mock API responses via MSW
- Test happy path + error state + loading state
- Use screen queries from @testing-library/react

VERIFY
------
cd web
npm run test
npm run test:coverage  # Check coverage output

GIT (Codex only)
---
git add web/tests/unit/features/
git commit -m "test(web): add unit tests for all feature pages — attendance, gradebook, budgets, skills, compliance, financial"
```

---

### WEB-P4-4 — E2E Test Expansion

```
CONTEXT
-------
Existing E2E: 5 tests in web/e2e/ (parent feed, teacher assignment, student submission, admin invitation, 2FA)
Playwright configured, helpers.ts exists

TASK
----
Add to web/e2e/:

1. attendance-flow.spec.ts — Teacher marks attendance for a class, parent views history
2. gradebook-flow.spec.ts — Teacher enters grades, student views grade detail
3. invoice-payment.spec.ts — Parent views invoice, uploads payment proof
4. budget-flow.spec.ts — Admin creates budget, director approves request
5. dark-mode.spec.ts — Toggle dark mode, verify CSS variable changes, verify persistence
6. language-switch.spec.ts — Switch FR → AR, verify RTL direction attribute, switch back to FR

CONSTRAINTS: Use existing helpers.ts patterns. Each test must be independent and not depend on other test state.

VERIFY
------
cd web
npm run test:e2e  # All tests pass (or at least compile without error)

GIT (Codex only)
---
git add web/e2e/
git commit -m "test(web): add 6 E2E tests — attendance, gradebook, invoice, budget, dark mode, i18n"
```

---

### WEB-P4-5 — Final Verification Gate

```
CONTEXT
-------
All phases P0-P4 are complete. This is the final verification pass.

TASK
----
Run ALL of these commands and fix any failures:

1. TypeScript: cd web && npx tsc --noEmit
2. Lint: npm run lint
3. Unit tests: npm run test
4. E2E tests: npm run test:e2e
5. Production build: npm run build
6. Build size check: ls -la dist/assets/ (warn if any chunk > 500KB)

7. Feature coverage audit — verify these directories exist and have >= 3 files each:
   src/features/attendance/
   src/features/gradebook/
   src/features/budgets/
   src/features/micro-schools/
   src/features/skills/
   src/features/compliance/
   src/features/sync/
   src/features/financial-health/

8. Shared component audit — verify these files exist:
   src/shared/ui/DataTable.tsx
   src/shared/ui/Pagination.tsx
   src/shared/ui/ConfirmDialog.tsx
   src/shared/ui/Skeleton.tsx
   src/shared/ui/Badge.tsx
   src/shared/ui/Tabs.tsx
   src/shared/ui/Breadcrumb.tsx
   src/shared/ui/SearchInput.tsx
   src/shared/ui/StatCard.tsx
   src/shared/ui/ErrorBoundary.tsx
   src/shared/ui/FormField.tsx

9. Accessibility check:
   grep -rn "aria-" src/ --include="*.tsx" | wc -l  # Target: >= 100

10. Dark mode check:
    grep "data-theme" src/app/styles.css | wc -l  # Target: >= 1
    grep -c "#[0-9a-fA-F]\{3,6\}" src/features/**/*.tsx  # Target: 0 (no hardcoded colors)

11. i18n check:
    grep -c "t(" src/features/**/*.tsx | awk -F: '{sum+=$2} END {print sum}'  # Target: >= 200

VERIFY
------
All 11 checks must pass. If any fail, fix the issue and re-run.
Output a summary table:
| Check | Status | Details |
|-------|--------|---------|
| TypeScript | PASS/FAIL | error count |
| Lint | PASS/FAIL | warning count |
| ... | ... | ... |

GIT (Codex only)
---
git add -A
git commit -m "chore(web): final verification gate — all checks green"
```

---

## Summary

| Prompt | Phase | Scope | Est. Files |
|--------|-------|-------|-----------|
| WEB-P0-1 | Infrastructure | Form library + components | 8 |
| WEB-P0-2 | Infrastructure | Shared component library | 10 |
| WEB-P0-3 | Infrastructure | Error boundaries + network | 5 |
| WEB-P0-4 | Infrastructure | Accessibility foundation | 3 |
| WEB-P0-5 | Infrastructure | Dark mode | 3 |
| WEB-P0-6 | Infrastructure | TypeScript types + routes | 5 |
| WEB-P1-1 | Critical | Attendance (full build) | 7 |
| WEB-P1-2 | Critical | Gradebook (new) | 6 |
| WEB-P1-3 | Critical | Invoices (enhance) | 3 |
| WEB-P1-4 | Innovation | Micro-Budgets | 7 |
| WEB-P1-5 | Innovation | Micro-Schools | 6 |
| WEB-P2-1 | Partial | Activities (enhance) | 2 |
| WEB-P2-2 | Partial | Content (enhance) | 3 |
| WEB-P2-3 | Partial | Feed (enhance) | 3 |
| WEB-P2-4 | Innovation | Skills Passport | 7 |
| WEB-P2-5 | Innovation | MEN Compliance | 6 |
| WEB-P3-1 | Innovation | Offline Sync | 6 |
| WEB-P3-2 | Innovation | Financial Health | 6 |
| WEB-P3-3 | Refactor | Component splitting | ~28 |
| WEB-P3-4 | Polish | Dark mode audit | 0 (edits) |
| WEB-P3-5 | Polish | Accessibility audit | 0 (edits) |
| WEB-P4-1 | Testing | Test infrastructure | 4 |
| WEB-P4-2 | Testing | Shared component tests | 7 |
| WEB-P4-3 | Testing | Feature page tests | 9 |
| WEB-P4-4 | Testing | E2E expansion | 6 |
| WEB-P4-5 | Verification | Final gate | 0 |
| **Total** | **26 prompts** | | **~150 files** |
