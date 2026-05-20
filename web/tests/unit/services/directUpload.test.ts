import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { directUpload, shouldUseDirect } from '@/shared/lib/upload';
import { apiResponse } from '../../utils/mocks';
import { server } from '../../utils/mocks';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Create a File whose .size is overridden without allocating real bytes */
function makeFile(size: number, name = 'test.bin', type = 'application/octet-stream'): File {
  const file = new File([], name, { type });
  Object.defineProperty(file, 'size', { value: size, configurable: true });
  return file;
}

interface XhrMockOpts {
  /** HTTP status to report in onload */
  status?: number;
  /** Fire onerror instead of onload */
  fireError?: boolean;
  /** Loaded bytes to report via upload.onprogress before onload */
  progressSteps?: number[];
}

/**
 * Returns a minimal XMLHttpRequest replacement class and a reference to the
 * most-recently created instance so tests can inspect captured headers.
 */
function makeXhrClass(opts: XhrMockOpts = {}) {
  const { status = 200, fireError = false, progressSteps = [50, 100] } = opts;
  let lastInstance: InstanceType<ReturnType<typeof makeXhrClass>['MockXHR']> | null = null;

  class MockXHR {
    status = status;
    readonly headers: Record<string, string> = {};
    private _uploadListeners: Record<string, Array<(e: ProgressEvent) => void>> = {};
    private _listeners: Record<string, Array<() => void>> = {};

    upload = {
      addEventListener: (event: string, handler: (e: ProgressEvent) => void) => {
        if (!lastInstance) return;
        const listeners = lastInstance._uploadListeners;
        if (!listeners[event]) listeners[event] = [];
        listeners[event].push(handler);
      },
      removeEventListener: () => {},
      onprogress: null as ((e: ProgressEvent) => void) | null,
    };

    addEventListener(event: string, handler: () => void) {
      if (!this._listeners[event]) this._listeners[event] = [];
      this._listeners[event].push(handler);
    }

    removeEventListener() {}

    constructor() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      lastInstance = this as unknown as InstanceType<ReturnType<typeof makeXhrClass>['MockXHR']>;
    }

    open() {}

    setRequestHeader(name: string, value: string) {
      this.headers[name] = value;
    }

    send() {
      if (fireError) {
        for (const handler of this._listeners['error'] ?? []) {
          handler();
        }
        return;
      }
      const total = 100;
      for (const loaded of progressSteps) {
        const event = {
          lengthComputable: true,
          loaded,
          total,
        } as ProgressEvent;
        this.upload.onprogress?.(event);
        for (const handler of this._uploadListeners['progress'] ?? []) {
          handler(event);
        }
      }
      for (const handler of this._listeners['load'] ?? []) {
        handler();
      }
    }
  }

  return { MockXHR, getInstance: () => lastInstance };
}

/** MSW response stubs for the upload endpoints */
function uploadHandlers(
  opts: {
    uploadId?: string;
    uploadUrl?: string;
    confirmResult?: Record<string, unknown>;
    initStatus?: number;
    initError?: Record<string, unknown>;
  } = {},
) {
  const {
    uploadId = 'uid-test-1',
    uploadUrl = 'https://minio.example.test/bucket/object?X-Amz-Signature=sig',
    confirmResult = {
      id: 'asset-abc',
      url: 'https://cdn.example.test/asset-abc',
      etag: '"abc123"',
      size: 20971520,
      mime_type: 'video/mp4',
    },
    initStatus = 200,
    initError,
  } = opts;

  return [
    http.post('/api/v1/content/upload-url', () => {
      if (initError) {
        return HttpResponse.json(initError, { status: initStatus });
      }
      return apiResponse({
        upload_url: uploadUrl,
        id: uploadId,
        mime_type: 'video/mp4',
      });
    }),
    http.post('/api/v1/content/upload-confirm', () => apiResponse(confirmResult)),
  ];
}

// ---------------------------------------------------------------------------
// shouldUseDirect
// ---------------------------------------------------------------------------

