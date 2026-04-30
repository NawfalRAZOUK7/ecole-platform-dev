# MinIO Integration — Sequential Paste-Ready Prompts

> **Use this file to drive any AI agent (Claude, ChatGPT, Codex, SWE-agent, Kimi, etc.) through the full MinIO integration.**
>
> Each prompt below is **self-contained**. Copy everything between `===== BEGIN PROMPT N =====` and `===== END PROMPT N =====`, paste it into your AI chat, and run.
>
> Run prompts **in order**. Stop after each one to review the diff, run validation, and commit manually.

---

## How to Use

1. Pick the next prompt by number.
2. Copy everything between the BEGIN/END markers (inside the fenced block).
3. Paste into your AI agent of choice.
4. Wait for the agent to finish, review the changed files.
5. Run the validation commands the agent returns.
6. Apply the suggested **manual Git commit** shown after each prompt.
7. Proceed to the next prompt.

If anything goes wrong, use the **Rollback** line shown after each prompt.

---

## Prompt Index

| # | Title | Phase | Complexity | Required? |
| - | ----- | ----- | ---------- | --------- |
| 0 | Baseline Recon and Implementation Map | — | low | yes |
| 1 | Phase 1 Infrastructure: Add MinIO to Docker Compose | 1 | low | yes |
| 2 | Phase 2A Backend Config | 2 | low | yes |
| 3 | Phase 2B S3StorageBackend | 2 | medium | yes |
| 4 | Phase 2C Unify Document Storage | 2 | medium-high | yes |
| 5 | Phase 3A Download Helper | 3 | low | yes |
| 6 | Phase 3B Adapt Endpoints | 3 | medium | yes |
| 7 | Phase 4 Migration Script | 4 | medium | yes |
| 8 | Phase 5 Switch Rollout Docs | 5 | low | yes |
| 9 | Phase 5B Cleanup (after grace period) | 5 | low | optional |
| 10 | Phase 6 Web Signed URLs | 6 | medium | optional |
| 11 | Phase 7 Mobile Signed URLs | 7 | medium | optional |
| 12 | Phase 8A Large Upload Design | 8 | medium | optional |
| 13 | Phase 8B Large Upload Backend | 8 | high | optional |
| 14 | Phase 8C Web Direct Upload | 8 | medium | optional |
| 15 | Phase 8D Mobile Direct Upload | 8 | medium-high | optional |
| 16 | Observability + Runbook | — | medium | recommended |
| 17 | Final Conformance Review | — | medium | yes |

**Minimal foundational path:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 17.
**Full path with clients:** add 9, 10, 11, 16.
**Full path with large uploads:** add 12, 13, 14, 15.

---

## Prompt 0 — Baseline Recon and Implementation Map

- **Recommended model:** Claude Sonnet / ChatGPT / SWE-agent / Codex
- **Complexity:** low (read-only)
- **Prerequisites:** none.
- **Files in scope:** read-only across `backend/`, `web/`, `mobile/`, `infra/`.
- **Architecture sections:** §1 Findings, §2 Target architecture.

```text
===== BEGIN PROMPT 0 =====

ROLE: senior backend architect and AI coding agent.

REPO CONTEXT
- FastAPI backend, React/Vite web app, Flutter mobile app.
- Two existing storage abstractions: backend/app/core/storage.py and backend/app/services/file_storage.py.
- DB stores relative file paths; no schema change is needed for foundational MinIO rollout.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md
- minio-integration-plan.md

ARCHITECTURE INVARIANTS (always apply)
- One private bucket per environment (ecole-{env}-private).
- Tenant + domain isolation via key prefixes (schools/{school_id}/...).
- Backend authorizes; clients receive short-lived presigned URLs only.
- Default download contract: 302 redirect; ?as=metadata returns JSON.
- Use aioboto3 in async paths.
- Keep LocalStorageBackend usable for dev/tests.

OPERATING RULES
- Do not modify files outside the declared scope.
- Do not run destructive commands.
- Output must be a Markdown report only; do not write code.

SCOPE OF THIS PROMPT
- Architecture sections: §1 Findings, §2 Target architecture.
- Files in scope: read-only across backend/, web/, mobile/, infra/.
- Depends on: none.

TASK
1. Inspect files and routes related to storage, uploads, downloads, documents, submissions, assignments, content assets, Docker compose, and config.
2. Produce an implementation map with sections:
   - Implementation Map
   - High-Risk Areas
   - Recommended Phase Order
3. Include exact file paths discovered.
4. Explicitly answer: are there any direct filesystem accesses outside the two storage abstractions? List them with file paths if any.

OUTPUT
- Markdown report only. No code edits.

ANTI-DRIFT RULES
- Do not propose DB schema changes.
- Do not propose bucket-per-school.
- Do not propose public buckets.
- Do not propose direct upload before foundational backend storage is done.

===== END PROMPT 0 =====
```

After this prompt:

- **Validation:** report explicitly mentions all hidden direct filesystem accesses (or confirms none).
- **Rollback:** N/A — read-only step.
- **Manual commit:** none required.
- **Next:** Prompt 1.

---

## Prompt 1 — Phase 1 Infrastructure: Add MinIO to Docker Compose

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** low
- **Prerequisites:** Prompt 0 reviewed.
- **Files in scope:** `infra/docker-compose.dev.yml`, `infra/docker-compose.staging.yml`, `infra/docker-compose.prod.yml`, `.env.example`.
- **Architecture sections:** §2.6 Docker integration, §2.2 Bucket layout.

