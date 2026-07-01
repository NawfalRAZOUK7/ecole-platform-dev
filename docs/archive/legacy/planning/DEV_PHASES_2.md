# École Platform — Development Phases Guide (Phases 13-18)

> This file continues the roadmap from DEV_PHASES.md (Phases 0-12).
> Each phase has a clear goal, the subfolders you work in, and what "done" looks like.
> Open a new Claude Code session per phase, focused on the relevant subfolder.

---

## Phase Overview

| Phase | Name | Estimated Complexity | Duration | Dependencies |
|-------|------|---------------------|----------|--------------|
| 13 | Notifications Center | Medium | ~3-4 days | Phase 8 (COM domain), Phase 5 (mobile push) |
| 14 | Reports & Analytics | High | ~5-7 days | Phase 3 (all domain APIs), Phase 8 (KPI service) |
| 15 | Calendar & Events | Medium | ~3-4 days | Phase 3 (ERP domain), Phase 13 (notification hub) |
| 16 | Document Management | High | ~4-6 days | Phase 3 (LMS domain), Phase 0 (infra/storage) |
| 17 | Exam Management | High | ~5-7 days | Phase 3 (LMS grades), Phase 14 (PDF reports), Phase 15 (calendar) |
| 18 | Parent-Teacher Meetings | Medium | ~3-5 days | Phase 13 (notifications), Phase 15 (calendar) |

**Total estimated: 23-33 days**

---

## Architecture Considerations (Cross-Phase)

### Caching Strategy
- **Redis** for all short-lived cache (unread counts, dashboard KPIs, analytics queries)
- TTL policies: unread count 30s, analytics 5min, report status 10s, calendar events 2min
- Cache invalidation: event-driven via service layer (not TTL-only for critical data)
- Cache key namespacing: `ecole:{school_id}:{domain}:{resource}:{id}`

### File Storage
- **Local filesystem** for development (`/app/storage/` volume mount)
- **S3-compatible** for staging/production (MinIO for self-hosted, AWS S3 for cloud)
- Signed URLs for downloads (1h expiry, single-use option for sensitive documents)
- Storage abstraction layer: `FileStorageBackend` protocol with `LocalStorage` and `S3Storage` implementations
- File size limits enforced at Nginx (client_max_body_size) and application level
- Virus scanning: ClamAV integration point (optional, enabled via env flag)

### Real-Time Events
- **Server-Sent Events (SSE)** for web real-time updates (notification count, meeting status)
- Endpoint: GET /events/stream (authenticated, per-user filtered)
- Redis Pub/Sub as event bus between backend instances
- Events: `notification.new`, `meeting.updated`, `grade.published`, `document.uploaded`
- Mobile: push notifications for real-time (no SSE needed)
- Fallback: polling every 60s if SSE connection drops

### Background Tasks
- **ARQ** (async Redis queue) for background jobs
- Job types: report generation, email digest, reminder dispatch, file processing, cleanup
- Job status tracking in Redis with TTL (24h)
- Dead letter queue for failed jobs (max 3 retries)
- Scheduled tasks: digest (daily 07:00), cleanup (daily 03:00), reminders (every 5min check)

### Database Considerations
- New tables add ~10 migrations (one per domain extension)
- Full-text search: PostgreSQL `tsvector` + GIN indexes for documents and resources
- JSONB columns for flexible metadata (event recurrence rules, grading scale config)
- Partitioning consideration for exam_grades if volume exceeds 1M rows/year

---

## Phase 13 — Notifications Center *(~3-4 days)*
**Subfolders:** `backend/` + `web/` + `mobile/`
**Goal:** Unified notification hub with in-app, push, and email digest channels.

### Description
Replace the basic notification system from Phase 3 with a full notification center. Users can configure per-channel per-category preferences. Push notifications are properly tracked with delivery status. Email digests aggregate unread notifications on a daily/weekly schedule.

