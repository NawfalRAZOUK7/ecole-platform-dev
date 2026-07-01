import { api } from '@/core/api/client';
import type { QuizSummary } from '@/features/lms/quizzes/api/quizzes.api';

export interface Result {
  assignment_id: string;
  assignment_title: string;
  course_title: string;
  due_at: string | null;
  submitted_at: string | null;
  score: number | null;
  out_of: number | null;
  letter_grade: string | null;
  feedback: string | null;
  submission_status: string;
}

export interface QuizAttemptResult {
  id: string;
  quiz_id: string;
  quiz_title?: string;
  attempt_no: number;
  score: number | null;
  max_score: number | null;
  status: string;
  completed_at: string | null;
}

export interface ResultsFilters extends Record<string, string | number | undefined> {
  cursor?: string;
}

export const resultsService = {
  listAssignmentResults(params: ResultsFilters) {
    return api.list<Result>('/results', params);
  },

  async listQuizResults() {
    const response = await api.list<QuizSummary>('/quizzes', { status: 'published' });
    return {
      data: response.data.map((quiz) => ({
        id: quiz.id,
        quiz_id: quiz.id,
        quiz_title: quiz.title,
        attempt_no: 1,
        score: null,
        max_score: quiz.total_points ?? null,
        status: quiz.status,
        completed_at: null,
      })) satisfies QuizAttemptResult[],
      meta: response.meta,
    };
  },
};