```text
===== BEGIN PROMPT 1 =====

ROLE: senior DevOps/backend engineer implementing Phase 1 of the MinIO integration.

REPO CONTEXT
- FastAPI backend, React/Vite web app, Flutter mobile app.
- Existing storage abstractions in backend/app/core/storage.py and backend/app/services/file_storage.py.
- DB stores relative file paths; no schema change.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.6 Docker integration, §2.2 Bucket layout)
- minio-integration-plan.md (Phase 1)

ARCHITECTURE INVARIANTS
- Private bucket per env (ecole-dev-private for dev).
- Default storage backend remains local until a later phase.

OPERATING RULES
- Do not modify backend/web/mobile source code.
- Do not commit real credentials.

SCOPE OF THIS PROMPT
- Files in scope: infra/docker-compose.dev.yml, infra/docker-compose.staging.yml, infra/docker-compose.prod.yml, .env.example.
- Out of scope: any backend/web/mobile code change.
- Depends on: none (review Prompt 0 first).

TASK
1. Add MinIO service to infra/docker-compose.dev.yml.
2. Add a one-shot minio-init service using minio/mc.
3. Create the dev bucket ecole-dev-private (private, no anonymous access).
4. Enable SSE-S3 if supported by mc in this compose context.
5. Add lifecycle rules where practical:
   - submissions expire after 730 days
   - temporary or preview assets expire as planned
   - permanent documents/content/videos/audio do not expire
6. Add minio_data volume.
7. Add MinIO/S3 variables to .env.example.
8. If staging/prod compose files exist, add equivalent env wiring or comments for managed MinIO/S3, without embedding secrets.

OUTPUT
- Modified compose/.env files only.
- Summary of changed files and exact validation commands.

ANTI-DRIFT RULES
- Do not set STORAGE_BACKEND=s3 by default yet.
- Do not remove upload_data volume yet.
- Do not expose MinIO publicly beyond localhost bindings in dev.
- Do not create public buckets.
- Do not create one bucket per school.

VALIDATION
- docker compose dev stack starts minio and minio-init.
- minio-init exits successfully.
- Bucket ecole-dev-private exists and is private.
- Backend container can reach http://minio:9000 (but backend behavior is still local).

===== END PROMPT 1 =====
```

After this prompt:

- **Rollback:** `git revert` the compose changes; `docker volume rm minio_data` only if empty.
- **Manual commit:** `git commit -m "chore(infra): add MinIO dev storage services"`
- **Next:** Prompt 2.

---

## Prompt 2 — Phase 2A Backend Config: Add S3/MinIO Settings

- **Recommended model:** Claude Sonnet / ChatGPT / Codex
- **Complexity:** low
- **Prerequisites:** Prompt 1 merged.
- **Files in scope:** `backend/app/core/config.py`, `.env.example`.
- **Architecture sections:** §2.4 Backend storage layer, Appendix B Env vars.

```text
===== BEGIN PROMPT 2 =====

ROLE: senior FastAPI backend engineer implementing Phase 2A of the MinIO integration.

REPO CONTEXT
- Existing storage abstractions in backend/app/core/storage.py and backend/app/services/file_storage.py.
- DB stores relative file paths; no schema change.
- Existing document_storage_* settings may already exist in config.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.4, Appendix B)
- minio-integration-plan.md (Phase 2 Step 2)

ARCHITECTURE INVARIANTS
- Default runtime behavior must remain local storage.
- One private bucket per environment.

OPERATING RULES
- Config-only prompt. Do not implement S3StorageBackend.
- Do not change defaults from local to s3.

SCOPE OF THIS PROMPT
- Files in scope: backend/app/core/config.py, .env.example, related test/config files.
- Out of scope: implementing S3StorageBackend (Prompt 3); changing default backend.
- Depends on: Prompt 1.

TASK
1. Add or consolidate settings:
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
3. If both generic S3 settings and document_storage_* settings exist, define a clear compatibility plan (mapping or backward-compatible aliases).
4. Update .env.example with safe placeholders.
5. Add/adjust tests if settings parsing is covered.

OUTPUT
- Changed settings/env files and tests only.
- Summary of changed settings and backward compatibility behavior.

ANTI-DRIFT RULES
- Do not change default from local to s3.
- Do not remove existing document storage settings if callers still use them.
- Do not hardcode dev bucket in Python code.
- Do not add DB migrations.

VALIDATION
- App settings load with no S3 env vars.
- App settings load with dev MinIO env vars.
- Existing tests still pass.

===== END PROMPT 2 =====
```

After this prompt:

- **Rollback:** `git revert` the config changes; `STORAGE_BACKEND` default remains `local`.
- **Manual commit:** `git commit -m "chore(config): add S3 storage settings"`
- **Next:** Prompt 3.

---

## Prompt 3 — Phase 2B Backend Storage Layer: Implement S3StorageBackend

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** medium
- **Prerequisites:** Prompt 2 merged.
- **Files in scope:** `backend/app/core/storage.py`, `backend/pyproject.toml`, `backend/tests/test_s3_storage_backend.py` (new).
- **Architecture sections:** §2.4 Backend storage layer.

```text
===== BEGIN PROMPT 3 =====

ROLE: senior FastAPI backend engineer implementing Phase 2B of the MinIO integration.

REPO CONTEXT
- Existing StorageBackend Protocol and LocalStorageBackend in backend/app/core/storage.py.
- Callers do `from app.core.storage import storage`.
- save() returns (relative_path, sha256, size).
- DB stores relative paths.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.4)
- minio-integration-plan.md (Phase 2 Steps 1–6)

ARCHITECTURE INVARIANTS
- Keep LocalStorageBackend intact.
- Add S3StorageBackend using aioboto3.
- One singleton aioboto3 session reused across requests.

OPERATING RULES
- Do not modify service-layer business logic.
- Do not modify routes.
- Do not modify backend/app/services/file_storage.py (that is Prompt 4).

SCOPE OF THIS PROMPT
- Files in scope: backend/app/core/storage.py, backend dependency manifest, new tests.
- Out of scope: services/file_storage.py (Prompt 4); API routes (Prompt 6).
- Depends on: Prompt 2.

TASK
1. Add aioboto3 dependency to pyproject.toml or equivalent.
2. Extend the StorageBackend Protocol with:
   - save (existing)
   - read or access-url behavior compatible with existing callers
   - delete (existing)
   - exists (existing)
   - presign_get(relative_path, expires_in, response_filename?) -> str
   - stat(relative_path) -> ObjectStat (size_bytes, etag, content_type, last_modified)
3. Implement S3StorageBackend using aioboto3:
   - configure with endpoint_url, region_name, access/secret keys
   - addressing_style="path" when S3_FORCE_PATH_STYLE
   - put_object with Cache-Control: private, max-age=300
   - ServerSideEncryption=AES256 if S3_SSE_ENABLED
4. Implement a storage factory returning LocalStorageBackend or S3StorageBackend based on STORAGE_BACKEND.
5. Preserve `from app.core.storage import storage` import pattern.
6. Ensure save returns (relative_path, sha256, size).
7. Object keys must be relative paths only (no bucket name).
8. Add unit tests with mocked or fake S3 (moto or equivalent).

OUTPUT
- Modified storage code and dependency manifest only.
- New tests for save/exists/delete/stat/presign behavior.
- Validation commands.

ANTI-DRIFT RULES
- Do not remove LocalStorageBackend.
- Do not alter service-layer business logic.
- Do not introduce a second unrelated storage abstraction.
- Do not use sync boto3 in async request paths.
- Do not stream S3 downloads to temp files for normal user downloads.
- Do not make the bucket public.

VALIDATION
- Existing local storage tests pass with STORAGE_BACKEND=local.
- New S3 backend tests pass.
- With STORAGE_BACKEND=s3 and dev MinIO running, a small file can be saved, stat'ed, presigned, downloaded, and deleted.

===== END PROMPT 3 =====
```

