# Web Level 3 — Architecture Governance & Tooling

Add automated guardrails to enforce the FSD layer hierarchy, prevent architecture decay, and maintain code quality at scale through ESLint rules, dependency graphs, barrel exports, and CI checks.

---

## What L3 Adds to L2

L2 defines the folder structure and layer rules. L3 **automates their enforcement** so developers cannot accidentally violate them.

| Concern | L2 State | L3 Target |
|---------|---------|-----------|
| Import rules | Documented (markdown) | Enforced by ESLint |
| Barrel exports | Optional | Required with lint rules |
| Cross-feature imports | Manual review | Automated detection |
| Architecture drift | Discovered during refactors | Blocked in CI |
| New module creation | Copy-paste | Scaffolder templates |
| Dead code | Manual grep | Automated detection |

---

## 1. ESLint Import Boundaries

### Layer Enforcement Rule

Create a custom ESLint configuration or use `eslint-plugin-boundaries` to enforce:

```js
// .eslintrc.cjs — boundaries configuration
const layers = [
  { name: 'app', pattern: 'app/**' },
  { name: 'pages', pattern: 'pages/**' },
  { name: 'widgets', pattern: 'widgets/**' },
  { name: 'features', pattern: 'features/**' },
  { name: 'entities', pattern: 'entities/**' },
  { name: 'shared', pattern: 'shared/**' },
];

// Rules:
// pages     → widgets, features, entities, shared, app
// widgets   → features, entities, shared
// features  → entities, shared
// entities  → shared
// shared    → shared (only)
```

Example violations that would fail CI:

```ts
// BAD: entities importing from features
import { useLogin } from '@/features/auth/login';   // ❌ ERROR

// BAD: features importing from widgets
import { TopNavbar } from '@/widgets/top-navbar';    // ❌ ERROR

// BAD: pages importing from pages
import { AdminPage } from '@/pages/admin';          // ❌ ERROR

// BAD: entities importing from app
import { AuthContext } from '@/app/providers';       // ❌ ERROR

// GOOD: features importing from entities
import { UserAvatar } from '@/entities/user';        // ✅ OK

// GOOD: widgets importing from features
import { LoginForm } from '@/features/auth/login';  // ✅ OK
```

### Public API Enforcement

Enforce that consumers only import from `index.ts` (not deep paths):

```ts
// BAD: deep import
import { useLogin } from '@/features/auth/login/model/useLogin';  // ❌ ERROR

// GOOD: barrel import
import { useLogin } from '@/features/auth/login';                  // ✅ OK
```

---

## 2. Barrel Exports (index.ts) Governance

### Required Pattern

Every module MUST export its public API through `index.ts`:

```ts
// features/auth/login/index.ts
export { LoginForm } from './ui/LoginForm';
export { useLogin } from './model/useLogin';
export type { LoginPayload } from './api/login.api';
// Internal files like api/client-config.ts are NOT exported
```

### Lint Rule: No Reaching Into Internal Paths

```js
// .eslintrc
{
  rules: {
    'no-restricted-imports': ['error', {
      patterns: [
        // Block deep imports into any feature
        '@/features/*/*/*',
        // Block deep imports into entities
        '@/entities/*/*/*',
        // Block deep imports into widgets
        '@/widgets/*/*/*',
      ]
    }]
  }
}
```

**Exception:** Within a module, files can import from sibling folders freely:

```ts
// features/auth/login/model/useLogin.ts
import { loginApi } from '../api/login.api';   // ✅ OK (same module)
import { LoginForm } from '../ui/LoginForm';   // ✅ OK (same module)
```

---

## 3. Dependency Graph Visualization

### Tool: `dependency-cruiser`

Generate a visual dependency graph to audit the architecture:

```bash
# Install
npm install --save-dev dependency-cruiser

# Generate graph
npx depcruise src --include-only "^src" --output-type dot | dot -T svg > dependency-graph.svg
```

### Expected Graph (L2/L3)

