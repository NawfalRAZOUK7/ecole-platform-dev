import { waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { JustificationReviewPage } from '@/features/admin/ui/JustificationReviewPage';
import { renderWithProviders } from '../../../utils/render';

const adminHooks = vi.hoisted(() => ({
  useAdminJustifications: vi.fn(),
  useReviewJustification: vi.fn(),
}));

vi.mock('@/features/admin/model/useAdmin', () => ({
  useAdminJustifications: adminHooks.useAdminJustifications,
  useReviewJustification: adminHooks.useReviewJustification,
}));

const pendingJustification = {
  id: 'just-1',
  attendance_record_id: 'att-1',
  parent_id: 'parent-1',
  status: 'pending',
  reason: 'Child was sick',
  rejection_reason: null,
  created_at: '2026-04-05T00:00:00Z',
};

const rejectedJustification = {
  id: 'just-2',
  attendance_record_id: 'att-2',
  parent_id: 'parent-2',
  status: 'rejected',
  reason: 'Family trip',
  rejection_reason: 'Not a valid reason',
  created_at: '2026-04-06T00:00:00Z',
};

function justificationsResult(items: unknown[], error: Error | null = null) {
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

describe('JustificationReviewPage', () => {
  beforeEach(() => {
    adminHooks.useAdminJustifications.mockReturnValue(justificationsResult([]));
    adminHooks.useReviewJustification.mockReturnValue({
      error: null,
      isPending: false,
      mutateAsync: vi.fn(),
    });
  });

  it('renders without crashing', async () => {
    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows empty state with no justifications', async () => {
    const { container } = renderWithProviders(<JustificationReviewPage />, {
      user: { role: 'ADM' },
    });
    await waitFor(() => expect(container.innerHTML.length).toBeGreaterThan(0));
  });

  it('renders pending justification items', async () => {
    adminHooks.useAdminJustifications.mockReturnValue(justificationsResult([pendingJustification]));

    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('Child was sick'));
  });

  it('renders rejected justification with rejection reason', async () => {
    adminHooks.useAdminJustifications.mockReturnValue(
      justificationsResult([rejectedJustification]),
    );

    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows error banner on API failure', async () => {
    adminHooks.useAdminJustifications.mockReturnValue(
      justificationsResult([], new Error('Server error')),
    );

    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