After this prompt:

- **Rollback:** `git revert` the storage changes; with `STORAGE_BACKEND=local`, the local backend remains active.
- **Manual commit:** `git commit -m "feat(storage): add S3-compatible backend"`
- **Next:** Prompt 4.

---

## Prompt 4 — Phase 2C Unify Document FileStorageBackend

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** medium-high
- **Prerequisites:** Prompt 3 merged.
- **Files in scope:** `backend/app/services/file_storage.py`, callers in `backend/app/services/student_documents.py` and `backend/app/services/lms/content_service.py`, related tests.
- **Architecture sections:** §1 Findings (two storage layers), §2.4 Backend storage layer.

```text
===== BEGIN PROMPT 4 =====

ROLE: senior backend engineer unifying document file storage with the new S3-compatible backend.

REPO CONTEXT
- Two storage layers exist:
  - backend/app/core/storage.py
  - backend/app/services/file_storage.py
- Phase 16 document storage currently has local and S3-like support.
- Document model has thumbnail generation, dedup by sha256, and virus scan hook.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§1 Findings, §2.4)
- minio-integration-plan.md (Phase 2 Step 5)

ARCHITECTURE INVARIANTS
- Keep public method signatures stable: store_upload, reuse_upload, store_upload_copy, exists, delete.
- Keep deduplication and thumbnail generation working.
- Document DB schema must not change.

OPERATING RULES
- Do not modify API routes (Prompt 6).
- Do not change Document or DocumentVersion DB schema.

SCOPE OF THIS PROMPT
- Files in scope: backend/app/services/file_storage.py, callers in student_documents.py and lms/content_service.py, related tests.
- Out of scope: API routes (Prompt 6); DB schema.
- Depends on: Prompt 3.

TASK
1. Rewire file_storage.py so document storage uses the same async S3 client as core storage.
2. Preserve public methods: store_upload, reuse_upload, store_upload_copy, exists, delete.
3. Review every caller of local_path / read_bytes / tempfile and document which are safe and which need follow-up.
4. Replace tempfile-download patterns for normal user downloads — those become presigned URLs in Prompt 6 (do not implement that here).
5. Keep thumbnail generation working for images.
6. Keep deduplication by sha256 working.
7. Keep virus_scan_hook working for backend-mediated uploads.
8. Add or update tests for document storage under both local and S3 modes.

OUTPUT
- Modified document/storage files and tests only.
- A list of any remaining local_path call sites with safety analysis.

ANTI-DRIFT RULES
- Do not change Document DB schema.
- Do not break document versioning.
- Do not remove deduplication.
- Do not remove thumbnail generation.
- Do not silently read large S3 objects fully into memory.

VALIDATION
- Existing document upload tests pass.
- Existing coloring page save flow passes.
- S3-backed document upload can store and reuse an object.
- Thumbnail generation still works for image uploads.

===== END PROMPT 4 =====
```

After this prompt:

- **Rollback:** `git revert` the changes; previous local + S3-like document storage logic resumes.
- **Manual commit:** `git commit -m "refactor(storage): unify document storage backend"`
- **Next:** Prompt 5.

---

## Prompt 5 — Phase 3A Download Metadata and Redirect Helper

- **Recommended model:** Claude Sonnet / ChatGPT / Codex
- **Complexity:** low
- **Prerequisites:** Prompts 3 and 4 merged.
- **Files in scope:** `backend/app/schemas/storage.py` (new), shared download helper module.
- **Architecture sections:** §2.5 API design.
- **FastAPI alias note:** `as` is a Python reserved keyword — use `as_: str | None = Query(None, alias="as")` so the URL stays `?as=metadata`.

```text
===== BEGIN PROMPT 5 =====

ROLE: senior FastAPI backend engineer implementing the shared API download layer for MinIO.

REPO CONTEXT
- Existing download endpoints currently use FileResponse.
- Service layer enforces ACL (school boundary, role).
- New behavior:
  - default: 302 redirect to presigned URL
  - optional: ?as=metadata returns JSON metadata
- as is a Python reserved keyword — use FastAPI alias.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.5)
- minio-integration-plan.md (Phase 3 Step 1)

ARCHITECTURE INVARIANTS
- Authorization happens in the service layer before generating the presigned URL.
- Backend issues short-lived presigned URLs only (TTL ~10 min).

OPERATING RULES
- This prompt creates reusable helper/schema only — do not yet update endpoints (Prompt 6).
- Do not skip authorization.

SCOPE OF THIS PROMPT
- Files in scope: backend/app/schemas/storage.py (new), shared download helper module, related tests.
- Out of scope: updating endpoints (Prompt 6).
- Depends on: Prompts 3, 4.

TASK
1. Add a reusable DownloadMetadata schema with fields:
   - download_url
   - expires_at
   - mime_type
   - size
   - filename
   - etag (optional)
2. Add a reusable helper for:
   - generating metadata response
   - generating RedirectResponse
   - applying filename / Content-Disposition through presign params
3. Support query parameter ?as=metadata. In FastAPI, declare the route parameter as `as_: str | None = Query(None, alias="as")` because `as` is a reserved Python keyword.
4. Keep the helper generic enough for submissions, content assets, exercise PDFs, and documents.
5. Add focused unit tests for the helper.

OUTPUT
- New schema and helper module, plus tests.
- Helper API and example usage.

ANTI-DRIFT RULES
- Do not skip endpoint-level authorization.
- Do not let the presign helper accept arbitrary unaudited paths from clients.
- Do not use public URLs.
- Do not put MinIO credentials in responses.
- Do not change existing route paths.

VALIDATION
- Helper tests pass.
- Metadata JSON shape is stable and documented in tests.
- Redirect response includes a presigned Location.

===== END PROMPT 5 =====
```

After this prompt:

- **Rollback:** `git revert` the helper additions; no endpoints depend on it yet.
- **Manual commit:** `git commit -m "feat(api): add signed download response helpers"`
- **Next:** Prompt 6.

---

## Prompt 6 — Phase 3B Adapt Download Endpoints to 302 + Metadata

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** medium
- **Prerequisites:** Prompt 5 merged.
- **Files in scope:** `backend/app/api/v1/submissions.py`, `backend/app/api/v1/content.py`, assignment exercise PDF route, document download routes, related tests.
- **Architecture sections:** §2.5 API design.
- **FastAPI alias note:** use `as_: str | None = Query(None, alias="as")`.