```
        ┌──────────┐
        │    app   │
        └────┬─────┘
             │
        ┌────┴─────┐
        │  pages   │
        └────┬─────┘
             │
      ┌──────┴──────┐
      │   widgets   │
      └──────┬──────┘
             │
      ┌──────┴──────┐
      │   features  │
      └──────┬──────┘
             │
      ┌──────┴──────┐
      │  entities   │
      └──────┬──────┘
             │
      ┌──────┴──────┐
      │   shared    │
      └─────────────┘
```

**No arrows should skip layers** (e.g. pages → entities directly) and **no upward arrows** (e.g. entities → features).

### CI Gate

```bash
# In CI pipeline
npx depcruise src --config .dependency-cruiser.js
# Fails if any forbidden import is detected
```

---

## 4. Module Scaffolder

### Script: `scripts/create-module.js`

Automate creation of new modules with correct structure:

```bash
# Usage
node scripts/create-module.js --layer features --name create-invoice

# Creates:
src/features/create-invoice/
├── api/
│   └── create-invoice.api.ts    # with stub api call
├── model/
│   ├── useCreateInvoice.ts      # with stub React Query hook
│   └── create-invoice.schema.ts # with zod stub
├── ui/
│   └── CreateInvoiceForm.tsx    # with stub component
├── lib/
│   └── (empty)
└── index.ts                     # with correct exports
```

### Prevents Copy-Paste Drift

Developers no longer copy existing modules (risking wrong patterns, leftover names). The scaffolder guarantees:
- Correct folder structure
- Consistent naming conventions
- Required `index.ts` barrel
- Type-safe stubs

---

## 5. Architectural Compliance Checks in CI

### GitHub Actions Workflow

```yaml
# .github/workflows/architecture-check.yml
name: Architecture Compliance
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      
      # 1. ESLint boundary check
      - run: npx eslint src --max-warnings 0
      
      # 2. Dependency graph check
      - run: npx depcruise src --config .dependency-cruiser.js
      
      # 3. Verify all modules have index.ts
      - run: node scripts/verify-barrels.js
      
      # 4. Detect deep imports (fallback)
      - run: |
          if grep -r "from '@/features/.*/.*/.*'" src --include="*.ts" --include="*.tsx"; then
            echo "Deep imports detected! Use barrel exports."
            exit 1
          fi
```

### Script: `scripts/verify-barrels.js`

Ensures every folder in `features/`, `entities/`, `widgets/`, `pages/` has an `index.ts`:

```js
const fs = require('fs');
const path = require('path');

const layers = ['features', 'entities', 'widgets', 'pages'];
let errors = 0;

for (const layer of layers) {
  const layerPath = path.join('src', layer);
  if (!fs.existsSync(layerPath)) continue;
  
  const modules = fs.readdirSync(layerPath, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => d.name);
  
  for (const mod of modules) {
    const indexPath = path.join(layerPath, mod, 'index.ts');
    if (!fs.existsSync(indexPath)) {
      console.error(`Missing index.ts: src/${layer}/${mod}/`);
      errors++;
    }
  }
}

if (errors > 0) process.exit(1);
console.log('All modules have index.ts barrels ✓');
```

---

## 6. Dead Code Detection

### Tool: `knip`

```bash
npm install --save-dev knip
npx knip
```

Detects:
- Exported symbols never imported
- Unused dependencies
- Unused files
- Unused type exports

### CI Gate

```bash
npx knip --production
# Fails if dead exports found in production code
```

---

## 7. Circular Dependency Prevention

### ESLint Rule

```js
// Using eslint-plugin-import
{
  plugins: ['import'],
  rules: {
    'import/no-cycle': ['error', { maxDepth: Infinity }]
  }
}
```

### Architecture-Level Prevention

The FSD layer hierarchy (entities → features → widgets → pages) inherently prevents most circular dependencies because arrows only flow downward. L3 enforces this:

