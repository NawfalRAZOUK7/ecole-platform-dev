import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { ContentDetailPage } from '@/features/content/catalog/ui/ContentDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, apiResponse, server } from '../../../utils/mocks';

const mockContentItem = {
  id: 'content-1',
  title: 'Arabic Storybook',
  content_type: 'story',
  level_band: 'cp',
  language: 'ar',
  subject: 'arabic',
  description: 'A great storybook for early learners',
  page_count: 12,
  letter: 'A',
  target_age_min: 6,
  target_age_max: 7,
  theme_color: '#FF5733',
  thumbnail_path: null,
  origin: 'PLATFORM',
  status: 'published',
  created_by: 'user-1',
  original_content_id: null,
};

function renderDetailPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/content/:id" element={<ContentDetailPage />} />
    </Routes>,
    { user: { role: 'STD' }, route: '/content/content-1' },
  );
}

describe('ContentDetailPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/content-items/:id', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiResponse(mockContentItem);
      }),
    );
    renderDetailPage();
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders content details successfully', async () => {
    server.use(
      http.get('/api/v1/content-items/:id', () => apiResponse(mockContentItem)),
      http.get('/api/v1/content-items/:id/pages', () => apiListResponse([])),
    );
    renderDetailPage();
    expect(await screen.findByText('Arabic Storybook')).toBeInTheDocument();
  });

  it('shows error state when content fails to load', async () => {
    server.use(
      http.get('/api/v1/content-items/:id', () => apiErrorResponse('Content not found', 404)),
    );
    renderDetailPage();
    await waitFor(() => {
      expect(
        screen.queryByText(/not found/i) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });
});