### Backend Tasks
1. Notification hub service with channel routing engine
2. Notification preferences CRUD (per user, per channel, per category)
3. Device token registration/deregistration endpoints
4. FCM server-side send via firebase-admin SDK
5. Push delivery tracking (sent, delivered, failed, clicked)
6. Email digest service with Jinja2 templates (fr/ar/en)
7. Celery/ARQ task for scheduled digest generation
8. Unread count endpoint with Redis caching (30s TTL)
9. Mark as read/unread, mark-all-read endpoints
10. Batch notification creation endpoint (ADM, SYS)
11. Database migrations: notification_preferences, device_tokens tables
12. SMTP integration with environment-based configuration
13. Unsubscribe endpoint with signed token

### Web Frontend Tasks
1. Redesigned notification center page with filters
2. Bell icon with unread badge in header (polling or SSE)
3. Dropdown quick-view (last 5 unread)
4. Notification preferences settings page
5. Device management panel
6. Mark all as read functionality
7. Deep link navigation from notification click

### Mobile Tasks
1. Redesigned notification center screen with category chips
2. Swipe actions (mark read, delete)
3. Push notification handling improvements (foreground banner)
4. Token refresh and backend registration on app start
5. Notification preferences screen
6. Offline cache (last 100 notifications in SQLite)

### Testing Requirements
- Integration tests: notification creation, channel routing, preferences
- Push delivery mock tests (firebase-admin mock)
- Email digest template rendering tests (fr/ar/en)
- RBAC tests: all notification endpoints x all roles
- Load test: 1000 batch notifications within 10s

### Deployment Notes
- Requires `firebase-admin` Python package + Firebase service account JSON
- SMTP credentials in environment variables
- New Celery/ARQ beat schedule for digest task
- Redis Pub/Sub channel for real-time notification events

### Done when:
- [ ] Notification preferences persist and route correctly
- [ ] Push notifications delivered within 5s
- [ ] Email digest sent at configured time
- [ ] Unread badge updates within 2s
- [ ] All tests passing

---

## Phase 14 — Reports & Analytics *(~5-7 days)*
**Subfolders:** `backend/` + `web/` + `mobile/`
**Goal:** PDF report generation, data export, and admin analytics dashboard.

### Description
Enable school administrators and teachers to generate PDF reports (student report cards, class summaries, attendance reports, billing statements). Provide exportable data in CSV/XLSX formats. Build an analytics dashboard with KPI cards, trend charts, and comparison periods.

### Backend Tasks
1. PDF generation service (WeasyPrint: HTML/CSS → PDF)
2. Report templates in Jinja2 (report card, class summary, attendance, billing, school analytics)
3. Bilingual PDF support (fr/ar with RTL)
4. Async report generation via ARQ (POST /reports/generate → job_id)
5. Report status tracking and download with signed URL
6. CSV streaming export (no full dataset in memory)
7. XLSX export via openpyxl
8. Export size limits and pagination
9. Analytics API endpoints: overview, attendance trends, grade distributions, billing, engagement
10. Redis caching for analytics queries (5min TTL)
11. Date range filtering with comparison periods
12. Database migrations: report_jobs, data_exports tables
13. Report file cleanup task (expire after 24h)
14. Prometheus metrics: report_generation_count, report_generation_duration_seconds

### Web Frontend Tasks
1. Reports page with type selector and parameter form
2. Generate → progress indicator → download flow
3. Report history table
4. Analytics dashboard (ADM/DIR): KPI cards, trend charts, distribution charts
5. Chart library integration (recharts or chart.js)
6. Date range picker with presets and comparison mode
7. Export buttons (PNG chart, CSV/XLSX data)

### Mobile Tasks
1. Reports screen with role-filtered report types
2. Generate → push notification → download/share flow
3. PDF viewer integration (share sheet)
4. Analytics summary screen (ADM/DIR) with sparklines
5. Offline cache for last 5 generated reports

### Testing Requirements
- PDF generation tests: verify output is valid PDF, correct data, RTL rendering
- Export tests: CSV field accuracy, XLSX formatting
- Analytics query accuracy tests (compare with raw SQL)
- RBAC tests: all report/analytics endpoints x all roles
- Performance test: report generation <30s for 40-student class

