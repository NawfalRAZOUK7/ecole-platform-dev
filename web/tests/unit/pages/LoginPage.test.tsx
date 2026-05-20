import userEvent from '@testing-library/user-event';
import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LoginPage } from '@/pages/auth/LoginPage';
import { renderWithProviders } from '../../utils/render';

describe('LoginPage OAuth', () => {
  beforeEach(() => {
    sessionStorage.clear();
    window.history.replaceState(null, '', '/login');
  });

  it('renders social login buttons and starts Google OAuth with the school ID', async () => {
    const user = userEvent.setup();
    const startOAuthLogin = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(<LoginPage />, {
      route: '/login',
      user: null,
      auth: { startOAuthLogin },
    });

    await user.click(screen.getByRole('button', { name: /continue with google/i }));

    expect(startOAuthLogin).toHaveBeenCalledWith('google', '00000000-0000-4000-8000-000000000001');
    expect(screen.getByRole('button', { name: /continue with microsoft/i })).toBeInTheDocument();
  });

  it('completes OAuth login from callback query parameters', async () => {
    const completeOAuthLogin = vi.fn().mockResolvedValue(undefined);
    sessionStorage.setItem(
      'oauth_pending',
      JSON.stringify({ provider: 'google', state: 'state-1', schoolId: 'school-1' }),
    );

    renderWithProviders(<LoginPage />, {
      route: '/login?code=mock_google_code&state=state-1',
      user: null,
      auth: { completeOAuthLogin },
    });

    await waitFor(() => {
      expect(completeOAuthLogin).toHaveBeenCalledWith(
        'google',
        'mock_google_code',
        'state-1',
        'school-1',
      );
    });
  });
});
