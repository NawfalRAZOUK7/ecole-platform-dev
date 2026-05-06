# MinIO Integration Plan

> Step-by-step execution plan for integrating MinIO (S3-compatible object storage) into the École Platform.
> Designed to be followed sequentially by a coding AI agent or human implementer.

---

## 2. Global Overview

### Architecture in one paragraph

Replace the current local filesystem (`uploads/` directory + `LocalStorageBackend`) with an S3-compatible object store (**MinIO** in dev/staging, MinIO or AWS S3 in prod). The existing `StorageBackend` Protocol stays the source of truth — a new `S3StorageBackend` slots in behind it. Downloads stop streaming bytes through FastAPI and instead return **short-lived presigned URLs**; clients fetch bytes directly from MinIO. Uploads continue through the backend in Phase 1; direct presigned PUT is added in Phase 8 for large files (videos).

### Key decisions

- **One bucket per environment**: `ecole-dev-private`, `ecole-staging-private`, `ecole-prod-private`. Tenant + domain isolation via key prefixes (`schools/{school_id}/{exercises|submissions|content|documents|videos|audio}/...`).
- **Private bucket + presigned URLs**: bucket has no anonymous read; backend authorizes (JWT + school boundary + role) and issues a presigned GET (TTL 10 min default).
- **302 redirect for backward compatibility**: existing download endpoints keep their URL contract — they redirect to the presigned URL. New JSON variant via `?as=metadata`.
- **`aioboto3`**: async S3 client; portable across MinIO / AWS S3 / Cloudflare R2 / Wasabi.
- **No DB schema change**: existing `storage_path` / `file_path` columns become S3 object keys as-is.
- **Server-side encryption**: SSE-S3 enabled at bucket level. KMS not required.
- **Phase 1 ships without any client change**: web and mobile keep working through the 302 redirect.

---

## 3. Phases

### Phase 1 — Infrastructure (MinIO setup)

#### 🎯 Objective

Stand up MinIO in `infra/docker-compose.dev.yml` with a healthy bucket, lifecycle rules, and SSE-S3 — without touching backend code.

#### ✅ Checklist

- [ ] Add `minio` service to `infra/docker-compose.dev.yml`
- [ ] Add `minio-init` one-shot service using `minio/mc`
- [ ] Create bucket `ecole-dev-private`
- [ ] Apply lifecycle rules per prefix
- [ ] Enable SSE-S3 at bucket level
- [ ] Add MinIO env vars to `.env.example` and `.env`
- [ ] Add `minio_data` named volume
- [ ] Add MinIO to `infra/docker-compose.staging.yml` and `infra/docker-compose.prod.yml` (or document managed alternative)

#### 🔽 Detailed Steps

**Step 1.1 — Add MinIO service**

- File: `infra/docker-compose.dev.yml`
- Add service `minio` using image `minio/minio:latest`
- Expose ports `9000` (S3 API) and `9001` (web console), bound to `127.0.0.1`
- Mount volume `minio_data:/data`
- Set env vars: `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` (read from `.env`)
- Healthcheck: `GET /minio/health/live`
- Network: `ecole-network`
- Expected: `docker compose up minio` brings up a healthy MinIO; console reachable at `http://localhost:9001`
- Dependencies: none

**Step 1.2 — Add `minio-init` one-shot**

- File: `infra/docker-compose.dev.yml`
- Service uses `minio/mc:latest`
- `depends_on: { minio: { condition: service_healthy } }`
- Entrypoint script:
  - Wait for MinIO ready
  - `mc alias set` against the local MinIO
  - `mc mb --ignore-existing ecole/ecole-dev-private`
  - `mc anonymous set none ecole/ecole-dev-private`
  - `mc encrypt set sse-s3 ecole/ecole-dev-private`
  - `mc ilm rule add` for each lifecycle policy (see Step 1.4)
  - Exit cleanly on success (`restart: "no"`)
- Expected: bucket created, lifecycle and SSE applied; container exits 0
- Dependencies: Step 1.1

**Step 1.3 — Add MinIO volume**

- File: `infra/docker-compose.dev.yml`
- Add `minio_data:` under top-level `volumes:`
- Expected: persistent storage across restarts
- Dependencies: Step 1.1

**Step 1.4 — Define lifecycle rules**

- Apply via `minio-init` script:
  - `schools/*/submissions/*` → expire after 730 days (2 academic years)
  - `documents/previews/*` → expire after 30 days if source deleted
  - `schools/*/exercises/*`, `documents/*`, `videos/*`, `audio/*` → no expiration
- Expected: `mc ilm rule list ecole/ecole-dev-private` returns the rules
- Dependencies: Step 1.2

**Step 1.5 — Update `.env.example` and `.env`**

