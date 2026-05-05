import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  DIRECT_UPLOAD_THRESHOLD_BYTES,
  directUpload,
  putToStorage,
  shouldUseDirect,
  UploadPutError,
  UploadQuarantinedError,
} from '@/services/uploads/directUpload';
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
    upload: { onprogress: ((e: ProgressEvent) => void) | null } = { onprogress: null };
    onload: (() => void) | null = null;
    onerror: (() => void) | null = null;
    ontimeout: (() => void) | null = null;
    readonly headers: Record<string, string> = {};

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
        this.onerror?.();
        return;
      }
      const total = 100;
      for (const loaded of progressSteps) {
        this.upload.onprogress?.({
          lengthComputable: true,
          loaded,
          total,
        } as ProgressEvent);
      }
      this.onload?.();
    }
  }

  return { MockXHR, getInstance: () => lastInstance };
}

/** MSW response stubs for the three Phase-8 backend endpoints */
function uploadHandlers(
  opts: {
    uploadId?: string;
    uploadUrl?: string;
    state?: string;
    errorMessage?: string | null;
  } = {},
) {
  const {
    uploadId = 'uid-test-1',
    uploadUrl = 'https://minio.example.test/bucket/object?X-Amz-Signature=sig',
    state = 'available',
    errorMessage = null,
  } = opts;

  return [
    http.post('/api/v1/uploads/init', () =>
      apiResponse({
        upload_id: uploadId,
        upload_url: uploadUrl,
        object_key: 'schools/s1/content/object',
        expires_at: '2026-12-31T23:59:59Z',
        max_size_bytes: 524_288_000,
      }),
    ),
    http.post('/api/v1/uploads/complete', () => apiResponse({})),
    http.get(`/api/v1/uploads/${uploadId}/status`, () =>
      apiResponse({
        upload_id: uploadId,
        state,
        target_id: state === 'available' ? 'asset-abc' : null,
        target_kind: state === 'available' ? 'content_asset' : null,
        error_message: errorMessage,
      }),
    ),
  ];
}

// ---------------------------------------------------------------------------
// shouldUseDirect
// ---------------------------------------------------------------------------

