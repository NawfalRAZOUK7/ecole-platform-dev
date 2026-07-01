# MinIO Integration AI Agent Prompts

> Purpose: reusable prompts that can be executed with any capable AI coding agent to reproduce the MinIO integration described in `MINIO_INTEGRATION_ARCHITECTURE.md` and `minio-integration-plan.md`.
>
> These prompts are phase-separated, include context contracts, input/output expectations, anti-drift rules, and a suggested manual Git commit after each phase.

---

## How to Use This Document

1. Execute prompts **in order** unless a prompt is explicitly marked optional or parallelizable.
2. Before each prompt, make sure the working tree is clean or intentionally staged.
3. After each prompt, review the diff manually.
4. Run the validation commands suggested by the agent.
5. Commit manually using the suggested commit message.
6. Do **not** let an agent skip validation or silently change architecture decisions.

---

## Global Context Contract for All Prompts

Every prompt in this file assumes the following project context:

- Existing enterprise educational platform.
- Backend: FastAPI.
- Web: React / Vite.
- Mobile: Flutter.
- Existing local file storage under `uploads/`.
- Existing abstractions:
  - `backend/app/core/storage.py` with `StorageBackend` and `LocalStorageBackend`.
  - `backend/app/services/file_storage.py` with `FileStorageBackend`, local backend, and an existing S3-like backend.
- Existing DB already stores relative file paths such as:
  - `storage_path`
  - `file_path`
  - `exercise_pdf_path`
  - `thumbnail_path`
- **No DB schema change is required** for the foundational MinIO rollout.
- Existing auth and authorization rules must remain authoritative.
- Existing service-layer logic must not be bypassed.

### Global Architecture Decisions

- One private bucket per environment:
  - `ecole-dev-private`
  - `ecole-staging-private`
  - `ecole-prod-private`
- Tenant and domain isolation via object key prefixes.
- Private bucket; no anonymous reads.
- Backend authorizes requests, then issues presigned URLs.
- Download endpoints keep backward compatibility through `302` redirects.
- New clients can request JSON metadata using `?as=metadata`.
- S3-compatible access implemented with `aioboto3`.
- Keep `LocalStorageBackend` as fallback for dev/tests.
- Do not introduce a third storage abstraction.

### Global Anti-Drift Rules

- Do not change DB schema unless explicitly asked in a later prompt.
- Do not delete existing local storage support.
- Do not replace service-layer authorization with storage-layer checks.
- Do not expose MinIO credentials to web or mobile clients.
- Do not make buckets public.
- Do not stream large download bytes through FastAPI after API adaptation.
- Do not create bucket-per-school architecture.
- Do not hardcode bucket names, endpoints, or credentials.
- Do not add HLS/transcoding in the foundational phases.
- Do not implement direct-to-MinIO upload before the optional large-upload phase.
- Do not silently rename existing endpoints.
- Do not break current web/mobile clients during Phases 1–5.

---

## Prompt 0 — Baseline Recon and Implementation Map

**Recommended model:** Claude Sonnet / ChatGPT / SWE-agent / Codex
**Estimated complexity:** low (read-only)

### Objective

Ask the agent to inspect the existing repository and produce a concise implementation map before modifying anything.

**Prerequisites:** none — entry point of the integration.
**Out of scope:** any code changes; this is reconnaissance only.

### Prompt

```text
You are a senior backend architect and AI coding agent working in an existing enterprise educational platform.

CONTEXT CONTRACT:
- Read these two files first:
  - MINIO_INTEGRATION_ARCHITECTURE.md
  - minio-integration-plan.md
- The platform has FastAPI backend, React/Vite web app, Flutter mobile app.
- Existing storage abstractions exist in:
  - backend/app/core/storage.py
  - backend/app/services/file_storage.py
- DB already stores relative file paths. No DB schema change is needed for foundational MinIO rollout.
- Goal is to integrate MinIO/S3-compatible storage without breaking existing logic.

INPUT:
- Current repository state.
- The two MinIO planning documents listed above.

TASK:
1. Inspect the files and routes related to storage, uploads, downloads, documents, submissions, assignments, content assets, Docker compose, and config.
2. Produce an implementation map that identifies:
   - Files to modify.
   - Tests likely affected.
   - Existing call sites of storage.read/local_path/FileResponse.
   - Existing local upload paths.
   - Existing S3/document config fields.
3. Do not edit files yet.

OUTPUT CONTRACT:
- Return a concise Markdown report only.
- Include a section titled "Implementation Map".
- Include a section titled "High-Risk Areas".
- Include a section titled "Recommended Phase Order".
- Include exact file paths discovered.

ANTI-DRIFT RULES:
- Do not propose DB schema changes.
- Do not propose bucket-per-school.
- Do not propose public buckets.
- Do not propose direct upload before foundational backend storage is done.
- Do not write code.

VALIDATION:
- The report must explicitly mention whether any hidden direct filesystem access exists outside the two storage abstractions.
```

### Rollback

N/A — read-only step, no changes to revert.

### Suggested manual Git commit

No commit required. This is a read-only reconnaissance step.

---

## Prompt 1 — Phase 1 Infrastructure: Add MinIO to Docker Compose

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** low

### Objective

Add local MinIO infrastructure with bucket initialization, lifecycle rules, environment variables, and no backend behavior change.

**Prerequisites:** Prompt 0 reviewed.
**Out of scope:** any change inside `backend/`, `web/`, or `mobile/` source code.

### Prompt

