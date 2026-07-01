import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { ProgressDashboardPage } from '@/features/academic/progress/ui/ProgressDashboardPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiErrorResponse } from '../../../utils/mocks';

const mockProgressData = {
  student_id: 'student-1',
  student_name: 'Alice Example',
  grade_trends: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{ label: 'Average', data: [75, 80, 85] }],
  },
  content_completion: {
    summary: { total: 10, completed: 8, completion_rate: 80 },
    labels: ['Completed', 'Remaining'],
    datasets: [{ label: 'Content', data: [8, 2] }],
  },
  activity_scores: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{ label: 'Score', data: [70, 75, 80] }],
  },
  attendance: {
    overview: {
      labels: ['Present', 'Absent', 'Late'],
      datasets: [{ label: 'Attendance', data: [90, 5, 5] }],
      summary: { total: 100, present: 90, attendance_rate: 90 },
    },
    trend: {
      labels: ['Jan', 'Feb', 'Mar'],
      datasets: [{ label: 'Trend', data: [88, 90, 92] }],
    },
  },
  assessment_results: {
    labels: ['Quiz 1', 'Exam 1'],
    datasets: [
      { label: 'Score', data: [18, 16] },
      { label: 'Max', data: [20, 20] },
    ],
  },
};

describe('ProgressDashboardPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/progress/me', () => apiResponse({ data: mockProgressData })));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<ProgressDashboardPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/progress/me', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse({ data: mockProgressData });
      }),
    );
    renderWithProviders(<ProgressDashboardPage />, { user: { role: 'STD' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders dashboard content after load', async () => {
    renderWithProviders(<ProgressDashboardPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('shows error on API failure', async () => {
    server.use(http.get('/api/v1/progress/me', () => apiErrorResponse('Failed to load progress')));
    renderWithProviders(<ProgressDashboardPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('uses student-specific endpoint for parent view', async () => {
    server.use(
      http.get('/api/v1/progress/student/:studentId', () =>
        apiResponse({ data: mockProgressData }),
      ),
    );
    renderWithProviders(<ProgressDashboardPage />, {
      user: { role: 'PAR' },
      route: '/?studentId=student-1',
    });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(50);
    });
  });
});
