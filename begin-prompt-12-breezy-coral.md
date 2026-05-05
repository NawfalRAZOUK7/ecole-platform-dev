# Phase 8 — Direct-to-MinIO Large File Upload: Design Report

## Context

Prompts 1–8 delivered a complete MinIO storage backend. All uploads today flow through FastAPI as a byte proxy (`save()` on `S3StorageBackend` streams the body to `put_object`). That works for small files but saturates the backend container for large uploads (videos ≥ 100 MB). Phase 8 offloads byte transfer to a presigned PUT URL so the client writes directly to MinIO; the backend only authorizes, validates metadata, and runs post-upload scan/finalization. This is explicitly scoped as optional in the plan doc (Step 11) and is HLS-free.

**Invariants that cannot move:**
- Browser/mobile never receive S3 credentials (only short-lived signed URLs)
- Unscanned uploads are invisible to users
- HLS/transcoding is out of scope

---

## 1. Endpoint Specifications

### 1.1 `POST /uploads/init`

**File**: `backend/app/api/v1/uploads.py` (new)

**Purpose**: Authorize the upload, validate declared metadata, generate a presigned PUT URL, and create a tracking row in `upload_state = uploading`.

#### Request schema

```json
{
  "kind": "assignment_pdf | submission_file | content_asset | video | audio",
  "filename": "lecture-week3.mp4",
  "mime_type": "video/mp4",
  "size_bytes": 734003200,
  "scope": {
    "school_id": "uuid",
    "assignment_id": "uuid | null",
    "submission_id": "uuid | null",
    "content_item_id": "uuid | null"
  }
}
```

`scope` fields are kind-specific; irrelevant fields are ignored. At least one scope FK must match the kind (enforced in validation).

#### Response schema (200 OK)

```json
{
  "upload_id": "uuid",
  "upload_url": "https://minio.example.com/ecole-prod-private/schools/.../uuid.mp4?...",
  "object_key": "schools/{sid}/videos/{item_id}/{uuid}.mp4",
  "expires_at": "2026-05-05T14:15:00Z",
  "max_size_bytes": 2147483648,
  "required_headers": {
    "Content-Type": "video/mp4",
    "Content-Length": "734003200"
  }
}
```

`upload_url` is a presigned PUT URL. The client MUST send the exact `Content-Type` and `Content-Length` shown — MinIO enforces these via the signature.

**TTL formula**: `max(900, ceil(size_bytes / 102400))` seconds, capped at 86400 s (24 h). Gives a 100 KB/s floor so a 2 GB video gets ~6 h.