```text
You are a senior DevOps/backend engineer implementing Phase 1 of the MinIO integration.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Follow Phase 1 only.
- Do not modify backend application logic yet.
- Default storage backend must remain local until a later phase.

INPUT:
- Existing infra/docker-compose.dev.yml.
- Existing infra/docker-compose.staging.yml and infra/docker-compose.prod.yml if present.
- Existing .env.example.

TASK:
1. Add a MinIO service to infra/docker-compose.dev.yml.
2. Add a one-shot minio-init service using minio/mc.
3. Create the dev bucket ecole-dev-private.
4. Keep bucket private: no anonymous access.
5. Enable SSE-S3 if supported by MinIO/mc in this compose context.
6. Add lifecycle rules where practical:
   - submissions expire after 730 days.
   - temporary or preview assets can expire according to the plan.
   - permanent documents/content/videos/audio do not expire by default.
7. Add minio_data volume.
8. Add MinIO/S3 variables to .env.example.
9. If staging/prod compose files exist, add equivalent env wiring or clear comments for managed MinIO/S3 usage, but avoid embedding secrets.

OUTPUT CONTRACT:
- Modify only infrastructure/config documentation files needed for Phase 1.
- Do not change Python, TypeScript, or Dart application logic.
- Return a summary of changed files.
- Return exact validation commands to run.

ANTI-DRIFT RULES:
- Do not set STORAGE_BACKEND=s3 by default yet.
- Do not remove upload_data volume yet.
- Do not expose MinIO publicly beyond localhost bindings in dev.
- Do not commit real credentials.
- Do not create public buckets.
- Do not create one bucket per school.

VALIDATION:
- docker compose dev stack can start minio and minio-init.
- minio-init exits successfully.
- bucket ecole-dev-private exists.
- bucket is private.
- backend container can reach http://minio:9000, but backend behavior is still local.
```

### Rollback

`git revert` the compose changes; `docker volume rm minio_data` only if the volume is empty.

### Suggested manual Git commit

```text
git commit -m "chore(infra): add MinIO dev storage services"
```

---

## Prompt 2 — Phase 2A Backend Config: Add S3/MinIO Settings

**Recommended model:** Claude Sonnet / ChatGPT / Codex
**Estimated complexity:** low

### Objective

Add clean configuration fields for selecting local vs S3 storage and connecting to MinIO, without changing runtime behavior yet.

**Prerequisites:** Prompt 1 merged.
**Out of scope:** implementing `S3StorageBackend` (that is Prompt 3); changing default storage backend.

### Prompt

```text
You are a senior FastAPI backend engineer implementing Phase 2A of the MinIO integration.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- This prompt is config-only.
- Default runtime behavior must remain local storage.

INPUT:
- backend/app/core/config.py
- .env.example
- Any test/config files that validate settings.

TASK:
1. Add or consolidate settings for:
   - STORAGE_BACKEND = local | s3, default local
   - S3_ENDPOINT
   - S3_REGION
   - S3_ACCESS_KEY
   - S3_SECRET_KEY
   - S3_BUCKET
   - S3_FORCE_PATH_STYLE
   - S3_SSE_ENABLED
   - S3_PRESIGN_GET_TTL_SECONDS
   - S3_PRESIGN_PUT_TTL_SECONDS
2. Avoid duplicating existing document_storage_* settings unless necessary.
3. If both generic S3 settings and document_storage_* settings exist, define a clear compatibility plan:
   - either map document settings to generic settings,
   - or keep backward-compatible aliases.
4. Update .env.example with safe placeholders.
5. Add/adjust tests if settings parsing is covered.

OUTPUT CONTRACT:
- Changed files only related to settings/env examples/tests.
- No storage backend implementation yet.
- Return a summary of changed settings and backward compatibility behavior.

ANTI-DRIFT RULES:
- Do not change default from local to s3.
- Do not remove existing document storage settings if callers still use them.
- Do not hardcode dev bucket in Python code.
- Do not add DB migrations.

VALIDATION:
- App settings load with no S3 env vars.
- App settings load with dev MinIO env vars.
- Existing tests still pass.
```

### Rollback

`git revert` the config changes; `STORAGE_BACKEND` defaults remain `local`, so runtime is unaffected.

### Suggested manual Git commit

```text
git commit -m "chore(config): add S3 storage settings"
```

---

## Prompt 3 — Phase 2B Backend Storage Layer: Implement S3StorageBackend

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** medium

### Objective

Implement an S3-compatible backend using `aioboto3` behind the existing `StorageBackend` abstraction.

**Prerequisites:** Prompt 2 merged.
**Out of scope:** modifying `backend/app/services/file_storage.py` (that is Prompt 4); modifying API route handlers (that is Prompt 6).

### Prompt

```text
You are a senior FastAPI backend engineer implementing Phase 2B of the MinIO integration.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Existing StorageBackend lives in backend/app/core/storage.py.
- Keep LocalStorageBackend intact.
- Add S3StorageBackend using aioboto3.
- Keep current callers working.

INPUT:
- backend/app/core/storage.py
- backend/app/core/config.py
- backend dependency file (pyproject.toml, requirements, or equivalent)
- Existing storage tests, if any.

TASK:
1. Add aioboto3 dependency.
2. Extend or adapt StorageBackend to support:
   - save
   - read or access-url behavior compatible with existing callers
   - delete
   - exists
   - presign_get
   - stat/head metadata
3. Implement S3StorageBackend using aioboto3.
4. Implement a storage factory that returns LocalStorageBackend or S3StorageBackend based on STORAGE_BACKEND.
5. Preserve the existing import pattern if callers do `from app.core.storage import storage`.
6. Ensure save still returns relative path, sha256 checksum, and size.
7. Ensure keys are relative paths and do not include bucket name.
8. Add unit tests with mocked/fake S3 where practical.

OUTPUT CONTRACT:
- Modify backend storage code and dependency files only.
- Include tests for save/exists/delete/stat/presign behavior.
- Return validation commands.

ANTI-DRIFT RULES:
- Do not remove LocalStorageBackend.
- Do not alter service-layer business logic.
- Do not introduce a second unrelated storage abstraction.
- Do not use sync boto3 in async request paths.
- Do not stream S3 downloads to temp files for normal user downloads.
- Do not make the bucket public.

VALIDATION:
- Existing local storage tests pass with STORAGE_BACKEND=local.
- New S3 backend tests pass.
- With STORAGE_BACKEND=s3 and dev MinIO running, a small file can be saved, stat'ed, presigned, downloaded, and deleted.
```

