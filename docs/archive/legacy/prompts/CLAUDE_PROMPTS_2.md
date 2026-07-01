# École Platform — Claude Prompts (Phases 13-18)

> Each prompt is self-contained. Copy-paste it into a new session.
> After finishing a phase, close the session and open a new one for the next phase.
> Phases 0-12 are covered in CLAUDE_PROMPTS.md. This file continues with new feature phases.

---

## Phase 13 — Notifications Center

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs access to existing COM domain models, mobile push config, and report specs.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-12 are done. I need you to implement Phase 13.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 13 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/models/com.py for existing notification models
- Read ecole-platform-dev/backend/app/services/ for existing notification delivery logic
- Read ecole-platform-dev/mobile/lib/shared/push_notifications.dart for current FCM/APNs setup
- Read ecole-platform-dev/web/src/features/ for existing notification page

PHASE 13 — Notifications Center:

BACKEND (FastAPI):
- Notification hub service — backend/app/services/notification_hub.py
  - Unified notification registry: in-app, push, email, SMS channels
  - Notification preferences per user per channel: POST /notifications/preferences, GET /notifications/preferences
  - Channel routing engine: decide which channels based on user prefs + notification priority
  - Batch notification creation: POST /notifications/batch (ADM, SYS roles)
  - Mark as read/unread: PATCH /notifications/{id}/read, PATCH /notifications/mark-all-read
  - Notification categories: academic, billing, attendance, system, announcement
  - Unread count endpoint: GET /notifications/unread-count (lightweight, cacheable 30s in Redis)
  - Notification history with filters: GET /notifications?category=&channel=&read=&from=&to= (cursor pagination)
  - Delete notification: DELETE /notifications/{id} (soft delete, ADM can hard delete)
- Push notification configuration — backend/app/services/push_config.py
  - Device token registration: POST /devices/register (token, platform, device_name)
  - Device token deregistration: DELETE /devices/{device_id}
  - List registered devices: GET /devices (per user)
  - FCM server-side send via firebase-admin SDK
  - APNs fallback via FCM unified API
  - Silent push for background data sync
  - Push delivery tracking: store delivery_status (sent, delivered, failed, clicked)
  - Retry with exponential backoff for transient failures (max 3 retries)
- Email digest service — backend/app/services/email_digest.py
  - Digest preferences: daily or weekly summary, per user
  - POST /notifications/digest/preferences (PAR, TCH, ADM)
  - Celery/ARQ task: generate digest at configured time (default 07:00 Africa/Casablanca)
  - Email template rendering (Jinja2): fr/ar/en with RTL support for Arabic
  - Digest content: unread notifications grouped by category, action links
  - Unsubscribe link with signed token (one-click unsubscribe per CAN-SPAM/GDPR)
  - SMTP integration via environment config (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS)
  - Email delivery tracking: sent, bounced, opened (via pixel if consented)
- Database migrations:
  - notification_preferences table (user_id, channel, category, enabled, digest_frequency)
  - device_tokens table (user_id, token, platform, device_name, last_active_at)
  - notification_deliveries: add channel, delivery_status, delivered_at, clicked_at columns
- Pydantic schemas: schemas/notifications.py (preferences, device registration, digest config)
- RBAC: PAR/STD read own, TCH read own + class notifications, ADM full access, SYS batch create
- Audit trail on preference changes, batch sends, device registrations

WEB FRONTEND (React):
- Notification center page — /notifications (redesigned)
  - Bell icon in header with unread badge (polls every 60s or WebSocket)
  - Dropdown quick-view: last 5 unread notifications with mark-as-read
  - Full page: filterable list by category, read/unread, date range
  - Mark all as read button
  - Click notification → navigate to relevant page (deep link mapping)
  - Empty state, loading skeleton, error state
- Notification preferences page — /settings/notifications
  - Toggle per category per channel (in-app, push, email)
  - Digest frequency selector (off, daily, weekly)
  - Device management: list registered devices, remove device
- i18n: all strings in fr/ar/en, RTL for Arabic

MOBILE (Flutter):
- Notification center screen (redesigned)
  - Pull-to-refresh, infinite scroll with cursor pagination
  - Category filter chips (academic, billing, attendance, system)
  - Swipe to mark as read, swipe to delete
  - Tap → deep link navigation to relevant screen
  - Unread badge on bottom nav bar icon
- Push notification handling improvements
  - Foreground: show in-app banner (dismissible)
  - Background: system notification with deep link
  - Token refresh on app start, register with backend
- Notification preferences screen
  - Per-category per-channel toggles
  - Digest frequency picker
