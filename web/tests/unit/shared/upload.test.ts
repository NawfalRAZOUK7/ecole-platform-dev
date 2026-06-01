/**
 * Tests for src/shared/lib/upload.ts
 * Covers: shouldUseDirect, directUpload success + error paths.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { shouldUseDirect, directUpload, type UploadKind } from '@/shared/lib/upload';

// ---------------------------------------------------------------------------
// shouldUseDirect
// ---------------------------------------------------------------------------

describe('shouldUseDirect', () => {
  it('returns true for content_asset kind regardless of size', () => {
    const file = new File(['small'], 'test.jpg', { type: 'image/jpeg' });
    expect(shouldUseDirect(file, 'content_asset')).toBe(true);
  });

  it('returns true for cms_asset kind', () => {
    const file = new File(['x'], 'doc.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'cms_asset')).toBe(true);
  });

  it('returns true for exercise_pdf kind', () => {
    const file = new File(['x'], 'exercise.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'exercise_pdf')).toBe(true);
  });

  it('returns false for submission_file under 5MB', () => {
    const file = new File(['small data'], 'sub.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'submission_file')).toBe(false);
  });

  it('returns false for document under 5MB', () => {
    const file = new File(['small'], 'doc.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'document')).toBe(false);
  });

  it('returns true for any file > 5MB', () => {
    const largeContent = 'a'.repeat(6 * 1024 * 1024);
    const file = new File([largeContent], 'large.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'submission_file')).toBe(true);
  });

  it('returns true for file exactly over 5MB threshold', () => {
    const content = 'b'.repeat(5 * 1024 * 1024 + 1);
    const file = new File([content], 'border.pdf', { type: 'application/pdf' });
    expect(shouldUseDirect(file, 'document')).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// directUpload — helpers
// ---------------------------------------------------------------------------

function createMockXhr() {
  const listeners: Record<string, ((...args: unknown[]) => void)[]> = {};
  const uploadListeners: Record<string, ((...args: unknown[]) => void)[]> = {};
  let sendResolver: (() => void) | null = null;
  const sendCalled = new Promise<void>((resolve) => {
    sendResolver = resolve;
  });

  const xhr = {
    open: vi.fn(),
    setRequestHeader: vi.fn(),
    send: vi.fn(() => {
      sendResolver?.();
    }),
    upload: {
      addEventListener: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
        uploadListeners[event] = uploadListeners[event] || [];
        uploadListeners[event].push(handler);
      }),
    },
    addEventListener: vi.fn((event: string, handler: (...args: unknown[]) => void) => {
      listeners[event] = listeners[event] || [];
      listeners[event].push(handler);
    }),
    status: 200,
    statusText: 'OK',
    _sendCalled: sendCalled,
    _triggerLoad: () => listeners['load']?.forEach((fn) => fn()),
    _triggerError: () => listeners['error']?.forEach((fn) => fn()),
    _triggerAbort: () => listeners['abort']?.forEach((fn) => fn()),
    _triggerProgress: (loaded: number, total: number) =>
      uploadListeners['progress']?.forEach((fn) => fn({ lengthComputable: true, loaded, total })),
  };
  return xhr;
}

// ---------------------------------------------------------------------------
// directUpload — tests
// ---------------------------------------------------------------------------

describe('directUpload', () => {
  let mockXhr: ReturnType<typeof createMockXhr>;

  beforeEach(() => {
    mockXhr = createMockXhr();
    vi.stubGlobal(
      'XMLHttpRequest',
      vi.fn().mockImplementation(() => mockXhr),
    );
    vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid' });
    Object.defineProperty(document, 'cookie', { value: '', configurable: true });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('calls all state change callbacks in order', async () => {
    const states: string[] = [];
    const stateChange = vi.fn((s: string) => states.push(s));
    const progressCb = vi.fn();

    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: vi.fn().mockResolvedValue({
            data: {
              upload_url: 'https://s3.example.com/upload',
              id: 'upload-1',
              mime_type: 'image/jpeg',
            },
            meta: { timestamp: '', version: '' },
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: vi.fn().mockResolvedValue({
            data: {
              id: 'result-1',
              url: 'https://cdn.example.com/file.jpg',
              etag: 'etag123',
              size: 1024,
              mime_type: 'image/jpeg',
            },
            meta: { timestamp: '', version: '' },
          }),
        }),
    );

    const file = new File(['test content'], 'test.jpg', { type: 'image/jpeg' });
    const uploadPromise = directUpload({
      kind: 'content_asset',
      scope: { school_id: 'school-1' },
      file,
      onStateChange: stateChange,
      onProgress: progressCb,
    });

    // Wait until XHR.send() is called (guarantees listeners are registered)
    await mockXhr._sendCalled;
    mockXhr._triggerProgress(50, 100);
    mockXhr._triggerLoad();

    const result = await uploadPromise;

    expect(states).toContain('pending');
    expect(states).toContain('uploading');
    expect(states).toContain('processing');
    expect(states).toContain('completed');
    expect(result.id).toBe('result-1');
    expect(result.url).toBe('https://cdn.example.com/file.jpg');
    expect(progressCb).toHaveBeenCalledWith(50);
  });

  it('throws when XHR fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({
          data: {
            upload_url: 'https://s3.example.com/upload',
            id: 'upload-1',
            mime_type: 'image/jpeg',
          },
          meta: { timestamp: '', version: '' },
        }),
      }),
    );

    mockXhr.status = 500;
    mockXhr.statusText = 'Server Error';

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const uploadPromise = directUpload({
      kind: 'submission_file',
      scope: { school_id: 'school-1', submission_id: 'sub-1' },
      file,
    });

    await mockXhr._sendCalled;
    mockXhr._triggerError();

    await expect(uploadPromise).rejects.toThrow('Upload failed');
  });

  it('throws when XHR is aborted', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({
          data: {
            upload_url: 'https://s3.example.com/upload',
            id: 'upload-1',
            mime_type: 'image/jpeg',
          },
          meta: { timestamp: '', version: '' },
        }),
      }),
    );

    const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
    const uploadPromise = directUpload({
      kind: 'cms_asset',
      scope: { school_id: 'school-1' },
      file,
    });

    await mockXhr._sendCalled;
    mockXhr._triggerAbort();

    await expect(uploadPromise).rejects.toThrow('Upload aborted');
  });

  it('throws when the backend upload URL request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({
          error: {
            code: 'ERR',
            message: 'Server error',
            category: 'system',
            retryable: false,
            timestamp: '',
          },
        }),
      }),
    );

    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' });
    await expect(
      directUpload({ kind: 'document', scope: { school_id: 'school-1' }, file }),
    ).rejects.toThrow();
  });

  it('works without progress or stateChange callbacks', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: vi.fn().mockResolvedValue({
            data: {
              upload_url: 'https://s3.example.com/upload',
              id: 'up-1',
              mime_type: 'application/pdf',
            },
            meta: { timestamp: '', version: '' },
          }),
        })
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: vi.fn().mockResolvedValue({
            data: {
              id: 'r1',
              url: 'https://cdn.example.com/doc.pdf',
              etag: 'abc',
              size: 512,
              mime_type: 'application/pdf',
            },
            meta: { timestamp: '', version: '' },
          }),
        }),
    );

    const file = new File(['content'], 'doc.pdf', { type: 'application/pdf' });
    const uploadPromise = directUpload({
      kind: 'exercise_pdf',
      scope: { school_id: 'school-1' },
      file,
    });

    await mockXhr._sendCalled;
    mockXhr._triggerLoad();

    const result = await uploadPromise;
    expect(result.id).toBe('r1');
  });
});
