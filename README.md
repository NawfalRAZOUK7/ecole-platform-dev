<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React_18-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL_16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Redis_7-DC382D?style=for-the-badge&logo=redis&logoColor=white" />
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
</p>

<h1 align="center">🏫 École Platform</h1>

<p align="center">
  <strong>Plateforme SaaS E-Learning pour les Écoles K-12 au Maroc</strong><br>
  ERP scolaire · LMS · Communication · Facturation · Gamification
</p>

<p align="center">
  <a href="docs/ARCHITECTURE.md">Architecture</a> ·
  <a href="docs/API-REFERENCE.md">API Reference</a> ·
  <a href="docs/DEPLOYMENT.md">Déploiement</a> ·
  <a href="docs/TESTING.md">Tests</a> ·
  <a href="docs/SECURITY.md">Sécurité</a> ·
  <a href="docs/CROSS-PLATFORM.md">Cross-Platform</a>
</p>

---

## ✨ Nouveautés v1.1 (2026-05)

- **Stockage objet S3/MinIO** avec uploads directs jusqu'à 50 MB et scan antivirus ClamAV
- **Programmes académiques** (versions, équivalences, règles d'éligibilité, snapshots immuables)
- **Facturation bilingue AR/FR** conforme aux exigences fiscales marocaines (TVA, ICE, RC)
- **Phase E** : parité visuelle complète web ⇄ mobile sur les écrans destinés aux jeunes élèves
- **Déploiement Kubernetes** matures (Helm chart 15 templates, Kind local, K8s E2E en CI)
- **Mobile** étendu de 35 à 50+ modules : rubriques, banque de questions, passeport compétences, conformité, micro-budgets, micro-écoles, et plus

Détail complet : [`CHANGELOG.md`](CHANGELOG.md#110--2026-05-06)

---

## 📋 À propos

École Platform est une plateforme complète de gestion scolaire et d'apprentissage en ligne, conçue pour les écoles K-12 au Maroc. Elle couvre l'ensemble du cycle éducatif à travers une expérience web et mobile unifiée, avec support trilingue (العربية · Français · English).

### Fonctionnalités principales

| Module | Description |
|--------|-------------|
| **IAM** | Authentification JWT + 2FA/TOTP, RBAC 5 rôles, invitations, gestion profils |
| **ERP** | Écoles, classes, inscriptions, emplois du temps, niveaux scolaires |
| **LMS** | Contenus, quiz, évaluations, soumissions, banque de questions, rubriques |
| **Communication** | Messagerie interne, notifications push, annonces, fil d'actualité, calendrier |
| **Facturation** | Factures, paiements, structures de frais, budgets, santé financière |
| **Gamification** | Étoiles, XP, niveaux, badges, streaks, leaderboard, jeux éducatifs (mémoire, tri, vocabulaire) |
| **Suivi** | Présence, carnet de notes, progression, compétences (Skill Passport), rapports |
| **Conformité** | Audit trail, conformité MEN, GDPR, exports de données |

---

## 🏗 Stack Technologique

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTS                               │
│   📱 Flutter (Élève/Parent)    💻 React (Enseignant/Admin) │
├─────────────────────────────────────────────────────────┤
│                   NGINX (Reverse Proxy + SSL)            │
├─────────────────────────────────────────────────────────┤
│                   FastAPI (REST API v1 + WebSocket)       │
│    ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│    │ Services │──│ Repos    │──│ SQLAlchemy Async  │     │
│    └──────────┘  └──────────┘  └──────────────────┘     │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL 16        Redis 7          File Storage      │
│  (Data)               (Cache/Queue)    (Uploads)         │
├─────────────────────────────────────────────────────────┤
│  Prometheus · Grafana · Loki · Tempo · Alertmanager      │
└─────────────────────────────────────────────────────────┘
```

| Couche | Technologie | Détails |
|--------|-------------|---------|
| Backend API | **FastAPI** + Python 3.12 | SQLAlchemy 2.0 async, Pydantic v2, Alembic |
| Frontend Web | **React 18** + TypeScript | Vite 5, React Query v5, React Router v6, i18n |
| Mobile | **Flutter 3** + Dart | Riverpod, GoRouter, Dio, Clean Architecture |
| Base de données | **PostgreSQL 16** | 60+ migrations, replicas lecture |
| Cache/Queue | **Redis 7** | Sessions, rate limiting, tâches async |
| Stockage objet | **MinIO / S3** | Uploads directs, URLs présignées, scan ClamAV |
| PDF | **WeasyPrint** | Factures et reçus bilingues AR/FR conformes MEN/TVA |
| Infra | **Docker** + **Kubernetes (Helm)** | Helm chart (15 templates), Kind local, blue-green |
| CI/CD | **GitHub Actions** | 10 workflows (lint, test, build, deploy, K8s E2E) |
| Monitoring | **Grafana** stack | 8 dashboards, Prometheus, Loki, Tempo, Alertmanager |

---

## 📁 Structure du Projet

```
ecole-platform-dev/
│
├── backend/                    # 🐍 API FastAPI (Python)
│   ├── app/
│   │   ├── api/v1/             # 57 fichiers de routes REST
│   │   ├── core/               # Config, database, security, middleware
│   │   ├── models/             # 23 modules SQLAlchemy ORM
│   │   ├── schemas/            # Pydantic v2 schemas (request/response)
│   │   ├── services/           # Logique métier
│   │   ├── repositories/       # Accès données (queries async)
│   │   ├── domain/             # Entités métier & enums
│   │   └── templates/          # Templates email (Jinja2)
│   ├── alembic/versions/       # 56 migrations DB
│   └── tests/                  # 133 fichiers de test
│
├── web/                        # ⚛️ SPA React (TypeScript)
│   ├── src/
│   │   ├── features/           # Modules fonctionnels (student, teacher, admin, rewards, games...)
│   │   ├── services/           # API client, auth, services métier
│   │   └── shared/             # 25+ composants UI réutilisables, hooks, i18n
│   └── tests/                  # 27 fichiers de test (Vitest + MSW)
│
├── mobile/                     # 📱 App Flutter (Dart)
│   └── lib/
│       ├── features/           # 35+ modules fonctionnels
│       ├── domain/             # Entités & interfaces repository
│       ├── data/               # API client (Dio), DTOs, implémentations
│       └── shared/             # Widgets réutilisables, design tokens
│
├── infra/                      # 🚀 Infrastructure
│   ├── k8s/templates/          # 15 manifests Kubernetes (Helm)
│   ├── grafana/dashboards/     # 8 dashboards JSON
│   ├── prometheus/             # Métriques & alertes
│   ├── loki/                   # Agrégation de logs
│   ├── nginx/                  # Reverse proxy
│   └── docker-compose.*.yml    # Dev, staging, prod, monitoring
│
├── .github/workflows/          # 9 pipelines CI/CD
├── docs/                       # 📖 Documentation projet
├── scripts/                    # Scripts d'automatisation
└── Makefile                    # 50+ commandes make
```

---

## 🚀 Quick Start

### Prérequis

- Docker & Docker Compose
- Node.js 18+ (pour le web)
- Flutter 3.x (pour le mobile)
- Python 3.12+ (pour le développement backend local)

### Lancement

```bash
# 1. Cloner et configurer
git clone <repo-url> && cd ecole-platform-dev
cp .env.example .env

# 2. Démarrer l'environnement (backend + DB + Redis + Nginx)
make up

# 3. Appliquer les migrations
make migrate

# 4. Charger les données de test
make seed

# 5. Vérifier
make health
# → {"status": "healthy", "version": "0.1.0"}
```

```bash
# Frontend web
cd web && npm install && npm run dev
# → http://localhost:5173

# Application mobile
cd mobile && flutter pub get && flutter run
```

### Comptes de test

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Admin | `admin@ecole.test` | `Admin123!` |
| Enseignant | `teacher@ecole.test` | `Teacher123!` |
| Parent | `parent@ecole.test` | `Parent123!` |
| Élève | `student@ecole.test` | `Student123!` |

---

## 🎮 Gamification & Contenu Éducatif

Le système de gamification motive les élèves à travers :

- **⭐ Étoiles & XP** — Gagnées en complétant des leçons, quiz et jeux
- **🏅 Niveaux** — Progression basée sur les XP (`xpThreshold = 50 × (level-1) × level`)
- **🔥 Streaks** — Séries de jours consécutifs d'activité
- **🎖 Badges** — Débloqués automatiquement selon des critères (premier login, streak 7 jours, quiz master...)
- **🏆 Leaderboard** — Classement par classe
- **🎯 Jeux éducatifs** — Memory match, tri, cartes de vocabulaire avec récompenses

---

## 🔗 Stratégie Cross-Platform

| Rôle | Plateforme principale | Raison |
|------|----------------------|--------|
| Élève (STD) | 📱 Mobile | Interaction tactile, jeux, engagement quotidien |
| Parent (PAR) | 📱 Mobile | Consultation rapide, notifications push |
| Enseignant (TCH) | 💻 Web | Gestion complexe, saisie de données |
| Admin (ADM) | 💻 Web | Tableaux de bord, configuration, audit |

Quand une fonctionnalité existe sur une plateforme mais pas l'autre, un composant **PlatformBridgeCard** informe l'utilisateur avec un design attractif et une explication contextuelle (en arabe).

> Voir [docs/CROSS-PLATFORM.md](docs/CROSS-PLATFORM.md) pour les détails d'implémentation.

---

## 📊 Métriques du Projet

| Métrique | Valeur |
|----------|--------|
| Lignes de code total | **~188 000** |
| Backend (Python) | 80 500 LOC · 287 fichiers |
| Frontend Web (TypeScript) | 50 500 LOC · 338 fichiers |
| Mobile (Dart) | 57 300 LOC · 276 fichiers |
| API Endpoints | 57 modules de routes |
| Modèles de données | 23 modules SQLAlchemy |
| Migrations DB | 56 fichiers Alembic |
| Tests | 133 backend + 27 web + 1 contrat |
| Dashboards Grafana | 8 |
| Workflows CI/CD | 9 |
| Templates Kubernetes | 15 |
| Langues | 3 (العربية · Français · English) |

---

## 📖 Documentation

| Document | Contenu |
|----------|---------|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Architecture globale, couches, patterns, diagrammes |
| [`docs/API-REFERENCE.md`](docs/API-REFERENCE.md) | Endpoints API, groupes, authentification, pagination |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Docker, Kubernetes, CI/CD, environnements |
| [`docs/TESTING.md`](docs/TESTING.md) | Stratégie de tests, infrastructure, couverture |
| [`docs/SECURITY.md`](docs/SECURITY.md) | Auth, RBAC, sécurité API, audit, GDPR |
| [`docs/CROSS-PLATFORM.md`](docs/CROSS-PLATFORM.md) | Stratégie mobile-first/web-first, PlatformBridgeCard |
| [`docs/DATABASE.md`](docs/DATABASE.md) | Schéma, migrations, modèles, groupes |
| [`CHANGELOG.md`](CHANGELOG.md) | Historique des versions et changements |
| [`ROADMAP.md`](ROADMAP.md) | Fonctionnalités done / in progress / planned / future |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Git workflow, conventions commits/branches/PRs, code style |
| [`INSTALLATION.md`](INSTALLATION.md) | Guide d'installation complet (Docker, web, mobile, local) |
| [`LICENSE`](LICENSE) | MIT License |
| [`backend/README.md`](backend/README.md) | Documentation backend détaillée |
| [`web/README.md`](web/README.md) | Documentation frontend web |
| [`mobile/README.md`](mobile/README.md) | Documentation application mobile |
| [`infra/README.md`](infra/README.md) | Documentation infrastructure |

---

## 🛠 Commandes Make

| Commande | Description |
|----------|-------------|
| `make up` | Démarrer l'environnement dev |
| `make down` | Arrêter l'environnement |
| `make logs` | Suivre les logs en temps réel |
| `make migrate` | Exécuter les migrations Alembic |
| `make seed` | Charger les données de test |
| `make test` | Lancer les tests backend |
| `make test-cov` | Tests + rapport de couverture |
| `make lint` | Linting (Ruff + MyPy) |
| `make monitoring-up` | Démarrer Prometheus + Grafana + Loki |
| `make deploy-blue-green` | Déploiement blue-green production |

---

## 📄 Licence

Projet de Fin d'Études — © 2026 Nawfal Razouk