describe('shouldUseDirect', () => {
  it('returns true for content_asset regardless of size', () => {
    const tiny = makeFile(1, 'clip.mp4', 'video/mp4');
    expect(shouldUseDirect(tiny, 'content_asset')).toBe(true);
  });

  it('returns true for cms_asset regardless of size', () => {
    const tiny = makeFile(1, 'image.png', 'image/png');
    expect(shouldUseDirect(tiny, 'cms_asset')).toBe(true);
  });

  it('returns true for exercise_pdf regardless of size', () => {
    const tiny = makeFile(1, 'doc.pdf', 'application/pdf');
    expect(shouldUseDirect(tiny, 'exercise_pdf')).toBe(true);
  });

  it('returns false for small submission_file', () => {
    const small = makeFile(5 * 1024 * 1024, 'doc.pdf', 'application/pdf');
    expect(shouldUseDirect(small, 'submission_file')).toBe(false);
  });

  it('returns false when size equals the threshold exactly', () => {
    const exact = makeFile(5 * 1024 * 1024, 'doc.pdf', 'application/pdf');
    expect(shouldUseDirect(exact, 'submission_file')).toBe(false);
  });

  it('returns true when size exceeds the threshold', () => {
    const large = makeFile(5 * 1024 * 1024 + 1, 'report.pdf', 'application/pdf');
    expect(shouldUseDirect(large, 'submission_file')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// directUpload
// ---------------------------------------------------------------------------

describe('directUpload', () => {
  beforeEach(() => {
    // Provide a succeeding XHR mock so the PUT never touches real network
    const { MockXHR } = makeXhrClass({ status: 200 });
    vi.stubGlobal('XMLHttpRequest', MockXHR);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('happy path: returns result after upload and confirm', async () => {
    server.use(...uploadHandlers());

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');
    const states: string[] = [];

    const result = await directUpload({
      kind: 'content_asset',
      scope: { school_id: 'school-1', content_item_id: 'ci-1' },
      file,
      onStateChange: (s) => states.push(s),
    });

    expect(result.id).toBe('asset-abc');
    expect(result.url).toBe('https://cdn.example.test/asset-abc');
    expect(states).toEqual(['pending', 'uploading', 'processing', 'completed']);
  });

  it('calls onProgress during XHR upload', async () => {
    const { MockXHR } = makeXhrClass({ progressSteps: [25, 75, 100] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    server.use(...uploadHandlers());

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');
    const progress: number[] = [];

    await directUpload({
      kind: 'content_asset',
      scope: { school_id: 'school-1' },
      file,
      onProgress: (p) => progress.push(p),
    });

    expect(progress).toContain(25);
    expect(progress).toContain(75);
    expect(progress).toContain(100);
  });

  it('rejects when init returns non-2xx', async () => {
    server.use(
      ...uploadHandlers({
        initStatus: 422,
        initError: {
          error: {
            code: 'ERR-VAL-422',
            message: 'Unsupported mime type',
            category: 'validation',
            retryable: false,
            timestamp: new Date().toISOString(),
          },
        },
      }),
    );

    const file = makeFile(512, 'bad.exe', 'application/x-msdownload');

    await expect(
      directUpload({
        kind: 'submission_file',
        scope: { school_id: 'school-1', submission_id: 'sub-1' },
        file,
      }),
    ).rejects.toThrow();
  });

  it('rejects when XHR PUT fails', async () => {
    const { MockXHR } = makeXhrClass({ status: 403, progressSteps: [] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    server.use(...uploadHandlers());

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');

    await expect(
      directUpload({
        kind: 'content_asset',
        scope: { school_id: 'school-1' },
        file,
      }),
    ).rejects.toThrow('Upload failed');
  });

  it('rejects on XHR network error', async () => {
    const { MockXHR } = makeXhrClass({ fireError: true, progressSteps: [] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    server.use(...uploadHandlers());

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');

    await expect(
      directUpload({
        kind: 'content_asset',
        scope: { school_id: 'school-1' },
        file,
      }),
    ).rejects.toThrow('Upload failed');
  });

  it('does NOT set an Authorization header on the PUT request', async () => {
    const { MockXHR, getInstance } = makeXhrClass();
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    server.use(...uploadHandlers());

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');
    await directUpload({
      kind: 'content_asset',
      scope: { school_id: 'school-1' },
      file,
    });

    const instance = getInstance();
    expect(instance).not.toBeNull();
    expect(Object.keys(instance!.headers)).not.toContain('Authorization');
  });
});
