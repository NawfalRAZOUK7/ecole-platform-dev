# École Platform — TODO General 2 (Phases 13–18 + Cross-Cutting)

> Granular task checklist for future development. Each item maps to a sub-task within a phase.
> Mark `[x]` as you complete each item.

---

## Phase 13 — Notifications Center

### 13A — Backend
- [x] Notification hub service with channel routing (in-app, push, email)
- [x] `GET /notifications` — list with cursor pagination + read/type filters
- [x] `POST /notifications/{id}/read` — mark single as read
- [x] `POST /notifications/read-all` — mark all as read
- [x] `DELETE /notifications/{id}` — soft-delete
- [x] `GET /notifications/preferences` — user notification preferences
- [x] `PUT /notifications/preferences` — update preferences
- [x] Device token registration/deregistration endpoints
- [x] FCM integration via `firebase-admin` SDK
- [x] Push delivery tracking (sent, delivered, failed, clicked)
- [x] Email digest service with Jinja2 templates (fr/ar/en)
- [x] ARQ scheduled task for daily digest at 07:00
- [x] Unread count endpoint with Redis caching (30s TTL)
- [x] Database migrations: notification_preferences, device_tokens
- [x] ABAC enforcement on all endpoints

### 13B — Web Frontend
- [x] Notification bell icon in Layout header with unread badge
- [x] Dropdown quick-view (last 5 unread)
- [x] `/notifications` page — full list with infinite scroll
- [x] Read/unread toggle filter + mark-all-read button
- [x] Click-through navigation to `action_url`
- [x] `/settings/notifications` preferences page
- [x] i18n keys in fr/en/ar

### 13C — Mobile
- [x] `NotificationsScreen` — list with pull-to-refresh
- [x] Swipe-to-dismiss (soft delete) + swipe-to-read
- [x] Badge on bottom nav icon (unread count)
- [x] `NotificationPreferencesScreen` — switches for channels
- [x] `flutter_local_notifications` foreground display
- [x] Offline cache: last 100 notifications in SQLite
- [x] i18n keys in fr/en/ar

### 13D — Tests
- [x] Postman collection: notification CRUD + preferences
- [x] Integration tests: channel routing, preferences
- [x] Push delivery mock tests
- [x] Email digest template rendering tests
- [ ] Load test: 1000 batch notifications within 10s

---

## Phase 14 — Reports & Analytics

### 14A — Backend
- [x] PDF generation service (WeasyPrint)
- [x] Report templates: student report card, class summary, attendance, billing
- [x] Bilingual PDF support (fr/ar with RTL)
- [x] Async report generation (POST /reports/generate → job_id)
- [x] Report status tracking + signed URL download
- [x] CSV streaming export endpoint
- [x] XLSX export via openpyxl
- [x] Analytics API: overview, attendance trends, grade distributions, billing, engagement
- [x] Redis caching for analytics (5min TTL)
- [x] Date range filtering with comparison periods
- [x] Database migrations: report_jobs, data_exports
- [x] Report file cleanup task (24h expiry)

### 14B — Web Frontend
- [x] `/reports` page with type selector + parameter form
- [x] Generate → progress → download flow
- [x] Report history table
- [x] Analytics dashboard (ADM/DIR): KPI cards, trend charts, distribution charts
- [x] Date range picker with presets + comparison mode
- [x] Export buttons (PNG chart, CSV/XLSX data)

### 14C — Mobile
- [x] `ReportsScreen` with role-filtered report types
- [x] Generate → notification → download/share flow
- [x] PDF viewer + share sheet
- [x] `AnalyticsSummaryScreen` (ADM/DIR) with sparklines
- [x] Offline cache for last 5 reports

### 14D — Tests
- [x] Postman collection: report generation + analytics endpoints
- [x] PDF output validation tests
- [x] CSV/XLSX field accuracy tests
- [x] Analytics query accuracy vs raw SQL
- [ ] Performance: report generation < 30s for 40-student class

---

## Phase 15 — Calendar & Events

### 15A — Backend
- [ ] Calendar service with Moroccan holiday seed data
- [ ] Event CRUD with type/visibility controls
- [ ] Recurring event support (weekly, annual)
- [ ] RSVP system with capacity enforcement
- [ ] Reminder service (ARQ periodic task, every 5min)
- [ ] iCal feed generation with signed token auth
- [ ] Event visibility filtering by role + class membership
- [ ] Database migrations: events, event_rsvps, event_reminders, moroccan_holidays

