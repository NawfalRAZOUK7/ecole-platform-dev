# 🧪 Stratégie de Tests

## Vue d'ensemble

| Couche | Framework | Fichiers | Couverture |
|--------|-----------|----------|------------|
| Backend | Pytest + pytest-asyncio | 140+ | Services, repos, endpoints, sécurité, perf, contrats, PDF |
| Web | Vitest + MSW + Testing Library | 50+ | Pages, composants, services, contrats — **97.7% endpoints** |
| Mobile | Flutter test | 50+ unit/widget + 2 intégration | Widgets, providers, repositories, navigation |
| E2E | Playwright | 17 specs | Parcours utilisateur complets |
| K8s E2E | Kind + Helm | `.github/workflows/k8s-e2e.yml` | Validation chart + smoke tests sur cluster |

---

## Backend (Pytest)

### Organisation

```
backend/tests/
├── unit/                  # ~80 tests — services, schemas, utilitaires
├── integration/           # ~30 tests — endpoints API avec vraie DB
├── security/              # ~10 tests — RBAC, injection, auth bypass
├── performance/           # ~5 tests — benchmarks endpoints critiques
├── contract/              # ~5 tests — validation schemas API
├── edge/                  # ~3 tests — cas limites
├── factories/             # Factories pour générer des données de test
└── conftest.py            # Fixtures partagées (app, client, db, auth)
```

### Lancer les tests

```bash
# Tous les tests
make test

# Avec couverture
make test-cov

# Tests rapides uniquement
pytest -m "not slow" tests/

# Tests de sécurité
pytest -m "security" tests/

# Un module spécifique
pytest tests/unit/test_rewards_service.py -v
```

### Fixtures clés

- `app` — Instance FastAPI configurée pour les tests
- `client` — Client HTTP async (httpx.AsyncClient)
- `db` — Session DB de test avec rollback automatique
- `auth_headers(role)` — Headers JWT pour un rôle donné

---

## Frontend Web (Vitest)

### Organisation

```
web/tests/
├── unit/
│   ├── features/              # Tests de pages et composants fonctionnels
│   │   ├── AttendancePage.test.tsx
│   │   ├── StudentHomePage.test.tsx
│   │   ├── RewardsService.test.ts
│   │   ├── LevelBadge.test.tsx
│   │   ├── StreakCard.test.tsx
│   │   └── ... (16 fichiers)
│   ├── shared/                # Tests des composants UI partagés
│   │   ├── PlatformBridgeCard.test.tsx
│   │   ├── StatCard.test.tsx
│   │   ├── Badge.test.tsx
│   │   ├── DataTable.test.tsx
│   │   └── ... (10 fichiers)
│   ├── api-client.test.ts     # Client HTTP
│   └── auth-context.test.tsx  # Contexte d'authentification
├── contract/
│   └── api-contract.test.ts   # Validation du contrat API
├── utils/
│   ├── render.tsx             # Helper de rendu avec providers
│   ├── factories.ts           # Factories (createUser, createStudent, etc.)
│   └── mocks.ts               # MSW handlers + helpers
└── setup.ts                   # Configuration globale (MSW server, polyfills)
```

### Infrastructure de test

