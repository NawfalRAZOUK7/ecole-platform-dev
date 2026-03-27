/**
 * Unified API client service with mandatory headers.
 *
 * Reference: S-075 — HTTP client per Pack E1
 * Headers: Authorization, Accept-Language, X-Correlation-Id, X-Client-Version, X-Client-Platform
 * Features: auto-retry with exponential backoff, cursor pagination helpers, 401 auto-refresh
 */

import i18next from 'i18next';

const API_BASE = '/api/v1';
const CLIENT_VERSION = '0.1.0';
const MAX_RETRIES = 3;

// In-memory access token (never stored in localStorage for security)
let accessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

function generateCorrelationId(): string {
  return crypto.randomUUID();
}

function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match ? decodeURIComponent(match[1]) : null;
}

/** Standard API error shape from backend */
export interface ApiError {
  code: string;
  message: string;
  category: string;
  correlation_id?: string;
  retryable: boolean;
  details?: Record<string, unknown>;
  timestamp: string;
}

export interface ApiResponse<T> {
  data: T;
  meta: {
    timestamp: string;
    version: string;
  };
}

export interface ApiListResponse<T> {
  data: T[];
  meta: {
    next_cursor: string | null;
    has_more: boolean;
    timestamp: string;
    version: string;
  };
}

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly apiError: ApiError;

  constructor(status: number, apiError: ApiError) {
    super(apiError.message);
    this.name = 'ApiClientError';
    this.status = status;
    this.apiError = apiError;
  }
}

async function refreshAccessToken(): Promise<string | null> {
  const csrf = getCsrfToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (csrf) {
    headers['X-CSRF-Token'] = csrf;
  }

  try {
    const resp = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers,
      credentials: 'include',
    });

    if (!resp.ok) {
      setAccessToken(null);
      return null;
    }

    const body = await resp.json();
    const newToken = body.data?.access_token;
    if (newToken) {
      setAccessToken(newToken);
      return newToken;
    }
    return null;
  } catch {
    setAccessToken(null);
    return null;
  }
}

async function ensureRefresh(): Promise<string | null> {
  // Deduplicate concurrent refresh calls
  if (!refreshPromise) {
    refreshPromise = refreshAccessToken().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  params?: Record<string, string | number | undefined>;
  skipAuth?: boolean;
  retries?: number;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = 'GET', body, params, skipAuth = false, retries = 0 } = options;

  // Build URL with query params
  let url = `${API_BASE}${path}`;
  if (params) {
    const sp = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null) {
        sp.set(k, String(v));
      }
    }
    const qs = sp.toString();
    if (qs) url += `?${qs}`;
  }

  // Build headers
  const headers: Record<string, string> = {
    'Accept': 'application/json',
    'Accept-Language': i18next.language || 'fr',
    'X-Correlation-Id': generateCorrelationId(),
    'X-Client-Version': CLIENT_VERSION,
    'X-Client-Platform': 'web',
  };

  if (!skipAuth && accessToken) {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const fetchOpts: RequestInit = {
    method,
    headers,
    credentials: 'include',
  };

  if (body !== undefined) {
    fetchOpts.body = JSON.stringify(body);
  }

  const resp = await fetch(url, fetchOpts);

  // Handle 401 — try refresh once
  if (resp.status === 401 && !skipAuth && retries === 0) {
    const newToken = await ensureRefresh();
    if (newToken) {
      return request<T>(path, { ...options, retries: 1 });
    }
    // Refresh failed — throw auth error
    const errorBody = await resp.json().catch(() => null);
    throw new ApiClientError(401, errorBody?.error || {
      code: 'ERR-AUTHN-001',
      message: 'Authentication required',
      category: 'authn',
      retryable: false,
      timestamp: new Date().toISOString(),
    });
  }

  // Parse response
  const responseBody = await resp.json().catch(() => null);

  if (!resp.ok) {
    const apiError: ApiError = responseBody?.error || {
      code: `ERR-SYS-${resp.status}`,
      message: resp.statusText || 'Unknown error',
      category: 'system',
      retryable: false,
      timestamp: new Date().toISOString(),
    };

    // Retry on retryable errors with exponential backoff
    if (apiError.retryable && retries < MAX_RETRIES) {
      const delay = Math.min(1000 * 2 ** retries, 10000);
      await sleep(delay);
      return request<T>(path, { ...options, retries: retries + 1 });
    }

    throw new ApiClientError(resp.status, apiError);
  }

  return responseBody as T;
}

// Typed convenience methods
export const api = {
  get: <T>(path: string, params?: Record<string, string | number | undefined>) =>
    request<ApiResponse<T>>(path, { params }),

  list: <T>(path: string, params?: Record<string, string | number | undefined>) =>
    request<ApiListResponse<T>>(path, { params }),

  post: <T>(path: string, body?: unknown) =>
    request<ApiResponse<T>>(path, { method: 'POST', body }),

  patch: <T>(path: string, body?: unknown) =>
    request<ApiResponse<T>>(path, { method: 'PATCH', body }),

  put: <T>(path: string, body?: unknown) =>
    request<ApiResponse<T>>(path, { method: 'PUT', body }),

  delete: <T>(path: string) =>
    request<ApiResponse<T>>(path, { method: 'DELETE' }),
};
