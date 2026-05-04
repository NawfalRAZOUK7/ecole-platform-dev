# MinIO Storage Rollout — Phase 5 Runbook

> **Status**: Phases 1–4 implemented. Ready for per-environment activation.  
> **Audience**: person deploying the storage switch.  
> **Time estimate**: ~30 minutes per environment (excluding migration script runtime).

---

## Table of Contents

1. [Overview](#1-overview)
2. [Prerequisites](#2-prerequisites)
3. [Rollout order](#3-rollout-order)
4. [Dev rollout — step by step](#4-dev-rollout--step-by-step)
5. [Staging rollout — step by step](#5-staging-rollout--step-by-step)
6. [Production rollout — step by step](#6-production-rollout--step-by-step)
7. [Smoke test checklist](#7-smoke-test-checklist)
8. [Rollback procedure](#8-rollback-procedure)
9. [Grace period and upload_data cleanup](#9-grace-period-and-upload_data-cleanup)
10. [Reference — environment variables](#10-reference--environment-variables)

---

## 1. Overview

Flipping `STORAGE_BACKEND=s3` (and `DOCUMENT_STORAGE_BACKEND=s3`) makes the backend
read and write all files through MinIO instead of the local `uploads/` directory.

**What changes after the flip:**

- New uploads → land in MinIO bucket under the original `relative_path` as object key.
- Downloads → return `302 → presigned URL` (unchanged contract for web/mobile clients).
- Existing files → only accessible from MinIO; local `uploads/` is a cold read-only backup
  during the 30-day grace period.

**What does NOT change:**

- DB schema — `storage_path` / `file_path` columns remain object keys (no migration needed).
- API routes — same URLs, same HTTP methods, same auth.
- `LocalStorageBackend` code — stays in place, used for tests and rollback.
- `upload_data` Docker volume — stays mounted during the entire grace period.

> ⚠️ **Never skip staging.** Always run dev → staging → prod in order.

---

## 2. Prerequisites

Confirm all of the following before starting any environment flip:

| #   | Check                                 | How to verify                                                                     |
| --- | ------------------------------------- | --------------------------------------------------------------------------------- |
| 1   | Phases 1–4 code is deployed           | `git log --oneline -5` shows migration commits                                    |
| 2   | MinIO is reachable from backend       | `docker exec ecole-backend curl -sf http://minio:9000/minio/health/live`          |
| 3   | Bucket exists and is private          | `docker exec ecole-minio-init mc ls local/<bucket>` (or MinIO console at `:9001`) |
| 4   | SSE-S3 is enabled on the bucket       | MinIO console → bucket → Encryption tab shows `SSE-S3`                            |
| 5   | Migration script ran successfully     | `cat artifacts/minio_migration_*.json \| python3 -m json.tool` — `"failed": 0`    |
| 6   | Verification sample passed            | Same file — `"sample_passed": true`                                               |
| 7   | Object count matches local file count | `mc ls --recursive ecole/<bucket> \| wc -l` ≈ local file count                    |
| 8   | No ongoing uploads during flip        | Confirm with team; schedule a low-traffic window for staging/prod                 |

---

## 3. Rollout order

```text
dev  ──►  staging  ──►  prod
```

**Never flip prod before staging has been stable for at least 24 hours.**

---

## 4. Dev rollout — step by step

### 4.1 Run the migration script (if not already done)

```bash
# Dry run first — verify scope
python scripts/migrate_local_to_minio.py \
    --dry-run \
    --source uploads/ \
    --bucket ecole-dev-private

# Real run with verification sample
python scripts/migrate_local_to_minio.py \
    --source uploads/ \
    --bucket ecole-dev-private \
    --verify-sample 50
```

Check the summary in `artifacts/minio_migration_development_*.json`:

```json
{
  "failed": 0,
  "sample_passed": true
}
```

### 4.2 Flip the storage backend

Edit `.env` (dev only — never commit this change to the repo; keep it in your local `.env`):

```bash
# --- Before ---
STORAGE_BACKEND=local
DOCUMENT_STORAGE_BACKEND=local

# --- After ---
STORAGE_BACKEND=s3
DOCUMENT_STORAGE_BACKEND=s3
```

> The `.env.example` comment intentionally says "keep local until migration is complete".
> This is the moment migration is confirmed complete for dev.

### 4.3 Restart backend and worker

```bash
docker compose -f infra/docker-compose.dev.yml restart backend worker
# Wait ~10 seconds, then verify health
make health
# Expected: {"status": "healthy", ...}
```

### 4.4 Run the smoke test checklist

Follow [Section 7](#7-smoke-test-checklist) completely.

### 4.5 Confirm zero pending uploads

Re-run the migration script to confirm all files are already in MinIO:

```bash
python scripts/migrate_local_to_minio.py \
    --source uploads/ \
    --bucket ecole-dev-private \
    --verify-sample 0  # skip re-verification; just confirm counts

# Expected output: uploaded=0, failed=0
```

### 4.6 Keep upload_data mounted

Do **not** remove `upload_data` from compose. It remains mounted as a cold backup
for the 30-day grace period (see [Section 9](#9-grace-period-and-upload_data-cleanup)).

---

## 5. Staging rollout — step by step

### 5.1 Run the migration script against staging

```bash
# Staging credentials come from CI/CD environment or secrets manager
S3_ENDPOINT=https://minio.staging.example.com \
S3_ACCESS_KEY=<staging-access-key> \
S3_SECRET_KEY=<staging-secret-key> \
python scripts/migrate_local_to_minio.py \
    --source /path/to/staging/uploads/ \
    --bucket ecole-staging-private \
    --verify-sample 50
```

### 5.2 Flip the storage backend

In your staging `.env` or CI/CD secrets manager:

```bash
STORAGE_BACKEND=s3
DOCUMENT_STORAGE_BACKEND=s3
```

`docker-compose.staging.yml` already injects these via `${STORAGE_BACKEND:-local}`
(the default remains `local` until you change the env).

### 5.3 Restart backend

```bash
docker compose -f infra/docker-compose.staging.yml restart backend worker
```

If you use zero-downtime deploys (rolling replicas), trigger a rolling restart through
your CI/CD pipeline so at least one replica stays healthy during the restart.

### 5.4 Run the smoke test checklist

Follow [Section 7](#7-smoke-test-checklist) against the staging URL.

### 5.5 Monitor for 24 hours

Watch for:

- `5xx` spikes on `/api/v1/submissions/*/files/*`, `/api/v1/content-items/*/assets/*`,
  `/api/v1/assignments/*/exercise-pdf`, `/api/v1/documents/*`
- `Location:` header in download responses pointing to `minio.staging.example.com` (not local)
- MinIO error rate in Grafana (if monitoring is up)

Only proceed to production after 24 hours of stable staging.

---

## 6. Production rollout — step by step

> ⚠️ **Run during a scheduled maintenance window.** Announce to users in advance.  
> ⚠️ **Confirm staging has been stable for ≥ 24 hours before proceeding.**

### 6.1 Pre-flight read-only check

Before any changes, verify the prod MinIO bucket is reachable and populated:

```bash
# From a machine with prod credentials
mc alias set prod https://minio.prod.example.com <access-key> <secret-key>
mc ls prod/ecole-prod-private --recursive | wc -l
# Must match local file count
```

### 6.2 Run the migration script against production

```bash
S3_ENDPOINT=https://minio.prod.example.com \
S3_ACCESS_KEY=<prod-access-key> \
S3_SECRET_KEY=<prod-secret-key> \
python scripts/migrate_local_to_minio.py \
    --source /prod/uploads/ \
    --bucket ecole-prod-private \
    --concurrency 4 \
    --verify-sample 100
```

Use `--concurrency 4` (lower than default) to avoid overwhelming prod MinIO.

### 6.3 Flip the storage backend

In prod `.env.prod` or secrets manager:

```bash
STORAGE_BACKEND=s3
DOCUMENT_STORAGE_BACKEND=s3
```

### 6.4 Restart backend (rolling, zero-downtime)

```bash
# Rolling restart via Docker / orchestrator
docker compose -f infra/docker-compose.prod.yml up -d --no-deps backend worker
```

Or trigger a rolling deploy in your CI/CD pipeline.

### 6.5 Run the smoke test checklist

Follow [Section 7](#7-smoke-test-checklist) against the prod URL.
Use **read-only checks first** (downloads only) before testing uploads.

### 6.6 Watch error rates for 1 hour

Alert thresholds to watch:

- Backend `5xx` rate > 0.1% → roll back immediately.
- Download `302` responses with `Location: http://minio:9000/...` (wrong: that's the internal address) → check `S3_ENDPOINT` value.
- MinIO `4xx` rate > 1% → presigned URL TTL or CORS issue.

---

## 7. Smoke test checklist

Run these checks **after restarting** in each environment. Use `TOKEN` = a valid JWT
from a teacher or admin account.

```bash
API="http://localhost:8000/api/v1"   # adjust per env
TOKEN="<your-jwt-token>"
```

### 7.1 Assignment exercise PDF

```bash
# Upload (as teacher — use real IDs from your test data)
curl -s -X POST "$API/assignments/<ASSIGNMENT_ID>/exercise-pdf" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_files/sample_exercise.pdf"

# Download — expect 302 + Location pointing to MinIO
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/assignments/<ASSIGNMENT_ID>/exercise-pdf" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: HTTP/1.1 302 Found  + Location: https://minio.*/ecole-*-private/*

# Metadata variant
curl -s -H "Authorization: Bearer $TOKEN" \
    "$API/assignments/<ASSIGNMENT_ID>/exercise-pdf?as=metadata"
# Expected JSON: { "download_url": "https://minio...", "mime_type": "application/pdf", ... }
```

### 7.2 Submission file

```bash
# Upload submission file
curl -s -X POST "$API/submissions/<SUBMISSION_ID>/files" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_files/sample_submission.pdf"

# Download — expect 302
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/submissions/<SUBMISSION_ID>/files/<FILE_ID>" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: HTTP/1.1 302 Found  + Location: https://minio.*/ecole-*-private/*
```

### 7.3 Content asset

```bash
# Upload content asset
curl -s -X POST "$API/content-items/<CONTENT_ID>/assets" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_files/sample_image.png"

# Download via asset endpoint
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/content-items/<CONTENT_ID>/assets/<ASSET_ID>" | grep -E "^(HTTP|[Ll]ocation)"

# Stream endpoint
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/content-items/<CONTENT_ID>/stream" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: 302 for both
```

### 7.4 Document (student documents)

```bash
# Download document
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/documents/<DOCUMENT_ID>/download" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: 302

# Document preview
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/documents/<DOCUMENT_ID>/preview" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: 302

# Specific version
curl -sI -H "Authorization: Bearer $TOKEN" \
    "$API/documents/<DOCUMENT_ID>/versions/1/download" | grep -E "^(HTTP|[Ll]ocation)"
# Expected: 302
```

### 7.5 Verify bytes reach the client

Follow the `Location` URL from any of the above and confirm bytes arrive:

```bash
PRESIGNED_URL="<paste Location header value>"
curl -sI "$PRESIGNED_URL" | head -5
# Expected: HTTP/1.1 200 OK  (no Authorization header needed — presigned URL is self-authenticating)
```

### 7.6 Verify unauthorized access is blocked

```bash
# Without token — must return 401 or 403 (never a redirect to MinIO)
curl -sI "$API/submissions/<SUBMISSION_ID>/files/<FILE_ID>" | head -3
# Expected: HTTP/1.1 401 Unauthorized  (no Location header)
```

### 7.7 Video / audio (if sample files exist)

```bash
# Upload a short .mp4 (≤ 25 MB)
curl -s -X POST "$API/content-items/<CONTENT_ID>/assets" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_files/sample_video.mp4"

# Download — verify 302 and Range request works
PRESIGNED_URL=$(curl -s -H "Authorization: Bearer $TOKEN" \
    "$API/content-items/<CONTENT_ID>/assets/<ASSET_ID>?as=metadata" | python3 -c "import sys,json; print(json.load(sys.stdin)['download_url'])")

curl -sI -H "Range: bytes=0-1023" "$PRESIGNED_URL" | head -5
# Expected: HTTP/1.1 206 Partial Content
```

### 7.8 Backend log sanity check

```bash
docker compose -f infra/docker-compose.dev.yml logs --tail=50 backend | grep -iE "error|warn|exception"
# Expected: no storage-related errors
```

---

## 8. Rollback procedure

**Use this if any smoke test fails or if error rates spike post-flip.**

This procedure takes under 2 minutes.

### Step 1 — Revert the env

In `.env` (dev) or secrets manager (staging/prod):

```bash
# Change back to local
STORAGE_BACKEND=local
DOCUMENT_STORAGE_BACKEND=local
```

### Step 2 — Restart backend and worker

```bash
# Dev
docker compose -f infra/docker-compose.dev.yml restart backend worker

# Staging
docker compose -f infra/docker-compose.staging.yml restart backend worker

# Prod (rolling — adjust to your deployment method)
docker compose -f infra/docker-compose.prod.yml up -d --no-deps backend worker
```

### Step 3 — Verify health

```bash
make health
# Expected: {"status": "healthy", ...}
```

### Step 4 — Confirm local files are intact

```bash
# Dev
ls -lh uploads/
# All original files must still be present (we never deleted them)
```

### Step 5 — Triage before re-attempting

Check backend logs for the specific error:

```bash
docker compose -f infra/docker-compose.dev.yml logs --tail=100 backend | grep -iE "s3|minio|storage|boto"
```

Common causes:

| Symptom                                                 | Likely cause                           | Fix                                                       |
| ------------------------------------------------------- | -------------------------------------- | --------------------------------------------------------- |
| `NoSuchBucket`                                          | Wrong `S3_BUCKET` value                | Correct bucket name in env                                |
| `InvalidAccessKeyId`                                    | Wrong credentials                      | Update `S3_ACCESS_KEY` / `S3_SECRET_KEY`                  |
| `Connection refused`                                    | Wrong `S3_ENDPOINT`                    | Check endpoint URL (internal Docker hostname vs external) |
| `SignatureDoesNotMatch`                                 | Clock skew                             | Sync system clock: `ntpdate -s time.nist.gov`             |
| `307 redirect loop`                                     | `S3_FORCE_PATH_STYLE=false` with MinIO | Set `S3_FORCE_PATH_STYLE=true`                            |
| Downloads still returning `FileResponse` (200, not 302) | `STORAGE_BACKEND` not picked up        | Confirm env var is set and container was fully restarted  |

> ⚠️ **Do not remove `upload_data` volume at any point during triage.**
> Local files are the rollback surface — keep them until the 30-day grace period expires.

---

## 9. Grace period and upload_data cleanup

### Grace period policy

| Event                                              | Timeline                |
| -------------------------------------------------- | ----------------------- |
| `STORAGE_BACKEND=s3` stable in prod                | Day 0                   |
| Archive `uploads/` as `uploads_prod_<date>.tar.gz` | Day 0                   |
| Keep `upload_data` volume mounted                  | Days 0 – 30             |
| Remove `upload_data` mount from compose            | After Day 30            |
| Delete archived tarball                            | After Day 60 (optional) |

### How to archive local uploads before removing the volume

```bash
# On the host, not inside the container
docker run --rm \
    -v ecole-platform-dev_upload_data:/uploads:ro \
    -v "$(pwd)/backups":/backups \
    alpine \
    tar -czf /backups/uploads_dev_$(date +%Y%m%d).tar.gz -C /uploads .

# Verify the archive
tar -tzf backups/uploads_dev_*.tar.gz | head -20
```

### How to remove upload_data from compose (deferred — do not do this now)

Only execute these steps after the 30-day grace period has passed and no rollback
was needed.

**`infra/docker-compose.dev.yml`** — remove these lines:

```yaml
# In backend service volumes: — REMOVE after Day 30 of stable s3 operation
- upload_data:/app/uploads          # <-- remove this line

# In worker service volumes: — REMOVE after Day 30
- upload_data:/app/uploads          # <-- remove this line

# In top-level volumes: — REMOVE after Day 30
upload_data:                        # <-- remove this line
```

**`infra/docker-compose.staging.yml`** — remove:

```yaml
# In backend service volumes:
- staging_uploads:/app/uploads      # <-- remove after Day 30

# In top-level volumes:
staging_uploads:                    # <-- remove after Day 30
```

**`infra/docker-compose.prod.yml`** — remove:

```yaml
# In backend service volumes:
- backend_uploads:/app/uploads      # <-- remove after Day 30

# In top-level volumes:
backend_uploads:                    # <-- remove after Day 30
```

After editing compose files:

```bash
docker compose -f infra/docker-compose.dev.yml up -d --no-deps backend worker
# Confirm health
make health
```

> `LocalStorageBackend` code remains in the codebase indefinitely — it is the local dev
> fallback and the rollback path. Only the Docker volume mount is removed.

---

## 10. Reference — environment variables

### Per-environment bucket names

| Environment | Bucket                  |
| ----------- | ----------------------- |
| dev         | `ecole-dev-private`     |
| staging     | `ecole-staging-private` |
| prod        | `ecole-prod-private`    |

### Variables that control the storage switch

```bash
# Both must be changed together
STORAGE_BACKEND=s3               # local (default) | s3
DOCUMENT_STORAGE_BACKEND=s3     # local (default) | s3
```

### MinIO connection variables

```bash
S3_ENDPOINT=http://minio:9000    # Internal Docker hostname for dev
                                  # https://minio.staging.example.com for staging
                                  # https://minio.prod.example.com for prod
S3_BUCKET=ecole-dev-private
S3_REGION=us-east-1
S3_ACCESS_KEY=<key>
S3_SECRET_KEY=<secret>
S3_FORCE_PATH_STYLE=true         # Required for MinIO; false for AWS S3
S3_SSE_ENABLED=true
S3_PRESIGN_GET_TTL_SECONDS=600   # 10 min — download / preview links
S3_PRESIGN_PUT_TTL_SECONDS=900   # 15 min — direct upload links (Phase 8)
```

### Presigned URL validation

A correctly issued presigned URL:

- Starts with `https://minio.<env>.example.com/ecole-<env>-private/`
- Contains `X-Amz-Expires=600` (or the configured TTL)
- Does **not** require an `Authorization` header
- Returns `200 OK` directly from MinIO (no backend hop)
