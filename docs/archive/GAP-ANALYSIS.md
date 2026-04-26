# Feature Gap Analysis — Plateforme Éducative "École"

**PDF Spec:** `ecole-platform-report/sources/E_learning_Platform.pdf`
**Date:** 2026-04-25
**Legend:** DONE = fully implemented, PARTIAL = scaffolded/basic, MISSING = not yet built

---

## 1. AI & Agents Intelligents

### 1.1 Agent de Recommandation

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Analyse du profil et progrès de l'enfant | PARTIAL | `GET /api/v1/ai/recommendations` exists, `progress` endpoints exist | `progress/` feature folder exists | `progress/` feature exists | Real ML model — currently uses mock provider. Need real scoring pipeline that ingests quiz results, time-on-task, error patterns to build a learner profile |
| Suggestions personnalisées de cours et activités | PARTIAL | Endpoint returns recommendations | Not wired to display AI suggestions | Not wired | Backend returns mock data. Need: real recommendation engine (collaborative filtering or rule-based), UI cards showing "Recommended for you" on student dashboard |
| Adaptation du niveau de difficulté | DONE | `difficulty_adapter.py` service + `difficulty_adaptation` model fully implemented | `student/` feature exists | `progress/` exists | Fully functional — adjusts quiz difficulty based on performance history |
| Recommandation de jeux éducatifs | PARTIAL | `GET /api/v1/games/configs` filters by age/difficulty | `games/` feature exists | `games/` with mini-games | Missing AI-driven game selection. Current filtering is rule-based (age + difficulty). Need: model that matches game type to learning gaps |

### 1.2 Services IA

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Correction automatique des exercices | PARTIAL | `quiz_grading.py` auto-grades MCQ/true-false | `quizzes/` + `results/` | `quizzes/` | MCQ auto-grading works. Missing: free-text/essay auto-correction using NLP. Need AI provider integration for open-ended answers |
| Aide à l'écriture (reconnaissance, suggestions) | PARTIAL | `POST /api/v1/writing-attempts` + `ai_service.py` with mock/claude providers | Not wired in web UI | Not wired | Backend plumbing exists with full provider abstraction (mock + Claude). Missing: web/mobile UI for writing workspace, handwriting recognition component |
| Analyse prédictive des performances | MISSING | Analytics endpoints exist (`analytics.py`) but no predictive model | `analytics/` shows historical data | No analytics | Need: ML pipeline that forecasts student performance trends, at-risk detection, early warning alerts |
| Génération de contenu adaptatif | MISSING | Content CRUD exists but no generative pipeline | `content/` feature exists | `content/` exists | Need: AI service that generates exercises/stories adapted to student level. Requires new endpoint + provider method |

---

## 2. Fonctionnalités par Profil Utilisateur

### 2.1 Pour l'Enfant (Student)

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Interface ludique et adaptée à l'âge | PARTIAL | Age-based content filtering exists | Basic UI, not gamified | Flutter UI with games/coloring/stories | Web needs age-adapted themes. Mobile is ahead with coloring, mini-games |
| Cours interactifs (histoires, vidéos, livres) | DONE | Content library with stories, videos, PDFs seeded. `content_library.py` API | `content/` feature | `content/` + `coloring/` | Content delivery works. Could enhance with interactive elements (embedded quizzes in stories) |
| Activités éducatives variées | DONE | Quizzes, activities, assignments, submissions endpoints all exist | `quizzes/`, `activities/`, `submissions/` | `quizzes/`, `student/` | Working end-to-end |
| Jeux pédagogiques personnalisés | DONE | `games/` API with configs, completions, age filtering | `games/` feature | `games/` with memory, sorting, vocabulary games | Games work. Personalization is rule-based not AI-driven (see 1.1) |
| Outils d'écriture assistée par IA | PARTIAL | `writing-attempts` endpoint exists | Not yet in UI | Not yet in UI | Backend ready. Need: writing workspace component in web + mobile |
| Suivi de progression visuel | DONE | `progress/` API returns detailed metrics | `progress/` feature | `progress/` feature | Working with charts and level tracking |

