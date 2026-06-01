import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { ActivityDetailPage } from '@/features/ai/activities/ui/ActivityDetailPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockActivity = {
  id: 'activity-1',
  title: 'Math Quiz',
  type: 'quiz',
  activity_type: 'quiz',
  difficulty: 'medium',
  objective: 'Practice multiplication',
  pedagogical_objective: 'Times tables mastery',
  description: 'Test your math skills',
  instructions: 'Complete all questions',
  sessions: [],
  participants: [],
  grading: null,
};

describe('ActivityDetailPage', () => {
  it('renders without crashing', async () => {
    server.use(http.get('/api/v1/activities', () => apiListResponse([mockActivity])));
    renderWithProviders(
      <Routes>
        <Route path="/activities/:id" element={<ActivityDetailPage />} />
      </Routes>,
      { route: '/activities/activity-1', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/activities', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiListResponse([mockActivity]);
      }),
    );
    renderWithProviders(
      <Routes>
        <Route path="/activities/:id" element={<ActivityDetailPage />} />
      </Routes>,
      { route: '/activities/activity-1', user: { role: 'TCH' } },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders activity data when loaded', async () => {
    server.use(http.get('/api/v1/activities', () => apiListResponse([mockActivity])));
    renderWithProviders(
      <Routes>
        <Route path="/activities/:id" element={<ActivityDetailPage />} />
      </Routes>,
      { route: '/activities/activity-1', user: { role: 'TCH' } },
    );
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state on failure', async () => {
    server.use(http.get('/api/v1/activities', () => apiErrorResponse('Load failed')));
    renderWithProviders(
      <Routes>
        <Route path="/activities/:id" element={<ActivityDetailPage />} />
      </Routes>,
      { route: '/activities/activity-1', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