```
entities/user → features/auth/login → widgets/top-navbar → pages/dashboard
     ↑                                              ↘
     └──────────────── ❌ NO CYCLE POSSIBLE (ESLint blocks)
```

---

## 8. Testing Strategy Per Layer

| Layer | Test Type | Rationale |
|-------|-----------|-----------|
| `entities` | Unit tests for mappers, types | Pure data, no UI |
| `features` | Hook tests (React Testing Library) | User actions, async logic |
| `widgets` | Component tests (RTL) | Composition logic |
| `pages` | E2E or minimal smoke tests | Thin glue, not much to test |
| `shared` | Unit + visual regression | Generic components need coverage |

### Co-location Rule

Tests live next to the file they test:

```
features/auth/login/
├── api/
│   ├── login.api.ts
│   └── login.api.test.ts        # ← co-located
├── model/
│   ├── useLogin.ts
│   └── useLogin.test.ts         # ← co-located
└── ui/
    ├── LoginForm.tsx
    └── LoginForm.test.tsx        # ← co-located
```

---

## 9. Documentation Enforcement

### Module README Template

Every `features/*/` and `entities/*/` folder must include a `README.md`:

```markdown
# features/auth/login

## Responsibility
Handles user authentication via email/password.

## Public API
- `LoginForm` — UI component
- `useLogin` — React Query mutation hook
- `type LoginPayload` — input type

## Dependencies
- entities/user (for User type)
- shared/api (for core HTTP client)

## No-Import Zones
- widgets/ (widgets consume this feature, not vice versa)
- pages/ (pages consume this feature, not vice versa)
```

### CI Check

```bash
# Verify README.md exists in each module
for dir in src/features/*/ src/entities/*/; do
  if [ ! -f "$dir/README.md" ]; then
    echo "Missing README: $dir"
    exit 1
  fi
done
```

---

## 10. Implementation Phases

### Phase 1 — ESLint Setup (Week 1)
1. Install `eslint-plugin-boundaries` or configure custom rules
2. Define layer hierarchy in `.eslintrc.cjs`
3. Run on existing codebase, fix violations (or grandfather with comments)
4. Add to pre-commit hook (`lint-staged`)

### Phase 2 — Dependency Cruiser (Week 1–2)
1. Install `dependency-cruiser`
2. Configure `.dependency-cruiser.js` with layer rules
3. Generate initial dependency graph
4. Add to CI pipeline

### Phase 3 — Barrel Enforcement (Week 2)
1. Create `scripts/verify-barrels.js`
2. Ensure every module has `index.ts`
3. Add `no-restricted-imports` rule for deep paths
4. Fix all deep imports in codebase

### Phase 4 — Scaffolder (Week 3)
1. Create `scripts/create-module.js`
2. Add to `package.json` scripts: `"create:module": "node scripts/create-module.js"`
3. Document usage in `CONTRIBUTING.md`

### Phase 5 — CI Integration (Week 3–4)
1. Create `.github/workflows/architecture-check.yml`
2. Add `knip` for dead code detection
3. Add circular dependency check
4. Add README verification

### Phase 6 — Team Onboarding (Ongoing)
1. Update `CONTRIBUTING.md` with architecture rules
2. Run lunch-and-learn on FSD
3. Add architecture decision record (ADR) for the migration

---

## Effort Summary

| Item | Files/Config | Effort |
|------|-------------|--------|
| ESLint boundaries | 1 config + fixes | Medium |
| Dependency cruiser | 1 config + CI | Low |
| Barrel verification | 1 script + fixes | Medium |
| Module scaffolder | 1 script + templates | Low |
| CI workflow | 1 YAML | Low |
| Dead code (knip) | 1 config + cleanup | Medium |
| Circular dependency | ESLint rule | Low |
| README enforcement | 1 script | Low |
| **Total** | **~10 config/script files** | **Medium** |

L3 is primarily **tooling and automation**, not file moves like L1/L2. The main work is configuring rules and cleaning up existing violations.
