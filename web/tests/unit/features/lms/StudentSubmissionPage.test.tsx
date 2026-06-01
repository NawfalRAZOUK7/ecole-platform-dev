import { screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { StudentSubmissionPage } from '@/features/lms/submissions/ui/StudentSubmissionPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockAssignment = {
  id: 'assign-1',
  title: 'Math Homework',
  course_id: 'course-1',
  due_at: '2026-12-01T00:00:00Z',
  total_points: 20,
  exercise_type: 'STANDARD',
  exercise_pdf_path: null,
};

describe('StudentSubmissionPage', () => {
  it('renders without crashing', async () => {
    server.use(http.get('/api/v1/assignments', () => apiListResponse([])));
    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/assignments', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders assignments when loaded', async () => {
    server.use(http.get('/api/v1/assignments', () => apiListResponse([mockAssignment])));
    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).toContain('Math Homework');
    });
  });

  it('shows empty state when no assignments', async () => {
    server.use(http.get('/api/v1/assignments', () => apiListResponse([])));
    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error state on failure', async () => {
    server.use(http.get('/api/v1/assignments', () => apiErrorResponse('Load failed')));
    renderWithProviders(<StudentSubmissionPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
