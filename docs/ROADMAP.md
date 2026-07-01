# 🗺 Roadmap

## ✅ Done

### v1.1 (2026-05) — Production Hardening & Compliance

#### Storage & Uploads
- [x] Unified storage abstraction (local / MinIO / S3)
- [x] MinIO development stack in `docker-compose.dev.yml`
- [x] Direct large-file uploads (web + mobile, up to 50 MB)
- [x] Presigned download URLs with redirect
- [x] ClamAV virus scanning + retry logic
- [x] Virus scan Prometheus metrics
- [x] Local-uploads → MinIO migration script
- [x] MinIO observability runbook

#### Academic Programs (G49–G50)
- [x] Programs / Versions / Equivalences / Snapshots
- [x] Eligibility rules engine
- [x] Enrollments lifecycle
- [x] Web admin UI (programs, versions, equivalences, eligibility, enrollments)
- [x] Student academic history (web + mobile)

#### Bilingual Invoicing & Moroccan Compliance
- [x] Bilingual AR/FR PDF templates (WeasyPrint)
- [x] TVA breakdown on `InvoiceItem`
- [x] Banking + branding fields on `School`
- [x] Payment receipt PDF + QR code
- [x] All 7 phases shipped

#### Phase A / B — Student & Parent Enrichment
- [x] Writing Workspace (student creative writing)
- [x] Parent Shared Review with comments
- [x] `ParentAlertService`

#### Phase D — Kubernetes-First Deployment
- [x] Helm chart matured (15 templates, 3 values overlays)
- [x] Local Kind cluster (`ecole-dev`)
- [x] K8s E2E workflow + Helm validation in CI
- [x] Blue-green compose configurations

#### Phase E — Cross-Platform Kid UX
- [x] E1 level-age mapping + auto age-filtering
- [x] E2 longest_streak tracking
- [x] E4 Cairo font on web (Arabic-optimized)
- [x] E5 kid-friendly color system on web
- [x] E6 shimmer skeletons on kid-facing screens
- [x] E7 mobile branded splash screen
- [x] E8 web design tokens matching mobile
- [x] E9 kid-friendly empty states
- [x] E10 mobile offline content caching (TTL 7d)

#### Mobile Expansion
- [x] Rubrics module (list, editor, grading)
- [x] Question bank module (import, quiz generation)
- [x] Quiz analytics
- [x] Class progress
- [x] Parent absence justification with attachments
- [x] My Children page (parent)
- [x] Skills passport (radar, export, analytics)
- [x] Compliance module (curriculum mapping, reports)
- [x] Financial health (snapshots, export)
- [x] Micro-budgets (envelopes, allocations, MAD)
- [x] Micro-schools CRUD
- [x] Attendance heatmap + offline cache
- [x] Gradebook with 0–20 Moroccan scale + transcript
- [x] Sync v2 (status, conflicts, shell indicator)
- [x] Recovery flows + privacy + report schedules
- [x] Native Android + iOS platforms initialized
- [x] Accessibility (Semantics on 30+ screens)
- [x] 278 hardcoded colors → theme tokens (dark-mode safe)

#### Backend Depth & Auth
- [x] New permissions (LMS_ASSIGNMENT_READ, LMS_ACTIVITY_READ, skill dimensions, milestones)
- [x] Role redirection refactor
- [x] JWT extraction from query parameters (signed-URL flow)
- [x] Reward badge management (CRUD + admin UI + seeding)
- [x] Trilingual login error translations

#### Timetable
- [x] `max_consecutive_classes` constraint
- [x] Academic year support
- [x] Generation preview (dry-run)

#### Testing
- [x] 18 new mobile test files (30+ unit/widget + 2 integration)
- [x] Web tests for all new features
- [x] Backend integration tests for invoice/receipt PDFs
- [x] Web endpoint coverage at **97.7%** (was ~95%)
- [x] 25 missing API service methods added; 13 HTTP method mismatches fixed

---

### Core Platform (v1.0)
- [x] FastAPI backend with 57 API modules
- [x] PostgreSQL 16 with 56 Alembic migrations
- [x] Redis 7 (sessions, cache, rate limiting)
- [x] JWT authentication + optional 2FA/TOTP
- [x] RBAC with 5 roles and granular permissions
- [x] Cursor-based pagination

### Web Frontend
- [x] React 18 + TypeScript + Vite SPA
- [x] 15+ feature modules (student, teacher, admin, rewards, games, attendance, gradebook, invoices, budgets, messaging...)
- [x] 25+ shared UI components
- [x] React Query v5 data fetching
- [x] Trilingual support (ar/fr/en) with RTL

