import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { AnnouncementsPage } from '@/features/communication/announcements/ui/AnnouncementsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockAnnouncement = {
  id: 'ann-1',
  title: 'School Closure Notice',
  body: 'The school will be closed on Friday.',
  status: 'published',
  target_roles: ['STD', 'PAR', 'TCH'],
  published_at: '2026-01-10T08:00:00Z',
  created_at: '2026-01-09T15:00:00Z',
  created_by: 'admin-1',
};

describe('AnnouncementsPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/announcements', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders announcements successfully', async () => {
    server.use(http.get('/api/v1/announcements', () => apiListResponse([mockAnnouncement])));
    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('School Closure Notice')).toBeInTheDocument();
  });

  it('shows empty state when no announcements', async () => {
    server.use(http.get('/api/v1/announcements', () => apiListResponse([])));
    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/empty/i) || document.querySelector('.empty-state__icon'),
      ).toBeTruthy();
    });
  });

  it('shows error state when announcements fail to load', async () => {
    server.use(
      http.get('/api/v1/announcements', () => apiErrorResponse('Failed to load announcements')),
    );
    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load announcements/)).toBeInTheDocument();
  });
});