```text
===== BEGIN PROMPT 6 =====

ROLE: senior FastAPI backend engineer adapting existing file download endpoints to signed MinIO access.

REPO CONTEXT
- Phase 3A helper and DownloadMetadata schema already exist.
- Existing download endpoints currently use FileResponse.
- Existing clients (web, mobile) must continue working.
- Service-layer ACL must remain authoritative.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.5)
- minio-integration-plan.md (Phase 3 Steps 2–8)

ARCHITECTURE INVARIANTS
- Default response: 302 redirect to presigned URL.
- ?as=metadata returns JSON metadata.
- as is a Python reserved keyword — use `as_: str | None = Query(None, alias="as")` so the public URL stays ?as=metadata.

OPERATING RULES
- Preserve all existing route paths and HTTP methods.
- Preserve all ACL checks and school boundary checks.
- Keep local backend mode working in tests/dev.

SCOPE OF THIS PROMPT
- Files in scope:
  - backend/app/api/v1/submissions.py
  - backend/app/api/v1/content.py
  - assignment exercise PDF route (in v1/assignments.py or _helpers.py)
  - document download route(s)
  - related endpoint tests
- Out of scope: upload endpoints; route renaming; web/mobile client changes.
- Depends on: Prompt 5.

TASK
1. Update submission file download endpoint.
2. Update content asset download endpoint.
3. Update content stream compatibility endpoint.
4. Update assignment exercise PDF download endpoint.
5. Update document download endpoints if present.
6. Preserve all existing ACL checks and school boundary checks.
7. Preserve old route paths and HTTP methods.
8. Add/update tests:
   - default request returns 302
   - ?as=metadata returns JSON
   - unauthorized user cannot receive a presigned URL
   - missing file returns existing error shape
9. Ensure local backend mode still works.

OUTPUT
- Modified backend API/service/tests only.
- List of changed endpoints and validation commands.

ANTI-DRIFT RULES
- Do not return raw storage paths to clients.
- Do not bypass service methods that enforce permissions.
- Do not break existing upload endpoints.
- Do not introduce direct MinIO dependency in route code if the storage helper can abstract it.
- Do not convert uploads to direct PUT in this phase.

VALIDATION
- curl with auth to old download URL returns 302 with a Location pointing to MinIO.
- curl with auth and ?as=metadata returns JSON.
- Following the 302 downloads the file.
- Range request against the Location URL returns 206 for video/audio-capable objects.
- Existing web/mobile flows remain functional.

===== END PROMPT 6 =====
```

After this prompt:

- **Rollback:** `git revert` the route changes; FileResponse-based behavior resumes.
- **Manual commit:** `git commit -m "feat(api): serve downloads via presigned redirects"`
- **Next:** Prompt 7.

---

## Prompt 7 — Phase 4 Data Migration Script

- **Recommended model:** Claude Sonnet / Codex / ChatGPT
- **Complexity:** medium
- **Prerequisites:** Prompt 3 merged (S3 backend functional).
- **Files in scope:** `scripts/migrate_local_to_minio.py` (new), `artifacts/`.
- **Architecture sections:** §1 Findings (DB stores relative paths), §2.2 Bucket layout.

```text
===== BEGIN PROMPT 7 =====

ROLE: senior backend engineer writing a safe production migration script for local uploads to MinIO.

REPO CONTEXT
- Existing local files are under uploads/.
- DB stores relative paths; those become S3 object keys as-is.
- Re-running the script must be safe.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§1 Findings, §2.2)
- minio-integration-plan.md (Phase 4)

ARCHITECTURE INVARIANTS
- Idempotent migration (HEAD before PUT, skip on match).
- No DB mutation.
- Bucket is private; no anonymous reads.

OPERATING RULES
- Do not run the migration automatically.
- Do not delete local files.
- Use bounded concurrency.

SCOPE OF THIS PROMPT
- Files in scope: scripts/migrate_local_to_minio.py (new), artifacts/, related tests.
- Out of scope: DB changes, deleting local files.
- Depends on: Prompt 3.

TASK
1. Create scripts/migrate_local_to_minio.py.
2. CLI flags:
   - --source
   - --bucket
   - --dry-run
   - --verify-sample
   - --concurrency
   - --prefix (optional)
3. Walk the source directory recursively.
4. Object key = path relative to source.
5. HEAD destination before PUT; skip if size/etag matches.
6. Upload missing or mismatched objects.
7. Preserve MIME using mimetypes.guess_type with safe fallback.
8. Bounded concurrency with asyncio.Semaphore (default 8).
9. Verification sample (default N=50) downloads via presigned URL and compares SHA-256.
10. Emit a JSON summary under artifacts/minio_migration_{env}_{timestamp}.json.
11. Tests for dry-run and key mapping.

OUTPUT
- Migration script and tests only.
- Exact dry-run and real-run commands for dev/staging/prod.

ANTI-DRIFT RULES
- Do not mutate DB.
- Do not delete local files.
- Do not assume bucket is public.
- Do not read huge files fully into memory (stream).
- Do not fail entire migration on one file without reporting it.
- Do not hardcode dev bucket.

VALIDATION
- Dry run reports expected file count.
- Real run uploads files to MinIO.
- Re-running real run skips already-migrated files.
- Verification sample passes.

===== END PROMPT 7 =====
```

After this prompt:

- **Rollback:** Script is read-from-source; no DB or local file changes. To remove migrated objects: `mc rm --recursive --force ecole/<bucket>/<prefix>` (dev only).
- **Manual commit:** `git commit -m "feat(storage): add local uploads to MinIO migration script"`
- **Next:** Prompt 8.

---

## Prompt 8 — Phase 5 Switch Backend to MinIO Safely

- **Recommended model:** Claude Sonnet / ChatGPT / SWE-agent
- **Complexity:** low (docs)
- **Prerequisites:** Prompts 1–7 merged.
- **Files in scope:** docs only — `INSTALLATION.md`, runbook docs, infra compose comments.
- **Architecture sections:** §2.6 Docker integration, §3 What changes per layer.

