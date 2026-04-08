# Ecole Platform — General Prompts (Analyze, Execute-All, Verify)

> Generated: 2026-04-06
> These are meta-prompts: they orchestrate the detailed prompts in WEB-FRONTEND-PROMPTS.md
> Compatible with: Codex, Claude Code, Cursor, Aider, or any AI coding tool

---

## 1. ANALYZE — Full Codebase Analysis Before Starting

> Run this FIRST to get a baseline understanding of the current state.

```
ROLE: You are a senior frontend architect analyzing a React 18 + TypeScript codebase.

PROJECT: ecole-platform-dev/web/
  - React 18.3.1 + Vite 6.0 + TypeScript 5.6 (strict)
  - TanStack React Query v5, React Router v6, i18next, Recharts
  - Custom CSS (no Tailwind), CSS variables for theming
  - i18n: French (default), Arabic (RTL), English
  - 10 RBAC roles: SYS, SUP, ADM, DIR, TCH, EDUCATOR, PAR, STD, CONTENT_MGR, PUBLIC

ANALYZE AND REPORT:

1. ARCHITECTURE AUDIT
   - Count total .tsx and .ts files in src/
   - Count total lines of code
   - List all feature directories in src/features/ with file counts
   - Identify the service pattern (Page → Hook → Service → API)
   - Check if barrel files (index.ts) exist for clean imports

2. DEPENDENCY AUDIT
   - Read package.json
   - List all prod and dev dependencies with versions
   - Flag any outdated or vulnerable packages
   - Check if react-hook-form, zod, msw are installed

3. COMPONENT INVENTORY
   - List all shared components in src/shared/ui/
   - List all shared hooks in src/shared/hooks/
   - Identify missing common components (DataTable, Pagination, Modal, Skeleton, etc.)
   - Flag any component > 400 lines that needs splitting

4. ROUTE COVERAGE
   - Read src/app/App.tsx
   - Count total routes
   - List which feature directories have NO routes (missing pages)
   - List routes that point to features with < 50 lines (stub pages)

5. BACKEND API COVERAGE
   - Count backend router files in backend/app/api/v1/
   - Count total endpoint functions
   - Compare against frontend services to find uncovered backend endpoints
   - List backend modules with ZERO frontend coverage

6. TEST COVERAGE
   - Count test files in tests/ and e2e/
   - List what is tested vs what is not
   - Check vitest.config.ts and playwright.config.ts

7. QUALITY CHECKS
   - Run: npx tsc --noEmit (count errors)
   - Run: npm run lint (count warnings)
   - Run: npm run build (succeeds?)
   - Check for hardcoded colors (grep for hex codes in .tsx files)
   - Check accessibility (count aria-* attributes across all files)
   - Check i18n coverage (count files using t() vs not)

OUTPUT FORMAT:
Produce a markdown report with each section above, including counts,
file paths, and a severity rating (CRITICAL / WARNING / INFO) for each finding.
End with a prioritized action list.
```

---

## 2. EXECUTE-ALL — Run All Prompts in Sequence

> This is a single mega-prompt that tells the AI to execute all 26 prompts from WEB-FRONTEND-PROMPTS.md in order.

```
ROLE: You are a senior full-stack developer implementing a frontend roadmap.

PROJECT: ecole-platform-dev/web/
REFERENCE: Read the file docs/WEB-FRONTEND-PROMPTS.md in its entirety first.

INSTRUCTIONS:
Execute ALL prompts from WEB-FRONTEND-PROMPTS.md in strict sequential order:
  WEB-P0-1 through WEB-P0-6 (Infrastructure)
  WEB-P1-1 through WEB-P1-5 (Critical features + Innovation)
  WEB-P2-1 through WEB-P2-5 (Partial features + Innovation)
  WEB-P3-1 through WEB-P3-5 (Final innovation + Polish)
  WEB-P4-1 through WEB-P4-5 (Testing + Verification)

FOR EACH PROMPT:
1. Read the CONTEXT section to understand the current state
2. Execute the TASK section completely — create all listed files, modify all listed files
3. Run the VERIFY section — fix any failures before moving to the next prompt
4. Execute the GIT section to commit (only if running in Codex; skip if Claude Code)

RULES:
- Do NOT skip any prompt
- Do NOT modify prompts (execute them as written)
- If a VERIFY step fails, fix the issue before proceeding
- If an npm install fails, try alternative: npm install --legacy-peer-deps
- After ALL 26 prompts, run the WEB-P4-5 final verification gate
- Output a final summary table showing PASS/FAIL for each prompt

FINAL OUTPUT:
| Prompt | Status | Files Created | Files Modified | Verify |
|--------|--------|---------------|----------------|--------|
| WEB-P0-1 | DONE | 7 | 2 | PASS |
| WEB-P0-2 | DONE | 10 | 2 | PASS |
| ... | ... | ... | ... | ... |
```

---