### Rollback

`git revert` the storage changes; with `STORAGE_BACKEND=local`, the local backend remains active.

### Suggested manual Git commit

```text
git commit -m "feat(storage): add S3-compatible backend"
```

---

## Prompt 4 — Phase 2C Unify Document FileStorageBackend

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** medium-high

### Objective

Make `backend/app/services/file_storage.py` use the new S3-compatible storage behavior consistently, removing unsafe tempfile download patterns where possible.

**Prerequisites:** Prompt 3 merged.
**Out of scope:** modifying API routes (that is Prompt 6); changing the `Document` DB schema.

### Prompt

```text
You are a senior backend engineer unifying the platform's document file storage with the new S3-compatible backend.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- There are two storage layers today:
  - backend/app/core/storage.py
  - backend/app/services/file_storage.py
- Phase 16 document storage currently has local and S3-like support.
- Keep public method signatures stable where callers depend on them.

INPUT:
- backend/app/services/file_storage.py
- backend/app/core/storage.py
- backend/app/services/student_documents.py
- backend/app/services/lms/content_service.py
- Tests related to documents and uploads.

TASK:
1. Rewire file_storage.py so document storage uses the same S3 settings and async S3 behavior as core storage.
2. Preserve existing high-level methods:
   - store_upload
   - reuse_upload
   - store_upload_copy
   - exists
   - delete
3. Review all callers of local_path/read_bytes/tempfile behavior.
4. Replace normal user-download tempfile behavior with presigned URL access in later API phase, not here.
5. Keep thumbnail generation working for images.
6. Keep deduplication by sha256 working.
7. Keep virus_scan_hook behavior working for backend-mediated uploads.
8. Add or update tests for document storage under local and S3 modes.

OUTPUT CONTRACT:
- Modify only backend document/storage-related files and tests.
- Return a list of any remaining local_path call sites and why they are safe or need later work.

ANTI-DRIFT RULES:
- Do not change Document DB schema.
- Do not break document versioning behavior.
- Do not remove deduplication.
- Do not remove thumbnail generation.
- Do not silently read large S3 objects fully into memory unless the caller requires it and size is bounded.

VALIDATION:
- Existing document upload tests pass.
- Existing coloring page save flow passes.
- S3-backed document upload can store and reuse an object.
- Thumbnail generation still works for image uploads.
```

### Rollback

`git revert` the `file_storage.py` changes; the previous local + S3-like document storage logic resumes.

### Suggested manual Git commit

```text
git commit -m "refactor(storage): unify document storage backend"
```

---

## Prompt 5 — Phase 3A Download Metadata and Redirect Helper

**Recommended model:** Claude Sonnet / ChatGPT / Codex
**Estimated complexity:** low

### Objective

Create reusable backend helpers/schemas for returning download metadata or redirecting to presigned URLs.

**Prerequisites:** Prompts 3 and 4 merged.
**Out of scope:** updating endpoints to use the helper (that is Prompt 6).
**Note for FastAPI:** the URL must be `?as=metadata`, but `as` is a reserved Python keyword. Declare the parameter as `as_: str | None = Query(None, alias="as")` so the URL stays `?as=metadata` while Python sees `as_`.

### Prompt

```text
You are a senior FastAPI backend engineer implementing the shared API download layer for MinIO.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Existing download endpoints currently use FileResponse.
- New behavior:
  - default: 302 redirect to presigned URL
  - optional: ?as=metadata returns JSON
- Authorization must happen before generating the presigned URL.

INPUT:
- backend/app/api/v1/* route files that download files.
- backend/app/schemas or equivalent schema directory.
- backend/app/core/storage.py.

TASK:
1. Add a reusable DownloadMetadata schema with:
   - download_url
   - expires_at
   - mime_type
   - size
   - filename
   - etag optional
2. Add a reusable helper for:
   - generating metadata response
   - generating RedirectResponse
   - applying filename/content-disposition behavior through presign params
3. Support query parameter `?as=metadata`. In FastAPI, declare it as `as_: str | None = Query(None, alias="as")` because `as` is a reserved Python keyword.
4. Keep helper generic enough for submissions, content assets, exercise PDFs, and documents.
5. Add focused unit tests for the helper.

OUTPUT CONTRACT:
- Add reusable schema/helper code.
- Do not yet modify every endpoint unless straightforward.
- Return the exact helper API and example usage.

ANTI-DRIFT RULES:
- Do not skip endpoint-level authorization.
- Do not make presign helper accept arbitrary unaudited paths from clients.
- Do not use public URLs.
- Do not put MinIO credentials in responses.
- Do not change existing route paths.

VALIDATION:
- Helper tests pass.
- Metadata JSON shape is stable and documented in tests.
- Redirect response includes a MinIO/S3 presigned Location.
```

### Rollback

`git revert` the helper/schema additions; no endpoints depend on it yet.

### Suggested manual Git commit

```text
git commit -m "feat(api): add signed download response helpers"
```

---

## Prompt 6 — Phase 3B Adapt Download Endpoints to 302 + Metadata

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** medium

### Objective

Convert all relevant download endpoints to presigned URL redirects while preserving backward compatibility.

