# Web + Mobile ↔ Backend Alignment Plan

> After the backend taxonomy/rename/RBAC work, the clients drifted. This is the
> read-only audit + the ordered fix plan. **No client code changed yet** — awaiting
> sign-off. Verified by reading the actual files (not just grep counts).

## Findings, grouped by root cause (ordered by severity)

### R1 — Subject & Level vocabulary out of sync  ⚠️ BREAKS content/quiz CRUD  (P0)
The clients still ship the **old French/invalid** vocabulary:
- `LEVELS = ['maternelle','cp','ce1','ce2','cm1','cm2','6eme'…'terminale']`
  — backend `ContentLevelBand` enum is `PS/MS/GS/1AEP…6AEP/1AC/2AC/3AC/TC/1BAC/2BAC`.
- `SUBJECTS = ['math','french','arabic','science','history','geography','english',
  'islamic_studies','art','sport']` — `science / history / geography /
  islamic_studies` are **not** enum members (backend has `activite_scientifique`,
  `svt`, `physique_chimie`, `histoire_geo`, `islamic`).

Effect: creating or filtering content/quizzes with these values is **rejected by
the backend** (`validate_subject` / enum cast). Duplicated across:
- web: `content/cms/model/content-upload.types.ts`, `content/cms/model/quiz-builder.types.ts`,
  `lms/teacher/model/teacher-quiz.types.ts`, `content/teacher-library/model/content-library.types.ts`,
  + dropdown UIs `content/cms/ui/ReviewQueuePage.tsx`, `ContentListPage.tsx`, `ContentUploadPanel.tsx`.
- mobile: equivalent subject lists (~6 hits).