describe('shouldUseDirect', () => {
  it('returns true for video regardless of size', () => {
    const tiny = makeFile(1, 'clip.mp4', 'video/mp4');
    expect(shouldUseDirect(tiny, 'video')).toBe(true);
  });

  it('returns true for audio regardless of size', () => {
    const tiny = makeFile(1, 'track.mp3', 'audio/mpeg');
    expect(shouldUseDirect(tiny, 'audio')).toBe(true);
  });

  it('returns false for small non-video/audio file', () => {
    const small = makeFile(5 * 1024 * 1024, 'doc.pdf', 'application/pdf');
    expect(shouldUseDirect(small, 'content_asset')).toBe(false);
  });

  it('returns false when size equals the threshold exactly', () => {
    const exact = makeFile(DIRECT_UPLOAD_THRESHOLD_BYTES, 'doc.pdf', 'application/pdf');
    expect(shouldUseDirect(exact, 'submission_file')).toBe(false);
  });

  it('returns true when size exceeds the threshold', () => {
    const large = makeFile(DIRECT_UPLOAD_THRESHOLD_BYTES + 1, 'report.pdf', 'application/pdf');
    expect(shouldUseDirect(large, 'submission_file')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// putToStorage
// ---------------------------------------------------------------------------

describe('putToStorage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('calls onProgress with intermediate and final values', async () => {
    const { MockXHR } = makeXhrClass({ progressSteps: [25, 75, 100] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(1024, 'test.pdf', 'application/pdf');
    const progress: number[] = [];

    await putToStorage('https://minio.example.test/key', file, (p: number) => progress.push(p));

    expect(progress).toContain(25);
    expect(progress).toContain(75);
    expect(progress).toContain(100);
  });

  it('resolves on 2xx status', async () => {
    const { MockXHR } = makeXhrClass({ status: 200 });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(512, 'test.bin');
    await expect(putToStorage('https://minio.example.test/key', file)).resolves.toBeUndefined();
  });

  it('rejects with UploadPutError on non-2xx status', async () => {
    const { MockXHR } = makeXhrClass({ status: 403, progressSteps: [] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(512, 'test.bin');
    await expect(putToStorage('https://minio.example.test/key', file)).rejects.toBeInstanceOf(
      UploadPutError,
    );
  });

  it('rejects on network error', async () => {
    const { MockXHR } = makeXhrClass({ fireError: true, progressSteps: [] });
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(512, 'test.bin');
    await expect(putToStorage('https://minio.example.test/key', file)).rejects.toThrow(
      /network error/i,
    );
  });

  it('does NOT set an Authorization header on the PUT request', async () => {
    const { MockXHR, getInstance } = makeXhrClass();
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(512, 'test.bin');
    await putToStorage('https://minio.example.test/key', file);

    const instance = getInstance();
    expect(instance).not.toBeNull();
    expect(Object.keys(instance!.headers)).not.toContain('Authorization');
  });
});

// ---------------------------------------------------------------------------
// directUpload (integration)
// ---------------------------------------------------------------------------

describe('directUpload', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Provide a succeeding XHR mock so putToStorage never touches a real network
    const { MockXHR } = makeXhrClass({ status: 200 });
    vi.stubGlobal('XMLHttpRequest', MockXHR);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('happy path: progresses through all states and returns available', async () => {
    server.use(...uploadHandlers({ state: 'available' }));

    const file = makeFile(20 * 1024 * 1024, 'lecture.mp4', 'video/mp4');
    const states: string[] = [];

    const promise = directUpload({
      kind: 'video',
      scope: { school_id: 'school-1', content_item_id: 'ci-1' },
      file,
      onStateChange: (s: string) => states.push(s),
    });

    // Advance past the 2-second poll interval; advanceTimersByTimeAsync
    // flushes microtasks between each timer tick so fetch responses land first.
    await vi.advanceTimersByTimeAsync(3000);

    const result = await promise;

    expect(result.state).toBe('available');
    expect(result.target_id).toBe('asset-abc');
    // directUpload emits 'processing' before completeUpload; pollUntilDone
    // emits it again on first poll — two 'processing' entries are correct.
    expect(states).toEqual(['preparing', 'uploading', 'processing', 'processing', 'available']);
  });

  it('infected file: status quarantined → throws UploadQuarantinedError', async () => {
    server.use(...uploadHandlers({ state: 'quarantined' }));

    const file = makeFile(20 * 1024 * 1024, 'virus.mp4', 'video/mp4');

    // Attach .catch() immediately to prevent an unhandled-rejection warning
    // while fake timers are running. We collect the thrown value and assert below.
    let thrownError: unknown = null;
    const settled = directUpload({
      kind: 'video',
      scope: { school_id: 'school-1' },
      file,
    }).catch((e: unknown) => {
      thrownError = e;
    });

    await vi.advanceTimersByTimeAsync(3000);
    await settled;

    expect(thrownError).toBeInstanceOf(UploadQuarantinedError);
  });

  it('init failure (422): throws without calling XHR PUT', async () => {
    server.use(
      http.post('/api/v1/uploads/init', () =>
        HttpResponse.json(
          {
            error: {
              code: 'ERR-VAL-422',
              message: 'Unsupported mime type',
              category: 'validation',
              retryable: false,
              timestamp: new Date().toISOString(),
            },
          },
          { status: 422 },
        ),
      ),
    );

    // Spy on XHR so we can assert send() is never called
    const sendSpy = vi.fn();
    const { MockXHR } = makeXhrClass();
    MockXHR.prototype.send = sendSpy;
    vi.stubGlobal('XMLHttpRequest', MockXHR);

    const file = makeFile(512, 'bad.exe', 'application/x-msdownload');

    await expect(
      directUpload({
        kind: 'submission_file',
        scope: { school_id: 'school-1', submission_id: 'sub-1' },
        file,
      }),
    ).rejects.toThrow();

    expect(sendSpy).not.toHaveBeenCalled();
  });
});