### 15B — Web Frontend
- [ ] `/calendar` page with month/week/list views
- [ ] Color-coded events by type
- [ ] Event creation modal
- [ ] Event detail with RSVP + attendee list
- [ ] Add to external calendar buttons (Google, Outlook, iCal)
- [ ] Filter sidebar (type, class)

### 15C — Mobile
- [ ] `CalendarScreen` with `table_calendar` package
- [ ] Event detail bottom sheet with RSVP
- [ ] Device calendar integration
- [ ] Push notification reminders
- [ ] Offline cache for current month

### 15D — Tests
- [ ] Postman collection: event CRUD + RSVP
- [ ] Recurring event generation tests
- [ ] RSVP capacity enforcement tests
- [ ] Reminder dispatch timing tests
- [ ] iCal RFC 5545 compliance tests

---

## Phase 16 — Document Management

### 16A — Backend
- [ ] Pluggable file storage (LocalStorage + S3Storage)
- [ ] Upload endpoint with MIME validation + size limits + SHA-256 dedup
- [ ] Thumbnail generation (Pillow)
- [ ] Signed URL download endpoint (1h expiry)
- [ ] Student document CRUD with category + expiry
- [ ] Document checklist per school (required docs config)
- [ ] Expiry notification (30 days before)
- [ ] Teacher resource library with full-text search (tsvector)
- [ ] Resource rating system
- [ ] Database migrations: documents, resources, resource_ratings, student_document_requirements
- [ ] File cleanup task (30 days after soft delete)

### 16B — Web Frontend
- [ ] `/documents` page with tabs (My Docs, Student Docs, Resources)
- [ ] Drag-and-drop upload zone with progress bar
- [ ] Grid/list view toggle with thumbnails
- [ ] Inline preview (images, PDFs)
- [ ] Student document checklist with status badges
- [ ] Resource library with search, filters, rating stars
- [ ] Bulk actions (download ZIP, delete)

### 16C — Mobile
- [ ] `DocumentsScreen` with tab layout + category chips
- [ ] Camera capture for document scanning
- [ ] File picker upload with progress
- [ ] PDF/image preview screen
- [ ] Resource library with search
- [ ] Downloaded files available offline

### 16D — Tests
- [ ] Upload/download integration tests (all MIME types)
- [ ] SHA-256 dedup verification
- [ ] Full-text search accuracy tests
- [ ] RBAC tests: document endpoints x all roles
- [ ] Storage backend tests (local + S3 mock)

---

## Phase 17 — Exam Management

### 17A — Backend
- [ ] Exam CRUD with status lifecycle (draft → scheduled → grading → published → archived)
- [ ] Exam types aligned with Moroccan curriculum (CC, DS, ER, EN)
- [ ] Conflict detection (same class, overlapping time)
- [ ] Room and proctor assignment
- [ ] Grading scale configuration (0-20 default)
- [ ] Grade entry with batch support + validation
- [ ] Double-entry verification option
- [ ] Grade statistics (min, max, avg, median, std_dev, distribution)
- [ ] Weighted average calculation (coefficient system)
- [ ] Result publication with notification triggers
- [ ] Bulletin scolaire PDF generation (per-period + annual)
- [ ] Grade appeal workflow (submit → review → decide → notify)
- [ ] Database migrations: exams, exam_grades, grading_scales, grade_appeals, exam_proctors
- [ ] Calendar integration (exams on Phase 15 calendar)

### 17B — Web Frontend
- [ ] Exam management page (calendar + list views)
- [ ] Exam creation form with conflict detection
- [ ] Grading interface with batch entry + live statistics
- [ ] Results view: period summary, weighted averages, rank
- [ ] Bulletin PDF download
- [ ] Appeals management page (ADM)

### 17C — Mobile
- [ ] `ExamsScreen` with upcoming/past tabs + countdown
- [ ] Grading screen (TCH) with numeric keypad
- [ ] Results screen with grade cards
- [ ] Bulletin download/share
- [ ] Appeal submission (PAR)
- [ ] Offline cache for exam schedule + grades

