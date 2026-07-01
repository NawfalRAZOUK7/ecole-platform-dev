# Agent Handoff — Run, Verify & Finish

Paste the prompt below into a coding agent **running locally in VS Code** (Codex,
Claude Code, Kimi, etc.) that has a real shell, the repo checked out, and can run
`npm`, `flutter`, `alembic`, `pytest`. It was written because the authoring agent
could **not** execute builds/migrations/tests — only static checks (parse,
brace/paren balance, JSON validity, alembic head graph).

Repo root: `ecole-platform-dev/` with `backend/`, `web/`, `mobile/`.

---

## PROMPT (copy from here)

You are picking up work done by another agent that could not run anything. Your
job is to **install, migrate, seed, build, analyze, test, and fix** so all of the
recently-added features actually run, then complete a few deliberately-deferred
items. Work methodically; after each step, if something fails, fix it before
moving on. Don't refactor unrelated code.

### 0. Context — what was added (all verified only statically)

1. **2FA**: client-side QR (`qrcode.react` web / `qr_flutter` mobile), SMS-2FA UI, backup-codes copy/guard, `refreshUser` in AuthContext.
2. **EDUCATOR role** wired on web + mobile (redirects, guards, nav).
3. **Design/UX**: mobile age/niveau theming + kids colors, Micro-École progress feed, WCAG fixes, niveau axis on web.
4. **AI provider**: 3-way auto factory (`mock` | `claude` | `open`) in `backend/app/services/ai/provider_factory.py` + new `open_model_provider.py`; config keys in `.env.example`.
5. **Letter Puzzle (procedural jigsaw)**: `backend` seed (`letter_puzzle` GameConfigs, 5 AR + 5 FR + 4 EN), `web` `LetterPuzzleGame.tsx` + `lib/jigsawGeometry.ts`, `mobile` `letter_puzzle/jigsaw_geometry.dart` + rewritten `screens/letter_puzzle_screen.dart` (drag-drop, confetti, TTS, config-driven, letter picker). New deps: `confetti` (mobile), `qrcode.react`/`qr_flutter`.
6. **Quiz generation from content (Feature B)**: `backend` `services/lms/content_quiz.py` + endpoint `POST /quizzes/from-content/{id}`; web `GenerateQuizButton` on content cards + mobile sheet; quiz player 🔊 audio. Localized template stems (ar/fr/en); `quizzes.language` column drives trilingual TTS.
7. **Onboarding/approval**: `backend/app/models/onboarding.py`, `services/platform/onboarding.py`, `api/v1/onboarding.py` (public `/applications/{formal-school,micro-school}` + SUP `/platform/applications…`); web `features/onboarding/` (`ApplyPage` at `/apply`, `PlatformApplicationsPage` at `/platform`), SUP → `/platform` redirect + nav.

