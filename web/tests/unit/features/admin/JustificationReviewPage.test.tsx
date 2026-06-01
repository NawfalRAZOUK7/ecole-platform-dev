import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { JustificationReviewPage } from '@/features/admin/ui/JustificationReviewPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

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

describe('JustificationReviewPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/admin/justifications', () => apiListResponse([])));
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
    server.use(
      http.get('/api/v1/admin/justifications', () => apiListResponse([pendingJustification])),
    );
    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toContain('Child was sick'));
  });

  it('renders rejected justification with rejection reason', async () => {
    server.use(
      http.get('/api/v1/admin/justifications', () => apiListResponse([rejectedJustification])),
    );
    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows error banner on API failure', async () => {
    server.use(http.get('/api/v1/admin/justifications', () => apiErrorResponse('Server error')));
    renderWithProviders(<JustificationReviewPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
