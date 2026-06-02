/**
 * Tests for the upload-related methods of
 * src/features/lms/submissions/api/submissions.api.ts that need a full XHR
 * mock (Authorization header injection + onload/onerror/onprogress).
 *
 * Covers:
 *   - uploadSubmissionFile, legacy XHR path (small files < 5MB)
 *     - happy path → resolves
 *     - file_type_hint forwarded in form data
 *     - onProgress invoked with rounded percentage
 *     - non-2xx → rejects with "Upload failed"
 *     - network error → rejects with "Upload failed"
 *     - Authorization: Bearer <token> header injected when getAccessToken()
 *       returns a token
 *   - uploadSubmissionFile, direct upload path (large files)
 *     - throws when there is no school context
 *   - uploadFiles: batches multiple uploadSubmissionFile calls
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { submissionsService } from '@/features/lms/submissions/api/submissions.api';
import { setAccessToken, setSchoolId } from '@/core/api/client';

// ---------------------------------------------------------------------------
// FakeXHR that records the request and lets the test drive load/error events.
// Mirrors the production XHR call sequence: open → setRequestHeader →
// upload.onprogress → send → load|error.
// ---------------------------------------------------------------------------
class FakeXHR {
  public readonly headers = new Map<string, string>();
  public method = '';
  public url = '';
  public body: BodyInit | null = null;
  public status = 0;
  public statusText = '';
  public upload: { onprogress?: (event: ProgressEvent) => void } = {};
  public onload: (() => void) | null = null;
  public onerror: (() => void) | null = null;

  open(method: string, url: string) {
    this.method = method;
    this.url = url;
  }
  setRequestHeader(name: string, value: string) {
    this.headers.set(name, value);
  }
  send(body?: BodyInit | null) {
    this.body = body ?? null;
    // Tests drive the load/error events explicitly via .triggerLoad / .triggerError.
  }
  triggerLoad(status: number) {
    this.status = status;
    this.statusText = status === 200 ? 'OK' : 'Error';
    this.onload?.();
  }
  triggerProgress(loaded: number, total: number) {
    this.upload.onprogress?.(
      new ProgressEvent('progress', { lengthComputable: true, loaded, total }),
    );
  }
  triggerError() {
    this.onerror?.();
  }
}

describe('submissionsService.uploadSubmissionFile — legacy XHR path', () => {
  let originalXhr: typeof XMLHttpRequest;
  let xhr: FakeXHR;

  beforeEach(() => {
    originalXhr = globalThis.XMLHttpRequest;
    xhr = new FakeXHR();
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: function MockXhr() {
        return xhr;
      },
    });
    setAccessToken(null);
    setSchoolId(null);
  });

  afterEach(() => {
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: originalXhr,
    });
    setAccessToken(null);
    setSchoolId(null);
  });

  const smallFile = (content = 'hello'): File =>
    new File([content], 'note.txt', { type: 'text/plain' });

  it('POSTs the file via multipart and resolves on 200', async () => {
    const promise = submissionsService.uploadSubmissionFile('sub-1', smallFile());

    expect(xhr.method).toBe('POST');
    expect(xhr.url).toBe('/api/v1/submissions/sub-1/files');
    expect(xhr.body).toBeInstanceOf(FormData);

    xhr.triggerLoad(200);
    await expect(promise).resolves.toBeUndefined();
  });

  it('appends file_type_hint to the form data when provided', async () => {
    const file = smallFile();
    const promise = submissionsService.uploadSubmissionFile('sub-1', file, 'audio');

    expect(xhr.body).toBeInstanceOf(FormData);
    const fd = xhr.body as FormData;
    expect(fd.get('file_type_hint')).toBe('audio');

    xhr.triggerLoad(201);
    await expect(promise).resolves.toBeUndefined();
  });

  it('invokes onProgress with a rounded percentage', async () => {
    const onProgress = vi.fn();
    const promise = submissionsService.uploadSubmissionFile(
      'sub-1',
      smallFile(),
      undefined,
      onProgress,
    );

    xhr.triggerProgress(50, 100);
    xhr.triggerProgress(75, 100);
    xhr.triggerLoad(200);

    await expect(promise).resolves.toBeUndefined();
    expect(onProgress).toHaveBeenCalledWith(50);
    expect(onProgress).toHaveBeenCalledWith(75);
  });

  it('rejects with "Upload failed" on a non-2xx response', async () => {
    const promise = submissionsService.uploadSubmissionFile('sub-1', smallFile());
    xhr.triggerLoad(500);
    await expect(promise).rejects.toThrow('Upload failed');
  });

  it('rejects with "Upload failed" on a network error', async () => {
    const promise = submissionsService.uploadSubmissionFile('sub-1', smallFile());
    xhr.triggerError();
    await expect(promise).rejects.toThrow('Upload failed');
  });

  it('injects Authorization: Bearer <token> when an access token is set', async () => {
    setAccessToken('my-jwt');
    const promise = submissionsService.uploadSubmissionFile('sub-1', smallFile());
    expect(xhr.headers.get('Authorization')).toBe('Bearer my-jwt');
    xhr.triggerLoad(200);
    await expect(promise).resolves.toBeUndefined();
  });

  it('does NOT set Authorization when no token is present', async () => {
    setAccessToken(null);
    const promise = submissionsService.uploadSubmissionFile('sub-1', smallFile());
    expect(xhr.headers.has('Authorization')).toBe(false);
    xhr.triggerLoad(200);
    await expect(promise).resolves.toBeUndefined();
  });
});

describe('submissionsService.uploadSubmissionFile — direct upload path', () => {
  beforeEach(() => {
    setAccessToken(null);
    setSchoolId(null);
  });
  afterEach(() => {
    setAccessToken(null);
    setSchoolId(null);
  });

  it('throws when the file is large but no school context is available', async () => {
    // 6 MB triggers the direct upload branch (threshold is 5 MB).
    const big = new File([new Uint8Array(6 * 1024 * 1024)], 'big.bin', {
      type: 'application/octet-stream',
    });

    await expect(submissionsService.uploadSubmissionFile('sub-1', big)).rejects.toThrow(
      'No school context available',
    );
  });
});

describe('submissionsService.uploadFiles', () => {
  let originalXhr: typeof XMLHttpRequest;
  // Track every XHR created so we can drive each individually.
  const xhrs: FakeXHR[] = [];

  beforeEach(() => {
    originalXhr = globalThis.XMLHttpRequest;
    xhrs.length = 0;
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: function MockXhr() {
        const x = new FakeXHR();
        xhrs.push(x);
        return x;
      },
    });
    setAccessToken(null);
    setSchoolId(null);
  });

  afterEach(() => {
    Object.defineProperty(globalThis, 'XMLHttpRequest', {
      configurable: true,
      writable: true,
      value: originalXhr,
    });
    setAccessToken(null);
    setSchoolId(null);
  });

  it('uploads every file in the array and resolves when all succeed', async () => {
    const files = [
      new File(['a'], 'a.txt', { type: 'text/plain' }),
      new File(['b'], 'b.txt', { type: 'text/plain' }),
      new File(['c'], 'c.txt', { type: 'text/plain' }),
    ];
    const promise = submissionsService.uploadFiles('sub-1', files);

    // Each file triggers one XHR concurrently — drive them all to load.
    expect(xhrs).toHaveLength(3);
    xhrs.forEach((x) => x.triggerLoad(200));

    const results = await promise;
    expect(results).toHaveLength(3);
    xhrs.forEach((x) => expect(x.url).toBe('/api/v1/submissions/sub-1/files'));
  });

  it('rejects when any file upload fails', async () => {
    const files = [
      new File(['a'], 'a.txt', { type: 'text/plain' }),
      new File(['b'], 'b.txt', { type: 'text/plain' }),
    ];
    const promise = submissionsService.uploadFiles('sub-1', files);

    expect(xhrs).toHaveLength(2);
    // First succeeds, second fails.
    xhrs[0].triggerLoad(200);
    xhrs[1].triggerLoad(500);

    await expect(promise).rejects.toThrow('Upload failed');
  });
});