**Error responses**:
- `400` — unsupported MIME, size exceeds per-kind limit, missing required scope field
- `403` — missing permission or school boundary violation
- `404` — scope entity not found (e.g., `submission_id` doesn't exist)

---

### 1.2 `POST /uploads/complete`

**File**: `backend/app/api/v1/uploads.py`

**Purpose**: Signal that the client finished the PUT. Backend verifies via `HEAD`, transitions state to `scanning`, enqueues the ARQ scan job.

#### Request schema

```json
{
  "upload_id": "uuid",
  "sha256": "optional hex string — client-computed, used for integrity check",
  "size_bytes": 734003200
}
```

`sha256` is optional but strongly encouraged. When present, the ARQ job verifies it against the ETag (for non-multipart objects) or a streaming re-hash.

#### Response schema (202 Accepted)

```json
{
  "upload_id": "uuid",
  "state": "scanning",
  "status_url": "/api/v1/uploads/{upload_id}/status"
}
```

**Behavior sequence** (synchronous, fast):
1. Load `upload_session` by `upload_id`, assert `upload_state = uploading`, assert caller is the original uploader
2. `HEAD` the object key on MinIO — fail `409` if object not found (client didn't PUT yet)
3. Compare reported `size_bytes` with HEAD `ContentLength` — fail `422` if mismatch
4. Update `upload_sessions.upload_state = 'scanning'`, set `completed_at = now()`
5. Enqueue `task_post_upload_scan(upload_id)` via ARQ
6. Return 202

**Error responses**:
- `404` — `upload_id` not found
- `403` — caller is not the original uploader
- `409` — object not yet present in MinIO (client hasn't PUT)
- `410` — session expired (state is `failed` due to orphan cleanup)
- `422` — size mismatch between declared and actual

---

### 1.3 `GET /uploads/{id}/status` (optional, recommended)

**File**: `backend/app/api/v1/uploads.py`

**Purpose**: Polling endpoint so clients can display a progress state after calling `/complete`.

#### Response schema (200 OK)

```json
{
  "upload_id": "uuid",
  "state": "uploading | scanning | available | failed | quarantined",
  "kind": "video",
  "target_id": "uuid | null",
  "target_kind": "content_item_asset | submission_file | ...",
  "error_message": "null | string",
  "created_at": "ISO-8601",
  "completed_at": "ISO-8601 | null",
  "scanned_at": "ISO-8601 | null"
}
```

`target_id` is populated only when `state = available`. The client uses it to reload the final entity (e.g., the `ContentItemAsset` record) and show the uploaded file.

**Authorization**: Caller must be the original uploader OR have read permission on the upload's scope entity.

**Error responses**:
- `404` — `upload_id` not found
- `403` — caller has no access to this session

---

## 2. Upload State Machine

```
                  ┌─────────────────────────────────────────────────────────┐
                  │                                                         │
  POST /init      │    client PUT       POST /complete     ARQ scan pass    │
  ──────────► UPLOADING ──────────────► SCANNING ──────────────────► AVAILABLE
                  │                         │                               │
                  │                         │    ARQ scan infected          │
                  │                         └───────────────────────► QUARANTINED
                  │                         │                               │
                  │                         │    ARQ error / HEAD fail      │
                  │                         └───────────────────────► FAILED
                  │                                                         │
                  │  orphan cleanup (cron, >24h in UPLOADING)              │
                  └─────────────────────────────────────────────────────────┘
                                     ↓
                               (session deleted or state=FAILED)
```

| State | Visible to users? | Object in MinIO? | DB entity created? |
|---|---|---|---|
| `uploading` | No | No (being written by client) | No |
| `scanning` | No | Yes | No |
| `available` | Yes | Yes | Yes (created by ARQ worker) |
| `quarantined` | No | No (deleted by ARQ worker) | No |
| `failed` | No | Maybe (orphan cleanup handles it) | No |

---

## 3. Authorization Rules per Upload Kind

All upload kinds require a valid JWT from the school matching `scope.school_id`. No inter-school uploads are possible.

| Kind | Required permission | Who can upload | Scope FK required | School boundary |
|---|---|---|---|---|
| `assignment_pdf` | `PERM_LMS_CONTENT_ASSET_UPLOAD` | Teacher or admin who owns the assignment's course | `assignment_id` | `assignment.school_id == JWT school` |
| `submission_file` | `PERM_LMS_SUBMISSION_FILE_UPLOAD` | Student who owns the submission (or teacher for correction feedback) | `submission_id` | `submission.school_id == JWT school` |
| `content_asset` | `PERM_LMS_CONTENT_ASSET_UPLOAD` | Teacher/admin with course write access | `content_item_id` | `content_item.school_id == JWT school` |
| `video` | `PERM_LMS_CONTENT_ASSET_UPLOAD` | Teacher/admin with course write access | `content_item_id` | same |
| `audio` | `PERM_LMS_CONTENT_ASSET_UPLOAD` | Teacher/admin with course write access | `content_item_id` | same |

The `/init` handler must load the scope entity from the DB to verify ownership, not just check the permission string. A teacher can upload a content asset only for their own course, not any course in the school.

---

## 4. Validation Rules

### 4.1 Per-kind MIME and size limits

| Kind | Allowed MIME types | Max `size_bytes` | Notes |
|---|---|---|---|
| `assignment_pdf` | `application/pdf` | 50 MB | Strict PDF only |
| `submission_file` | `application/pdf`, `image/jpeg`, `image/png`, `image/gif`, `application/vnd.openxmlformats-officedocument.*`, `application/msword`, `application/zip`, `text/plain` | 100 MB | Existing `allowed_mime_types` config |
| `content_asset` | All `submission_file` MIME types + `application/vnd.ms-excel`, `application/vnd.ms-powerpoint` | 200 MB | |
| `video` | `video/mp4` | 2048 MB (2 GB) | `MAX_VIDEO_SIZE_MB` config |
| `audio` | `audio/mpeg`, `audio/mp4`, `audio/ogg`, `audio/wav` | 200 MB | `MAX_AUDIO_SIZE_MB` config |

Config keys to add to `app/core/config.py`:
```
max_video_size_mb: int = 2048
max_audio_size_mb: int = 200
max_submission_file_size_mb: int = 100
max_content_asset_size_mb: int = 200
```
`max_document_size_mb` already exists (50 MB).

### 4.2 Content-Length enforcement

The presigned PUT URL is generated with `ContentType` and `ContentLength` included in the signed parameters. MinIO rejects any PUT where the actual body length differs from the signed `ContentLength`. This prevents:
- Size limit bypass (upload more than declared)
- MIME spoofing (different Content-Type at PUT time)

The `generate_presigned_url("put_object", Params={..., "ContentType": mime_type, "ContentLength": size_bytes})` call in `presign_put` handles this automatically.

### 4.3 Object key prefix rules

| Kind | Key prefix pattern | Extension source |
|---|---|---|
| `assignment_pdf` | `schools/{sid}/exercises/{assignment_id}/{uuid}.pdf` | Hardcoded `.pdf` |
| `submission_file` | `schools/{sid}/submissions/{submission_id}/{uuid}{ext}` | Derived from `mime_type` (mime→ext map) |
| `content_asset` | `schools/{sid}/content/{item_id}/{uuid}{ext}` | Derived from `mime_type` |
| `video` | `schools/{sid}/videos/{item_id}/{uuid}.mp4` | Hardcoded `.mp4` |
| `audio` | `schools/{sid}/audio/{item_id}/{uuid}{ext}` | Derived from `mime_type` |

The `{uuid}` is generated server-side at `/init` time. Clients never construct keys.

Key generation lives in a `_build_object_key(kind, scope, mime_type) -> str` helper in the new `uploads.py` router. The helper validates that the prefix matches the expected pattern before calling `presign_put`.

---

## 5. ARQ Worker: `task_post_upload_scan`

**New file**: `backend/app/core/tasks.py` (add to existing `WorkerSettings.functions`)  
**Implementation file**: `backend/app/workers/post_upload.py` (new)

### Responsibilities

```
task_post_upload_scan(ctx, upload_id: str) -> None
```

1. **Load session**: fetch `upload_sessions` row by `upload_id`; if not found or state ≠ `scanning`, log warning and return (idempotent)
2. **HEAD verification**: call `storage.stat(object_key)` — if object missing, update state → `failed` with error message and return
3. **Virus scan**: stream object from MinIO via `storage.read_stream(object_key)`, pipe to `virus_scan_hook`. If scan unavailable (ClamAV down): update state → `failed`, set `error_message = "scan service unavailable"`, **re-enqueue with exponential backoff** (3 attempts, 30s/120s/300s delays)
4. **On CLEAN**:
   a. Generate thumbnail if kind is `content_asset` with image MIME or `video` (image: PIL resize to 200×200; video: skip in Phase 8, note as future work)
   b. Call `_create_target_entity(session)` — creates the appropriate DB record:
      - `assignment_pdf` → update `assignments.exercise_pdf_path = object_key`
      - `submission_file` → insert `SubmissionFile(file_path=object_key, mime_type=..., file_size=...)`
      - `content_asset` / `video` / `audio` → insert `ContentItemAsset(file_path=object_key, ...)`
   c. Update `upload_sessions.upload_state = 'available'`, set `scanned_at = now()`, set `target_id = new_entity_id`
5. **On INFECTED**:
   a. Delete object from MinIO: `storage.delete(object_key)`
   b. Update `upload_sessions.upload_state = 'quarantined'`, set `scanned_at = now()`, set `error_message = "file failed virus scan"`
   c. Write audit log entry (use existing audit log pattern in the codebase)
6. **On unhandled exception**: update state → `failed`, set `error_message` to exception string; do NOT delete the object

### Retry policy

| Attempt | Delay | State during wait |
|---|---|---|
| 1 (initial) | — | `scanning` |
| 2 | 30 s | `scanning` |
| 3 | 120 s | `scanning` |
| 4 (final) | 300 s | `scanning` |

After 4 failures: state → `failed`, `error_message = "scan failed after max retries"`.

### Orphan cleanup

Add to existing cron schedule in `WorkerSettings`:
- `task_cleanup_orphaned_uploads` — runs daily at 04:00 UTC
- Selects rows where `state = 'uploading'` AND `created_at < now() - 24h`
- Attempts `storage.delete(object_key)` (best effort, object may not exist yet)
- Updates rows to `state = 'failed'`, `error_message = 'upload session expired'`

This complements the MinIO lifecycle rule (expire objects under `schools/*/uploading/` prefix after 24h) as a belt-and-suspenders approach.

---

## 6. DB Schema Additions

**Only one new table is required.** Existing file-bearing tables (`submission_files`, `content_item_assets`, `assignments`, `documents`) do not need new columns. The `upload_sessions` table is the sole state-tracking surface.

### New table: `upload_sessions`

```sql
CREATE TABLE upload_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    upload_state    VARCHAR(20) NOT NULL DEFAULT 'uploading',
                    -- CHECK: ('uploading','scanning','available','quarantined','failed')
    kind            VARCHAR(30) NOT NULL,
                    -- CHECK: ('assignment_pdf','submission_file','content_asset','video','audio')
    object_key      TEXT NOT NULL,
    mime_type       TEXT NOT NULL,
    size_bytes      BIGINT NOT NULL,
    sha256          TEXT,                -- client-declared at /complete, nullable
    school_id       UUID NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    uploader_id     UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    scope_data      JSONB NOT NULL DEFAULT '{}',
                    -- e.g. {"assignment_id":"...", "submission_id":null, "content_item_id":"..."}
    expires_at      TIMESTAMP WITH TIME ZONE NOT NULL,  -- presigned URL expiry
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    completed_at    TIMESTAMP WITH TIME ZONE,           -- set by /complete
    scanned_at      TIMESTAMP WITH TIME ZONE,           -- set by ARQ worker
    target_id       UUID,                               -- set when state='available'
    target_kind     TEXT,                               -- e.g. 'submission_file'
    error_message   TEXT
);

CREATE INDEX idx_upload_sessions_state ON upload_sessions(upload_state);
CREATE INDEX idx_upload_sessions_school ON upload_sessions(school_id);
CREATE INDEX idx_upload_sessions_uploader ON upload_sessions(uploader_id);
CREATE INDEX idx_upload_sessions_created ON upload_sessions(created_at);
```

**No `upload_state` column is added to `submission_files`, `content_item_assets`, or `assignments`.** Those rows are created only after the scan passes, so they are always in a valid/visible state. Backward compatibility with proxy-uploaded files is automatic — those rows exist without an `upload_session` and remain visible.

### Why not add columns to existing tables?

| Approach | Migrations | Backward compat | Risk |
|---|---|---|---|
| Single `upload_sessions` table | 1 migration | Perfect — old rows unaffected | Low |
| Add `upload_state` to each table | 4–5 migrations | Requires NULL handling / default in each query | Medium |
| Polymorphic `target_id` on existing tables | 4–5 migrations | Complex JOIN logic | High |

The single-table approach is migration-safe, reversible (drop the table to roll back), and isolates the upload lifecycle concern cleanly.

---

## 7. Migration Plan

### Migration file

**File**: `backend/alembic/versions/{hash}_g{N+1}_phase8_upload_sessions.py`

**Operations** (all in one migration, forward only):

```python
def upgrade():
    op.create_table('upload_sessions', ...)   # as defined above
    op.create_index(...)                       # 4 indexes
    op.execute("COMMENT ON TABLE upload_sessions IS 'Phase 8: direct-to-MinIO upload lifecycle tracking'")

def downgrade():
    op.drop_table('upload_sessions')          # safe — no FK references from other tables
```

**Migration safety**:
- Non-blocking (new table, no column adds to existing tables)
- Downgrade is safe: `drop_table` on an empty or irrelevant table
- Zero data migration needed (no existing rows to backfill)
- Can be run while the app is live (no lock contention)

### Rollout order

1. Run migration (zero-downtime)
2. Deploy backend with new `/uploads/*` endpoints (new module, no changes to existing endpoints)
3. Deploy ARQ worker with `task_post_upload_scan` (new function registered in `WorkerSettings`)
4. Ship web/mobile direct-upload UI (Steps 8.5 / 8.6 in the plan doc)
5. Optionally: add MinIO lifecycle rule for `schools/*/videos/` prefix (infra-only, no deploy)

Each step is independently shippable as a small PR.

---

## 8. CORS Requirement (Infra)

MinIO bucket CORS must allow direct PUT from web/mobile origins. Configuration to add to `infra/docker-compose.dev.yml` MinIO init:

```json
{
  "CORSRules": [{
    "AllowedOrigins": ["https://app.ecole.example.com"],
    "AllowedMethods": ["PUT"],
    "AllowedHeaders": ["Content-Type", "Content-Length", "x-amz-*"],
    "MaxAgeSeconds": 3600
  }]
}
```

Without this, browsers block the PUT. This is a known risk flagged in the plan doc (Phase 8 risks).

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Client never calls `/complete` after PUT | Orphaned objects accumulate | Lifecycle rule (24h expiry) + daily cron cleanup |
| Presigned URL TTL too short for large file on slow network | Upload fails mid-way | Dynamic TTL formula: `max(900, ceil(size_bytes/102400))` s |
| ClamAV unavailable during scan | File stuck in `scanning` | ARQ retries with backoff; state → `failed` after 4 attempts |
| Client lies about `size_bytes` in `/init`, uploads different size | MinIO rejects the PUT (enforced by signed ContentLength) | Signature enforcement + HEAD re-check in `/complete` |
| CORS not configured on MinIO | Browser PUT silently fails | Document as prerequisite; integration test PUT from browser origin |
| `assignment_pdf` state: PDF exists in MinIO but `exercise_pdf_path` not yet updated | Race condition if user requests before ARQ finishes | `GET /assignments/{id}/exercise-pdf` returns 404 until `available`; client uses `/status` to poll |
| Video thumbnail generation in ARQ | Not implemented in Phase 8 | Explicitly deferred; `thumbnail_path` remains null for videos |

---

## 10. Implementation Decomposition (Small PRs)

| PR | Contents | Risk |
|---|---|---|
| PR-A | Alembic migration for `upload_sessions` | Zero — new table only |
| PR-B | `presign_put` method on `S3StorageBackend` + unit tests | Low — additive |
| PR-C | `POST /uploads/init` + `POST /uploads/complete` + `GET /uploads/{id}/status` endpoints | Medium — new auth/validation logic |
| PR-D | `task_post_upload_scan` ARQ worker + `task_cleanup_orphaned_uploads` cron | Medium — side effects |
| PR-E | Web `directUpload.ts` service + UI progress | Low (frontend only) |
| PR-F | Mobile `upload_client.dart` + Dio progress | Low (mobile only) |
| PR-G | MinIO CORS + lifecycle rule config | Infra only |

PRs A→B→C→D must be merged in order. E, F, G can land in any order after D.

---

## 11. Verification Checklist

- [ ] `upload_sessions` table created; downgrade drops it cleanly
- [ ] `POST /uploads/init` for `video/mp4` at 1 GB returns a presigned PUT URL with correct TTL
- [ ] MinIO rejects a PUT with wrong Content-Length (verify with `curl`)
- [ ] `POST /uploads/complete` fails with `409` if object not yet in MinIO
- [ ] ARQ worker transitions state: `scanning` → `available` after clean scan
- [ ] ARQ worker transitions state: `scanning` → `quarantined` on EICAR test file; object deleted from MinIO
- [ ] `GET /uploads/{id}/status` returns `target_id` only after state = `available`
- [ ] Proxy-upload path (existing `POST /submissions/{id}/files`) still works unchanged
- [ ] Backend container CPU and bandwidth are flat during a 500 MB direct upload
- [ ] Orphan cleanup deletes sessions older than 24h in `uploading` state

---

## Files Referenced

| Purpose | Path |
|---|---|
| Storage backend (add `presign_put`) | `backend/app/core/storage.py` |
| Config (add per-kind size limits) | `backend/app/core/config.py` |
| New uploads router | `backend/app/api/v1/uploads.py` (new) |
| ARQ tasks registry | `backend/app/core/tasks.py` |
| Post-upload scan worker | `backend/app/workers/post_upload.py` (new) |
| New Alembic migration | `backend/alembic/versions/{hash}_g{N+1}_phase8_upload_sessions.py` (new) |
| Architecture doc (§2.5, §4) | `ecole-platform-dev/MINIO_INTEGRATION_ARCHITECTURE.md` |
| Execution plan (Phase 8) | `ecole-platform-dev/minio-integration-plan.md` lines 640–738 |
