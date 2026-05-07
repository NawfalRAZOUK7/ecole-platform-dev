# Changelog

All notable changes to École Platform are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.1.0] — 2026-05-06

### 🚀 Production Hardening, Academic Programs, Bilingual Billing, K8s-First Deployment

Major release focused on production readiness, regulatory compliance (Moroccan TVA + MEN), object-storage migration, and a substantial mobile feature expansion. All items below were added or substantially reworked since `1.0.0`.

### Added

#### Object Storage & Large-File Uploads (MinIO / S3)
- Unified storage abstraction with pluggable S3-compatible backend (`local`, `minio`, `s3`)
- MinIO development stack added to `infra/docker-compose.dev.yml`
- Direct large-file uploads on web and mobile (multipart, resumable up to 50 MB)
- Presigned download redirects for authenticated content access
- ClamAV virus-scanning pipeline with retry logic on upload completion
- Prometheus metrics for virus scan results (`virus_scan_total`, `virus_scan_duration_seconds`)
- Migration script `scripts/migrate_local_uploads_to_minio.py` for cutover
- Operational runbook (`infra/MINIO_RUNBOOK.md`) and conformance review

#### Academic Programs Lifecycle (G49–G50)
- New domain modules: `Program`, `ProgramVersion`, `ProgramEquivalence`, `ProgramSnapshot`, `EligibilityRule`, `Enrollment`
- Eligibility check engine (rules-based, age + level + prerequisite + custom predicates)
- Program assignment workflow with snapshot persistence (audit-grade history)
- Web admin UI: `ProgramsPage`, `ProgramVersionsPage`, `ProgramEquivalencesPage`, `EnrollmentsPage`, `EligibilityRulesPage`, `AssignProgramDialog`, `EligibilityCheckTile`, `StudentAcademicHistoryPage`
- Mobile student academic history view with timeline of enrollments and equivalences
- 2 Alembic migrations (G49, G50) covering all program-related tables

#### Bilingual Invoicing & Moroccan Tax Compliance (Phases 1–7)
- WeasyPrint-based PDF generation for invoices and payment receipts
- Bilingual templates: Arabic (RTL) and French (LTR), with shared CSS partials
- TVA breakdown fields on `InvoiceItem` (`tva_rate`, `tva_amount`, `tva_base`)
- Banking and branding fields on `School` (`bank_name`, `bank_iban`, `bank_swift`, `bank_rib`, `brand_logo_url`, `brand_color`, `legal_ice`, `legal_rc`)
- New endpoints: `GET /invoices/{id}/pdf`, `GET /payments/{id}/receipt`, with role-aware access checks
- QR-code embedding on receipts (`qrcode==7.4.2`)
- Integration tests for PDF generation, content-disposition, and Arabic font rendering

#### Phase A — Student Writing Workspace
- New `WritingWorkspacePage` (web) and `features/writing` module (mobile)
- Backend service `WritingService` with auto-save, draft history, and word-count tracking
- Integration with rewards (writing completion grants stars + XP via `RewardEvent`)

#### Phase B — Parent Shared Review
- `SharedReviewService` exposing parent-readable summaries of child sessions
- `SharedReviewPage` and `ReviewDetailPage` (web), with comment thread per review
- `ParentAlertService` for proactive alerts (struggling sessions, missed deadlines, achievements)
- Trilingual notification templates

#### Phase D — Kubernetes Production Deployment
- Helm chart matured to 15 templates with values overlays (`values-local`, `values-staging`, `values-prod`)
- Local `Kind` cluster setup script (`scripts/k8s-local-up.sh`) creating `ecole-dev` cluster
- K8s end-to-end testing workflow (`.github/workflows/k8s-e2e.yml`)
- Helm `lint` + `template` validation steps in CI
- Blue-green compose configurations (`docker-compose.blue.yml`, `docker-compose.green.yml`) for non-K8s rollouts
- Enhanced kubeconfig setup script with error handling and validation
- Documentation: `docs/KUBERNETES_SETUP.md`

#### Phase E — Cross-Platform Kid-Facing UX
- E1: Level-to-age mapping and automatic age-filtering of student content
- E2: `longest_streak` tracking on `StudentReward` with backfill migration
- E3: Web reward payload field-name alignment with mobile contract
- E4: Cairo font (Arabic-optimized) bundled and applied on web for AR locale
- E5: Kid-friendly color system on web (matches mobile `KidsContentColors`)
- E6: Shimmer loading skeletons on all kid-facing screens
- E7: Branded splash screen on mobile (Android + iOS)
- E8: Shared web design tokens matching mobile theme tokens (light + dark)
- E9: Kid-friendly empty states with mascot illustrations on all new screens
- E10: Offline content caching on mobile (TTL 7 days for downloaded content)