### 1. Backend — migrate, seed, run, test

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # if no venv
pip install -r requirements.txt
# Migration chain (updated): merge_b_quiz_heads_2026_06 → add_quiz_source_columns
# → add_quiz_language → add_onboarding_applications → add_user_activation_token
alembic heads        # MUST print exactly ONE head: add_user_activation_token
alembic upgrade head # apply all; investigate if a 2nd head appears (merge it)
python -m app.seed   # seeds letter puzzles + superadmin (superadmin@ecole-platform.ma / superadmin123)
pytest -q            # run the suite; fix regressions
uvicorn app.main:app --reload   # smoke-test endpoints below
```

Smoke-test (with the server up):
- `POST /api/v1/applications/micro-school` (anonymous) with a JSON body → 201.
- Login as superadmin → `GET /api/v1/platform/applications?status=pending` → see it.
- `POST /api/v1/platform/applications/{id}/approve` → returns `activation_url` (+ `activation_token` outside production) + `created_school_id` + `created_user_id`. Verify a `School(school_type='informal')`, an **INACTIVE** owner `User` (with `activation_token_hash`/`activation_expires_at`), and an active `Membership(role_code='EDUCATOR')` were created. (Superseded the old invitation-code path — see §6 update.)
- `POST /api/v1/quizzes/from-content/{contentId}` (teacher) with `{"question_types":["MCQ","TRUE_FALSE"],"count":3,"sources":["template"]}` → draft quiz; confirm stems match the content language and `language` is stored.
- Optional: set `AI_PROVIDER=claude` + `AI_API_KEY` and re-run quiz gen with `"sources":["ai"]` to confirm the real provider path.

### 2. Web — install, typecheck, build, run

```bash
cd web
npm install          # pulls qrcode.react (added to package.json)
npm run build        # or: npx tsc --noEmit  → fix any TS errors
npm run dev
```
Click-through:
- Student → Games → **Letter Puzzle**: drag pieces into slots, audio per piece (ar/fr/en), confetti on finish. **Most likely fix: piece-to-slot pixel alignment** in `LetterPuzzleGame.tsx` (board uses `geom.col*CELL`/`geom.row*CELL`).
- Teacher content card → **Générer un quiz** → draft with source badges; open the quiz player → 🔊 per question speaks the right language.
- 2FA page: QR renders locally; SMS card; backup-codes copy + "saved" gate.
- `/apply` (logged out) → submit a formal + a micro application.
- Login as superadmin → lands on `/platform` → approve/reject; approval shows the invitation code.

### 3. Mobile — pub get, analyze, run

```bash
cd mobile
flutter pub get      # pulls confetti + qr_flutter
flutter analyze      # fix analyzer errors/warnings
flutter run
```
Click-through:
- Games → **Puzzle de lettres**: drag-drop jigsaw, confetti, TTS, letter picker (AppBar), pulls letters from backend (`/games/configs?game_type=letter_puzzle`), falls back to local Arabic offline. **Likely fix: piece/slot alignment** in `screens/letter_puzzle_screen.dart` (uses `_PieceGeom.bounds`).
- Teacher content card → quiz icon → generate sheet (localized) → draft.
- Student quiz player → 🔊 uses the quiz's stored language.

### 4. Finish the deferred items (the authoring agent intentionally left these)

1. **Onboarding attachments (uploads).** Model/schema already support
   `SchoolApplicationAttachment`. Add `POST /applications/{id}/attachments`
   (multipart `UploadFile`) wired to `app/core/storage.py`, enforce size/mime
   caps, and a web file-input on `ApplyPage`. (User explicitly wants uploads.)
2. **Invite email on approval.** `OnboardingService.approve` currently returns
   the plaintext invitation code (dev convention). Add an invitation email
   template and send it to `applicant_email` via `services/auth/email.py`.
3. **Rate-limit the public application endpoints** (`/applications/*`) and add
   basic anti-abuse (they're anonymous).
4. **SUP cross-tenant auth.** Confirm the SUP auth context isn't hard-locked to
   one `school_id`; platform endpoints must act across tenants. The seed gives
   SUP a membership under one school — verify/repair.
5. **Discoverability link.** Add a "Demande d'inscription → /apply" link on the
   web login page.
6. **Activation link (optional upgrade).** Today approved owners use the
   invitation-code path (reuses `/register`). If you want one-click onboarding,
   add a set-password activation token + `/auth/activate` + `/activate` page.
7. **Mobile 🔊 tooltip + onboarding form.** The mobile quiz 🔊 tooltip is still a
   hardcoded French string — add a key in `lib/l10n/app_localizations.dart`
   (`_translations` has `'fr'/'ar'/'en'` maps) and use `t.t(...)`. Optionally add
   a mobile public application form (web-first for now).
8. **Letter puzzle pixel polish.** After running, tune jigsaw knob curves /
   alignment on both platforms if pieces don't seat cleanly.

### 5. Definition of done

- `alembic upgrade head` clean (single head), `pytest` green, `npm run build`
  and `flutter analyze` clean.
- Every click-through in §2 and §3 works on a device/browser.
- Deferred items in §4 implemented (at least 1–5; 6 optional).

Report what you changed and anything that couldn't be made to work.

---

## SESSION UPDATE — one-click activation, resend, email model, tests, providers

This supersedes the invitation-code references above. The approved-owner flow is
now a **set-password activation link**, not an 8-char `/register` code.

### New migration

- `add_user_activation_token` (head; down_revision `add_onboarding_applications`)
  adds `users.activation_token_hash`, `users.activation_expires_at`, and index
  `idx_users_activation_token`. `alembic heads` must print exactly this one head.

### Backend behaviour to verify

- **approve** (`OnboardingService.approve`): creates the `School` + an **INACTIVE**
  owner `User` (`school_id` set, throwaway password hash, sha256 activation token,
  72h expiry) + an active `Membership` (ADM for formal, EDUCATOR for micro).
  Returns `activation_url`; `activation_token` is included **only when
  `APP_ENV != production`**. Email is per-school unique (`uq_users_email_school`)
  and each approval makes a fresh school, so the same person can own multiple
  schools.
- **`POST /auth/activate`** (public, rate-limited, in `AUTH_PATHS`): body
  `{token, password}`. Verifies the token hash against an INACTIVE user, checks
  expiry, **enforces the password policy** (`password_validator`), sets the
  password, flips status to ACTIVE, and clears the token (single use).
- **`POST /platform/applications/{id}/resend-activation`** (SUP): regenerates the
  token (72h) for an approved app whose owner is still INACTIVE, re-emails the
  link, invalidates the previous token. Rejects if already ACTIVE.
- Email template `app/templates/email/application_approved.html` now renders an
  `{{ activation_url }}` button (trilingual) instead of an invitation code.

Smoke-test (server up), continuing from §1:
- Take `activation_token` from the approve response (dev only) and
  `POST /api/v1/auth/activate` `{ "token": "<t>", "password": "SecurePass123!" }`
  → 200; the owner `User` is now ACTIVE with a null token.
- `POST /api/v1/auth/login` as that owner (email + new password + their
  `school_id`) → 200.
- Re-`POST /auth/activate` with the same token → 4xx (single use).
- `POST /platform/applications/{id}/resend-activation` (as SUP) → new
  `activation_url`; the old token no longer activates, the new one does.

### New tests

- `tests/unit/services/platform/test_onboarding_logic.py` — DB-free: role/
  school-type mapping, `_school_code` shape/uniqueness, token hashing,
  `ActivateRequest` + application-request schema validation.
- `tests/integration/api/onboarding/test_onboarding_activation.py` — DB-backed
  service flow: approve provisions account+membership+token; activate
  valid/reused/expired/weak-password/invalid; resend regenerates + invalidates.
  (Written but not executed by the authoring agent — run `pytest` and fix any
  fixture mismatch, e.g. password-policy specifics or the `db_session`
  commit/rollback interaction.)

### Web + mobile additions

- Web: `/activate` page (`ActivatePage.tsx`, fr/en/ar via `activate.*` keys),
  public route in `App.tsx`, `applicationsService.activate()` +
  `resendActivation()`, SUP console shows the activation link + a "🔁 Renvoyer le
  lien d'activation" button on approved rows.
- Mobile: native `ActivateScreen` (`/activate?token=`), added `/apply` **and**
  `/activate` to the router's public-page allowlist (the missing `/apply` entry
  was a latent redirect bug). Note: the emailed link is a **web** URL, so opening
  it on a phone lands on the responsive web page; the native screen is the
  in-app equivalent. True email→app deep linking still needs iOS/Android
  universal-link/app-link config (not done — known gap).

### Providers (mock → real)

See `backend/docs/PROVIDERS_MOCK_TO_REAL.md` for the exact env vars (AI / SMS /
email) and selection precedence. No code change needed to switch; AI auto-detects
Claude → open model → mock. Configure real SMTP before production so activation
emails actually deliver.

### Not done (intentional)

- Demo `SchoolApplication` seed rows are **kept** (needed for a product demo
  video) — do not remove before that's recorded.

## END PROMPT
