# Changelog

All notable changes to École Platform are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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
