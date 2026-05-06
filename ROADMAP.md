# 🗺 Roadmap

## ✅ Done

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

### Payment & Finance
- [x] Invoice PDF generation + Moroccan compliance (WeasyPrint, TVA, bilingual) — Phase 7 complete

### Quality & Polish
- [ ] Increase backend test coverage to 90%+
- [ ] Add Flutter widget tests for critical screens
- [ ] Performance optimization for large datasets (1000+ students)

---

## 📋 Planned (Next Phase)

### AI & Intelligence
- [ ] AI-powered content recommendations based on student performance
- [ ] Predictive analytics for at-risk students
- [ ] Automatic difficulty adaptation for quizzes and games
- [ ] Natural language processing for Arabic writing feedback
- [ ] Smart timetable generation with constraint solver

### Advanced Features
- [ ] Offline-first mobile with full sync queue
- [ ] Parent-child shared review interface (enhanced)
- [ ] Bulk enrollment via CSV/Excel import
- [ ] Advanced report generation (PDF bulletins)
- [ ] SMS/WhatsApp notification channels

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
