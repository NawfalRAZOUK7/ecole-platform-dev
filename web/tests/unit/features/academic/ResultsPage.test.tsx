import { screen, waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, expect, it } from 'vitest';
import { ResultsPage } from '@/features/academic/results/ui/ResultsPage';
import { renderWithProviders } from '../../../utils/render';
import { apiErrorResponse, apiListResponse, server } from '../../../utils/mocks';

const mockResult = {
  assignment_id: 'asgn-1',
  assignment_title: 'Homework 1 - Fractions',
  course_title: 'Mathematics CM2',
  due_at: '2026-03-15T00:00:00Z',
  submitted_at: '2026-03-14T10:00:00Z',
  score: 17,
  out_of: 20,
  letter_grade: 'A',
  feedback: 'Excellent work!',
  submission_status: 'graded',
};

const mockQuizResult = {
  id: 'attempt-1',
  quiz_id: 'quiz-1',
  quiz_title: 'Quiz on Fractions',
  attempt_no: 1,
  score: 15,
  max_score: 20,
  status: 'published',
  completed_at: null,
};

function setupHandlers() {
  server.use(
    http.get('/api/v1/results', () => apiListResponse([mockResult])),
    http.get('/api/v1/quizzes', () => apiListResponse([mockQuizResult])),
  );
}

describe('ResultsPage', () => {
  it('renders loading state initially', () => {
    server.use(
      http.get('/api/v1/results', async () => {
        await new Promise((r) => setTimeout(r, 100));
        return apiListResponse([]);
      }),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    expect(
      document.querySelector('[role="status"]') || document.querySelector('.loading-state'),
    ).toBeTruthy();
  });

  it('renders assignment results after load', async () => {
    setupHandlers();
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    expect(await screen.findByText('Homework 1 - Fractions')).toBeInTheDocument();
  });

  it('shows score and course title', async () => {
    setupHandlers();
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(screen.queryByText('Mathematics CM2')).toBeTruthy();
      expect(screen.queryByText(/17\/20/) || screen.queryByText('17')).toBeTruthy();
    });
  });

  it('shows letter grade', async () => {
    setupHandlers();
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(screen.queryByText(/\(A\)/) || screen.queryByText('A')).toBeTruthy();
    });
  });

  it('shows feedback text', async () => {
    setupHandlers();
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(screen.queryByText('Excellent work!')).toBeTruthy();
    });
  });

  it('shows empty state when no assignments', async () => {
    server.use(
      http.get('/api/v1/results', () => apiListResponse([])),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(
        document.querySelector('.empty-state') ||
          screen.queryByText(/empty/i) ||
          screen.queryByText(/📊/),
      ).toBeTruthy();
    });
  });

  it('shows error banner when results fail to load', async () => {
    server.use(
      http.get('/api/v1/results', () => apiErrorResponse('Failed to load results')),
      http.get('/api/v1/quizzes', () => apiListResponse([])),
    );
    renderWithProviders(<ResultsPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(
        screen.queryByText(/Failed to load results/) ||
          screen.queryByText(/error/i) ||
          document.querySelector('[role="alert"]'),
      ).toBeTruthy();
    });
  });

  it('renders for parent role', async () => {
    setupHandlers();
    renderWithProviders(<ResultsPage />, { user: { role: 'PAR' } });
    expect(await screen.findByText('Homework 1 - Fractions')).toBeInTheDocument();
  });
});