**Prerequisites:** Prompt 5 merged (helper and schema available).
**Out of scope:** changing upload endpoints; renaming any route path or HTTP method.
**Note for FastAPI:** `as` is a Python reserved keyword — use `as_: str | None = Query(None, alias="as")` so the public URL stays `?as=metadata`.

### Prompt

```text
You are a senior FastAPI backend engineer adapting existing file download endpoints to signed MinIO access.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Phase 3A helper/schema already exists.
- Existing clients must continue working.
- Default response must be 302 redirect to presigned URL.
- `?as=metadata` must return JSON metadata.

INPUT:
- backend/app/api/v1/submissions.py
- backend/app/api/v1/content.py
- backend/app/api/v1/assignments.py or equivalent assignment routes
- backend/app/services/lms/_helpers.py
- Document download route files
- Existing endpoint tests.

TASK:
1. Update submission file download endpoint.
2. Update content asset download endpoint.
3. Update content stream compatibility endpoint.
4. Update assignment exercise PDF download endpoint.
5. Update document download endpoints if present.
6. Preserve all existing ACL checks and school boundary checks.
7. Preserve old route paths and HTTP methods.
8. Add/update tests:
   - default request returns 302
   - metadata request returns JSON
   - unauthorized user cannot receive a presigned URL
   - missing file returns existing error shape
9. Ensure local backend mode still works in tests/dev.

OUTPUT CONTRACT:
- Modify only backend API/service/tests needed for download behavior.
- Return changed endpoints list.
- Return validation commands.

ANTI-DRIFT RULES:
- Do not return raw storage paths to clients.
- Do not bypass service methods that enforce permissions.
- Do not break existing upload endpoints.
- Do not introduce direct MinIO dependency in route code if storage helper can abstract it.
- Do not convert uploads to direct PUT in this phase.

VALIDATION:
- curl with auth to old download URL returns 302.
- curl with auth and ?as=metadata returns JSON.
- Following 302 downloads the file.
- Range request against Location URL returns 206 for video/audio-capable objects.
- Existing web/mobile flows remain functional.
```

### Rollback

`git revert` the route changes; `FileResponse`-based behavior resumes (LocalStorageBackend mode also still works).

### Suggested manual Git commit

```text
git commit -m "feat(api): serve downloads via presigned redirects"
```

---

## Prompt 7 — Phase 4 Data Migration Script

**Recommended model:** Claude Sonnet / Codex / ChatGPT
**Estimated complexity:** medium

### Objective

Create an idempotent migration script to copy existing local `uploads/` content into MinIO while preserving relative paths.

**Prerequisites:** Prompt 3 merged (S3 backend functional).
**Out of scope:** mutating any DB record; deleting local files.

### Prompt

```text
You are a senior backend engineer writing a safe production migration script for local uploads to MinIO.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- DB stores relative paths. Those paths must become S3 object keys as-is.
- Script must be idempotent and safe to re-run.
- Do not alter DB records.

INPUT:
- Existing uploads directory structure.
- backend/app/core/config.py
- backend/app/core/storage.py or S3 client helper.
- scripts/ directory conventions.

TASK:
1. Create scripts/migrate_local_to_minio.py.
2. Add CLI flags:
   - --source
   - --bucket
   - --dry-run
   - --verify-sample
   - --concurrency
   - --prefix optional if needed
3. Walk source directory recursively.
4. For every local file, compute object key as path relative to source.
5. HEAD destination object before PUT.
6. Skip existing objects with matching size/checksum when possible.
7. Upload missing or mismatched objects.
8. Preserve MIME content type using safe mimetype guessing.
9. Add bounded concurrency.
10. Add verification sample that downloads objects and compares SHA-256.
11. Emit a JSON summary under artifacts/.
12. Add tests for dry-run and key mapping where practical.

OUTPUT CONTRACT:
- Add migration script and tests only.
- Do not run the migration automatically.
- Return exact dry-run and real-run commands for dev/staging/prod.

ANTI-DRIFT RULES:
- Do not mutate DB.
- Do not delete local files.
- Do not assume bucket is public.
- Do not read huge files fully into memory.
- Do not fail entire migration on one file without reporting it.
- Do not hardcode dev bucket.

VALIDATION:
- Dry run reports expected file count.
- Real run uploads files to MinIO.
- Re-running real run skips already-migrated files.
- Verification sample passes.
```

### Rollback

The script is read-from-source; no DB or local file changes happen. To remove migrated objects: `mc rm --recursive --force ecole/<bucket>/<prefix>` against the dev bucket.

### Suggested manual Git commit

```text
git commit -m "feat(storage): add local uploads to MinIO migration script"
```

---

## Prompt 8 — Phase 5 Switch Backend to MinIO Safely

**Recommended model:** Claude Sonnet / ChatGPT / SWE-agent
**Estimated complexity:** low (docs)

### Objective

Prepare the environment flip from local storage to MinIO, including rollout steps, smoke tests, rollback, and cleanup of local volume references after grace period.

**Prerequisites:** Prompts 1–7 merged.
**Out of scope:** any application code change; flipping production env automatically; removing `upload_data` volume immediately.

### Prompt

