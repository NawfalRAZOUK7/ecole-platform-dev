import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { CmsContentListPage } from '@/features/content/cms/ui/ContentListPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockContentItem = {
  id: 'content-1',
  title: 'Math Worksheet Grade 6',
  content_type: 'worksheet',
  level_band: 'ce2',
  language: 'fr',
  subject: 'math',
  description: 'A great math worksheet',
  page_count: 5,
  letter: null,
  target_age_min: 7,
  target_age_max: 8,
  theme_color: null,
  thumbnail_path: null,
  origin: 'PLATFORM',
  status: 'published',
  created_by: 'user-1',
  original_content_id: null,
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/cms/content', () => apiListResponse([mockContentItem])),
    http.get('/api/v1/content/library', () => apiListResponse([])),
    http.get('/api/v1/levels', () => apiListResponse([])),
  );
}

describe('CmsContentListPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/cms/content', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/content/library', () => apiListResponse([])),
    );
    renderWithProviders(<CmsContentListPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders content items successfully', async () => {
    setupHandlers();
    renderWithProviders(<CmsContentListPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('Math Worksheet Grade 6')).toBeInTheDocument();
  });

  it('shows empty state when no content', async () => {
    server.use(
      http.get('/api/v1/cms/content', () => apiListResponse([])),
      http.get('/api/v1/content/library', () => apiListResponse([])),
    );
    renderWithProviders(<CmsContentListPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText(/empty/i) || document.querySelector('.empty-state')).toBeTruthy();
    });
  });

  it('shows error state when content fails to load', async () => {
    server.use(
      http.get('/api/v1/cms/content', () => apiErrorResponse('Failed to load content')),
      http.get('/api/v1/content/library', () => apiListResponse([])),
    );
    renderWithProviders(<CmsContentListPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load content/)).toBeInTheDocument();
  });
});
