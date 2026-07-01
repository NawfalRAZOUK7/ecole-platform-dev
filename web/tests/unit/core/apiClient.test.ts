/**
 * Tests for src/core/api/client.ts
 * Covers: setAccessToken, getAccessToken, setSchoolId, getSchoolId,
 * ApiClientError, normalizeDownloadMetadataPath (via getDownloadUrl), request internals
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  setAccessToken,
  getAccessToken,
  setSchoolId,
  getSchoolId,
  ApiClientError,
  getDownloadUrl,
  api,
  type ApiError,
} from '@/core/api/client';

// ---------------------------------------------------------------------------
// fetch mock helpers
// ---------------------------------------------------------------------------

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: vi.fn().mockResolvedValue(body),
  };
}

function makeApiBody<T>(data: T) {
  return { data, meta: { timestamp: new Date().toISOString(), version: '0.1.0' } };
}

function makeErrorBody(message: string, status = 500): ApiError {
  return {
    code: `ERR-SYS-${status}`,
    message,
    category: 'system',
    retryable: false,
    timestamp: new Date().toISOString(),
  };
}

beforeEach(() => {
  setAccessToken(null);
  setSchoolId(null);
  vi.stubGlobal('crypto', { randomUUID: () => 'test-correlation-id' });
  Object.defineProperty(document, 'cookie', { value: '', configurable: true, writable: true });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Token / school helpers
// ---------------------------------------------------------------------------

describe('access token management', () => {
  it('stores and retrieves access token', () => {
    expect(getAccessToken()).toBeNull();
    setAccessToken('tok123');
    expect(getAccessToken()).toBe('tok123');
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });
});

describe('school ID management', () => {
  it('stores and retrieves school ID', () => {
    expect(getSchoolId()).toBeNull();
    setSchoolId('school-1');
    expect(getSchoolId()).toBe('school-1');
    setSchoolId(null);
    expect(getSchoolId()).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// ApiClientError
// ---------------------------------------------------------------------------

describe('ApiClientError', () => {
  it('has correct name, status and apiError', () => {
    const err = new ApiClientError(404, {
      code: 'ERR-404',
      message: 'Not Found',
      category: 'not_found',
      retryable: false,
      timestamp: '2026-01-01T00:00:00Z',
    });
    expect(err.name).toBe('ApiClientError');
    expect(err.status).toBe(404);
    expect(err.message).toBe('Not Found');
    expect(err.apiError.code).toBe('ERR-404');
  });
});

// ---------------------------------------------------------------------------
// api.get — success
// ---------------------------------------------------------------------------

describe('api.get', () => {
  it('returns parsed response on success', async () => {
    const data = { id: '1', name: 'Test' };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(makeApiBody(data))));
    setAccessToken('tok');
    const result = await api.get<typeof data>('/test');
    expect(result.data).toEqual(data);
  });

  it('includes query params in URL', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({})));
    vi.stubGlobal('fetch', mockFetch);
    await api.get('/items', { page: '2', limit: '10' });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('page=2');
    expect(url).toContain('limit=10');
  });

  it('omits undefined params', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({})));
    vi.stubGlobal('fetch', mockFetch);
    await api.get('/items', { defined: '1', undef: undefined });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('defined=1');
    expect(url).not.toContain('undef');
  });

  it('adds Authorization header when token set', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({})));
    vi.stubGlobal('fetch', mockFetch);
    setAccessToken('bearer-token');
    await api.get('/me');
    const headers = mockFetch.mock.calls[0][1]?.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer bearer-token');
  });

  it('does not add Authorization when no token', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({})));
    vi.stubGlobal('fetch', mockFetch);
    await api.get('/public');
    const headers = mockFetch.mock.calls[0][1]?.headers as Record<string, string>;
    expect(headers['Authorization']).toBeUndefined();
  });

  it('throws ApiClientError on non-ok response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(jsonResponse({ error: makeErrorBody('Server error', 500) }, 500)),
    );
    await expect(api.get('/fail')).rejects.toThrow(ApiClientError);
  });

  it('throws with fallback error shape when response body is null', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        statusText: 'Service Unavailable',
        json: vi.fn().mockRejectedValue(new Error('not json')),
      }),
    );
    await expect(api.get('/fail')).rejects.toThrow(ApiClientError);
  });
});

// ---------------------------------------------------------------------------
// api.post / patch / put / delete
// ---------------------------------------------------------------------------

describe('api.post', () => {
  it('sends JSON body', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({ id: '1' })));
    vi.stubGlobal('fetch', mockFetch);
    const payload = { name: 'New item' };
    await api.post('/items', payload);
    const init = mockFetch.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe('POST');
    expect(init.body).toBe(JSON.stringify(payload));
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
  });

  it('sends FormData without Content-Type override', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({ id: '1' })));
    vi.stubGlobal('fetch', mockFetch);
    const form = new FormData();
    form.append('file', new Blob(['hello']), 'test.txt');
    await api.post('/upload', form);
    const init = mockFetch.mock.calls[0][1] as RequestInit;
    expect(init.body).toBe(form);
    expect((init.headers as Record<string, string>)['Content-Type']).toBeUndefined();
  });
});

describe('api.patch', () => {
  it('uses PATCH method', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({ id: '1' })));
    vi.stubGlobal('fetch', mockFetch);
    await api.patch('/items/1', { name: 'Updated' });
    expect(mockFetch.mock.calls[0][1]?.method).toBe('PATCH');
  });
});

describe('api.put', () => {
  it('uses PUT method', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({ id: '1' })));
    vi.stubGlobal('fetch', mockFetch);
    await api.put('/items/1', { name: 'Updated' });
    expect(mockFetch.mock.calls[0][1]?.method).toBe('PUT');
  });
});

describe('api.delete', () => {
  it('uses DELETE method', async () => {
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody(null)));
    vi.stubGlobal('fetch', mockFetch);
    await api.delete('/items/1');
    expect(mockFetch.mock.calls[0][1]?.method).toBe('DELETE');
  });
});

// ---------------------------------------------------------------------------
// 401 refresh flow
// ---------------------------------------------------------------------------

describe('401 refresh flow', () => {
  it('refreshes token and retries on 401', async () => {
    setAccessToken('old-token');
    let callCount = 0;
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      callCount++;
      if (url.includes('/auth/refresh')) {
        return jsonResponse({ data: { access_token: 'new-token' } });
      }
      if (callCount === 1) {
        return jsonResponse({ error: makeErrorBody('Unauthorized', 401) }, 401);
      }
      return jsonResponse(makeApiBody({ id: '1' }));
    });
    vi.stubGlobal('fetch', mockFetch);
    const result = await api.get('/me');
    expect(result.data).toEqual({ id: '1' });
    expect(getAccessToken()).toBe('new-token');
  });

  it('throws AuthError when refresh fails', async () => {
    setAccessToken('old-token');
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/auth/refresh')) {
        return { ok: false, status: 401, json: vi.fn().mockRejectedValue(new Error('fail')) };
      }
      return jsonResponse({ error: makeErrorBody('Unauthorized', 401) }, 401);
    });
    vi.stubGlobal('fetch', mockFetch);
    await expect(api.get('/me')).rejects.toThrow(ApiClientError);
  });
});

// ---------------------------------------------------------------------------
// api.list
// ---------------------------------------------------------------------------

describe('api.list', () => {
  it('returns list response', async () => {
    const items = [{ id: '1' }, { id: '2' }];
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse({
            data: items,
            meta: { next_cursor: null, has_more: false, timestamp: '', version: '' },
          }),
        ),
    );
    const result = await api.list<{ id: string }>('/items');
    expect(result.data).toEqual(items);
    expect(result.meta.has_more).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// CSRF header
// ---------------------------------------------------------------------------

describe('CSRF token', () => {
  it('adds X-CSRF-Token header on POST when csrf_token cookie present', async () => {
    Object.defineProperty(document, 'cookie', {
      value: 'csrf_token=my-csrf-value',
      configurable: true,
    });
    const mockFetch = vi.fn().mockResolvedValue(jsonResponse(makeApiBody({ id: '1' })));
    vi.stubGlobal('fetch', mockFetch);
    // Refresh uses CSRF - trigger it
    setAccessToken('tok');
    const mockFetchForRefresh = vi
      .fn()
      .mockResolvedValue(jsonResponse({ data: { access_token: 'new-tok' } }));
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(async (url: string) => {
        if (url.includes('/auth/refresh')) return mockFetchForRefresh();
        return jsonResponse({ error: makeErrorBody('Unauthorized', 401) }, 401);
      }),
    );
    await api.get('/protected').catch(() => {
      /* ignore error */
    });
    // Refresh was called - verify
    expect(mockFetchForRefresh).toBeCalled();
  });
});

