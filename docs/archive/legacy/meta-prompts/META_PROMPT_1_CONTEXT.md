# META-PROMPT 1: Context Understanding

> Copy-paste this ENTIRE prompt into a new Claude Code or Codex session.
> Open folder: `ecole-platform-dev/` (NOT the parent folder)
> This prompt makes the AI understand the full project before any work begins.

---

```md
I'm about to refactor "École Platform" — an EdTech SaaS for K-12 schools in Morocco. This is a monorepo with FastAPI backend, React web, and Flutter mobile. Phases 0-16 are implemented. I need to do a full-stack architecture refactor.

BEFORE DOING ANYTHING, you must read and deeply understand these files. Read them IN THIS EXACT ORDER. Do NOT skip any file. Do NOT start writing code until you have read ALL of them.

STEP 1 — Read the architecture standard (THE MOST IMPORTANT FILE):
- Read ARCHITECTURE_STANDARD.md — This defines the exact patterns for backend (3-tier), web (React Query hooks), mobile (Clean Architecture), and infra (security). Every single change you make MUST follow these patterns exactly. This is non-negotiable.

STEP 2 — Read the refactor plan:
- Read REFACTOR_PROMPTS.md — This contains ALL the individual refactor prompts organized by phase and batch. You will execute these one by one in META-PROMPT 2.
- Read REFACTOR_CHECKLIST.md — This is the tracking document. After each batch, you will update the checkboxes.

STEP 3 — Understand the project context:
- Read CLAUDE_PROMPTS.md (phases 0-12 specifications) — Just the phase headers and summaries, NOT the full prompts. Understand what was built.
- Read CLAUDE_PROMPTS_2.md (phases 13-18 specifications) — Same, understand phases 13-16 which are implemented.
- Read DEV_PHASES.md and DEV_PHASES_2.md if they exist — Understand the feature roadmap.
- Read TODO_GENERAL.md and TODO_GENERAL_2.md if they exist — Understand what's done vs pending.

STEP 4 — Understand the current codebase:
- List all files in backend/app/repositories/ — These are the existing repositories (4 from Codex).
- List all files in backend/app/services/ — These are the services to refactor.
- List all files in backend/app/api/v1/ — These are the routers.
- List all files in backend/app/core/ — These are shared utilities.
- Read backend/app/core/permissions.py — Understand the RBAC system (110 permissions, 8 roles).
- Read backend/app/core/dependencies.py — Understand how authentication and DI work.
- Read web/src/main.tsx — Current web entry point.
- Read web/src/services/api/client.ts — Current API client.
- List all directories in web/src/features/ — Current feature structure.
- List all directories in mobile/lib/features/ — Current mobile structure.

STEP 5 — Understand the known issues:
- The backend has mixed architecture: Phases 0-12 use 2-tier (Router→Service with embedded SQL), Phases 13-16 use 3-tier (Router→Service→Repository). We're standardizing everything to 3-tier.
- The web has no React Query — pages directly call api.get() with useState/useEffect. We're adding React Query with custom hooks.
- RBAC is inconsistent: Phases 14-16 use @requires_permission(PERM_CONSTANT), older phases use hardcoded role checks. We're standardizing to the permission system.
- Infra has security issues: .env in git, Redis without auth, hardcoded passwords.
- Phase 14 is missing PDF templates and Arabic RTL report support.
- Phase 16 ResourcesPage.tsx is a 137-byte stub, document expiry notifications are missing, bulk document operations are missing.

STEP 6 — Confirm understanding:
After reading everything, provide a summary of:
1. How many backend services need refactoring (those with embedded SQL)
2. How many web features need React Query hooks
3. How many missing features need to be implemented
4. The total number of batches to execute from REFACTOR_PROMPTS.md
5. Any concerns or blockers you see

Do NOT start any code changes. Just read, understand, and confirm.

CRITICAL RULE: NEVER run any git command throughout this entire session and any future sessions. No git add, git commit, git push, git stash, git checkout, git reset, or any other git operation. I will handle ALL git operations myself after reviewing changes. This rule applies to ALL prompts that follow.
```
