import { api } from '@/services/api/client';

export type QuizQuestionType = 'MCQ' | 'TRUE_FALSE' | 'FILL_IN' | 'DRAG_DROP' | 'MATCHING';
export type QuizDifficulty = 'EASY' | 'MEDIUM' | 'HARD';

export interface QuizQuestion {
  id: string;
  question_type: QuizQuestionType;
  question_text: string;
  question_media_path: string | null;
  options: unknown;
  correct_answer?: unknown;
  points: number;
  order: number;
  explanation: string | null;
}

export interface QuizSummary {
  id: string;
  school_id: string | null;
  created_by: string;
  title: string;
  description: string | null;
  subject: string | null;
  level_band: string | null;
  difficulty: QuizDifficulty | null;
  time_limit_minutes: number | null;
  max_attempts: number;
  shuffle_questions: boolean;
  status: string;
  total_points: number;
  question_count: number;
  recommended?: boolean;
}

export interface QuizDetail extends QuizSummary {
  questions: QuizQuestion[];
}

export interface QuizQuestionInput {
  question_type: QuizQuestionType;
  question_text: string;
  question_media_path?: string | null;
  options: unknown;
  correct_answer: unknown;
  points: number;
  order: number;
  explanation?: string | null;
}

export interface QuizPayload {
  title: string;
  description?: string | null;
  subject?: string | null;
  level_band?: string | null;
  difficulty?: QuizDifficulty | null;
  time_limit_minutes?: number | null;
  max_attempts: number;
  shuffle_questions: boolean;
  questions: QuizQuestionInput[];
}

export interface QuizListFilters extends Record<string, string | number | undefined> {
  subject?: string;
  level_band?: string;
  status?: string;
  difficulty?: string;
  cursor?: string;
  limit?: number;
}

export interface QuizAttempt {
  id: string;
  quiz_id: string;
  student_id: string;
  attempt_no: number;
  started_at: string;
  completed_at: string | null;
  score: number | null;
  max_score: number;
  status: string;
}

export interface QuizRespondPayload {
  question_id: string;
  student_answer: unknown;
}

export interface QuizAttemptResultItem {
  question_id: string;
  question_type: QuizQuestionType;
  question_text: string;
  student_answer: unknown;
  correct_answer: unknown;
  is_correct: boolean | null;
  points_earned: number | null;
  points: number;
  explanation: string | null;
}

export interface QuizAttemptResult {
  attempt: QuizAttempt;
  responses: QuizAttemptResultItem[];
}

export interface QuizAnalyticsQuestionStat {
  question_id: string;
  question_text: string;
  question_type: QuizQuestionType;
  total_responses: number;
  correct_responses: number;
  accuracy: number | null;
}

export interface QuizAnalytics {
  quiz_id: string;
  title: string;
  total_attempts: number;
  completed_attempts: number;
  average_score: number | null;
  max_score_achieved: number | null;
  min_score_achieved: number | null;
  average_percentage: number | null;
  question_stats: QuizAnalyticsQuestionStat[];
}

export const quizzesService = {
  createQuiz(payload: QuizPayload) {
    return api.post<{ id: string }>('/quizzes', payload);
  },

  listQuizzes(params: QuizListFilters = {}) {
    return api.list<QuizSummary>('/quizzes', params);
  },

  getQuiz(quizId: string) {
    return api.get<QuizDetail>(`/quizzes/${quizId}`);
  },

  updateQuiz(quizId: string, payload: Partial<QuizPayload>) {
    return api.put<void>(`/quizzes/${quizId}`, payload);
  },

  publishQuiz(quizId: string) {
    return api.post<{ id: string; status: string }>(`/quizzes/${quizId}/publish`);
  },

  startAttempt(quizId: string) {
    return api.post<QuizAttempt>(`/quizzes/${quizId}/start`);
  },

  respondToQuestion(attemptId: string, payload: QuizRespondPayload) {
    return api.post<{ id: string; attempt_id: string; question_id: string; answered_at: string }>(
      `/attempts/${attemptId}/respond`,
      payload,
    );
  },

  submitAttempt(attemptId: string) {
    return api.post<QuizAttempt>(`/attempts/${attemptId}/submit`);
  },

  getResults(attemptId: string) {
    return api.get<QuizAttemptResult>(`/attempts/${attemptId}/results`);
  },

  getAnalytics(quizId: string) {
    return api.get<QuizAnalytics>(`/quizzes/${quizId}/analytics`);
  },
};