### 2.2 Pour le Parent

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Tableau de bord des statistiques enfant | DONE | `analytics/` + `progress/` APIs with parent access | `analytics/` + `family/` features | `analytics/` + `family/` features | Working — parent can see child stats |
| Visualisation des résultats et cours | DONE | Results, gradebook, courses APIs | `results/`, `gradebook/` | `results/` | Working |
| Interface de révision partagée | PARTIAL | Content accessible to parents | `family/` feature exists | `family/` feature exists | Basic shared view exists. Missing: collaborative review sessions where parent and child review together in real-time |
| Alertes et recommandations IA | MISSING | Notifications API exists, but no AI-triggered alerts | `notifications/` feature | `notifications/` feature | Need: AI alert service that detects concerning patterns (grade drops, low engagement) and pushes parent notifications |
| Communication avec l'enseignant | DONE | `messaging/` API with threads, read receipts | `messages/` feature | `messages/` feature | Fully working parent-teacher messaging |
| Historique complet des activités | DONE | Activity feed API, audit trail | `feed/` feature | `feed/` feature | Working |

### 2.3 Pour l'Enseignant (Teacher)

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Gestion des classes et élèves | DONE | `classes/`, `enrollments/`, `students` APIs | `admin/`, `teacher/` features | `teacher/` feature | Working |
| Création et organisation des cours | DONE | `courses/`, `content/`, `content_library` APIs | `content/`, `teacher/` | `teacher/` | Working |
| Attribution d'exercices et activités | DONE | `assignments/`, `class_assignments` APIs | `submissions/`, `activities/` | `student/`, `submissions/` | Working |
| Suivi individualisé des progrès | DONE | `progress/` API with per-student views | `progress/`, `gradebook/` | `progress/` | Working |
| Outils d'évaluation et correction | DONE | `assessments/`, `rubrics/`, `gradebook/`, `question_bank` APIs | `quizzes/`, `rubrics/`, `gradebook/`, `question-bank/` | `quizzes/` | Working — includes rubrics, gradebook, question bank |
| Communication avec les parents | DONE | `messaging/` API | `messages/` feature | `messages/` feature | Working |

### 2.4 Pour l'École (Admin/Director)

| Feature | Status | Backend | Web | Mobile | What's missing |
|---------|--------|---------|-----|--------|----------------|
| Portail d'administration complet | DONE | `admin/`, `schools/` APIs, full ABAC permissions | `admin/` feature | `admin/` feature | Working — user management, school settings, feature toggles |
| Gestion des abonnements et facturation | DONE | `billing/`, `invoices/`, `payments/` APIs | `billing/`, `invoices/` | `billing/`, `invoices/` | Working — plans, invoices, payment tracking |
| Tableau de bord analytique global | DONE | `analytics/` with overview, attendance, grades, billing, engagement KPIs | `analytics/` feature | `analytics/` | Working |
| Gestion des utilisateurs | DONE | IAM model, `profiles/`, role management, `invitations/` | `admin/`, `profile/` | `admin/`, `profile/` | Working — full RBAC/ABAC |
| Rapports d'utilisation et performance | DONE | `reports/` API with scheduling + export | `reports/` feature | `reports/` | Working |

---

## 3. Architecture & Technologies

### 3.1 Stack Technique

| Layer | PDF Spec | Implemented | Status | Notes |
|-------|----------|-------------|--------|-------|
| Frontend Web | React + TypeScript | React + TypeScript (Vite) | DONE | Full feature set in `web/src/` |
| Application Mobile | Flutter (Dart) | Flutter (Dart) | DONE | Full feature set in `mobile/lib/` |
| Backend/API | FastAPI (Python) | FastAPI (Python) | DONE | 55+ API modules in `backend/app/api/v1/` |
| Base de Données | PostgreSQL | PostgreSQL 16 | DONE | With PgBouncer, read replicas |
| Cache | Redis | Redis 7 | DONE | Session cache, task queue |
| Services IA | Python (ML frameworks) | Python mock + Claude provider | PARTIAL | Provider abstraction ready, needs real ML models |

### 3.2 Architecture

| Aspect | PDF Spec | Status | Notes |
|--------|----------|--------|-------|
| Monolithique modulaire | Single codebase, modular | DONE | Clean module separation under `app/api/v1/`, `app/services/`, `app/models/` |
| Préparé pour scaling | Kubernetes-ready | DONE | Docker multi-stage, PgBouncer, read replicas, blue-green deploy |

---

## 4. Pratiques DevOps

