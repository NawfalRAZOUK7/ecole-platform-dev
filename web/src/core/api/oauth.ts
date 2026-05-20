/**
 * OAuth / Social Login API client.
 *
 * Reference: Phase 10 — Social Login Support
 */

import { ApiResponse } from './client';

const API_BASE = '/api/v1';

/** OAuth provider supported by the backend */
export type OAuthProvider = 'google' | 'microsoft';

export interface OAuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface OAuthLoginPayload {
  provider: OAuthProvider;
  code: string;
  redirect_uri: string;
  school_id: string;
}

export interface OAuthLoginResult {
  access_token: string;
  refresh_token: string;
  csrf_token: string;
  token_type: string;
  expires_in: number;
  refresh_expires_in: number;
  email_verification_required?: boolean;
}

/**
 * Get the OAuth authorization URL from the backend.
 * The backend returns the URL to redirect the user to for consent.
 */
export async function getOAuthUrl(
  provider: OAuthProvider,
  redirectUri: string,
): Promise<OAuthUrlResponse> {
  const params = new URLSearchParams({ redirect_uri: redirectUri });
  const resp = await fetch(`${API_BASE}/auth/oauth/${provider}/url?${params.toString()}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });

  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new Error(body.error?.message || `OAuth URL request failed (${resp.status})`);
  }

  const body: ApiResponse<OAuthUrlResponse> = await resp.json();
  return body.data;
}

/**
 * Exchange OAuth authorization code for JWT tokens.
 */
export async function exchangeOAuthCode(payload: OAuthLoginPayload): Promise<OAuthLoginResult> {
  const resp = await fetch(`${API_BASE}/auth/oauth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const body = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    throw new Error(body.error?.message || `OAuth login failed (${resp.status})`);
  }

  return body.data as OAuthLoginResult;
}
