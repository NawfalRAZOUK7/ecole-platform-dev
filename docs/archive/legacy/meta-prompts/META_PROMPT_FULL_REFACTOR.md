# Meta Prompt: Full Backend Refactor — Ecole Platform

> Single unified meta prompt that chains OOP refactoring (Phases A-F), Feature Enhancements (Phases A-E), and Model/Role Enhancements (Phases MR-A through MR-F) into one execution flow.

---

## Step 1: Context Loading

Read these files to understand the project:

1. `backend/app/models/__init__.py` — all model exports
2. `backend/app/repositories/__init__.py` — all repository exports
3. `backend/app/core/dependencies.py` — dependency injection setup
4. `backend/app/core/permissions.py` — RBAC system (110 permissions, 8 roles)
5. `backend/app/api/v1/router.py` — all registered routes
6. `ARCHITECTURE_STANDARD.md` — existing 3-tier architecture patterns

## Step 2: Read Architecture Standards

Read these CAREFULLY — they are your blueprints:

1. `OOP_ARCHITECTURE_STANDARD.md` — ALL OOP patterns with code examples:
   - Part A: Unit of Work
   - Part B: Value Objects (MoroccanGrade, Money, TypedId, RoleSet)
   - Part C: ProfileLoader (User/Role composition with all 8 roles)
   - Part D: Domain Events + Delivery Strategy
   - Part E: Evaluatable Protocol
   - Part F: LMS Service Splitting

2. `ENHANCEMENT_ARCHITECTURE.md` — ALL feature enhancement specs:
   - Section A: IAM (Impersonation, Login History, Session Limits)
   - Section B: LMS (Rubrics, Gradebook, Question Bank, Late Penalties)
   - Section C: Billing/ERP (Sibling Discounts, Late Fees, Payment Plans, Attendance Analytics, Timetable)
   - Section D: Comms/Docs (Message Attachments, Search, Versioning, Report Scheduling, AI Provider)

## Step 3: Read Current Service Layer

Scan these to understand what you'll be modifying:

1. List all files in `backend/app/services/`
2. Read the first 50 lines of `backend/app/services/lms.py`
3. Read `backend/app/services/notification_hub.py`
4. Read `backend/app/services/auth.py` first 100 lines
5. Read `backend/app/models/iam.py`

## Step 4: Confirm Understanding

After reading, confirm:
- You understand the 3-tier pattern (Router → Service → Repository) already in place
- You understand that OOP refactoring adds WITHIN the service layer, not replacing it
- You understand the new domain/ directory structure
- You know which services perform write operations (need UnitOfWork)
- You understand all 15 feature enhancements and their model/service/endpoint requirements

Once confirmed, say: **"Context loaded. Ready to execute full refactor."**

---

## Step 5: Execute Prompts

Open the two prompt files and execute prompts in this EXACT order:

### Part 1: OOP Refactor (from OOP_REFACTOR_PROMPTS.md)

| Order | Prompt | Description |
|-------|--------|-------------|
| 1 | OOP-A1 | Value Objects |
| 2 | OOP-A2 | UnitOfWork (core services) |
| 3 | OOP-A3 | UnitOfWork (all services) |
| 4 | OOP-B1 | Profile Models + Migration G26 |
| 5 | OOP-B2 | ProfileLoader |
| 6 | OOP-C1 | Domain Event Classes |
| 7 | OOP-C2 | Delivery Strategies |
| 8 | OOP-C3 | Wire Events into Services |
| 9 | OOP-D1 | Protocols + Grading Strategies |
| 10 | OOP-D2 | StudentWork Service |
| 11 | OOP-E1 | Split lms.py into sub-services |
| 12 | OOP-F1 | OOP Validation |

### Part 2: Feature Enhancements (from ENHANCEMENT_PROMPTS.md)

| Order | Prompt | Description |
|-------|--------|-------------|
| 13 | ENH-A1 | IAM: Impersonation + Login History + Session Limits |
| 14 | ENH-B1 | LMS: Rubric Models + Migration G28a |
| 15 | ENH-B2 | LMS: Rubric Service + Router |
| 16 | ENH-B3 | LMS: Weighted Gradebook + GPA |
| 17 | ENH-B4 | LMS: Question Bank + Late Penalties |
| 18 | ENH-C1 | Billing: Sibling Discounts + Late Fees + Payment Plans |
| 19 | ENH-C2 | ERP: Attendance Analytics + Alerts |
| 20 | ENH-C3 | ERP: Timetable Auto-Generation |
| 21 | ENH-D1 | Comms/Docs: Attachments + Search + Versioning |
| 22 | ENH-D2 | Reports: Scheduling + AI Provider Abstraction |
| 23 | ENH-E1 | Enhancement Validation |

