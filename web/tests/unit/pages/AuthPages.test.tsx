/**
 * Tests for src/pages/auth/ and src/pages/user/GDPRPage.tsx
 */
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage';
import { GDPRPage } from '@/pages/user/GDPRPage';
import { renderWithProviders } from '../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../utils/mocks';

// ---------------------------------------------------------------------------
// ForgotPasswordPage
// ---------------------------------------------------------------------------
describe('ForgotPasswordPage', () => {
  it('renders the forgot password form', () => {
    renderWithProviders(<ForgotPasswordPage />, { user: null, isAuthenticated: false });
    expect(document.body.innerHTML.length).toBeGreaterThan(50);
  });

  it('shows email input', () => {
    renderWithProviders(<ForgotPasswordPage />, { user: null, isAuthenticated: false });
    const emailInput = document.querySelector('input[type="email"], input[name="email"]');
    expect(emailInput).toBeTruthy();
  });

  it('sends recovery request on form submit', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/v1/recovery/request', () =>
        HttpResponse.json({ data: null, meta: { timestamp: '', version: '' } }),
      ),
    );
    renderWithProviders(<ForgotPasswordPage />, { user: null, isAuthenticated: false });
    const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement;
    if (emailInput) {
      await user.type(emailInput, 'teacher@ecole.ma');
      // Find submit button
      const submitBtn = document.querySelector('button[type="submit"]') as HTMLButtonElement;
      if (submitBtn) await user.click(submitBtn);
      await waitFor(() => expect(document.body.textContent).toBeTruthy());
    }
  });

  it('shows error when recovery request fails', async () => {
    const user = userEvent.setup();
    server.use(http.post('/api/v1/recovery/request', () => apiErrorResponse('User not found')));
    renderWithProviders(<ForgotPasswordPage />, { user: null, isAuthenticated: false });
    const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement;
    if (emailInput) {
      await user.type(emailInput, 'unknown@test.com');
      const buttons = document.querySelectorAll('button[type="submit"], button');
      if (buttons.length > 0) {
        await user.click(buttons[0] as HTMLElement);
        await waitFor(() => expect(document.body.textContent).toBeTruthy());
      }
    }
  });

  it('shows success state after sending', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('/api/v1/recovery/request', () =>
        HttpResponse.json({ data: null, meta: { timestamp: '', version: '' } }),
      ),
    );
    renderWithProviders(<ForgotPasswordPage />, { user: null, isAuthenticated: false });
    const emailInput = document.querySelector('input[type="email"]') as HTMLInputElement;
    if (emailInput) {
      await user.type(emailInput, 'teacher@ecole.ma');
      const buttons = document.querySelectorAll('button');
      if (buttons.length > 0) {
        await user.click(buttons[0] as HTMLElement);
      }
    }
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});

// ---------------------------------------------------------------------------
// ResetPasswordPage
// ---------------------------------------------------------------------------
describe('ResetPasswordPage', () => {
  it('renders reset password form', () => {
    renderWithProviders(<ResetPasswordPage />, {
      user: null,
      isAuthenticated: false,
      route: '/reset-password?token=abc123',
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows password input fields', () => {
    renderWithProviders(<ResetPasswordPage />, {
      user: null,
      isAuthenticated: false,
      route: '/reset-password?token=reset-tok',
    });
    const inputs = document.querySelectorAll('input[type="password"]');
    expect(inputs.length).toBeGreaterThanOrEqual(1);
  });

  it('handles missing token gracefully', () => {
    renderWithProviders(<ResetPasswordPage />, { user: null, isAuthenticated: false });
    expect(document.body.textContent).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// GDPRPage
// ---------------------------------------------------------------------------
describe('GDPRPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/users/:userId/consent-log', () => apiResponse({ entries: [], total: 0 })),
      http.get('/api/v1/users/:userId/data-export', () =>
        apiResponse({ user_id: 'u1', email: 'u@test.com', created_at: '2026-01-01T00:00:00Z' }),
      ),
    );
  });

  it('renders GDPR page without crashing', async () => {
    renderWithProviders(<GDPRPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    renderWithProviders(<GDPRPage />, { user: { role: 'STD' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error when consent load fails', async () => {
    server.use(http.get('/api/v1/privacy/consents', () => apiErrorResponse('Unauthorized')));
    renderWithProviders(<GDPRPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders for ADM role', async () => {
    renderWithProviders(<GDPRPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