- **Vitest** — Runner rapide avec support JSX/TSX natif
- **jsdom** — Environnement navigateur simulé
- **MSW (Mock Service Worker)** — Interception des requêtes HTTP au niveau réseau
- **@testing-library/react** — Rendu orienté utilisateur (pas d'implémentation)
- **Factories** — `createUser()`, `createStudent()`, `createInvoice()`, etc.
- **renderWithProviders()** — Wrapping automatique (QueryClient, AuthContext, MemoryRouter, i18n)

### Lancer les tests

```bash
cd web

# Tous les tests
npm test

# Mode watch
npm run test:watch

# Avec couverture
npm run test:coverage

# Un fichier spécifique
npx vitest tests/unit/shared/PlatformBridgeCard.test.tsx
```

### Pattern de test

```tsx
// Exemple : test d'un composant avec MSW mock
import { screen } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { StudentHomePage } from '@/features/student/StudentHomePage';
import { renderWithProviders } from '../../utils/render';
import { apiResponse, server } from '../../utils/mocks';

describe('StudentHomePage', () => {
  it('displays XP and level stats', async () => {
    server.use(
      http.get('/api/v1/rewards/me', () =>
        apiResponse({ stars: 42, xp: 320, level: 3, streak_days: 5 })
      )
    );

    renderWithProviders(<StudentHomePage />, {
      user: { role: 'STD', full_name: 'Amine' },
    });

    expect(await screen.findByText('320')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
  });
});
```

---

## Couverture par fonctionnalité

| Fonctionnalité | Backend | Web | Mobile |
|---------------|---------|-----|--------|
| Authentification (login, 2FA, JWT) | ✅ Unit + Integration + Security | ✅ AuthContext tests | ✅ Auth flow |
| Présence | ✅ Service + API | ✅ AttendancePage | ✅ Widget |
| Carnet de notes | ✅ Service + API | ✅ GradebookPage | ✅ Widget |
| Factures | ✅ Service + API | ✅ InvoiceDetailPage | ✅ Widget |
| Budgets | ✅ Service + API | ✅ BudgetListPage | — |
| Récompenses (XP, étoiles, niveaux) | ✅ Service + API | ✅ RewardsService + LevelBadge + StreakCard | ✅ Provider |
| Page d'accueil élève | ✅ API | ✅ StudentHomePage | ✅ Screen |
| PlatformBridgeCard | — | ✅ 6 tests | ✅ Widget |
| Composants partagés | — | ✅ Badge, DataTable, FormField, Pagination, etc. | ✅ Widgets |
| Contrat API | ✅ Contract tests | ✅ api-contract.test | — |
| Sécurité RBAC | ✅ Security tests | — | — |
| Performance | ✅ Perf benchmarks | — | — |
| **PDF facture/reçu (v1.1)** | ✅ Integration (rendu, AR/FR, TVA) | — | — |
| **Programmes académiques (v1.1)** | ✅ Service + API + eligibility engine | ✅ ProgramsPage, ProgramVersionsPage, ProgramEquivalencesPage, EnrollmentsPage, EligibilityRulesPage, AssignProgramDialog, EligibilityCheckTile, StudentAcademicHistoryPage | ✅ Academic history screen |
| **Storage S3/MinIO (v1.1)** | ✅ Backend abstraction + scan ClamAV | ✅ `useSignedUrl`, `directUpload` | ✅ Direct upload widget |
| **Writing Workspace (v1.1)** | ✅ Service + API | ✅ WritingWorkspacePage | — |
| **Shared Review (v1.1)** | ✅ Service + API + ParentAlertService | ✅ SharedReviewPage, ReviewDetailPage | — |
| **K8s deployment (v1.1)** | — | — | — | (validation : workflow `k8s-e2e.yml`)

---

## Infrastructure de tests v1.1

### Backend
- Fixtures `pdf_generator`, `mock_clamav`, `signed_url_provider` ajoutées dans `conftest.py`
- Factories `program_version_factory`, `enrollment_factory`, `eligibility_rule_factory`
- Tests `testcontainers` pour MinIO et PostgreSQL en mode intégration

### Web
- Mocks MSW pour les nouveaux endpoints (programs, eligibility, uploads/initiate)
- Helper `renderWithProviders()` étendu pour les pages programmes
- 25 méthodes de service API ajoutées pour atteindre **97.7%** de couverture endpoints
- 13 mismatches HTTP (GET/POST/PUT/DELETE) corrigés

### Mobile
- `pump_helpers.dart` : helpers pour pumper un widget avec navigation + Riverpod
- `mock_repositories.dart` : doubles pour tous les repositories utilisés en widget tests
- `entity_factories.dart` : factories pour entités (User, Program, Enrollment, Reward, etc.)
- 30+ tests unitaires + widgets ajoutés sur les nouveaux modules

### Workflow K8s E2E
1. Démarre un cluster Kind dans le runner GitHub
2. `helm lint` + `helm template` du chart
3. `helm install` avec `values-local.yaml`
4. Attente readiness des pods (backend, web, postgres, redis, minio)
5. Smoke tests via `curl` sur les endpoints `/health`, `/api/v1/openapi.json`
6. Cleanup garanti via `trap`
