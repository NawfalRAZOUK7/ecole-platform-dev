/**
 * Tests for src/core/api/oauth.ts
 * Covers getOAuthUrl and exchangeOAuthCode functions.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { getOAuthUrl, exchangeOAuthCode } from '@/core/api/oauth';

function mockFetchOk(data: unknown) {
  return vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: vi.fn().mockResolvedValue({ data, meta: {} }),
  });
}

function mockFetchError(status: number, message: string) {
  return vi.fn().mockResolvedValue({
    ok: false,
    status,
    json: vi.fn().mockResolvedValue({ error: { message } }),
  });
}

beforeEach(() => {
  vi.stubGlobal('crypto', { randomUUID: () => 'test-uuid' });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('getOAuthUrl', () => {
  it('returns auth_url and state on success', async () => {
    const oauthResponse = {
      auth_url: 'https://accounts.google.com/oauth/authorize?...',
      state: 'random-state',
    };
    vi.stubGlobal('fetch', mockFetchOk(oauthResponse));

    const result = await getOAuthUrl('google', 'https://app.example.com/callback');

    expect(result.auth_url).toBe(oauthResponse.auth_url);
    expect(result.state).toBe(oauthResponse.state);
  });

  it('calls the correct endpoint with provider and redirect_uri', async () => {
    const mockFetch = mockFetchOk({ auth_url: 'https://login.ms/...', state: 'state-ms' });
    vi.stubGlobal('fetch', mockFetch);

    await getOAuthUrl('microsoft', 'https://app.example.com/oauth/callback');

    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain('/auth/oauth/microsoft/url');
    expect(url).toContain('redirect_uri=');
    expect(url).toContain('app.example.com');
  });

  it('works for google provider', async () => {
    vi.stubGlobal(
      'fetch',
      mockFetchOk({ auth_url: 'https://accounts.google.com/...', state: 'g-state' }),
    );
    const result = await getOAuthUrl('google', 'https://app.test/callback');
    expect(result.auth_url).toContain('google.com');
  });

  it('throws on non-ok response with error message', async () => {
    vi.stubGlobal('fetch', mockFetchError(400, 'Invalid redirect URI'));
    await expect(getOAuthUrl('google', 'invalid')).rejects.toThrow('Invalid redirect URI');
  });

  it('throws generic message when response body has no error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 503,
        json: vi.fn().mockRejectedValue(new Error('no json')),
      }),
    );
    await expect(getOAuthUrl('google', 'https://app.test/callback')).rejects.toThrow('503');
  });
});

describe('exchangeOAuthCode', () => {
  it('returns OAuthLoginResult on success', async () => {
    const loginResult = {
      access_token: 'eyJ...',
      refresh_token: 'rft...',
      csrf_token: 'csrf123',
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_expires_in: 86400,
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi.fn().mockResolvedValue({ data: loginResult }),
      }),
    );

    const payload = {
      provider: 'google' as const,
      code: 'auth-code-xyz',
      redirect_uri: 'https://app.example.com/callback',
      school_id: 'school-1',
    };
    const result = await exchangeOAuthCode(payload);

    expect(result.access_token).toBe(loginResult.access_token);
    expect(result.token_type).toBe('Bearer');
  });

  it('posts to /auth/oauth/login with JSON body', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: vi
        .fn()
        .mockResolvedValue({
          data: {
            access_token: 'tok',
            refresh_token: 'rft',
            csrf_token: 'csrf',
            token_type: 'Bearer',
            expires_in: 3600,
            refresh_expires_in: 86400,
          },
        }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await exchangeOAuthCode({
      provider: 'microsoft',
      code: 'code123',
      redirect_uri: 'https://app/cb',
      school_id: 'school-2',
    });

    const [url, init] = mockFetch.mock.calls[0] as [string, RequestInit];
    expect(url).toContain('/auth/oauth/login');
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe('application/json');
    const body = JSON.parse(init.body as string);
    expect(body.provider).toBe('microsoft');
    expect(body.code).toBe('code123');
  });

  it('throws on failed response with error message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: vi.fn().mockResolvedValue({ error: { message: 'Invalid OAuth code' } }),
      }),
    );
    await expect(
      exchangeOAuthCode({
        provider: 'google',
        code: 'bad',
        redirect_uri: 'https://app/cb',
        school_id: 'school-1',
      }),
    ).rejects.toThrow('Invalid OAuth code');
  });

  it('throws generic message when response body has no error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn().mockResolvedValue({}),
      }),
    );
    await expect(
      exchangeOAuthCode({ provider: 'google', code: 'x', redirect_uri: 'y', school_id: 'z' }),
    ).rejects.toThrow('500');
  });

  it('includes email_verification_required field when present', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: vi
          .fn()
          .mockResolvedValue({
            data: {
              access_token: 'tok',
              refresh_token: 'rft',
              csrf_token: 'csrf',
              token_type: 'Bearer',
              expires_in: 3600,
              refresh_expires_in: 86400,
              email_verification_required: true,
            },
          }),
      }),
    );
    const result = await exchangeOAuthCode({
      provider: 'google',
      code: 'code',
      redirect_uri: 'https://app/cb',
      school_id: 'school-1',
    });
    expect(result.email_verification_required).toBe(true);
  });
});