- Offline: cache last 100 notifications in SQLite, sync on reconnect

ACCEPTANCE CRITERIA:
- [ ] Unread count updates within 2s of new notification
- [ ] Push notification delivered to registered device within 5s
- [ ] Email digest sent at configured time with correct timezone
- [ ] Notification preferences persist across sessions
- [ ] Device token auto-refreshes on FCM token rotation
- [ ] Category filters work correctly on all platforms
- [ ] Mark-all-read clears badge on web and mobile
- [ ] Unsubscribe link works without authentication
- [ ] RBAC enforced: students cannot send batch notifications
- [ ] Audit log captures all preference changes and batch operations
- [ ] All new endpoints return 401/404/403 in correct deny ordering
- [ ] Integration tests for notification hub (happy + unhappy paths)
- [ ] i18n complete for fr/ar/en on web and mobile

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Follow router → service → repository layer pattern.
- Use SQLAlchemy 2.0 async with Mapped[] type annotations.
- Do Phase 13 ONLY. When done, stop and wait.
```

---

## Phase 14 — Reports & Analytics

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)
**Why parent?** Needs access to KPI service, analytics events, and all domain models for report generation.

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-13 are done. I need you to implement Phase 14.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 14 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/services/kpi.py for existing KPI computation
- Read ecole-platform-dev/backend/app/services/analytics.py for event tracking
- Read ecole-platform-dev/backend/app/models/ for all domain models

PHASE 14 — Reports & Analytics:

BACKEND (FastAPI):
- PDF report generation — backend/app/services/reports.py
  - WeasyPrint or reportlab for server-side PDF rendering
  - Report templates (Jinja2 HTML → PDF):
    - Student report card: grades per subject, attendance %, teacher comments, period summary
    - Class summary report: average grades, attendance stats, top/bottom performers
    - Attendance report: per-student absence count, justified vs unjustified, trends
    - Billing statement: invoices, payments, outstanding balance per parent
    - School-wide analytics: enrollment counts, grade distributions, attendance rates
  - Report generation endpoint: POST /reports/generate (async, returns job_id)
  - Report status: GET /reports/{job_id}/status (pending, generating, ready, failed)
  - Report download: GET /reports/{job_id}/download (returns PDF, signed URL, 24h expiry)
  - Report list: GET /reports?type=&period=&status= (cursor pagination)
  - Background task via Celery/ARQ for heavy report generation
  - Report caching: same parameters within 1h returns cached version
  - Bilingual report support: fr/ar with RTL layout for Arabic PDFs
- Exportable data — backend/app/services/data_export.py
  - CSV export for tabular data: GET /export/csv?entity=&filters= (streaming response)
  - Supported entities: students, grades, attendance, invoices, payments
  - Excel export (openpyxl): GET /export/xlsx?entity=&filters=
  - Export size limit: max 10,000 rows per request (paginate for larger)
  - Export audit: log who exported what and when
- Admin analytics dashboard API — backend/app/api/v1/analytics.py
  - GET /analytics/overview — school-wide KPIs (active users, attendance rate, grade avg, collection rate)
  - GET /analytics/attendance?period=&class_id= — attendance trends (daily/weekly/monthly)
  - GET /analytics/grades?period=&subject= — grade distribution histograms
  - GET /analytics/billing?period= — revenue, outstanding, collection rate trends
  - GET /analytics/engagement — platform usage metrics (DAU, MAU, feature adoption)
  - All analytics endpoints support date range filtering and comparison periods
  - Redis caching with 5min TTL for dashboard queries
  - Prometheus metrics: report_generation_count, report_generation_duration_seconds
- Database migrations:
  - report_jobs table (id, type, parameters, status, requester_id, file_path, created_at, completed_at, expires_at)
  - data_exports table (id, entity, filters, format, requester_id, row_count, created_at)
- Pydantic schemas: schemas/reports.py, schemas/analytics.py
- RBAC:
  - STD: own report card only
  - PAR: own children report cards + billing statements
  - TCH: class summary, attendance reports for assigned classes
  - ADM/DIR: all reports + analytics dashboard + data exports
- Audit trail on all report generation and data export operations

WEB FRONTEND (React):
- Reports page — /reports
  - Report type selector (report card, class summary, attendance, billing, school analytics)
  - Parameter form: period, class, student selectors (role-filtered)
  - Generate button → progress indicator → download link
  - Report history table with status badges and re-download
- Analytics dashboard — /analytics (ADM/DIR only)
  - KPI cards: active users, attendance rate, avg grade, collection rate
  - Charts (recharts or chart.js):
    - Attendance trend line chart (daily/weekly/monthly toggle)
    - Grade distribution bar chart per subject
    - Billing waterfall: invoiced → paid → outstanding
    - Engagement funnel: registered → active → engaged
  - Date range picker with preset options (this week, this month, this period, custom)
  - Comparison mode: compare with previous period
  - Export buttons: download chart as PNG, download data as CSV/XLSX
- i18n: all labels, chart axes, report templates in fr/ar/en

MOBILE (Flutter):
- Reports screen
  - List of available reports (filtered by role)
  - Generate report → background task → push notification when ready
  - Download and open PDF (share sheet on iOS/Android)
  - Report history with status indicators
- Analytics summary screen (ADM/DIR only)
  - KPI cards with sparkline trends
  - Simplified charts (fl_chart package)
  - Tap card → detail view with full chart
- Offline: cache last 5 generated reports in local storage

ACCEPTANCE CRITERIA:
- [ ] PDF report generates within 30s for a class of 40 students
- [ ] Arabic PDF renders correctly with RTL layout
- [ ] CSV/XLSX export streams without loading entire dataset in memory
- [ ] Analytics dashboard loads within 2s (Redis cached)
- [ ] Charts render correctly with real data
- [ ] Date range comparison shows % change indicators
- [ ] Export audit log captures all download events
- [ ] Report files auto-expire after 24h (cleanup task)
- [ ] RBAC: students cannot access class-wide or school-wide reports
- [ ] Mobile PDF opens in system viewer (share sheet)
- [ ] All new endpoints follow deny ordering (401 → 404 → 403)
- [ ] Integration tests for report generation pipeline
- [ ] i18n complete for fr/ar/en on web, mobile, and PDF templates

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Do Phase 14 ONLY. When done, stop and wait.
```

