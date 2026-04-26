# Ecole Platform — Phase 2 General Prompts

> Generated: 2026-04-06
> Meta-prompts for Phase 2 (WEB-P5 → WEB-P9)
> Prerequisite: Phase 1 (WEB-P0 → WEB-P4) all green

---

## 1. ANALYZE-P2 — Pre-Phase 2 Baseline

```
ROLE: Senior frontend architect
PROJECT: ecole-platform-dev/web/

Run these checks to establish a Phase 2 baseline:

1. BUNDLE ANALYSIS
   npm run build
   ls -la dist/assets/*.js | awk '{printf "%s %.1fKB\n", $9, $5/1024}'
   Report: total bundle size, largest chunk, number of chunks

2. ENDPOINT COVERAGE
   Count API calls per service:
   for svc in $(find src/features -name "*.service.ts"); do
     count=$(grep -cE "\.(get|post|put|patch|delete|list)\(" "$svc");
     echo "$(basename $(dirname $svc)): $count";
   done | sort -t: -k2 -rn
   Total frontend API calls vs 311 backend endpoints

3. CI/CD STATUS
   ls .github/workflows/ 2>/dev/null || echo "No CI workflows"
   cat .husky/pre-commit 2>/dev/null || echo "No pre-commit hooks"

4. TEST COUNTS
   npm run test -- --reporter=verbose 2>&1 | tail -5
   ls web/e2e/*.spec.ts | wc -l

5. ROUTE COUNT
   grep -c "path=" src/app/App.tsx

Output: Markdown table with baseline numbers to compare against after Phase 2.
```

---

## 2. EXECUTE-ALL-P2 — Run All Phase 2 Prompts

```
ROLE: Senior full-stack developer.
PROJECT: ecole-platform-dev/web/
REFERENCE: Read docs/WEB-PHASE2-PROMPTS.md in its entirety first.

Execute ALL 18 prompts in strict order:
  WEB-P5-1 through WEB-P5-3 (Performance)
  WEB-P6-1 through WEB-P6-5 (Endpoint Coverage Tier 1)
  WEB-P7-1 through WEB-P7-5 (Endpoint Coverage Tier 2)
  WEB-P8-1 through WEB-P8-2 (CI/CD)
  WEB-P9-1 through WEB-P9-3 (Integration + Final Gate)

FOR EACH PROMPT:
1. Read CONTEXT
2. Execute TASK completely
3. Run VERIFY — fix any failures before next prompt
4. Execute GIT (Codex only)

FINAL OUTPUT: Summary table showing PASS/FAIL for each prompt.
```

---

## 3. EXECUTE-PHASE (Individual Phases)

### Execute Phase 5 (Performance)
```
Read docs/WEB-PHASE2-PROMPTS.md. Execute WEB-P5-1 through WEB-P5-3 in order.
After all 3: npm run build, verify no chunk > 300KB.
```

### Execute Phase 6 (Coverage Tier 1)
```
Read docs/WEB-PHASE2-PROMPTS.md. Execute WEB-P6-1 through WEB-P6-5 in order.
Prerequisite: Phase 5 complete.
After all 5: npx tsc --noEmit && npm run lint && npm run build.
```

### Execute Phase 7 (Coverage Tier 2)
```
Read docs/WEB-PHASE2-PROMPTS.md. Execute WEB-P7-1 through WEB-P7-5 in order.
Prerequisite: Phases 5-6 complete.
After all 5: verify, build, check endpoint coverage count.
```

### Execute Phase 8 (CI/CD)
```
Read docs/WEB-PHASE2-PROMPTS.md. Execute WEB-P8-1 through WEB-P8-2 in order.
Prerequisite: Phases 5-7 complete.
Validate GitHub Actions YAML syntax.
```

### Execute Phase 9 (Integration + Gate)
```
Read docs/WEB-PHASE2-PROMPTS.md. Execute WEB-P9-1 through WEB-P9-3 in order.
The last prompt (WEB-P9-3) is the final gate — ALL checks must pass.
```

---

## 4. VERIFY-ALL-P2 — Full Phase 2 Verification

```
PROJECT: ecole-platform-dev/web/

=== BUILD ===
npx tsc --noEmit                        # 0 errors
npm run lint                             # 0 errors
npm run build                            # success
ls -la dist/assets/*.js | awk '$5>307200 {print "FAIL:", $9}'  # no chunk > 300KB

=== TESTS ===
npm run test                             # all pass
npm run test:e2e                         # all pass
npm run test:contract                    # all paths match backend

=== COVERAGE ===
grep -rn "api\." src/features/ --include="*.service.ts" | wc -l   # target: >= 250
ls -d src/features/*/ | wc -l                                      # target: >= 28
grep -c "path=" src/app/App.tsx                                    # target: >= 70

=== CI/CD ===
ls .github/workflows/web-ci.yml                                    # exists
ls .github/workflows/web-e2e.yml                                   # exists
ls .husky/pre-commit                                               # exists

=== QUALITY ===
grep -rn "aria-" src/ --include="*.tsx" | wc -l                    # target: >= 150
grep "data-theme" src/app/styles.css | wc -l                       # target: >= 1
grep -rn "useTranslation\|t(" src/features/ --include="*.tsx" | wc -l  # target: >= 2500

Output verification table.
```

---

## 5. PROGRESS-CHECK-P2

```
Check which Phase 2 prompts (WEB-P5-1 through WEB-P9-3) are complete.
For each prompt, check if OUTPUT files exist and VERIFY commands pass.

| Prompt | Description | Status |
|--------|-------------|--------|
| WEB-P5-1 | Code splitting | DONE/TODO |
| ... | ... | ... |

State: "X of 18 prompts complete. Next: WEB-P{x}-{y}"
```

---

## 6. COVERAGE-REPORT — Detailed Endpoint Coverage

```
Generate a detailed coverage report comparing backend endpoints vs frontend API calls.

For each backend router file (backend/app/api/v1/*.py):
1. Extract prefix and all endpoint paths with HTTP methods
2. Search frontend services for matching API calls
3. Mark each endpoint as: COVERED / UNCOVERED / PARTIAL (path exists but method differs)

Output:
| Backend Module | Total | Covered | Uncovered | Coverage % |
|---------------|-------|---------|-----------|-----------|
| attendance | 8 | 8 | 0 | 100% |
| billing | 14 | 14 | 0 | 100% |
| ... | ... | ... | ... | ... |
| TOTAL | 311 | X | Y | Z% |

List all still-uncovered endpoints at the end.
```
