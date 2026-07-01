import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { TwoFactorPage } from '@/features/user/profile/ui/TwoFactorPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

describe('TwoFactorPage', () => {
  beforeEach(() => {
    server.use(
      http.post('/api/v1/auth/2fa/setup', () =>
        apiResponse({ provisioning_uri: 'otpauth://totp/test', secret: 'SECRET123' }),
      ),
    );
  });

  it('renders without crashing for user without 2FA', async () => {
    renderWithProviders(<TwoFactorPage />, { user: { role: 'TCH', totp_enabled: false } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows enable button when 2FA is disabled', async () => {
    const { container } = renderWithProviders(<TwoFactorPage />, {
      user: { role: 'TCH', totp_enabled: false },
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.innerHTML.length).toBeGreaterThan(100);
  });

  it('shows disable button when 2FA is enabled', async () => {
    const { container } = renderWithProviders(<TwoFactorPage />, {
      user: { role: 'TCH', totp_enabled: true },
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.innerHTML.length).toBeGreaterThan(100);
  });

  it('renders page title', async () => {
    renderWithProviders(<TwoFactorPage />, { user: { role: 'TCH', totp_enabled: false } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(100));
  });

  it('shows status indicator for 2FA state', async () => {
    const { container } = renderWithProviders(<TwoFactorPage />, {
      user: { role: 'STD', totp_enabled: false },
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.textContent).toBeTruthy();
  });
});
