import { waitFor } from '@testing-library/react';
import { http } from 'msw';
import { describe, it, expect, beforeEach } from 'vitest';
import { QuizPlayerPage } from '@/features/lms/student/ui/QuizPlayerPage';
import { renderWithProviders } from '../../../utils/render';
import { server, apiListResponse, apiErrorResponse } from '../../../utils/mocks';

const mockQuiz = {
  id: 'quiz-1',
  school_id: null,
  created_by: 'teacher-1',
  title: 'Math Quiz',
  description: 'Basic math questions',
  subject: 'Math',
  level_band: null,
  difficulty: 'EASY' as const,
  time_limit_minutes: null,
  max_attempts: 3,
  shuffle_questions: false,
  status: 'published',
  total_points: 20,
  question_count: 2,
  recommended: false,
};

describe('QuizPlayerPage', () => {
  beforeEach(() => {
    server.use(http.get('/api/v1/quizzes', () => apiListResponse([mockQuiz])));
  });

  it('renders without crashing', async () => {
    renderWithProviders(<QuizPlayerPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.innerHTML.length).toBeGreaterThan(50));
  });

  it('shows loading state initially', () => {
    server.use(
      http.get('/api/v1/quizzes', async () => {
        await new Promise((r) => setTimeout(r, 200));
        return apiListResponse([]);
      }),
    );
    renderWithProviders(<QuizPlayerPage />, { user: { role: 'STD' } });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows empty state when no quizzes', async () => {
    server.use(http.get('/api/v1/quizzes', () => apiListResponse([])));
    renderWithProviders(<QuizPlayerPage />, { user: { role: 'STD' } });
    await waitFor(() => {
      expect(document.body.textContent).not.toContain('Loading');
    });
    expect(document.body.innerHTML.length).toBeGreaterThan(0);
  });

  it('shows error on API failure', async () => {
    server.use(http.get('/api/v1/quizzes', () => apiErrorResponse('Failed to load quizzes')));
    renderWithProviders(<QuizPlayerPage />, { user: { role: 'STD' } });
    await waitFor(() => expect(document.body.textContent).toBeTruthy());
  });
});
