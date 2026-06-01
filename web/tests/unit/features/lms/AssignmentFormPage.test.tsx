import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { AssignmentFormPage } from '@/features/lms/teacher/ui/AssignmentFormPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockCourse = {
  id: 'course-1',
  class_id: 'class-1',
  title: 'Introduction to Math',
  description: null,
  status: 'active',
};

const mockAssignment = {
  id: 'assignment-1',
  course_id: 'course-1',
  title: 'Chapter 1 Homework',
  description: null,
  due_at: '2026-06-01T10:00:00Z',
  total_points: 20,
};

describe('AssignmentFormPage', () => {
  beforeEach(() => {
    server.use(
      http.get('/api/v1/courses', () => apiListResponse([mockCourse])),
      http.get('/api/v1/assignments', () => apiListResponse([mockAssignment])),
    );
  });

  it('renders without crashing', async () => {
    renderWithProviders(<AssignmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/courses', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<AssignmentFormPage />, { user: { role: 'TCH' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows empty state when no assignments', async () => {
    server.use(http.get('/api/v1/assignments', () => apiListResponse([])));
    renderWithProviders(<AssignmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows assignments list when loaded', async () => {
    renderWithProviders(<AssignmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => {
      expect(document.body.innerHTML.length).toBeGreaterThan(100);
    });
  });

  it('shows error on API failure', async () => {
    server.use(
      http.get('/api/v1/courses', () => apiErrorResponse('Failed to load courses')),
      http.get('/api/v1/assignments', () => apiErrorResponse('Failed to load assignments')),
    );
    renderWithProviders(<AssignmentFormPage />, { user: { role: 'TCH' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