---

## Phase 15 — Calendar & Events

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-14 are done. I need you to implement Phase 15.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 15 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/models/erp.py for academic_years, periods, classes
- Read ecole-platform-dev/backend/app/services/notification_hub.py for notification integration

PHASE 15 — Calendar & Events:

BACKEND (FastAPI):
- Calendar service — backend/app/services/calendar.py
  - School calendar with Moroccan holidays (auto-populated): Eid Al-Fitr, Eid Al-Adha, Mawlid, Independence Day, Green March, etc.
  - Academic calendar events: period start/end, exam weeks, holidays, teacher training days
  - Custom events: school-specific events created by ADM/DIR
  - Event CRUD:
    - POST /events (ADM, DIR, TCH for class events)
    - GET /events?from=&to=&type=&class_id= (all authenticated roles, filtered by visibility)
    - GET /events/{id} (detail with RSVP stats)
    - PUT /events/{id} (ADM, DIR, event creator)
    - DELETE /events/{id} (ADM, DIR, soft delete)
  - Event types: holiday, exam, meeting, excursion, ceremony, custom
  - Event visibility: school-wide, class-specific, role-specific (e.g., teachers-only)
  - Recurring events: weekly (e.g., club meetings), annual (holidays)
  - iCal feed: GET /calendar/ical?token= (signed token, no auth header needed)
- RSVP system — backend/app/services/rsvp.py
  - POST /events/{id}/rsvp (PAR, STD, TCH — body: { status: attending|declined|maybe })
  - GET /events/{id}/rsvp (own RSVP status)
  - GET /events/{id}/rsvps (ADM, DIR, event creator — list all RSVPs with counts)
  - RSVP deadline enforcement (optional, per event)
  - Capacity limit enforcement (optional, per event)
- Reminders — backend/app/services/reminders.py
  - Auto-reminders: 1 day before, 1 hour before (configurable per event)
  - Reminder delivery via notification hub (push + in-app)
  - Celery/ARQ periodic task: check upcoming events, send reminders
  - Reminder preferences: POST /events/reminder-preferences (opt-out per category)
- Database migrations:
  - events table (id, school_id, title_fr, title_ar, title_en, description, type, visibility, start_at, end_at, location, capacity, rsvp_deadline, recurrence_rule, created_by, is_all_day)
  - event_rsvps table (event_id, user_id, status, responded_at)
  - event_reminders table (event_id, remind_at, channel, sent)
  - moroccan_holidays seed data (pre-populated for current + next academic year)
- Pydantic schemas: schemas/calendar.py (event create/update, RSVP, reminder prefs)
- RBAC:
  - STD: view school-wide + own class events, RSVP
  - PAR: view school-wide + children class events, RSVP
  - TCH: view all + create class events, view RSVPs for own events
  - ADM/DIR: full CRUD, view all RSVPs, manage holidays
- Audit trail on event creation, modification, deletion

