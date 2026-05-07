# 🏗 Architecture

## Vue d'ensemble

École Platform suit une architecture **monolith modulaire** avec séparation stricte des couches. Le backend expose une API REST v1 consommée par deux clients : une SPA React (web) et une application Flutter (mobile).

```
                    ┌──────────────┐    ┌──────────────┐
                    │  React SPA   │    │ Flutter App  │
                    │  (Web)       │    │ (Mobile)     │
                    └──────┬───────┘    └──────┬───────┘
                           │                   │
                    ┌──────┴───────────────────┴──────┐
                    │         Nginx (Reverse Proxy)    │
                    │         SSL · Rate Limit · CORS  │
                    └──────────────┬───────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     FastAPI Backend        │
                    │  ┌─────────────────────┐   │
                    │  │   API Routes (v1)   │   │
                    │  ├─────────────────────┤   │
                    │  │   Service Layer     │   │
                    │  ├─────────────────────┤   │
                    │  │   Repository Layer  │   │
                    │  ├─────────────────────┤   │
                    │  │   SQLAlchemy Models │   │
                    │  └─────────────────────┘   │
                    └────┬──────────────┬────────┘
                         │              │
              ┌──────────┴──┐    ┌──────┴──────┐
              │ PostgreSQL  │    │    Redis     │
              │ (Data)      │    │ (Cache/Queue)│
              └─────────────┘    └─────────────┘
```

## Backend — Architecture en couches

### Couche API (`app/api/v1/`)

Responsabilités : routing HTTP, validation des entrées (Pydantic), sérialisation des réponses, documentation OpenAPI.

Chaque fichier de route représente un module fonctionnel. Les routes utilisent les dépendances FastAPI (`Depends()`) pour l'injection de l'authentification et des services.

```python
@router.get("/rewards/me")
async def get_my_rewards(auth: AuthContext = Depends(get_auth_context)):
    return await rewards_service.get_student_rewards(auth.user_id)
```

### Couche Services (`app/services/`)

Responsabilités : logique métier, orchestration multi-repository, validation des règles de gestion, émission d'événements.

Les services ne connaissent pas HTTP — ils travaillent avec des objets métier et délèguent l'accès aux données aux repositories.

### Couche Repositories (`app/repositories/`)

Responsabilités : requêtes SQL via SQLAlchemy async, pagination par curseur, filtres, agrégations.

Les repositories retournent des modèles ORM ou des tuples de résultat, jamais des réponses HTTP.

### Couche Models (`app/models/`)

24 modules de modèles organisés en 9+ groupes de migration :

| Groupe | Modules | Tables principales |
|--------|---------|-------------------|
| **G1 — IAM** | `iam.py` | users, sessions, memberships, invitation_codes, parent_child_links, profiles |
| **G2 — ERP** | `erp.py`, `school.py`, `levels.py` | schools, classes, enrollments, timetable, attendance, programs |
| **G3 — LMS** | `lms.py`, `skill_passport.py` | content_items, quizzes, questions, submissions, rubrics, gradebook |
| **G4 — COM** | `com.py`, `calendar.py` | conversations, messages, notifications, announcements, events |
| **G5 — Billing & Finance** | `billing.py`, `budget.py`, `financial_health.py` | invoices, payments, fee_structures, budgets, micro-budgets, financial snapshots |
| **G6 — Audit & Gamification** | `audit.py`, `games.py`, `rewards.py`, `feature.py` | audit_logs, feature_toggles, rewards, badges, game_configs |
| **G7 — Programmes (v1.1)** | `erp.py` (G49–G50) | programs, program_versions, program_equivalences, eligibility_rules, program_assignment_events |
| **G8 — Conformité & Reporting** | `men_compliance.py`, `reporting.py` | compliance_reports, curriculum_mappings, report_jobs, report_schedules, data_exports |
| **G9 — Stockage & Sync** | `documents.py`, `uploads.py`, `sync_queue.py` | documents, document_versions, resources, upload_sessions, sync_queue, sync_devices, sync_conflicts |

Modules transversaux : `ai.py`, `difficulty_adaptation.py`, `micro_school.py`, `calendar.py`.

---

## Frontend Web — Architecture React

### Organisation feature-based

Chaque module fonctionnel dans `src/features/` est autonome :

```
src/features/rewards/
├── RewardsPage.tsx           # Page principale
├── StudentRewardsPage.tsx    # Vue étudiant
├── LeaderboardPage.tsx       # Classement
├── LevelBadge.tsx            # Composant badge de niveau
├── StreakCard.tsx             # Composant série
├── StarCounter.tsx           # Compteur d'étoiles
├── BadgeShelf.tsx            # Étagère de badges
├── rewards.service.ts        # Client API + normalizers
└── useRewards.ts             # React Query hooks
```