```text
===== BEGIN PROMPT 8 =====

ROLE: senior technical lead preparing the safe rollout from local filesystem storage to MinIO.

REPO CONTEXT
- Phases 1–4 are implemented.
- Environment switch is controlled by STORAGE_BACKEND.
- Local storage code remains.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.6, §3)
- minio-integration-plan.md (Phase 5)

ARCHITECTURE INVARIANTS
- Default code default remains local; flip is per-env.
- Rollback to local is always possible during the grace period.
- LocalStorageBackend stays.

OPERATING RULES
- Documentation prompt only. Do not change application code.
- Do not flip production env automatically.

SCOPE OF THIS PROMPT
- Files in scope: INSTALLATION.md, deployment docs, runbook docs, compose comments.
- Out of scope: any code change; flipping production env; removing upload_data.
- Depends on: Prompts 1–7.

TASK
1. Document the rollout order: dev → staging → prod.
2. Smoke test checklist for uploads/downloads:
   - assignment exercise PDF
   - submission file
   - content asset
   - document
   - video/audio if sample files exist
3. Rollback procedure:
   - set STORAGE_BACKEND=local
   - restart backend/worker
   - keep uploads volume during the grace period
4. Compose cleanup instructions for later removal of upload_data — but do not remove it now.
5. Ensure .env.example clearly states STORAGE_BACKEND defaults to local until migration is complete.
6. Update deployment docs if they exist.

OUTPUT
- Documentation and inline compose comments only.
- A rollout checklist a human can follow step-by-step.

ANTI-DRIFT RULES
- Do not remove upload_data immediately.
- Do not delete uploads directory.
- Do not remove LocalStorageBackend.
- Do not make s3 the code default.
- Do not run migrations automatically.

VALIDATION
- A human can follow the rollout doc step-by-step.
- Rollback path is explicit and quick.
- No application behavior changes occur just by merging this documentation.

===== END PROMPT 8 =====
```

After this prompt:

- **Rollback:** `git revert` the doc changes; no application behavior changed.
- **Manual commit:** `git commit -m "docs(storage): document MinIO rollout and rollback"`
- **Next:** Prompt 9 (optional cleanup, after grace period) OR Prompt 17 (final review) for the minimal foundational path.

---

## Prompt 9 — Phase 5B Optional Cleanup After Stable Rollout

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** low
- **Prerequisites:** Prompt 8 rolled out and stable for at least 30 days.
- **Files in scope:** `infra/docker-compose.dev.yml`, `infra/docker-compose.staging.yml`, `infra/docker-compose.prod.yml`, deployment docs.
- **Architecture sections:** §2.6 Docker integration.

```text
===== BEGIN PROMPT 9 =====

ROLE: senior DevOps engineer performing post-rollout cleanup after MinIO has been stable for at least 30 days.

REPO CONTEXT
- MinIO has been the source of truth for at least 30 days.
- Local uploads have been archived and verified.
- LocalStorageBackend code must remain for tests and dev fallback.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.6)
- minio-integration-plan.md (Phase 5 Step 5)

ARCHITECTURE INVARIANTS
- LocalStorageBackend stays.
- No application code is removed.

OPERATING RULES
- Do not delete files from disk.
- Do not run destructive Docker volume commands.
- Do not remove upload_data if any service still depends on it.

SCOPE OF THIS PROMPT
- Files in scope: infra compose files, deployment docs.
- Out of scope: application code; deleting files.
- Depends on: Prompt 8 stable for ≥30 days.

TASK
1. Remove upload_data volume mounts from backend and worker services.
2. Remove top-level upload_data volume declarations if unused.
3. Update docs to say uploads are stored in MinIO, not local Docker volume.
4. Keep local backend code and local test configuration intact.

OUTPUT
- Modified compose files and docs only.
- Explicit confirmation that local backend code remains.

ANTI-DRIFT RULES
- Do not remove LocalStorageBackend.
- Do not delete files from disk.
- Do not remove upload_data if any service still depends on it.

VALIDATION
- Compose config validates.
- Backend starts without /app/uploads mount when STORAGE_BACKEND=s3.
- Tests using LocalStorageBackend still pass.

===== END PROMPT 9 =====
```

After this prompt:

- **Rollback:** `git revert` the compose changes; re-add `upload_data` mounts.
- **Manual commit:** `git commit -m "chore(infra): remove obsolete local upload volume"`
- **Next:** Prompt 10 (web client) or Prompt 17 (final review).

---

## Prompt 10 — Phase 6 Web Integration with Signed URLs

- **Recommended model:** Claude Sonnet / ChatGPT / Codex
- **Complexity:** medium
- **Prerequisites:** Prompt 6 merged (backend metadata variant exists).
- **Files in scope:** `web/src/services/api/client.ts`, `web/src/features/submissions/submissions.service.ts`, `web/src/features/cms/cms.service.ts`, `web/src/shared/hooks/useSignedUrl.ts` (new), media/PDF rendering components.
- **Architecture sections:** §2.7 Client consumption, §3 Web changes.

```text
===== BEGIN PROMPT 10 =====

ROLE: senior frontend engineer integrating signed MinIO URLs into the React/Vite web app.

REPO CONTEXT
- Backend already supports default 302 redirect and ?as=metadata JSON.
- Existing web upload behavior must remain unchanged.
- TanStack Query is the data layer.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.7, §3 Web changes)
- minio-integration-plan.md (Phase 6)

ARCHITECTURE INVARIANTS
- Browser must never receive S3 credentials.
- Always get URLs from the backend metadata endpoint.
- Cache signed URLs in client at 80% of TTL.

OPERATING RULES
- Do not change backend.
- Do not remove existing upload progress behavior.

SCOPE OF THIS PROMPT
- Files in scope: web API client, submissions/cms services, useSignedUrl hook, media/PDF rendering components.
- Out of scope: backend; upload flows.
- Depends on: Prompt 6.

TASK
1. Add a typed DownloadMetadata interface.
2. Add an API helper that calls ?as=metadata.
3. Add useSignedUrl(path) hook using TanStack Query (staleTime ~80% of TTL, refetch on 403).
4. Update submission downloads to use signed URLs (e.g. <a href={url} download>).
5. Update CMS/content asset previews to use signed URLs.
6. Render:
   - videos with <video src={url} controls>
   - audio with <audio src={url} controls>
   - PDFs with iframe or pdf.js using the URL
7. Refresh metadata on 403 from MinIO or after expiry.
8. Add/update frontend tests where applicable.

OUTPUT
- Modified web files only.
- Manual QA steps.

ANTI-DRIFT RULES
- Do not send MinIO credentials to the browser.
- Do not use raw storage paths as URLs.
- Do not remove existing upload progress behavior.
- Do not fetch large media as Blob before playback.
- Do not bypass backend authorization; always go through the metadata endpoint.

VALIDATION
- Web downloads still work.
- Video playback uses direct MinIO URL and supports seeking.
- Audio playback uses direct MinIO URL.
- PDF preview works.
- Expired URL refreshes cleanly.
- Browser DevTools shows media bytes coming from MinIO/CDN, not FastAPI.

===== END PROMPT 10 =====
```

