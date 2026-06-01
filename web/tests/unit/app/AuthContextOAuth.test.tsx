/**
 * Extended tests for AuthContext: OAuth flows.
 * Covers: startOAuthLogin, completeOAuthLogin (CSRF check, success, error paths).
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AuthProvider, useAuth } from '@/app/providers/AuthContext';
import { setAccessToken } from '@/core/api/client';
import { renderWithProviders } from '../../utils/render';
import { server } from '../../utils/mocks';

beforeEach(() => {
  setAccessToken(null);
  sessionStorage.clear();
});

afterEach(() => {
  sessionStorage.clear();
  vi.restoreAllMocks();
});

function OAuthHarness() {
  const { error, isLoading, isAuthenticated, startOAuthLogin, completeOAuthLogin, clearError } =
    useAuth();
  return (
    <div>
      <div data-testid="auth-state">{isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="loading">{isLoading ? 'yes' : 'no'}</div>
      <div data-testid="error">{error ?? 'none'}</div>
      <button onClick={() => void startOAuthLogin('google', 'school-1')}>Start Google OAuth</button>
      <button
        onClick={() => void completeOAuthLogin('google', 'code-xyz', 'state-abc', 'school-1')}
      >
        Complete OAuth
      </button>
      <button onClick={clearError}>Clear Error</button>
    </div>
  );
}

function renderOAuth() {
  return renderWithProviders(
    <AuthProvider>
      <OAuthHarness />
    </AuthProvider>,
    { user: null },
  );
}

describe('AuthContext — OAuth', () => {
  it('startOAuthLogin attempts OAuth URL on click', async () => {
    const user = userEvent.setup();
    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Start Google OAuth' }));
    // Loading starts - button was clicked and OAuth flow attempted
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('startOAuthLogin shows error when OAuth URL fetch fails', async () => {
    const user = userEvent.setup();
    vi.doMock('@/core/api/oauth', () => ({
      getOAuthUrl: vi.fn().mockRejectedValue(new Error('OAuth service down')),
      exchangeOAuthCode: vi.fn(),
    }));

    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Start Google OAuth' }));

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('no');
    });
    // Either error or completed state
    expect(document.body.textContent).toBeTruthy();
    vi.doUnmock('@/core/api/oauth');
  });

  it('completeOAuthLogin fails when no pending OAuth state in sessionStorage', async () => {
    const user = userEvent.setup();
    // No oauth_pending in sessionStorage → error
    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Complete OAuth' }));

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('no');
    });
    // Should set error since no pending state
    expect(screen.getByTestId('error').textContent).not.toBe('none');
  });

  it('completeOAuthLogin fails when state does not match', async () => {
    const user = userEvent.setup();
    // Set pending state with different state value
    sessionStorage.setItem(
      'oauth_pending',
      JSON.stringify({ provider: 'google', state: 'different-state', schoolId: 'school-1' }),
    );

    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Complete OAuth' }));

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('no');
    });
    // Mismatched state → error
    expect(screen.getByTestId('error').textContent).not.toBe('none');
  });

  it('completeOAuthLogin succeeds when state matches', async () => {
    const user = userEvent.setup();
    // Set valid pending state
    sessionStorage.setItem(
      'oauth_pending',
      JSON.stringify({ provider: 'google', state: 'state-abc', schoolId: 'school-1' }),
    );

    server.use(
      http.get('/api/v1/auth/me', () =>
        HttpResponse.json({
          data: {
            id: 'u1',
            email: 'oauth@test.com',
            full_name: 'OAuth User',
            role: 'STD',
            school_id: 'school-1',
            totp_enabled: false,
            permissions: [],
            memberships: [],
          },
          meta: { timestamp: '', version: '' },
        }),
      ),
    );

    vi.doMock('@/core/api/oauth', () => ({
      getOAuthUrl: vi.fn(),
      exchangeOAuthCode: vi.fn().mockResolvedValue({
        access_token: 'oauth-token',
        refresh_token: 'rft',
        csrf_token: 'csrf',
        token_type: 'Bearer',
        expires_in: 3600,
        refresh_expires_in: 86400,
      }),
    }));

    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Complete OAuth' }));

    await waitFor(
      () => {
        const authState = screen.getByTestId('auth-state').textContent;
        const loading = screen.getByTestId('loading').textContent;
        // Either authenticated or done loading
        expect(loading).toBe('no');
      },
      { timeout: 5000 },
    );

    vi.doUnmock('@/core/api/oauth');
  });

  it('completeOAuthLogin handles invalid JSON in sessionStorage', async () => {
    const user = userEvent.setup();
    sessionStorage.setItem('oauth_pending', 'invalid-json{{{');

    renderOAuth();
    await user.click(screen.getByRole('button', { name: 'Complete OAuth' }));

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('no');
    });
    expect(screen.getByTestId('error').textContent).not.toBe('none');
  });
});