#### Mobile Expansion
- Rubrics module: list, editor, grading flows
- Question bank module: list, import (CSV/JSON), quiz generation
- Quiz analytics: attempts listing with score distribution
- Class progress screen with localization
- Parent absence justification with file attachments
- My Children page (parent overview)
- Skills passport mobile: radar overview, passport export, evaluation, analytics
- Compliance module mobile: dashboard, curriculum mapping, reports
- Financial health module: dashboard, snapshots, export
- Micro-budgets module: envelopes, allocations, requests with MAD currency formatting
- Micro-schools module: CRUD, enrollments, resources, progress tracking
- Attendance module: history heatmap, analytics charts, offline cache
- Gradebook module: grade grid, student detail, transcript with 0–20 Moroccan scale
- Sync infrastructure v2: status indicator, conflict resolution UI, shell-level offline indicator
- Recovery flows, privacy settings, scheduled report subscriptions
- Native Android and iOS platform initialization (Gradle 8, Swift 5.9)
- Accessibility: `Semantics` annotations on 30+ feature screens (50+ annotations total)
- Theme refactor: 278 hardcoded colors replaced with theme tokens (dark-mode safe)
- Test infrastructure: pump helpers, mock repositories, entity factories

#### Backend Depth & Auth
- New permissions: `PERM_LMS_ASSIGNMENT_READ`, `PERM_LMS_ACTIVITY_READ`, skill dimension and milestone permissions
- Refactored role redirection logic into a dedicated `auth/role_redirect.py` module
- Access token extraction from query parameters (enables signed-URL JWT flow)
- Improved login error handling and trilingual error translations
- Reward badge management endpoints (CRUD) with admin-only role gate
- Reward badge seeding script for default badge catalog

#### Timetable Enhancements
- New constraint type `max_consecutive_classes` with validator
- Academic year support on timetable constraints
- Generation preview (dry-run) endpoint before committing a generated timetable

#### Testing & Coverage
- 18 new mobile test files (30+ unit/widget tests, 2 integration tests)
- Web tests for all new features: `PlatformBridgeCard`, `LevelBadge`, `RewardsService`, `StreakCard`, `StudentHomePage`, `EmptyState`, `LoadingState`, `StatCard`, `useSignedUrl`, `directUpload`, programs/enrollments/eligibility pages
- Backend integration tests for invoice PDF and payment receipt endpoints
- E2E spec for student submission flow with new content types
- Web endpoint coverage raised to **97.7%** (was ~95%): 25 missing API service methods added, 13 HTTP method mismatches fixed

#### Documentation
- New `docs/MINIO_INTEGRATION_ARCHITECTURE.md` and `docs/MINIO_ROLLOUT.md`
- New `docs/PAYMENT_DOCUMENTATION.md` (full Moroccan compliance implementation guide)
- New `docs/clamav-setup.md`
- Refreshed `docs/ARCHITECTURE.md`, `docs/API-REFERENCE.md`, `docs/DATABASE.md`, `docs/DEPLOYMENT.md`, `docs/TESTING.md`, `docs/SECURITY.md`, `docs/CROSS-PLATFORM.md`

### Changed
- Document storage backend unified behind a single abstraction (callers no longer differentiate local vs S3)
- Submission max-file-size message updated to 50 MB
- Web invoices and notifications prefetching switched to infinite query with cursor pagination
- Backend Dockerfile and deployment configuration tuned for K8s (non-root user, distroless final stage)
- Docker images bumped to Node 22-alpine for web build stage
- `formatDate` enhanced with granular options and error handling

### Fixed
- Auth: avoid 500 on invalid school login
- CI: migration safety failures, security gate, OpenAPI snapshot drift, e2e server mode, GHCR tags, lint gate, docs workflow
- Mobile: PDF render Android Gradle compatibility
- Difficulty adapter: quiz attempt status filter corrected from `GRADED` to `COMPLETED`
- Rewards: error handling in `useRewardChildren` query function

### Removed
- Demo seeding script and related fixtures (replaced by environment-driven seeding)
- Obsolete local-upload Docker volume

---

## [1.0.0] — 2026-04-26

### 🎉 Initial Release — Full Platform

Complete K-12 EdTech SaaS platform with backend API, web frontend, mobile app, and production infrastructure.

### Added

#### Core Platform
- FastAPI backend with 57 API endpoint modules covering IAM, ERP, LMS, Communication, Billing, and Audit
- PostgreSQL 16 database with 23 model modules and 56 Alembic async migrations
- Redis 7 integration for sessions, rate limiting, and async task queue
- JWT authentication with refresh tokens and optional 2FA/TOTP support
- RBAC authorization with 5 roles (ADM, DIR, TCH, PAR, STD) and granular permissions
- Cursor-based pagination across all list endpoints
- Structured error responses with categorized error codes

