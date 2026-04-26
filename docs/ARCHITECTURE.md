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

23 modules de modèles organisés en 6 groupes de migration :

| Groupe | Modules | Tables principales |
|--------|---------|-------------------|
| **G1 — IAM** | `iam.py` | users, sessions, memberships, invitations, totp_secrets |
| **G2 — ERP** | `erp.py`, `school.py`, `levels.py` | schools, classes, enrollments, timetable_slots, levels |
| **G3 — LMS** | `lms.py`, `skill_passport.py` | content_items, quizzes, questions, submissions, rubrics |
| **G4 — COM** | `com.py`, `calendar.py` | messages, threads, notifications, announcements, events |
| **G5 — Billing** | `billing.py`, `budget.py`, `financial_health.py` | invoices, payments, fee_structures, budgets |
| **G6 — Audit** | `audit.py`, `men_compliance.py`, `reporting.py` | audit_events, feature_toggles, compliance_checks |

Groupes additionnels : `games.py`, `rewards.py`, `documents.py`, `micro_school.py`, `ai.py`, `sync_queue.py`.

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