After this prompt:

- **Rollback:** `git revert` the web changes; previous fetch/blob path resumes (backend still serves 302 + metadata).
- **Manual commit:** `git commit -m "feat(web): consume signed storage URLs"`
- **Next:** Prompt 11 (mobile) or Prompt 16 (observability).

---

## Prompt 11 — Phase 7 Mobile Integration with Signed URLs

- **Recommended model:** Claude Sonnet / ChatGPT / Kimi / Codex
- **Complexity:** medium
- **Prerequisites:** Prompt 6 merged.
- **Files in scope:** `mobile/lib/data/api/api_client.dart`, video/audio/PDF screens, signed URL cache helper (new).
- **Architecture sections:** §2.7 Client consumption, §3 Mobile changes.

```text
===== BEGIN PROMPT 11 =====

ROLE: senior Flutter engineer integrating signed MinIO URLs into the mobile app.

REPO CONTEXT
- Backend already supports ?as=metadata.
- Existing upload behavior must remain unchanged.
- Dio is the HTTP client.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.7, §3 Mobile changes)
- minio-integration-plan.md (Phase 7)

ARCHITECTURE INVARIANTS
- Mobile app must never receive S3 credentials.
- Cache signed URLs in memory at 80% of TTL.

OPERATING RULES
- Do not change backend.
- Do not change existing upload flows.

SCOPE OF THIS PROMPT
- Files in scope: mobile/lib/data/api/api_client.dart, repositories/services for content/submissions/documents, video/audio/PDF screens, new SignedUrlCache helper.
- Out of scope: backend; upload changes.
- Depends on: Prompt 6.

TASK
1. Add a DownloadMetadata model (Dart).
2. Add fetchSignedUrl(path) to ApiClient.
3. Add a small in-memory SignedUrlCache with expiry safety margin.
4. Wire video to signed URL using video_player or existing video package.
5. Wire audio to signed URL using just_audio or existing audio package.
6. Wire PDF viewing using flutter_pdfview or download-to-temp-file via signed URL.
7. Refetch URL on expiry/403/app resume.
8. Keep existing multipart upload flow unchanged.
9. Add tests where the mobile project supports them.

OUTPUT
- Modified mobile files only.
- Manual QA steps for iOS and Android.

ANTI-DRIFT RULES
- Do not embed S3/MinIO credentials in the mobile app.
- Do not use raw storage paths as URLs.
- Do not download entire videos before playback.
- Do not change backend endpoint contracts.
- Do not remove existing upload progress callbacks.

VALIDATION
- Video plays and seek works on Android and iOS.
- Audio plays reliably.
- PDF opens from signed URL or temp file.
- URL refresh works after expiry/app resume.
- Existing upload tests/flows still pass.

===== END PROMPT 11 =====
```

After this prompt:

- **Rollback:** `git revert` the mobile changes; previous download path resumes.
- **Manual commit:** `git commit -m "feat(mobile): consume signed storage URLs"`
- **Next:** Prompt 12 (large upload design) or Prompt 16 (observability).

---

## Prompt 12 — Phase 8A Large Upload API Design Only

- **Recommended model:** Claude Sonnet / ChatGPT
- **Complexity:** medium (design)
- **Prerequisites:** Prompts 1–8 merged.
- **Files in scope:** design report only (no code).
- **Architecture sections:** §2.5 API design (Phase 2 row), §4 Best practices.

```text
===== BEGIN PROMPT 12 =====

ROLE: senior backend architect designing direct-to-MinIO large file upload support.

REPO CONTEXT
- Foundational MinIO integration (Prompts 1–8) is complete.
- Direct uploads are an optional Phase 8.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.5, §4)
- minio-integration-plan.md (Phase 8 design)

ARCHITECTURE INVARIANTS
- Browser/mobile never receive S3 credentials.
- Unscanned uploads must not be visible to users.
- HLS/transcoding is out of scope.

OPERATING RULES
- Design-only prompt. Do not write code.

SCOPE OF THIS PROMPT
- Output: a design report.
- Files in scope: none (the agent should not edit files).
- Depends on: Prompts 1–8.

TASK
1. Design API endpoints:
   - POST /uploads/init
   - POST /uploads/complete
   - Optional GET /uploads/{id}/status
2. Define request/response schemas for each endpoint.
3. Define upload states:
   - uploading
   - scanning
   - available
   - failed
   - quarantined
4. Define authorization rules per upload kind:
   - assignment PDFs
   - submission files
   - content assets
   - videos
   - audio
5. Define validation rules (MIME, size, content-length, key prefix).
6. Define ARQ worker responsibilities for post-upload scan/thumbnail.
7. Identify whether DB schema additions are required and which tables.
8. Produce a migration-safe plan if DB changes are needed.

OUTPUT
- Markdown design report with endpoint tables, schema examples, state transitions, and risks.

ANTI-DRIFT RULES
- Do not implement HLS/transcoding.
- Do not bypass virus scanning.
- Do not make unscanned uploads visible.
- Do not expose S3 credentials to clients.
- Do not assume all upload kinds need the same DB changes.

VALIDATION
- Design is implementable in small PRs.
- Design clearly states whether DB migrations are needed.

===== END PROMPT 12 =====
```

After this prompt:

- **Rollback:** N/A — design report only.
- **Manual commit (if report saved):** `git commit -m "docs(storage): design direct large-file uploads"`
- **Next:** Prompt 13 (only after design is approved).

---

## Prompt 13 — Phase 8B Implement Direct Large Uploads

- **Recommended model:** Claude Sonnet / Codex / SWE-agent
- **Complexity:** high
- **Prerequisites:** Prompt 12 design accepted.
- **Files in scope:** `backend/app/core/storage.py` (presign_put), `backend/app/api/v1/uploads.py` (new), `backend/app/workers/post_upload.py` (new), related tests.
- **Architecture sections:** §4 Streaming videos, §4 Security.

