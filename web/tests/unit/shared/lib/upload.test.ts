/**
 * Tests for src/shared/lib/upload.ts
 * Covers:
 *  - shouldUseDirect (size threshold + alwaysDirectKinds)
 *  - directUpload happy path (state transitions + progress events)
 *  - directUpload error paths (xhr error, xhr abort, non-2xx)
 */
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { server } from '../../../utils/mocks';

import {
  directUpload,
  shouldUseDirect,
  type DirectUploadOptions,
  type UploadKind,
  type UploadState,
} from '@/shared/lib/upload';

// NOTE: api.post<T>() returns ApiResponse<T> = { data: T, meta: ... }
// (cf. src/core/api/client.ts line 287). All MSW responses must wrap their
// payload in a `{ data: ... }` envelope.
const META = { timestamp: '2026-06-01T00:00:00Z', version: '1.0.0' };

// ---------------------------------------------------------------------------
// shouldUseDirect — pure helper, no XHR
// ---------------------------------------------------------------------------
describe('shared/lib/upload — shouldUseDirect', () => {
  const file = (size: number) =>
    new File([new Uint8Array(size)], 'sample', { type: 'application/octet-stream' });

  it('uses direct upload for files larger than the 5MB threshold', () => {
    expect(shouldUseDirect(file(6 * 1024 * 1024), 'submission_file')).toBe(true);
  });

  it('uses non-direct for small submission files', () => {
    expect(shouldUseDirect(file(1024), 'submission_file')).toBe(false);
  });

  it('always uses direct upload for content_asset regardless of size', () => {
    expect(shouldUseDirect(file(10), 'content_asset')).toBe(true);
  });

  it('always uses direct upload for cms_asset and exercise_pdf', () => {
    expect(shouldUseDirect(file(10), 'cms_asset')).toBe(true);
    expect(shouldUseDirect(file(10), 'exercise_pdf')).toBe(true);
  });

  it('does NOT use direct upload for small document uploads', () => {
    expect(shouldUseDirect(file(10), 'document')).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// directUpload — needs an XHR mock since jsdom XHR cannot reach MSW directly
// for the presigned PUT to "minio". We stub XMLHttpRequest entirely.
// ---------------------------------------------------------------------------
class FakeXHR {
  upload = {
    listeners: new Map<string, (event: ProgressEvent) => void>(),
    addEventListener(name: string, cb: (event: ProgressEvent) => void) {
      this.listeners.set(name, cb);
    },
  };
  listeners = new Map<string, (event?: Event) => void>();
  status = 0;
  statusText = '';
  responseURL = '';

  addEventListener(name: string, cb: (event?: Event) => void) {
    this.listeners.set(name, cb);
  }
  open(_method: string, url: string) {
    this.responseURL = url;
  }
  setRequestHeader(_k: string, _v: string) {
    // no-op
  }
  send(_body?: unknown) {
    // Default: simulate progress then success on next microtask.
    queueMicrotask(() => {
      const progress = this.upload.listeners.get('progress');
      if (progress) {
        progress(new ProgressEvent('progress', { lengthComputable: true, loaded: 50, total: 100 }));
        progress(
          new ProgressEvent('progress', { lengthComputable: true, loaded: 100, total: 100 }),
        );
      }
      this.status = 200;
      this.statusText = 'OK';
      this.listeners.get('load')?.();
    });
  }
  abort() {
    this.listeners.get('abort')?.();
  }
}

describe('shared/lib/upload — directUpload', () => {
  let originalXhr: typeof XMLHttpRequest;
  let xhrInstance: FakeXHR;

  beforeEach(() => {
    originalXhr = globalThis.XMLHttpRequest;
    xhrInstance = new FakeXHR();
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: function MockXhr() {
        return xhrInstance;
      },
    });
  });

  afterEach(() => {
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: originalXhr,
    });
  });

  function options(overrides?: Partial<DirectUploadOptions>): DirectUploadOptions {
    return {
      kind: 'submission_file' as UploadKind,
      scope: { school_id: 's1', submission_id: 'sub1' },
      file: new File(['hello'], 'note.txt', { type: 'text/plain' }),
      ...overrides,
    };
  }

  it('walks pending → uploading → processing → completed on success', async () => {
    server.use(
      http.post('/api/v1/content/upload-url', () =>
        HttpResponse.json({
          data: { upload_url: 'https://minio.example/upload', id: 'u1', mime_type: 'text/plain' },
          meta: META,
        }),
      ),
      http.post('/api/v1/content/upload-confirm', () =>
        HttpResponse.json({
          data: { id: 'u1', url: 'https://cdn/u1', etag: 'abc', size: 5, mime_type: 'text/plain' },
          meta: META,
        }),
      ),
    );

    const stateChanges: UploadState[] = [];
    const progresses: number[] = [];

    const result = await directUpload(
      options({
        onStateChange: (s) => stateChanges.push(s),
        onProgress: (p) => progresses.push(p),
      }),
    );

    expect(stateChanges).toEqual(['pending', 'uploading', 'processing', 'completed']);
    expect(progresses).toEqual([50, 100]);
    expect(result).toMatchObject({ id: 'u1', url: 'https://cdn/u1', etag: 'abc' });
    expect(xhrInstance.responseURL).toBe('https://minio.example/upload');
  });

  it('throws when the presigned upload returns a non-2xx', async () => {
    server.use(
      http.post('/api/v1/content/upload-url', () =>
        HttpResponse.json({
          data: { upload_url: 'https://minio.example/upload', id: 'u2', mime_type: 'text/plain' },
          meta: META,
        }),
      ),
    );

    // Override the XHR mock to return a 500 error
    xhrInstance.send = function () {
      queueMicrotask(() => {
        this.status = 500;
        this.statusText = 'Internal Server Error';
        this.listeners.get('load')?.();
      });
    };

    await expect(directUpload(options())).rejects.toThrow(/Upload failed/);
  });

  it('rejects when xhr error event fires', async () => {
    server.use(
      http.post('/api/v1/content/upload-url', () =>
        HttpResponse.json({
          data: { upload_url: 'https://minio.example/upload', id: 'u3', mime_type: 'text/plain' },
          meta: META,
        }),
      ),
    );

    xhrInstance.send = function () {
      queueMicrotask(() => {
        this.listeners.get('error')?.();
      });
    };

    await expect(directUpload(options())).rejects.toThrow('Upload failed');
  });

  it('rejects when xhr abort event fires', async () => {
    server.use(
      http.post('/api/v1/content/upload-url', () =>
        HttpResponse.json({
          data: { upload_url: 'https://minio.example/upload', id: 'u4', mime_type: 'text/plain' },
          meta: META,
        }),
      ),
    );

    xhrInstance.send = function () {
      queueMicrotask(() => {
        this.listeners.get('abort')?.();
      });
    };

    await expect(directUpload(options())).rejects.toThrow('Upload aborted');
  });

  it('does not invoke onProgress when callback is omitted', async () => {
    server.use(
      http.post('/api/v1/content/upload-url', () =>
        HttpResponse.json({
          data: { upload_url: 'https://minio.example/upload', id: 'u5', mime_type: 'text/plain' },
          meta: META,
        }),
      ),
      http.post('/api/v1/content/upload-confirm', () =>
        HttpResponse.json({
          data: { id: 'u5', url: 'https://cdn/u5', etag: 'e', size: 5, mime_type: 'text/plain' },
          meta: META,
        }),
      ),
    );

    const onStateChange = vi.fn();
    await directUpload(options({ onStateChange }));
    expect(onStateChange).toHaveBeenCalledWith('completed');
  });
});