```text
You are a senior technical lead preparing the safe rollout from local filesystem storage to MinIO.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Phases 1–4 are implemented.
- Do not remove local storage code.
- Environment switch is controlled by STORAGE_BACKEND.

INPUT:
- infra/docker-compose.dev.yml
- infra/docker-compose.staging.yml
- infra/docker-compose.prod.yml
- .env.example
- INSTALLATION.md or deployment docs
- Existing smoke test docs/scripts.

TASK:
1. Update docs with exact rollout order:
   - dev
   - staging
   - prod
2. Add or update smoke test checklist for uploads/downloads:
   - assignment exercise PDF
   - submission file
   - content asset
   - document
   - video/audio if sample files exist
3. Document rollback:
   - set STORAGE_BACKEND=local
   - restart backend/worker
   - keep uploads volume during grace period
4. Prepare compose cleanup instructions for later removal of upload_data volume, but do not remove it unless explicitly requested.
5. Ensure .env.example clearly says STORAGE_BACKEND defaults to local until migration is complete.
6. If project has deployment docs, update them.

OUTPUT CONTRACT:
- Documentation and deployment config comments only unless a small smoke script already exists and can be safely extended.
- Do not flip production env automatically.
- Return a rollout checklist.

ANTI-DRIFT RULES:
- Do not remove upload_data immediately.
- Do not delete uploads directory.
- Do not remove LocalStorageBackend.
- Do not make s3 the code default.
- Do not run migrations automatically.

VALIDATION:
- A human can follow the rollout doc step-by-step.
- Rollback path is explicit and quick.
- No application behavior changes occur just by merging this documentation.
```

### Rollback

`git revert` the doc changes; no application behavior was modified.

### Suggested manual Git commit

```text
git commit -m "docs(storage): document MinIO rollout and rollback"
```

---

## Prompt 9 — Phase 5B Optional Cleanup After Stable Rollout

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** low

### Objective

After MinIO has been stable for the agreed grace period, remove obsolete local upload volume mounts from compose while keeping local backend code.

**Prerequisites:** Prompt 8 rolled out and stable for at least 30 days in the target environment.
**Out of scope:** removing `LocalStorageBackend` or any application code; deleting files from disk.

### Prompt

```text
You are a senior DevOps engineer performing post-rollout cleanup after MinIO has been stable for at least 30 days.

CONTEXT CONTRACT:
- Only execute this prompt after Phase 5 has been stable in the target environment.
- LocalStorageBackend code must remain.
- Local uploads have been archived and verified.

INPUT:
- infra/docker-compose.dev.yml
- infra/docker-compose.staging.yml
- infra/docker-compose.prod.yml
- Deployment docs.

TASK:
1. Remove upload_data volume mounts from backend and worker services where MinIO is now the source of truth.
2. Remove top-level upload_data volume declarations if unused.
3. Update docs to say uploads are stored in MinIO, not local Docker volume.
4. Keep local backend code and local test configuration intact.

OUTPUT CONTRACT:
- Modify compose/docs only.
- Return explicit confirmation that local backend code remains.

ANTI-DRIFT RULES:
- Do not remove LocalStorageBackend.
- Do not delete files from disk.
- Do not remove upload_data if any service still depends on it.
- Do not run destructive Docker volume commands.

VALIDATION:
- Compose config validates.
- Backend starts without /app/uploads mount when STORAGE_BACKEND=s3.
- Tests using LocalStorageBackend still pass.
```

### Rollback

`git revert` the compose changes; re-add `upload_data` mounts for `backend` and `worker` and the top-level volume declaration if needed.

### Suggested manual Git commit

```text
git commit -m "chore(infra): remove obsolete local upload volume"
```

---

## Prompt 10 — Phase 6 Web Integration with Signed URLs

**Recommended model:** Claude Sonnet / ChatGPT / Codex
**Estimated complexity:** medium

### Objective

Update the React web app to use metadata endpoints and signed URLs directly for downloads, previews, video, audio, and PDFs.

**Prerequisites:** Prompt 6 merged (backend metadata variant exists).
**Out of scope:** any backend change; replacing existing upload progress logic; embedding S3 credentials in the browser.

### Prompt

```text
You are a senior frontend engineer integrating signed MinIO URLs into the React/Vite web app.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Backend already supports default 302 and ?as=metadata JSON.
- Existing web upload behavior must remain unchanged.
- Web should use signed URLs natively for rendering/downloading.

INPUT:
- web/src/services/api/client.ts
- web/src/features/submissions/submissions.service.ts
- web/src/features/cms/cms.service.ts
- Existing hooks using TanStack Query.
- Existing media/PDF rendering components.

TASK:
1. Add a typed DownloadMetadata interface.
2. Add API helper to request `?as=metadata`.
3. Add `useSignedUrl` hook using TanStack Query.
4. Cache signed URLs for about 80% of TTL.
5. Update submission downloads to use signed URLs.
6. Update CMS/content asset previews to use signed URLs.
7. Render:
   - videos with `<video src={url} controls>`
   - audio with `<audio src={url} controls>`
   - PDFs with iframe/pdf viewer using the URL
8. Refresh metadata when a signed URL expires or returns 403.
9. Keep old fallback behavior where useful.
10. Add/update frontend tests if the project has them.

OUTPUT CONTRACT:
- Modify web app files only.
- Do not change backend.
- Return changed components/services and manual QA steps.

ANTI-DRIFT RULES:
- Do not send MinIO credentials to browser.
- Do not use raw storage paths as public URLs.
- Do not remove existing upload progress behavior.
- Do not fetch large media as Blob before playback.
- Do not bypass backend authorization; always get URLs from backend metadata endpoint.

VALIDATION:
- Web downloads still work.
- Video playback uses direct MinIO URL and supports seeking.
- Audio playback uses direct MinIO URL.
- PDF preview works.
- Expired URL refreshes cleanly.
- Browser DevTools shows media bytes coming from MinIO/CDN, not FastAPI.
```

### Rollback

`git revert` the web changes; the previous fetch/blob path resumes (backend still serves both 302 and metadata).

### Suggested manual Git commit

```text
git commit -m "feat(web): consume signed storage URLs"
```

---

## Prompt 11 — Phase 7 Mobile Integration with Signed URLs