WEB FRONTEND (React):
- Calendar page — /calendar
  - Monthly calendar view (default) with event dots
  - Weekly view and list/agenda view toggle
  - Color-coded by event type (holiday=red, exam=orange, meeting=blue, custom=green)
  - Click date → day detail with events list
  - Click event → event detail modal (description, location, RSVP button, attendee count)
  - Create event button (ADM, DIR, TCH) → event form modal
  - Filter sidebar: event type checkboxes, class selector
- Event detail page — /events/{id}
  - Full description, location (with map link if coordinates provided), time
  - RSVP buttons: Attending / Maybe / Declined
  - Attendee list (for ADM/DIR/creator)
  - Edit/Delete buttons (for authorized roles)
  - Add to Google Calendar / Outlook / iCal download button
- iCal subscription link in settings
- i18n: all event types, labels, Moroccan holiday names in fr/ar/en

MOBILE (Flutter):
- Calendar screen
  - Month view with event indicators (dots under dates)
  - Day view: scrollable list of events
  - Pull-to-refresh
  - Tap event → detail bottom sheet
- Event detail screen
  - RSVP buttons with confirmation
  - Share event (system share sheet)
  - Add to device calendar (device_calendar package)
- Create event screen (ADM, DIR, TCH)
  - Form: title (fr/ar/en), type, date/time, location, visibility, capacity
  - Recurring event toggle with frequency picker
- Push notification for reminders (deep link to event)
- Offline: cache current month events in SQLite