### 17D — Tests
- [ ] Exam conflict detection tests
- [ ] Weighted average calculation accuracy tests
- [ ] Double-entry discrepancy detection tests
- [ ] Result publication notification tests
- [ ] Appeal workflow end-to-end tests
- [ ] Bulletin PDF content verification

---

## Phase 18 — Parent-Teacher Meetings

### 18A — Backend
- [ ] Teacher availability management (recurring + one-time slots)
- [ ] Meeting booking with double-booking prevention (optimistic locking)
- [ ] Buffer time + daily limit enforcement
- [ ] Meeting status lifecycle (requested → confirmed → completed → cancelled)
- [ ] Jitsi Meet room generation with JWT auth
- [ ] Meeting notes CRUD (teacher writes, parent reads)
- [ ] Action items tracking with status + due dates
- [ ] Follow-up reminders via notification hub
- [ ] Bulk conference day scheduling (ADM)
- [ ] School-level meeting settings
- [ ] Database migrations: teacher_availability, meetings, meeting_notes, meeting_action_items

### 18B — Web Frontend
- [ ] Meetings page with tabs (Upcoming, Past, Action Items)
- [ ] Multi-step booking flow (teacher → date → slot → confirm)
- [ ] Teacher availability grid editor
- [ ] Meeting detail with video join button
- [ ] Notes section (TCH editable, PAR read-only)
- [ ] Action items checklist with due dates
- [ ] Admin meeting settings page

### 18C — Mobile
- [ ] `MeetingsScreen` with upcoming/past tabs
- [ ] Bottom sheet booking flow
- [ ] Video call join (Jitsi/external app)
- [ ] Meeting detail with notes + action items
- [ ] Teacher availability editor
- [ ] Push reminders + status change notifications
- [ ] Offline cache for meetings + action items

### 18D — Tests
- [ ] Double-booking prevention tests (concurrent simulation)
- [ ] Buffer time + daily limit tests
- [ ] Jitsi room URL generation tests
- [ ] Meeting notes visibility tests
- [ ] Action item lifecycle tests
- [ ] Cancellation notification tests

---

## Cross-Cutting Concerns

### Performance
- [ ] Database query optimization audit (EXPLAIN ANALYZE on slow queries)
- [ ] Add database indexes for common filter patterns
- [ ] Implement connection pooling tuning (asyncpg pool size)
- [ ] Add Redis pipeline for batch operations
- [ ] Frontend bundle size audit + code splitting
- [ ] Image lazy loading + responsive sizes
- [ ] Mobile: implement pagination for all list screens

### Accessibility (a11y)
- [ ] Web: WCAG 2.1 AA audit on all pages
- [ ] Web: keyboard navigation for all interactive elements
- [ ] Web: screen reader labels (aria-label, aria-describedby)
- [ ] Web: color contrast verification (4.5:1 ratio)
- [ ] Mobile: TalkBack/VoiceOver testing on key flows
- [ ] Mobile: minimum touch target sizes (48dp)

### Security Hardening
- [ ] Rate limiting on all auth endpoints (10 req/min)
- [ ] Rate limiting on file upload endpoints (5 req/min)
- [ ] CSRF protection audit
- [ ] Content Security Policy headers
- [ ] SQL injection audit (parameterized queries verification)
- [ ] XSS audit on user-generated content rendering
- [ ] File upload: magic byte validation (not just extension)
- [ ] JWT refresh token rotation
- [ ] Audit log for admin actions

### i18n & L10n
- [ ] Arabic RTL layout testing on all pages/screens
- [ ] Date/number formatting per locale verification
- [ ] Missing translation key audit (all 3 locales)
- [ ] Moroccan Darija informal strings review
- [ ] Currency formatting: MAD with proper symbol placement

### Mobile Offline Support
- [ ] SQLite local database for offline data
- [ ] Sync queue for offline mutations (retry on reconnect)
- [ ] Offline indicator in app bar
- [ ] Graceful degradation: read cached data when offline
- [ ] Conflict resolution strategy for sync (last-write-wins vs merge)

### DevOps & CI/CD
- [ ] GitHub Actions: lint + test on PR
- [ ] GitHub Actions: build Docker images on merge to main
- [ ] Staging environment auto-deploy
- [ ] Database migration CI check (no breaking changes)
- [ ] Dependency vulnerability scanning (Dependabot/Snyk)
- [ ] Mobile: Fastlane setup for iOS/Android builds