### Deployment Notes
- Requires `weasyprint` system dependencies (libpango, libcairo)
- Add to Dockerfile: `apt-get install -y libpango-1.0-0 libcairo2`
- Arabic font package: `fonts-noto-core` for proper RTL PDF rendering
- ARQ worker needs sufficient memory for PDF generation (~256MB per concurrent report)

### Done when:
- [ ] PDF reports generate correctly in fr and ar
- [ ] CSV/XLSX exports stream without memory issues
- [ ] Analytics dashboard loads within 2s
- [ ] All tests passing

---

## Phase 15 — Calendar & Events *(~3-4 days)*
**Subfolders:** `backend/` + `web/` + `mobile/`
**Goal:** School calendar with events, RSVP, reminders, and iCal feed.

### Description
Provide a school calendar pre-populated with Moroccan holidays and academic periods. Teachers and administrators can create events (exams, meetings, excursions). Parents and students can RSVP. Automatic reminders are sent via the notification hub. An iCal feed enables subscription from external calendar apps.

### Backend Tasks
1. Calendar service with Moroccan holiday seed data
2. Event CRUD endpoints with type and visibility controls
3. Recurring event support (weekly, annual)
4. RSVP system with capacity enforcement
5. Reminder service with configurable timing (ARQ periodic task)
6. iCal feed generation with signed token authentication
7. Calendar integration with Phase 15 exam schedule
8. Database migrations: events, event_rsvps, event_reminders, moroccan_holidays tables
9. Event visibility filtering by role and class membership

### Web Frontend Tasks
1. Calendar page with month/week/list views
2. Color-coded events by type
3. Event creation form (modal)
4. Event detail with RSVP and attendee list
5. Add to external calendar buttons (Google, Outlook, iCal)
6. Filter sidebar (type, class)

### Mobile Tasks
1. Calendar screen with month + day views
2. Event detail bottom sheet with RSVP
3. Add to device calendar integration
4. Push notification reminders
5. Offline cache for current month events

### Testing Requirements
- Event CRUD integration tests
- RSVP capacity enforcement tests
- Recurring event generation correctness tests
- Reminder dispatch timing tests
- iCal feed validation (RFC 5545 compliance)
- RBAC tests: event endpoints x all roles

### Deployment Notes
- Moroccan holiday data needs annual update (seed script with year parameter)
- ARQ beat task for reminder checks (every 5min)
- iCal endpoint bypasses JWT auth (uses signed token in URL)

### Done when:
- [ ] Moroccan holidays display on calendar
- [ ] Events create/edit/delete correctly
- [ ] RSVP with capacity works
- [ ] Reminders sent on time
- [ ] iCal feed subscribable
- [ ] All tests passing

---

## Phase 16 — Document Management *(~4-6 days)*
**Subfolders:** `backend/` + `web/` + `mobile/` + `infra/`
**Goal:** File upload/download system, student document tracking, teacher resource library.

### Description
Implement a document management system with pluggable storage backends (local dev, S3 production). Support student administrative documents (certificates, medical records) with expiry tracking and checklist management. Build a teacher resource library with search, tagging, and ratings.

### Backend Tasks
1. Pluggable file storage service (LocalStorage + S3Storage)
2. Upload endpoint with MIME validation, size limits, SHA-256 dedup
3. Thumbnail generation for images (Pillow)
4. Signed URL download endpoint
5. Student document CRUD with category and expiry
6. Document checklist per school (required documents configuration)
7. Document expiry notification (30 days before)
8. Teacher resource library CRUD with full-text search (tsvector)
9. Resource rating system
10. Database migrations: documents, resources, resource_ratings, student_document_requirements tables
11. Storage metrics (Prometheus)
12. Virus scan integration point (ClamAV, optional)
13. File cleanup task for soft-deleted files (30 days retention)