ACCEPTANCE CRITERIA:
- [ ] Moroccan holidays pre-populated for current academic year
- [ ] Calendar renders correctly in month/week/list views
- [ ] Event creation with recurrence generates correct instances
- [ ] RSVP updates reflected in real-time (or within 5s)
- [ ] Capacity enforcement blocks RSVP when full
- [ ] Reminders sent at configured times via push + in-app
- [ ] iCal feed works with Google Calendar and Apple Calendar
- [ ] Events filtered correctly by role visibility
- [ ] Arabic event titles render correctly with RTL
- [ ] RBAC: students cannot create or delete events
- [ ] All new endpoints follow deny ordering (401 → 404 → 403)
- [ ] Integration tests for event CRUD, RSVP, reminders
- [ ] i18n complete for fr/ar/en

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Do Phase 15 ONLY. When done, stop and wait.
```

---

## Phase 16 — Document Management

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-15 are done. I need you to implement Phase 16.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 16 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/models/ for existing models (submission_files in lms.py)
- Read ecole-platform-dev/backend/app/core/config.py for storage configuration

PHASE 16 — Document Management:

BACKEND (FastAPI):
- File upload service — backend/app/services/file_storage.py
  - Pluggable storage backend: local filesystem (dev), S3-compatible (staging/prod)
  - Upload endpoint: POST /documents/upload (multipart/form-data)
    - Max file size: 50MB (configurable via env)
    - Allowed MIME types: PDF, DOCX, XLSX, PPTX, images (PNG, JPG, WEBP), ZIP
    - Virus scan hook (ClamAV integration point, optional)
    - File hash deduplication (SHA-256)
    - Thumbnail generation for images (Pillow, 200x200)
  - Download endpoint: GET /documents/{id}/download (signed URL, 1h expiry)
  - Preview endpoint: GET /documents/{id}/preview (thumbnail or first page for PDFs)
  - Delete endpoint: DELETE /documents/{id} (soft delete, ADM can hard delete)
  - List endpoint: GET /documents?category=&owner=&type= (cursor pagination)
- Student documents — backend/app/services/student_documents.py
  - Document categories: certificate, report_card, medical, identity, transcript, other
  - Link document to student: POST /students/{id}/documents (PAR, ADM)
  - List student documents: GET /students/{id}/documents (PAR for own children, TCH for assigned, ADM all)
  - Required documents checklist per school: GET /students/{id}/documents/checklist
  - Document expiry tracking (e.g., medical certificates): auto-notification 30 days before expiry
- Teacher resources library — backend/app/services/resource_library.py
  - Resource CRUD:
    - POST /resources (TCH, ADM — upload + metadata: subject, level, type, tags)
    - GET /resources?subject=&level=&type=&tags=&q= (full-text search, cursor pagination)
    - GET /resources/{id} (detail + download link)
    - PUT /resources/{id} (owner or ADM)
    - DELETE /resources/{id} (owner or ADM)
  - Resource types: lesson_plan, worksheet, presentation, exam_template, reference
  - Resource sharing: school-wide or class-specific visibility
  - Download count tracking
  - Resource rating: POST /resources/{id}/rate (TCH, 1-5 stars), GET /resources/{id}/rating
- Database migrations:
  - documents table (id, school_id, uploader_id, filename, original_filename, mime_type, size_bytes, sha256, storage_path, thumbnail_path, category, linked_student_id, expires_at, download_count, deleted_at)
  - resources table (id, school_id, uploader_id, title, description, subject, level, type, tags[], file_id FK→documents, visibility, download_count, avg_rating, rating_count)
  - resource_ratings table (resource_id, user_id, rating, created_at)
  - student_document_requirements table (school_id, category, required, description)
- Pydantic schemas: schemas/documents.py, schemas/resources.py
- RBAC:
  - STD: view own documents (read-only), view shared resources
  - PAR: upload/view documents for own children, view shared resources
  - TCH: upload/manage own resources, view student documents for assigned classes
  - ADM/DIR: full access to all documents and resources
- File storage metrics: upload_count, upload_size_bytes, storage_total_bytes (Prometheus)
- Audit trail on all upload, download, delete operations

WEB FRONTEND (React):
- Documents page — /documents
  - Tab layout: My Documents | Student Documents (PAR/TCH/ADM) | Resources Library
  - Upload zone: drag-and-drop area + file picker button
  - Upload progress bar with cancel button
  - File list: grid view (thumbnails) and list view toggle
  - File preview: images inline, PDFs in embedded viewer, others show icon + metadata
  - Filter/search bar: category, type, date range, full-text search
  - Bulk actions: select multiple → download ZIP, delete (ADM)
- Student documents section (PAR/TCH/ADM)
  - Student selector dropdown
  - Document checklist with status (uploaded, missing, expired)
  - Upload document → select category → link to student
  - Expiry warnings with yellow/red badges
- Resources library — /resources
  - Search with filters: subject, level, type, tags, rating
  - Resource cards: thumbnail, title, subject, level, rating stars, download count
  - Resource detail modal: preview, metadata, download button, rate (TCH)
  - Upload resource form: file + metadata (title, subject, level, type, tags)
- i18n: all labels, categories, document types in fr/ar/en

MOBILE (Flutter):
- Documents screen
  - Tab: My Documents | Student Documents | Resources
  - File upload from camera (photos) or file picker
  - Upload progress indicator
  - File list with thumbnails and metadata
  - Tap → preview (images inline, PDFs via pdf_render, others → share sheet)
- Student documents
  - Checklist view with status badges
  - Camera capture for scanning documents (image_picker)
  - Upload → category selection → link to student
- Resources library
  - Search and filter interface
  - Resource cards with ratings
  - Download for offline access (stored in app documents directory)
- Offline: cache document metadata in SQLite, downloaded files available offline

ACCEPTANCE CRITERIA:
- [ ] File upload works for all allowed MIME types up to 50MB
- [ ] Duplicate files detected by SHA-256 hash (no re-upload)
- [ ] Thumbnails generated for images within 2s
- [ ] Signed download URLs expire after 1h
- [ ] Student document checklist reflects school requirements
- [ ] Document expiry notifications sent 30 days before
- [ ] Resource search returns results within 500ms (full-text indexed)
- [ ] Resource ratings calculate correct average
- [ ] Drag-and-drop upload works on web
- [ ] Camera upload works on mobile (iOS + Android)
- [ ] RBAC: students cannot upload documents or delete others' files
- [ ] Storage metrics exposed on /metrics endpoint
- [ ] All new endpoints follow deny ordering (401 → 404 → 403)
- [ ] Integration tests for upload, download, search, RBAC
- [ ] i18n complete for fr/ar/en

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Do Phase 16 ONLY. When done, stop and wait.
```

---

## Phase 17 — Exam Management

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-16 are done. I need you to implement Phase 17.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 17 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/models/lms.py for assessments, grades, submissions
- Read ecole-platform-dev/backend/app/models/erp.py for classes, periods, enrollments
- Read ecole-platform-dev/backend/app/services/reports.py for PDF generation

PHASE 17 — Exam Management:

BACKEND (FastAPI):
- Exam scheduling — backend/app/services/exam_scheduling.py
  - Exam CRUD:
    - POST /exams (TCH, ADM — subject, class_ids[], date, start_time, duration_minutes, room, type)
    - GET /exams?period=&class_id=&subject=&status= (cursor pagination)
    - GET /exams/{id} (detail with enrolled students count)
    - PUT /exams/{id} (TCH owner, ADM)
    - DELETE /exams/{id} (ADM, soft delete)
  - Exam types: controle_continu, devoir_surveille, examen_regional, examen_national, rattrapage
  - Exam status lifecycle: draft → scheduled → in_progress → grading → published → archived
  - Conflict detection: POST /exams/check-conflicts (same class, overlapping time)
  - Exam calendar view: GET /exams/calendar?from=&to= (integrates with Phase 15 calendar)
  - Room assignment with capacity validation
  - Exam schedule publication: POST /exams/{id}/publish-schedule (notifies students + parents)
  - Proctor assignment: POST /exams/{id}/proctors (ADM — assign TCH to proctor)
