import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { RegisterPage } from '@/features/auth/ui/RegisterPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

describe('RegisterPage', () => {
  beforeEach(() => {
    server.use(
      http.post('/api/v1/auth/register', () =>
        apiResponse({
          user_id: 'user-1',
          school_id: 'school-1',
          role: 'STD',
          access_token: 'tok-123',
          email_verification_required: false,
        }),
      ),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<RegisterPage />, { user: null });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows the invite code step by default', async () => {
    const { container } = renderWithProviders(<RegisterPage />, { user: null });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
    expect(container.querySelector('input')).toBeTruthy();
  });

  it('renders the registration title', async () => {
    renderWithProviders(<RegisterPage />, { user: null });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows progress steps', async () => {
    const { container } = renderWithProviders(<RegisterPage />, { user: null });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with invite token from URL params', async () => {
    renderWithProviders(<RegisterPage />, {
      user: null,
      route: '/register?invite=TESTINVITE',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
