import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { ContentDetailPage } from '@/features/content/catalog/ui/ContentDetailPage';
import { renderWithProviders } from '../../../utils/render';

const contentHooks = vi.hoisted(() => ({
  useContentDetail: vi.fn(),
  useToggleContentPublish: vi.fn(),
  useUpdateContentOrdering: vi.fn(),
  useUpdateContentProgress: vi.fn(),
}));

vi.mock('@/features/content/catalog/model/useContent', () => ({
  useContentDetail: contentHooks.useContentDetail,
  useToggleContentPublish: contentHooks.useToggleContentPublish,
  useUpdateContentOrdering: contentHooks.useUpdateContentOrdering,
  useUpdateContentProgress: contentHooks.useUpdateContentProgress,
}));

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

function detailResult(data: unknown, error: Error | null = null) {
  return {
    data: error ? undefined : data,
    error,
    isLoading: false,
    refetch: vi.fn(),
  };
}

function renderDetailPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/content/:id" element={<ContentDetailPage />} />
    </Routes>,
    { user: { role: 'STD' }, route: '/content/content-1' },
  );
}

describe('ContentDetailPage', () => {
  beforeEach(() => {
    contentHooks.useContentDetail.mockReturnValue(detailResult(mockContentItem));
    contentHooks.useToggleContentPublish.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    contentHooks.useUpdateContentOrdering.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    contentHooks.useUpdateContentProgress.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders loading state initially', () => {
    contentHooks.useContentDetail.mockReturnValue({
      ...detailResult(undefined),
      isLoading: true,
    });

    renderDetailPage();
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders content details successfully', async () => {
    contentHooks.useContentDetail.mockReturnValue(detailResult(mockContentItem));

    renderDetailPage();
    expect(await screen.findByText('Arabic Storybook')).toBeInTheDocument();
  });

  it('shows error state when content fails to load', async () => {
    contentHooks.useContentDetail.mockReturnValue(
      detailResult(undefined, new Error('Content not found')),
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