- Grading workflow — backend/app/services/exam_grading.py
  - Grade entry:
    - POST /exams/{id}/grades (TCH — batch: [{ student_id, score, remarks }])
    - PUT /exams/{id}/grades/{student_id} (TCH — update individual grade)
    - GET /exams/{id}/grades (TCH, ADM — all grades for exam)
    - GET /exams/{id}/grades/{student_id} (STD own, PAR child, TCH, ADM)
  - Grading scale configuration per school: POST /grading-scales (ADM)
    - Moroccan standard: 0-20 scale, pass = 10
    - Custom scales: letter grades (A-F), percentage, competency-based
  - Grade validation rules:
    - Score within scale bounds
    - Double-entry verification option (two teachers grade, flag discrepancies > 2 points)
    - Grade modification after publication requires ADM approval
  - Grade statistics: GET /exams/{id}/stats (min, max, avg, median, std_dev, distribution histogram)
  - Weighted average calculation per subject per period (coefficient system per Moroccan curriculum)
- Result publication — backend/app/services/result_publication.py
  - Publish results: POST /exams/{id}/publish-results (TCH, ADM)
  - Publication triggers:
    - Notification to students + parents (via notification hub)
    - Results visible on student dashboard
    - PDF bulletin generation (integrates with Phase 14 reports)
  - Bulletin scolaire (report card):
    - Per-period: all subjects, scores, coefficients, weighted average, rank, teacher remarks
    - Annual: period averages, annual average, promotion decision
    - Conseil de classe remarks field
  - Result appeal: POST /exams/{id}/grades/{student_id}/appeal (PAR — reason text)
  - Appeal workflow: GET /appeals?status= (ADM), PUT /appeals/{id} (ADM — approve/reject with justification)
- Database migrations:
  - exams table (id, school_id, subject, class_ids[], type, status, date, start_time, duration_minutes, room, capacity, proctor_ids[], created_by, published_at)
  - exam_grades table (exam_id, student_id, score, max_score, coefficient, remarks, graded_by, verified_by, graded_at)
  - grading_scales table (school_id, name, type, scale_config JSONB, is_default)
  - grade_appeals table (exam_id, student_id, parent_id, reason, status, decision, decided_by, decided_at)
  - exam_proctors table (exam_id, teacher_id, assigned_by)
- Pydantic schemas: schemas/exams.py (exam CRUD, grade entry, appeal, grading scale)
- RBAC:
  - STD: view own exam schedule + own grades
  - PAR: view children exam schedule + grades, submit appeals
  - TCH: create exams for own subjects, grade own exams, view assigned class results
  - ADM/DIR: full access, manage grading scales, approve grade modifications, handle appeals
- Audit trail on grade entry, modification, publication, appeals

WEB FRONTEND (React):
- Exam management page — /exams
  - Calendar/list view of upcoming exams
  - Exam creation form (TCH, ADM): subject, classes, date/time, duration, room, type
  - Conflict detection warning before save
  - Exam detail page: schedule info, enrolled students, grading status
- Grading interface — /exams/{id}/grading (TCH)
  - Student roster table with score input fields
  - Batch entry: paste from spreadsheet (tab-separated)
  - Auto-save on blur (debounced 500ms)
  - Validation: red border if out of scale bounds
  - Statistics panel: live-updating min/max/avg/distribution chart
  - Submit for review / Publish results buttons
- Results view — /results (STD, PAR)
  - Period selector
  - Grades table: subject, exam type, score, max, coefficient, weighted
  - Period summary: weighted average, rank (if enabled), teacher remarks
  - Download bulletin PDF button
- Appeals management — /appeals (ADM)
  - List with status filters
  - Review form: original grade, appeal reason, decision, justification
- i18n: all exam types, grading terms, Moroccan curriculum vocabulary in fr/ar/en

MOBILE (Flutter):
- Exam schedule screen
  - Upcoming exams list with countdown (days/hours)
  - Exam detail: subject, date, time, duration, room
  - Add to device calendar button
  - Push notification reminders (1 day before, 1 hour before)
- Grading screen (TCH)
  - Student list with score entry
  - Numeric keypad optimized input
  - Submit grades with confirmation