### Web Frontend Tasks
1. Documents page with tabs (My Documents, Student Documents, Resources)
2. Drag-and-drop upload zone with progress
3. File grid/list view toggle with thumbnails
4. Inline preview (images, PDFs)
5. Student document checklist with status badges
6. Resources library with search, filters, rating stars
7. Bulk actions (download ZIP, delete)

### Mobile Tasks
1. Documents screen with tab layout
2. Camera capture for document scanning
3. File picker upload with progress
4. File preview (images, PDFs via pdf_render)
5. Resource library with search
6. Offline: downloaded files available offline

### Testing Requirements
- Upload/download integration tests (all MIME types)
- SHA-256 dedup verification tests
- Full-text search accuracy tests
- Resource rating calculation tests
- RBAC tests: document endpoints x all roles
- Storage backend tests (local + S3 mock)

### Deployment Notes
- Development: Docker volume mount for local storage
- Production: S3 bucket with lifecycle rules (archive after 1 year)
- MinIO container for staging S3-compatible storage
- `Pillow` for thumbnail generation, `python-magic` for MIME detection
- Nginx: `client_max_body_size 50m` for uploads
- ClamAV container (optional): add to docker-compose if enabled

### Done when:
- [ ] Upload works for all allowed types up to 50MB
- [ ] Dedup prevents re-upload of identical files
- [ ] Student document checklist reflects requirements
- [ ] Resource search returns results <500ms
- [ ] All tests passing

---

## Phase 17 — Exam Management *(~5-7 days)*
**Subfolders:** `backend/` + `web/` + `mobile/`
**Goal:** Exam scheduling, grading workflows, result publication with Moroccan curriculum support.

### Description
Full exam lifecycle management aligned with the Moroccan education system (0-20 grading scale, coefficient-weighted averages, controle continu / devoir surveille / examen regional / examen national). Includes conflict detection, grading workflows with double-entry verification, bulletin scolaire generation, and grade appeal process.

### Backend Tasks
1. Exam CRUD with status lifecycle (draft → scheduled → in_progress → grading → published → archived)
2. Exam types aligned with Moroccan curriculum
3. Conflict detection (same class, overlapping time)
4. Room and proctor assignment
5. Grading scale configuration (0-20 default, custom scales)
6. Grade entry with batch support and validation
7. Double-entry verification option (flag discrepancies)
8. Grade statistics computation (min, max, avg, median, std_dev, distribution)
9. Weighted average calculation (coefficient system)
10. Result publication with notification triggers
11. Bulletin scolaire PDF generation (per-period and annual)
12. Grade appeal workflow (submit → review → decide → notify)
13. Database migrations: exams, exam_grades, grading_scales, grade_appeals, exam_proctors tables
14. Calendar integration (exams appear on Phase 15 calendar)
15. Post-publication grade modification approval flow

### Web Frontend Tasks
1. Exam management page (calendar + list views)
2. Exam creation form with conflict detection
3. Grading interface with student roster and batch entry
4. Live statistics panel during grading
5. Results view with period summary, weighted averages, rank
6. Bulletin PDF download
7. Appeals management page (ADM)

### Mobile Tasks
1. Exam schedule screen with countdown
2. Grading screen (TCH) with numeric keypad
3. Results screen with grade cards
4. Bulletin download/share
5. Appeal submission (PAR)
6. Offline cache for exam schedule + grades

### Testing Requirements
- Exam conflict detection tests
- Grading scale validation tests
- Weighted average calculation accuracy tests (verify with manual computation)
- Double-entry discrepancy detection tests
- Result publication notification tests
- Appeal workflow end-to-end tests
- Bulletin PDF content verification tests
- RBAC tests: exam endpoints x all roles

### Deployment Notes
- Depends on Phase 14 (PDF generation infrastructure)
- Grading scale seed data for Moroccan standard (0-20)
- Coefficient data per subject per level (configurable per school)
- Heavy computation during grade statistics — consider async for large classes

### Done when:
- [ ] Exam lifecycle works end-to-end
- [ ] Grades validated against scale
- [ ] Weighted averages correct per Moroccan system
- [ ] Bulletin PDF generates correctly (fr/ar)
- [ ] Appeals workflow completes
- [ ] All tests passing

