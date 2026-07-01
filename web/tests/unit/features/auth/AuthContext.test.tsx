import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { AuthProvider, useAuth } from '@/app/providers/AuthContext';
import { setAccessToken } from '@/core/api/client';
import { createUser } from '../../../utils/factories';
import { renderWithProviders } from '../../../utils/render';
import { apiResponse, server } from '../../../utils/mocks';

function AuthHarness() {
  const { user, isAuthenticated, isLoading, error, twoFactorPending, login, verify2fa, logout } =
    useAuth();

  return (
    <div>
      <div data-testid="auth-state">{isAuthenticated ? 'yes' : 'no'}</div>
      <div data-testid="loading-state">{isLoading ? 'yes' : 'no'}</div>
      <div data-testid="user-name">{user?.full_name ?? 'none'}</div>
      <div data-testid="error-state">{error ?? 'none'}</div>
      <div data-testid="pending-email">{twoFactorPending?.email ?? 'none'}</div>
      <button type="button" onClick={() => void login('teacher@ecole.test', 'secret', 'school-1')}>
        Login
      </button>
      <button type="button" onClick={() => void verify2fa('123456')}>
        Verify 2FA
      </button>
      <button type="button" onClick={() => void logout()}>
        Logout
      </button>
    </div>
  );
}

function renderAuthProvider() {
  return renderWithProviders(
    <AuthProvider>
      <AuthHarness />
    </AuthProvider>,
    { user: null },
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    setAccessToken(null);
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  });

  afterEach(() => {
    setAccessToken(null);
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
  });

  it('completes the login flow and loads the user profile', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('/api/v1/auth/login', () => apiResponse({ access_token: 'token-login' })),
      http.get('/api/v1/auth/me', () => apiResponse(createUser({ full_name: 'Teacher Login' }))),
    );

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading-state')).toHaveTextContent('no');
    });

    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('yes');
    });
    expect(screen.getByTestId('user-name')).toHaveTextContent('Teacher Login');
  });

  it('handles 2FA verification before authenticating the user', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('/api/v1/auth/login', () =>
        apiResponse({ requires_2fa: true, temp_token: 'temp-token-1' }),
      ),
      http.post('/api/v1/auth/2fa/verify', () => apiResponse({ access_token: 'token-2fa' })),
      http.get('/api/v1/auth/me', () => apiResponse(createUser({ full_name: 'Teacher 2FA' }))),
    );

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading-state')).toHaveTextContent('no');
    });

    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByTestId('pending-email')).toHaveTextContent('teacher@ecole.test');
    });

    await user.click(screen.getByRole('button', { name: 'Verify 2FA' }));

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('yes');
    });
    expect(screen.getByTestId('user-name')).toHaveTextContent('Teacher 2FA');
    expect(screen.getByTestId('pending-email')).toHaveTextContent('none');
  });

  it('restores the session through token refresh on mount', async () => {
    document.cookie = 'csrf_token=test-csrf; path=/';

    server.use(
      http.post('/api/v1/auth/refresh', () => apiResponse({ access_token: 'token-refresh' })),
      http.get('/api/v1/auth/me', () => apiResponse(createUser({ full_name: 'Teacher Refresh' }))),
    );

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('yes');
    });
    expect(screen.getByTestId('user-name')).toHaveTextContent('Teacher Refresh');
  });

  it('logs the user out and clears auth state', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('/api/v1/auth/login', () => apiResponse({ access_token: 'token-logout' })),
      http.post('/api/v1/auth/logout', () => apiResponse({})),
      http.get('/api/v1/auth/me', () => apiResponse(createUser({ full_name: 'Teacher Logout' }))),
    );

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId('loading-state')).toHaveTextContent('no');
    });

    await user.click(screen.getByRole('button', { name: 'Login' }));

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('yes');
    });

    await user.click(screen.getByRole('button', { name: 'Logout' }));

    await waitFor(() => {
      expect(screen.getByTestId('auth-state')).toHaveTextContent('no');
    });
    expect(screen.getByTestId('user-name')).toHaveTextContent('none');
  });

  it('shows error on failed login (invalid credentials)', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-IAM-401', message: 'Invalid credentials' } }),
            { status: 401, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    renderAuthProvider();
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
  });

  it('shows locked error when account is locked', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-IAM-403', message: 'Account locked' } }),
            { status: 403, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    renderAuthProvider();
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
  });

  it('cancel2fa clears twoFactorPending state', async () => {
    const user = userEvent.setup();
    // First trigger 2FA pending
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({
              data: { requires_2fa: true, temp_token: 'tmp123', email: 'teacher@ecole.test' },
            }),
            { status: 200, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    function AuthHarnessWith2faCancel() {
      const { twoFactorPending, login, cancel2fa } = useAuth();
      return (
        <div>
          <div data-testid="pending-email">{twoFactorPending?.email ?? 'none'}</div>
          <button type="button" onClick={() => void login('t@test.com', 'pw', 'school-1')}>
            Login
          </button>
          <button type="button" onClick={cancel2fa}>
            Cancel 2FA
          </button>
        </div>
      );
    }
    renderWithProviders(
      <AuthProvider>
        <AuthHarnessWith2faCancel />
      </AuthProvider>,
      { user: null },
    );
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('pending-email')).not.toHaveTextContent('none');
    });
    await user.click(screen.getByRole('button', { name: 'Cancel 2FA' }));
    await waitFor(() => {
      expect(screen.getByTestId('pending-email')).toHaveTextContent('none');
    });
  });

  it('clearError removes error from state', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-GENERIC', message: 'Generic error' } }),
            { status: 500, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    function AuthHarnessWithClear() {
      const { error, login, clearError } = useAuth();
      return (
        <div>
          <div data-testid="error-state">{error ?? 'none'}</div>
          <button type="button" onClick={() => void login('t@test.com', 'pw', 'school-1')}>
            Login
          </button>
          <button type="button" onClick={clearError}>
            Clear Error
          </button>
        </div>
      );
    }
    renderWithProviders(
      <AuthProvider>
        <AuthHarnessWithClear />
      </AuthProvider>,
      { user: null },
    );
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
    await user.click(screen.getByRole('button', { name: 'Clear Error' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).toHaveTextContent('none');
    });
  });

  it('shows disabled error when account is disabled', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-MISC', message: 'Account disabled' } }),
            { status: 403, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    renderAuthProvider();
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
  });

  it('shows oauth error for ERR-OAUTH code', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-OAUTH-001', message: 'OAuth failed' } }),
            { status: 400, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    renderAuthProvider();
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
  });

  it('shows generic error for unknown error code', async () => {
    const user = userEvent.setup();
    server.use(
      http.post(
        '/api/v1/auth/login',
        () =>
          new Response(
            JSON.stringify({ error: { code: 'ERR-UNKNOWN-999', message: 'Something went wrong' } }),
            { status: 500, headers: { 'Content-Type': 'application/json' } },
          ),
      ),
    );
    renderAuthProvider();
    await user.click(screen.getByRole('button', { name: 'Login' }));
    await waitFor(() => {
      expect(screen.getByTestId('error-state')).not.toHaveTextContent('none');
    });
  });
});