- Results screen (STD, PAR)
  - Period grade cards with weighted averages
  - Tap subject → exam detail with score history
  - Download/share bulletin PDF
- Appeals screen (PAR)
  - Submit appeal form
  - Track appeal status
- Offline: cache exam schedule + grades in SQLite

ACCEPTANCE CRITERIA:
- [ ] Exam conflict detection catches overlapping schedules
- [ ] Grade entry validates against configured scale
- [ ] Weighted average calculates correctly with Moroccan coefficient system
- [ ] Double-entry verification flags discrepancies > threshold
- [ ] Result publication triggers notifications to all relevant users
- [ ] Bulletin PDF generates with correct data and formatting (fr/ar)
- [ ] Grade modification after publication requires ADM approval
- [ ] Appeal workflow completes end-to-end (submit → review → notify)
- [ ] Exam statistics compute correctly (min, max, avg, median, std_dev)
- [ ] RBAC: students cannot modify grades or access others' results
- [ ] All new endpoints follow deny ordering (401 → 404 → 403)
- [ ] Integration tests for exam CRUD, grading, publication, appeals
- [ ] i18n complete for fr/ar/en

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Do Phase 17 ONLY. When done, stop and wait.
```

---

## Phase 18 — Parent-Teacher Meetings

**Tool:** Claude Code
**Open folder:** `Ecole-Platform/` (the parent folder)

```md
I'm building "École Platform" — an EdTech SaaS for K-12 schools in Morocco.
This is a monorepo with FastAPI backend, React web, and Flutter mobile.
Phases 0-17 are done. I need you to implement Phase 18.

CONTEXT:
- Read ecole-platform-dev/DEV_PHASES_2.md for the full plan (Phase 18 section)
- Read ecole-platform-dev/TODO_GENERAL_2.md to see what's already done
- Read ecole-platform-dev/backend/app/models/ for user, class, enrollment models
- Read ecole-platform-dev/backend/app/services/notification_hub.py for notification integration
- Read ecole-platform-dev/backend/app/services/calendar.py for calendar integration

PHASE 18 — Parent-Teacher Meetings:

BACKEND (FastAPI):
- Meeting scheduling — backend/app/services/meetings.py
  - Teacher availability management:
    - POST /meetings/availability (TCH — set available time slots: day, start_time, end_time, slot_duration_minutes)
    - GET /meetings/availability?teacher_id=&date= (PAR — view available slots)
    - DELETE /meetings/availability/{id} (TCH — remove slot)
  - Meeting booking:
    - POST /meetings/book (PAR — teacher_id, slot_datetime, student_id, topic)
    - GET /meetings?status=&from=&to= (all roles, filtered by involvement)
    - GET /meetings/{id} (detail with video link if applicable)
    - PUT /meetings/{id} (reschedule — TCH or PAR, notifies other party)
    - DELETE /meetings/{id}/cancel (TCH or PAR, requires reason, notifies other party)
  - Meeting types: in_person, video_call
  - Slot duration: configurable per teacher (default 15min)
  - Buffer time between meetings: configurable (default 5min)
  - Max meetings per day per teacher: configurable (default 8)
  - Auto-confirmation vs manual approval (school-level setting)
  - Meeting status lifecycle: requested → confirmed → in_progress → completed → cancelled
  - Bulk scheduling for parent-teacher conference days:
    - POST /meetings/conference (ADM — date, teachers[], slot_duration, start_time, end_time)
    - Auto-generates availability slots for all specified teachers
- Video call integration — backend/app/services/video_calls.py
  - Jitsi Meet integration (self-hosted or jitsi.org):
    - Generate unique room URL per meeting
    - JWT token for room authentication (optional, for security)
    - Room auto-created on meeting start, destroyed after end + 10min grace
  - Alternative: generic video link field (teacher pastes Zoom/Google Meet link)
  - Video link included in meeting confirmation notification
  - Meeting join endpoint: GET /meetings/{id}/join (redirects to video URL, logs join time)
- Meeting notes — backend/app/services/meeting_notes.py
  - POST /meetings/{id}/notes (TCH — markdown text, action_items[], follow_up_date)
  - GET /meetings/{id}/notes (TCH who wrote, PAR involved, ADM)
  - PUT /meetings/{id}/notes (TCH — update until 48h after meeting)
  - Notes visibility: teacher writes, parent can view (not edit)
  - Action items tracking:
    - Each action item: description, assigned_to (PAR or TCH), due_date, status (pending/done)
    - GET /meetings/action-items?status=&assigned_to= (filter own action items)
    - PUT /meetings/action-items/{id} (mark as done)
  - Follow-up reminders via notification hub
