# Contributing to École Platform

Thank you for your interest in contributing! This document outlines the conventions and workflows used in this project.

---

## Git Workflow

We follow **GitHub Flow** with feature branches:

```
main (stable, deployable)
 └── feature/IAM-login-2fa        ← feature branch
 └── fix/attendance-null-check    ← bugfix branch
 └── refactor/rewards-service     ← refactor branch
```

### Branch Naming

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<module>-<description>` | `feature/rewards-leaderboard` |
| Bug fix | `fix/<module>-<description>` | `fix/auth-token-refresh` |
| Refactor | `refactor/<module>-<description>` | `refactor/gradebook-queries` |
| Documentation | `docs/<description>` | `docs/api-reference` |
| Infrastructure | `infra/<description>` | `infra/k8s-hpa-config` |
| Test | `test/<module>-<description>` | `test/rewards-service-unit` |

### Rules
- Always branch from `main`
- Keep branches short-lived (1-3 days max)
- Delete branch after merge

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

### Types

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code refactoring (no feature change) |
| `test` | Adding or updating tests |
| `docs` | Documentation changes |
| `style` | Formatting, linting (no logic change) |
| `perf` | Performance improvement |
| `ci` | CI/CD pipeline changes |
| `chore` | Maintenance tasks (deps, config) |
| `build` | Build system changes |

### Scopes

| Scope | Applies to |
|-------|-----------|
| `backend` | Backend API |
| `web` | React frontend |
| `mobile` | Flutter app |
| `infra` | Docker, K8s, CI |
| `db` | Database, migrations |
| Module name | e.g., `rewards`, `auth`, `attendance` |

### Examples

```
feat(rewards): add class leaderboard endpoint
fix(auth): handle expired refresh token gracefully
refactor(backend): extract pagination into shared utility
test(web): add PlatformBridgeCard unit tests
docs: update API reference with gamification endpoints
ci: add web E2E workflow with Playwright
chore(deps): bump FastAPI to 0.111
```

---

## Pull Request Convention

### Title
Same format as commit: `type(scope): description`

### Description Template

```markdown
## Summary
Brief description of what this PR does.

## Changes
- Added/Modified/Removed X
- Added/Modified/Removed Y

## Testing
- [ ] Unit tests added/updated
- [ ] Manual testing done
- [ ] Existing tests pass

## Screenshots (if UI changes)
[Attach screenshots or screen recordings]
```

### Rules
- Keep PRs focused (one feature/fix per PR)
- Ensure CI passes before requesting review
- Squash merge to keep history clean
- Reference related issues: `Closes #42`

---

## Code Style

### Backend (Python)

- **Linter**: Ruff (replaces flake8 + isort + black)
- **Type checker**: MyPy (strict mode)
- **Formatter**: Ruff format
- **Line length**: 100 characters

```bash
# Check
make lint

# Auto-fix
make lint-fix
```

### Frontend Web (TypeScript)

- **Linter**: ESLint with TypeScript rules
- **Formatter**: Prettier
- **Line length**: 100 characters

```bash
cd web
npm run lint
npm run format
```

### Mobile (Dart)

- **Linter**: dart analyze with recommended rules
- **Formatter**: dart format

```bash
cd mobile
flutter analyze
dart format .
```

---

## Testing

### Before submitting a PR

```bash
# Backend
make test

# Web
cd web && npm test

# Mobile
cd mobile && flutter test
```

### Test file naming
- Backend: `test_<module>.py` in `tests/unit/` or `tests/integration/`
- Web: `<Component>.test.tsx` in `tests/unit/features/` or `tests/unit/shared/`
- Mobile: `<widget>_test.dart` in `test/`

---

## Project Structure Rules

1. **Feature isolation**: each feature module should be self-contained (components + hooks + services + types)
2. **No circular imports**: features should not import from each other directly — use shared modules
3. **API consistency**: all endpoints return the standard `{ data, meta }` or `{ error }` format
4. **RTL support**: all new UI components must work in RTL mode (Arabic is the primary language)
5. **i18n**: all user-facing strings must go through the translation system (never hardcode text)

---

## Getting Help

- Check existing [documentation](docs/README.md)
- Review the [API Reference](docs/API-REFERENCE.md)
- Look at existing code for patterns and conventions