## 3. EXECUTE-PHASE — Run a Single Phase

> Use these when you want to run one phase at a time instead of all 26 prompts.

### Execute Phase 0 (Infrastructure)
```
Read docs/WEB-FRONTEND-PROMPTS.md and execute prompts WEB-P0-1 through WEB-P0-6 in order.
For each prompt: execute TASK, run VERIFY, fix any failures, then execute GIT section.
After completing all 6 prompts, run:
  cd web && npx tsc --noEmit && npm run lint && npm run build
Report results.
```

### Execute Phase 1 (Critical + Innovation)
```
Read docs/WEB-FRONTEND-PROMPTS.md and execute prompts WEB-P1-1 through WEB-P1-5 in order.
Prerequisite: Phase 0 must be complete (shared components must exist).
For each prompt: execute TASK, run VERIFY, fix any failures, then execute GIT section.
After completing all 5 prompts, run:
  cd web && npx tsc --noEmit && npm run lint && npm run build
Report results.
```

### Execute Phase 2 (Partial + Innovation)
```
Read docs/WEB-FRONTEND-PROMPTS.md and execute prompts WEB-P2-1 through WEB-P2-5 in order.
Prerequisite: Phases 0-1 must be complete.
For each prompt: execute TASK, run VERIFY, fix any failures, then execute GIT section.
After completing all 5 prompts, run verification.
```

### Execute Phase 3 (Final Innovation + Polish)
```
Read docs/WEB-FRONTEND-PROMPTS.md and execute prompts WEB-P3-1 through WEB-P3-5 in order.
Prerequisite: Phases 0-2 must be complete.
For each prompt: execute TASK, run VERIFY, fix any failures, then execute GIT section.
After completing all 5 prompts, run verification.
```

### Execute Phase 4 (Testing + Verification)
```
Read docs/WEB-FRONTEND-PROMPTS.md and execute prompts WEB-P4-1 through WEB-P4-5 in order.
Prerequisite: Phases 0-3 must be complete.
For each prompt: execute TASK, run VERIFY, fix any failures, then execute GIT section.
The last prompt (WEB-P4-5) is the final verification gate — ALL checks must pass.
```

---

## 4. VERIFY-ALL — Complete Verification Suite

> Run this after completing all phases to verify everything is correct.

```
ROLE: You are a QA engineer verifying a React frontend.

PROJECT: ecole-platform-dev/web/

RUN THESE CHECKS IN ORDER:

=== BUILD CHECKS ===
cd web
npx tsc --noEmit                    # MUST: 0 errors
npm run lint                         # MUST: 0 errors, 0 warnings
npm run build                        # MUST: clean build, no warnings
ls -la dist/assets/*.js | awk '{print $5, $9}'  # WARN if any > 500KB

=== TEST CHECKS ===
npm run test                         # MUST: all pass
npm run test:coverage                # REPORT: coverage percentage
npm run test:e2e                     # MUST: all pass (or report failures)

=== FEATURE COVERAGE ===
For each directory below, verify it exists and has >= 3 .ts/.tsx files:
  src/features/attendance/
  src/features/gradebook/
  src/features/budgets/
  src/features/micro-schools/
  src/features/skills/
  src/features/compliance/
  src/features/sync/
  src/features/financial-health/

=== SHARED COMPONENTS ===
Verify these files exist in src/shared/ui/:
  DataTable.tsx, Pagination.tsx, ConfirmDialog.tsx, Skeleton.tsx, Badge.tsx,
  Tabs.tsx, Breadcrumb.tsx, SearchInput.tsx, StatCard.tsx, ErrorBoundary.tsx,
  FormField.tsx, FormSelect.tsx, FormTextarea.tsx, FormCheckbox.tsx, FormDatePicker.tsx,
  OfflineIndicator.tsx, RetryButton.tsx

=== QUALITY CHECKS ===
# Accessibility
grep -rn "aria-" src/ --include="*.tsx" | wc -l
# Target: >= 100

# Dark mode
grep "data-theme" src/app/styles.css | wc -l
# Target: >= 1

# No hardcoded colors in feature files
grep -rn "#[0-9a-fA-F]\{3,6\}" src/features/ --include="*.tsx" | wc -l
# Target: 0

# i18n usage
grep -rn "useTranslation\|t(" src/features/ --include="*.tsx" | wc -l
# Target: >= 200

# No files > 400 lines
find src/features/ -name "*.tsx" -exec wc -l {} + | awk '$1 > 400 {count++} END {print count " files > 400 lines"}'
# Target: 0

# Route count
grep -c "path=" src/app/App.tsx
# Target: >= 60

# Form library usage
grep -rn "useForm\|useFormContext\|zodResolver" src/features/ --include="*.tsx" | wc -l
# Target: >= 10

=== OUTPUT ===
Produce a verification report:

| Category | Check | Result | Target | Status |
|----------|-------|--------|--------|--------|
| Build | TypeScript | 0 errors | 0 | PASS |
| Build | Lint | 0 errors | 0 | PASS |
| Build | Vite build | Success | Success | PASS |
| Test | Unit tests | X pass | All | PASS/FAIL |
| Test | E2E tests | X pass | All | PASS/FAIL |
| Feature | Innovation modules | 6/6 | 6 | PASS/FAIL |
| Quality | ARIA attributes | X | >= 100 | PASS/FAIL |
| Quality | Dark mode | Yes | Yes | PASS/FAIL |
| Quality | i18n coverage | X | >= 200 | PASS/FAIL |
| Quality | No oversized files | X | 0 | PASS/FAIL |

If ANY check fails, list the specific failures and suggest fixes.
```