**Fix:** one **shared source of truth** for levels + subjects, aligned to the
backend enums, reused everywhere (so it can't re-drift). Add `other` to subjects
with a free-text `subject_other` input. Optional: a code→label map for nice
display (`1AEP → "1AEP (CP)"`). This is the only item that actually breaks a flow.

### R3 — Conversations: client `subject` vs backend `subject_line`  ⚠️ silent feature break  (P1)
Backend renamed the column **and** the API field to `subject_line` (model,
request, response — `schemas/communication/__init__.py`, `services/.../communication.py`).
Clients still use `subject`:
- web: `communication/messages/api/messages.api.ts` (`subject: string | null`),
  `ConversationsPage.tsx` (sends `subject`, reads `conversation.subject`).
- mobile: `conversations_screen.dart` + the conversation model.

Effect: on create the subject is dropped (backend ignores `subject`); on display
the client always falls back to the participant name. No crash — just broken.
**Fix:** rename the client field `subject → subject_line` (API type + create
payload + display read) in web and mobile.

### R2 — Payment proof upload  ✅ not broken (informational, P3)
Backend dropped the `payment_proofs` table but **kept a compatibility endpoint**
`POST /payments/{id}/proof` ("compatibility wrapper … returns an acknowledgement").
So `uploadPaymentProof` in web/mobile still works — the proof just isn't persisted.
**Decision needed (not urgent):** keep the upload UI (works as an ack) or hide it.

### R4 — level_band display  (folds into R1)
Clients treat `level_band` as an opaque `string` (no French label map beyond CSS
theme keys `maternelle.css` / `age_theme.dart`, which are *theme names*, fine).
Raw Moroccan codes will render. Covered by the optional label map in R1.

### R5 — Game-config edit gating  (P2, low risk)
Backend now enforces `PERM-AI:game-config:manage` (403 for unauthorized). Clients
call game endpoints but don't gate the *edit* affordance by role. For the demo
students only *play* (allowed), so low risk. **Fix (later):** hide create/update
game-config UI from roles lacking the permission.

### R6 — New fields surfacing (subject_other / topic)  (P3, optional)
Clients don't yet send/display `subject_other` or content `topic`. Only needed if
the demo creates "other"-subject content. Tie to R1 (the `other` input).

---

## Proposed execution order

1. **R1 — vocab alignment** (P0, unblocks content/quiz CRUD). Shared levels+subjects
   const aligned to backend enums; update the 4 type files + 3 dropdown UIs (web)
   and the mobile lists; add `other` + `subject_other`.
2. **R3 — conversation `subject_line` rename** (P1) in web + mobile.
3. **R5 — game-config edit gating** (P2) — hide edit UI from unauthorized roles.
4. **R2 / R6 decisions** (P3) — keep-or-hide proof UI; surface `subject_other`/`topic`
   only if the demo needs them.

Then verify: `cd web && npm run typecheck && npm run lint && npm run build`,
`cd mobile && flutter analyze`. (Tests deferred per owner.)

> Out of scope here (tracked elsewhere): full web↔mobile **nav parity**,
> `/reports` vs `/results`-vs-`/progress` reconciliation, the ~340-string mobile
> i18n sweep — those are UI-coherence, not backend-drift. Sequence them after R1–R3.

---

## Progress log

### R1 — vocab alignment
- **Web vocab: DONE + `npm run typecheck` GREEN (exit 0).** One shared SoT
  `src/shared/taxonomy.ts` (`LEVEL_BANDS`, `LEVEL_LABELS`, `SUBJECTS` incl.
  `other`, `QUIZ_SUBJECTS`, `SUBJECT_OTHER`), mirroring the backend enums. All
  definition sites now import from it (the 4 type/entity files, the 2 inline
  pages, and `teacher-library/model/content-library.types.ts` re-points
  `SUBJECT_OPTIONS`/`LEVEL_OPTIONS`). No old French/invalid subject vocab remains
  on any create/filter dropdown (`'history'` leftovers are react-query cache
  keys, not subjects).
- **Mobile:** content/quiz subject inputs are free-text (no dropdown vocab to
  drift); `colors.dart` subject→colour map keys aligned to Moroccan codes.
- **`subject_other` in CMS content create: DONE + typecheck GREEN (exit 0).**
  Wired the `other` → free-text matière input end-to-end in the main CMS upload
  path:
  - `content-upload.types.ts`: added `subject_other` to the zod schema
    (`.max(120)`, optional), a `superRefine` rule requiring it when
    `subject === 'other'`, the `CmsContentFormValues` interface field, and the
    form defaults.
  - `ContentUploadPage.tsx`: `watchedSubject` drives a conditional `FormField`
    (shown only when `subject === 'other'`); the create payload sends
    `subject_other` only for `other` (else `undefined`). Mirrors the backend
    contract in `subject_rules.validate_subject` (school content + `other`
    requires a name; platform content rejects `other`).
  - i18n: added `cms.upload.subjectOther` (label) + `cms.validation.subjectOther`
    (max) + `cms.validation.subjectOtherRequired` (fr/ar/en).
  - Teacher-quiz + CMS-bulk `subject_other` were completed afterwards — see
    **R6** below.

### R3 — conversation `subject` → `subject_line`
- **DONE (web typecheck GREEN, exit 0; mobile pending `flutter analyze`).**
  Backend renamed the column + API field to `subject_line` (request
  `ConversationCreate.subject_line` max 300, response `subject_line`). Aligned
  both clients:
  - **web:** `messages.api.ts` (`Conversation.subject_line`, create-payload type
    `subject_line?`), `model/useMessages.ts` (mutation payload type),
    `ConversationsPage.tsx` (send `subject_line`, both display reads). The
    `t('messages.subject')` label keys are UI strings, not the API field — left
    as-is.
  - **mobile:** `domain/entities/communication/conversation.dart` (field
    `subjectLine`, ctor, `fromJson` reads `json['subject_line']`),
    `conversations_screen.dart` (POST body key `subject_line`, both display
    reads `conversation.subjectLine`).
  - Verified the other `subject` hits (content/quiz/rubric/resource mappers) are
    the **matière** field — unchanged on the backend, correctly left alone.

### R5 — game-config edit gating
- **DONE (web typecheck GREEN, exit 0; mobile is play-only, nothing to gate).**
  Backend gates create/update game-config behind `PERM-AI:game-config:manage`
  (only **TCH + EDUCATOR** hold it). The web routes allowed `['TCH','ADM']`, so
  an **ADM** saw Create/Edit/Save affordances that 403 on submit. Fixes:
  - New SoT `src/shared/permissions.ts` (`PERMISSIONS.GAME_CONFIG_MANAGE` +
    `hasPermission(perms, perm)`), mirroring the backend.
  - `ProtectedRoute` extended with an optional `permissions?: string[]` gate
    (requires all listed); applied `permissions={[GAME_CONFIG_MANAGE]}` to
    `/teacher/games/new` (the editor) so URL-typing an ADM is redirected home.
  - `GamesListPage`: `canManageGames` now uses the permission (was role
    `TCH||ADM`) → hides the "Create game" button for ADM.
  - `GameConfigDetailPage`: hides the "Create game" button **and** the embedded
    `GameConfigEditor` unless the user holds the permission (ADM gets a
    read-only detail view).
  - Mobile games are play-only (only `GET /games/configs`); no authoring UI.

### R6 — surface `subject_other` in the remaining create forms
- **DONE (web typecheck + lint GREEN).** Backend accepts `subject_other` on
  `QuizCreate` (max 120) and validates it via the shared `validate_subject`, so
  custom matières work for quizzes too. Wired:
  - **Teacher quiz** (`teacher-quiz.types.ts`, `TeacherQuizCreateForm.tsx`,
    `quizzes.api.ts`): new `QUIZ_SUBJECT_OPTIONS = [...QUIZ_SUBJECTS, 'other']`;
    selecting *Other* reveals a required free-text input; payload now carries
    `subject_other` (null unless `subject === 'other'`); submit is blocked while
    the custom name is empty. `QuizPayload`/`TeacherQuizPayload` gained the field.
  - **CMS bulk** (`ContentUploadPage.tsx`, `CmsBulkUploadForm.tsx`): `SUBJECTS`
    already exposes `other`, so a `bulkSubjectOther` input now appears for it and
    is sent with every file; the batch is blocked (with
    `cms.validation.subjectOtherRequired`) if the custom name is empty — closing
    the latent 422 where bulk could send `subject='other'` with no name.
  - i18n: added `cms.subjects.other` (Other/Autre/أخرى) so the dropdowns show a
    label instead of the raw `other` code (fr/ar/en).
  - Content `topic` (sujet): backend column exists; surfacing it in the CMS form
    is left as optional polish (not needed for the demo).

### R4 — subject-label i18n (Moroccan codes → official titles)
- **DONE.** The dropdowns/cards/filters render subjects via
  `t('cms.subjects.<code>', <code>)`, but `cms.subjects` only had the **old**
  vocab, so the 22 new Moroccan codes (`activite_scientifique`,
  `physique_chimie`, `histoire_geo`, `svt`, `islamic`, `amazigh`,
  `informatique`, …) fell back to **raw snake_case** in ~10 web surfaces.
  - Mirrored the backend's authoritative `SUBJECT_TITLES` (AR/FR/EN, from
    `app/models/curriculum.py`) into `cms.subjects` for all three locales — 24
    matières + `other` (added `quranic`, which is MEN-TODO scope, with a sensible
    label). Sourced from the backend so the labels can't re-drift.
  - Pruned 4 **stale** keys (`science`, `history`, `geography`,
    `islamic_studies`) — no longer valid codes.
  - Verified programmatically: **every** taxonomy `SUBJECTS` code now resolves to
    a label (0 missing); all three JSON files valid.
  - Mobile needs no equivalent: its subject inputs are free-text and the only
    displayed subject name (`transcript` `subjectName`) arrives **resolved** from
    the backend.