#### Web Frontend (React)
- React 18 SPA with TypeScript and Vite
- 338 source files across 15+ feature modules (student, teacher, admin, rewards, games, attendance, gradebook, invoices, budgets, messaging, etc.)
- 25+ shared UI components (DataTable, Badge, ConfirmDialog, PlatformBridgeCard, StatCard, etc.)
- React Query v5 for data fetching with cache and optimistic updates
- Trilingual support (العربية / Français / English) with RTL via react-i18next
- Vitest + MSW + Testing Library test suite (27 test files)

#### Mobile App (Flutter)
- Flutter 3 app with Dart and Riverpod state management
- 276 source files across 35+ feature modules
- Clean Architecture (domain / data / features / shared)
- GoRouter navigation with role-based redirects
- Kid-facing design system (KidsContentColors) with gamification widgets (LevelBadge, StreakCard, BadgesPreview)
- WebSocket real-time sync support
- Trilingual localization (ar / fr / en) with RTL

#### Gamification System
- Student rewards: stars, XP, levels, badges, streaks
- XP-based leveling formula: `threshold = 50 × (level-1) × level`
- Badge system with configurable criteria (streak, completion, manual)
- Class leaderboard ranked by stars and level
- Educational mini-games: memory match, sorting, vocabulary cards
- Game completion rewards (configurable stars + XP per game)
- Reward history tracking with event types

#### Educational Content
- Content library with browse, upload, assign, and review workflows
- Story reader with page-by-page narration, Arabic letter themes, and age targeting
- Interactive coloring book (mobile-optimized with touch drawing)
- Writing workspace for student creative writing
- Quiz player with multiple question types and auto-grading

#### Cross-Platform Strategy
- Mobile-first priority for students and parents
- Web-first priority for teachers and administrators
- PlatformBridgeCard component (React + Flutter) to inform users about features on the other platform
- Arabic bridge messages with RTL support

#### Administration
- Admin dashboard with KPI summary cards (users, sessions, invitations, events, justifications)
- Users by role breakdown with visual bars
- Feature toggle management
- School settings configuration
- MEN compliance checking

#### Communication
- Internal messaging with threads
- Push notifications
- School announcements with role targeting
- Activity feed
- Calendar events

#### Finance
- Invoice management with status tracking
- Payment recording
- Fee structure configuration per level
- Budget envelopes with spending tracking
- Financial health indicators

#### Attendance & Gradebook
- Class attendance with present/absent/late/justified statuses
- Attendance analytics (rates, trends)
- Gradebook with weighted categories (quiz, exam, homework)
- Student transcripts with period averages and class rank
- Absence justification with file attachments

#### Infrastructure
- Docker Compose configurations for dev, staging, and production
- Kubernetes Helm chart with 15 templates (Deployment, Service, Ingress, HPA, PVC, NetworkPolicy, PDB, CronJob, Job, etc.)
- 9 GitHub Actions CI/CD workflows (backend CI, web CI, E2E, deploy staging, deploy K8s, docs, cleanup, dependabot)
- Nginx reverse proxy with SSL support
- Blue-green deployment strategy with auto-rollback

#### Monitoring & Observability
- Prometheus metrics collection
- 8 Grafana dashboards (API, Database, Redis, Auth, Business, Infra, Logs, Alerts)
- Loki + Promtail log aggregation
- Tempo distributed tracing
- Alertmanager notification routing

#### Security
- Password hashing with bcrypt
- Rate limiting per IP and per user via Redis
- CORS configurable by environment
- Audit trail for all sensitive actions
- GDPR endpoints (data export, account deletion)
- Pre-commit hooks with detect-secrets
- Input validation via Pydantic v2

#### Testing
- Backend: 133 test files (unit, integration, security, performance, contract, edge cases)
- Web: 27 test files with Vitest, MSW mock server, Testing Library, and factory helpers
- API contract tests validating request/response schemas
- Test infrastructure: fixtures, factories, render helpers

#### Documentation
- Comprehensive README.md with badges, architecture diagram, and quick start
- 7 documentation files: Architecture, API Reference, Database, Deployment, Testing, Security, Cross-Platform
- Sub-project READMEs (backend, web, mobile, infra)
- OpenAPI spec (auto-generated)

---

## [0.1.0] — 2026-01-15

### Added
- Initial project scaffolding
- FastAPI backend skeleton with core modules
- PostgreSQL + Redis Docker setup
- React frontend with basic routing
- Flutter mobile app shell
- Basic CI pipeline