**Recommended model:** Claude Sonnet / ChatGPT / Kimi / Codex
**Estimated complexity:** medium

### Objective

Update the Flutter app to request signed URL metadata from the backend and feed URLs to native media/PDF viewers.

**Prerequisites:** Prompt 6 merged.
**Out of scope:** any backend change; replacing existing upload flow; embedding S3 credentials in the mobile app.

### Prompt

```text
You are a senior Flutter engineer integrating signed MinIO URLs into the mobile app.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Backend already supports ?as=metadata for downloads.
- Existing upload behavior must remain unchanged.
- Mobile clients must never receive MinIO credentials.

INPUT:
- mobile/lib/data/api/api_client.dart
- Existing repositories/services for submissions/content/documents.
- Existing screens/widgets for video/audio/PDF/files.

TASK:
1. Add a DownloadMetadata model.
2. Add `fetchSignedUrl` or equivalent method to ApiClient.
3. Add a small in-memory SignedUrlCache with expiry safety margin.
4. Wire video playback to signed URL using existing video player package or `video_player`.
5. Wire audio playback to signed URL using existing audio player or `just_audio`.
6. Wire PDF viewing to signed URL or download-to-temp-file using signed URL.
7. Refetch URL on expiry/403/app resume.
8. Keep existing upload multipart flows unchanged.
9. Add tests where the mobile project supports them.

OUTPUT CONTRACT:
- Modify mobile app files only.
- Do not change backend.
- Return changed files and manual QA steps for iOS and Android.

ANTI-DRIFT RULES:
- Do not embed S3/MinIO credentials in the mobile app.
- Do not use raw storage paths as URLs.
- Do not download entire videos before playback.
- Do not change backend endpoint contracts.
- Do not remove existing upload progress callbacks.

VALIDATION:
- Video plays and seek works on Android and iOS.
- Audio plays reliably.
- PDF opens from signed URL or temp file.
- URL refresh works after expiry/app resume.
- Existing upload tests/flows still pass.
```

### Rollback

`git revert` the mobile changes; the previous download path resumes (backend still serves both 302 and metadata).

### Suggested manual Git commit

```text
git commit -m "feat(mobile): consume signed storage URLs"
```

---

## Prompt 12 — Phase 8A Large Upload API Design Only

**Recommended model:** Claude Sonnet / ChatGPT
**Estimated complexity:** medium (design)

### Objective

Design the direct-to-MinIO upload API without coding it yet, including states, security checks, and endpoint contracts.

**Prerequisites:** Prompts 1–8 merged.
**Out of scope:** writing implementation code; implementing HLS or transcoding.

### Prompt

```text
You are a senior backend architect designing direct-to-MinIO large file upload support.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Foundational MinIO integration is already complete.
- This is design-only. Do not write code.
- Direct uploads are optional Phase 8.

INPUT:
- Current backend models and routes for content assets, submissions, videos/audio if present.
- Existing permission/auth patterns.
- Current upload size limits.

TASK:
1. Design API endpoints:
   - POST /uploads/init
   - POST /uploads/complete
   - Optional GET /uploads/{id}/status
2. Define request/response schemas.
3. Define upload states:
   - uploading
   - scanning
   - available
   - failed
   - quarantined
4. Define authorization rules by upload kind:
   - assignment PDFs
   - submission files
   - content assets
   - videos
   - audio
5. Define validation rules:
   - MIME types
   - size limits
   - content length
   - object key prefix
6. Define ARQ worker responsibilities for post-upload scan/thumbnail.
7. Identify whether any DB state additions are required for Phase 8.
8. Produce a migration-safe plan if DB changes are needed.

OUTPUT CONTRACT:
- Markdown design report only.
- Include endpoint tables, schema examples, state transitions, and risks.
- Do not edit files.

ANTI-DRIFT RULES:
- Do not implement HLS/transcoding.
- Do not bypass virus scanning.
- Do not make unscanned uploads visible.
- Do not expose S3 credentials to clients.
- Do not assume all upload kinds need the same DB changes.

VALIDATION:
- Design is implementable in small PRs.
- Design clearly states whether DB migrations are needed.
```

### Rollback

N/A — design report only.

### Suggested manual Git commit (if report is saved)

```text
git commit -m "docs(storage): design direct large-file uploads"
```

---

## Prompt 13 — Phase 8B Implement Direct Large Uploads

**Recommended model:** Claude Sonnet / Codex / SWE-agent
**Estimated complexity:** high

### Objective

Implement direct-to-MinIO large uploads using presigned PUT, post-upload validation, and background scanning.

**Prerequisites:** Prompt 12 design accepted.
**Out of scope:** modifying web/mobile direct upload clients (Prompts 14 and 15); skipping virus scanning.

### Prompt

```text
You are a senior FastAPI backend engineer implementing direct large-file uploads to MinIO.

CONTEXT CONTRACT:
- Execute only after Prompt 12 design has been approved.
- Foundational MinIO integration is complete.
- Clients must upload directly to MinIO using presigned PUT.
- Backend must validate before and after upload.

INPUT:
- Approved Phase 8 design document.
- backend/app/core/storage.py
- backend/app/api/v1 routes
- ARQ worker/task setup
- Relevant models/services for upload targets.

TASK:
1. Add presign_put support to S3StorageBackend.
2. Add POST /uploads/init.
3. Add POST /uploads/complete.
4. Add upload status tracking if approved by design.
5. Add ARQ post-upload scan task.
6. Make uploaded objects unavailable until scan passes.
7. Add lifecycle cleanup for incomplete uploads.
8. Add backend tests for:
   - init authorization
   - presigned PUT generation
   - complete validation
   - scan success
   - scan/quarantine failure
   - expired/incomplete upload cleanup

OUTPUT CONTRACT:
- Backend implementation and tests only.
- Do not modify web/mobile direct upload clients in this prompt.
- Return endpoint docs and validation commands.

ANTI-DRIFT RULES:
- Do not skip post-upload HEAD validation.
- Do not make scanning optional for user-uploaded files.
- Do not expose uploads before available state.
- Do not use public buckets.
- Do not hardcode size limits.

VALIDATION:
- A large test file can be uploaded via presigned PUT.
- Complete endpoint validates MinIO object metadata.
- Unscanned object is not visible to users.
- Clean object becomes available.
- Infected test object is quarantined/deleted.
```

