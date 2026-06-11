# Plan — Onboarding & SuperAdmin Approval (Formal School + Micro-École / Educator)

> Detailed implementation plan from the Codex discussion, verified against the
> code. Status: **planned**. Build is phased; backend first.

## 0. Goal

No school, admin, educator, teacher, parent, or student becomes active by public
self-registration. Instead:

```
Public application  →  SuperAdmin review (approve / reject / request-info)
                    →  provisioning (tenant + owner account)
                    →  owner activates (set password)  →  login
                    →  owner invites their members (existing invitation codes)
```

Two application types: **formal school** and **micro-école / educator**.

## 1. Locked decisions

| # | Decision |
|---|---|
| Micro-école tenant | On approval, create a **`School` with `school_type='informal'`** as the tenant; the EDUCATOR is its owner/member; `micro_schools` rows keep `educator_id` AND get that `school_id`. Reuses existing tenancy/billing/isolation. |
| Activation | **Both**: approved owners get an **account + set-password activation link** (reusing the existing account-recovery/reset infra). **Invitation codes stay** as how owners then onboard teachers/parents/students. |
| SuperAdmin UI (first build) | **MVP**: `/platform` console (SUP only) — applications queue, detail, approve / reject / request-info. Schools/educators lists later. |
| Attachments | **Included now**: applications support file uploads (ID, authorization docs, photos) via the existing storage pipeline. |

## 2. What already exists (verified)

- `schools.school_type` enum: `formal` | `informal` (+ validator). ✅
- `micro_schools` is **educator-owned** (`educator_id`), not nested under a formal school. ✅
- `RoleCode.SUP` + seeded `superadmin@ecole-platform.ma`. ✅ (UI minimal)
- Account-recovery / password-reset flow (`account_recovery_requests`, OTP, reset). ✅ → reuse for activation.
- Email service (`services/auth/email.py`, `delivery/email_delivery.py`) + content upload/storage pipeline. ✅
- Invitation + `/auth/register` (8-char code) flow. ✅ → stays for member onboarding.

## 3. What's missing (this feature)

1. Application data model + attachments.
2. Public application endpoints (anonymous, rate-limited).
3. SUP platform endpoints (list / approve / reject / request-info).
4. Provisioning on approval (school/informal-school + owner account + activation).
5. Activation (set-password) endpoint + page.
6. Web: public application form(s) + SUP console + activation page + `SUP → /platform` redirect.
7. (Later) Mobile application form.

## 4. Data model

**`schoolapplications`** (one table, typed):
- `id`, `application_type` (`formal_school` | `micro_school`)
- `status` (`pending` | `needs_info` | `approved` | `rejected`), default `pending`
- Applicant: `applicant_name`, `applicant_email`, `applicant_phone`, `city`, `language`
- Org: `org_name` (school / micro-école name), `address`, `neighborhood` (micro), `max_capacity` (micro), `level_band` / `subjects` (formal, JSONB)
- `notes` (applicant message), `review_notes` (SUP)
- Outcome: `reviewed_by` (FK users), `reviewed_at`, `created_school_id` (FK schools), `created_user_id` (FK users)
- Timestamps.
- Indexes: `(status, application_type)`, `applicant_email`.

**`schoolapplication_attachments`**:
- `id`, `application_id` (FK, cascade), `file_path`, `mime_type`, `file_size`, `kind` (`id_doc` | `authorization` | `photo` | `other`), `created_at`.

**Activation** (reuse account-recovery): on approval, create the owner user with
`status=INACTIVE` (no `PENDING` enum change needed), then issue a recovery/reset
token and email a set-password link. `/activate` = set password → `status=ACTIVE`.

Enums (new): `ApplicationType`, `ApplicationStatus`.

## 5. Backend endpoints

**Public (anonymous, rate-limited, multipart for files):**
- `POST /applications/formal-school`
- `POST /applications/micro-school`
- `POST /applications/{id}/attachments` (or multipart on create)
- `GET  /applications/status?email=&ref=` (optional: applicant checks status)

**SuperAdmin (`requires_permission` SUP / platform scope):**
- `GET  /platform/applications?type=&status=`
- `GET  /platform/applications/{id}`
- `POST /platform/applications/{id}/approve`
- `POST /platform/applications/{id}/reject` (body: reason)
- `POST /platform/applications/{id}/request-info` (body: message)

**Activation:**
- `POST /auth/activate` (token, new_password) — reuses recovery/reset internals.

## 6. Approval logic (`OnboardingService`)

`approve(application_id, auth)`:
- **formal_school** → create `School(school_type='formal', name=org_name, …)`; create owner `User(role target ADM, status=INACTIVE)` + membership(ADM); issue activation token; email set-password link; set `created_school_id`, `created_user_id`, `status=approved`.
- **micro_school** → create `School(school_type='informal', name=org_name)`; create owner `User(EDUCATOR, status=INACTIVE)` + membership(EDUCATOR); create `MicroSchool(educator_id=owner, school_id=informal tenant, name, neighborhood, city, phone, max_capacity)`; issue activation token; email; set outcome fields.
- Audit-log every transition. Idempotent (re-approve is a no-op once approved).

`reject` / `request-info` → set status + `review_notes`, email applicant.

## 7. Permissions / tenancy notes

- Platform endpoints require **SUP** and must **bypass school scoping** (cross-tenant). ⚠️ Verify the SUP auth context isn't hard-locked to one `school_id` (the seed gives SUP a membership under `SCHOOL_ID`). May need a "platform" auth path.
- Public endpoints: no auth → **rate-limit** + basic anti-abuse (email format, optional email verification before SUP sees it); cap attachment size/count/type.

## 8. Migration

New Alembic revision `add_onboarding_applications` (down_revision = current head
`add_quiz_language`): create the two tables. Additive only.

## 9. Web

- **Public**: `/apply` (choose type) → `FormalSchoolApplicationPage` / `MicroSchoolApplicationPage` with file upload; public success/status page.
- **SUP console**: route `/platform` (SUP only) → applications queue + detail drawer + approve/reject/request-info; add `SUP: '/platform'` to `roleRedirects.ts` + `Layout` nav.
- **Activation**: `/activate?token=…` → set-password page.

## 10. Mobile (later phase)

Application form + status check (educators often on mobile). Defer to a later
phase; web-first for the one-time onboarding.

## 11. Phases & sequencing

| Phase | Content | Verify |
|---|---|---|
| 1 | Models (`schoolapplications`, attachments) + enums + migration | parse, single head |
| 2 | Schemas + public application endpoints (+ attachments, rate limit) | parse, unit test pure validators |
| 3 | SUP platform endpoints + `OnboardingService.approve/reject/request-info` + activation endpoint | parse, unit tests for approval branching |
| 4 | Web public application forms (+ upload) | balance, build |
| 5 | Web SUP console + activation page + SUP redirect/nav | balance, build |
| 6 | Emails (reuse service), i18n (fr/en/ar), seed a demo application | — |
| 7 | Mobile application form | analyze |

## 12. Open risks

- **SUP cross-tenant access** — confirm/repair before platform endpoints rely on it.
- **Anonymous abuse** — rate limiting + attachment caps are mandatory.
- **Email deliverability** — mock in dev (consistent with existing mock SMS/email).
- **Can't run here** — every phase verified by parse/balance; real `alembic upgrade`, builds, and a click-through needed on your machine.

---

_Plan written against the verified current code. Decisions locked with the user._
