# META-PROMPT 2: Execute Refactoring

> Copy-paste this ENTIRE prompt into the SAME session as META-PROMPT 1.
> The AI already has context from META-PROMPT 1.
> This prompt tells the AI to extract and execute each batch from REFACTOR_PROMPTS.md automatically.

---

```md
You have already read and understood the full project context from the previous prompt. Now it's time to execute the refactoring.

YOUR TASK: Execute ALL refactoring batches from REFACTOR_PROMPTS.md, one by one, in order. You do NOT need me to copy-paste each prompt — you already have the file. Extract each batch's instructions and execute them directly.

EXECUTION ORDER (follow REFACTOR_PROMPTS.md exactly):

PHASE 1 — BACKEND:
1. Pre-Requisite (shared utilities — BaseRepository, request_utils.py, wire existing repos)
2. Batch 1 — Auth & Audit (extract AuthRepository, AuditRepository)
3. Batch 2 — Billing & Payments (extract BillingRepository)
4. Batch 3 — ERP: Classes, Attendance, Timetable (extract ERPRepository)
5. Batch 4 — LMS: Content, Assignments, Quizzes (extract LMSRepository, QuizRepository)
6. Batch 5 — Communication, Progress & Analytics (extract remaining repos)
7. Batch 6 — Admin, Profiles, GDPR & remaining (extract final repos)
8. Post-Refactor Backend Validation

PHASE 2 — FIX MISSING FEATURES:
9. Phase 14 gaps: Create PDF Jinja2 templates (student card, class summary, attendance, billing) with Arabic RTL support. Add weekly analytics aggregation.
10. Phase 15 gaps: Add holiday CRUD endpoints for ADM. Add event type color coding.
11. Phase 16 gaps: Implement ResourcesPage.tsx properly. Add document expiry notifications. Add bulk document operations (multi-select → ZIP download, bulk delete).

PHASE 3 — WEB FRONTEND:
12. Web Pre-Requisite (install React Query, QueryClientProvider, useQueryDefaults)
13. Web Batch 1 — Notifications, Feed, Calendar (services + hooks)
14. Web Batch 2 — Teacher & Admin (services + hooks)
15. Web Batch 3 — All remaining features (services + hooks)

PHASE 4 — INFRA SECURITY:
16. Infra Security hardening (.env, Redis, PostgreSQL, Grafana, Alertmanager)

RULES FOR EACH BATCH:

1. Before starting a batch, re-read the specific batch instructions from REFACTOR_PROMPTS.md.
2. Read ALL files listed in that batch's "READ THESE FILES" section before writing any code.
3. Follow ARCHITECTURE_STANDARD.md patterns EXACTLY — no shortcuts, no alternatives.
4. RBAC STANDARDIZATION: For every router you touch in backend batches, check if it uses hardcoded role checks (`if role == "ADM"`) and replace them with `@requires_permission(PERM_CONSTANT)`. If a permission constant doesn't exist, create it in `backend/app/core/permissions.py` and add it to the appropriate roles.
5. After completing each batch, update REFACTOR_CHECKLIST.md — mark completed items with [x].
6. After each batch, run the verification step:
   - Backend: `cd backend && python -c "from app.repositories import *; print('OK')"`
   - Web: `cd web && npm run build`
   - Mobile: `cd mobile && flutter analyze` (only if mobile files were touched)
7. After verification passes, tell me what files were changed (list them) so I can review and commit myself.
8. Then immediately move to the next batch — do NOT wait for me.
9. NEVER run any git command. No git add, no git commit, no git push. I handle git myself.

IF YOU HIT A PROBLEM:
- If a batch fails verification, fix the issue before moving to the next batch
- If you find a file that doesn't exist (e.g., a web page referenced in the prompt), note it and skip that specific file
- If you run out of context, save your progress in REFACTOR_CHECKLIST.md and tell me which batch to resume from

IMPORTANT — DO NOT:
- Run ANY git command (no git add, git commit, git push, git stash, git checkout, or any other git operation). I will handle all git operations myself after reviewing your changes.
- Change any API endpoint URLs or response formats
- Change any model or schema
- Delete any existing test
- Change mobile architecture (it's already correct)
- Skip RBAC standardization on any router you touch

START NOW with Phase 1, Batch 0 (Pre-Requisite).
```