### Execution Rules for Each Prompt

For each prompt:
1. Read the prompt text carefully from its source file.
2. Re-read the relevant section of the architecture document as referenced.
3. Execute ALL steps listed in the prompt.
4. Verify the changes work (imports resolve, no syntax errors).
5. Update `FULL_REFACTOR_CHECKLIST.md` — mark completed items with [x].
6. Tell me what files were changed (list them) so I can review and commit myself.
7. Move to the next prompt only after the current one is fully complete.
8. If a prompt references files that don't exist yet (from a previous prompt), check that the previous prompt was executed first.

### Part 3: Model & Role Enhancements (from MODEL_ROLE_PROMPTS.md)

| Order | Prompt | Description |
|-------|--------|-------------|
| 24 | MR-A1 | School Model + SchoolScopedMixin + SoftDeleteMixin |
| 25 | MR-B1 | Helper Properties on All Models |
| 26 | MR-B2 | __repr__ Methods on All Models |
| 27 | MR-B3 | SQLAlchemy Validators |
| 28 | MR-C1 | PG Enum Types + Column Conversions |
| 29 | MR-D1 | DIR + SUP + CONTENT_MGR Permissions + Role Hierarchy |
| 30 | MR-E1 | ABAC Helpers + PAR/STD Validation |
| 31 | MR-E2 | Replace Hardcoded Role Strings with Permissions |
| 32 | MR-F1 | Full Model & Role Validation |

### After Each Prompt

Say: **"Prompt [ID] complete. Files changed: [list]. Ready for next prompt."**

Then **wait for my confirmation** before proceeding.

---

## Step 6: Final Verification

After ALL 32 prompts are complete, run the verification checks from:
1. `META_PROMPT_OOP_3_VERIFY.md` — 10 OOP verification checks
2. `ENHANCEMENT_PROMPTS.md` → ENH-E1 — 18 enhancement verification checks
3. `MODEL_ROLE_PROMPTS.md` → MR-F1 — 12 model/role verification checks

Report results in a single PASS/FAIL summary table.

---

## CRITICAL RULES — READ BEFORE STARTING

1. **NEVER run any git command.** No git add, commit, push, stash, checkout, or any other git command. I handle all git operations manually.
2. **Do NOT skip any prompt** or run them out of order.
3. **Do NOT change method signatures** or router response shapes of existing endpoints.
4. **Do NOT delete existing files** unless the prompt explicitly says to.
5. **Use UnitOfWork** for ALL write operations in services.
6. **Use Value Objects** (MoroccanGrade, Money) wherever grades or amounts are calculated.
7. **Follow 3-tier pattern** for all new code: Router → Service → Repository.
8. **AI Provider**: MockProvider must return realistic, useful responses. ClaudeProvider should be fully coded but inactive (activated by setting AI_PROVIDER=claude in .env).
9. **Migrations**: G26 (OOP profiles), G27a-b (IAM + Billing), G28a-d (LMS), G29a-b (ERP), G30a-c (Comms/Docs), G31a-b (School + Enums).
10. **SchoolScopedMixin** replacement must not change actual DB columns — only Python declarations.
11. **ABAC helpers** must not break existing role-scoped queries — augment, don't replace.

---

## Reference Files

| File | Purpose |
|------|---------|
| `OOP_ARCHITECTURE_STANDARD.md` | OOP pattern blueprints with code examples |
| `OOP_REFACTOR_PROMPTS.md` | 12 OOP execution prompts (A1-F1) |
| `ENHANCEMENT_ARCHITECTURE.md` | Feature enhancement design specs |
| `ENHANCEMENT_PROMPTS.md` | 11 enhancement execution prompts (A1-E1) |
| `MODEL_ROLE_ARCHITECTURE.md` | Model OOP + Role/Permission design specs |
| `MODEL_ROLE_PROMPTS.md` | 9 model/role execution prompts (MR-A1 to MR-F1) |
| `FULL_REFACTOR_CHECKLIST.md` | Unified progress tracking (~170 items) |
| `META_PROMPT_OOP_3_VERIFY.md` | OOP verification checks |
| `ARCHITECTURE_STANDARD.md` | Existing 3-tier architecture reference |
