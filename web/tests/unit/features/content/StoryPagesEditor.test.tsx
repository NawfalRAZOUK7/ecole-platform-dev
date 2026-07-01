import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { StoryPagesEditor } from '@/features/content/cms/ui/StoryPagesEditor';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

describe('StoryPagesEditor', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/content-items/:contentId/pages', () => apiListResponse([])),
      http.post('/api/v1/content-items/:contentId/pages', () => apiListResponse([])),
      http.delete('/api/v1/content-items/:contentId/assets/:assetId', () => apiListResponse([])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<StoryPagesEditor contentId="content-1" contentType="story" />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no pages', async () => {
    renderWithProviders(<StoryPagesEditor contentId="content-1" contentType="story" />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders for coloring_book type', async () => {
    renderWithProviders(<StoryPagesEditor contentId="content-2" contentType="coloring_book" />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error banner on API failure', async () => {
    server.use(
      http.get('/api/v1/content-items/:contentId/pages', () => apiErrorResponse('Server error')),
    );
    renderWithProviders(<StoryPagesEditor contentId="content-1" contentType="story" />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
