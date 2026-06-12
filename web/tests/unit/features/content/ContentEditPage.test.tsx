import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { CmsContentEditPage } from '@/features/content/cms/ui/ContentEditPage';
import { renderWithProviders } from '../../../utils/render';

const cmsHooks = vi.hoisted(() => ({
  useCmsContentItem: vi.fn(),
  useDeleteCmsContent: vi.fn(),
  useUpdateCmsContent: vi.fn(),
  useUploadCmsContentAsset: vi.fn(),
}));

vi.mock('@/features/content/cms/model/useCms', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/features/content/cms/model/useCms')>();
  return {
    ...actual,
    useCmsContentItem: cmsHooks.useCmsContentItem,
    useDeleteCmsContent: cmsHooks.useDeleteCmsContent,
    useUpdateCmsContent: cmsHooks.useUpdateCmsContent,
    useUploadCmsContentAsset: cmsHooks.useUploadCmsContentAsset,
  };
});

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

function cmsContentResult(data: unknown, error: Error | null = null) {
  return {
    data: error ? undefined : data,
    error,
    isLoading: false,
    refetch: vi.fn(),
  };
}

function renderEditPage() {
  return renderWithProviders(
    <Routes>
      <Route path="/cms/content/:contentId/edit" element={<CmsContentEditPage />} />
    </Routes>,
    { user: { role: 'ADM' }, route: '/cms/content/content-1/edit' },
  );
}

describe('CmsContentEditPage', () => {
  beforeEach(() => {
    cmsHooks.useCmsContentItem.mockReturnValue(cmsContentResult(mockContentItem));
    cmsHooks.useDeleteCmsContent.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    cmsHooks.useUpdateCmsContent.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    cmsHooks.useUploadCmsContentAsset.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders loading state initially', () => {
    cmsHooks.useCmsContentItem.mockReturnValue({
      ...cmsContentResult(undefined),
      isLoading: true,
    });

    renderEditPage();
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders edit form with content data', async () => {
    cmsHooks.useCmsContentItem.mockReturnValue(cmsContentResult(mockContentItem));

    renderEditPage();
    await waitFor(() => {
      const titleInput = document.querySelector('input[name="title"]') as HTMLInputElement;
      expect(titleInput?.value || screen.queryByDisplayValue('Biology Lesson')).toBeTruthy();
    });
  });

  it('shows error when content fails to load', async () => {
    cmsHooks.useCmsContentItem.mockReturnValue(
      cmsContentResult(undefined, new Error('Content not found')),
    );

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
