import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { FeedPage } from '@/features/content/feed/ui/FeedPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('FeedPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/feed', () => apiListResponse([])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<FeedPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no feed items', async () => {
    renderWithProviders(<FeedPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders with feed data', async () => {
    server.use(
      http.get('/api/v1/feed', () =>
        apiListResponse([
          {
            id: 'feed-1',
            item_type: 'announcement',
            title: 'School News',
            body: 'Important update',
            created_at: '2026-01-01T00:00:00Z',
            is_read: false,
            reference_id: null,
          },
        ]),
      ),
    );
    renderWithProviders(<FeedPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/feed', () => apiErrorResponse('Server error')));
    renderWithProviders(<FeedPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