### Mobile App
- [x] Flutter 3 + Riverpod + GoRouter
- [x] 35+ feature modules with Clean Architecture
- [x] Kid-facing design system (KidsContentColors)
- [x] WebSocket real-time sync
- [x] Trilingual localization with RTL

### Gamification
- [x] Stars, XP, levels, badges, streaks
- [x] Class leaderboard
- [x] Educational mini-games (memory, sorting, vocabulary)
- [x] Game completion rewards
- [x] Reward history

### Educational Content
- [x] Content library (browse, upload, assign, review)
- [x] Story reader with Arabic letters
- [x] Interactive coloring book (mobile)
- [x] Writing workspace
- [x] Quiz player with auto-grading

### Cross-Platform
- [x] Mobile-first strategy for students/parents
- [x] Web-first strategy for teachers/admin
- [x] PlatformBridgeCard (React + Flutter)

### Infrastructure
- [x] Docker Compose (dev/staging/prod)
- [x] Kubernetes Helm chart (15 templates)
- [x] 9 GitHub Actions CI/CD workflows
- [x] Blue-green deployment
- [x] Prometheus + Grafana (8 dashboards) + Loki + Tempo
- [x] MinIO / S3-compatible object storage (Phase 5 complete)
- [x] Local Kubernetes setup with Kind (ecole-dev cluster)

### Testing
- [x] 133 backend test files (unit/integration/security/performance)
- [x] 27 web test files (Vitest + MSW)
- [x] Test infrastructure (factories, fixtures, render helpers)

### Academic Records
- [x] Academic Program Management (G49-G50 migrations — programs, versions, equivalences, snapshots)
- [x] Student transcript feature (PDF transcript generation via WeasyPrint, transcript service + API)

### Payment & Finance
- [x] Invoice PDF generation + Moroccan compliance (WeasyPrint, TVA, bilingual) — all 7 phases

### Documentation
- [x] README.md with architecture overview
- [x] 12 docs/ files (Architecture, API, DB, Deploy, Tests, Security, Cross-Platform, K8s Setup, MinIO Rollout, MinIO Architecture, Payment, ClamAV)
- [x] CHANGELOG, ROADMAP, CONTRIBUTING, INSTALLATION, LICENSE

---

## 🔄 In Progress

### Quality & Polish
- [ ] Increase backend test coverage to 90%+ (currently ~85%)
- [ ] Performance optimization for large datasets (1000+ students)
- [ ] Lighthouse score audit and tuning on web

### Compliance v2
- [ ] MEN curriculum referential v2 (real ministry data import)
- [ ] DGSSI security questionnaire compliance check

---

## 📋 Planned (Next Phase)

### AI & Intelligence
- [ ] LLM gateway with prompt templates and rate limits
- [ ] RAG-based pedagogical assistant over course content
- [ ] AI-powered content recommendations based on student performance
- [ ] Predictive analytics for at-risk students
- [ ] Adaptive difficulty engine v2 (currently rule-based, target ML-based)
- [ ] Natural language processing for Arabic writing feedback
- [ ] Voice-based interaction for young learners (maternelle)
- [ ] Smart timetable generation with constraint solver

### Advanced Features
- [ ] Bulk enrollment via CSV/Excel import
- [ ] Advanced report generation (PDF bulletins per period)
- [ ] SMS/WhatsApp notification channels
- [ ] Parent payment portal v2 (CMI, Payzone integration)

### Platform Expansion
- [ ] Multi-tenant support (multiple schools per instance)
- [ ] School network admin (group of schools)
- [ ] Marketplace for educational content
- [ ] Teacher-to-teacher content sharing

---

## 🔮 Future Vision

### Long-term Goals
- [ ] Arabic OCR for handwriting recognition
- [ ] Voice-based interaction for young learners (maternelle)
- [ ] AR/VR educational experiences
- [ ] Integration with Moroccan Ministry of Education (MEN) systems
- [ ] Mobile-native payment integration (CMI, Payzone)
- [ ] Real-time collaborative editing (Google Docs-style)
- [ ] Parent community features (forums, events)
- [ ] White-label deployment for different school networks

### Technical Debt & Improvements
- [ ] Migrate to microservices if scale requires
- [ ] GraphQL API alongside REST for complex queries
- [ ] CDN for static content delivery
- [ ] Database sharding for multi-tenant at scale
- [ ] Mobile app stores deployment (App Store + Google Play)
