/**
 * Phase 8 — Direct-to-MinIO upload service.
 *
 * Flow: POST /uploads/init → XHR PUT (presigned URL, no auth header) →
 *       POST /uploads/complete → poll GET /uploads/{id}/status until terminal state.
 *
 * Routing: video/audio always use direct upload; other kinds use direct when
 * file exceeds DIRECT_UPLOAD_THRESHOLD_BYTES. Small files use the legacy
 * multipart path in their respective service modules.
 *
 * Security invariants:
 *   - upload_url is never persisted (logged only in DEV)
 *   - putToStorage sends NO Authorization header to MinIO
 *   - Callers must not retry the PUT; restart from init on failure
 */

import { api } from '@/services/api/client';

// ---------------------------------------------------------------------------
// Public types
// ---------------------------------------------------------------------------

export type UploadKind = 'assignment_pdf' | 'submission_file' | 'content_asset' | 'video' | 'audio';

export type UploadState =
  | 'preparing'
  | 'uploading'
  | 'processing'
  | 'available'
  | 'failed'
  | 'quarantined';

export interface UploadScope {
  school_id: string;
  assignment_id?: string;
  submission_id?: string;
  content_item_id?: string;
}

export interface DirectUploadOptions {
  kind: UploadKind;
  scope: UploadScope;
  file: File;
  onProgress?: (percent: number) => void;
  onStateChange?: (state: UploadState) => void;
}

export interface DirectUploadResult {
  upload_id: string;
  target_id: string | null;
  target_kind: string | null;
  state: UploadState;
}

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

export class UploadTimeoutError extends Error {
  constructor() {
    super('Upload scan timed out — please try again');
    this.name = 'UploadTimeoutError';
  }
}

export class UploadQuarantinedError extends Error {
  constructor() {
    super('File failed security scan and was quarantined');
    this.name = 'UploadQuarantinedError';
  }
}

export class UploadPutError extends Error {
  constructor(public readonly status: number) {
    super(`Storage PUT failed with status ${status}`);
    this.name = 'UploadPutError';
  }
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

/** 10 MB — files above this threshold bypass the backend and go direct to MinIO */
export const DIRECT_UPLOAD_THRESHOLD_BYTES = 10 * 1024 * 1024;

export function shouldUseDirect(file: File, kind: UploadKind): boolean {
  if (kind === 'video' || kind === 'audio') return true;
  return file.size > DIRECT_UPLOAD_THRESHOLD_BYTES;
}

// ---------------------------------------------------------------------------
// Internal: init
// ---------------------------------------------------------------------------

interface InitUploadResponse {
  upload_id: string;
  upload_url: string;
  object_key: string;
  expires_at: string;
  max_size_bytes: number;
}

async function initUpload(
  kind: UploadKind,
  scope: UploadScope,
  file: File,
): Promise<InitUploadResponse> {
  const resp = await api.post<InitUploadResponse>('/uploads/init', {
    kind,
    scope,
    mime_type: file.type,
    size_bytes: file.size,
  });
  return resp.data;
}

// ---------------------------------------------------------------------------
// Internal: PUT to MinIO (no Authorization header)
// ---------------------------------------------------------------------------

export function putToStorage(
  url: string,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', url);

    // Content-Type must match what was declared at /init (MinIO verifies the signature)
    xhr.setRequestHeader('Content-Type', file.type);
    // Do NOT set Authorization — presigned URL already embeds credentials

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress?.(100);
        resolve();
        return;
      }
      reject(new UploadPutError(xhr.status));
    };

    xhr.onerror = () => reject(new Error('Network error during storage PUT'));
    xhr.ontimeout = () => reject(new Error('Storage PUT timed out'));

    xhr.send(file);
  });
}

// ---------------------------------------------------------------------------
// Internal: complete
// ---------------------------------------------------------------------------

async function completeUpload(uploadId: string, sizeBytes: number): Promise<void> {
  const maxRetries = 3;
  let delay = 500;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      await api.post('/uploads/complete', {
        upload_id: uploadId,
        size_bytes: sizeBytes,
      });
      return;
    } catch (err) {
      // Do not retry 4xx errors (client-side problem)
      if (err && typeof err === 'object' && 'status' in err) {
        const status = (err as { status: number }).status;
        if (status >= 400 && status < 500) throw err;
      }
      if (attempt === maxRetries) throw err;
      await new Promise((r) => setTimeout(r, delay));
      delay = Math.min(delay * 2, 4000);
    }
  }
}

// ---------------------------------------------------------------------------
// Internal: poll until terminal state
// ---------------------------------------------------------------------------

interface StatusResponse {
  upload_id: string;
  state: string;
  target_id: string | null;
  target_kind: string | null;
  error_message: string | null;
}

const TERMINAL_STATES = new Set(['available', 'failed', 'quarantined']);
const POLL_INTERVAL_MS = 2000;
const POLL_MAX_INTERVAL_MS = 8000;
const POLL_TIMEOUT_MS = 5 * 60 * 1000;

async function pollUntilDone(
  uploadId: string,
  onStateChange?: (state: UploadState) => void,
): Promise<DirectUploadResult> {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  let interval = POLL_INTERVAL_MS;
  let firstPoll = true;

  while (Date.now() < deadline) {
    if (firstPoll) {
      onStateChange?.('processing');
      firstPoll = false;
    }

    await new Promise((r) => setTimeout(r, interval));
    interval = Math.min(interval * 1.5, POLL_MAX_INTERVAL_MS);

    const resp = await api.get<StatusResponse>(`/uploads/${uploadId}/status`);
    const { state, target_id, target_kind } = resp.data;

    if (TERMINAL_STATES.has(state)) {
      const result: DirectUploadResult = {
        upload_id: uploadId,
        target_id,
        target_kind,
        state: state as UploadState,
      };

      if (state === 'quarantined') throw new UploadQuarantinedError();
      if (state === 'failed') {
        throw new Error(resp.data.error_message ?? 'Upload processing failed');
      }

      return result;
    }
  }

  throw new UploadTimeoutError();
}

// ---------------------------------------------------------------------------
// Public: orchestrate full upload flow
// ---------------------------------------------------------------------------

export async function directUpload({
  kind,
  scope,
  file,
  onProgress,
  onStateChange,
}: DirectUploadOptions): Promise<DirectUploadResult> {
  onStateChange?.('preparing');

  const { upload_id, upload_url } = await initUpload(kind, scope, file);

  if (import.meta.env.DEV) {
    console.debug('[directUpload] upload_id=%s key obtained', upload_id);
    // upload_url intentionally not logged even in dev
  }

  onStateChange?.('uploading');
  await putToStorage(upload_url, file, onProgress);

  onStateChange?.('processing');
  await completeUpload(upload_id, file.size);

  const result = await pollUntilDone(upload_id, onStateChange);
  onStateChange?.(result.state);
  return result;
}