### Patterns clés

- **React Query** pour le data fetching avec cache, refetch automatique et optimistic updates
- **Normalizer pattern** : les services transforment les réponses API (snake_case → camelCase) pour isoler le frontend du format backend
- **Composants partagés** (`shared/ui/`) : 25+ composants réutilisables (DataTable, Badge, ConfirmDialog, PlatformBridgeCard, StatCard, etc.)
- **i18n** : react-i18next avec 3 langues et support RTL automatique

---

## Mobile — Architecture Flutter

### Clean Architecture

```
lib/
├── domain/              # Couche métier pure (pas de dépendances framework)
│   ├── entities/        # Objets métier (User, StudentRewards, LibraryItem...)
│   └── repositories/    # Interfaces (contrats)
│
├── data/                # Implémentation des contrats
│   ├── api/             # Client HTTP Dio + interceptors
│   ├── dto/             # Data Transfer Objects
│   └── repositories_impl/  # Implémentations concrètes
│
├── features/            # 35+ modules UI (screens + providers)
│   ├── student/         # Accueil, contenu, progression
│   ├── rewards/         # Récompenses, badges, leaderboard
│   ├── games/           # Jeux éducatifs
│   └── ...
│
└── shared/              # Code partagé
    ├── widgets/         # Widgets réutilisables (PlatformBridgeCard, SearchFilterBar...)
    └── ui/tokens/       # Design tokens (colors, spacing)
```

### State Management — Riverpod

Chaque écran utilise un `StateNotifier` ou `FutureProvider` dédié :

```dart
final rewardsProvider = FutureProvider.autoDispose<StudentRewards>((ref) async {
  final repo = ref.read(rewardsRepositoryProvider);
  return repo.getMyRewards();
});
```

---

## Patterns transversaux

| Pattern | Usage |
|---------|-------|
| **Repository** | Séparation accès données / logique métier |
| **Service Layer** | Orchestration et règles de gestion |
| **AuthContext + RequiresPermission** | RBAC transversal sur chaque endpoint |
| **Feature-based Organization** | Modules autonomes (composants + hooks + services + types) |
| **Factory Pattern (Tests)** | Fonctions `createUser()`, `createStudent()` pour les données de test |
| **MSW Mock Server** | Interception HTTP dans les tests web sans serveur réel |
| **Cursor-based Pagination** | `next_cursor` + `has_more` pour les grandes listes |
| **Normalizer Pattern** | Transformation snake_case → camelCase dans les services frontend |
| **Bridge Card Pattern** | Informer les utilisateurs des fonctionnalités sur l'autre plateforme |
| **StateNotifier (Mobile)** | Gestion d'état Riverpod avec états loading/error/data |
| **Storage Abstraction** | Backend `local` / `minio` / `s3` interchangeable derrière une interface commune |
| **Signed URL Redirect** | Téléchargement via redirection HTTP 307 vers URL S3 présignée (durée courte) |
| **Snapshot d'audit** | Persistance d'instantanés (`ProgramSnapshot`) à chaque changement structurant |
| **State Machine (Workflows)** | Cycle de vie des entités (demandes budgétaires, soumissions, paiements) modélisé explicitement |
| **Seed Architecture** | Système de données demo idempotent (`seed.py` + `seed_extensions.py` + `seed_enhanced.py`) couvrant ~93% des tables |
| **Offline Sync** | SQLite local + file d'attente de sync + résolution de conflits pour le mobile en connectivité limitée |

---

## Stockage et CDN — Architecture S3/MinIO

Depuis la v1.1, l'ensemble des fichiers (devoirs déposés, contenus pédagogiques, pièces justificatives, factures PDF, ressources micro-école) transite par une couche de stockage objet S3-compatible.

```
   ┌─────────────┐                              ┌──────────────────┐
   │ Client      │  1. POST /uploads/initiate   │   FastAPI        │
   │ (web/mobile)│ ───────────────────────────► │   StorageService │
   │             │  2. ← Pre-signed PUT URL     │                  │
   │             │ ◄─────────────────────────── │                  │
   │             │  3. PUT bytes directement    │                  │
   │             │ ──────────────────────────►  │   ┌──────────┐   │
   │             │                              │   │  MinIO/S3│   │
   │             │  4. POST /uploads/complete   │   └─────┬────┘   │
   │             │ ───────────────────────────► │         │        │
   │             │                              │         ▼        │
   │             │                              │   ┌──────────┐   │
   │             │                              │   │  ClamAV  │   │
   │             │  5. ← {status, scan_result} │   │  scan    │   │
   │             │ ◄─────────────────────────── │   └──────────┘   │
   └─────────────┘                              └──────────────────┘
```