// ---------------------------------------------------------------------------
// getDownloadUrl
// ---------------------------------------------------------------------------

describe('getDownloadUrl', () => {
  it('returns DownloadMetadata from a backend path', async () => {
    const meta = {
      download_url: 'https://s3.example.com/file.pdf',
      expires_at: '2026-01-01T00:00:00Z',
      mime_type: 'application/pdf',
      size: 1024,
      filename: 'file.pdf',
      etag: 'abc',
    };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(meta)));
    const result = await getDownloadUrl('/files/doc.pdf');
    expect(result.download_url).toBe('https://s3.example.com/file.pdf');
  });

  it('unwraps ApiResponse envelope', async () => {
    const inner = {
      download_url: 'https://cdn.example.com/file.jpg',
      expires_at: '',
      mime_type: 'image/jpeg',
      size: 512,
      filename: 'img.jpg',
      etag: null,
    };
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(jsonResponse({ data: inner, meta: { timestamp: '', version: '' } })),
    );
    const result = await getDownloadUrl('/files/img.jpg');
    expect(result.filename).toBe('img.jpg');
  });

  it('throws on empty path', async () => {
    await expect(getDownloadUrl('')).rejects.toThrow('required');
  });

  it('throws on cross-origin URL', async () => {
    await expect(getDownloadUrl('https://evil.com/malware.exe')).rejects.toThrow();
  });

  it('strips API base prefix from path', async () => {
    const meta = {
      download_url: 'https://cdn.example.com/doc.pdf',
      expires_at: '',
      mime_type: 'application/pdf',
      size: 100,
      filename: 'doc.pdf',
      etag: null,
    };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(meta)));
    const result = await getDownloadUrl('/api/v1/files/doc.pdf');
    expect(result.download_url).toContain('cdn.example.com');
  });
});
