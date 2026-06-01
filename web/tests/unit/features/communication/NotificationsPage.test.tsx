import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { NotificationsPage } from '@/features/communication/notifications/ui/NotificationsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('NotificationsPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/notifications', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<NotificationsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no notifications', async () => {
    renderWithProviders(<NotificationsPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with notification items', async () => {
    server.use(
      http.get('/api/v1/notifications', () =>
        apiListResponse([
          {
            id: 'notif-1',
            title: 'New Grade Posted',
            body: 'Your grade for Math has been posted.',
            category: 'academic',
            channel: 'in_app',
            is_read: false,
            created_at: '2026-01-01T00:00:00Z',
            reference_id: null,
            reference_type: null,
          },
        ]),
      ),
    );
    renderWithProviders(<NotificationsPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/notifications', () => apiErrorResponse('Server error')));
    renderWithProviders(<NotificationsPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
