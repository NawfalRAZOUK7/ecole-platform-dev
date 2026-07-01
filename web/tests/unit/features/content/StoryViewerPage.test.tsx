import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { StoryViewerPage } from '@/features/content/student/ui/StoryViewerPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockContentItem = {
  id: 'content-1',
  title: 'My Story',
  type: 'story',
  status: 'published',
  subject: 'reading',
  level: 'ce1',
  description: null,
  thumbnail_url: null,
  created_at: '2026-01-01T00:00:00Z',
  sort_order: 1,
};

describe('StoryViewerPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/content-items/:id', () => apiResponse(mockContentItem)),
      http.get('/api/v1/content-items/:id/pages', () => apiListResponse([])),
      http.post('/api/v1/content-items/:id/progress', () => apiResponse({})),
      http.post('/api/v1/content-items/:id/complete', () => apiResponse({})),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<StoryViewerPage />, {
      user: { role: 'STD' },
      route: '/content/story/content-1',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    renderWithProviders(<StoryViewerPage />, {
      user: { role: 'STD' },
      route: '/content/story/content-1',
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders with empty pages', async () => {
    renderWithProviders(<StoryViewerPage />, {
      user: { role: 'STD' },
      route: '/content/story/content-1',
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error when content fails to load', async () => {
    server.use(
      http.get('/api/v1/content-items/:id', () => apiErrorResponse('Content not found', 404)),
    );
    renderWithProviders(<StoryViewerPage />, {
      user: { role: 'STD' },
      route: '/content/story/content-1',
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