```text
===== BEGIN PROMPT 13 =====

ROLE: senior FastAPI backend engineer implementing direct large-file uploads to MinIO.

REPO CONTEXT
- Foundational MinIO integration is complete.
- Phase 8A design is approved.
- ARQ worker infrastructure exists.

DOCS TO READ FIRST
- The Phase 8A design report (output of Prompt 12)
- MINIO_INTEGRATION_ARCHITECTURE.md (§4)
- minio-integration-plan.md (Phase 8 Steps 1–4)

ARCHITECTURE INVARIANTS
- Clients upload directly to MinIO using presigned PUT.
- Backend validates before init and after completion.
- Unscanned objects are not visible.

OPERATING RULES
- Do not change web/mobile clients (Prompts 14, 15).
- Do not skip post-upload validation.

SCOPE OF THIS PROMPT
- Files in scope: backend storage (presign_put), new uploads API routes, ARQ post-upload worker, related tests.
- Out of scope: web/mobile direct upload clients.
- Depends on: Prompt 12.

TASK
1. Add presign_put(relative_path, expires_in, content_type, max_size) to S3StorageBackend.
2. Add POST /uploads/init endpoint with ACL by upload kind, MIME and size validation, key generation, DB row in uploading state, return {upload_url, key, expires_at, max_size, upload_id}.
3. Add POST /uploads/complete endpoint that HEADs the object, validates size/etag, transitions DB to scanning, enqueues ARQ post-upload job.
4. Add ARQ post-upload job:
   - stream object from MinIO
   - run virus_scan_hook
   - on clean: state → available, generate thumbnail if applicable
   - on infected: state → quarantined, delete object, audit log
5. Add lifecycle cleanup for incomplete uploads (objects in uploading state expire after 24h).
6. Tests: init authorization, presigned PUT generation, complete validation, scan success, scan/quarantine failure, expired/incomplete upload cleanup.

OUTPUT
- Backend implementation and tests only.
- Endpoint docs and validation commands.

ANTI-DRIFT RULES
- Do not skip post-upload HEAD validation.
- Do not make scanning optional for user-uploaded files.
- Do not expose uploads before available state.
- Do not use public buckets.
- Do not hardcode size limits.

VALIDATION
- A large test file can be uploaded via presigned PUT.
- Complete endpoint validates MinIO object metadata.
- Unscanned object is not visible to users.
- Clean object becomes available.
- Infected (EICAR) test object is quarantined/deleted.

===== END PROMPT 13 =====
```

After this prompt:

- **Rollback:** `git revert` the upload routes and worker; lifecycle rule cleans orphans within 24h.
- **Manual commit:** `git commit -m "feat(storage): support direct large uploads"`
- **Next:** Prompts 14 and 15 in parallel.

---

## Prompt 14 — Phase 8C Web Direct Upload Client

- **Recommended model:** Claude Sonnet / ChatGPT / Codex
- **Complexity:** medium
- **Prerequisites:** Prompt 13 merged.
- **Files in scope:** `web/src/services/uploads/directUpload.ts` (new), upload UI components.
- **Architecture sections:** §2.7 Client consumption, §4 Streaming videos.

```text
===== BEGIN PROMPT 14 =====

ROLE: senior React frontend engineer implementing direct large-file uploads to MinIO.

REPO CONTEXT
- Backend direct upload API is implemented and tested (Prompt 13).
- Existing small-file multipart upload remains as fallback.
- Browser must not receive S3 credentials, only presigned PUT URLs.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.7, §4)
- minio-integration-plan.md (Phase 8 Step 5)

ARCHITECTURE INVARIANTS
- Direct upload only for files above a configured threshold or for video/audio kinds.
- Multipart fallback for small files.

OPERATING RULES
- Do not change backend.
- Do not log presigned URLs in production logs.

SCOPE OF THIS PROMPT
- Files in scope: new directUpload service, upload UI components.
- Out of scope: backend; mobile.
- Depends on: Prompt 13.

TASK
1. Add directUpload service:
   - call /uploads/init
   - XMLHttpRequest PUT to upload_url with progress events
   - call /uploads/complete
   - poll status if needed
2. Use direct upload only for files above threshold or video/audio kinds.
3. Preserve existing multipart upload for small files.
4. UI states:
   - preparing
   - uploading
   - processing/scanning
   - available
   - failed
5. Retry behavior for init/complete; do not blind-retry PUT unless backend supports resumable uploads.
6. Add frontend tests where available.

OUTPUT
- Web implementation only.
- Manual QA steps.

ANTI-DRIFT RULES
- Do not store upload_url permanently.
- Do not log presigned URLs.
- Do not send Authorization header to MinIO PUT URL unless required by signature.
- Do not remove old multipart path.

VALIDATION
- Large video upload shows progress.
- Complete call marks asset as processing/available.
- Small uploads still use the old path.
- Failed upload surfaces a useful UI error.

===== END PROMPT 14 =====
```

After this prompt:

- **Rollback:** `git revert` the web direct-upload changes; multipart fallback remains.
- **Manual commit:** `git commit -m "feat(web): add direct large-file uploads"`
- **Next:** Prompt 15 (mobile) or Prompt 16 (observability).

---

## Prompt 15 — Phase 8D Mobile Direct Upload Client

- **Recommended model:** Claude Sonnet / Kimi / ChatGPT / Codex
- **Complexity:** medium-high
- **Prerequisites:** Prompt 13 merged.
- **Files in scope:** `mobile/lib/data/api/upload_client.dart` (new), upload UI screens.
- **Architecture sections:** §2.7 Client consumption, §4 Streaming videos.

```text
===== BEGIN PROMPT 15 =====

ROLE: senior Flutter engineer implementing direct large-file uploads to MinIO.

REPO CONTEXT
- Backend direct upload API is implemented and tested (Prompt 13).
- Existing mobile uploadFile multipart flow must remain available.
- Mobile app must not receive S3 credentials.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§2.7, §4)
- minio-integration-plan.md (Phase 8 Step 6)

ARCHITECTURE INVARIANTS
- Direct upload for video/audio/large files; multipart fallback for small.
- App must handle background/resume gracefully.

OPERATING RULES
- Do not change backend.
- Do not log presigned URLs.

SCOPE OF THIS PROMPT
- Files in scope: new upload_client.dart, upload UI screens, related tests.
- Out of scope: backend; web.
- Depends on: Prompt 13.

TASK
1. Direct upload client flow:
   - init upload
   - Dio PUT to upload_url with onSendProgress
   - complete upload
   - poll status if backend requires scanning state
2. Use direct upload for videos/audio/large files; keep existing uploadFile for small files.
3. UI states:
   - preparing
   - uploading
   - processing/scanning
   - available
   - failed
4. App background/resume:
   - expired URL refetch if safe
   - avoid duplicate complete calls
5. Add tests where mobile supports them.

OUTPUT
- Mobile implementation only.
- Manual QA steps for Android and iOS.

ANTI-DRIFT RULES
- Do not embed S3 credentials.
- Do not store presigned URLs long-term.
- Do not remove old multipart upload path.
- Do not blindly retry PUT after partial upload unless backend supports resumable upload.
- Do not make uploaded files visible before backend complete/scanning passes.

VALIDATION
- Large video upload succeeds on Android and iOS.
- Progress is accurate.
- App resume after short background works.
- Expired upload URL surfaces a recoverable error.
- Small upload path still works.

===== END PROMPT 15 =====
```