### Rollback

`git revert` the upload routes and worker; the lifecycle rule on `uploading` state cleans up orphaned objects after 24 h.

### Suggested manual Git commit

```text
git commit -m "feat(storage): support direct large uploads"
```

---

## Prompt 14 — Phase 8C Web Direct Upload Client

**Recommended model:** Claude Sonnet / ChatGPT / Codex
**Estimated complexity:** medium

### Objective

Update the web app to use direct presigned PUT for large uploads while preserving old multipart uploads for small files or unsupported kinds.

**Prerequisites:** Prompt 13 merged.
**Out of scope:** removing the existing multipart upload path; backend changes.

### Prompt

```text
You are a senior React frontend engineer implementing direct large-file uploads to MinIO.

CONTEXT CONTRACT:
- Backend direct upload API is implemented and tested.
- Existing small-file upload behavior must remain available as fallback.
- Browser must not receive S3 credentials, only presigned PUT URLs.

INPUT:
- Web upload services/components for submissions/content/video/audio.
- Backend upload API contract from Phase 8.

TASK:
1. Add direct upload service:
   - init request
   - XMLHttpRequest PUT to upload_url with progress
   - complete request
   - status polling if needed
2. Use direct upload only for files above configured threshold or for video/audio kinds.
3. Preserve existing multipart upload for small files.
4. Add progress UI states:
   - preparing
   - uploading
   - processing/scanning
   - available
   - failed
5. Add retry behavior for init/complete, but not unsafe blind retry for PUT unless resumable behavior exists.
6. Add frontend tests where available.

OUTPUT CONTRACT:
- Web app implementation only.
- Do not change backend.
- Return manual QA steps.

ANTI-DRIFT RULES:
- Do not store upload_url permanently.
- Do not log presigned URLs in production logs.
- Do not send Authorization header to MinIO PUT URL unless required by signature.
- Do not remove old multipart path.

VALIDATION:
- Large video upload shows progress.
- Complete call marks asset processing/available.
- Small uploads still use old path.
- Failed upload surfaces useful UI error.
```

### Rollback

`git revert` the web direct-upload changes; the existing multipart upload path remains the fallback.

### Suggested manual Git commit

```text
git commit -m "feat(web): add direct large-file uploads"
```

---

## Prompt 15 — Phase 8D Mobile Direct Upload Client

**Recommended model:** Claude Sonnet / Kimi / ChatGPT / Codex
**Estimated complexity:** medium-high

### Objective

Update the Flutter app to use direct presigned PUT for large uploads while preserving existing multipart upload flow.

**Prerequisites:** Prompt 13 merged.
**Out of scope:** removing the existing multipart upload path; backend changes.

### Prompt

```text
You are a senior Flutter engineer implementing direct large-file uploads to MinIO.

CONTEXT CONTRACT:
- Backend direct upload API is implemented and tested.
- Existing mobile uploadFile multipart flow must remain available.
- Mobile app must not receive S3 credentials.

INPUT:
- mobile/lib/data/api/api_client.dart
- Mobile upload repositories/services/screens.
- Backend upload API contract from Phase 8.

TASK:
1. Add direct upload client flow:
   - init upload
   - Dio PUT to upload_url with onSendProgress
   - complete upload
   - poll status if backend requires scanning state
2. Use direct upload for videos/audio/large files.
3. Keep existing uploadFile for small files.
4. Add progress states:
   - preparing
   - uploading
   - processing/scanning
   - available
   - failed
5. Handle app background/resume carefully:
   - expired URL refetch if safe
   - avoid duplicate complete calls
6. Add tests where mobile project supports them.

OUTPUT CONTRACT:
- Mobile app implementation only.
- Do not modify backend.
- Return Android/iOS manual QA steps.

ANTI-DRIFT RULES:
- Do not embed S3 credentials.
- Do not store presigned URLs long-term.
- Do not remove old multipart upload path.
- Do not blindly retry PUT after partial upload unless backend supports resumable upload.
- Do not make uploaded files visible before backend complete/scanning passes.

VALIDATION:
- Large video upload succeeds on Android and iOS.
- Progress is accurate.
- App resume after short background works.
- Expired upload URL shows recoverable error.
- Small upload path still works.
```

### Rollback

`git revert` the mobile direct-upload changes; the existing multipart upload path remains the fallback.

### Suggested manual Git commit

```text
git commit -m "feat(mobile): add direct large-file uploads"
```

---

## Prompt 16 — Observability and Operational Runbook

**Recommended model:** Claude Sonnet / ChatGPT / Codex
**Estimated complexity:** medium

### Objective

Add metrics, logs, and operational documentation for MinIO-backed storage.

**Prerequisites:** Foundational MinIO integration complete (Prompts 1–8). Optional client/large-upload prompts may also be merged.
**Out of scope:** changing storage behavior; adding high-cardinality labels (user id, school id, filename, object key).

### Prompt