- File: `.env.example`, `.env`
- Add the variables defined in [Section 5 / Environment variables](#environment-variables)
- Default `STORAGE_BACKEND=local` so the switch is opt-in until Phase 5
- Expected: secrets baseline still passes; no production credentials committed
- Dependencies: none

**Step 1.6 — Replicate to staging/prod compose**

- Files: `infra/docker-compose.staging.yml`, `infra/docker-compose.prod.yml`
- Either run a hardened MinIO with TLS, or document AWS S3 / managed alternative and skip the service
- Expected: env-specific bucket names (`ecole-staging-private`, `ecole-prod-private`) reachable from backend
- Dependencies: Step 1.1, Step 1.2

#### 🧪 Validation

- `docker compose -f infra/docker-compose.dev.yml up -d minio minio-init` brings both services up; `minio-init` exits 0
- MinIO console at `http://localhost:9001` shows bucket `ecole-dev-private` with SSE and lifecycle rules
- `mc ls ecole/ecole-dev-private` works from a container in the network
- Backend container can reach `http://minio:9000` (test with `curl`)

#### ⚠️ Risks

- **Default credentials in `.env`** committed by accident → use `secrets.baseline`
- **Healthcheck flakiness** if `minio-init` runs before the bucket is ready → use a retry loop with backoff
- **Port conflicts** if `9000` or `9001` is already used locally → bind to `127.0.0.1` and document overrides
- **Disk pressure** on dev laptops if `minio_data` grows → document manual prune or set ILM aggressively in dev

---

### Phase 2 — Backend Storage Layer

#### 🎯 Objective

Implement `S3StorageBackend` behind the existing `StorageBackend` Protocol, add presign helpers, unify the Phase 16 file storage service, and select the backend via config — **without** changing any caller.

#### ✅ Checklist

- [ ] Add `aioboto3` dependency
- [ ] Extend `StorageBackend` Protocol with `presign_get` and `stat`
- [ ] Implement `S3StorageBackend` in `backend/app/core/storage.py`
- [ ] Replace singleton `storage` with config-driven factory
- [ ] Rewire `S3FileStorageBackend` in `backend/app/services/file_storage.py` to share the async client; drop `tempfile` path
- [ ] Add settings to `backend/app/core/config.py`
- [ ] Unit tests with `moto` (or a fake S3 fixture)
- [ ] Integration test against the dev MinIO container

#### 🔽 Detailed Steps

**Step 2.1 — Add `aioboto3`**

- File: `backend/pyproject.toml` (and lockfile)
- Add `aioboto3` (latest compatible with `boto3` already in tree)
- Expected: `pip install` / `uv sync` succeeds; no version conflict with existing `boto3`
- Dependencies: none

**Step 2.2 — Extend the Protocol**

- File: `backend/app/core/storage.py`
- Add to `StorageBackend` Protocol:
  - `async def presign_get(self, relative_path: str, *, expires_in: int, response_filename: str | None = None) -> str`
  - `async def stat(self, relative_path: str) -> ObjectStat` where `ObjectStat` is a dataclass with `size_bytes`, `etag`, `content_type`, `last_modified`
- Update `LocalStorageBackend` to satisfy the new methods:
  - `presign_get`: return a signed internal URL pointing to a backend route that streams the file (used only when `STORAGE_BACKEND=local`)
  - `stat`: read file metadata from filesystem
- Expected: the Protocol is still implemented by both backends; type checks pass
- Dependencies: Step 2.1

**Step 2.3 — Implement `S3StorageBackend`**

- File: `backend/app/core/storage.py`
- Class implements all `StorageBackend` methods using `aioboto3`:
  - `save`: streams the upload to `put_object` (or multipart for large bodies); compute SHA-256 in the same pass; respect existing `validate_mime_type` / `validate_file_size`; call `virus_scan_hook` on the in-memory chunks
  - `read`: returns a presigned GET URL (replaces "download to tempfile then return Path"); do **not** download bytes
  - `delete`: `delete_object`
  - `exists`: `head_object` with 404 handling
  - `presign_get`: `generate_presigned_url("get_object", ...)` with optional `ResponseContentDisposition`
  - `stat`: `head_object`
- Use a singleton async session; configure with `endpoint_url`, `region_name`, `aws_access_key_id`, `aws_secret_access_key`, and `s3={"addressing_style": "path"}` when `S3_FORCE_PATH_STYLE=true`
- Set `Cache-Control: private, max-age=300` on `put_object`
- Set `ServerSideEncryption=AES256` if `S3_SSE_ENABLED=true`
- Expected: writes succeed against MinIO; read returns a working presigned URL
- Dependencies: Step 2.2

**Step 2.4 — Config-driven factory**

- File: `backend/app/core/storage.py`, `backend/app/core/config.py`
- Add `Settings.storage_backend: Literal["local", "s3"] = "local"`
- Add `Settings.s3_*` fields (see [env vars](#environment-variables))
- Replace `storage = LocalStorageBackend()` with `storage = build_storage_backend(settings)` returning the right implementation
- Expected: callers `from app.core.storage import storage` keep working; behavior depends on env
- Dependencies: Step 2.3

**Step 2.5 — Unify Phase 16 file storage**

- File: `backend/app/services/file_storage.py`
- Refactor `S3FileStorageBackend` to delegate to the new async client (or drop it and have `FileStorageService` accept any `StorageBackend`)
- **Drop the tempfile-download path** in `local_path` — for S3, `local_path` becomes either:
  - Forbidden for callers (raise) and replaced everywhere by `presign_get`, OR
  - Returns a streaming context manager that yields chunks (only used for in-process processing like thumbnail generation)
- Keep `store_upload`, `reuse_upload`, `store_upload_copy`, `_maybe_generate_thumbnail` signatures unchanged
- Expected: callers (`student_documents.py`, `content_service.py` coloring page) keep working
- Dependencies: Step 2.4

**Step 2.6 — Unit tests**

- File: `backend/tests/test_s3_storage_backend.py` (new)
- Use `moto` for a fake S3 server (or a pytest fixture spinning the MinIO container)
- Cover: `save` round-trip, `exists`, `delete`, `presign_get` returns a 200-able URL, `stat` matches what was written, MIME / size validation rejection, virus scan hook invocation
- Expected: green tests; coverage on the new backend ≥ 90%
- Dependencies: Step 2.3

**Step 2.7 — Integration test against dev MinIO**

- File: `backend/tests/integration/test_minio_round_trip.py` (new, gated by env flag)
- Skipped unless `MINIO_INTEGRATION=1`
- Boots no services; expects `infra/docker-compose.dev.yml minio` already running
- Round-trips a small PDF and a small MP4 through `storage.save` → `storage.presign_get` → HTTP GET
- Expected: 200 OK, body bytes match, Range request returns 206
- Dependencies: Phase 1 complete

#### 🧪 Validation

- `pytest backend/tests/test_s3_storage_backend.py` green
- `MINIO_INTEGRATION=1 pytest backend/tests/integration/test_minio_round_trip.py` green
- `from app.core.storage import storage; await storage.save(...)` works in a `python -m` shell against dev MinIO
- No regressions in existing test suite (`pytest backend/tests`)

#### ⚠️ Risks

- **Sync boto3 inside async**: existing `S3FileStorageBackend` uses sync `boto3.client`. Mixing sync calls in async code blocks the event loop — make sure all S3 calls go through `aioboto3` after Step 2.5.
- **`local_path` semantics drift**: any caller still relying on a real local file (e.g. PIL thumbnail generation) must switch to streaming bytes from S3 in memory.
- **Path-style addressing**: MinIO requires `S3_FORCE_PATH_STYLE=true`; AWS S3 prefers virtual-hosted style → keep this configurable per env.
- **Virus scan hook on streaming**: `virus_scan_hook` currently expects full bytes; verify it still works with the chunked write path or buffer up to a max size.
- **Connection pool exhaustion**: ensure the `aioboto3` session is reused (singleton) — do not instantiate a client per request.

---

### Phase 3 — API Adaptation

#### 🎯 Objective

Convert all download endpoints to return **302 → presigned URL** by default and JSON metadata when `?as=metadata` is passed, without breaking existing clients.

#### ✅ Checklist

- [ ] Define `DownloadMetadata` Pydantic schema
- [ ] Update submission file download endpoint
- [ ] Update content asset download endpoint
- [ ] Update content stream compatibility endpoint
- [ ] Update assignment exercise PDF download endpoint
- [ ] Update student documents download endpoint(s)
- [ ] Add response examples in OpenAPI
- [ ] Update API tests

#### 🔽 Detailed Steps

**Step 3.1 — `DownloadMetadata` schema**

- File: `backend/app/schemas/storage.py` (new) or co-located in existing schemas module
- Fields: `download_url: HttpUrl`, `expires_at: datetime`, `mime_type: str`, `size: int`, `filename: str`, `etag: str | None`
- Expected: importable from API routes
- Dependencies: Phase 2

**Step 3.2 — Submission file download**

- File: `backend/app/api/v1/submissions.py`
- Endpoint: `GET /submissions/{submission_id}/files/{file_id}`
- Behavior:
  - Run existing ACL check (school boundary + role)
  - If query `as=metadata`: return `DownloadMetadata` JSON (200)
  - Else: issue presigned URL and return `RedirectResponse(url, status_code=302)`
  - In both cases set `Content-Disposition` via `ResponseContentDisposition` on the presigned URL
- Expected: existing clients receive bytes (via redirect); new clients can call with `?as=metadata`
- Dependencies: Step 3.1

**Step 3.3 — Content asset download**

- File: `backend/app/api/v1/content.py`
- Endpoint: `GET /content-items/{content_item_id}/assets/{asset_id}`
- Same pattern as Step 3.2
- Expected: same behavior contract
- Dependencies: Step 3.1

**Step 3.4 — Content stream compatibility endpoint**

- File: `backend/app/api/v1/content.py`
- Endpoint: `GET /content-items/{content_item_id}/stream`
- Same pattern; presigned URL TTL stays at default (10 min)
- Expected: video/audio playback works via `<video>` / `<audio>` after redirect
- Dependencies: Step 3.1

**Step 3.5 — Assignment exercise PDF download**

- File: `backend/app/services/lms/_helpers.py`, `backend/app/api/v1/assignments.py`
- Endpoint: `GET /assignments/{assignment_id}/exercise-pdf`
- Same pattern; force `Content-Disposition: attachment; filename=exercise_{id}.pdf`
- Expected: clients keep downloading PDFs unchanged
- Dependencies: Step 3.1

**Step 3.6 — Student documents download**

- File: `backend/app/api/v1/documents.py` (or wherever the route currently lives)
- Same pattern across all download routes (current version, specific version, thumbnail)
- Expected: web Documents UI keeps working
- Dependencies: Step 3.1

**Step 3.7 — OpenAPI examples**

- File: route modules touched above
- Add response examples for both 302 and 200 (`as=metadata`)
- Expected: Swagger UI shows both flows clearly
- Dependencies: Steps 3.2 – 3.6

**Step 3.8 — Update API tests**

- File: `backend/tests/test_*_endpoints.py`
- Update tests that assert `FileResponse` to:
  - Either assert `302` + presigned URL pattern
  - Or call with `?as=metadata` and assert JSON shape
- Expected: green test suite
- Dependencies: Steps 3.2 – 3.6

#### 🧪 Validation

- `curl -I -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/submissions/{id}/files/{fid}` returns `302` with `Location` pointing to MinIO
- `curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/api/v1/submissions/{id}/files/{fid}?as=metadata"` returns JSON conforming to `DownloadMetadata`
- Web app still renders submission downloads (without code change)
- Mobile app still renders submission downloads (without code change)
- Range request against the presigned URL returns 206

#### ⚠️ Risks

- **Clients that strip Authorization on redirect**: most browsers / Dio do, but the presigned URL doesn't need it (signature in query string). Verify no client adds an Authorization header when fetching MinIO.
- **CORS on MinIO**: clients fetching directly from MinIO from a different origin require CORS rules on the bucket.
- **PDFs displayed inline vs attachment**: choose `inline` for in-app preview, `attachment` for "download" buttons. Pass via query param if needed.
- **Audit log volume**: don't audit every presign issuance — sample or remove existing per-download audit calls.

---

### Phase 4 — Data Migration

#### 🎯 Objective

Move every file currently in the local `uploads/` volume into MinIO, preserving the relative path as the object key, idempotently and verifiably.

#### ✅ Checklist

- [ ] Write `scripts/migrate_local_to_minio.py`
- [ ] Dry-run mode (lists keys, never writes)
- [ ] Idempotent (skip if key exists with matching size or etag)
- [ ] Checksum sample verification
- [ ] Logging + summary report
- [ ] Run in dev → staging → prod
- [ ] Archive `uploads/` after success (do not delete immediately)

#### 🔽 Detailed Steps

**Step 4.1 — Migration script skeleton**

- File: `scripts/migrate_local_to_minio.py` (new)
- CLI flags: `--source DIR`, `--bucket NAME`, `--dry-run`, `--verify-sample N`, `--concurrency N`
- Reads MinIO settings from existing `app.core.config`
- Walks the source directory recursively
- For each file: object key = path relative to source dir
- Expected: script importable; `--help` works
- Dependencies: Phase 2

**Step 4.2 — Idempotent upload**

- For each candidate file:
  - HEAD the destination key
  - If exists and `size_bytes` match (and optionally etag matches local SHA-256 for non-multipart objects), skip
  - Else, `put_object` with the original MIME (best guess via `mimetypes`)
- Expected: re-running the script after a partial run picks up only missing files
- Dependencies: Step 4.1

**Step 4.3 — Concurrency**

- Use a bounded `asyncio.Semaphore` (default concurrency 8)
- Expected: script saturates network without flooding MinIO
- Dependencies: Step 4.2

**Step 4.4 — Verification sample**

- Pick `N` random files post-migration (default `N=50`)
- Download via presigned URL
- Compare SHA-256 to source
- Expected: 100% match in sample; non-zero diff aborts the run
- Dependencies: Step 4.2

**Step 4.5 — Reporting**

- Emit a JSON summary: `{ scanned, uploaded, skipped, failed, sample_passed, total_bytes, duration_seconds }`
- Log to stdout and to `artifacts/minio_migration_{env}_{timestamp}.json`
- Expected: human-readable post-run report
- Dependencies: Step 4.4

**Step 4.6 — Run order**

- Dev: run, verify, eyeball app
- Staging: run during low-traffic window, verify, eyeball app
- Prod: run during maintenance window or with double-write enabled (see Risks)
- Expected: every env reports `failed=0` and `sample_passed=true`
- Dependencies: Steps 4.1 – 4.5

**Step 4.7 — Archive `uploads/`**

- After Phase 5 complete and stable:
  - Tar + compress: `uploads_{env}_{date}.tar.gz` to a backup location
  - Keep for at least 30 days, then delete
- Expected: rollback possible during the grace period
- Dependencies: Phase 5

#### 🧪 Validation

- Script runs end-to-end without error on dev
- `mc ls ecole/ecole-dev-private --recursive | wc -l` matches local file count
- Sample SHA-256 matches
- App still functions end-to-end (uploads/downloads) after switch in Phase 5

#### ⚠️ Risks

- **Live writes during migration**: in prod, new uploads keep landing in `uploads/` while migration runs. Mitigation options:
  - Run during scheduled maintenance window with read-only mode, OR
  - Implement temporary "double-write" (LocalStorageBackend writes to both targets) before migrating, then re-run migration to catch new files.
- **Filename collisions**: if any local path contains characters MinIO disallows in keys, normalize before upload.
- **Memory pressure** on very large files: stream `put_object` from a file handle, do not read into memory.
- **Time skew**: if local clock is wrong, presigned URL TTLs may be invalid — `ntp` should be running.

---

### Phase 5 — Switch to MinIO

#### 🎯 Objective

Flip `STORAGE_BACKEND=s3` per environment, validate, and drop the local `upload_data` volume mount once stable.

#### ✅ Checklist

- [ ] Set `STORAGE_BACKEND=s3` in dev `.env`
- [ ] Smoke test dev
- [ ] Set `STORAGE_BACKEND=s3` in staging
- [ ] Smoke test staging (full E2E suite)
- [ ] Set `STORAGE_BACKEND=s3` in prod (during planned window)
- [ ] Smoke test prod (read-only checks first)
- [ ] After 30-day grace, remove `upload_data` volume mounts
- [ ] After 30-day grace, archive and delete `uploads/`

#### 🔽 Detailed Steps

**Step 5.1 — Flip dev**

- File: `.env`, `infra/docker-compose.dev.yml`
- Set `STORAGE_BACKEND=s3`
- Restart `backend` and `worker`
- Expected: existing files still accessible (via 302 to MinIO); new uploads land in MinIO
- Dependencies: Phase 4 done in dev

**Step 5.2 — Smoke test dev**

- Manual checklist:
  - Upload a PDF as a teacher → verify object lands in MinIO
  - Download as a student → verify 302 + bytes match
  - Upload an image → verify thumbnail generated
  - Upload a video → verify Range request works
  - Upload an audio file → verify playback in `<audio>`
- Expected: every action passes
- Dependencies: Step 5.1

**Step 5.3 — Flip staging**

- Same as Step 5.1 for staging
- Run full E2E suite
- Dependencies: Phase 4 done in staging

**Step 5.4 — Flip prod**

- Schedule a maintenance note to users
- Same as Step 5.1 for prod
- Watch error rates and Grafana for 1 hour post-flip
- Dependencies: Phase 4 done in prod

**Step 5.5 — Cleanup local volume**

- File: `infra/docker-compose.dev.yml`, `infra/docker-compose.staging.yml`, `infra/docker-compose.prod.yml`
- After 30 days of stability, remove the `upload_data` volume from `backend` and `worker` services
- Remove the `upload_data:` volume declaration
- Keep `LocalStorageBackend` class in code (no removal — useful for tests and as a fallback)
- Expected: backend container no longer mounts `/app/uploads`; nothing breaks
- Dependencies: Steps 5.1 – 5.4 stable for 30 days

#### 🧪 Validation

- All file features (LMS, documents, content, submissions) work end-to-end on each env
- Error rate on `/api/v1/submissions/.../files/.*` and `/api/v1/content-items/.*/assets/.*` does not regress
- Disk usage of dev volume stops growing

#### ⚠️ Risks

- **Hidden caller of `LocalStorageBackend`**: a service might assume a real local path. Search for `local_path(` and `read(` callers; ensure none break when the backend is `s3`.
- **Long-lived processes** holding old config in memory: ensure full restart of backend and worker after the env change.
- **Rollback**: if a critical bug surfaces, set `STORAGE_BACKEND=local` and redeploy — local files are still on disk during the grace period.

---

### Phase 6 — Web Integration (optional)

#### 🎯 Objective

Update the React web app to consume signed URLs natively (cheaper, faster, scrubbing-capable for video).

#### ✅ Checklist

- [ ] Add `getDownloadUrl(path)` helper in API client
- [ ] Add `useSignedUrl(path)` hook (TanStack Query)
- [ ] Update `submissions.service.ts` download flow
- [ ] Update `cms.service.ts` asset rendering
- [ ] Switch video/audio/PDF rendering to native tags with signed URLs
- [ ] Cache invalidation on 403

#### 🔽 Detailed Steps

**Step 6.1 — API client helper**

- File: `web/src/services/api/client.ts`
- Add `getDownloadUrl(path: string): Promise<DownloadMetadata>` calling the metadata variant (`?as=metadata`)
- Expected: typed metadata returned to callers
- Dependencies: Phase 3

**Step 6.2 — `useSignedUrl` hook**

- File: `web/src/shared/hooks/useSignedUrl.ts` (new)
- Wraps `getDownloadUrl` in a TanStack Query
- `staleTime` = 80% of TTL (default 8 minutes)
- Refetch on 403 from MinIO
- Returns `{ url, expiresAt, mimeType, size, filename, isLoading, error }`
- Expected: components get a stable URL while it's valid; auto-renews near expiry
- Dependencies: Step 6.1

**Step 6.3 — Update submissions**

- File: `web/src/features/submissions/submissions.service.ts`, `useSubmissions.ts`
- Replace any blob-based download with: fetch metadata → use `<a href={url} download>` or open in tab
- Expected: download works without buffering through JS
- Dependencies: Step 6.2

**Step 6.4 — Update CMS assets**

- File: `web/src/features/cms/cms.service.ts`
- Replace `fetchAssetBlob` with `useSignedUrl`
- For video assets: render `<video src={url} controls />`
- For audio: render `<audio src={url} controls />`
- For PDF: render `<iframe src={url} />` or use pdf.js with the URL
- Expected: scrubbing on video works; bandwidth no longer goes through backend
- Dependencies: Step 6.2

**Step 6.5 — Error handling on 403**

- File: `web/src/shared/hooks/useSignedUrl.ts`
- When the URL returns 403 (e.g. expired), invalidate the query and refetch
- Expected: long-paused video resumes after refetch without user action
- Dependencies: Step 6.2

#### 🧪 Validation

- Video scrubbing is smooth (DevTools Network shows Range requests directly to MinIO)
- PDF preview opens instantly
- Network panel shows zero asset bytes through the backend container during playback
- Refresh after 10 minutes still plays (URL renews)

#### ⚠️ Risks

- **CORS** on MinIO bucket must allow the web origin; otherwise `<video>` fails silently.
- **Mixed content** in prod: MinIO must be served over HTTPS if the app is HTTPS.
- **TanStack Query cache key**: must include the resource id, **not** the URL itself.

---

### Phase 7 — Mobile Integration (optional)

#### 🎯 Objective

Update the Flutter mobile app to consume signed URLs natively with platform players.

#### ✅ Checklist

- [ ] Add `fetchSignedUrl(path)` in `api_client.dart`
- [ ] Add a small `SignedUrlCache`
- [ ] Wire `video_player` to signed URLs
- [ ] Wire `just_audio` (or `audioplayers`) to signed URLs
- [ ] Wire `flutter_pdfview` to signed URLs
- [ ] Handle 403 with refetch

#### 🔽 Detailed Steps

**Step 7.1 — API client method**

- File: `mobile/lib/data/api/api_client.dart`
- Add `Future<DownloadMetadata> fetchSignedUrl(String path)` calling the metadata variant
- Expected: typed result, error mapping consistent with existing API errors
- Dependencies: Phase 3

**Step 7.2 — Signed URL cache**

- File: `mobile/lib/data/services/signed_url_cache.dart` (new)
- Stores `{path → (url, expiresAt)}` in memory
- Returns cached URL while not expired (with 20% safety margin)
- Expected: avoids redundant calls during a viewing session
- Dependencies: Step 7.1

**Step 7.3 — Video player wiring**

- File: `mobile/lib/presentation/screens/.../video_screen.dart` (existing video screens)
- Initialize `VideoPlayerController.networkUrl(Uri.parse(url))` with the signed URL
- Refetch on 403 from `video_player`
- Expected: native scrubbing, hardware decoding
- Dependencies: Step 7.2

**Step 7.4 — Audio player wiring**

- File: existing audio screens
- Use `just_audio` `AudioSource.uri(Uri.parse(url))`
- Expected: smooth playback
- Dependencies: Step 7.2

**Step 7.5 — PDF rendering**

- File: existing PDF viewer screens
- Use `flutter_pdfview` with `PDFView(filePath: ...)` after downloading via signed URL to a temp file (or use a widget that supports network URLs directly)
- Expected: same UX as today, faster load
- Dependencies: Step 7.2

#### 🧪 Validation

- Video plays with seek bar working on iOS and Android
- Audio plays in background mode (if app supports)
- PDF renders within 1–2 seconds for typical assignment PDFs
- App still works offline for previously cached files (if applicable)

#### ⚠️ Risks

- **Background fetch** may not have the same auth context — refetch the URL on resume.
- **Older devices** may struggle with high-resolution videos; consider HLS in Phase 9 (out of scope here).
- **Certificate pinning**: if the app pins the API certificate, MinIO's certificate must also be trusted (or use a separate domain with proper pinning rules).

---

### Phase 8 — Large File Uploads (optional)

#### 🎯 Objective

Move large file uploads (videos, big PDFs) off the backend and directly to MinIO via presigned PUT, with post-upload validation and async virus scan.

#### ✅ Checklist

- [ ] Add `presign_put` to `S3StorageBackend`
- [ ] Add `POST /uploads/init` endpoint
- [ ] Add `POST /uploads/complete` endpoint
- [ ] Move virus scan to ARQ worker
- [ ] Add upload state to relevant DB rows (`uploading | scanning | available | quarantined`)
- [ ] Update web upload UI for direct PUT
- [ ] Update mobile upload UI for direct PUT
- [ ] Increase per-file size limit for videos

#### 🔽 Detailed Steps

**Step 8.1 — `presign_put` helper**

- File: `backend/app/core/storage.py`
- Add `async def presign_put(self, relative_path: str, *, expires_in: int, content_type: str, max_size: int) -> str`
- Use `generate_presigned_url("put_object", ...)` with `ContentType` and `ContentLength` constraints
- Expected: returns a URL the client can `PUT` to with the exact content type and size
- Dependencies: Phase 2

**Step 8.2 — `POST /uploads/init`**

- File: `backend/app/api/v1/uploads.py` (new)
- Body: `{ kind: "video"|"audio"|"document", filename, mime_type, size_bytes, scope: { course_id?, lesson_id?, ... } }`
- Behavior:
  - ACL check based on `scope`
  - Validate `mime_type` against allowed list and `size_bytes` against per-kind max
  - Generate object key (`schools/{sid}/videos/{course_id}/{uuid}.mp4`)
  - Insert DB row in `uploading` state
  - Return `{ upload_url, key, expires_at, max_size, upload_id }`
- Expected: client receives a one-time PUT URL
- Dependencies: Step 8.1

**Step 8.3 — `POST /uploads/complete`**

- File: `backend/app/api/v1/uploads.py`
- Body: `{ upload_id, sha256?, size_bytes? }`
- Behavior:
  - Backend `head_object` on the key
  - Validate size matches client claim
  - Persist final DB row (or update existing) → state `scanning`
  - Enqueue an ARQ job for virus scan + thumbnail generation
- Expected: upload visible to other users only after scan passes
- Dependencies: Step 8.2

**Step 8.4 — ARQ post-upload job**

- File: `backend/app/workers/post_upload.py` (new) and registered in `app.core.tasks.WorkerSettings`
- Job:
  - Stream the object from MinIO
  - Run `virus_scan_hook`
  - On clean: state → `available`, generate thumbnail if applicable
  - On infected: state → `quarantined`, delete object, audit log
- Expected: state transitions visible to the caller via a status endpoint
- Dependencies: Step 8.3

**Step 8.5 — Web direct PUT**

- File: `web/src/services/uploads/directUpload.ts` (new)
- Flow: `init` → `XMLHttpRequest.PUT(upload_url, file)` with progress events → `complete`
- Expected: upload progress works; backend bandwidth not consumed by file bytes
- Dependencies: Steps 8.2 – 8.4

**Step 8.6 — Mobile direct PUT**

- File: `mobile/lib/data/api/upload_client.dart` (new)
- Use Dio to PUT the file with `onSendProgress`
- Expected: same UX as today, much higher throughput
- Dependencies: Steps 8.2 – 8.4

**Step 8.7 — Per-kind size limits**

- File: `backend/app/core/config.py`
- Add `max_video_size_mb`, `max_audio_size_mb`, `max_document_size_mb`
- Wire into `init` validation
- Expected: videos up to 2 GB allowed; documents stay at 50 MB
- Dependencies: Step 8.2

#### 🧪 Validation

- Uploading a 1 GB video works in both web and mobile with progress
- Upload of an EICAR test file gets quarantined and is not visible to other users
- Backend container CPU and bandwidth do not spike during a large upload
- DB state transitions are observable and consistent

#### ⚠️ Risks

- **CORS for PUT** on the bucket: must allow `PUT`, `Content-Type`, and `x-amz-*` headers.
- **Orphaned objects**: if a client calls `init` and never `complete`, objects pile up. Mitigation: lifecycle rule expiring `uploading` state objects after 24 h.
- **Scan failures**: define a clear UX state for `scanning` (e.g. show "processing", disable "share").
- **TTL too short**: long uploads on slow networks may outlast the URL TTL — set TTL based on declared `size_bytes` and a minimum throughput assumption (e.g. 100 KB/s floor).

---

## 5. Cross-Cutting Concerns

### Environment variables

```bash
# Storage backend selection
STORAGE_BACKEND=s3                          # local | s3 — default local until Phase 5

# MinIO root (dev only — managed differently in prod)
MINIO_ROOT_USER=ecole-admin
MINIO_ROOT_PASSWORD=change-me-strong-secret

# S3 client (used by backend + worker + scripts)
S3_ENDPOINT=http://minio:9000               # https://minio.ecole.example.com in prod
S3_REGION=us-east-1
S3_ACCESS_KEY=ecole-backend
S3_SECRET_KEY=change-me-strong-secret
S3_BUCKET=ecole-dev-private                 # ecole-staging-private / ecole-prod-private
S3_FORCE_PATH_STYLE=true                    # required for MinIO; false for AWS S3
S3_SSE_ENABLED=true

# Presigned URL TTLs
S3_PRESIGN_GET_TTL_SECONDS=600              # 10 min default
S3_PRESIGN_PUT_TTL_SECONDS=900              # 15 min default (Phase 8)

# Per-kind size limits
MAX_VIDEO_SIZE_MB=2048                      # 2 GB (Phase 8)
MAX_AUDIO_SIZE_MB=200
MAX_DOCUMENT_SIZE_MB=50
```

### Security

- **Authorization remains in the backend**: every download endpoint runs the existing JWT + school boundary + role checks before issuing a presigned URL.
- **Presigned URLs are short-lived**: 10 min for GET, 15 min for PUT. Clients refresh transparently.
- **No direct credentials in clients**: only the backend has `S3_ACCESS_KEY` / `S3_SECRET_KEY`.
- **Bucket is private**: `mc anonymous set none` enforced by `minio-init`.
- **SSE-S3 at rest**: enabled at bucket level.
- **TLS in transit** for staging and prod (terminate at the MinIO-fronting reverse proxy).
- **Virus scan**: existing `virus_scan_hook` runs in Phase 1 path (multipart through backend); moves to ARQ post-upload job in Phase 8.
- **Audit log**: existing upload/delete audit calls stay; do **not** audit every presign issuance.

### Performance

- **Streaming**: clients fetch from MinIO directly with HTTP Range support — videos scrub natively.
- **No backend buffering**: download paths no longer go through FastAPI memory.
- **CDN**: optional in prod (CloudFront / Cloudflare). Presigned URLs work through CDNs as long as `X-Amz-*` query params are preserved.
- **Caching headers**: `Cache-Control: private, max-age=300` set at upload time.
- **Client-side URL cache**: TanStack Query on web, in-memory map on mobile, both at 80% of TTL.
- **Connection pooling**: single `aioboto3` session reused across requests.

### Backward compatibility

- **DB schema unchanged**: `storage_path` and `file_path` columns become object keys.
- **`LocalStorageBackend` retained**: not deleted, used for local dev without MinIO and for tests.
- **Existing endpoints unchanged**: same paths and methods, additional `?as=metadata` variant.
- **Default 302 redirect**: old clients keep working without code changes.
- **Gradual env rollout**: `STORAGE_BACKEND` switch is per-env and reversible.
- **Migration is idempotent**: re-runs are safe; rollback to local is possible during the 30-day grace period.

---

## 6. Execution Order

### Sequential phases (must be done in order)

1. **Phase 1 — Infrastructure**
2. **Phase 2 — Backend Storage Layer**
3. **Phase 3 — API Adaptation**
4. **Phase 4 — Data Migration**
5. **Phase 5 — Switch to MinIO**

> Phases 1–5 = Phase 1 of the broader rollout. They deliver MinIO end-to-end with **zero client changes**.

### Parallelizable phases (after Phase 5)

- **Phase 6 — Web Integration** ← can run in parallel with Phase 7
- **Phase 7 — Mobile Integration** ← can run in parallel with Phase 6
- **Phase 8 — Large File Uploads** ← starts after Phase 6 and Phase 7 are stable, because it changes the upload contract

```text
1 → 2 → 3 → 4 → 5 → ┬→ 6 ┐
                    ├→ 7 ├→ 8
                    └────┘
```

### Per-environment progression

For each phase that mutates an environment (1, 4, 5):

```text
dev → staging → prod
```

Never skip staging.

---

## 7. Definition of Done (DoD)

The integration is **done** when all of the following are true:

- [ ] `STORAGE_BACKEND=s3` is the active setting in dev, staging, and prod
- [ ] All file uploads (PDFs, images, videos, audio, documents) land in the per-env MinIO bucket under the `schools/{school_id}/...` prefix
- [ ] All file downloads return a 302 to a presigned URL by default and JSON metadata when `?as=metadata` is set
- [ ] No download bytes flow through the FastAPI process for any storage-backed resource
- [ ] The migration script ran successfully in every env with `failed=0` and verified sample
- [ ] The local `upload_data` Docker volume is removed from compose files
- [ ] The `uploads/` directory is archived and can be restored within 30 days
- [ ] `LocalStorageBackend` still passes its unit tests and remains usable for local dev
- [ ] All existing API tests pass; new tests for `S3StorageBackend` ≥ 90% coverage
- [ ] Bucket has SSE-S3 enabled, no public access, and lifecycle rules applied
- [ ] Presigned URL TTLs configurable via env (default 10 min for GET, 15 min for PUT)
- [ ] Documentation updated: `MINIO_INTEGRATION_ARCHITECTURE.md`, `INSTALLATION.md`, `.env.example`
- [ ] Runbook for rollback (`STORAGE_BACKEND=local`) documented
- [ ] (If Phase 6 done) Web app uses signed URLs natively for video/audio/PDF
- [ ] (If Phase 7 done) Mobile app uses signed URLs natively for video/audio/PDF
- [ ] (If Phase 8 done) Direct presigned PUT works for files up to the per-kind limit and post-upload virus scan transitions DB state correctly

---

## 8. Notes for AI Implementers

### Always do

- **Reuse the existing abstractions**: implement against `StorageBackend` and `FileStorageBackend`. Do not introduce a third storage interface.
- **Reuse existing validators**: `validate_mime_type`, `validate_file_size`, `virus_scan_hook` already exist — call them, do not duplicate.
- **Reuse `AuditService`**: every state-changing storage operation already has an audit call upstream — keep it; do not add new audit points for read.
- **Use a singleton `aioboto3` session**: instantiate once per process, share across requests.
- **Preserve `relative_path` semantics**: the value returned by `save()` must remain compatible with what's stored in `storage_path` / `file_path` columns.
- **Make the migration script idempotent**: HEAD before PUT, skip on match, verify with sample.
- **Default `STORAGE_BACKEND=local`** in any new config until Phase 5 — never change defaults to `s3` in code, only in env per environment.
- **Set `Content-Disposition`** appropriately on presigned GETs (`inline` for previews, `attachment` for downloads).
- **Force path-style** addressing for MinIO (`s3={"addressing_style": "path"}`).
- **Honor multi-tenancy**: every key must start with `schools/{school_id}/`.

### Never do

- **Do not change the DB schema** for storage paths. The columns are object keys.
- **Do not delete `LocalStorageBackend`**. It's the dev fallback and the test backend.
- **Do not stream file bytes through FastAPI for downloads**. The whole point of this integration is to stop that.
- **Do not create one bucket per tenant**. Use prefixes.
- **Do not embed user-supplied filenames as object keys** without sanitization. Existing helpers (`_safe_filename`, `uuid` prefix) must be preserved.
- **Do not hardcode bucket names**. Always read from settings.
- **Do not mix sync `boto3` and `aioboto3`** in the request path. All S3 calls in async code go through `aioboto3`.
- **Do not set TTL above 15 min** for sensitive content.
- **Do not break the 302 contract** in Phase 3 — existing clients depend on it.
- **Do not migrate prod without running staging first.**
- **Do not delete `uploads/`** before the 30-day grace period after Phase 5.

### Prioritize

1. **Backward compatibility** > new features. Every step must leave existing endpoints functional.
2. **Idempotency** in migration and any retryable operation.
3. **Observability**: add logs at each phase boundary; emit Prometheus metrics for presign rate and upload latency in Phase 2.
4. **Tests**: extend the existing pytest patterns; do not invent new frameworks.
5. **Reversibility**: every phase has a rollback (`STORAGE_BACKEND=local`, restore `uploads/`, revert env, etc.).

### When in doubt

- Re-read [Section 2 — Global Overview](#2-global-overview) and [Section 5 — Cross-Cutting Concerns](#5-cross-cutting-concerns).
- Default to **smaller, reversible PRs** over large batched ones.
- If a step seems to require a DB migration, **stop and reconsider** — this plan is explicitly designed to avoid it.
