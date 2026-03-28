import { api } from '@/services/api/client';

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

  listQuizResults() {
    return api.list<QuizAttemptResult>('/results/quizzes');
  },
};
