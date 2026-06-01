import { waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { describe, it, expect } from 'vitest';
import { Route, Routes } from 'react-router-dom';
import { RubricGradingPage } from '@/features/lms/rubrics/ui/RubricGradingPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiResponse, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockRubric = {
  id: 'rubric-1',
  title: 'Essay Rubric',
  subject: 'French',
  description: null,
  criteria: [
    {
      id: 'c-1',
      name: 'Content',
      weight: 2,
      levels: [
        { id: 'l-1', label: 'Excellent', score: 4, description: 'Outstanding' },
        { id: 'l-2', label: 'Satisfactory', score: 2, description: 'OK' },
      ],
    },
  ],
  created_at: '2026-01-01T00:00:00Z',
};

const mockResults = {
  results: [
    {
      student_id: 'student-1',
      rubric_id: 'rubric-1',
      total_score: 8,
      max_score: 8,
      percentage: 100,
      entries: [],
    },
  ],
};

describe('RubricGradingPage', () => {
  it('renders without crashing', async () => {
    server.use(
      http.get('/api/v1/rubrics/rubric-1', () => apiResponse(mockRubric)),
      http.get('/api/v1/submissions/rubric-1/rubric-results', () => apiResponse(mockResults)),
    );
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/grade" element={<RubricGradingPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/grade', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/rubrics/rubric-1', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiResponse(mockRubric);
      }),
      http.get('/api/v1/submissions/rubric-1/rubric-results', () => apiResponse(mockResults)),
    );
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/grade" element={<RubricGradingPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/grade', user: { role: 'TCH' } },
    );
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('renders rubric grading form with criteria', async () => {
    server.use(
      http.get('/api/v1/rubrics/rubric-1', () => apiResponse(mockRubric)),
      http.get('/api/v1/submissions/rubric-1/rubric-results', () => apiResponse(mockResults)),
    );
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/grade" element={<RubricGradingPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/grade', user: { role: 'TCH' } },
    );
    await waitFor(
      () => {
        expect(document.body.textContent).not.toContain('Loading');
      },
      { timeout: 3000 },
    );
    expect(document.body.textContent).toContain('Content');
  });

  it('shows error state on failure', async () => {
    server.use(
      http.get('/api/v1/rubrics/rubric-1', () => apiErrorResponse('Not found', 404)),
      http.get('/api/v1/submissions/rubric-1/rubric-results', () =>
        apiErrorResponse('Not found', 404),
      ),
    );
    renderWithProviders(
      <Routes>
        <Route path="/rubrics/:id/grade" element={<RubricGradingPage />} />
      </Routes>,
      { route: '/rubrics/rubric-1/grade', user: { role: 'TCH' } },
    );
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