---

## 5. FIX-FAILURES — Auto-Fix Verification Failures

> Run this AFTER VERIFY-ALL if any checks failed.

```
ROLE: You are a senior developer fixing verification failures.

PROJECT: ecole-platform-dev/web/

I ran the VERIFY-ALL prompt and got the following failures:
[PASTE THE FAILURE OUTPUT HERE]

For each failure:
1. Identify the root cause
2. Fix the issue (edit the relevant files)
3. Re-run the specific verification check
4. Confirm it passes

After fixing all failures, re-run the FULL VERIFY-ALL suite and output the updated report.

RULES:
- Do NOT skip any failure
- Do NOT suppress errors (fix the root cause)
- If a test fails, fix the test AND the code if needed
- If a type error exists, fix the type (don't cast to `any`)
- Commit fixes: git commit -m "fix(web): resolve verification failures — [list issues]"
```

---

## 6. DIFF-REPORT — Generate Change Summary

> Run this at any point to see what has changed since a baseline.

```
PROJECT: ecole-platform-dev/web/

Generate a comprehensive diff report:

1. Git status: git status --short
2. New files: git diff --name-only --diff-filter=A HEAD~N (replace N with number of commits in this session)
3. Modified files: git diff --name-only --diff-filter=M HEAD~N
4. Line counts: git diff --stat HEAD~N
5. Per-feature summary:
   For each directory in src/features/:
     - Files added
     - Files modified
     - Total line changes

Output as markdown table.
```

---

## 7. ROLLBACK — Undo Last Prompt Execution

> Use if a prompt produced bad results and you need to start over.

```
PROJECT: ecole-platform-dev/web/

SAFETY CHECK: Run git log --oneline -5 to see recent commits.
Show me the last 5 commits and ask which one to roll back to.

WARNING: This is destructive. Only proceed if the user confirms.

To rollback:
  git reset --soft HEAD~1   # Undo last commit, keep changes staged
  git restore --staged .     # Unstage all
  git checkout -- .          # Discard all changes

Then re-run the specific prompt that failed.
```

---

## 8. PROGRESS-CHECK — See Where You Are

> Run this to see which prompts are complete and which remain.

```
PROJECT: ecole-platform-dev/web/

Check the current state of the frontend and determine which prompts from
docs/WEB-FRONTEND-PROMPTS.md have been completed.

For each prompt (WEB-P0-1 through WEB-P4-5), check:
- Do the OUTPUT files listed in the prompt exist?
- Do they have content (non-empty)?
- Do the VERIFY commands pass?

Output:
| Prompt | Description | Status | Missing |
|--------|-------------|--------|---------|
| WEB-P0-1 | Form library | DONE/PARTIAL/TODO | - or list of missing items |
| WEB-P0-2 | Shared components | TODO | DataTable, Pagination, ... |
| ... | ... | ... | ... |

Then state: "X of 26 prompts complete. Next: WEB-P{x}-{y}"
```

---

## 9. SINGLE-PROMPT — Execute One Specific Prompt

> Use this template to run any individual prompt.

```
Read the file docs/WEB-FRONTEND-PROMPTS.md.
Find and execute prompt WEB-P{X}-{Y} (replace with actual prompt ID).

Steps:
1. Read the CONTEXT section
2. Verify prerequisites exist (check if dependent files from prior prompts are in place)
3. Execute the TASK section completely
4. Run the VERIFY section — fix any failures
5. Execute the GIT section (Codex only)
6. Report what was created/modified
```

---

## 10. ESTIMATE — Time & Effort Estimate

> Get an estimate of effort for any phase or the full roadmap.

```
Based on the prompts in docs/WEB-FRONTEND-PROMPTS.md, estimate:

1. For each phase (P0-P4):
   - Number of new files to create
   - Number of existing files to modify
   - Estimated lines of code (new)
   - Estimated complexity (simple/moderate/complex)
   - Estimated time for a senior React developer (hours)

2. Dependencies between phases (which must come before which)

3. Risk assessment:
   - Which prompts are most likely to have issues?
   - Which prompts depend on npm packages that might have version conflicts?
   - Which prompts require the most backend API knowledge?

Output as table with totals.
```
