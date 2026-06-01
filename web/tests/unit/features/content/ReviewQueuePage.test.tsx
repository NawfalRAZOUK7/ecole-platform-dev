import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { CmsReviewQueuePage } from '@/features/content/cms/ui/ReviewQueuePage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockSubmission = {
  id: 'sub-1',
  content_item_id: 'content-1',
  content_title: 'French Story Book',
  submitted_by: 'teacher-1',
  submitter_name: 'Mr. Ahmed',
  school_id: 'school-1',
  status: 'PENDING',
  submitted_at: '2026-01-10T09:00:00Z',
  reviewed_by: null,
  reviewed_at: null,
  review_notes: null,
  promoted_content_id: null,
};

describe('CmsReviewQueuePage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/cms/submissions', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<CmsReviewQueuePage />, { user: { role: 'ADM' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders submission items successfully', async () => {
    server.use(http.get('/api/v1/cms/submissions', () => apiListResponse([mockSubmission])));
    renderWithProviders(<CmsReviewQueuePage />, { user: { role: 'ADM' } });
    expect(await screen.findByText('French Story Book')).toBeInTheDocument();
    // submitter name and school are in the same div separated by bullet
    expect(screen.getByText(/Mr\. Ahmed/)).toBeInTheDocument();
  });

  it('shows empty state when no submissions', async () => {
    server.use(http.get('/api/v1/cms/submissions', () => apiListResponse([])));
    renderWithProviders(<CmsReviewQueuePage />, { user: { role: 'ADM' } });
    await waitFor(() => {
      expect(screen.queryByText(/empty/i) || document.querySelector('p.empty-state')).toBeTruthy();
    });
  });

  it('shows error state when submissions fail to load', async () => {
    server.use(
      http.get('/api/v1/cms/submissions', () => apiErrorResponse('Failed to load submissions')),
    );
    renderWithProviders(<CmsReviewQueuePage />, { user: { role: 'ADM' } });
    expect(await screen.findByText(/Failed to load submissions/)).toBeInTheDocument();
  });
});
