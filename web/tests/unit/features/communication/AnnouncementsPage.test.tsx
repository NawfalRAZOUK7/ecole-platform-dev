import { screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AnnouncementsPage } from '@/features/communication/announcements/ui/AnnouncementsPage';
import { renderWithProviders } from '../../../utils/render';

const announcementHooks = vi.hoisted(() => ({
  useAnnouncements: vi.fn(),
  useCreateAnnouncement: vi.fn(),
  usePublishAnnouncement: vi.fn(),
  useUpdateAnnouncement: vi.fn(),
}));

vi.mock('@/features/communication/announcements/model/useAnnouncements', () => ({
  useAnnouncements: announcementHooks.useAnnouncements,
  useCreateAnnouncement: announcementHooks.useCreateAnnouncement,
  usePublishAnnouncement: announcementHooks.usePublishAnnouncement,
  useUpdateAnnouncement: announcementHooks.useUpdateAnnouncement,
}));

const mockAnnouncement = {
  id: 'ann-1',
  school_id: 'school-1',
  author_id: 'admin-1',
  title: 'School Closure Notice',
  body: 'The school will be closed on Friday.',
  status: 'PUBLISHED',
  target_roles: ['STD', 'PAR', 'TCH'],
  target_class_ids: [],
  published_at: '2026-01-10T08:00:00Z',
  created_at: '2026-01-09T15:00:00Z',
  updated_at: null,
};

function announcementsResult(items: unknown[], error: Error | null = null) {
  return {
    data: error ? undefined : { pages: [{ data: items, meta: { has_more: false } }] },
    error,
    fetchNextPage: vi.fn(),
    hasNextPage: false,
    isFetchingNextPage: false,
    isLoading: false,
    refetch: vi.fn(),
  };
}

describe('AnnouncementsPage', () => {
  beforeEach(() => {
    announcementHooks.useAnnouncements.mockReturnValue(announcementsResult([]));
    announcementHooks.useCreateAnnouncement.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    announcementHooks.usePublishAnnouncement.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
    announcementHooks.useUpdateAnnouncement.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders loading state initially', () => {
    announcementHooks.useAnnouncements.mockReturnValue({
      ...announcementsResult([]),
      isLoading: true,
    });

    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders announcements successfully', async () => {
    announcementHooks.useAnnouncements.mockReturnValue(announcementsResult([mockAnnouncement]));

    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('School Closure Notice')).toBeInTheDocument();
  });

  it('shows empty state when no announcements', async () => {
    announcementHooks.useAnnouncements.mockReturnValue(announcementsResult([]));

    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/empty/i) || document.querySelector('.empty-state__icon'),
      ).toBeTruthy();
    });
  });

  it('shows error state when announcements fail to load', async () => {
    announcementHooks.useAnnouncements.mockReturnValue(
      announcementsResult([], new Error('Failed to load announcements')),
    );

    renderWithProviders(<AnnouncementsPage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load announcements/)).toBeInTheDocument();
  });
});
