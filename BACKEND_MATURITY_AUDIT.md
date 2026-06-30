# Backend Maturity Audit (#34)

> Read-only expert review of `backend/app` after the migration + seed pass.
> Evidence is cited as `file:line`. **No code was changed for this audit** — every
> item below is a recommendation awaiting your go-ahead. Companion to
> `BACKEND_COMPLETION_PLAN.md`.

## Executive summary

The backend is **production-shaped, not prototype**. Concrete signals:

- **418 endpoints**, of which **332 are `requires_permission`** (data-driven RBAC)
  and only **14 are raw `requires_role`** — strict-role separation is the norm.
- **Content scoping (D3) is enforced server-side** on every read/write content
  path, so hiding nav is defence-in-depth, not the security boundary.
- **75 structured `logger.*` calls** in services; the broad `except Exception`
  blocks in `auth.py` all **log with context** and guard side-effects (login
  history, audit, email) so they can't fail the main flow — correct, not a defect.
- **Low debt density**: 13 `TODO/FIXME` markers across the whole app; 4 stray
  `print()`s.

It is **not** "every line reviewed" — 99 services / 39 repositories. This audit
samples by pattern (async safety, N+1, observability, RBAC, API consistency) and
reads the high-signal hits. Findings are prioritized P1 (fix soon) → P3 (nice to
have). Nothing here blocks the demo; the seed and migrations are green.

---

## P1 — none found

No correctness-critical or security defects surfaced. The two changes from the
RBAC re-partition (inheritance removed; impersonation → SUP) and the content
scoping guards hold up under static review.

---

## P2 — worth fixing before it bites

1. **`requires_role` on two security-sensitive routes should be permission-based**
   - `app/api/v1/admin/admin.py:231` — `list_user_login_history` gated
     `requires_role(ADM, DIR, SUP)`. Login history is sensitive; under the strict
     DIR≠ADM model, decide deliberately whether **DIR (oversight)** should read
     per-user login history, and express it as a permission
     (`PERM-IAM:login-history:read`) rather than a role list.
   - `app/api/v1/ai/games.py:79` — `update_game_config` (a **write**) gated
     `requires_role(TCH, DIR, ADM, SUP, SYS)`. A write lumping five roles incl.
     TCH should be a single `requires_permission(...)`.

2. **N+1 reads inside loops** (≈50 await-in-loop sites; the *reads* are the real
   ones). Representative:
   - `app/services/academic/progress.py:487` — `get_student_grade_average` per
     student.
   - `app/services/academic/attendance_analytics.py:360` —
     `compute_student_absence_count` per student.
   - `app/services/admin/compliance.py:917,937` — `get_curriculum_by_scope` /
     `get_objective_by_code` per loop iteration.
   - `app/services/academic/erp.py:665` — `get_absence_justification_by_record`
     per record.
   These are fine at seed/demo scale but will degrade on real class sizes.
   Fix pattern: batch with a single `WHERE id IN (...)` / `GROUP BY` and build a
   dict, then look up in the loop. (The *creates*-in-loop — rubric, question
   bank, timetable, gradebook — run inside one UoW and are acceptable; bulk
   insert is a P3 optimization.)

## P3 — polish

1. **Replace `print()` with `logger`** (4 sites):
   `app/services/auth/sms_2fa.py:44,58` and
   `app/services/platform/suspicious_activity.py:24,43`. The dev-mode OTP print
   should be `logger.debug`, the failures `logger.warning(exc_info=True)`.
2. **Resolve the security-relevant TODOs** before they ossify:
   `app/api/v1/auth/webauthn.py:280` (`role="STD"` hard-coded — should resolve
   from membership) and `app/api/v1/auth/oauth.py:254` (token expiry not parsed).
   The reports.py Phase-2.1 TODOs are feature stubs, lower priority.
3. **Bulk-insert** the create-in-loop hotspots (timetable generation,
   gradebook categories) via `add_all` / `bulk_insert_mappings` if generation
   time matters.

---

