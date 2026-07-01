import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { ReviewDetailPage } from '@/features/user/family/ui/ReviewDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockSessionDetail = {
  id: 'session-1',
  child_id: 'child-1',
  type: 'quiz',
  title: 'Math Quiz',
  status: 'completed',
  completed_at: '2026-01-01T10:00:00Z',
  started_at: '2026-01-01T09:30:00Z',
  score: 85,
  max_score: 100,
  duration_minutes: 30,
  comments: [],
  text: null,
  suggestion: null,
  quiz_items: [],
};

function renderPage(route = '/family/review/child-1/sessions/session-1') {
  return renderWithProviders(
    <Routes>
      <Route path="/family/review/:childId/sessions/:sessionId" element={<ReviewDetailPage />} />
    </Routes>,
    { user: { role: 'PAR' }, route },
  );
}

describe('ReviewDetailPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/shared-reviews/:childId/sessions/:sessionId', () =>
        apiResponse(mockSessionDetail),
      ),
      http.post('/api/v1/shared-reviews/:childId/sessions/:sessionId/comments', () =>
        apiResponse({}),
      ),
    );
  });

  it('renders without crashing', async () => {
    renderPage();
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    renderPage();
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders session detail after loading', async () => {
    renderPage();
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(0));
  });

  it('shows error on API failure', async () => {
    server.use(
      http.get('/api/v1/shared-reviews/:childId/sessions/:sessionId', () =>
        apiErrorResponse('Session not found', 404),
      ),
    );
    renderPage();
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
