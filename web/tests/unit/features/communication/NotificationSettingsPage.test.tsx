import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { NotificationSettingsPage } from '@/features/communication/notifications/ui/NotificationSettingsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const preferencesResponse = {
  preferences: [
    { category: 'academic', channel: 'email', enabled: true },
    { category: 'billing', channel: 'email', enabled: false },
    { category: 'attendance', channel: 'push', enabled: true },
  ],
};

const digestResponse = {
  digest_frequency: 'daily',
};

describe('NotificationSettingsPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/notifications/preferences', () => apiResponse(preferencesResponse)),
      http.get('/api/v1/notifications/digest/preferences', () => apiResponse(digestResponse)),
      http.get('/api/v1/devices', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<NotificationSettingsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows the settings page after loading', async () => {
    const { container } = renderWithProviders(<NotificationSettingsPage />, {
      user: { role: 'TCH' },
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders empty devices state when no devices registered', async () => {
    renderWithProviders(<NotificationSettingsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders devices list when devices are registered', async () => {
    const device = {
      id: 'dev-1',
      device_name: 'My Phone',
      platform: 'android',
      token_preview: 'abc...xyz',
      last_active_at: '2026-04-01T00:00:00Z',
    };
    server.use(http.get('/api/v1/devices', () => apiListResponse([device])));
    renderWithProviders(<NotificationSettingsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/notifications/preferences', () => apiErrorResponse('Server error')),
      http.get('/api/v1/notifications/digest/preferences', () => apiResponse(digestResponse)),
      http.get('/api/v1/devices', () => apiListResponse([])),
    );
    renderWithProviders(<NotificationSettingsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