## RBAC / scoping correctness (D1–D4) — static verification

| Decision | Where enforced | Status |
|---|---|---|
| **D1** informal students = real accounts | seed personas (creche/msid) + `micro_enrollments.student_user_id` | ✅ seeded & FK-linked |
| **D3** content scoped by class/relationship | `content_service.list_content_items` (allowlist via `list_assigned_content_item_ids`), `update_content_progress`/`complete_content_item` (`_content_assigned_to_user` → 404 for STD/PAR), `get_content_item`/`get_content_asset` guards in `_helpers.py` | ✅ enforced on every read/write path |
| **Strict roles** DIR≠ADM, SUP≠SYS | `core/permissions.py` explicit composition (no inheritance); 332/346 gates are permission-based | ✅ (2 P2 routes to convert) |
| Impersonation = SUP only | `permissions.py` (removed from DIR) | ✅ |

**Conclusion:** the model is sound and enforced in code. The remaining gap is
*dynamic* proof — that a real STD token gets a 404 on someone else's content, and
DIR can't hit ADM-only writes. That needs your running stack (below).

---

## Dynamic smoke-test (run on your machine)

The stack is up (seed succeeded). Confirm the scoping behaves, not just compiles.
Demo passwords are in `seed-report.md`. Example with httpie/curl against the API:

```bash
# 1) STD (Amina, CP/1AEP) logs in → list content → note an item ID she's assigned
#    Then try to GET a content_item assigned to a DIFFERENT class → expect 404.
# 2) PAR logs in → should see only their own child's data.
# 3) DIR token → attempt an ADM-only write (e.g. PUT /schools/{id} or user:manage)
#    → expect 403. ADM token on the same route → expect 2xx.
# 4) TCH → GET content library → should only see their level bands.
```

If any of those four don't behave as stated, that's a real bug and I'll fix it
(with your OK). Until then, static review says the enforcement is in place.

---

## What I did NOT do

- No code edits (read-only audit, per your instruction).
- No test changes (deferred by you).
- Did not exhaustively read all 99 services — sampled by risk pattern. If you
  want a specific module (e.g. billing, sync, AI) fully line-read, say which.

---

## Fixes applied (2026-06-16, approved)

All compile-clean (`python -m compileall app/` exit 0). No tests touched.

- **P2 — login-history gate** → `admin.py` now uses
  `requires_permission(PERM_IAM_LOGIN_HISTORY_READ)` (behavior-preserving:
  perm held by exactly ADM/DIR/SUP). Dropped the unused `requires_role`/role imports.
- **P2 — game-config writes** → added `PERM-AI:game-config:manage` to the catalog;
  granted to **TCH, ADM, CONTENT_MGR, SUP** (via `_ADM_OPS` + TCH set + CONTENT_MGR set).
  `create_game_config` and `update_game_config` now `requires_permission(...)`.
  **Access change (intentional, strict-roles):** DIR (oversight) and SYS
  (automation) can no longer author game configs. Verified effective grants =
  {TCH, ADM, CONTENT_MGR, SUP}; DIR/SYS = False.
- **Real bug (was filed as a TODO) — webauthn role** → `webauthn.py` no longer
  hard-codes `role="STD"` after passkey auth; it resolves the role from the
  user's active membership (`repo.get_membership`) and denies if none. This
  previously mis-scoped every passkey login to student.
- **P2 — N+1** → added `compute_period_absence_counts` (one GROUP BY for the
  whole period) and rewired the attendance **alert-generation loop** to a single
  batched query + dict lookup instead of one query per student. Behavior
  preserved (missing students default to 0/0). Left the parent-children loop
  (N≤3) and import-time compliance loops as not-worth-the-risk.
- **P3 — logging** → 4 `print()` → `logger` (dev SMS OTP `debug`; SMS / GeoIP
  failures `warning(exc_info=True)`).

**Deferred (your call):** oauth `expires_in` parsing TODO (minor); remaining
lower-cardinality N+1 loops; the reports.py Phase-2.1 feature stubs.