```text
You are a senior platform engineer adding observability and operations support for MinIO-backed storage.

CONTEXT CONTRACT:
- Foundational MinIO integration is complete.
- Existing stack includes monitoring docs and likely Prometheus/Grafana infrastructure.
- Do not change storage behavior unless needed for metrics.

INPUT:
- Existing backend metrics patterns.
- infra/prometheus and infra/grafana directories.
- Deployment docs.
- MinIO integration docs.

TASK:
1. Add backend metrics where consistent with current patterns:
   - storage_upload_count
   - storage_upload_bytes
   - storage_presign_count
   - storage_operation_latency
   - storage_operation_errors
2. Label carefully:
   - env
   - backend=local|s3
   - operation
   - mime_type where safe
   - never label by user id, school id, filename, or object key
3. Add structured logs for storage failures without leaking presigned URLs.
4. Add/update Grafana dashboard panel if dashboards are code-managed.
5. Add runbook sections:
   - MinIO down
   - presigned URL 403
   - migration partial failure
   - rollback to local
   - bucket lifecycle verification
   - CORS troubleshooting

OUTPUT CONTRACT:
- Modify metrics/logging/docs/dashboards only.
- Return exact metrics names and labels.

ANTI-DRIFT RULES:
- Do not log credentials or presigned query strings.
- Do not add high-cardinality labels.
- Do not change endpoint behavior.
- Do not expose storage paths in public logs if they include sensitive filenames.

VALIDATION:
- Metrics scrape successfully.
- Dashboard loads.
- Runbook is usable during incident response.
```

### Rollback

`git revert` the metrics/dashboard/runbook changes; no storage runtime behavior was modified.

### Suggested manual Git commit

```text
git commit -m "chore(storage): add MinIO observability runbook"
```

---

## Prompt 17 — Final Verification and Architecture Conformance Review

**Recommended model:** Claude Sonnet / ChatGPT / SWE-agent
**Estimated complexity:** medium (review-only)

### Objective

Run a final end-to-end review to ensure implementation matches the architecture and has not drifted.

**Prerequisites:** every shipped prompt above is merged.
**Out of scope:** modifying any code or configuration; this is review-only.

### Prompt

```text
You are a senior software architect performing a final conformance review of the MinIO integration.

CONTEXT CONTRACT:
- Read MINIO_INTEGRATION_ARCHITECTURE.md and minio-integration-plan.md.
- Review the actual implementation diff/current repository.
- Do not write code unless explicitly asked after the review.

INPUT:
- Current repository after MinIO implementation.
- Test results if available.
- Deployment docs.

TASK:
1. Verify implementation against architecture decisions:
   - one bucket per environment
   - private bucket
   - presigned URLs
   - 302 backward compatibility
   - aioboto3 usage
   - no DB schema change for foundational phases
   - local backend retained
2. Verify all anti-drift rules.
3. Verify API backward compatibility.
4. Verify migration script safety.
5. Verify Docker and env docs.
6. Verify web/mobile optional integrations if implemented.
7. Produce a gap report:
   - compliant items
   - non-compliant items
   - risk severity
   - recommended fixes
8. Do not modify files.

OUTPUT CONTRACT:
- Markdown report only.
- Include final go/no-go recommendation.
- Include exact commands to run before production rollout.

ANTI-DRIFT RULES:
- Do not invent features not present.
- Do not assume tests passed if they were not run.
- Do not approve production rollout if validation evidence is missing.

VALIDATION:
- Report explicitly states whether production rollout is recommended.
```

### Rollback

N/A — review-only.

### Suggested manual Git commit (if report is saved)

```text
git commit -m "docs(storage): add MinIO conformance review"
```

---

## Suggested Overall Commit Sequence

Use these commits manually after reviewing each agent output:

1. `chore(infra): add MinIO dev storage services`
2. `chore(config): add S3 storage settings`
3. `feat(storage): add S3-compatible backend`
4. `refactor(storage): unify document storage backend`
5. `feat(api): add signed download response helpers`
6. `feat(api): serve downloads via presigned redirects`
7. `feat(storage): add local uploads to MinIO migration script`
8. `docs(storage): document MinIO rollout and rollback`
9. `chore(infra): remove obsolete local upload volume`
10. `feat(web): consume signed storage URLs`
11. `feat(mobile): consume signed storage URLs`
12. `docs(storage): design direct large-file uploads`
13. `feat(storage): support direct large uploads`
14. `feat(web): add direct large-file uploads`
15. `feat(mobile): add direct large-file uploads`
16. `chore(storage): add MinIO observability runbook`

---

## Minimal Safe Execution Path

If you only want foundational MinIO with no client rewrites, execute:

1. Prompt 0 — Baseline Recon
2. Prompt 1 — Infrastructure
3. Prompt 2 — Config
4. Prompt 3 — S3StorageBackend
5. Prompt 4 — Unify Document Storage
6. Prompt 5 — Download Helper
7. Prompt 6 — API Redirects
8. Prompt 7 — Migration Script
9. Prompt 8 — Switch/Rollout Docs
10. Prompt 17 — Final Review

This path maps to Phases 1–5 and preserves existing web/mobile behavior through `302` redirects.

---

## Optional Enhancement Path

After foundational rollout is stable:

1. Prompt 10 — Web signed URLs
2. Prompt 11 — Mobile signed URLs
3. Prompt 12 — Direct upload design
4. Prompt 13 — Direct upload backend
5. Prompt 14 — Web direct upload
6. Prompt 15 — Mobile direct upload
7. Prompt 16 — Observability
8. Prompt 17 — Final Review

---

## Final Reminder for Agents

MinIO integration must be boring, reversible, and production-oriented:

- Keep current logic intact.
- Preserve authorization.
- Avoid overengineering.
- Prefer small commits.
- Validate after each phase.
- Never expose credentials or public buckets.
