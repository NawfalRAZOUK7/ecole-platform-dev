import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { CmsContentEditPage } from '@/features/content/cms/ui/ContentEditPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockContentItem = {
  id: 'content-1',
  title: 'Biology Lesson',
  content_type: 'lesson',
  level_band: '6eme',
  language: 'fr',
  subject: 'science',
  description: 'Biology intro',
  page_count: null,
  letter: null,
  target_age_min: 11,
  target_age_max: 12,
  theme_color: null,
  thumbnail_path: null,
  origin: 'PLATFORM',
  status: 'draft',
  created_by: 'user-1',
  original_content_id: null,
};

function renderEditPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/cms/content/:contentId/edit" element={<CmsContentEditPage />} />
    </Routes>,
    { user: { role: 'ADM' }, route: '/cms/content/content-1/edit' },
  );
}

describe('CmsContentEditPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/cms/content', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([mockContentItem]);
      }),
    );
    renderEditPage();
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders edit form with content data', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiListResponse([mockContentItem])));
    renderEditPage();
    await waitFor(() => {
      const titleInput = document.querySelector('input[name="title"]') as HTMLInputElement;
      expect(titleInput?.value || screen.queryByDisplayValue('Biology Lesson')).toBeTruthy();
    });
  });

  it('shows error when content fails to load', async () => {
    server.use(http.get('/api/v1/cms/content', () => apiErrorResponse('Content not found', 404)));
    renderEditPage();
    await waitFor(() => {
      expect(
        screen.queryByText(/Content not found/) ||
          screen.queryByText(/not found/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });
});
