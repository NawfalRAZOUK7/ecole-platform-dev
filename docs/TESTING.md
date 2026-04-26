# 🧪 Stratégie de Tests

## Vue d'ensemble

| Couche | Framework | Fichiers | Couverture |
|--------|-----------|----------|------------|
| Backend | Pytest + pytest-asyncio | 133 | Services, repos, endpoints, sécurité, perf |
| Web | Vitest + MSW + Testing Library | 27 | Pages, composants, services, contrats |
| Mobile | Flutter test | Widget & unit tests | Widgets critiques |
| E2E | Playwright | Via CI workflow | Parcours utilisateur complets |

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
