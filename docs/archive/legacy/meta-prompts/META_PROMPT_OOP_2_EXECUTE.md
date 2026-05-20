# Meta Prompt OOP-2: Execute OOP Refactor

> Run this prompt AFTER META_PROMPT_OOP_1_CONTEXT.md has been loaded.

---

You have already loaded the project context and read OOP_ARCHITECTURE_STANDARD.md.

## Execution Instructions

1. Open `OOP_REFACTOR_PROMPTS.md`.
2. Execute each prompt **in order**, starting from OOP-A1.
3. For each prompt:
   a. Read the prompt text carefully.
   b. Re-read the relevant section of `OOP_ARCHITECTURE_STANDARD.md` as referenced.
   c. Execute ALL steps listed in the prompt.
   d. Verify the changes work (imports resolve, no syntax errors).
   e. Update `OOP_REFACTOR_CHECKLIST.md` — mark completed items with [x].
   f. Tell me what files were changed (list them) so I can review and commit myself.
4. Move to the next prompt only after the current one is fully complete.
5. If a prompt references files that don't exist yet (from a previous prompt), check that the previous prompt was executed first.

## Execution Order

Phase OOP-A (Foundation):
1. OOP-A1: Value Objects
2. OOP-A2: UnitOfWork (core)
3. OOP-A3: UnitOfWork (all services)

Phase OOP-B (Profiles):
4. OOP-B1: Profile Models + Migration
5. OOP-B2: ProfileLoader

Phase OOP-C (Events):
6. OOP-C1: Domain Event Classes
7. OOP-C2: Delivery Strategies
8. OOP-C3: Wire Events into Services

Phase OOP-D (Evaluatable):
9. OOP-D1: Protocols + Grading Strategies
10. OOP-D2: StudentWork Service

Phase OOP-E (LMS Split):
11. OOP-E1: Split lms.py

Phase OOP-F (Validation):
12. OOP-F1: Full Validation

## IMPORTANT — DO NOT:
- Skip any prompt
- Run prompts out of order
- Change method signatures or router response shapes
- Delete existing files without the prompt explicitly saying to
- Run ANY git command (no git add, commit, push, stash, checkout, or any other git command)

## After Each Prompt:
Tell me: "Prompt OOP-XX complete. Files changed: [list]. Ready for next prompt."
Then wait for my confirmation before proceeding.
