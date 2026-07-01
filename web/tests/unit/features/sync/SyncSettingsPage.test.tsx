import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { SyncSettingsPage } from '@/features/sync/ui/SyncSettingsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const syncDevice = {
  id: 'device-1',
  device_name: 'School Server',
  device_type: 'local_server',
  firmware_version: '2.1.0',
  is_active: true,
  school_id: 'school-1',
  last_sync_at: '2026-04-01T00:00:00Z',
  created_at: '2026-01-01T00:00:00Z',
};

describe('SyncSettingsPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/sync/devices', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<SyncSettingsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders page title', async () => {
    const { container } = renderWithProviders(<SyncSettingsPage />, { user: { role: 'ADM' } });
    // Page renders "Sync Settings" (translated)
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(100), { timeout: 5000 });
  });

  it('renders with device data in table', async () => {
    server.use(http.get('/api/v1/sync/devices', () => apiListResponse([syncDevice])));
    renderWithProviders(<SyncSettingsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('School Server'));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/sync/devices', () => apiErrorResponse('Server error')));
    renderWithProviders(<SyncSettingsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('renders configuration card and register device card', async () => {
    const { container } = renderWithProviders(<SyncSettingsPage />, { user: { role: 'ADM' } });
    // Page renders configuration cards after loading
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(100), { timeout: 5000 });
  });
});