- Database migrations:
  - teacher_availability table (id, teacher_id, school_id, day_of_week, start_time, end_time, slot_duration_minutes, buffer_minutes, is_recurring, specific_date)
  - meetings table (id, school_id, teacher_id, parent_id, student_id, type, status, scheduled_at, duration_minutes, topic, video_url, location, cancelled_reason, completed_at)
  - meeting_notes table (meeting_id, author_id, content_md, follow_up_date, created_at, updated_at)
  - meeting_action_items table (id, meeting_id, description, assigned_to_id, due_date, status, completed_at)
  - school_meeting_settings table (school_id, auto_confirm, default_slot_duration, default_buffer, max_daily_meetings)
- Pydantic schemas: schemas/meetings.py (availability, booking, notes, action items)
- RBAC:
  - STD: no direct access (meetings are between parents and teachers)
  - PAR: book meetings, view own meetings + notes, manage own action items
  - TCH: manage availability, view own meetings, write notes, manage action items
  - ADM/DIR: view all meetings, configure settings, bulk scheduling, manage conflicts
- Notifications:
  - Meeting booked → notify TCH (or PAR if TCH-initiated)
  - Meeting confirmed → notify both parties
  - Meeting reminder: 1 day before + 1 hour before
  - Meeting cancelled → notify other party with reason
  - Notes shared → notify PAR
  - Action item due → remind assigned person
- Audit trail on booking, cancellation, note creation

WEB FRONTEND (React):
- Meetings page — /meetings
  - Tab layout: Upcoming | Past | Action Items
  - Upcoming: list with date, teacher/parent name, topic, status, join button (if video)
  - Past: list with notes indicator, action items count
  - Action items: checklist view with due dates and status toggles
- Book meeting flow — /meetings/book
  - Step 1: Select teacher (from child's assigned teachers)
  - Step 2: Select date (calendar picker, shows available dates)
  - Step 3: Select time slot (available slots highlighted)
  - Step 4: Enter topic + select type (in-person/video)
  - Step 5: Confirm → notification sent
- Teacher availability management — /meetings/availability (TCH)
  - Weekly grid: drag to set available slots
  - Recurring vs one-time toggle
  - Slot duration and buffer configuration
  - Conference day mode: bulk slot creation
- Meeting detail — /meetings/{id}
  - Meeting info: date, time, teacher/parent, student, topic
  - Video call: "Join Meeting" button (disabled until 5min before start)
  - Notes section (TCH: edit, PAR: read-only)
  - Action items list with checkboxes
- Admin settings — /settings/meetings (ADM)
  - Auto-confirm toggle
  - Default slot duration and buffer
  - Max daily meetings
- i18n: all meeting terms, status labels in fr/ar/en

MOBILE (Flutter):
- Meetings screen
  - Upcoming meetings list with countdown
  - Tap → meeting detail
  - "Join Video Call" button (opens Jitsi/external app)
- Book meeting flow
  - Teacher selector → date picker → slot picker → topic → confirm
  - Streamlined 3-step flow with bottom sheet transitions
- Teacher availability screen (TCH)
  - Weekly slot editor
  - Tap day → set start/end times
- Meeting detail screen
  - Meeting info + status badge
  - Notes section (scrollable, markdown rendered)
  - Action items with tap-to-complete
- Push notifications for reminders, confirmations, cancellations
- Offline: cache upcoming meetings, action items in SQLite

ACCEPTANCE CRITERIA:
- [ ] Teacher can set recurring availability slots
- [ ] Parent can view only available (unbooked) slots
- [ ] Booking prevents double-booking (optimistic locking)
- [ ] Buffer time enforced between consecutive meetings
- [ ] Video call link generated and accessible from meeting detail
- [ ] Meeting notes editable by teacher up to 48h post-meeting
- [ ] Action items trackable by both parties
- [ ] Reminders sent at configured times (1 day, 1 hour before)
- [ ] Cancellation requires reason and notifies other party
- [ ] Conference day bulk scheduling works for 10+ teachers
- [ ] RBAC: students cannot book or view meeting notes
- [ ] All new endpoints follow deny ordering (401 → 404 → 403)
- [ ] Integration tests for booking flow, conflict detection, notes
- [ ] i18n complete for fr/ar/en

IMPORTANT RULES:
- NEVER run git commit, git push, or any git write command. You can run git status or git diff.
- After finishing, suggest the exact git add + git commit commands I should run manually in my terminal.
- After each completed step, update ecole-platform-dev/TODO_GENERAL_2.md to mark items as done.
- Do Phase 18 ONLY. When done, stop and wait.
```
