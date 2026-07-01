import { api } from '@/core/api/client';
import {
  quizzesService,
  type QuizAttempt as QuizEngineAttempt,
  type QuizAttemptResult as QuizEngineAttemptResult,
  type QuizDetail as QuizEngineDetail,
  type QuizQuestion as QuizEngineQuestion,
  type QuizSummary as QuizEngineSummary,
} from '@/features/lms/quizzes/api/quizzes.api';

export type QuizListItem = QuizEngineSummary;
export type Question = QuizEngineQuestion;
export type QuizDetail = QuizEngineDetail;
export type Attempt = QuizEngineAttempt;
export type ResultResponse = QuizEngineAttemptResult['responses'][number];
export type AttemptResult = QuizEngineAttemptResult;

export interface StudentClassOption {
  class_id: string;
  class_name: string;
}

export interface EnrollmentPayload {
  student_id: string;
  class_id: string;
  period_id: string;
  /** G49 Phase 1 follow-up: optional program (filière) on creation. When set,
   *  the backend writes one INITIAL ProgramAssignmentEvent in the same
   *  transaction. */
  program_id?: string;
}

export interface EnrollmentRecord {
  id: string;
  student_id: string;
  class_id: string;
  period_id: string;
  school_id: string;
  status: string;
  /** Always returned; null when no program is assigned. */
  program_id: string | null;
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

export interface StudentWorkItem {
  id: string;
  type: 'assignment' | 'quiz' | 'assessment';
  title: string;
  due_at: string | null;
  status: string;
  total_points: number | null;
  grading_type: string | null;
}

export interface StudentWorkListResponse {
  items: StudentWorkItem[];
  total: number;
}

export const studentService = {
  listPublishedQuizzes() {
    return quizzesService.listQuizzes({ status: 'published' });
  },

  getQuizDetail(quizId: string) {
    return quizzesService.getQuiz(quizId);
  },

  startQuizAttempt(quizId: string) {
    return quizzesService.startAttempt(quizId);
  },

  respondToAttempt(attemptId: string, payload: { question_id: string; student_answer: unknown }) {
    return quizzesService.respondToQuestion(attemptId, payload);
  },

  submitAttempt(attemptId: string) {
    return quizzesService.submitAttempt(attemptId);
  },

  getAttemptResults(attemptId: string) {
    return quizzesService.getResults(attemptId);
  },

  listStudentClasses() {
    return api.list<StudentClassOption>('/enrollments');
  },

  listStudentWork() {
    return api.get<StudentWorkListResponse>('/student-work');
  },

  listClassStudentWork(classId: string) {
    return api.get<StudentWorkListResponse>(`/student-work/class/${classId}`);
  },

  createEnrollment(payload: EnrollmentPayload) {
    return api.post<EnrollmentRecord>('/enrollments', payload);
  },

  listClassContent(classId: string) {
    return api.list<ClassContentItem>(`/classes/${classId}/content`);
  },

  updateContentProgress(contentItemId: string, status: string) {
    return api.post<void>(`/content-items/${contentItemId}/progress`, { status });
  },

  buildContentStreamUrl(contentItemId: string) {
    return `/content-items/${encodeURIComponent(contentItemId)}/stream`;
  },
};