### R2 — payment-proof upload (DECISION: keep as ack)
- **Kept.** Backend still exposes the compatibility endpoint
  `POST /payments/{id}/proof` (returns an acknowledgement; the dropped
  `payment_proofs` table is not restored). The web/mobile upload UI therefore
  still works as an ack and is **kept as-is** — no client change. If you later
  want it gone, hide `uploadPaymentProof` in web + mobile; flagged here for a
  one-line follow-up.

### Final verification
- **web `npm run typecheck` (tsc --noEmit): GREEN (exit 0).**
- **web `npm run lint` (eslint .): GREEN (exit 0).**
- **web `npm run build` (vite/rollup bundling): NOT runnable in this Linux
  sandbox** — the mounted `node_modules` was installed on the user's Mac, so it
  only contains `@rollup/rollup-darwin-arm64`; the sandbox is `linux arm64` and
  rollup aborts with `Cannot find module @rollup/rollup-linux-arm64-gnu`. This
  is an environment/platform mismatch, **not** a code error (tsc+eslint cover the
  source). Run `npm run build` on the Mac to confirm bundling.
- **mobile `flutter analyze`: NOT runnable here** (no Flutter/Dart SDK in the
  sandbox). Run on the user's machine. Mobile edits were limited to the
  conversation `subjectLine` rename (R3); no new mobile types were introduced.

### Decision — age-tier (RESOLVED: informal + formal préscolaire)
The "age-tier" (`maternelle.css`, `designContext.ageAccent`) is **purely UI
styling** (bigger fonts/icons/mascot for young kids) — NOT content, access, or
page structure. Content is already driven by class assignment + level + subject.
**Owner decision: scope the playful accent to INFORMAL context + FORMAL
préscolaire** (PS/MS/GS). Applied:
- web `shared/ui/designContext.ts`: `ageAccent = role === 'STD' && (designMode
  === 'informal' || ageTier === 'maternelle')` (formal primaire and above keep
  the standard look).
- mobile `presentation/shell_screen.dart`: student branch uses
  `accentTier = (informalContext || ageTier == AgeTier.maternelle) ? ageTier :
  AgeTier.college` so `AgeThemedView` only applies the playful accent for
  informal or préscolaire students.