After this prompt:

- **Rollback:** `git revert` the mobile direct-upload changes; multipart fallback remains.
- **Manual commit:** `git commit -m "feat(mobile): add direct large-file uploads"`
- **Next:** Prompt 16 (observability).

---

## Prompt 16 — Observability and Operational Runbook

- **Recommended model:** Claude Sonnet / ChatGPT / Codex
- **Complexity:** medium
- **Prerequisites:** Prompts 1–8 merged (and any optional client/upload prompts you shipped).
- **Files in scope:** `infra/prometheus/`, `infra/grafana/`, runbook docs, backend metrics modules.
- **Architecture sections:** §4 Best practices, §3 Per-layer changes.

```text
===== BEGIN PROMPT 16 =====

ROLE: senior platform engineer adding observability and operations support for MinIO-backed storage.

REPO CONTEXT
- Foundational MinIO integration is complete.
- Existing stack includes monitoring docs and Prometheus/Grafana infrastructure.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md (§4)
- minio-integration-plan.md (observability step)

ARCHITECTURE INVARIANTS
- Never use high-cardinality labels (user id, school id, filename, object key).
- Never log presigned URLs or credentials.

OPERATING RULES
- Do not change storage behavior unless required for metrics.
- Do not change endpoint behavior.

SCOPE OF THIS PROMPT
- Files in scope: backend metrics modules, infra/prometheus, infra/grafana, runbook docs.
- Out of scope: storage runtime behavior; endpoint contracts.
- Depends on: Prompts 1–8 (optionally 9, 10, 11, 13).

TASK
1. Add backend metrics consistent with existing patterns:
   - storage_upload_count
   - storage_upload_bytes
   - storage_presign_count
   - storage_operation_latency
   - storage_operation_errors
2. Labels: env, backend (local|s3), operation, mime_type (where safe). Never user id/school id/filename/key.
3. Structured logs for storage failures without leaking presigned URLs.
4. Add or update Grafana dashboard panel if dashboards are code-managed.
5. Runbook sections:
   - MinIO down
   - presigned URL 403
   - migration partial failure
   - rollback to local
   - bucket lifecycle verification
   - CORS troubleshooting

OUTPUT
- Modified metrics/logging/docs/dashboards only.
- Exact metrics names and labels.

ANTI-DRIFT RULES
- Do not log credentials or presigned query strings.
- Do not add high-cardinality labels.
- Do not change endpoint behavior.
- Do not expose sensitive filenames in public logs.

VALIDATION
- Metrics scrape successfully.
- Dashboard loads.
- Runbook is usable during an incident.

===== END PROMPT 16 =====
```

After this prompt:

- **Rollback:** `git revert` the metrics/dashboards/runbook changes; storage runtime is unaffected.
- **Manual commit:** `git commit -m "chore(storage): add MinIO observability runbook"`
- **Next:** Prompt 17.

---

## Prompt 17 — Final Verification and Architecture Conformance Review

- **Recommended model:** Claude Sonnet / ChatGPT / SWE-agent
- **Complexity:** medium (review-only)
- **Prerequisites:** every shipped prompt above is merged.
- **Files in scope:** read-only across the repo.
- **Architecture sections:** all sections of `MINIO_INTEGRATION_ARCHITECTURE.md`.

```text
===== BEGIN PROMPT 17 =====

ROLE: senior software architect performing a final conformance review of the MinIO integration.

REPO CONTEXT
- Implementation is complete (or partially complete) across the chosen prompts.

DOCS TO READ FIRST
- MINIO_INTEGRATION_ARCHITECTURE.md
- minio-integration-plan.md

ARCHITECTURE INVARIANTS
- One bucket per environment.
- Private bucket; backend authorizes; presigned URLs only.
- 302 backward compatibility default.
- aioboto3 in async paths.
- No DB schema change for foundational phases.
- LocalStorageBackend retained.

OPERATING RULES
- Review-only; do not modify any file.
- Do not approve production rollout if validation evidence is missing.

SCOPE OF THIS PROMPT
- Files in scope: read-only across the repo.
- Out of scope: any modification.
- Depends on: every shipped prompt above.

TASK
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

OUTPUT
- Markdown report only.
- Final go/no-go recommendation for production rollout.
- Exact commands to run before rollout.

ANTI-DRIFT RULES
- Do not invent features not present.
- Do not assume tests passed if they were not run.
- Do not approve production rollout if validation evidence is missing.

VALIDATION
- Report explicitly states whether production rollout is recommended.

===== END PROMPT 17 =====
```

After this prompt:

- **Rollback:** N/A — review-only.
- **Manual commit (if report saved):** `git commit -m "docs(storage): add MinIO conformance review"`
- **Next:** ship to production using the runbook from Prompt 8.

---

## Quick Reference — Commit Sequence

After running each prompt and reviewing the diff, run the matching commit:

```bash
# Phase 1
git commit -m "chore(infra): add MinIO dev storage services"

# Phase 2
git commit -m "chore(config): add S3 storage settings"
git commit -m "feat(storage): add S3-compatible backend"
git commit -m "refactor(storage): unify document storage backend"

# Phase 3
git commit -m "feat(api): add signed download response helpers"
git commit -m "feat(api): serve downloads via presigned redirects"

# Phase 4
git commit -m "feat(storage): add local uploads to MinIO migration script"

# Phase 5
git commit -m "docs(storage): document MinIO rollout and rollback"
git commit -m "chore(infra): remove obsolete local upload volume"

# Phase 6 / 7 (optional clients)
git commit -m "feat(web): consume signed storage URLs"
git commit -m "feat(mobile): consume signed storage URLs"

# Phase 8 (optional large uploads)
git commit -m "docs(storage): design direct large-file uploads"   # if report saved
git commit -m "feat(storage): support direct large uploads"
git commit -m "feat(web): add direct large-file uploads"
git commit -m "feat(mobile): add direct large-file uploads"

# Observability + final review
git commit -m "chore(storage): add MinIO observability runbook"
git commit -m "docs(storage): add MinIO conformance review"   # if report saved
```

---

## Final Reminder

- Run prompts **in order**.
- Review the diff after each prompt.
- Run the validation suggested by the agent.
- Commit manually using the line shown above.
- Use the **Rollback** line if anything goes wrong.
- Do not let an agent skip validation or silently change architecture decisions.