| Practice | PDF Spec | Status | What exists | What's missing |
|----------|----------|--------|-------------|----------------|
| CI/CD | GitHub Actions | DONE | `ci.yml`, `web-ci.yml`, `web-e2e.yml`, `deploy-staging.yml`, `docs.yml`, `cleanup-images.yml`, `dependabot-automerge.yml` | |
| Conteneurisation | Docker | DONE | Multi-stage Dockerfiles for backend + web, docker-compose for dev/staging/prod | |
| Orchestration | Kubernetes (préparé) | PARTIAL | Docker Compose with blue-green deploy scripts | No Kubernetes manifests yet. Need: k8s deployment YAMLs, Helm chart, or Kustomize overlays |
| Monitoring | Prometheus/Grafana | DONE | `prometheus.yml`, `alert_rules.yml`, Grafana dashboards, backend metrics exporter | |
| ELK Stack | Logging | MISSING | JSON file logging configured | No Elasticsearch/Logstash/Kibana. Need: ELK compose service or managed logging (CloudWatch, Datadog) |
| Git Flow | Versioning | DONE | Branch strategy with main/develop/feature | |
| Environments | Dev/Staging/Prod | DONE | `docker-compose.dev.yml`, `docker-compose.staging.yml`, `docker-compose.prod.yml` | All three environments fully configured |

---

## 5. Implementation Priority — What to build next

### Priority 1 — HIGH IMPACT, foundation for other features

1. **AI Provider: swap mock → real Claude/OpenAI integration**
   - **Backend:** `backend/app/services/ai/claude_provider.py` exists but needs real API key wiring and production-grade prompts
   - **Infra:** Add `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` to env/secrets
   - **Effort:** 2-3 days

2. **Writing workspace UI (web + mobile)**
   - **Web:** New component in `web/src/features/student/` — text editor with "Get AI help" button calling `POST /api/v1/writing-attempts`
   - **Mobile:** New screen in `mobile/lib/features/student/` — same flow
   - **Effort:** 3-5 days

### Priority 2 — MEDIUM IMPACT, key differentiators

3. **AI-triggered parent alerts**
   - **Backend:** New service `app/services/ai/alert_service.py` — monitors student metrics, triggers notifications when patterns detected (grade drops, inactivity)
   - **Web/Mobile:** Wire into existing `notifications/` feature
   - **Effort:** 3-4 days

4. **Predictive performance analytics**
   - **Backend:** New service `app/services/ai/predictive_analytics.py` — simple regression/trend model on quiz scores + engagement data
   - **Web:** New dashboard card in `analytics/` showing predicted trajectory
   - **Effort:** 5-7 days

5. **Free-text auto-correction**
   - **Backend:** Extend `quiz_grading.py` to call AI provider for open-ended answer evaluation
   - **Web/Mobile:** No change needed — results display already handles grading feedback
   - **Effort:** 2-3 days

### Priority 3 — NICE TO HAVE, polish

6. **Adaptive content generation**
   - **Backend:** New endpoint `POST /api/v1/ai/generate-content` — generates exercises/stories at student's level
   - **Web:** "Generate exercise" button in teacher course builder
   - **Effort:** 5-7 days

7. **Collaborative parent-child review sessions**
   - **Backend:** WebSocket room for shared review (extend `ws_manager.py`)
   - **Web/Mobile:** Shared review screen with synchronized content
   - **Effort:** 5-8 days

8. **Kubernetes manifests**
   - **Infra:** Helm chart or Kustomize with deployment, service, ingress, HPA
   - **Effort:** 3-5 days

9. **ELK Stack integration**
   - **Infra:** Add Elasticsearch, Logstash, Kibana to `docker-compose.monitoring.yml`, configure Filebeat
   - **Effort:** 2-3 days

10. **AI game recommendation engine**
    - **Backend:** Extend `game_service.py` with learning-gap analysis to recommend specific games
    - **Effort:** 3-4 days

---

## Summary

| Category | Total Features | DONE | PARTIAL | MISSING |
|----------|---------------|------|---------|---------|
| AI Agent de Recommandation | 4 | 1 | 2 | 1 |
| Services IA | 4 | 0 | 2 | 2 |
| Enfant (Student) | 6 | 4 | 2 | 0 |
| Parent | 6 | 4 | 1 | 1 |
| Enseignant (Teacher) | 6 | 6 | 0 | 0 |
| École (Admin) | 5 | 5 | 0 | 0 |
| Stack Technique | 6 | 5 | 1 | 0 |
| DevOps | 7 | 5 | 1 | 1 |
| **TOTAL** | **44** | **30 (68%)** | **9 (20%)** | **5 (11%)** |

The platform has a solid foundation with 68% of features fully done. The main gaps are in the AI services layer (which currently uses mock providers) and a few UI integrations for features that already have backend support. The Teacher and Admin profiles are 100% complete. The critical path forward is activating the real AI provider and building the writing workspace + parent alert UIs.
