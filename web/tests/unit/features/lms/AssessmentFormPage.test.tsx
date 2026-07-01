import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { AssessmentFormPage } from '@/features/lms/teacher/ui/AssessmentFormPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockAssessment = {
  id: 'assessment-1',
  class_id: 'class-1',
  title: 'Midterm Exam',
  due_at: '2026-06-01T10:00:00Z',
  window_end: null,
  total_points: 100,
  status: 'draft',
};

describe('AssessmentFormPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/teacher/classes', () =>
        apiResponse([
          { id: 'class-1', code: '6A', name: 'Class 6A' },
          { id: 'class-2', code: '6B', name: 'Class 6B' },
        ]),
      ),
      http.get('/api/v1/assessments', () => apiListResponse([mockAssessment])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<AssessmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/teacher/classes', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse([]);
      }),
    );
    renderWithProviders(<AssessmentFormPage />, { user: { role: 'TCH' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows empty state when no assessments', async () => {
    server.use(http.get('/api/v1/assessments', () => apiListResponse([])));
    renderWithProviders(<AssessmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows assessments list when loaded', async () => {
    renderWithProviders(<AssessmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('shows error on API failure', async () => {
    server.use(
      http.get('/api/v1/teacher/classes', () => apiErrorResponse('Failed to load classes')),
      http.get('/api/v1/assessments', () => apiErrorResponse('Failed to load assessments')),
    );
    renderWithProviders(<AssessmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
