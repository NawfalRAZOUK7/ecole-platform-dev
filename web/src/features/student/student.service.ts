import { api, getAccessToken } from '@/services/api/client';

export interface QuizListItem {
  id: string;
  title: string;
  description: string | null;
  subject: string | null;
  difficulty: string;
  time_limit_minutes: number | null;
  max_attempts: number;
  question_count: number;
  total_points: number;
  status: string;
}

export interface Question {
  id: string;
  question_type: string;
  question_text: string;
  question_media_path: string | null;
  options: Record<string, unknown> | null;
  points: number;
  order: number;
}

export interface QuizDetail {
  questions: Question[];
  [key: string]: unknown;
}

export interface Attempt {
  id: string;
  quiz_id: string;
  attempt_no: number;
  started_at: string | null;
  completed_at: string | null;
  score: number | null;
  max_score: number | null;
  status: string;
}

export interface ResultResponse {
  question_id: string;
  question_type: string;
  question_text: string;
  student_answer: unknown;
  correct_answer: unknown;
  is_correct: boolean | null;
  points_earned: number | null;
  points: number;
  explanation: string | null;
}

export interface AttemptResult {
  attempt: Attempt;
  responses: ResultResponse[];
}

export interface StudentClassOption {
  class_id: string;
  class_name: string;
}

export interface ClassContentItem {
  id: string;
  content_item_id: string;
  title: string;
  content_type: string;
  level_band: string | null;
  language: string | null;
  subject: string | null;
  description: string | null;
  assigned_at: string | null;
  teacher_notes: string | null;
}

export const studentService = {
  listPublishedQuizzes() {
    return api.list<QuizListItem>('/quizzes', { status: 'published' });
  },

  getQuizDetail(quizId: string) {
    return api.get<QuizDetail>(`/quizzes/${quizId}`);
  },

  startQuizAttempt(quizId: string) {
    return api.post<Attempt>(`/quizzes/${quizId}/start`);
  },

  respondToAttempt(attemptId: string, payload: { question_id: string; student_answer: unknown }) {
    return api.post<void>(`/attempts/${attemptId}/respond`, payload);
  },

  submitAttempt(attemptId: string) {
    return api.post<void>(`/attempts/${attemptId}/submit`);
  },

  getAttemptResults(attemptId: string) {
    return api.get<AttemptResult>(`/attempts/${attemptId}/results`);
  },

  listStudentClasses() {
    return api.list<StudentClassOption>('/enrollments');
  },

  listClassContent(classId: string) {
    return api.list<ClassContentItem>(`/classes/${classId}/content`);
  },

  updateContentProgress(contentItemId: string, status: string) {
    return api.post<void>(`/content-items/${contentItemId}/progress`, { status });
  },

  buildContentStreamUrl(contentItemId: string) {
    const token = getAccessToken();
    const url = new URL(`/api/v1/content-items/${contentItemId}/stream`, window.location.origin);
    if (token) {
      url.searchParams.set('token', token);
    }
    return url.toString();
  },
};