---

## Phase 18 — Parent-Teacher Meetings *(~3-5 days)*
**Subfolders:** `backend/` + `web/` + `mobile/`
**Goal:** Meeting scheduling with availability management, video call integration, and meeting notes.

### Description
Enable parents to book meetings with teachers through an availability-slot system. Support both in-person and video meetings (Jitsi Meet integration). Teachers write meeting notes with action items tracked by both parties. Administrators can set up conference days with bulk scheduling.

### Backend Tasks
1. Teacher availability management (recurring + one-time slots)
2. Meeting booking with double-booking prevention (optimistic locking)
3. Buffer time and daily limit enforcement
4. Meeting status lifecycle (requested → confirmed → in_progress → completed → cancelled)
5. Jitsi Meet room generation with JWT authentication
6. Meeting notes CRUD (teacher writes, parent reads)
7. Action items tracking with status and due dates
8. Follow-up reminders via notification hub
9. Bulk conference day scheduling (ADM)
10. School-level meeting settings (auto-confirm, slot duration, buffer, max daily)
11. Database migrations: teacher_availability, meetings, meeting_notes, meeting_action_items, school_meeting_settings tables
12. Cancellation with reason requirement and notification

### Web Frontend Tasks
1. Meetings page with tabs (Upcoming, Past, Action Items)
2. Multi-step booking flow (teacher → date → slot → topic → confirm)
3. Teacher availability grid editor (TCH)
4. Meeting detail page with video join button
5. Notes section (TCH editable, PAR read-only)
6. Action items checklist with due dates
7. Admin meeting settings page

### Mobile Tasks
1. Meetings screen with upcoming/past tabs
2. Streamlined booking flow (bottom sheet steps)
3. Video call join (open Jitsi/external app)
4. Meeting detail with notes and action items
5. Teacher availability editor
6. Push notifications for reminders and status changes
7. Offline cache for upcoming meetings and action items

### Testing Requirements
- Availability slot management tests
- Double-booking prevention tests (concurrent booking simulation)
- Buffer time and daily limit enforcement tests
- Jitsi room URL generation tests
- Meeting notes visibility tests (TCH write, PAR read)
- Action item lifecycle tests
- Cancellation notification tests
- RBAC tests: meeting endpoints x all roles

### Deployment Notes
- Jitsi Meet: self-hosted container or jitsi.org public (configurable via env)
- `PyJWT` for Jitsi room tokens (if self-hosted with JWT auth)
- Notification hub dependency (Phase 13 must be complete)
- Meeting reminders via ARQ periodic task (integrates with Phase 15 reminders)

### Done when:
- [ ] Teachers can set and manage availability
- [ ] Parents can book available slots
- [ ] Double-booking prevented
- [ ] Video call accessible from meeting detail
- [ ] Notes and action items tracked
- [ ] Reminders sent on time
- [ ] All tests passing

---

## Summary: What Subfolder to Open Per Phase

| Phase | Primary Subfolder | Secondary |
|-------|-------------------|-----------|
| 13 | `backend/` (services, api, models) | `web/`, `mobile/` |
| 14 | `backend/` (services, api) | `web/`, `mobile/`, `infra/` (fonts) |
| 15 | `backend/` (services, api, models) | `web/`, `mobile/` |
| 16 | `backend/` (services, api, models) | `web/`, `mobile/`, `infra/` (storage) |
| 17 | `backend/` (services, api, models) | `web/`, `mobile/` |
| 18 | `backend/` (services, api, models) | `web/`, `mobile/`, `infra/` (Jitsi) |

---

## Recommended Session Strategy

**Phase 13 = full-stack session** (notification hub touches backend + web + mobile)

**Phase 14 = backend-first, then frontend** (PDF + analytics backend, then dashboard UI)

**Phase 15-16 = full-stack sessions** (each is a self-contained feature)

**Phase 17 = backend-heavy** (grading logic is complex, then UI for grading interface)

**Phase 18 = full-stack session** (scheduling + video + notes across all platforms)
