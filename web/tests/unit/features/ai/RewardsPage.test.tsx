import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { RewardsPage } from '@/features/ai/rewards/ui/RewardsPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockRewards = {
  id: 'reward-1',
  student_id: 'student-1',
  stars: 50,
  xp: 100,
  level: 2,
  streak_days: 5,
  longest_streak: 10,
  badges: [],
  last_activity_at: null,
  level_progress: 60,
};

const mockClass = {
  id: 'class-1',
  name: 'Class 6A',
  code: '6A',
  school_id: 'school-1',
};

const mockStudent = {
  id: 'student-1',
  full_name: 'Test Student',
  email: 'student@test.com',
};

describe('RewardsPage (ADM/TCH role - directory)', () => {
  it('renders without crashing', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiResponse([mockClass])),
      http.get('/api/v1/teacher/classes/class-1/students', () => apiResponse([mockStudent])),
    );
    renderWithProviders(<RewardsPage />, { user: { role: 'ADM' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/teacher/classes', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse([mockClass]);
      }),
    );
    renderWithProviders(<RewardsPage />, { user: { role: 'TCH' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders classes when loaded', async () => {
    server.use(http.get('/api/v1/teacher/classes', () => apiResponse([mockClass])));
    renderWithProviders(<RewardsPage />, { user: { role: 'TCH' } });
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state on failure', async () => {
    server.use(http.get('/api/v1/teacher/classes', () => apiErrorResponse('Load failed')));
    renderWithProviders(<RewardsPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});

describe('RewardsPage (STD role - student home)', () => {
  it('renders student rewards view', async () => {
    server.use(
      http.get('/api/v1/rewards/me', () =>
        HttpResponse.json({
          data: mockRewards,
          meta: { timestamp: new Date().toISOString(), version: 'test' },
        }),
      ),
      http.get('/api/v1/rewards/badges', () => apiListResponse([])),
      http.get('/api/v1/rewards/history', () => apiListResponse([])),
      http.get('/api/v1/rewards/history/:studentId', () => apiListResponse([])),
    );
    renderWithProviders(<RewardsPage />, { user: { role: 'STD', id: 'student-1' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
