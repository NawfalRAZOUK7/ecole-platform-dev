# Product / Long-Term Roadmap — post-PFE

> Scope note: the PFE (graduation project) ships the system **as built today**.
> The items here are **deliberately deferred** — they're the right long-term
> direction, not PFE work. This file exists so the thinking isn't lost. Companion
> to `BACKEND_COMPLETION_PLAN.md` (what shipped) and `BACKEND_MATURITY_AUDIT.md`
> (code-level findings).

---

## 1. The big one: converge micro / macro into one platform with a "formality mode"

### The problem (why the current model feels wrong)

"Micro" today is not a *mode* of the platform — it's a **second copy** of it.
Parallel trees describe the same nouns:

| Formal world | Micro/informal world | Same underlying concept? |
|---|---|---|
| `schools` | `micro_schools` | Yes — a tenant |
| `classes` | `micro_groups` | Yes — a group of students |
| `enrollments` | `micro_enrollments` | Yes — student↔group |
| `content_items` + `ClassContentAssignment` | `micro_resources` | Yes — content for a group |
| `invoices` / fee structures | `micro_payments` | Yes — billing |
| grades / assessments | `micro_progress_logs` | **No — genuinely different** |
| academic periods | (none) | **No — genuinely different** |

Forking the shared concepts means every feature is built, scoped, and tested
twice, and the copies drift. That drift is exactly how we ended up with **formal
content scoped by class assignment (curated, D3) but micro content scoped by an
`age_group` string (uncurated)** — the inconsistency that triggered this whole
discussion.

### What is genuinely different vs merely duplicated

**Genuinely different (keep separate, as a thin "informal mode" layer):**
- Progress is **observational** (milestones, photos, notes) — not 0–20 grades,
  no report cards, no MEN curriculum compliance.
- **No academic periods** — continuous, age-rolling.
- Grouping is by **age / developmental stage**, not grade level.
- The adult is an **educator/animateur**, not a subject teacher.
- **Simpler billing** (flat monthly fee vs tuition structures, sibling discounts,
  installments).

**Merely duplicated (should converge to one spine):**
- school = tenant, student = user, parent-link = parent-link,
- group = set of students, content = content, enrollment = student-in-group,
- billing primitives (invoice/line/payment).

### Target model

**One platform, two formality modes.** There is ONE "learning group" concept; a
formal class and a micro-group are the same thing with two **membership rules**:
- *grade-based* (enrolled in 1AEP), or
- *age-based* (3–5 → "Petits curieux").

Content always flows **group → student** (one scoping rule for everyone). Age is
demoted to *how a group is formed* + a guardrail — never the access filter.
The genuine differences (graded vs observational progress; periods or not; fee
rules) become **mode-specific behaviors layered on the shared spine**, not
separate data trees.

> Key principle (the "class not age" decision): **content reaches every student
> through a class/group assignment, uniformly.** For préscolaire the group is
> age-banded, so age still matters — but only to *define the group*, not to
> grant content access.

### Phased convergence (do NOT big-bang)

The parallel tables exist, are migrated, seeded, and working — so sequence it:

1. **Content + scoping spine (highest leverage).** Merge `micro_resources` into
   `content_items` (a resource *is* content). Make one assignment-based scoping
   rule resolve a student to their group whether that's a `Class` or a
   `micro_group` (a `_user_group_ids` resolver alongside `_user_class_ids`, plus
   a `micro_group_content_assignments` table mirroring `ClassContentAssignment`).
   Outcome: one way content reaches a child; age stops being the filter.
2. **Grouping.** Give the group concept a `grouping_type` (grade | age) so
   micro-groups become age-grouped classes; fold `micro_enrollments` into
   `enrollments`.
3. **Billing & progress — only if justified.** May never be worth merging:
   graded-vs-observational and the fee differences are real domain forks. Keep
   them separate unless a concrete need appears.

**Endgame:** micro/macro survives as a meaningful distinction *only where it's
real* (progress semantics, periods, fee rules) and disappears everywhere it was
just duplication (content, grouping, scoping, billing primitives).

### Decision record
- 2026-06-16 — Chosen for **PFE: keep the current dual-tree model as-is** (it
  works, it's seeded, the demo shows micro-schools functioning). Convergence is
  **post-PFE**. The "class not age" content fix is part of phase 1 above and is
  therefore deferred with it.

---

## 2. Deferred technical items (from the maturity audit)

Carried over from `BACKEND_MATURITY_AUDIT.md` — none block the PFE:

- **oauth `expires_in` parsing** (`app/api/v1/auth/oauth.py`) — store real token
  expiry instead of `None`.
- **Remaining N+1 reads** — parent-children dashboard loop (low N), import-time
  compliance loops (`get_curriculum_by_scope` / `get_objective_by_code` per
  iteration), `erp.py` absence-justification per record. Batch with
  `WHERE id IN (...)` / `GROUP BY` when real-scale load matters.
- **Bulk-insert** the create-in-loop hotspots (timetable generation, gradebook
  categories) via `add_all` / `bulk_insert_mappings`.
- **reports.py Phase-2.1 stubs** — discount parsing, child-fetch in report jobs.

---

## 3. Other product-grade hardening (not PFE)

- Full **web↔mobile nav parity** + reconcile `/reports` and `/results`-vs-
  `/progress` across clients.
- **Mobile i18n** — externalize remaining ~340 hardcoded strings to
  `app_localizations.dart` (fr/ar/en) with a CI guard.
- **Arabic native review** of the web translations.
- **Test suite rewrite** to match the post-taxonomy schema (deferred by owner).
- Collège/lycée **niveau→matière** detail; `amazigh` + `quranic` subjects; msid
  Quranic memorisation (hifz) levels; `MicroSchool.type_detail` UX.
