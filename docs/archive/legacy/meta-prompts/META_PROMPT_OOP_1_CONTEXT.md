# Meta Prompt OOP-1: Context Understanding

> Run this prompt FIRST in a new Claude Code or Codex session before executing OOP refactor prompts.

---

You are about to perform an OOP (Object-Oriented Programming) refactoring of the Ecole Platform backend.

## Step 1: Read Project Structure

Read these files to understand the project:

1. `backend/app/models/__init__.py` — all model exports
2. `backend/app/repositories/__init__.py` — all repository exports
3. `backend/app/core/dependencies.py` — dependency injection setup
4. `backend/app/core/permissions.py` — RBAC system (110 permissions, 8 roles)
5. `backend/app/api/v1/router.py` — all registered routes
6. `ARCHITECTURE_STANDARD.md` — existing 3-tier architecture patterns

## Step 2: Read OOP Standards

Read these files CAREFULLY — they are your blueprint:

1. `OOP_ARCHITECTURE_STANDARD.md` — ALL OOP patterns with code examples:
   - Part A: Unit of Work
   - Part B: Value Objects (MoroccanGrade, Money, TypedId, RoleSet)
   - Part C: ProfileLoader (User/Role composition with all 8 roles)
   - Part D: Domain Events + Delivery Strategy (communication decoupling)
   - Part E: Evaluatable Protocol (Quiz/Assignment/Assessment unification)
   - Part F: LMS Service Splitting (76KB → 5 sub-services)
2. `OOP_REFACTOR_PROMPTS.md` — the execution prompts you will run
3. `OOP_REFACTOR_CHECKLIST.md` — progress tracking

## Step 3: Read Current Service Layer

Scan these to understand what you'll be modifying:

1. List all files in `backend/app/services/` — note the largest ones
2. Read the first 50 lines of `backend/app/services/lms.py` — see current structure
3. Read `backend/app/services/notification_hub.py` — this is what Domain Events replaces
4. Read `backend/app/services/auth.py` first 100 lines — see current register/login pattern
5. Read `backend/app/models/iam.py` — current User + Profile models

## Step 4: Confirm Understanding

After reading, confirm:
- You understand the 3-tier pattern (Router → Service → Repository) already in place
- You understand that OOP refactoring adds WITHIN the service layer, not replacing it
- You understand the new domain/ directory structure
- You know which services perform write operations (need UnitOfWork)

Once confirmed, say: "Context loaded. Ready to execute OOP refactor prompts."

---

CRITICAL RULE: NEVER run any git command throughout this entire session and any future sessions. No git add, commit, push, stash, checkout, or any other git command. The user handles all git operations manually.