### Interface unifiée

```python
class StorageBackend(Protocol):
    async def initiate_upload(self, key: str, size: int) -> UploadInitiation: ...
    async def complete_upload(self, key: str, parts: list[Part]) -> StoredFile: ...
    async def get_signed_download_url(self, key: str, ttl: int) -> str: ...
    async def delete(self, key: str) -> None: ...
```

Trois implémentations interchangeables :
- `LocalStorage` — système de fichiers (dev sans MinIO)
- `MinioStorage` — MinIO (dev complet, staging on-prem)
- `S3Storage` — AWS S3 ou compatible (production)

### Téléchargements — redirection signée

Les endpoints de téléchargement (`GET /content/{id}/download`, `GET /invoices/{id}/pdf`, etc.) ne renvoient pas le fichier directement : ils émettent une redirection HTTP 307 vers une URL S3 présignée valable 5 minutes. Cette approche décharge l'API du transfert de fichiers volumineux et permet au client de bénéficier des optimisations CDN de S3/MinIO.

### Antivirus — pipeline ClamAV

Toute complétion d'upload déclenche une tâche asynchrone `scan_uploaded_file()` exécutée par le worker ARQ. Le résultat (`clean`, `infected`, `error`) est persisté sur la métadonnée du fichier ; un fichier infecté est immédiatement supprimé du bucket et notifié à l'uploader. Les métriques Prometheus `virus_scan_total{result}` et `virus_scan_duration_seconds` alimentent le tableau de bord sécurité Grafana.

---

## Domaine Programmes Académiques

Le domaine introduit en v1.1 (migrations G49–G50) modélise le cycle de vie des programmes pédagogiques avec audit complet :

```
Program ─┬─► ProgramVersion ─┬─► EligibilityRule
         │                   └─► ProgramEquivalence
         │
         └─► Enrollment ──► ProgramSnapshot (immutable)
```

### Entités principales

| Entité | Rôle |
|--------|------|
| `Program` | Programme pédagogique (ex. « Cycle primaire », « Filière internationale ») avec niveau cible et matières |
| `ProgramVersion` | Version datée d'un programme (la version est l'unité d'inscription, pas le programme lui-même) |
| `ProgramEquivalence` | Correspondance entre deux versions (ex. v2024 ↔ v2025 pour reconnaître les acquis) |
| `EligibilityRule` | Règle déclarative (âge minimum, niveau prérequis, validation de modules) évaluée par un moteur de règles |
| `Enrollment` | Inscription d'un élève à une `ProgramVersion`, avec snapshot immuable au moment de l'inscription |
| `ProgramSnapshot` | Cliché complet de la version au moment de l'inscription (matières, coefficients, règles) — garantit que les règles ne changent pas pour un élève déjà inscrit |

### Moteur d'éligibilité

Le service `eligibility_engine.py` évalue les règles dans l'ordre : préfiltres rapides (âge, niveau) puis prédicats lourds (transcripts, équivalences). Le résultat (`eligible`, `eligible_with_conditions`, `ineligible`) est cachable par `(student_id, version_id)` car déterministe.

---

## Topologie de déploiement Kubernetes

```
                          ┌──────────────────┐
                          │   Ingress nginx  │  (TLS, WAF)
                          └────────┬─────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │  web Deploy    │  │  backend Deploy │  │  worker Deploy │
     │  (HPA 2-10)    │  │  (HPA 3-20)     │  │  (HPA 1-5)    │
     └────────────────┘  └────────┬───────┘  └────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       ┌────────────┐       ┌──────────┐       ┌──────────┐
       │ PostgreSQL │       │  Redis   │       │  MinIO   │
       │ (PVC RWO)  │       │  (PVC)   │       │  (PVC)   │
       └────────────┘       └──────────┘       └──────────┘
```

Le chart Helm `infra/k8s/` expose 15 templates : `backend-deployment`, `backend-service`, `backend-hpa`, `web-deployment`, `web-service`, `worker-deployment`, `ingress`, `configmap`, `secrets`, `namespace`, `pdb`, `pvc-uploads`, `cronjob-backups`, `job-migrations`, `networkpolicy`. Trois fichiers de valeurs (`values-local.yaml`, `values-staging.yaml`, `values-prod.yaml`) paramètrent les ressources, replicas et secrets selon l'environnement.

Le déploiement local `Kind` (cluster `ecole-dev`) sert à valider le chart en CI (`.github/workflows/k8s-e2e.yml`) avant tout push vers staging.
